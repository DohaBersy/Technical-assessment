"""
test_emitter.py

Tests for emitter.py -- uses mocking to avoid needing a live DataHub.
"""
from unittest.mock import patch, MagicMock

from ingestion.source import TableRecord, ColumnInfo
from ingestion.emitter import MetadataEmitter


def _sample_table():
    return TableRecord(
        name="customers",
        description="Customer master data",
        owner="alice@company.com",
        columns=[ColumnInfo(name="id", data_type="string")],
    )


def test_dry_run_does_not_create_real_emitter():
    emitter = MetadataEmitter(gms_server="http://fake:8080", dry_run=True)
    assert emitter._emitter is None


def test_dry_run_reports_success_without_network():
    emitter = MetadataEmitter(gms_server="http://fake:8080", dry_run=True)
    result = emitter.emit_table(_sample_table())
    assert result is True


@patch("ingestion.emitter.DatahubRestEmitter")
def test_real_emit_calls_the_sdk_emitter(mock_emitter_class):
    mock_emitter_instance = MagicMock()
    mock_emitter_class.return_value = mock_emitter_instance

    emitter = MetadataEmitter(gms_server="http://fake:8080", dry_run=False)
    emitter.emit_table(_sample_table())

    assert mock_emitter_instance.emit.call_count == 3


@patch("ingestion.emitter.DatahubRestEmitter")
def test_emit_failure_is_caught_and_logged(mock_emitter_class):
    mock_emitter_instance = MagicMock()
    mock_emitter_instance.emit.side_effect = ConnectionError("network down")
    mock_emitter_class.return_value = mock_emitter_instance

    emitter = MetadataEmitter(gms_server="http://fake:8080", dry_run=False)
    result = emitter.emit_table(_sample_table())

    assert result is False


@patch("ingestion.emitter.DatahubRestEmitter")
def test_emit_all_counts_successes_and_failures(mock_emitter_class):
    mock_emitter_instance = MagicMock()
    mock_emitter_class.return_value = mock_emitter_instance

    good_table = _sample_table()
    bad_table = TableRecord(name="broken", description="", owner="", columns=[])

    call_count = {"n": 0}

    def emit_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] > 3:
            raise ConnectionError("simulated failure")

    mock_emitter_instance.emit.side_effect = emit_side_effect

    emitter = MetadataEmitter(gms_server="http://fake:8080", dry_run=False)
    summary = emitter.emit_all([good_table, bad_table])

    assert summary["succeeded"] == 1
    assert summary["failed"] == 1
    assert summary["total"] == 2