"""
evaluator.py

The "brain" of the rules engine. Given one Rule and one dataset's info,
decides: does this rule apply? if so, does it pass or fail?

EXTENSIBILITY DESIGN (answers "how would you add a new rule type
without changing the core engine?"):

PROPERTY_CHECKS is a registry mapping a property name (e.g. "hasOwner")
to a small function that knows how to check it. To support a brand
new property, add ONE line to this dictionary -- evaluate_rule()
itself never needs to change.
"""
from dataclasses import dataclass
from typing import Optional, List

from rules_engine.rule_loader import Rule, Action


@dataclass
class DatasetInfo:
    """A simple representation of a dataset's known facts."""
    name: str
    platform: str
    has_owner: bool
    has_description: bool


PROPERTY_CHECKS = {
    "hasOwner": lambda dataset: dataset.has_owner,
    "hasDescription": lambda dataset: dataset.has_description,
}


def matches_filter(rule: Rule, dataset: DatasetInfo) -> bool:
    expected_platform = rule.filter.get("platform")
    if expected_platform is not None and dataset.platform != expected_platform:
        return False
    return True


def evaluate_rule(rule: Rule, dataset: DatasetInfo) -> Optional[List[Action]]:
    """
    Returns rule.on_pass, rule.on_fail, or None (rule doesn't apply here).
    """
    if not matches_filter(rule, dataset):
        return None

    for condition in rule.conditions:
        check_fn = PROPERTY_CHECKS.get(condition.property)
        if check_fn is None:
            return rule.on_fail

        actual_value = check_fn(dataset)
        if actual_value != condition.expected:
            return rule.on_fail

    return rule.on_pass