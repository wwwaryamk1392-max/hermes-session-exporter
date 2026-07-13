"""Shared fixtures for tests."""

import json
import pytest
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def sample_json_path():
    return EXAMPLES / "sample_session.json"


@pytest.fixture
def sample_jsonl_path():
    return EXAMPLES / "sample_session.jsonl"


@pytest.fixture
def session_dict():
    return {
        "title": "Test Session",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "tool", "name": "search", "content": "Found 3 results"},
            {"role": "assistant", "content": "Here are the results."},
        ],
    }


@pytest.fixture
def session_dict_no_title():
    return {
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
        ],
    }


@pytest.fixture
def make_session_file(tmp_path):
    """Factory fixture: write a dict to a .json file and return the path."""
    def _make(data, name="test_session.json"):
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p
    return _make
