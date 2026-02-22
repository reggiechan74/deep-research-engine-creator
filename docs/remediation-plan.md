# Deep Research Engine Creator — Remediation Plan

Cross-model review by GPT-5.3-codex identified 13 findings. Second-pass review of the initial remediation plan rated 6 fixes as PARTIAL and 1 as INSUFFICIENT. This v2 plan incorporates all feedback.

**Review scores:** 6 ADEQUATE, 5 PARTIAL → refined, 1 INSUFFICIENT → strengthened, 1 PARTIAL (LOW) → accepted.

---

## Finding 1 [CRITICAL]: plugin-json.tmpl requires fields not in schema/wizard — DONE

**Problem:** `plugin-json.tmpl` uses `{{engineDescription}}`, `{{authorName}}`, `{{authorEmail}}`, `{{keywords}}` — none exist in `engineMeta` schema or wizard.

**Fix:**
1. **Schema** (`engine-config-schema.json`): Add `description` (string), `author` (object with `name`/`email`, both optional), and `keywords` (string array) to `engineMeta`. None are required — wizard auto-derives defaults.
2. **SKILL.md wizard** (Section 1): After domain description, ask for engine description (default: auto-derive as "A domain-specialized research engine for {domain}"). Ask for author name and email (default: empty, populated from git config if available). Keywords auto-derived from domain + question types; shown for confirmation, not asked from scratch.
3. **Generation protocol** (SKILL.md Step 3): Document mapping: `engineDescription` ← `engineMeta.description`, `authorName` ← `engineMeta.author.name` (default: empty string), `authorEmail` ← `engineMeta.author.email` (default: empty string), `keywords` ← `engineMeta.keywords` joined as `"word1", "word2"` format.
4. **Presets**: Do NOT add `author` to presets (Codex review: presets are section defaults, not engineMeta owners). Add `keywords` arrays to all 5 presets since keywords ARE domain-specific.
5. **Example**: Add `description`, `author`, `keywords` to patent example `engine-config.json`.

**Files changed:**
- `skills/engine-creator/templates/engine-config-schema.json`
- `skills/engine-creator/SKILL.md` (Section 1 + Generation Step 3)
- `skills/engine-creator/domain-presets/*.json` (all 5)
- `examples/patent-intelligence-engine/engine-config.json`

---

## Finding 2 [HIGH]: Template placeholders exceed config model — DONE

**Problem:** Placeholders like `{{standardTierDescription}}`, `{{verificationModeInstructions}}`, `{{deadLinkInstructions}}` have no direct schema field — they're derived/expanded values.

**Fix:** Add a **Placeholder Derivation Rules** section to SKILL.md Generation Step 8 that explicitly documents how each derived placeholder is computed:

| Placeholder | Derivation |
|---|---|
| `{{quickTierDescription}}` | Build from `tiers.quick.agents` list: "Single-agent lookup using [agent role]" |
| `{{standardTierDescription}}` | Build from `tiers.standard.agents`: "[N] agents: [role1], [role2]" |
| `{{deepTierDescription}}` | Build from `tiers.deep.agents`: "Full pipeline with [N] agents" |
| `{{comprehensiveTierDescription}}` | Build from `tiers.comprehensive.agents` + followUpRound: "All [N] agents + follow-up round" |
| `{{agentSpecialization}}` | Concatenate all agent specialization strings, comma-separated |
| `{{verificationModeInstructions}}` | Expand based on `citationManagement.verificationMode`: none → "No verification", spot-check → "Verify random sample of HIGH-confidence citations", comprehensive → "Verify every cited source" |
| `{{deadLinkInstructions}}` | Expand based on `citationManagement.deadLinkHandling`: flag-only → "Mark dead links with [DEAD LINK] tag", archive-fallback → "Attempt Wayback Machine retrieval, fall back to flag", exclude-from-high → "Downgrade claims relying on unreachable sources" |
| `{{verificationReportConfig}}` | Expand from `citationManagement.verificationReport` enabled/scope settings |
| `{{operationalLessons}}` | Default: "No entries yet — update after first research run with `/post-mortem`." |

**Files changed:**
- `skills/engine-creator/SKILL.md` (new subsection under Generation Step 8)

---

## Finding 3 [HIGH]: Wizard section numbering inconsistent — DONE

**Problem:** README says 8 sections, but SKILL.md uses "Section 2.5" for Sample Questions, making 9 blocks. Commands reference both conventions.

**Fix:** Renumber to true 9 sections:
- Section 1: Domain Identity
- Section 2: Research Scope
- Section 3: Sample Research Questions (was 2.5)
- Section 4: Source Strategy (was 3)
- Section 5: Agent Pipeline (was 4)
- Section 6: Quality Framework (was 5)
- Section 7: Output Structure (was 6)
- Section 8: Advanced Configuration (was 7)
- Section 9: Custom Prompts (was 8)

Update all references: "Guide the user through **9 sections**", "Pre-fill sections 4-9 when preset selected".

**Files changed:**
- `skills/engine-creator/SKILL.md` (section headers and intro text)
- `commands/create-engine.md` (section list)
- `commands/update-engine.md` (multiSelect list)
- `README.md` (wizard sections table)

---

## Finding 4 [HIGH]: /update-engine regeneration matrix misses key files — DONE

**Problem:** Source strategy changes should also regenerate `commands/sources.md`; agent/tier changes should regenerate `commands/research.md`; metadata changes need path updates.

**Fix:** Expand the regeneration matrix:

| What Changed | Files to Regenerate |
|---|---|
| Source strategy | `skills/{name}/SKILL.md` + `commands/sources.md` |
| Quality framework, output structure, custom prompts | `skills/{name}/SKILL.md` |
| Agent pipeline (agents added/removed/modified) | Agent `.md` files in `agents/` + `skills/{name}/SKILL.md` + `commands/research.md` |
| Engine metadata (name, description, version, mode) | `.claude-plugin/plugin.json` + `README.md` + `commands/research.md` + `commands/sources.md` + skill dir rename if name changed |
| Mode change (self-contained ↔ extension) | Full regeneration of ALL files — SKILL.md template changes entirely, dependency check added/removed |
| Name change | Rename `skills/{old}/` → `skills/{new}/`, update all internal path references in commands and SKILL.md |
| Any change at all | `README.md` + `engine-config.json` (always regenerated) |

**Files changed:**
- `commands/update-engine.md` (section 6 regeneration table)

---

## Finding 5 [HIGH]: Example skill dir doesn't match generator convention — DONE

**Problem:** Generator says `skillDirName = engineMeta.name`, so patent engine should use `skills/patent-intelligence-engine/`. Example uses `skills/patent-research/`.

**Fix:** Rename example skill directory from `patent-research` to `patent-intelligence-engine`. Update `commands/research.md` reference to match.

**Files changed:**
- Rename: `examples/patent-intelligence-engine/skills/patent-research/` → `examples/patent-intelligence-engine/skills/patent-intelligence-engine/`
- `examples/patent-intelligence-engine/commands/research.md` (skill path reference)

---

## Finding 6 [HIGH]: Extension-mode dependency is brittle — DONE

**Problem:** Extension template hard-codes `.claude/commands/deep-research.md` path. Plugin-to-plugin dependency semantics aren't well-defined in Claude Code.

**Fix:**
1. Change dependency check to a **two-step ordered search**: first check `.claude/commands/deep-research.md`, then check for any skill file containing "deep-research" in `skills/*/SKILL.md`. Stop at the first match. If no match found, report the specific paths checked and fail.
2. Store the discovered base skill path as a `{{baseSkillPath}}` placeholder in the extension template so the generated file has a concrete, verified path — not a hard-coded guess.
3. In SKILL.md generation protocol (Step 8, extension mode): before template substitution, run the dependency check. If base skill not found, warn user and abort generation. Write the verified path into `{{baseSkillPath}}`.

**Files changed:**
- `skills/engine-creator/templates/extension-skill.md.tmpl` (dependency check section)
- `skills/engine-creator/SKILL.md` (generation Step 8, extension mode handling)

---

## Finding 7 [MEDIUM]: allowed-tools YAML format may be invalid — DONE

**Problem:** `command-template.md.tmpl` uses `allowed-tools: Task, WebFetch, ...` (comma-separated scalar) while other commands use array syntax `["Read", "Write"]`.

**Fix:** Change to YAML array syntax for consistency with all other command files.

**Files changed:**
- `skills/engine-creator/templates/command-template.md.tmpl` (line 4)

---

## Finding 8 [MEDIUM]: Schema lacks relational/structural constraints — DONE

**Problem:** Tier agent IDs aren't validated against declared agents. `citationManagement` and `verificationReport` lack `additionalProperties: false` and `required`.

**Fix:**
1. Add `additionalProperties: false` and `required` array to `citationManagement` and `verificationReport`.
2. Add a note in the schema description for `tierConfig.agents` items: "Must reference IDs from `agentPipeline.agents[].id`". (JSON Schema can't cross-reference arrays natively, but the description serves as documentation for the validator.)

**Files changed:**
- `skills/engine-creator/templates/engine-config-schema.json`

---

## Finding 9 [MEDIUM]: /test-engine doesn't validate against schema — DONE

**Problem:** Config validity check only verifies top-level keys exist, not full JSON Schema compliance.

**Fix:** Replace the shallow key check with a multi-level validation:
- 4a: Verify all required top-level keys (existing)
- 4b: Validate `engineMeta` has all required fields (name, displayName, domain, audience, version, mode, createdAt, createdBy) and `name` matches kebab-case pattern
- 4c: Verify each tier in `agentPipeline.tiers` only references agent IDs that exist in `agentPipeline.agents[].id` — this is the relational constraint JSON Schema can't enforce
- 4d: Validate `qualityFramework` has all required fields (confidenceScoring with 4 levels, minimumEvidence, validationRules, citationStandard)
- 4e: Validate `sourceStrategy.credibilityTiers` has all 5 tiers with non-empty `name` and `sources`
- 4f: Scan all `.md` files in the engine for unresolved `{{placeholder}}` patterns (regex: `\{\{[a-zA-Z]+\}\}`)
- 4g: If the engine config has `citationManagement`, verify `verificationMode` is one of the valid enum values

This provides deep structural validation without requiring a JSON Schema library (which is unavailable in Claude Code's runtime).

**Files changed:**
- `commands/test-engine.md` (Check 4 expanded)

---

## Finding 10 [MEDIUM]: Presets reference paywalled sources — DONE

**Problem:** Legal and market presets list Westlaw, LexisNexis, Gartner, etc. as Tier 1/2 sources — inaccessible to most users.

**Fix:** Restructure preset source tiers to lead with freely accessible sources. Move paywalled sources to secondary position with `(subscription required)` annotation:
- Legal: Lead with CanLII, PACER, Google Scholar Case Law. Note Westlaw/LexisNexis as `(subscription required)`.
- Market: Lead with SEC EDGAR, SEDAR+, Google Finance. Note Gartner/IBISWorld as `(subscription required)`.

**Files changed:**
- `skills/engine-creator/domain-presets/legal-research.json`
- `skills/engine-creator/domain-presets/market-intelligence.json`

---

## Finding 11 [LOW]: Timestamp instruction uses `TZ` with `date -u` — DONE

**Problem:** `TZ='America/New_York' date -u` outputs UTC regardless of TZ.

**Fix:** Remove `-u` flag and use `%:z` for RFC 3339 compliant offset: `TZ='America/New_York' date '+%Y-%m-%dT%H:%M:%S%:z'` (produces `-05:00` not `-0500`).

**Files changed:**
- `skills/engine-creator/SKILL.md` (Config Assembly step 3)

---

## Finding 12 [LOW]: Example metadata format drift — DONE

**Problem:** SKILL.md says `deep-research-engine-creator/1.0.0`, example uses `deep-research-engine-creator v1.0.0`.

**Fix:** Standardize on slash format: `deep-research-engine-creator/1.0.0`.

**Files changed:**
- `examples/patent-intelligence-engine/engine-config.json` (createdBy field)

---

## Finding 13 [LOW]: publish-engine.sh makes optimistic git assumptions — DONE

**Problem:** Assumes `main` branch. No idempotent update handling.

**Fix:**
1. Detect default branch: `git remote show origin | grep 'HEAD branch' | awk '{print $NF}'`
2. Check if engine directory already exists in marketplace — if so, prompt for confirmation before overwriting (default: yes with `--force` flag to skip). Preserve marketplace-side untracked files by using `rsync --delete` instead of `rm -rf + cp`.
3. Add `--force` flag to skip confirmation for CI usage.
4. Handle no-op commit: if `git diff --cached --quiet`, skip commit and report "No changes to publish."

**Files changed:**
- `scripts/publish-engine.sh`

---

## Dependency Graph

```
Finding 3 (renumber) ──→ Finding 4 (update-engine references section numbers)
Finding 1 (schema)   ──→ Finding 8 (schema constraints build on expanded schema)
Finding 8 (schema)   ──→ Finding 9 (test-engine checks mirror schema structure)
Finding 5 (example)  ──→ Finding 12 (metadata fix in same example file)
```

## Implementation Order (dependency-safe)

1. Finding 3 (HIGH) — Section renumbering FIRST (affects all doc references)
2. Finding 1 (CRITICAL) — Schema + wizard + presets + example
3. Finding 2 (HIGH) — Placeholder derivation rules
4. Finding 5 (HIGH) — Example skill dir rename
5. Finding 12 (LOW) — Metadata format (same example file, do while it's open)
6. Finding 4 (HIGH) — Update-engine regeneration matrix
7. Finding 6 (HIGH) — Extension dependency handling
8. Finding 8 (MEDIUM) — Schema constraints (builds on F1 schema additions)
9. Finding 7 (MEDIUM) — YAML format fix
10. Finding 9 (MEDIUM) — Test-engine validation expansion (uses F8 schema structure)
11. Finding 10 (MEDIUM) — Preset paywalled sources
12. Finding 11 (LOW) — Timestamp fix
13. Finding 13 (LOW) — Publish script

**Estimated files touched:** 20 unique files across 13 findings.

## Codex Plan Review Notes (v2 incorporated)

- F1: Do NOT add `author` to presets; presets are section defaults, not engineMeta
- F4: Added mode-change and name-change rows to regeneration matrix
- F6: Tightened dependency discovery with ordered two-step search and verified path injection
- F9: Expanded from 4 to 7 sub-checks; acknowledged JSON Schema runtime limitation
- F11: Changed `%z` to `%:z` for RFC 3339 compliance
- F13: Added no-op commit handling and rsync-based update semantics

---

## Round 2 Findings (Claude Opus 4.6 Review)

See `docs/plans/2026-02-21-round2-remediation-design.md` for full design.
See `docs/plans/2026-02-21-round2-remediation-plan.md` for implementation plan.

14 additional issues identified and remediated. Status: DONE.
