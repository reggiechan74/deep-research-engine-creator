# Research Protocol Reference — Patent Intelligence Engine

---

### Context Discipline

- Summarize sources immediately; per-source abstracts of 120 words or fewer; use IDs not full citations in chat
- Each agent chat response of 500 tokens or fewer; avoid meta narration
- Pass-based workflow: Pass 1 (initial sweep + notes), Pass 2 (synthesis of top claims/gaps), Pass 3 (targeted follow-up on gaps)
- Before each pass, reload only outline + top notes to manage context window
- Abort conditions: stop recursion when no new credible sources after 2 alternate branches or depth cap reached
- Note all stops and aborts in methodology log

---

## Search Query Generation Protocol

For each research question, generate a minimum of 4 queries before searching:

1. **Direct query** -- Core terminology and primary keywords for the question
2. **Synonym variant** -- Alternative terms, Intellectual property and patent landscape analysis-specific jargon, regional naming conventions
3. **Adversarial** -- "problems with [X]", "criticism of [X]", "failure of [X]", "[X] controversy"
4. **Expert-source targeted** -- `site:` filters for preferred authoritative domains

### Preferred Sites for Targeted Queries

1. patents.google.com
2. patft.uspto.gov
3. appft.uspto.gov
4. worldwide.espacenet.com
5. patentscope.wipo.int
6. epo.org
7. scholar.google.com
8. lens.org
9. ipo.gov.uk
10. cipo.ic.gc.ca

### Domain-Specific Search Templates

- **patent-number-lookup**: `"{patent_number}" patent claims abstract assignee site:{preferred_site}`
- **technology-landscape**: `"{technology_keyword}" patent landscape {cpc_class} filing trend {year_range}`
- **assignee-portfolio**: `"{assignee_name}" patent portfolio {technology_area} site:{preferred_site}`
- **classification-search**: `{cpc_code} OR {ipc_code} "{technology_keyword}" patent site:patents.google.com`
- **prior-art-search**: `"{invention_keyword}" prior art {technical_field} before:{priority_date}`
- **patent-family**: `"{patent_number}" family continuation divisional priority claim`
- **fto-risk-search**: `"{technology_keyword}" patent infringement freedom-to-operate {jurisdiction}`
- **patent-litigation**: `"{patent_number}" OR "{assignee_name}" patent litigation lawsuit infringement {year}`
- **patent-citation-network**: `"{patent_number}" cited-by references forward-citation backward-citation`

Additional queries may be generated for geographic variants, temporal slices, or
domain-specific databases as the topic demands. All queries must be logged to
`BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md` with timestamps and result counts.

---

## Iterative Search-Assess-Refine Protocol

Each Phase 2 agent follows this protocol for each assigned research question:

```
For each assigned research question:

  Pass 1 -- SEARCH: Execute diversified query set (4+ queries per question)
    - Apply Search Query Generation Protocol
    - Cast wide net across source types and credibility tiers
    - Record all queries and results in Methodology_Log_[AgentID].md

  Pass 2 -- ASSESS: Evaluate sufficiency
    - Are there 2+ independent sources for key claims?
    - Are there unanswered sub-questions?
    - Are there contradictions needing resolution?
    - Score current evidence against Confidence Scoring Framework

  Pass 3 -- REFINE (if gaps found):
    - Generate targeted follow-up queries addressing specific gaps
    - Execute search with refined queries
    - Assess again against sufficiency criteria
    - Max 4 iterations per research question

  ABORT when:
    - No new credible sources after 2 alternate query branches
    - Depth cap reached (4 iterations)
    - Topic branch determined to be outside engine scope

  LOG: Each iteration recorded in Methodology_Log_[AgentID].md with:
    - Queries executed (with engine/filters)
    - Results found (count, top sources)
    - Sufficiency assessment
    - Decision (continue, refine, or abort)
```

---

## Incremental Write Protocol

Write findings to disk after completing EACH research question — never accumulate
all findings for a single large write at the end.

After completing all Search-Assess-Refine passes for one research question:

1. APPEND new claims to `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
2. APPEND new sources to `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
3. APPEND the iteration log entry to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
4. APPEND discovered sources to `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`
5. OVERWRITE status JSON to `BASE_DIR/_status/[AgentID].json` (see Agent Status Protocol)
6. OVERWRITE claims status to `BASE_DIR/_status/[AgentID]_claims.json` with all claims
   discovered so far (cumulative, not per-question). Each claim is a JSON object:
   `{"id": "C-01", "text": "...", "confidence": "HIGH|MEDIUM|LOW|SPECULATIVE|null",
    "status": "pending|under_investigation|investigated", "sourceCount": 2,
    "question": "The originating research question"}`
   The file is a JSON array of these objects. On first write, create as `[]` then populate.

### File Creation Convention

- First write creates the file with a markdown header (e.g., `# Claims — [AgentID]`)
- Subsequent writes append a section separator (`---`) followed by the new content
- Files are always valid markdown at every intermediate point

### Context Release

After writing to disk, release detailed findings from working memory. Retain only:
- Claim IDs and confidence levels (e.g., "C-01 HIGH, C-02 MEDIUM")
- Source count and top source IDs
- Brief gap summary (one line)

This keeps the context window lean for subsequent research questions.

---

## Agent Status Protocol

Maintain a status file at `BASE_DIR/_status/[AgentID].json`. This file is OVERWRITTEN
(not appended) after each research question — it represents current state only.

The `_status/` directory is created by the orchestrator before agents are deployed.

### Status JSON Schema

```json
{
  "agentId": "[AgentID]",
  "engineId": "${ENGINE_ID}",
  "phase": 2,
  "status": "researching | writing | assessing | refining | complete | error",
  "currentAction": "Searching 'solid-state battery cathode 2024'",
  "activity": "searching | assessing | refining | writing | idle",
  "questions": [
    {
      "text": "The research question text",
      "status": "complete | active | pending",
      "startedAt": "ISO-8601 timestamp or null",
      "completedAt": "ISO-8601 timestamp or null",
      "durationMs": 102000
    }
  ],
  "webFetchesUsed": 4,
  "webFetchCap": 10,
  "claimsFound": 7,
  "sourcesCollected": 4,
  "iterationPass": 2,
  "maxIterations": 3,
  "errors": 0,
  "aborts": 0,
  "lastUpdated": "ISO-8601 timestamp"
}
```

### When to Write Status

- On agent start: status "researching", initialize questions array with all assigned
  questions (status "pending"), set first question to "active" with startedAt timestamp,
  activity "searching", errors 0, aborts 0
- Before each WebSearch call: update currentAction to the search query string
  (e.g., "Searching 'solid-state battery cathode patent 2024'")
- Before each WebFetch call: update currentAction to the URL being fetched
  (e.g., "Fetching https://patents.google.com/patent/US20240123456")
- After each Search pass: update activity to "searching"
- During assessment: update currentAction to what is being assessed
  (e.g., "Assessing claim C-03 against 2 sources")
- After each Assess pass: update activity to "assessing"
- During refinement: update currentAction to the refinement query
  (e.g., "Refining: searching for contradictory evidence on cathode materials")
- After each Refine pass: update activity to "refining"
- After writing files for a completed question: set the question's status to "complete"
  with completedAt and durationMs, set next question to "active" with startedAt,
  update claimsFound and sourcesCollected totals, activity "writing"
- On error: increment errors counter, status "error" if fatal, add "message" field
- On abort: increment aborts counter, log abort reason
- On completion of all questions: status "complete", activity "idle"

---

## Action Logging Protocol

Maintain an append-only action log at `BASE_DIR/_status/[AgentID]_log.json`.
This file is a JSON array. Append new entries after each significant action.

Log these events:
- Before starting each research question: type "start"
- After each WebSearch call: type "search" with query and result count
- After each WebFetch call: type "fetch" with URL and status (success/403_blocked/timeout/error)
- When a new claim is identified: type "claim" with ID, text, initial confidence
- When assessing a claim: type "assess" with claim ID and result
- After writing files to disk: type "write" with file list and counts
- After completing a research question: type "question_complete" with totals
- On error or abort: type "error" or "abort" with message/reason

Each entry includes a timestamp. The log is append-only — never overwrite or truncate.
On agent start, create the file with an empty array `[]`. Append by reading the current
array, pushing the new entry, and writing back.

**Size limit:** Cap the log at 500 entries per agent. If the array exceeds 500 entries,
drop the oldest entries to stay within the limit.

### Log Entry Schema

```json
{
  "type": "start | search | fetch | claim | assess | write | question_complete | error | abort",
  "timestamp": "ISO-8601 timestamp",
  // type-specific fields:
  // start: "question", "questionIndex"
  // search: "query", "engine", "resultCount"
  // fetch: "url", "status" (success/403_blocked/timeout/error)
  // claim: "claimId", "text", "confidence"
  // assess: "claimId", "result", "sourcesChecked"
  // write: "files", "claimsAdded", "sourcesAdded"
  // question_complete: "question", "questionIndex", "claimsTotal", "sourcesTotal"
  // error: "message"
  // abort: "reason"
}
```

---

## File Isolation Protocol

Each Phase 2 agent writes ONLY to its own files. No shared files during parallel research.

Per-agent output files:
- Claims: `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
- Bibliography: `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
- Methodology log: `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
- Sources: `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`
- Status: `BASE_DIR/_status/[AgentID].json`
- Claims status: `BASE_DIR/_status/[AgentID]_claims.json`
- Action log: `BASE_DIR/_status/[AgentID]_log.json`

Phase 3 synthesis consolidates per-agent files into unified versions.
Do NOT write to any file that another agent might also be writing to.

---

## WebFetch Cap

Cap total WebFetch calls at 10 per agent per research session.
Prioritize highest-credibility, most-accessible sources.
If a URL returns 403/blocked/paywall, note it in methodology log and move on — do not retry.

---

## Failure Recovery Protocol

```
- Agent timeout with no output       --> Log gap in methodology file; proceed with remaining agents
- Agent produces no useful findings   --> Record gap; synthesis agent prioritizes gap-closing
- All agents fail on research question --> Flag as UNRESEARCHABLE with explanation
- Cross-agent contradictions          --> Synthesis runs dedicated reconciliation sub-task
- User reports factual error          --> Trigger targeted verification mini-search
```

---

## Context Management Guidelines

Keep each agent's working set lean to maximize effective research within token budgets.

### Token Budgets (approximate)

```
Planning:       2500 tokens output max
Research:       18000 tokens output max (per agent, files + chat)
Synthesis:      12000 tokens output max
Reporting:      12000 tokens output max
VVC:            8000 tokens output max (verification + correction combined)
Provenance Audit: 5K tokens output max
```

### Context Efficiency Rules

- Always read the outline first; then load only the question-specific files/notes needed
- Use structured outputs (tables, bullet summaries, query logs) instead of long prose to minimize token footprint
- Chunk long-source notes: summarize per source immediately after reading; store extended quotes in per-source appendices if needed
- Use citation IDs (`[W-01]`, `[E-01]`, `[I-01]`) and refer to them instead of repeating full citations
- For long runs, operate in passes: (1) initial sweep + notes, (2) synthesis of top claims/gaps, (3) targeted follow-up on gaps, resetting context to only outline + top notes each pass
- When a document is large, capture a condensed abstract, key data points, and contradictions; keep raw text out of the main context
- Encourage tool-side chunked reading (page/section-level) and avoid reloading full documents once summarized
