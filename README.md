# The Unofficial Guide — Project 1

---

## Domain

Off-campus housing in Seattle's University District (U-District) for UW students. Finding housing is one of the biggest decisions a UW student makes — it affects budget, commute, safety, and quality of life. The questions students have ("Is this landlord responsive?" "Is this building worth the price?" "Which property managers to avoid?") require lived experience, not brochure copy.

UW's housing resources list available units but don't aggregate tenant experiences or flag problem landlords. That information is spread across Reddit threads, ApartmentRatings reviews, and student journalism. It's on multiple platforms, hard to search, and easy to miss.

---

## Document Sources

13 sources covering apartment reviews, Daily UW journalism, tenant rights guides, and Reddit discussions.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | ApartmentRatings — AVA U District | Resident reviews | `documents/apartmentratings_ava_u_district.txt` |
| 2 | ApartmentRatings — Yugo Seattle Lothlorien | Resident reviews | `documents/apartmentratings_yugo_lothlorien.txt` |
| 3 | ApartmentRatings — Campus Apartments | Resident reviews | `documents/apartmentratings_campus_apartments.txt` |
| 4 | The Daily UW — Cost vs. convenience | Student journalism | `documents/dailyuw_cost_vs_convenience.txt` |
| 5 | The Daily UW — High-rise pricing | Student journalism | `documents/dailyuw_high_rise_pricing.txt` |
| 6 | The Daily UW — Tenant rights guide | Student journalism | `documents/dailyuw_tenant_rights_guide.txt` |
| 7 | The Daily UW — High-rises scamming students (op-ed) | Opinion journalism | `documents/dailyuw_high_rises_scamming.txt` |
| 8 | The Daily UW — Summer housing costs | Student journalism | `documents/dailyuw_summer_housing.txt` |
| 9 | The Daily UW — The ugly side of UW housing | Student journalism | `documents/dailyuw_ugly_side.txt` |
| 10 | UW IELP Off-Campus Housing Guide | Official guide | `documents/uw_ielp_housing_guide.txt` |
| 11 | Tripalink — U-District Apartment Guide | Student housing guide | `documents/tripalink_guide.txt` |
| 12 | r/udub — housing threads | Reddit | `documents/reddit_udub_housing.txt` |
| 13 | r/Seattle — U-District housing threads | Reddit | `documents/reddit_seattle_housing.txt` |

---

## Chunking Strategy

**Chunk size:** 200 words maximum (~240 tokens, safely within `all-MiniLM-L6-v2`'s 256-token hard limit).

**Overlap:** None. Natural-boundary cuts make each chunk self-contained; overlap would only add noise.

**Why these choices fit the documents:** The corpus has three structurally different document types, and a single word-based splitter failed all three: mid-sentence starts, pronouns with no referent ("Part of Wu's success..." with Wu introduced in the previous chunk), and reviews split across two chunks. The pipeline uses a three-way dispatch:

| Document type | Strategy | Function |
|---|---|---|
| `apartmentratings_*` | One chunk per review, split on `---` delimiters; building name prepended to every chunk | `chunk_reviews()` |
| `reddit_*` | One chunk per post/comment, split on `---` delimiters; metadata-only blocks filtered | `chunk_reddit()` |
| Everything else | Paragraphs accumulated up to 200 words, flushed at paragraph boundary; sentence-boundary fallback for oversized single paragraphs | `chunk_article()` |

**Preprocessing:** Building name extracted from file headers and prepended to each chunk so it's self-contained for retrieval. Instruction blocks stripped from manual-fill templates. Excess whitespace collapsed. Chunks under 15 words discarded.

**Final chunk count:** 132 chunks across 13 documents (avg 103 words, range 16–200).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`. Runs locally with no API key, fast, and well-suited to short review-length text, which is most of this corpus.

**Production tradeoff reflection:** If I were deploying this for real users, I'd look at `text-embedding-3-small` from OpenAI. It has better accuracy on domain-specific text and a much longer context window (8,191 tokens vs. 256 for MiniLM), which matters because some article paragraphs push close to the MiniLM limit. The tradeoff is API latency and cost ($0.02/1M tokens) vs. running free locally. Since the corpus is English-only, multilingual support isn't a factor. I'd skip Cohere Embed Multilingual unless the audience changed.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt enforces grounding with hard constraints:

> "Answer using ONLY the context passages provided in the user message. Do NOT use any knowledge from your training data, even if you are confident it is correct. If the answer is NOT present in the passages, respond with exactly: 'I don't have information about that in my sources.' Do not guess, speculate, or fill gaps with general knowledge."

The fallback phrase is mandatory. Context is injected in the user turn (not the system prompt) so it's fresh per query. Temperature is 0.2 to discourage elaboration beyond the passages.

**How source attribution is surfaced in the response:** Sources are assembled from chunk metadata (`hit["source"]` and `hit["building"]`), not generated by the LLM, so they're always present regardless of what the model outputs. The display format is controlled by the application, not the model.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about maintenance responsiveness at Hub U District? | Reviews mention slow or unresolved maintenance; op-ed calls it out specifically | "I don't have information about that in my sources." Retrieved chunks from Yugo, Campus Apartments, and AVA — none about Hub U District. | Off-target | Inaccurate |
| 2 | Which U-District landlords or buildings have the most complaints about deposit disputes? | Campus Apartments ApartmentRatings reviews mention deposit and maintenance issues | Named Campus Apartments; cited specific reviewers (Current Resident 891350, Miraearly) describing difficulty getting deposits back | Relevant | Accurate |
| 3 | How much should I expect to pay for a studio apartment in the U-District? | ~$1,334/mo avg studio (summer 2025 article); The Standard at $2,700/mo for 407 sq ft | The Standard at $2,700/mo (correct); $950/mo from Reddit; cited $1,500 average instead of the $1,334 from the summer article | Partially relevant | Partially accurate |
| 4 | What rights do I have as a tenant in Seattle if my landlord doesn't make repairs? | Seattle law requires timely repairs; 21-day deposit return with itemized deductions; tenants can report habitability issues to the city | Found tenant rights guide; stated landlords must provide safe conditions, but hedged ("the passage does not specifically state what rights you have") and missed the 21-day rule and city reporting option | Partially relevant | Partially accurate |
| 5 | What specific complaints do students have about The Standard and other U-District high-rises? | Spotty WiFi, broken elevators, unsecured premises, stolen packages, rent above $2,000–$2,300 | Named spotty WiFi (✓), unsecured premises (✓), disorganized management; added leaking sprinklers and no blinds (in source, not in expected); missed broken elevators and stolen packages | Relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

### Primary failure — Q4: Tenant rights (generation framing mismatch + corpus gap in expected answer)

**Question that failed:** "What rights do I have as a tenant in Seattle if my landlord doesn't make repairs?"

**What the system returned:** "According to Passage 1, as a tenant in Seattle, your landlord is required to provide you with living conditions that are clean, safe, and secure... However, the passage does not specifically state what rights you have if your landlord doesn't make repairs."

**Root cause — part 1 (generation stage, framing mismatch):** The top result had a cosine distance of 0.30, the strongest match across all five queries. `dailyuw_tenant_rights_guide_chunk_000` contains this:

> *"Landlords in Seattle are required to... maintain the structural integrity of the building, ensuring that utilities function..."*

That's the answer, but the chunk organizes it under **"Obligations of Landlords"**, not "Tenant Rights." The model saw landlord-obligation framing and concluded the passage didn't answer a question about tenant rights, even though "landlord must maintain X" and "you have the right to demand X" mean the same thing. The strict system prompt ("Do NOT speculate or fill gaps") made it worse: it prevents hallucination, but it also blocked an obvious inference from what the text says to what it means.

**Root cause — part 2 (corpus stage, incomplete source):** The planning.md expected answer included the 21-day deposit return rule and the ability to report habitability issues to the city. Checking all four chunks of the tenant rights guide reveals neither appears in the document. Those came from general knowledge of Seattle law. They were never in the documents.

**What I would change to fix it:**
- For the framing mismatch: add a line to the system prompt: *"If a passage states what a landlord is required to do, treat that as equivalent to a tenant right."*
- For the corpus gap: add a more complete source (e.g., the Seattle Office of Housing tenant rights page) that explicitly states the 21-day return rule and city reporting process.

---

### Secondary failure — Q1: Hub U District (corpus gap)

**Question that failed:** "What do students say about maintenance responsiveness at Hub U District?"

**What the system returned:** `"I don't have information about that in my sources."` The grounding constraint fired correctly, but the answer is a complete miss.

**Root cause (corpus stage):** Hub U District was never scraped. The three ApartmentRatings sources in the corpus are AVA U District, Yugo Seattle Lothlorien, and Campus Apartments. Because no chunk mentions Hub U District, the top-5 retrieval returned reviews about other buildings — all with high cosine distances (0.54–0.58, vs. 0.30 for a strong match). The LLM correctly declined to use irrelevant context. The fallback worked as intended. The problem was that Hub U District was never scraped.

**What I would change to fix it:** Scrape Hub U District reviews from ApartmentRatings and add as `documents/apartmentratings_hub_u_district.txt`. No pipeline changes needed — `build_chunks()` automatically applies `chunk_reviews()` to any `apartmentratings_*` file.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The Chunking Strategy section forced a decision about chunk boundaries before any code was written. When the initial `chunk_text()` produced mid-sentence cuts and cross-chunk pronoun references, the spec gave something concrete to check against: it said "semantic boundaries" but the code was doing mechanical word counts. That gap made the fix clear.

**One way your implementation diverged from the spec, and why:**

The spec flagged "generic retrieval across buildings" as a risk and proposed including the building name in chunk text to address it. The implementation did this — but the Q1 failure exposed a version of the same problem the spec didn't anticipate: a query for a building that isn't in the corpus at all produces off-target retrieval followed by a correct but useless fallback. The spec assumed all planned sources would be collected; Hub U District was never scraped.

---

## AI Usage

**Instance 1 — Initial chunking implementation**

- *What I gave the AI:* The Documents table and Chunking Strategy section from `planning.md`, plus the requirement for `load_documents()` and a word-based `chunk_text()` with 200-word chunks and 30-word overlap.
- *What it produced:* Working `load_documents()` and `chunk_text()` using a fixed word-count split with overlap.
- *What I changed or overrode:* After manually inspecting 5 sample chunks and finding mid-sentence starts and cross-chunk pronoun references, I directed a refactor into three document-aware strategies: `chunk_reviews()`, `chunk_reddit()`, and `chunk_article()`. The three-way dispatch was not in the original output; it came from manual quality review.

**Instance 2 — Grounded generation and system prompt**

- *What I gave the AI:* The Architecture diagram, the Evaluation Plan, the Groq model name (`llama-3.3-70b-versatile`), and a description of the grounding requirement (context-only answers, explicit fallback phrase, no training-data leakage).
- *What it produced:* The `ask()` function, system prompt, `format_context()`, and `format_sources()` in `app.py`.
- *What I changed or overrode:* The initial system prompt used softer language ("try to answer using only..."). I directed a revision to hard constraints ("ONLY the passages below," "Do NOT use any knowledge from your training data"). I also moved context injection from the system prompt to the user turn so it's fresh per query, and confirmed source attribution must come from metadata, not LLM output.
