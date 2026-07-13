"""
test_rule_loader.py

Tests for rule_loader.py -- pure logic, reads a YAML file we create
temporarily per test, no network involved.
"""
from rules_engine.rule_loader import load_rules


def _write_yaml(tmp_path, content: str):
    yaml_file = tmp_path / "rules.yaml"
    yaml_file.write_text(content)
    return str(yaml_file)


def test_loads_single_rule(tmp_path):
    content = """
rules:
  - name: "Test rule"
    filter:
      platform: csv
    conditions:
      - property: hasOwner
        expected: true
    on_pass:
      - action: add_tag
        tag: "urn:li:tag:Compliant"
    on_fail:
      - action: add_tag
        tag: "urn:li:tag:NeedsOwner"
"""
    path = _write_yaml(tmp_path, content)
    rules = load_rules(path)

    assert len(rules) == 1
    rule = rules[0]
    assert rule.name == "Test rule"
    assert rule.filter == {"platform": "csv"}
    assert len(rule.conditions) == 1
    assert rule.conditions[0].property == "hasOwner"
    assert rule.conditions[0].expected is True
    assert rule.on_pass[0].tag == "urn:li:tag:Compliant"
    assert rule.on_fail[0].tag == "urn:li:tag:NeedsOwner"


def test_loads_multiple_rules(tmp_path):
    content = """
rules:
  - name: "Rule A"
    filter:
      platform: csv
    conditions:
      - property: hasOwner
        expected: true
    on_pass:
      - action: add_tag
        tag: "urn:li:tag:Compliant"
    on_fail:
      - action: add_tag
        tag: "urn:li:tag:NeedsOwner"
  - name: "Rule B"
    filter:
      platform: csv
    conditions:
      - property: hasDescription
        expected: true
    on_pass:
      - action: add_tag
        tag: "urn:li:tag:Compliant"
    on_fail:
      - action: add_tag
        tag: "urn:li:tag:NeedsDescription"
"""
    path = _write_yaml(tmp_path, content)
    rules = load_rules(path)

    assert len(rules) == 2
    assert rules[0].name == "Rule A"
    assert rules[1].name == "Rule B"


def test_empty_rules_list(tmp_path):
    content = "rules: []"
    path = _write_yaml(tmp_path, content)
    rules = load_rules(path)
    assert rules == []