# Context Contamination Fix — Design Document

**Date:** 2026-02-23
**Issue:** `ISSUE_context-contamination.md`
**Approach:** Prompt-level guardrails (Approach 1)

---

## Problem

Research engines inherit ambient project context from three sources that persist across `/clear` boundaries: CLAUDE.md, claude-mem observation history, and prior research files on disk. The Phase 1 planning agent consumes this context and expands research scope beyond the user's stated topic.

The German International Schools run (`2026-02-22_192049_ET`) demonstrated the failure: a standalone landscape question was reframed as a GIST survival strategy extension, with ~40% of the report duplicating prior research.

## Design Decisions

1. **Standalone is the default.** All research runs scope strictly to the topic string unless `--extend` is passed.
2. **Approval gate is default for Standard+ tiers.** Phase 1 outline is presented for user review before Phase 2 agents execute. `--no-approve` is the explicit opt-out.
3. **Prompt-level enforcement, not system-level isolation.** The planning agent cannot un-see CLAUDE.md or system-reminders. The fix instructs it to ignore project context. This is soft enforcement — the `--approve` gate is the safety net.
4. **No schema changes.** No new engine config fields. The fix lives entirely in templates and derivation rules.

## Flag System

### New Flags

| Flag | Effect |
|------|--------|
| `--extend` | Opt into project-aware mode. Planning agent may read prior research, reference CLAUDE.md context, and build on previous findings. |
| `--no-approve` | Skip the outline approval gate (Standard+ tiers). For automation or power users who trust engine scoping. |

### Modified Behavior

| Flag | Current | New |
|------|---------|-----|
| `--approve` | Opt-in for Standard/Deep | Default for Standard/Deep/Comprehensive (annotated as default in usage) |
| (no flags) | Project-aware, no approval gate | Standalone mode, approval gate active |

### Phase 0 Flag Parsing (additions)

```
- If `--extend` is present, set CONTEXT_MODE to "extend" (project-aware)
- Otherwise, set CONTEXT_MODE to "standalone" (default)
- If `--no-approve` is present, skip approval gate
```

## Scope Discipline Block

New instruction block injected into Phase 1 planning agent prompt, conditional on CONTEXT_MODE.

### Standalone Mode (default)

```
### Scope Discipline

Your research scope is LIMITED to the user's stated topic: "{topic}"

- Do NOT read files outside BASE_DIR
- Do NOT reference prior research runs, their files, or their findings
- Do NOT incorporate project context from CLAUDE.md into research scope
- Do NOT use observation history or session context to expand the topic
- Generate ALL research questions strictly from the user's topic string
  and your domain expertise in {{domain}}
- If the topic is ambiguous, interpret it as a general domain question —
  do not assume it relates to any specific project or prior work
- Every section in the outline must map directly to the stated topic.
  Remove any section that requires project-specific knowledge to justify.
```

### Extend Mode (`--extend`)

```
### Scope Discipline

This research EXTENDS prior work in this project. You may:

- Read prior research files in the working directory for context
- Reference project context from CLAUDE.md to inform research scope
- Build on findings from previous research runs
- Frame new research questions that deepen or broaden prior findings

Clearly mark which sections build on prior work vs. new investigation.
```

## Approval Gate

### Current

```
- If `--comprehensive` OR `--approve`: Present outline to user for approval
```

### New

```
- If `--quick`: No approval gate
- If `--no-approve` is present: Skip approval gate
- Otherwise (Standard/Deep/Comprehensive): Present outline to user for approval before proceeding to Phase 2
```

## File Change Map

| File | Changes |
|------|---------|
| `templates/base-research-skill.md.tmpl` | Usage lines, Phase 0 flag parsing, Phase 1 scope discipline block insertion, approval gate logic inversion |
| `templates/command-template.md.tmpl` | argument-hint, usage lines, Phase 0 flag parsing |
| `SKILL.md` (engine-creator) | Add `{{scopeDisciplineBlock}}` derivation rule to placeholder table |
| `docs/ISSUE_context-contamination.md` | Add Resolution section |

### No Changes

- `templates/agent-template.md.tmpl` — agents read the outline (already scoped by Phase 1)
- Engine config schema — no new config fields (YAGNI)

## Derivation Rule

New placeholder `{{scopeDisciplineBlock}}` in engine-creator SKILL.md:

> Always generates both standalone and extend conditional blocks. The template includes both; Phase 0 selects which applies based on CONTEXT_MODE derived from `--extend` flag presence.

Since the template is static markdown (not runtime code), both blocks are written into the template with conditional prose: "If CONTEXT_MODE is standalone: [standalone block]. If CONTEXT_MODE is extend: [extend block]."
