"""Tests for input loading."""

import json
import pytest
from hermes_session_exporter.loader import load_input, detect_input_type


def test_load_json_single_session(sample_json_path):
    sessions = load_input(sample_json_path)
    assert len(sessions) == 1
    assert len(sessions[0].messages) == 8


def test_load_jsonl(sample_jsonl_path):
    sessions = load_input(sample_jsonl_path)
    assert len(sessions) == 1
    assert len(sessions[0].messages) == 6


def test_load_json_dict_with_messages(make_session_file, session_dict):
    path = make_session_file(session_dict)
    sessions = load_input(path)
    assert len(sessions) == 1
    assert sessions[0].title == "Test Session"
    assert len(sessions[0].messages) == 4


def test_load_json_array_of_sessions(make_session_file):
    data = [
        {"title": "Session A", "messages": [{"role": "user", "content": "a"}]},
        {"title": "Session B", "messages": [{"role": "user", "content": "b"}]},
    ]
    path = make_session_file(data)
    sessions = load_input(path)
    assert len(sessions) == 2


def test_load_json_no_title_derives_from_first_user(make_session_file, session_dict_no_title):
    path = make_session_file(session_dict_no_title)
    sessions = load_input(path)
    assert sessions[0].title is None


def test_load_jsonl_raw_messages(tmp_path):
    p = tmp_path / "raw.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "hi"}) + "\n"
        + json.dumps({"role": "assistant", "content": "hello"}) + "\n"
    )
    sessions = load_input(p)
    assert len(sessions) == 1
    assert len(sessions[0].messages) == 2


def test_load_directory(make_session_file, tmp_path):
    make_session_file({"title": "A", "messages": [{"role": "user", "content": "a"}]}, name="a.json")
    make_session_file({"title": "B", "messages": [{"role": "user", "content": "b"}]}, name="b.json")
    sessions = load_input(tmp_path)
    assert len(sessions) == 2


def test_load_empty_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_input(tmp_path)


def test_load_unsupported_extension(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported"):
        load_input(p)


def test_detect_input_type_json(sample_json_path):
    assert "JSON" == detect_input_type(sample_json_path)


def test_detect_input_type_jsonl(sample_jsonl_path):
    assert "JSONL" == detect_input_type(sample_jsonl_path)


def test_detect_input_type_directory(tmp_path):
    result = detect_input_type(tmp_path)
    assert "directory" in result


def test_load_nested_wrapper(make_session_file):
    data = {"sessions": [{"title": "Wrapped", "messages": [{"role": "user", "content": "x"}]}]}
    path = make_session_file(data)
    sessions = load_input(path)
    assert len(sessions) == 1
    assert sessions[0].title == "Wrapped"
