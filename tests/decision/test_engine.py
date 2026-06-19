import json
import unittest

from scripts.decision.engine import build_decision


AS_OF = "2026-06-19"


def evidence(evidence_id, source, title, observed_at, summary="", url=""):
    return {
        "evidence_id": evidence_id,
        "source": source,
        "title": title,
        "summary": summary or title,
        "url": url or f"https://example.test/{evidence_id}",
        "observed_at": observed_at,
        "provisional": False,
    }


class DecisionEngineTests(unittest.TestCase):
    def test_vague_idea_produces_three_directions_and_a_low_confidence_default(self):
        payload = {
            "goal": "Build something for teams that makes planning easier.",
            "constraints": [],
            "creative_brief": {},
            "evidence": [],
        }

        first = build_decision(payload, as_of=AS_OF)
        second = build_decision(payload, as_of=AS_OF)

        self.assertEqual(first, second)
        self.assertEqual(len(first["product_directions"]), 3)
        self.assertIn(
            first["selected_direction"]["id"],
            {item["id"] for item in first["product_directions"]},
        )
        self.assertEqual(first["decision_confidence"], "Low")
        self.assertTrue(first["clarifying_questions"])
        self.assertTrue(first["assumptions"])
        self.assertEqual(len(first["architecture_candidates"]), 3)
        json.dumps(first, sort_keys=True)

    def test_trendy_framework_is_rejected_without_fit_and_diverse_evidence(self):
        payload = {
            "goal": "Build a stable web dashboard for a small operations team.",
            "constraints": ["low maintenance", "stable ecosystem", "small team"],
            "creative_brief": {"platform": "web", "interaction_style": "dashboard"},
            "candidate_stacks": [
                {
                    "id": "future-js",
                    "name": "FutureJS",
                    "components": ["FutureJS"],
                    "capabilities": ["web", "dashboard"],
                    "maintenance": 90,
                    "complexity": 75,
                    "maturity_months": 4,
                    "harnesses": [],
                    "aliases": ["futurejs"],
                }
            ],
            "evidence": [
                evidence(
                    "E1",
                    "social",
                    "FutureJS is the framework everyone is discussing",
                    "2026-06-10",
                    "FutureJS is new and popular.",
                )
            ],
        }

        result = build_decision(payload, as_of=AS_OF)

        self.assertNotEqual(result["selected_architecture"]["id"], "future-js")
        rejected = {
            item["id"]: " ".join(item["reasons"]).lower()
            for item in result["rejected_options"]
        }
        self.assertIn("future-js", rejected)
        self.assertTrue(
            "maturity" in rejected["future-js"]
            or "evidence" in rejected["future-js"]
        )

    def test_stale_evidence_caps_confidence_and_adds_revisit_trigger(self):
        payload = {
            "goal": "Choose a hosted vector database using the latest pricing and limits.",
            "constraints": ["hosted", "latest pricing", "current service limits"],
            "creative_brief": {"platform": "web-api"},
            "evidence": [
                evidence(
                    "E1",
                    "official-docs",
                    "Vendor pricing and limits",
                    "2023-01-15",
                    "Hosted vector database pricing and service limits.",
                )
            ],
        }

        result = build_decision(payload, as_of=AS_OF)

        self.assertEqual(result["decision_confidence"], "Low")
        trigger_ids = {item["id"] for item in result["revisit_triggers"]}
        self.assertIn("stale-evidence", trigger_ids)
        selected = result["selected_architecture"]
        self.assertLess(selected["scores"]["evidence_freshness"], 50)

    def test_conflicting_constraints_are_reported_instead_of_hidden(self):
        payload = {
            "goal": "Build a notes app.",
            "constraints": [
                "fully offline",
                "instant sync across all devices",
                "no server",
            ],
            "creative_brief": {"architecture_signals": ["offline-first", "multi-device"]},
            "evidence": [],
        }

        result = build_decision(payload, as_of=AS_OF)

        self.assertTrue(result["conflicts"])
        self.assertEqual(result["decision_confidence"], "Low")
        self.assertIn(
            "offline",
            " ".join(result["conflicts"][0]["constraints"]).lower(),
        )
        self.assertIn(
            "server",
            " ".join(result["conflicts"][0]["constraints"]).lower(),
        )
        trigger_ids = {item["id"] for item in result["revisit_triggers"]}
        self.assertIn("resolve-conflicting-constraints", trigger_ids)

    def test_multi_stack_goal_selects_frontend_backend_handoff(self):
        payload = {
            "goal": "Build a data-heavy web dashboard with a REST API backend.",
            "constraints": [
                "separate frontend and backend",
                "TypeScript frontend",
                "Python backend",
                "small team",
            ],
            "creative_brief": {
                "platform": "web",
                "interaction_style": "dashboard",
                "architecture_signals": ["REST API backend", "data-heavy dashboard"],
            },
            "evidence": [
                evidence(
                    "E1",
                    "official-docs",
                    "Next.js documentation",
                    "2026-05-20",
                    "Next.js TypeScript dashboard framework.",
                ),
                evidence(
                    "E2",
                    "github",
                    "vercel/next.js repository",
                    "2026-05-18",
                    "Maintained Next.js source repository.",
                ),
                evidence(
                    "E3",
                    "official-docs",
                    "FastAPI documentation",
                    "2026-05-21",
                    "Python REST API framework with OpenAPI.",
                ),
                evidence(
                    "E4",
                    "github",
                    "fastapi/fastapi repository",
                    "2026-05-19",
                    "Maintained FastAPI source repository.",
                ),
            ],
        }

        result = build_decision(payload, as_of=AS_OF)

        self.assertGreaterEqual(len(result["architecture_candidates"]), 2)
        self.assertLessEqual(len(result["architecture_candidates"]), 4)
        selected = result["selected_architecture"]
        self.assertEqual(selected["id"], "nextjs-fastapi")
        self.assertEqual(selected["harness"]["primary"], "nextjs")
        self.assertEqual(selected["harness"]["secondary"], ["fastapi"])
        self.assertEqual(selected["handoff"]["architecture_mode"], "multi-stack")
        self.assertIn("install", selected["handoff"]["required_commands"])
        self.assertTrue(result["rejected_options"])


if __name__ == "__main__":
    unittest.main()
