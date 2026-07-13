"""
test_tagger.py

Tests for tagger.py -- uses mocking to avoid needing a live DataHub.
"""
from unittest.mock import patch, MagicMock

from rules_engine.rule_loader import Action
from rules_engine.tagger import TagApplier


def test_dry_run_does_not_create_real_emitter():
    tagger = TagApplier(gms_server="http://fake:8080", dry_run=True)
    assert tagger._emitter is None


def test_dry_run_reports_success_without_network():
    tagger = TagApplier(gms_server="http://fake:8080", dry_run=True)
    actions = [Action(action="add_tag", tag="urn:li:tag:Compliant")]
    result = tagger.apply_actions("urn:li:dataset:(urn:li:dataPlatform:csv,x,PROD)", actions)
    assert result is True


def test_no_tag_actions_returns_true_immediately():
    tagger = TagApplier(gms_server="http://fake:8080", dry_run=True)
    result = tagger.apply_actions("urn:li:dataset:(urn:li:dataPlatform:csv,x,PROD)", [])
    assert result is True


@patch("rules_engine.tagger.DatahubRestEmitter")
def test_real_emit_is_called_once_per_apply(mock_emitter_class):
    mock_instance = MagicMock()
    mock_emitter_class.return_value = mock_instance

    tagger = TagApplier(gms_server="http://fake:8080", dry_run=False)
    actions = [Action(action="add_tag", tag="urn:li:tag:Compliant")]
    tagger.apply_actions("urn:li:dataset:(urn:li:dataPlatform:csv,x,PROD)", actions)

    assert mock_instance.emit.call_count == 1


@patch("rules_engine.tagger.DatahubRestEmitter")
def test_emit_failure_is_caught_and_returns_false(mock_emitter_class):
    mock_instance = MagicMock()
    mock_instance.emit.side_effect = ConnectionError("network down")
    mock_emitter_class.return_value = mock_instance

    tagger = TagApplier(gms_server="http://fake:8080", dry_run=False)
    actions = [Action(action="add_tag", tag="urn:li:tag:Compliant")]
    result = tagger.apply_actions("urn:li:dataset:(urn:li:dataPlatform:csv,x,PROD)", actions)

    assert result is False