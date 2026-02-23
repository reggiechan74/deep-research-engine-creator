# Issue: Research Engine Context Contamination

**Date identified:** 2026-02-23
**Affected run:** `2026-02-22_192049_ET_german-international-schools-in-canada`
**Engine:** international-school-strategist v1.0.0
**Severity:** Design flaw — affects all research runs in project-aware environments

---

## What Happened

User ran `/international-school-strategist:research german international schools in canada` intending a standalone research request about the German school landscape across Canada.

The engine produced a 960-line comprehensive report that includes GIST-specific financial scenarios, tuition elasticity modeling, governance recommendations, intervention rankings, and a full implementation roadmap — none of which were requested. The output is a hybrid of "German schools in Canada" landscape research and a GIST survival strategy document.

## Root Cause

The research engine's Phase 1 planning agent inherited ambient project context from three sources that persist across `/clear` boundaries:

### 1. CLAUDE.md (project instructions, always loaded)

CLAUDE.md contains GIST-specific context:
```
- Current enrollment: 93 students (break-even: 113)
- Critical deadline: September 2026 board IB go/no-go vote
- Research corpus: 15 Markdown documents in 2026-02-19_205744_ET_gist-school-survival/
```

The planning agent read this and treated the new research as a continuation of the GIST project.

### 2. System-reminder context index (observation history)

The claude-mem observation index (~89 observations at the time) was injected into the session, containing detailed findings from the prior GIST survival research — financials, governance analysis, feedback loop models, etc.

### 3. Prior research files on disk

The `2026-02-19_205744_ET_gist-school-survival/` directory with 15 research documents was accessible to agents. The planning agent explicitly referenced it:

```yaml
relatedDocs:
  - 2026-02-19_205744_ET_gist-school-survival/gist-school-survival_Comprehensive_Report.md
  - 2026-02-19_205744_ET_gist-school-survival/gist-school-survival_Research_Outline.md
```

And in the outline body (line 24):
> "This framework builds on the February 19, 2026 comprehensive research project ('GIST School Survival'), which produced 15 documents, 125 claims, and 144 sources across 59 research tasks."

## Evidence of Scope Bloat

The research outline explicitly frames the new research as an extension:

> "The prior research treated GIST as an isolated case. This research reframes GIST within the pan-Canadian German international school ecosystem."

This reframing was not requested. The user asked for "german international schools in canada" — a standalone landscape question.

Sections in the final report that exceed the requested scope:
- Section 4: Financial Health Assessment (GIST-specific break-even analysis)
- Section 5: Scenario Analysis (3 GIST financial scenarios through 2029)
- Section 6: Real Estate & Facility Assessment (GIST lease risk)
- Section 7: Governance Capacity Review (GIST board skills)
- Section 9: Intervention Ranking (6 GIST-specific interventions)
- Section 11: Implementation Roadmap (4-phase GIST action plan)

These sections duplicate or extend the prior `gist-school-survival` report rather than answering the stated research question.

## Why /clear Didn't Help

A session boundary existed between the plugin installation work and the research request (prompt numbering reset to #1, new session S21). However, `/clear` only resets conversation context. It does NOT reset:

1. **CLAUDE.md** — loaded fresh every session from disk
2. **System-reminder context index** — observation history injected at session start
3. **File system access** — agents can read any file in the working directory

## Proposed Fix: Standalone Mode

The research engine needs a `--standalone` flag (or similar mechanism) that instructs the planning agent to:

1. **Ignore CLAUDE.md project context** — treat the research topic as domain-generic, not project-specific
2. **Do not read prior research files** — scope the research entirely from web sources and the user's topic string
3. **Do not reference the observation index** — prevent the planning agent from incorporating prior session findings
4. **Constrain the outline to the stated topic** — the planning agent should generate research questions strictly from the user's input, not from ambient project knowledge

### Design Considerations

- Default behavior should probably be `--standalone` (research is scoped to topic only), with `--project-aware` as the opt-in for extending prior research
- The `--approve` flag already exists and could serve as a gate to catch scope bloat before agents execute
- Agent prompts may need explicit instructions: "Do NOT read files outside BASE_DIR" and "Do NOT reference prior research unless the user's topic explicitly asks for it"
- The planning specialist's prompt should include: "Your research scope is LIMITED to: {topic}. Do not expand scope based on project context, CLAUDE.md, or files from prior research runs."

### Affected Components

| Component | File | Change Needed |
|-----------|------|---------------|
| Research command | `commands/research.md` | Add `--standalone` flag parsing |
| Skill file | `skills/international-school-strategist/SKILL.md` | Add scope-constraining instructions to Phase 1 planning |
| Agent prompts | `agents/*.md` | Add "do not reference prior research" guardrail |
| Engine creator | `deep-research-engine-creator` plugin | Propagate fix to all generated engines |

## Impact Assessment

- The contaminated report is still useful — it contains valid, VVC-verified research
- The unique value (national school census, provincial funding comparison, demographic data) is buried under duplicated GIST analysis
- ~40% of the report content duplicates or extends the prior research unnecessarily
- Research tokens were spent on work that had already been done

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
