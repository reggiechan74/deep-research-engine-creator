# Context Contamination Fix — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add scope discipline guardrails to research engine templates so Phase 1 planning agents don't consume ambient project context, and make the approval gate default for Standard+ tiers.

**Architecture:** Prompt-level guardrails injected via a new `{{scopeDisciplineBlock}}` placeholder. Two new flags (`--extend`, `--no-approve`) modify Phase 0 behavior. All changes propagate to future generated engines via the engine-creator's derivation rules.

**Tech Stack:** Markdown templates (no code — documentation-only repository)

---

### Task 1: Add scope discipline and new flags to base-research-skill.md.tmpl

**Files:**
- Modify: `deep-research-engine-creator/plugin/skills/engine-creator/templates/base-research-skill.md.tmpl`

**Step 1: Add new flags to Usage section (lines 17-23)**

Find this block:

```markdown
- `/research [topic] --outline-only` -- Planning phase only (produces outline, then stops)
- `/research [topic] --approve` -- Pause for user approval after Phase 1 before proceeding
```

Replace with:

```markdown
- `/research [topic] --outline-only` -- Planning phase only (produces outline, then stops)
- `/research [topic] --approve` -- Pause for user approval after Phase 1 (default for Standard+ tiers)
- `/research [topic] --no-approve` -- Skip outline approval gate (for automation or fast iteration)
- `/research [topic] --extend` -- Build on prior research in this project (default: standalone)
```

**Step 2: Add new flag parsing to Phase 0 (lines 48-56)**

Find this block:

```markdown
Parse tier from `$ARGUMENTS`:

- If `--quick` is present, set tier to **Quick**
- If `--standard` is present, set tier to **Standard**
- If `--deep` is present, set tier to **Deep**
- If `--comprehensive` is present, set tier to **Comprehensive**
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after Phase 1 for user approval
- Otherwise, default to **Standard** tier
```

Replace with:

```markdown
Parse tier from `$ARGUMENTS`:

- If `--quick` is present, set tier to **Quick**
- If `--standard` is present, set tier to **Standard**
- If `--deep` is present, set tier to **Deep**
- If `--comprehensive` is present, set tier to **Comprehensive**
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after Phase 1 for user approval
- If `--no-approve` is present, skip outline approval gate
- If `--extend` is present, set CONTEXT_MODE to **extend** (project-aware)
- Otherwise, set CONTEXT_MODE to **standalone** (default)
- Otherwise, default to **Standard** tier
```

**Step 3: Insert scope discipline block into Phase 1 planning instructions (after line 270)**

Find:

```markdown
### Phase 1: Strategic Research Planning

Deploy **research-planning-specialist** with instructions to:

- Analyze {{domain}} research topic complexity, scope, and domain requirements
```

Replace with:

```markdown
### Phase 1: Strategic Research Planning

Deploy **research-planning-specialist** with instructions to:

{{scopeDisciplineBlock}}

- Analyze {{domain}} research topic complexity, scope, and domain requirements
```

**Step 4: Update approval gate logic (lines 291-293)**

Find:

```markdown
**User Gates:**
- If `--outline-only`: Stop here. Present outline summary and exit.
- If `--comprehensive` OR `--approve`: Present outline to user for approval before proceeding to Phase 2.
```

Replace with:

```markdown
**User Gates:**
- If `--outline-only`: Stop here. Present outline summary and exit.
- If `--quick`: No approval gate — proceed directly to execution.
- If `--no-approve`: Skip approval gate — proceed directly to Phase 2.
- Otherwise (Standard/Deep/Comprehensive): Present outline to user for approval before proceeding to Phase 2.
```

**Step 5: Add scope discipline placeholders to Placeholder Reference section (after line 686)**

Find:

```markdown
### Operational
- `{{operationalLessons}}` -- accumulated post-mortem findings from past research runs
```

Replace with:

```markdown
### Scope & Context Isolation
- `{{scopeDisciplineBlock}}` -- conditional scope discipline instructions for Phase 1 planning agent, varies by CONTEXT_MODE (standalone vs. extend)

### Operational
- `{{operationalLessons}}` -- accumulated post-mortem findings from past research runs
```

**Step 6: Verify the edit**

Run: `grep -n "scopeDisciplineBlock\|--extend\|--no-approve\|CONTEXT_MODE" deep-research-engine-creator/plugin/skills/engine-creator/templates/base-research-skill.md.tmpl`

Expected: 6 matches — usage line, Phase 0 parsing (2 lines), Phase 1 insertion, placeholder reference, and the `--no-approve` usage line.

**Step 7: Commit**

```bash
git add deep-research-engine-creator/plugin/skills/engine-creator/templates/base-research-skill.md.tmpl
git commit -m "feat(engine-templates): add scope discipline block and context isolation flags to SKILL template

Adds --extend flag for project-aware mode (opt-in), --no-approve to skip approval gate,
{{scopeDisciplineBlock}} placeholder in Phase 1, and inverts approval gate to default-on for Standard+ tiers.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Add new flags to command-template.md.tmpl

**Files:**
- Modify: `deep-research-engine-creator/plugin/skills/engine-creator/templates/command-template.md.tmpl`

**Step 1: Update argument-hint (line 3)**

Find:

```markdown
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--outline-only]"
```

Replace with:

```markdown
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--no-approve] [--outline-only] [--extend]"
```

**Step 2: Update Usage section (lines 15-20)**

Find:

```markdown
- `/research [topic] --approve` -- Pause for user approval after planning phase
- `/research [topic] --outline-only` -- Stop after planning phase (outline only)
```

Replace with:

```markdown
- `/research [topic] --approve` -- Pause for user approval after planning phase (default for Standard+ tiers)
- `/research [topic] --no-approve` -- Skip outline approval gate (for automation or fast iteration)
- `/research [topic] --outline-only` -- Stop after planning phase (outline only)
- `/research [topic] --extend` -- Build on prior research in this project (default: standalone)
```

**Step 3: Update Phase 0 flag parsing (lines 24-32)**

Find:

```markdown
Parse tier from `$ARGUMENTS`:
- If `--quick` is present, set tier to Quick
- If `--standard` is present, set tier to Standard
- If `--deep` is present, set tier to Deep
- If `--comprehensive` is present, set tier to Comprehensive
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after planning phase for user approval
- Otherwise, default to Standard tier
- Strip flag tokens from `$ARGUMENTS` to derive the research topic
```

Replace with:

```markdown
Parse tier from `$ARGUMENTS`:
- If `--quick` is present, set tier to Quick
- If `--standard` is present, set tier to Standard
- If `--deep` is present, set tier to Deep
- If `--comprehensive` is present, set tier to Comprehensive
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after planning phase for user approval
- If `--no-approve` is present, skip outline approval gate
- If `--extend` is present, set CONTEXT_MODE to **extend** (project-aware)
- Otherwise, set CONTEXT_MODE to **standalone** (default)
- Otherwise, default to Standard tier
- Strip flag tokens from `$ARGUMENTS` to derive the research topic
```

**Step 4: Verify the edit**

Run: `grep -n "extend\|no-approve\|CONTEXT_MODE" deep-research-engine-creator/plugin/skills/engine-creator/templates/command-template.md.tmpl`

Expected: 6 matches across argument-hint, usage, and Phase 0 parsing.

**Step 5: Commit**

```bash
git add deep-research-engine-creator/plugin/skills/engine-creator/templates/command-template.md.tmpl
git commit -m "feat(engine-templates): add context isolation flags to command template

Mirrors --extend, --no-approve, and CONTEXT_MODE parsing from the SKILL template
into the research command template.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Add scopeDisciplineBlock derivation rule to engine-creator SKILL.md

**Files:**
- Modify: `deep-research-engine-creator/plugin/skills/engine-creator/SKILL.md`

**Step 1: Add the derivation rule to the Placeholder Derivation Rules table**

Find the last existing derivation rule row (line 270):

```markdown
| `{{vvcReadmeSection}}` | If VVC enabled: generate "## Verification, Validation & Correction (VVC)" section. Lead with the key distinction: every research tool cites sources, but a citation is just a URL -- it doesn't mean the AI read the source correctly. VVC goes further by extracting claims, re-fetching sources, and verifying both source credibility and accurate representation. Then describe claim types, verification scope, and tier behavior; otherwise: empty string |
```

Insert after it:

```markdown
| `{{scopeDisciplineBlock}}` | Always generate the following conditional block (both modes included in template output): "**If CONTEXT_MODE is standalone (default — no `--extend` flag):**\n\n### Scope Discipline\n\nYour research scope is LIMITED to the user's stated topic.\n\n- Do NOT read files outside BASE_DIR\n- Do NOT reference prior research runs, their files, or their findings\n- Do NOT incorporate project context from CLAUDE.md into research scope\n- Do NOT use observation history or session context to expand the topic\n- Generate ALL research questions strictly from the user's topic string and your domain expertise in {domain}\n- If the topic is ambiguous, interpret it as a general domain question — do not assume it relates to any specific project or prior work\n- Every section in the outline must map directly to the stated topic. Remove any section that requires project-specific knowledge to justify.\n\n**If CONTEXT_MODE is extend (`--extend` flag present):**\n\n### Scope Discipline\n\nThis research EXTENDS prior work in this project. You may:\n\n- Read prior research files in the working directory for context\n- Reference project context from CLAUDE.md to inform research scope\n- Build on findings from previous research runs\n- Frame new research questions that deepen or broaden prior findings\n\nClearly mark which sections build on prior work vs. new investigation." |
```

**Step 2: Verify the edit**

Run: `grep -n "scopeDisciplineBlock" deep-research-engine-creator/plugin/skills/engine-creator/SKILL.md`

Expected: 1 match in the derivation table.

**Step 3: Commit**

```bash
git add deep-research-engine-creator/plugin/skills/engine-creator/SKILL.md
git commit -m "feat(engine-creator): add scopeDisciplineBlock derivation rule

New placeholder generates conditional scope discipline instructions for
Phase 1 planning agents — standalone (default) constrains to topic only,
extend allows building on prior research.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Add Resolution section to ISSUE_context-contamination.md

**Files:**
- Modify: `deep-research-engine-creator/plugin/docs/ISSUE_context-contamination.md`

**Step 1: Append Resolution section after the Impact Assessment (line 105)**

Add at end of file:

```markdown
## Resolution

**Implemented:** 2026-02-23
**Design doc:** `docs/plans/2026-02-23-context-contamination-fix-design.md`

### Changes Made

1. **Standalone mode is now the default.** All research runs scope strictly to the user's topic string. The Phase 1 planning agent receives explicit scope discipline instructions to ignore CLAUDE.md, observation history, and prior research files.

2. **`--extend` flag for project-aware mode.** Users who want to build on prior research must explicitly opt in with `--extend`. This reverses the prior default (project-aware) to prevent accidental scope contamination.

3. **Approval gate defaults to ON for Standard+ tiers.** The Phase 1 outline is presented for user review before Phase 2 agents execute. Previously, only `--comprehensive` and explicit `--approve` triggered this gate. Users can skip with `--no-approve`.

4. **Scope discipline block in Phase 1 prompt.** New `{{scopeDisciplineBlock}}` placeholder in the SKILL template injects conditional instructions into the planning agent prompt based on CONTEXT_MODE.

5. **Propagated to engine-creator.** The derivation rule for `{{scopeDisciplineBlock}}` ensures all future generated engines include these guardrails.

### Limitations

- **Soft enforcement only.** The planning agent can still *see* CLAUDE.md and system-reminders in its context window — it is instructed to ignore them, not isolated from them.
- **Existing engines not auto-patched.** Engines generated before this fix must be manually updated or regenerated.
- **`--approve` gate relies on user judgment.** If the user approves a contaminated outline, downstream agents will still execute the bloated scope.
```

**Step 2: Commit**

```bash
git add deep-research-engine-creator/plugin/docs/ISSUE_context-contamination.md
git commit -m "docs: add resolution section to context contamination issue

Documents the implemented fix: standalone default, --extend opt-in,
approval gate inversion, and scope discipline block. Notes limitations.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Final verification

**Step 1: Verify all placeholders are consistent**

Run: `grep -rn "scopeDisciplineBlock\|CONTEXT_MODE\|--extend\|--no-approve" deep-research-engine-creator/plugin/skills/engine-creator/`

Expected matches:
- `templates/base-research-skill.md.tmpl`: ~7 matches (usage, Phase 0, Phase 1, placeholder ref)
- `templates/command-template.md.tmpl`: ~6 matches (argument-hint, usage, Phase 0)
- `SKILL.md`: ~1 match (derivation rule)

**Step 2: Verify no orphaned references**

Run: `grep -rn "scopeDisciplineBlock" deep-research-engine-creator/plugin/ | wc -l`

Expected: 3 files (base-research-skill.md.tmpl, SKILL.md, and the design doc)

**Step 3: Verify approval gate logic is consistent between templates**

Read the Phase 0 sections of both templates and confirm the flag parsing order and logic match.

**Step 4: Commit the design doc (if not already committed)**

```bash
git add deep-research-engine-creator/plugin/docs/plans/2026-02-23-context-contamination-fix-design.md
git commit -m "docs: add context contamination fix design document

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```
