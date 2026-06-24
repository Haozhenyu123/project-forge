
import json
import os
from pathlib import Path

import pytest

DOMAINS_DIR = Path(__file__).resolve().parents[2] / "src" / "project_forge" / "intent" / "domains"


def _list_profiles():
    return [p for p in DOMAINS_DIR.glob("*.json")]


class TestDomainProfiles:
    def test_at_least_general_exists(self):
        assert (DOMAINS_DIR / "general.json").is_file()

    def test_all_profiles_parse(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "domain" in data
            assert "probing_axes" in data
            assert "domain_profile" in data
            assert isinstance(data["domain_profile"], str)

    def test_required_questions_not_empty(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["domain"] != "general":
                assert len(data["probing_axes"]) > 0, f"{path.name} has empty probing_axes"

    def test_risk_weights_valid(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            for key, val in data.get("risk_weights", {}).items():
                assert val > 0, f"{path.name} has invalid risk_weight {key}={val}"

    def test_domain_matches_filename(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            expected = path.stem
            assert data["domain"] == expected, f"{path.name} has domain={data['domain']}, expected {expected}"

    def test_probing_axes_are_well_formed(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["domain"] != "general":
                assert "probing_axes" in data
                assert len(data["probing_axes"]) > 0, f"{path.name} has empty probing_axes"
                for ax in data["probing_axes"]:
                    assert "axis" in ax, f"{path.name} probing axis missing 'axis'"
                    assert "prompt" in ax, f"{path.name} probing axis missing 'prompt'"
                    assert "why_matters" in ax, f"{path.name} probing axis missing 'why_matters'"

    def test_capabilities_exist(self):
        for path in _list_profiles():
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "capabilities" in data
            assert isinstance(data["capabilities"], list)
