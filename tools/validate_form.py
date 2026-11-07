#!/usr/bin/env python3
"""Check a ServiceTitan Form 2.0 JSON file against the import-safe recipe.

Usage:
    python3 tools/validate_form.py FORM.json [--allow-triggers]

Prints one line per finding. FAIL lines are rules a form must meet to
import and open; WARN lines are things worth a look. Exit code is 0 when
nothing failed, 1 when something did, 2 on bad arguments.

The rule numbers match the recipe in SYSTEM-PROMPT.md and KNOWLEDGE.md.
"""

import json
import re
import sys

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
FIELD_TYPES = {"Text", "Number", "Dropdown", "Checkbox", "Date", "Picture", "Signature", "Stoplight"}
MAX_SECTION_DEPTH = 2  # root = 0. Three-deep nesting produced a form the editor could not open.


class Report:
    def __init__(self):
        self.fails = []
        self.warns = []

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def label(unit):
    return unit.get("name") or unit.get("htmlContent", "")[:40] or unit.get("id", "?")


def check_whitespace(rep, where, value):
    if isinstance(value, str) and value != value.strip():
        rep.warn(f"leading or trailing space in {where}: {value!r}")


def walk(rep, unit, parent, depth, ids, fields):
    """Visit one unit and its children. Returns nothing; findings go to rep."""
    utype = unit.get("unitType")
    uid = unit.get("id")
    where = f"{utype or 'unit'} '{label(unit)}'"

    if not isinstance(uid, str) or not UUID_RE.match(uid):
        rep.fail(f"rule 7: {where} has id {uid!r}, not a lowercase UUID")
    elif uid in ids:
        rep.fail(f"rule 7: duplicate unit id {uid} ({where})")
    else:
        ids[uid] = unit

    check_whitespace(rep, f"name of {where}", unit.get("name"))

    if utype == "Section":
        if depth > MAX_SECTION_DEPTH:
            rep.warn(f"{where} is nested {depth} deep; three-deep sections have failed to open in the editor")
        children = unit.get("units")
        if not isinstance(children, list):
            rep.fail(f"{where} has no units list")
            return
        for child in children:
            if isinstance(child, dict):
                walk(rep, child, unit, depth + 1, ids, fields)
            else:
                rep.fail(f"{where} contains a non-object unit")
        return

    if utype == "Field":
        fields.append(unit)
        ftype = unit.get("fieldType")
        if ftype not in FIELD_TYPES:
            rep.fail(f"{where} has unknown fieldType {ftype!r} (use Picture, not Photo; no Toggle, Radio, Header, Paragraph)")
        elif ftype == "Number":
            rep.fail(f"rule 6: {where} is a Number field; capture numbers as Text")
        if parent is None or depth <= 1 or parent.get("canBeDuplicated") is not True:
            rep.fail(f"rule 4: {where} is not inside a Section with canBeDuplicated: true")
        for v in unit.get("values") or []:
            check_whitespace(rep, f"a value of {where}", v)
        for v in unit.get("refusalReasons") or []:
            check_whitespace(rep, f"a refusal reason of {where}", v)
        return

    if utype == "StaticElement":
        if unit.get("header") is not False:
            rep.fail(f"rule 5: {where} must have header: false")
        if not isinstance(unit.get("htmlContent"), str):
            rep.fail(f"{where} has no htmlContent string")
        return

    rep.fail(f"{where} has unknown unitType {utype!r}")


def check_rules(rep, dd, ids):
    rules = dd.get("rules")
    has_logic = dd.get("hasConditionalLogic")
    if rules is None:
        if has_logic is True:
            rep.warn("hasConditionalLogic is true but there is no rules key")
        return 0
    if not isinstance(rules, list):
        rep.fail("rules must be a list")
        return 0
    if rules and has_logic is not True:
        rep.fail("rules exist but hasConditionalLogic is not true")

    hidden_on_load, shown = set(), set()
    for i, rule in enumerate(rules, 1):
        if "condition" in rule and "conditions" not in rule:
            rep.fail(f"rule #{i}: uses singular 'condition'; the importer needs 'conditions' (a list)")
        conds = rule.get("conditions")
        if not isinstance(conds, list) or not conds:
            rep.fail(f"rule #{i}: conditions must be a non-empty list")
            conds = []
        actions = rule.get("actions")
        if not isinstance(actions, list) or not actions:
            rep.fail(f"rule #{i}: actions must be a non-empty list")
            actions = []
        if len(actions) > 1:
            rep.fail(f"rule #{i}: has {len(actions)} actions; use one action per rule, in Off/On pairs")
        if rule.get("whenMatch") not in ("All", "Any"):
            rep.fail(f"rule #{i}: whenMatch must be 'All' or 'Any'")

        sources = set()
        for c in conds:
            ctype = c.get("type")
            if ctype == "Compare":
                left = c.get("left")
                if left not in ids:
                    rep.fail(f"rule #{i}: Compare condition 'left' {left!r} is not a unit id in this form")
                else:
                    sources.add(left)
            elif ctype != "InitialLoad":
                rep.warn(f"rule #{i}: condition type {ctype!r} has no verified JSON shape; build it in the builder")

        for a in actions:
            target = a.get("unit")
            if a.get("type") != "Toggle" or a.get("mode") not in ("On", "Off"):
                rep.warn(f"rule #{i}: action {a.get('type')!r}/{a.get('mode')!r} has no verified JSON shape")
            if target not in ids:
                rep.fail(f"rule #{i}: action targets {target!r}, not a unit id in this form")
                continue
            if target in sources:
                rep.fail(f"rule #{i}: a unit toggles itself based on its own value (circular logic)")
            is_load = any(c.get("type") == "InitialLoad" for c in conds)
            if a.get("mode") == "Off" and is_load:
                hidden_on_load.add(target)
            if a.get("mode") == "On":
                shown.add(target)

    for uid in hidden_on_load - shown:
        rep.warn(f"unit {label(ids[uid])!r} is hidden on load and no rule ever shows it")
    return len(rules)


def validate(doc, allow_triggers):
    rep = Report()
    fd = doc.get("FormData")
    if not isinstance(fd, dict):
        rep.fail("top-level FormData object missing")
        return rep, 0, 0
    if doc.get("IsForm20") is not True:
        rep.fail("rule 8: IsForm20 must be true at the top level")
    triggers = doc.get("FormTriggers")
    if triggers is None:
        rep.fail("rule 10: FormTriggers missing; use an empty list")
    elif triggers and not allow_triggers:
        rep.fail("rule 10: FormTriggers is not empty; import with no triggers and add them in the builder (or pass --allow-triggers)")

    d = fd.get("definition")
    if not isinstance(d, dict):
        rep.fail("FormData.definition missing")
        return rep, 0, 0
    if d.get("published") is not True:
        rep.fail("rule 1: FormData.definition.published must be true")
    for key in ("createdOn", "modifiedOn"):
        if not isinstance(fd.get(key), str) or not fd.get(key):
            rep.fail(f"rule 2: FormData.{key} must be an ISO timestamp string")
    if not is_int(fd.get("id")):
        rep.fail("rule 3: FormData.id must be an integer")
    if not is_int(d.get("id")):
        rep.fail("rule 3: FormData.definition.id must be an integer")
    check_whitespace(rep, "FormData.name", fd.get("name"))

    dd = d.get("definition")
    root = dd.get("rootSection") if isinstance(dd, dict) else None
    if not isinstance(root, dict):
        rep.fail("FormData.definition.definition.rootSection missing")
        return rep, 0, 0
    if root.get("unitType") != "Section":
        rep.fail("rootSection.unitType must be 'Section'")

    ids, fields = {}, []
    walk(rep, root, None, 0, ids, fields)
    if not fields:
        rep.warn("the form has no fields")
    n_rules = check_rules(rep, dd, ids)
    return rep, len(ids), n_rules


def main(argv):
    flags = {a for a in argv if a.startswith("--")}
    paths = [a for a in argv if not a.startswith("--")]
    if len(paths) != 1 or flags - {"--allow-triggers"}:
        print(__doc__.strip())
        return 2
    try:
        with open(paths[0], encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"FAIL  not valid JSON: {exc}")
        return 1
    if not isinstance(doc, dict):
        print("FAIL  top level must be a JSON object")
        return 1

    rep, n_units, n_rules = validate(doc, "--allow-triggers" in flags)
    for msg in rep.fails:
        print(f"FAIL  {msg}")
    for msg in rep.warns:
        print(f"WARN  {msg}")
    status = "FAILED" if rep.fails else "OK"
    print(f"{status}: {n_units} units, {n_rules} rules, {len(rep.fails)} failures, {len(rep.warns)} warnings")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
