---
description: "Display source hierarchy and configuration for Patent Intelligence Engine"
argument-hint: ""
allowed-tools: ["Read"]
---

# Patent Intelligence Engine — Source Configuration

Display the source credibility hierarchy, preferred sites, excluded sources, search templates, and filters configured for this research engine.

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

## Excluded Sources

The following domains or source types are never used:

1. wikipedia.org
2. quora.com
3. reddit.com
4. yahoo-answers.com

## Search Templates

Pre-configured search query patterns with runtime placeholder substitution:

| Template | Pattern |
|----------|---------|
| patent-number-lookup | `"{patent_number}" patent claims abstract assignee site:{preferred_site}` |
| technology-landscape | `"{technology_keyword}" patent landscape {cpc_class} filing trend {year_range}` |
| assignee-portfolio | `"{assignee_name}" patent portfolio {technology_area} site:{preferred_site}` |
| classification-search | `{cpc_code} OR {ipc_code} "{technology_keyword}" patent site:patents.google.com` |
| prior-art-search | `"{invention_keyword}" prior art {technical_field} before:{priority_date}` |
| patent-family | `"{patent_number}" family continuation divisional priority claim` |
| fto-risk-search | `"{technology_keyword}" patent infringement freedom-to-operate {jurisdiction}` |
| patent-litigation | `"{patent_number}" OR "{assignee_name}" patent litigation lawsuit infringement {year}` |
| patent-citation-network | `"{patent_number}" cited-by references forward-citation backward-citation` |

## Filters

- **Language:** en

---

*Source configuration is defined in the engine's `engine-config.json`. To modify, edit the config and regenerate or update the engine.*
