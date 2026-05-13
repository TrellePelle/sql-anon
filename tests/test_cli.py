import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sql_anon.cli import app

runner = CliRunner()


def test_anonymize_writes_sql_to_stdout_and_mapping_to_file(tmp_path):
    sql_file = tmp_path / "query.sql"
    sql_file.write_text("SELECT namn FROM personal", encoding="utf-8")

    result = runner.invoke(app, ["anonymize", str(sql_file)])

    assert result.exit_code == 0
    assert "tabell_1" in result.stdout

    mapping_file = tmp_path / "query.sql.mapping.json"
    assert mapping_file.exists()
    mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert "personal" in mapping.values()


def test_anonymize_invalid_sql_exits_with_error(tmp_path):
    sql_file = tmp_path / "bad.sql"
    sql_file.write_text("INTE GILTIG ###", encoding="utf-8")

    result = runner.invoke(app, ["anonymize", str(sql_file)])

    assert result.exit_code == 1
    assert "Fel" in result.stderr


def test_anonymize_missing_file_exits_with_error(tmp_path):
    result = runner.invoke(app, ["anonymize", str(tmp_path / "saknas.sql")])
    assert result.exit_code != 0


def test_deanonymize_replaces_placeholders(tmp_path):
    text_file = tmp_path / "svar.txt"
    text_file.write_text("Frågan hämtar från tabell_1", encoding="utf-8")
    mapping_file = tmp_path / "mapping.json"
    mapping_file.write_text(
        json.dumps({"tabell_1": "personal"}), encoding="utf-8"
    )

    result = runner.invoke(app, ["deanonymize", str(text_file), str(mapping_file)])

    assert result.exit_code == 0
    assert "personal" in result.stdout


def test_deanonymize_unknown_placeholder_exits_with_error(tmp_path):
    text_file = tmp_path / "svar.txt"
    text_file.write_text("tabell_99", encoding="utf-8")
    mapping_file = tmp_path / "mapping.json"
    mapping_file.write_text(
        json.dumps({"tabell_1": "personal"}), encoding="utf-8"
    )

    result = runner.invoke(app, ["deanonymize", str(text_file), str(mapping_file)])

    assert result.exit_code == 1


def test_explain_missing_api_key_exits_with_error(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    sql_file = tmp_path / "query.sql"
    sql_file.write_text("SELECT 1", encoding="utf-8")

    result = runner.invoke(app, ["explain", str(sql_file)])

    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.stderr


def test_explain_calls_anthropic_with_sql(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    sql_file = tmp_path / "query.sql"
    sql_file.write_text("SELECT 1", encoding="utf-8")

    with patch("sql_anon.cli.anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Detta är en förklaring.")]
        )
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["explain", str(sql_file)])

    assert result.exit_code == 0
    assert "Detta är en förklaring." in result.stdout
