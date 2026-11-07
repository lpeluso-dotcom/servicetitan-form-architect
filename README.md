# ServiceTitan Form Architect

A system prompt, a reference file and a starter example that turn an AI assistant into a designer of ServiceTitan native forms (Form 2.0). You describe the form in plain English, or hand over a paper form, an SOP or a form exported from ServiceTitan. The assistant returns an outline, then import-ready JSON for **Settings → Forms**, then the steps to test it.

It works with any assistant that accepts custom instructions and reference files: ChatGPT (Custom GPT or Project), Claude (Project), Gemini (Gem), Microsoft Copilot (agent), or a coding agent such as Claude Code or Codex pointed at this repo. Nothing here depends on one vendor.

## What's in the repo

| File | Use |
|---|---|
| `SYSTEM-PROMPT.md` | The instructions. Paste everything below its `---` line into the assistant's instructions field. |
| `KNOWLEDGE.md` | The reference file: export shape, unit types, smart fields, triggers, conditional logic, and lessons from failed imports. Add it as a reference file. |
| `examples/service-call-closeout.json` | A sample closeout form the assistant copies structure from. Add it as a reference file. You can also import it into ServiceTitan as a test. |
| `examples/service-call-closeout-conditional.json` | Example with a tested show/hide rule: show the photo only when SYSTEM TYPE is Other. |
| `tools/validate_form.py` | Checks a form file against the import-safe rules. Needs Python 3 and nothing else. |

## Setup

1. Create an assistant with custom instructions on your platform.
2. Paste the block below the `---` line in `SYSTEM-PROMPT.md` into its instructions.
3. Add `KNOWLEDGE.md` and `examples/service-call-closeout.json` as reference files (knowledge, project files or attachments, depending on the platform).
4. If the platform can run code (ChatGPT's Code Interpreter, Claude's analysis tool, a coding agent), turn it on. The assistant uses it to generate UUIDs and check the JSON.
5. No assistant builder? In a plain chat, attach the two files, paste the instructions block as your first message, then describe the form.

Test prompt: "Outline a residential AC tune-up form that flags equipment over 10 years old."

## How to use it

1. Describe the form.
2. The assistant answers with an **outline only**. Review it and ask for changes.
3. Approve it ("Outline approved, build the JSON"). You get the JSON and a short audit.
4. If the assistant could not run code itself, check the file before importing:

   ```bash
   python3 tools/validate_form.py my-form.json
   ```

5. In ServiceTitan, import the file in **Settings → Forms**.
6. **Open the imported form in the builder.** If the import returns a new form but it won't open, the import failed; paste the error back into the chat.
7. Preview it and test every path. Then add the trigger in the builder.

## Good to know

- Version 1 of each form comes with no show/hide logic, because that is the shape that imports most reliably. Add logic in the ServiceTitan form builder once the form opens, or ask the assistant for a version 2.
- Imports arrive published but with no trigger, so nothing pops up for techs until you add one. Add the trigger in the builder after you've tested the form. Job type and business unit names have to match your account exactly.
- To revise a form you already have, export it from ServiceTitan and paste or upload the JSON into the chat. Importing the revision creates a second form, so deactivate the old one (or remove its trigger) before you turn on the new trigger.
- Don't change a form a tech is filling out right now.
- Most shapes in `KNOWLEDGE.md` come from real exports and imports on a working ServiceTitan account. Where a shape is unverified, the file says so.

## Conditional example and test status

The original starter JSON was imported through the ServiceTitan UI and opened successfully on November 6, 2026. A conditional rule was then added and published in the builder:

- Blank SYSTEM TYPE: PHOTO OF EQUIPMENT hidden.
- SYSTEM TYPE = Other: photo shown.
- Change SYSTEM TYPE to Heat Pump: photo hidden again.
- Clear the answer: photo remains hidden.

The rules were exported from ServiceTitan and are included in [the conditional example](examples/service-call-closeout-conditional.json). It uses an InitialLoad/Off rule followed by a Compare/Equals/On rule. Account-specific form IDs and timestamps have been replaced with generic placeholders; unit UUIDs and rule references are preserved.

**The exported conditional JSON has not been verified through a fresh reimport.** Browser upload automation blocked that additional test. Open and preview every imported form in your own account before adding triggers. Both examples have no triggers or automatic job-completion email events.

To download the whole package, use **Code → Download ZIP**. An IT person can also clone this repository and run the Python validator. The repository does not include credentials or provide access to a ServiceTitan account.

## Credits

Created by **Quality Service Company, LLC (QSC) and Luke Peluso**.

## Not affiliated with ServiceTitan

This is an independent, community-made method, not an official ServiceTitan tool. ServiceTitan is a trademark of its owner, and nothing here is endorsed by them. ServiceTitan can change its import format at any time, so check every import by opening the form.

## License

MIT License. Copyright (c) 2026 Quality Service Company, LLC and Luke Peluso. See [LICENSE](LICENSE).
