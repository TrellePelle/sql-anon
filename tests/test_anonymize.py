import pytest

from sql_anon.anonymize import anonymize


def test_table_name_is_replaced():
    sql, mapping = anonymize("SELECT * FROM personal")
    assert "tabell_1" in sql
    assert "personal" in mapping.values()


def test_column_name_is_replaced():
    sql, mapping = anonymize("SELECT namn FROM personal")
    assert "kolumn_1" in sql
    assert "namn" in mapping.values()


def test_same_column_name_gets_same_placeholder():
    sql, mapping = anonymize("SELECT namn, namn FROM personal")
    assert sql.count("kolumn_1") == 2
    assert list(mapping.values()).count("namn") == 1


def test_alias_is_replaced():
    sql, mapping = anonymize("SELECT a.namn FROM personal a")
    assert "a" in mapping.values()
    assert any(ph.startswith("alias_") for ph in mapping)


def test_deterministic_mapping():
    sql1, mapping1 = anonymize("SELECT namn FROM personal")
    sql2, mapping2 = anonymize("SELECT namn FROM personal")
    assert sql1 == sql2
    assert mapping1 == mapping2


def test_invalid_sql_raises_value_error():
    with pytest.raises(ValueError):
        anonymize("INTE GILTIG SQL ###")


def test_empty_sql_raises_value_error():
    with pytest.raises(ValueError):
        anonymize("")


def test_whitespace_only_sql_raises_value_error():
    with pytest.raises(ValueError):
        anonymize("   \n\t  ")
