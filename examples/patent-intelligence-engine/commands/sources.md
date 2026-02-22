---
description: "Display the Patent Intelligence Engine's configured source hierarchy and search strategy"
allowed-tools: ["Read"]
---

# Patent Intelligence Engine -- Source Configuration

Display the source credibility hierarchy, preferred sites, excluded sources, search templates, and filters configured for this patent intelligence research engine.

## Source Credibility Hierarchy

| Tier | Name | Sources |
|------|------|---------|
| 1 | Official Patent Databases | USPTO PATFT and AppFT (patents.google.com, patft.uspto.gov); European Patent Office (EPO) Espacenet and Global Patent Index; WIPO PATENTSCOPE and PCT publications; Google Patents with full-text search and classification browsing; National patent office databases (JPO J-PlatPat, KIPO KIPRIS, CNIPA, CIPO) |
| 2 | Patent Analytics & Legal Sources | Patent prosecution histories (USPTO PAIR, EPO Register); Patent litigation databases (PACER, Docket Navigator, Lex Machina); Published patent examiner search reports and office actions; PTAB decisions and inter partes review proceedings; Patent classification systems (CPC, IPC) official documentation |
| 3 | Technical & Scientific Literature | Peer-reviewed technical journals related to the patent domain; Conference proceedings from major technical conferences; Standards body publications (IEEE, ISO, ASTM) relevant to patent claims; Published doctoral dissertations and technical reports; ArXiv preprints and academic working papers with disclosed methodology |
| 4 | Industry & Commercial Sources | Patent analytics platform reports (PatSnap, Orbit Intelligence, Innography); Industry news and trade publications covering patent activity; Company press releases and investor presentations mentioning IP; Technology blog posts from recognized patent attorneys and IP professionals; Patent valuation and licensing market reports |
| 5 | Unreliable / Unverified | Anonymous forum posts and unattributed patent commentary; Marketing materials claiming patent-pending status without application numbers; AI-generated patent summaries without verification against original filings; Unverified patent ownership claims on company websites; Social media discussions about patent disputes without case citations |

## Preferred Sites

The following domains are prioritized during web searches:

- `patents.google.com` -- Google Patents (full-text search, classification browsing, family links)
- `patft.uspto.gov` -- USPTO granted patents full-text database
- `appft.uspto.gov` -- USPTO published applications full-text database
- `worldwide.espacenet.com` -- EPO Espacenet worldwide patent search
- `patentscope.wipo.int` -- WIPO PATENTSCOPE international patent search
- `epo.org` -- European Patent Office official site and register
- `scholar.google.com` -- Google Scholar for non-patent literature and prior art
- `lens.org` -- The Lens open patent and scholarly search
- `ipo.gov.uk` -- UK Intellectual Property Office
- `cipo.ic.gc.ca` -- Canadian Intellectual Property Office

## Excluded Sources

The following domains or source types are never used:

- `wikipedia.org` -- User-editable, unsuitable for patent data verification
- `quora.com` -- Unverified answers, unreliable for IP analysis
- `reddit.com` -- Anonymous commentary, unreliable for patent data
- `yahoo-answers.com` -- Deprecated, unreliable

## Search Templates

Pre-configured search query patterns with runtime placeholder substitution:

| Template | Pattern | Use Case |
|----------|---------|----------|
| patent-number-lookup | `"{patent_number}" patent claims abstract assignee site:{preferred_site}` | Look up a specific patent by number |
| technology-landscape | `"{technology_keyword}" patent landscape {cpc_class} filing trend {year_range}` | Map the patent landscape for a technology area |
| assignee-portfolio | `"{assignee_name}" patent portfolio {technology_area} site:{preferred_site}` | Analyze a company's patent holdings |
| classification-search | `{cpc_code} OR {ipc_code} "{technology_keyword}" patent site:patents.google.com` | Search by CPC/IPC classification codes |
| prior-art-search | `"{invention_keyword}" prior art {technical_field} before:{priority_date}` | Find prior art before a specific priority date |
| patent-family | `"{patent_number}" family continuation divisional priority claim` | Trace patent family relationships |
| fto-risk-search | `"{technology_keyword}" patent infringement freedom-to-operate {jurisdiction}` | Assess freedom-to-operate risks |
| patent-litigation | `"{patent_number}" OR "{assignee_name}" patent litigation lawsuit infringement {year}` | Find patent litigation history |
| patent-citation-network | `"{patent_number}" cited-by references forward-citation backward-citation` | Map citation relationships |

## Filters

- **Language:** English (`en`)
- **Geographic scope:** Global -- USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO
- **Temporal default:** 2015-present with historical context for foundational patents

---

*Source configuration is defined in the engine's `engine-config.json`. To modify, edit the config and regenerate or update the engine.*
