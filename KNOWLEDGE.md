# ServiceTitan Form 2.0 — Reference

Reference file for the ServiceTitan Form Architect assistant (see `SYSTEM-PROMPT.md`). Most shapes here come from real Form 2.0 exports and imports on a working ServiceTitan account. Where a shape is not verified, or came from a fix rather than an export, this file says so. When this file and a general ServiceTitan guide disagree, trust this file, because it records what the importer actually accepted.

---

## 1. Native forms vs PDF forms

| | Native (Form 2.0) | PDF form |
|---|---|---|
| Stored as JSON | Yes | No |
| Conditional logic | Yes | No |
| Triggers | Yes | No |
| Smart fields | Yes | No |
| Can be AI-authored | Yes | No |
| Use when | You want logic, automation, or reportable data | The document is sign-and-file, with nothing to report on |

ServiceTitan has **no public API that creates or edits form templates**. The public Forms API only lists forms (name, active, published, has logic, has triggers) and reads submissions. Form templates are built and imported in **Settings → Forms**.

---

## 2. Full export shape

```json
{
  "FormData": {
    "id": 1,
    "name": "Service - Call Closeout",
    "active": true,
    "locked": false,
    "hide": false,
    "ownerTypes": ["Job"],
    "applyTagsTargets": ["Job"],
    "showOnMobile": true,
    "allowEmptyToPresent": false,
    "canDelete": false,
    "sendOnEvents": ["JobCompletion"],
    "dwyerBigBoardReport": false,
    "isAprysePdf": false,
    "createdOn": "2026-01-01T00:00:00.000Z",
    "modifiedOn": "2026-01-01T00:00:00.000Z",
    "definition": {
      "id": 1,
      "version": 1,
      "published": true,
      "printOptions": ["ShowBusinessUnitLogoOnPrintView"],
      "definition": {
        "rootSection": {
          "unitType": "Section",
          "canBeDuplicated": false,
          "name": "Root",
          "id": "<uuid>",
          "units": [ /* Sections only */ ]
        },
        "hasConditionalLogic": false
      }
    },
    "BusinessUnits": null,
    "ApplyTagTypes": null
  },
  "FormTriggers": [],
  "IsForm20": true,
  "IsLocked": false
}
```

Notes:
- The root section itself has `canBeDuplicated: false` and `name: "Root"`. Every section inside it has `canBeDuplicated: true`.
- `ownerTypes` seen in working forms: `Job`, `Call`, `Customer`, `Location`, `Equipment`. Default to `["Job"]`.
- `printOptions` also accepts `"SplitViewOnTwoColumns"`.
- `sendOnEvents: ["JobCompletion"]` controls post-submit email/print routing. Use `[]` unless someone wants that email or printout; otherwise it is noise.
- `FormTriggers` is a peer of `FormData`, not inside it.

---

## 3. Import-safe recipe

Rules 1, 2, 4 and 5 each caused a real failed import. Rules 3, 7 and 8 come from a vendor reference and cost nothing to follow. Rule 6 matched failed opens but was not proven to cause them. Rules 9 and 10 are safe defaults, not import requirements: forms with logic and triggers import fine when built correctly. A form that misses a required rule often imports, returns a new form ID, and then cannot be opened (blank screen, a 500 error, or `Cannot read properties of undefined (reading 'definition')`).

1. `definition.published: true`. A draft leaves no published snapshot, and the editor crashes. This is the most common cause.
2. `createdOn` and `modifiedOn` present as ISO strings.
3. `FormData.id` and `definition.id` are non-null integers. ServiceTitan overwrites them on import.
4. Every field is inside a Section with `canBeDuplicated: true`. No bare fields at the root.
5. Headings are `StaticElement` with `header: false` and `<h3>` HTML. Older hand-built forms use `header: true`, and those render in production, but that shape does not survive a fresh import.
6. No `fieldType: "Number"`. Capture numbers as `Text`.
7. UUIDs are lowercase hex only. A letter like g, h, n or p gives a 400 error: `Unit has invalid or empty Id: '0'`. Every ID must be unique across the whole form.
8. `IsForm20: true`. If the form has rules, `hasConditionalLogic: true` must also be set, or the rules never run.
9. A new form's first import is flat: `hasConditionalLogic: false` and no `rules` key. Add logic after the form opens cleanly. Revisions and forks of an exported form keep the rules they already have.
10. `FormTriggers: []` on every import. Rule 1 means the import arrives published, so a trigger in the JSON could launch an untested form for techs. Add triggers in the builder after testing.

Two more details from working forms: Checkbox fields carry `horizontalLayout: false`, and Signature fields always carry a `refusalReasons` array.

**Two different schemas.** The export/import format above (`rootSection`, `units`, `fieldType`, `name`, `isRequired`) is not the same as the format the ServiceTitan web app uses internally when you click Save (`FormItems`, `FormSections`, `ItemType`, `Required`). Never mix them.

---

## 4. Unit types

Three unit types exist inside `units[]`: `Section`, `Field`, `StaticElement`.

### Section

```json
{
  "unitType": "Section",
  "canBeDuplicated": true,
  "name": "Work Performed",
  "id": "<uuid>",
  "units": [ /* StaticElements and Fields */ ]
}
```

Sections can nest. Keep it to two levels on mobile. A hidden section is not submitted, and rules on hidden fields do not fire.

### StaticElement (headings and paragraphs)

```json
{
  "unitType": "StaticElement",
  "htmlContent": "<h3>Work Performed</h3>",
  "header": false,
  "isPrintViewOnly": false,
  "id": "<uuid>"
}
```

- Use `<h3>` for headings and `<p>`, `<strong>`, `<em>`, `<br>` for paragraphs. Keep HTML simple; ServiceTitan sanitizes it. No scripts, no external CSS.
- `isPrintViewOnly: true` hides the text from the tech on mobile and shows it on the printed copy. Good for legal or disclosure text.
- Mustache tokens such as `{{customer.name}}` do **not** work here. They print as literal text.

### Field skeleton

```json
{
  "fieldType": "Text",
  "unitType": "Field",
  "isRequired": false,
  "name": "WORK PERFORMED",
  "description": "",
  "id": "<uuid>"
}
```

`name` is the label the tech sees. `description` is help text (some companies put SKU codes here).

### Field types

| fieldType | Extra keys | Notes |
|---|---|---|
| `Text` | none | Also used for numbers in import-safe forms |
| `Number` | none | Avoid in imports (see recipe rule 6). No min/max/decimals observed |
| `Dropdown` | `values: ["A","B"]` | Flat string array. The label is the stored value |
| `Checkbox` | `values: [...]`, `horizontalLayout: false` | Multi-option. `values: ["Yes"]` makes a single toggle |
| `Date` | none | Use with `smartFieldTag: "TodayDate"` for auto date |
| `Picture` | none | Photo upload. `Photo` is not a valid type |
| `Signature` | `refusalReasons: [...]` | `name` is the full prompt the signer reads |
| `Stoplight` | `defaultValue: "Green"` | **Must** have `defaultValue`, or the form throws a 500 on open. This key came from that fix, not from an export, and no import-tested form has used Stoplight since. Values Red/Yellow/Green are unverified. Use a Dropdown unless the user wants a stoplight, and test it |

Types that do **not** exist: `Toggle`, `Radio`, `Header`, `Paragraph`, `Photo`.

### Examples

Dropdown:
```json
{
  "fieldType": "Dropdown",
  "values": ["Condenser", "Air Handler", "Rooftop", "Mini Split Indoor", "Mini Split Outdoor"],
  "unitType": "Field",
  "isRequired": true,
  "name": "UNIT TYPE",
  "description": "",
  "id": "<uuid>"
}
```

Checkbox, pass/fail/N/A:
```json
{
  "fieldType": "Checkbox",
  "values": ["Passed Inspection", "Failed Inspection - Attention Required", "N/A"],
  "horizontalLayout": false,
  "unitType": "Field",
  "isRequired": true,
  "name": "INSPECT ELECTRICAL CONNECTIONS",
  "description": "",
  "id": "<uuid>"
}
```

Checkbox as a toggle:
```json
{
  "fieldType": "Checkbox",
  "values": ["Yes"],
  "horizontalLayout": false,
  "unitType": "Field",
  "isRequired": false,
  "name": "PIPE USED",
  "description": "",
  "id": "<uuid>"
}
```

Signature:
```json
{
  "fieldType": "Signature",
  "refusalReasons": [
    "No one available to sign.",
    "I am not satisfied with the services received, and wish for an office member to contact me."
  ],
  "unitType": "Field",
  "isRequired": true,
  "name": "Your technician has completed the work above. Please sign to confirm the service was completed to your satisfaction.",
  "description": "",
  "id": "<uuid>"
}
```

Stoplight:
```json
{
  "fieldType": "Stoplight",
  "defaultValue": "Green",
  "unitType": "Field",
  "isRequired": false,
  "name": "OVERALL SYSTEM CONDITION",
  "description": "",
  "id": "<uuid>"
}
```

In submissions, a Checkbox `values` array becomes the selected options (`[]` if none). A blank Dropdown is `null`.

---

## 5. Smart fields

Smart fields fill themselves when the form opens. They are a `smartFieldTag` property on a field.

| smartFieldTag | fieldType | Fills with |
|---|---|---|
| `TodayDate` | Date | Today's date |
| `CustomerName` | Text | Customer name |
| `LocationAddress` | Text | Service address |
| `TechnicianName` | Text | Assigned technician |

```json
{
  "fieldType": "Text",
  "smartFieldTag": "CustomerName",
  "unitType": "Field",
  "isRequired": false,
  "name": "CUSTOMER NAME",
  "description": "",
  "id": "<uuid>"
}
```

- Tags are case-sensitive: `customerName` does not resolve.
- All four work on `Job`-owned forms. A tag resolves only when the form's owner type has that data.
- Set smart fields to `isRequired: false`.
- Other tags probably exist. Only these four are verified. To find more, add one in the builder and export the form.

---

## 6. Triggers

Two separate settings control a form's behavior.

**A. `FormData.sendOnEvents`**: what happens after submit (email or print). Verified value: `"JobCompletion"`.

**B. `FormTriggers[]`**: when ServiceTitan launches the form for the tech.

```json
{
  "Active": true,
  "Required": true,
  "MustCompleteFormWhenTriggered": false,
  "RequireEachTechToCompleteForm": false,
  "OwnerTypes": ["Job"],
  "JobEvent": "AfterArrival",
  "CustomerTypes": null,
  "BusinessUnitNames": ["HVAC Service"],
  "JobTypeNames": ["AC Tune-Up"],
  "EquipmentTypeNames": null,
  "ServiceNames": null,
  "OnAllAppointments": false,
  "Tags": null
}
```

| JobEvent | Fires when |
|---|---|
| `AfterArrival` | Tech taps Arrive on the appointment |
| `OnCompletionAfterInvoice` | Job is completed and the invoice is produced |

Other values probably exist; set them in the builder if needed.

Filters: each non-null filter narrows the trigger. `JobTypeNames`, `BusinessUnitNames` and `Tags` must match the account's names **exactly** (case and spaces). A typo silently disables the trigger. `OnAllAppointments: true` fires on every appointment, not only the first. Use it only for multi-day or multi-visit jobs; on a tune-up with a return visit it launches a second required form.

Guidance:
- One active trigger per form. Two matching triggers create two copies of the form on the same job.
- Delete inactive triggers instead of leaving `Active: false` entries around.
- `Required: true` blocks the tech from leaving the appointment without the form. Use it for safety and revenue forms only.
- Safety or setup checks: `AfterArrival`. Closeout, materials, signatures: `OnCompletionAfterInvoice`.
- Never put triggers in an import (recipe rule 10). This section exists so you can read and explain triggers in an exported form, and advise the user on what to pick in the builder.
- When a revised form replaces an old one, deactivate the old form or remove its trigger before turning on the new one. Importing a revision creates a second form, and two active matching triggers give techs two forms.

---

## 7. Conditional logic

Rules live in `definition.definition.rules[]`. When rules exist, set `hasConditionalLogic: true`.

### Verified rule shapes

Hide by default (runs when the form opens):
```json
{
  "whenMatch": "All",
  "actions": [
    { "type": "Toggle", "unit": "<section-or-field-uuid>", "mode": "Off", "isMet": false }
  ],
  "conditions": [ { "type": "InitialLoad" } ]
}
```

Show when a value is picked:
```json
{
  "whenMatch": "All",
  "actions": [
    { "type": "Toggle", "unit": "<section-or-field-uuid>", "mode": "On", "isMet": false }
  ],
  "conditions": [
    { "type": "Compare", "operator": "Equals", "left": "<source-field-uuid>", "right": "Gas Furnace" }
  ]
}
```

- `whenMatch` is `"All"` or `"Any"`.
- Use `conditions` (plural, an array). The singular `condition` object is broken.
- For a Checkbox source, only the single-option toggle is verified: `right: "Yes"` on a Checkbox with `values: ["Yes"]`. Rules on multi-option checkboxes are untested; build them in the builder and test in Preview. There is no confirmed way to fire on "unchecked".
- An "Is Filled" condition uses the property `field`, not `left`. Its exact JSON is otherwise unverified; build it in the builder and export it to copy the shape.
- Other operators (not equal, greater than, less than, is empty) exist in the builder. Their JSON operator strings are not verified. Build them in the builder.
- Hiding a required field releases it, because hidden fields do not block submit. There is no "make not required" action.

### Rule layout: one action per rule, in pairs

This is the shape of every working live form with logic that was read back on the source account. For each unit that starts hidden, emit two adjacent rules, one action each:

```json
[
  { "whenMatch": "All",
    "actions": [ { "type": "Toggle", "unit": "<unit-1>", "mode": "Off", "isMet": false } ],
    "conditions": [ { "type": "InitialLoad" } ] },
  { "whenMatch": "All",
    "actions": [ { "type": "Toggle", "unit": "<unit-1>", "mode": "On", "isMet": false } ],
    "conditions": [ { "type": "Compare", "operator": "Equals", "left": "<toggle-uuid>", "right": "Yes" } ] },
  { "whenMatch": "All",
    "actions": [ { "type": "Toggle", "unit": "<unit-2>", "mode": "Off", "isMet": false } ],
    "conditions": [ { "type": "InitialLoad" } ] },
  { "whenMatch": "All",
    "actions": [ { "type": "Toggle", "unit": "<unit-2>", "mode": "On", "isMet": false } ],
    "conditions": [ { "type": "Compare", "operator": "Equals", "left": "<toggle-uuid>", "right": "Yes" } ] }
]
```

Lower rules override higher rules, so each `On` rule wins over the `Off` rule just above it when its condition matches. Every hidden unit needs exactly one `Off` rule and one `On` rule. When a rule seems not to fire, check the rules below it.

### Rule traps

1. **Blank-value trap.** A blank field counts as "not equal to" every value. A rule like "hide if Refrigerant is not R-410A" fires on an empty field. Always pair "is not equal to" with "is filled".
2. **Circular logic.** Field X hides when Y = No, and Y hides when X = Yes. Both hide and the form freezes. A field must never hide itself, directly or through another field.
3. **One big InitialLoad rule.** A single InitialLoad rule with 27 Off actions made ServiceTitan's live renderer log "Cascade loop detected … aborting after 11 re-evaluations" on open, and the gated fields stayed visible. Never collect the hide actions into one rule. Use the pairs above.
4. **Merged rules.** Rules with up to 4 actions on one condition have worked. Larger merges are unproven. One vendor reference claims a hard maximum of 2 actions per rule; the pairwise layout avoids the question.

### Tags

Tagging a job from a form answer (for example, "Potential Replacement" when equipment is over 10 years old) is not verified as JSON. Tag rules need account-specific numeric tag IDs and break easily, so never hand-write them. The builder's **Apply Tags** setting has been used for a tag every submission should get. Whether it can apply a tag only on a certain answer is unverified; check in the builder and test it.

---

## 8. Proven building blocks

Most forms are built from these, in this order.

1. **Job context** (always first): a section with an `<h3>` title, then `TodayDate`, `CustomerName`, `LocationAddress`, `TechnicianName` smart fields.
2. **Inspection checklist**: one Checkbox per item with `["Passed Inspection", "Failed Inspection - Attention Required", "N/A"]`, plus a Text field for notes on failures and an optional Picture.
3. **Readings**: Text fields for measured values (temperatures, pressures, amps), named with the unit, for example `SUPPLY AIR TEMP (F)`.
4. **Materials used**: for long parts lists, a toggle Checkbox per category that reveals a Dropdown of sizes plus a quantity Text field. This replaces a wall of 200 checkboxes. It needs conditional logic (an Off/On rule pair for each hidden unit, see section 7), so build it as version 2. With many categories this means many rules; that is expected.
5. **Acknowledgment** (always last): a StaticElement stating what is being confirmed, then the Signature. No fields after the signature, because the mobile app treats the form as done once it is signed.

---

## 9. Style conventions

- **Form names:** `[Trade] [Phase] - [Task]`, for example `HVAC Service - Cooling Inspection`, `Plumbing Service - Closeout`. Title case, no leading `*`.
- **Field names:** short labels in ALL CAPS with no trailing punctuation: `TEST CONDENSATE PUMP`, not `Test condensate pump?`.
- **Values are permanent keys.** Dropdown and Checkbox strings are stored in submissions and used in rules and reports. Pick them carefully before first publish. Renaming one later orphans old data and breaks rules. `"Gas"` and `"gas"` are different, and so are `"Yes"` and `" Yes"`.
- **No leading or trailing spaces** in names, values, HTML, refusal reasons, or trigger names.
- **Refusal reasons:** reuse the same strings on every Signature across the account, so reports can roll them up.
- **Long lists:** past about 10 options, split into a category Dropdown plus a second Dropdown shown per category.
- **Other:** add a literal `"Other"` value and a Text field for the detail.

---

## 10. Self-audit prompts

Run these on every generated form before handing it back.

**Schema check.** Match every unit to a shape in section 4. List any unit that differs and say whether it is intended or a mistake.

**Import-safe check.** Confirm all ten rules in section 3.

**Logic check.** Walk every rule. Report: any rule with more than one action; any hidden unit without exactly one Off rule followed by one On rule; any "not equal to" without an "is filled" guard; any field whose rule hides itself directly or indirectly; any rule shadowed by a lower rule that was not intended; `hasConditionalLogic` matching whether rules exist.

**String check.** Spot-check names and values for stray spaces, case mismatches, and typos.

**Architecture review (optional).** Is the section order sensible? Do owner type and trigger fit the data? Are there fields that belong on another form or should not exist? Name the top three improvements.

---

## 11. Testing and publishing

1. Import the JSON in Settings → Forms. It arrives published (recipe rule 1) with no trigger (rule 10), so it does not launch for techs on its own.
2. Open the imported form in the builder. A new form ID alone does not prove the import worked.
3. Preview and walk every path: every Dropdown choice that drives logic, every toggle, the signature refusal path.
4. Only then add the trigger. If the form replaces an old one, deactivate the old form or remove its trigger first.
5. Never change a form a tech is filling out right now; they can lose their entries.
6. To add logic, triggers or tags after a clean import, make the change in the builder, test it, then export the form. That export is the new source of truth to paste back for revisions.

---

## 12. Lessons from real failures

| Symptom | Cause | Fix |
|---|---|---|
| Import returns an ID, form will not open, `reading 'definition'` error | Draft (`published: false`), missing timestamps, bare root fields, or `header: true` headings | Follow the import-safe recipe in section 3 |
| 500 error when opening a form with a Stoplight | Stoplight has no `defaultValue` | Add `"defaultValue": "Green"` |
| 400 `Unit has invalid or empty Id: '0'` | Non-hex letters in a UUID, or a missing ID | Lowercase hex UUIDs, one per unit |
| `{{customer.name}}` shows as literal text | Mustache tokens are not supported | Use a field with `smartFieldTag` |
| Cascade loop warnings, sections show when they should be hidden | Many actions in one rule, especially one big InitialLoad rule | Rebuild as one action per rule, in Off/On pairs |
| Section hides before the tech enters anything | Blank-value trap on "not equal to" | Add an "is filled" guard |
| Form freezes, fields vanish | Circular hide rules | Break the cycle |
| Trigger never fires | Job type or business unit name does not match exactly | Copy names from the account |
| Two copies of the form on one job | Two active triggers match, often an old form and its imported revision | Keep one active trigger; retire the old form |
