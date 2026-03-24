from artifact_radar.json_extract import extract_json_array, extract_json_object


def test_extract_array_plain():
    text = '[{"a": 1}, {"a": 2}]'
    assert extract_json_array(text) == [{"a": 1}, {"a": 2}]


def test_extract_array_with_fence():
    text = 'Here:\n```json\n[{"x": true}]\n```\ntrailing'
    assert extract_json_array(text) == [{"x": True}]


def test_extract_object():
    text = 'noise {"status": "HIGH RISK", "risk_score": 9} end'
    obj = extract_json_object(text)
    assert obj["status"] == "HIGH RISK"
    assert obj["risk_score"] == 9


def test_extract_array_invalid_returns_none():
    assert extract_json_array("no array here") is None
