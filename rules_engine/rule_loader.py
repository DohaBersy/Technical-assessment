"""
rule_loader.py

Reads the YAML rules file and converts it into Python objects.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import yaml


@dataclass
class Condition:
    property: str
    expected: Any


@dataclass
class Action:
    action: str
    tag: str


@dataclass
class Rule:
    name: str
    filter: Dict[str, Any]
    conditions: List[Condition] = field(default_factory=list)
    on_pass: List[Action] = field(default_factory=list)
    on_fail: List[Action] = field(default_factory=list)


def load_rules(path: str) -> List[Rule]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    rules = []
    for raw_rule in raw.get("rules", []):
        conditions = [
            Condition(property=c["property"], expected=c["expected"])
            for c in raw_rule.get("conditions", [])
        ]
        on_pass = [
            Action(action=a["action"], tag=a["tag"])
            for a in raw_rule.get("on_pass", [])
        ]
        on_fail = [
            Action(action=a["action"], tag=a["tag"])
            for a in raw_rule.get("on_fail", [])
        ]

        rules.append(
            Rule(
                name=raw_rule["name"],
                filter=raw_rule.get("filter", {}),
                conditions=conditions,
                on_pass=on_pass,
                on_fail=on_fail,
            )
        )

    return rules