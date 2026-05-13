import pytest

from sql_anon.anonymize import anonymize
from sql_anon.deanonymize import deanonymize


def test_replaces_placeholder_with_original():
    result = deanonymize("SELECT tabell_1", {"tabell_1": "personal"})
    assert result == "SELECT personal"


def test_text_without_placeholders_returned_unchanged():
    result = deanonymize("hello world", {"tabell_1": "personal"})
    assert result == "hello world"


def test_empty_mapping_returns_text_unchanged():
    result = deanonymize("hello world", {})
    assert result == "hello world"


def test_round_trip_restores_original_names():
    sql_in = "SELECT namn FROM personal"
    anonymized, mapping = anonymize(sql_in)
    restored = deanonymize(anonymized, mapping)

    assert "namn" in restored
    assert "personal" in restored
    assert "tabell_" not in restored
    assert "kolumn_" not in restored


def test_unknown_placeholder_raises_value_error():
    with pytest.raises(ValueError, match="okänd"):
        deanonymize("SELECT tabell_99", {"tabell_1": "personal"})


def test_unknown_placeholder_lists_all_missing_in_error():
    with pytest.raises(ValueError) as excinfo:
        deanonymize("SELECT tabell_99, kolumn_42", {"tabell_1": "personal"})
    assert "tabell_99" in str(excinfo.value)
    assert "kolumn_42" in str(excinfo.value)


def test_longer_placeholder_numbers_match_correctly():
    # kolumn_1 ska inte matcha början av kolumn_10
    mapping = {"kolumn_1": "namn", "kolumn_10": "lon"}
    result = deanonymize("SELECT kolumn_10 FROM x", mapping)
    assert result == "SELECT lon FROM x"


def test_replaces_multiple_occurrences():
    mapping = {"tabell_1": "personal", "kolumn_1": "namn"}
    result = deanonymize("kolumn_1, kolumn_1, tabell_1", mapping)
    assert result == "namn, namn, personal"
