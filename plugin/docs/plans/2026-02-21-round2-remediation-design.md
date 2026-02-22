# Round 2 Remediation Design — Deep Research Engine Creator

**Date:** 2026-02-21
**Scope:** Fix all 14 issues identified in Claude Opus 4.6 code review
**Approach:** Sequential, dependency-safe execution (templates → presets → schemas → example → docs)
**Validation:** Cross-model review via Codex (GPT-5.3) after all fixes

---

## Issues Summary

| # | Severity | Issue | Primary File(s) |
|---|----------|-------|-----------------|
| 1 | CRITICAL | Agent template hardcodes `Max 3 iterations` | `agent-template.md.tmpl` |
| 2 | CRITICAL | All 15 preset agents missing `Edit` tool | 5 preset JSON files |
| 3 | HIGH | Example SKILL.md hand-written, not template-generated | `examples/.../SKILL.md` |
| 4 | HIGH | Spot-check verification has 3 conflicting definitions | `SKILL.md`, templates |
| 5 | HIGH | plugin-json.tmpl produces invalid empty email | `plugin-json.tmpl`, `SKILL.md` |
| 6 | MEDIUM | Extension mode can't override advanced settings | `extension-skill.md.tmpl` |
| 7 | MEDIUM | `explorationDepth` invisible to users | `SKILL.md` Section 8 |
| 8 | MEDIUM | "Four-phase" but lists 5 phases | `base-research-skill.md.tmpl` |
| 9 | MEDIUM | sources-command-template missing argument-hint | `sources-command-template.md.tmpl` |
| 10 | MEDIUM | `{{version}}` vs `{{engineVersion}}` mismatch | `readme-template.md.tmpl` |
| 11 | LOW | Remediation plan has no status tracking | `docs/remediation-plan.md` |
| 12 | LOW | Example timestamp is manually hardcoded | `examples/.../engine-config.json` |
| 13 | LOW | Publish script silent branch fallback | `scripts/publish-engine.sh` |
| 14 | LOW | No .gitignore for generated engines | New file needed |

---

## Section 1: Template Fixes (Issues #1, #5, #8, #9, #10)

### Issue #1 — agent-template.md.tmpl:62
Change `Max 3 iterations per research question` to `Max {{maxIterations}} iterations per research question`.

### Issue #5 — plugin-json.tmpl + SKILL.md
The template always emits `"email": "{{authorEmail}}"`. When email is empty, this produces `"email": ""` which fails the `format: "email"` schema validation.

**Fix:** Add a derivation rule in SKILL.md Generation Step 3: when `engineMeta.author.email` is empty or absent, omit the `"email"` key entirely from the generated plugin.json. The template itself stays as-is (it's a text template, not a conditional engine), but the generation protocol instruction must say: "If authorEmail is empty, remove the `\"email\": \"{{authorEmail}}\"` line from the output."

### Issue #8 — base-research-skill.md.tmpl + extension-skill.md.tmpl
Change "four-phase research system" to "five-phase research system" in both templates. Phase 0 (Tier Detection) is a distinct phase.

### Issue #9 — sources-command-template.md.tmpl
Add `argument-hint: ""` to YAML frontmatter for consistency with all other command templates.

### Issue #10 — readme-template.md.tmpl:68
Change `{{version}}` to `{{engineVersion}}` in the footer line to match the documented placeholder name.

**Files:** 5 template files

---

## Section 2: Preset Fixes (Issue #2)

### Issue #2 — All 5 preset files
Add `"Edit"` to every agent's tools array in all 5 presets (15 edits total).

Before: `["Read", "Write", "Bash", "WebSearch", "WebFetch", "Glob", "Grep"]`
After: `["Read", "Write", "Edit", "Bash", "WebSearch", "WebFetch", "Glob", "Grep"]`

**Files:** `legal-research.json`, `market-intelligence.json`, `academic-research.json`, `osint-investigation.json`, `technical-due-diligence.json`

---

## Section 3: Schema & SKILL.md Fixes (Issues #4, #6, #7)

### Issue #4 — Spot-check definition
Standardize the `{{verificationModeInstructions}}` derivation for `spot-check` in SKILL.md to:
> "Verify a random sample of HIGH-confidence citations (minimum 3 or 20% of HIGH citations, whichever is greater). Record verification results in Methodology_Log.md."

The wizard description (line 77) is a short user-facing summary and stays as-is.

### Issue #6 — Extension advanced settings
Add an **Advanced Configuration Override** section to `extension-skill.md.tmpl` after Custom Prompts:

```markdown
## Advanced Configuration Override

Override the base skill's advanced settings with engine-specific values:

- Max iterations per question: {{maxIterations}}
- Exploration depth: {{explorationDepth}}
- Token budgets: Planning {{planningBudget}}, Research {{researchBudget}}, Synthesis {{synthesisBudget}}, Reporting {{reportingBudget}}

If any of these values are omitted from the engine configuration, the base skill's defaults are inherited.
```

Add corresponding placeholder entries to the extension template's Placeholder Reference.

### Issue #7 — explorationDepth in wizard
Add `explorationDepth` to SKILL.md Section 8 (Advanced Configuration). When user says "yes" to advanced settings, ask: "Maximum depth for recursive web exploration from seed URLs (1-10, default 5)?"

**Files:** `SKILL.md`, `extension-skill.md.tmpl`

---

## Section 4: Example Regeneration (Issues #3, #12)

### Issue #3 — Regenerate example SKILL.md from template
Delete hand-written `examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`.

Regenerate by applying `base-research-skill.md.tmpl` with values from `examples/patent-intelligence-engine/engine-config.json`, using all placeholder derivation rules.

**Key changes vs hand-written version:**
- Confidence notation: `3/3, 2/3` → `●●●, ●●○` (template standard)
- Citation prefixes: `[PS-01], [PA-01], [IL-01]` → `[W-01], [E-01], [I-01]` (template standard)
- Remove `<!-- NOTE: manually customized -->` comment
- Agent iteration limits: correctly say "Max 4 iterations" (from config)

Also regenerate:
- `commands/research.md` from `command-template.md.tmpl`
- `commands/sources.md` from `sources-command-template.md.tmpl`
- All 3 agent files from `agent-template.md.tmpl`
- `README.md` from `readme-template.md.tmpl`

### Issue #12 — Example timestamp
Update `engine-config.json` `createdAt` to actual current time via bash.

**Files:** 8 files in `examples/patent-intelligence-engine/`

---

## Section 5: Command, Script & Doc Fixes (Issues #11, #13, #14)

### Issue #11 — Remediation plan status
Add `Status` column to `docs/remediation-plan.md`. Mark all original 13 findings as DONE. Add Round 2 findings section.

### Issue #13 — Publish script warning
Add warning message in `scripts/publish-engine.sh` when falling back to "main":
```bash
echo "WARNING: Could not detect default branch, falling back to 'main'" >&2
```

### Issue #14 — .gitignore
Create `deep-research-engine-creator/.gitignore` with `generated-engines/`.

**Files:** 3 files (remediation-plan.md, publish-engine.sh, new .gitignore)

---

## Section 6: Cross-Model Validation

1. Self-validate: verify regenerated example passes all `/test-engine` checks mentally
2. Codex review: send full diff for cross-model validation
3. Update remediation plan with Codex results

---

## Dependency Graph

```
Section 1 (Templates) ──→ Section 4 (Example Regeneration)
Section 2 (Presets)    ──→ (independent)
Section 3 (SKILL.md)  ──→ Section 4 (Example Regeneration)
Section 4 (Example)    ──→ Section 6 (Validation)
Section 5 (Docs/Scripts) → (independent)
```

## File Impact

| Category | Files | Edits |
|----------|-------|-------|
| Templates | 5 | 6 fixes |
| Presets | 5 | 15 tool additions |
| SKILL.md | 1 | 3 fixes |
| Example (regenerated) | 8 | Full regeneration |
| Docs/Scripts | 3 | 3 fixes |
| New files | 1 | .gitignore |
| **Total** | **~23 files** | **14 issues resolved** |
