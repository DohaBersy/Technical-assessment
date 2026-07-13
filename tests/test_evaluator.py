"""
test_evaluator.py

Tests for evaluator.py -- pure logic, no network involved.
"""
from rules_engine.rule_loader import Rule, Condition, Action
from rules_engine.evaluator import evaluate_rule, matches_filter, DatasetInfo


def _owner_rule():
    return Rule(
        name="All datasets must have owners",
        filter={"platform": "csv"},
        conditions=[Condition(property="hasOwner", expected=True)],
        on_pass=[Action(action="add_tag", tag="urn:li:tag:Compliant")],
        on_fail=[Action(action="add_tag", tag="urn:li:tag:NeedsOwner")],
    )


def test_matches_filter_true_when_platform_matches():
    rule = _owner_rule()
    dataset = DatasetInfo(name="x", platform="csv", has_owner=True, has_description=True)
    assert matches_filter(rule, dataset) is True


def test_matches_filter_false_when_platform_differs():
    rule = _owner_rule()
    dataset = DatasetInfo(name="x", platform="snowflake", has_owner=True, has_description=True)
    assert matches_filter(rule, dataset) is False


def test_evaluate_rule_returns_on_pass_when_condition_met():
    rule = _owner_rule()
    dataset = DatasetInfo(name="x", platform="csv", has_owner=True, has_description=True)
    result = evaluate_rule(rule, dataset)
    assert result == rule.on_pass


def test_evaluate_rule_returns_on_fail_when_condition_not_met():
    rule = _owner_rule()
    dataset = DatasetInfo(name="x", platform="csv", has_owner=False, has_description=True)
    result = evaluate_rule(rule, dataset)
    assert result == rule.on_fail


def test_evaluate_rule_returns_none_when_filter_does_not_apply():
    rule = _owner_rule()
    dataset = DatasetInfo(name="x", platform="snowflake", has_owner=False, has_description=True)
    result = evaluate_rule(rule, dataset)
    assert result is None


def test_evaluate_rule_handles_unknown_property_as_fail():
    rule = Rule(
        name="Unknown property rule",
        filter={"platform": "csv"},
        conditions=[Condition(property="hasSomethingWeDontCheck", expected=True)],
        on_pass=[Action(action="add_tag", tag="urn:li:tag:Compliant")],
        on_fail=[Action(action="add_tag", tag="urn:li:tag:Unknown")],
    )
    dataset = DatasetInfo(name="x", platform="csv", has_owner=True, has_description=True)
    result = evaluate_rule(rule, dataset)
    assert result == rule.on_fail