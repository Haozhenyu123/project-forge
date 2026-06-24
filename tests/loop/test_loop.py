"""Loop Engine tests: signals, state machine, strategy, convergence, storage, service, security."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.loop.models import (
    ConfidenceTier,
    CostTier,
    LoopEpisode,
    LoopPolicy,
    LoopSignal,
    LoopStatus,
    SignalKind,
    SignalSeverity,
    OwnerClassification,
)
from project_forge.loop.signals import (
    validate_signal,
    classify_owner,
    deduplicate_signals,
    is_duplicate,
)
from project_forge.loop.state_machine import can_transition, transition, TRANSITIONS
from project_forge.loop.strategy import (
    evaluate_switch,
    evaluate_confidence,
    classify_migration_cost,
)
from project_forge.loop.convergence import check_convergence, generate_human_packet
from project_forge.loop.storage import ensure_dirs, save_state, load_state, atomic_write, backup_file


def _make_signal(kind="manual", severity="medium", signal_id="test-1", summary="Test signal"):
    return LoopSignal(
        signal_id=signal_id,
        source="test",
        kind=SignalKind(kind),
        severity=SignalSeverity(severity),
        observed_at=datetime.utcnow().isoformat(),
        summary=summary,
    )


class SignalValidationTests(unittest.TestCase):
    def test_valid_signal_passes(self):
        data = {
            "signal_id": "sig-1",
            "kind": "manual",
            "severity": "medium",
            "summary": "A test signal",
        }
        self.assertEqual([], validate_signal(data))

    def test_missing_signal_id_fails(self):
        errors = validate_signal({"kind": "manual", "severity": "low", "summary": "x"})
        self.assertIn("signal_id is required", errors)

    def test_unknown_kind_fails(self):
        errors = validate_signal({"signal_id": "x", "kind": "bogus", "severity": "low", "summary": "x"})
        self.assertTrue(any("unknown signal kind" in e for e in errors))

    def test_unknown_severity_fails(self):
        errors = validate_signal({"signal_id": "x", "kind": "manual", "severity": "extreme", "summary": "x"})
        self.assertTrue(any("unknown severity" in e for e in errors))

    def test_fingerprint_is_computed(self):
        s = _make_signal()
        self.assertTrue(len(s.fingerprint) > 0)

    def test_duplicate_fingerprints_detected(self):
        s1 = _make_signal(signal_id="same-id", summary="same summary text")
        s2 = _make_signal(signal_id="same-id", summary="same summary text")
        self.assertEqual(s1.fingerprint, s2.fingerprint)
        self.assertTrue(is_duplicate(s2, [s1.fingerprint]))


class OwnerClassificationTests(unittest.TestCase):
    def test_critical_security_goes_to_human(self):
        s = _make_signal(kind="security_advisory", severity="critical")
        self.assertEqual(OwnerClassification.HUMAN, classify_owner(s))

    def test_evidence_expiry_goes_to_forge(self):
        s = _make_signal(kind="evidence_expiry", severity="medium")
        self.assertEqual(OwnerClassification.FORGE, classify_owner(s))

    def test_verification_failure_goes_to_superpowers(self):
        s = _make_signal(kind="verification_failure", severity="high")
        self.assertEqual(OwnerClassification.SUPERPOWERS, classify_owner(s))

    def test_explicit_suggestion_is_honored(self):
        s = _make_signal(kind="verification_failure")
        s.suggested_owner = OwnerClassification.FORGE
        self.assertEqual(OwnerClassification.FORGE, classify_owner(s))


class StateMachineTests(unittest.TestCase):
    def test_idle_to_collecting(self):
        self.assertTrue(can_transition(LoopStatus.IDLE, LoopStatus.COLLECTING))

    def test_collecting_to_evaluating(self):
        self.assertTrue(can_transition(LoopStatus.COLLECTING, LoopStatus.EVALUATING))

    def test_evaluating_to_revising(self):
        self.assertTrue(can_transition(LoopStatus.EVALUATING, LoopStatus.REVISING))

    def test_revising_to_handoff_ready(self):
        self.assertTrue(can_transition(LoopStatus.REVISING, LoopStatus.HANDOFF_READY))

    def test_handoff_ready_to_awaiting_feedback(self):
        self.assertTrue(can_transition(LoopStatus.HANDOFF_READY, LoopStatus.AWAITING_FEEDBACK))

    def test_awaiting_feedback_to_collecting(self):
        self.assertTrue(can_transition(LoopStatus.AWAITING_FEEDBACK, LoopStatus.COLLECTING))

    def test_blocked_to_collecting(self):
        self.assertTrue(can_transition(LoopStatus.BLOCKED, LoopStatus.COLLECTING))

    def test_illegal_transition_raises(self):
        ep = LoopEpisode(episode_id="ep-1", slug="test", root_cause="test")
        ep.status = LoopStatus.IDLE
        with self.assertRaises(ValueError):
            transition(ep, LoopStatus.HANDOFF_READY)

    def test_transition_succeeds(self):
        ep = LoopEpisode(episode_id="ep-1", slug="test", root_cause="test")
        ep.status = LoopStatus.IDLE
        ep = transition(ep, LoopStatus.COLLECTING)
        self.assertEqual(LoopStatus.COLLECTING, ep.status)

    def test_all_defined_transitions(self):
        self.assertGreater(len(TRANSITIONS), 10)


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.policy = LoopPolicy.default()

    def test_switch_disabled_by_policy(self):
        self.policy.allow_primary_stack_switch = False
        result = evaluate_switch("node-ts", "nextjs", 50, 70, self.policy, ["a", "b"], ConfidenceTier.HIGH, CostTier.LOW, _make_signal())
        self.assertFalse(result["allowed"])

    def test_critical_security_forces_switch(self):
        s = _make_signal(kind="security_advisory", severity="critical")
        result = evaluate_switch("node-ts", "nextjs", 50, 70, self.policy, ["a"], ConfidenceTier.LOW, CostTier.HIGH, s)
        self.assertTrue(result["allowed"])
        self.assertIn("hard-block", result["reason"])

    def test_delta_below_threshold_blocks(self):
        result = evaluate_switch("node-ts", "nextjs", 50, 55, self.policy, ["a", "b"], ConfidenceTier.HIGH, CostTier.LOW, _make_signal())
        self.assertFalse(result["allowed"])
        self.assertIn("delta", result["reason"])

    def test_confidence_below_minimum_blocks(self):
        result = evaluate_switch("node-ts", "nextjs", 50, 70, self.policy, ["a", "b"], ConfidenceTier.LOW, CostTier.LOW, _make_signal())
        self.assertFalse(result["allowed"])

    def test_not_enough_sources_blocks(self):
        result = evaluate_switch("node-ts", "nextjs", 50, 70, self.policy, ["a"], ConfidenceTier.HIGH, CostTier.LOW, _make_signal())
        self.assertFalse(result["allowed"])

    def test_high_migration_cost_blocks(self):
        result = evaluate_switch("node-ts", "python", 50, 70, self.policy, ["a", "b", "c"], ConfidenceTier.HIGH, CostTier.HIGH, _make_signal())
        self.assertFalse(result["allowed"])

    def test_all_conditions_met_allows_switch(self):
        result = evaluate_switch("node-ts", "nextjs", 50, 75, self.policy, ["a", "b", "c"], ConfidenceTier.HIGH, CostTier.LOW, _make_signal())
        self.assertTrue(result["allowed"])

    def test_classify_same_family_low_cost(self):
        self.assertEqual(CostTier.LOW, classify_migration_cost("node-ts", "nextjs"))
        self.assertEqual(CostTier.LOW, classify_migration_cost("python", "fastapi"))

    def test_classify_cross_runtime_medium_cost(self):
        self.assertEqual(CostTier.MEDIUM, classify_migration_cost("node-ts", "python"))

    def test_classify_unknown_high_cost(self):
        self.assertEqual(CostTier.HIGH, classify_migration_cost("node-ts", "generic"))

    def test_confidence_high_with_strong_evidence(self):
        self.assertEqual(ConfidenceTier.HIGH, evaluate_confidence("High", 10, 0, 5))

    def test_confidence_low_with_provisional(self):
        self.assertEqual(ConfidenceTier.LOW, evaluate_confidence("High", 10, 8, 3))


class ConvergenceTests(unittest.TestCase):
    def test_initial_episode_continues(self):
        ep = LoopEpisode(episode_id="ep-1", slug="t", root_cause="test")
        result = check_convergence(ep, _make_signal(), "hash1")
        self.assertEqual("continue", result["action"])

    def test_exhausted_episode_blocks(self):
        ep = LoopEpisode(episode_id="ep-1", slug="t", root_cause="test", policy=LoopPolicy(max_iterations=1))
        from project_forge.loop.models import LoopIteration
        ep.iterations = [LoopIteration(iteration_id="i-1", index=1, signal=_make_signal(), decision_hash="h1", action="revise", summary="x")]
        result = check_convergence(ep, _make_signal(), "h2")
        self.assertEqual("human_packet", result["action"])

    def test_stale_progress_detected(self):
        ep = LoopEpisode(episode_id="ep-1", slug="t", root_cause="test")
        from project_forge.loop.models import LoopIteration
        ep.iterations = [
            LoopIteration(iteration_id="i-1", index=1, signal=_make_signal(signal_id="a"), decision_hash="h1", action="revise", summary="x"),
            LoopIteration(iteration_id="i-2", index=2, signal=_make_signal(signal_id="b"), decision_hash="h1", action="revise", summary="x"),
        ]
        result = check_convergence(ep, _make_signal(signal_id="c"), "h1")
        self.assertEqual("blocked", result["action"])

    def test_human_packet_has_required_fields(self):
        ep = LoopEpisode(episode_id="ep-1", slug="t", root_cause="test")
        packet = generate_human_packet(ep, [], [])
        self.assertTrue(len(packet.must_decide) > 0)
        self.assertIsNotNone(packet.generated_at)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ensure_dirs_creates_all(self):
        dirs = ensure_dirs(self.project)
        for d in dirs.values():
            self.assertTrue(d.is_dir())

    def test_save_and_load_state_roundtrip(self):
        ep = LoopEpisode(episode_id="ep-1", slug="test", root_cause="test")
        ep.status = LoopStatus.COLLECTING
        save_state(self.project, ep)
        loaded = load_state(self.project)
        self.assertIsNotNone(loaded)
        self.assertEqual("ep-1", loaded.episode_id)
        self.assertEqual(LoopStatus.COLLECTING, loaded.status)

    def test_atomic_write(self):
        path = self.project / "test.json"
        atomic_write(path, '{"key": "value"}')
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text())
        self.assertEqual("value", data["key"])

    def test_backup_creates_copy(self):
        path = self.project / "original.txt"
        path.write_text("original content")
        backup = backup_file(path)
        self.assertIsNotNone(backup)
        self.assertTrue(backup.is_file())
        self.assertTrue("bak-" in backup.name)

    def test_load_state_nonexistent(self):
        self.assertIsNone(load_state(self.project))


class SecurityTests(unittest.TestCase):
    """Verify that the loop engine cannot write application code or execute commands."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / "src").mkdir(parents=True)
        (self.project / "src" / "app.py").write_text("print('hello')")
        ensure_dirs(self.project)

    def tearDown(self):
        self.tmp.cleanup()

    def test_policy_denies_application_writes(self):
        policy = LoopPolicy.default()
        self.assertFalse(policy.allow_application_writes)
        self.assertFalse(policy.execute_install_or_run)

    def test_policy_to_dict_includes_safety_flags(self):
        policy = LoopPolicy.default()
        d = policy.to_dict()
        self.assertFalse(d["allow_application_writes"])
        self.assertFalse(d["execute_install_or_run"])


class IntegrationSignalFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_signal_dedup_across_runs(self):
        dirs = ensure_dirs(self.project)
        s1 = _make_signal(signal_id="a", summary="unique 1")
        s2 = _make_signal(signal_id="b", summary="unique 2")
        s3 = _make_signal(signal_id="a", summary="unique 1")  # duplicate of s1
        known = [s1.fingerprint]
        result = deduplicate_signals([s1, s2, s3], known)
        self.assertEqual(1, len(result))
        self.assertEqual(s2.fingerprint, result[0].fingerprint)

    def test_loop_status_on_empty_project(self):
        from project_forge.loop.service import get_loop_status
        result = get_loop_status(str(self.project))
        self.assertEqual("no_loop", result["status"])

    def test_ingest_signal_creates_inbox_entry(self):
        from project_forge.loop.service import ingest_signal
        dirs = ensure_dirs(self.project)
        data = {
            "signal_id": "sig-test",
            "kind": "manual",
            "severity": "low",
            "summary": "Ingest test",
        }
        result = ingest_signal(str(self.project), data)
        self.assertEqual("ingested", result["status"])
        inbox_files = list(dirs["inbox"].glob("*.json"))
        self.assertEqual(1, len(inbox_files))

    def test_ingest_invalid_signal_rejected(self):
        from project_forge.loop.service import ingest_signal
        result = ingest_signal(str(self.project), {"bad": "data"})
        self.assertEqual("invalid", result["status"])

    def test_resume_blocked_loop(self):
        from project_forge.loop.service import resume_loop
        # First create a blocked state
        ep = LoopEpisode(episode_id="ep-1", slug="test", root_cause="test")
        ep.status = LoopStatus.BLOCKED
        save_state(self.project, ep)
        result = resume_loop(str(self.project), "retry")
        self.assertEqual("resumed", result["status"])

    def test_resume_non_blocked_fails(self):
        from project_forge.loop.service import resume_loop
        ep = LoopEpisode(episode_id="ep-1", slug="test", root_cause="test")
        ep.status = LoopStatus.IDLE
        save_state(self.project, ep)
        result = resume_loop(str(self.project), "retry")
        self.assertEqual("error", result["status"])


class CompatibilityTests(unittest.TestCase):
    def test_loop_policy_defaults_match_spec(self):
        p = LoopPolicy.default()
        self.assertEqual(3, p.max_iterations)
        self.assertEqual("weekly", p.schedule)
        self.assertEqual(15, p.switch_score_delta)
        self.assertEqual(ConfidenceTier.MEDIUM, p.minimum_confidence)
        self.assertEqual(2, p.minimum_independent_sources)

    def test_handoff_schema_v2_accepts_loop_metadata(self):
        schema_path = Path(__file__).resolve().parents[2] / "docs" / "schemas" / "superpowers-handoff.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIn("loop", schema["properties"])
        loop_props = schema["properties"]["loop"]["properties"]
        self.assertIn("episode_id", loop_props)
        self.assertIn("decision_hash", loop_props)
        self.assertIn("current_status", loop_props)

    def test_loop_signal_schema_is_valid_json(self):
        schema_path = Path(__file__).resolve().parents[2] / "docs" / "schemas" / "loop-signal.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual("Project Forge Loop Signal", schema["title"])


if __name__ == "__main__":
    unittest.main()
