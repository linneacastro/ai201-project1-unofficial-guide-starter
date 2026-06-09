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

## Sample Chunks

Five representative chunks drawn from the pipeline output (random seed 42), one from each major source type:

---

**Chunk 1 — `apartmentratings_campus_apartments_chunk_015`**
Source: `apartmentratings_campus_apartments` · Strategy: `chunk_reviews()` · Words: 145

```
Building: Campus Apartments

Reviewer: Chadwick103
Rating: 3.0/5
Review: Shady — please reconsider. Also known as "Don Kennedy Real Estate." Beware a company
with two names. I consider it my civic duty to warn people. When my girlfriend and I looked at
the apartment there were a few things wrong, but we were promised everything would be fixed. It
wasn't. A week before move-in they demanded an extra $200 deposit. When we moved in the
apartment had only been vacuumed. Over the year: broken water heater, thin walls, a noisy
neighbor, a leaking ceiling, and a landlord who never answered the phone. Long story short, it
was a year from hell. The place had a great view and appeared nice on the outside, but if you
get that sinking feeling in your gut when you look at a property managed by these people, go
with it.
```

---

**Chunk 2 — `apartmentratings_ava_u_district_chunk_006`**
Source: `apartmentratings_ava_u_district` · Strategy: `chunk_reviews()` · Words: 56

```
Building: AVA U District

Reviewer: Current Resident 189693
Rating: 4.8/5
Review: i lived here begin 2013, it's really a amazing apt, AVA is the best apt in UW, there
have the best manager and the best gym, the largest study room, I like this apt, and there is
pet friendly, my cat love this apt too.
```

---

**Chunk 3 — `dailyuw_high_rises_scamming_chunk_001`**
Source: `dailyuw_high_rises_scamming` · Strategy: `chunk_article()` · Words: 168

```
So here you are: you've finally found an apartment building that charges under $2500 for rent
after weeks of searching. You move into a new building, telling yourself that although you'll be
on that ice soup diet for a while, at least you live in an apartment close to UW with a gym and
a sweet view. Soon, however, you find yourself amongst the many students moving into newer
buildings who have found that their $2,000 plus rent is paying for incompetent management,
malfunctioning amenities, and unsecured premises.

Many such complaints have come from students living in the newly constructed Standard apartment
buildings, completed Sept. 2023.

Standard residents have voiced concerns that their rent prices are too high for the amount of
problems they experience with the buildings.

Caitlin Igel, a third-year student, moved into the north Standard building the first day it
became available. Among the problems she described were spotty WiFi, leaking sprinklers, no
blinds or curtains on her unit's windows, unsecured premises, and disorganized management.
```

---

**Chunk 4 — `dailyuw_cost_vs_convenience_chunk_003`**
Source: `dailyuw_cost_vs_convenience` · Strategy: `chunk_article()` · Words: 169

```
Elkady currently lives in a triple on North Campus but is looking for an apartment for next
year. She said price is the most important factor in her decision of where to live next year,
but she also values proximity to campus.

"When you do it right, an off-campus apartment can be cheaper than dorming, not necessarily
just in price, but what you're getting," Elkady said. "So, you're paying the same thing, but
you're getting, like, your own room and your own bathroom, and like you, you have access to a
kitchen and everything."

Sacco said, although it depends on the type of housing, on-campus options are typically
comparable in price to equivalent off-campus options.

"Something we do is we take a look at our off-campus markets just to see [and] make sure that
we're within what is comparable," Sacco said.

Sacco also mentioned that the construction of Haggett Hall, scheduled to open in the fall of
2027, will add almost 800 spots to housing options on North Campus.
```

---

**Chunk 5 — `apartmentratings_yugo_lothlorien_chunk_023`**
Source: `apartmentratings_yugo_lothlorien` · Strategy: `chunk_reviews()` · Words: 75

```
Building: Yugo Seattle Lothlorien

Reviewer: Andrew Lai
Rating: 3.3/5
Review: This place isn't too bad. It's relatively close to campus and the accommodations were
everything I expected. I've never had issues with sound or noise. It was a bit annoying that
much of the infrastructure needed constant fixing — water leakage, elevators not working —
which proved to be a hassle. It's also rather expensive, but for a place close to campus it's
not bad.
```

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`. Runs locally with no API key, fast, and well-suited to short review-length text, which is most of this corpus.

**Production tradeoff reflection:** If I were deploying this for real users, I'd look at `text-embedding-3-small` from OpenAI. It has better accuracy on domain-specific text and a much longer context window (8,191 tokens vs. 256 for MiniLM), which matters because some article paragraphs push close to the MiniLM limit. The tradeoff is API latency and cost ($0.02/1M tokens) vs. running free locally. Since the corpus is English-only, multilingual support isn't a factor. I'd skip Cohere Embed Multilingual unless the audience changed.

---

## Retrieval Test Results

Top-3 chunks returned for three evaluation queries, run against the 132-chunk index using `all-MiniLM-L6-v2` cosine similarity.

---

### Query 1: "Which U-District landlords or buildings have the most complaints about deposit disputes?"

| Rank | Chunk ID | Source | Distance |
|------|----------|--------|----------|
| 1 | `apartmentratings_campus_apartments_chunk_009` | `apartmentratings_campus_apartments` | 0.5013 |
| 2 | `apartmentratings_campus_apartments_chunk_015` | `apartmentratings_campus_apartments` | 0.5155 |
| 3 | `apartmentratings_campus_apartments_chunk_001` | `apartmentratings_campus_apartments` | 0.5255 |

Top chunk text:

```
Building: Campus Apartments

Reviewer: Current Resident 891350
Rating: 2.0/5
Review: Terrible management, mold, and I still don't have my deposit back. I moved to the
U-District excited about a great location and access to amazing food, but my living situation
was miserable. Before I even moved in, my manager asked me to sign a document saying I'd read
the tenant agreement, but she had "forgotten" to bring it to the lease signing — and pulled
that same stunt with other tenants. I had windows that wouldn't close or lock, mold in the
kitchen and bathroom ceilings, and was promised a parking spot that was given to someone else.
The laundry machines ruined clothes. The manager was impossible to reach and yelled at me when
I contacted the owner. I've since moved out and have been hung up on twice trying to get my
deposit back. I strongly suggest finding another place — there are apartments in the U-District
that are cheaper by hundreds of dollars with far more professional management.
```

**Why the returned chunks are relevant:** All three hits are Campus Apartments reviews that use the word "deposit" explicitly and in a complaints context. Chunk_009 says "I still don't have my deposit back" and "hung up on twice trying to get my deposit back"; chunk_001 says "made getting all of it back literally impossible"; chunk_015 mentions an extra $200 deposit demanded before move-in. The embedding model recognized semantic similarity between "deposit disputes" and tenant language about deposits being withheld or demanded. All three top results come from the same source because Campus Apartments is the only building in the corpus with multiple deposit-specific reviews — the concentration is accurate, not a retrieval artifact.

---

### Query 2: "How much should I expect to pay for a studio apartment in the U-District?"

| Rank | Chunk ID | Source | Distance |
|------|----------|--------|----------|
| 1 | `dailyuw_high_rise_pricing_chunk_001` | `dailyuw_high_rise_pricing` | 0.3710 |
| 2 | `reddit_udub_housing_chunk_011` | `reddit_udub_housing` | 0.3747 |
| 3 | `dailyuw_high_rises_scamming_chunk_004` | `dailyuw_high_rises_scamming` | 0.3819 |

Top chunk text:

```
However, that invites another question — why are all these new apartments so grossly overpriced,
while the more cost-conscious of us are forced to resort to buildings dating back decades?

Let's start with the Standard as an example, which finished construction in 2023. To keep things
consistent, we'll look at a one-person studio apartment; in this case, a 407-square-foot
apartment is offered for $2,700 a month. As a result, the monthly price per square foot works
out to be $6.63.

This number means nothing alone, so for context, we can examine one of my personal prospective
candidates for an apartment lease: Campus View. This debatably charming slice of student housing
was built in the U-District in 1986, and despite rising high enough to merit its name, is still
dwarfed by the Standard a few blocks down. More importantly, the price per square foot pales in
comparison at $3.33 — nearly half that of its counterpart.
```

**Why the returned chunks are relevant:** This query produced the strongest retrieval distances in the evaluation set (0.37–0.38, versus 0.50+ for the deposit query), reflecting that pricing data is stated numerically and concretely in several documents. Chunk 1 gives a specific studio price at The Standard ($2,700/mo, $6.63/sq ft) alongside a comparison to an older building ($3.33/sq ft). Chunk 2 gives a low-end Reddit data point ($950/mo with utilities). Chunk 3 adds a $2,300 reference point from the op-ed. Together the three chunks cover the realistic price range — which is why the generated answer correctly reports a range rather than a single number.

---

### Query 3: "What specific complaints do students have about The Standard and other U-District high-rises?"

| Rank | Chunk ID | Source | Distance |
|------|----------|--------|----------|
| 1 | `dailyuw_high_rises_scamming_chunk_000` | `dailyuw_high_rises_scamming` | 0.4951 |
| 2 | `dailyuw_high_rises_scamming_chunk_001` | `dailyuw_high_rises_scamming` | 0.5328 |
| 3 | `dailyuw_high_rise_pricing_chunk_000` | `dailyuw_high_rise_pricing` | 0.5341 |

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt enforces grounding with hard constraints:

> "Answer using ONLY the context passages provided in the user message. Do NOT use any knowledge from your training data, even if you are confident it is correct. If the answer is NOT present in the passages, respond with exactly: 'I don't have information about that in my sources.' Do not guess, speculate, or fill gaps with general knowledge."

The fallback phrase is mandatory. Context is injected in the user turn (not the system prompt) so it's fresh per query. Temperature is 0.2 to discourage elaboration beyond the passages.

**How source attribution is surfaced in the response:** Sources are assembled from chunk metadata (`hit["source"]` and `hit["building"]`), not generated by the LLM, so they're always present regardless of what the model outputs. The display format is controlled by the application, not the model.

---

## Query Interface

**Application:** Gradio web app, launched via `python app.py`.

**Input field:**
- **Your question** — free-text input. The user types a question about U-District apartments, landlords, pricing, or tenant rights and presses Enter or clicks "Ask."

**Output fields:**
- **Answer** — 8-line text area. The LLM-generated response, grounded in the top-5 retrieved passages.
- **Retrieved from** — 4-line text area. Source documents listed as `source_name  (Building Name)`, assembled from chunk metadata by `format_sources()` in `app.py`. Not generated by the LLM.

**Sample interaction transcript:**

> **Your question:** Which U-District landlords or buildings have the most complaints about deposit disputes?
>
> **Answer:**
> The passages mention that Campus Apartments has multiple complaints about deposit disputes. Reviewer Current Resident 891350 mentions that they have been hung up on twice trying to get their deposit back. Reviewer Miraearly also had issues with getting their security deposit back, stating that the company made it "literally impossible" to get all of it back. However, the passages do not provide a comparison with other U-District landlords or buildings, so it is unclear if Campus Apartments has the "most" complaints.
>
> **Retrieved from:**
> • apartmentratings_campus_apartments  (Campus Apartments)
> • dailyuw_tenant_rights_guide

---

## Example Responses

**Response 1 — deposit disputes (source attribution in output):**

```
================================================================
The passages mention that Campus Apartments has multiple complaints about deposit disputes.
Reviewer Current Resident 891350 mentions that they have been hung up on twice trying to get
their deposit back. Reviewer Miraearly also had issues with getting their security deposit back,
stating that the company made it "literally impossible" to get all of it back. However, the
passages do not provide a comparison with other U-District landlords or buildings, so it is
unclear if Campus Apartments has the "most" complaints.

Sources:
  • apartmentratings_campus_apartments  (Campus Apartments)
  • dailyuw_tenant_rights_guide
================================================================
```

**Response 2 — studio pricing (source attribution in output):**

```
================================================================
According to the passages, the average rent for a studio within city limits is $1,500. However,
a specific studio apartment at The Standard is listed at $2,700 a month (407 sq ft), while a
Reddit post mentions a studio with utilities included at $950/mo. The expected price range for
a studio in the U-District varies widely depending on the building, roughly $950–$2,700.

Sources:
  • dailyuw_high_rise_pricing
  • reddit_udub_housing
  • dailyuw_high_rises_scamming
================================================================
```

**Response 3 — out-of-scope query (refusal):**

```
================================================================
I don't have information about that in my sources.

Sources:
  • apartmentratings_campus_apartments  (Campus Apartments)
  • tripalink_guide
  • reddit_seattle_housing
  • apartmentratings_yugo_lothlorien  (Yugo Seattle Lothlorien)
================================================================
```

Query: "What is the best sushi restaurant near the University of Washington?"

The retrieval stage always runs regardless of topic, so the sources list shows the four most semantically similar chunks (which happen to be about apartments). The LLM correctly refused to answer from irrelevant context — the grounding constraint fired as designed.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about maintenance responsiveness at Hub U District? | Reviews mention slow or unresolved maintenance; op-ed calls it out specifically | Correct fallback: "I don't have information about that in my sources." Hub U District is not in the corpus — retrieved off-target chunks from other buildings. | Off-target | N/A — source not collected |
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

### Note on Q1: Hub U District (corpus gap, not a system failure)

Q1 can't be evaluated as accurate or inaccurate — the system had no way to answer it. Hub U District was never scraped. The three ApartmentRatings sources in the corpus are AVA U District, Yugo Seattle Lothlorien, and Campus Apartments. The top-5 retrieval returned chunks from those other buildings (cosine distances 0.54–0.58, well below the 0.30 of a strong match), and the model correctly refused to answer from irrelevant context. The fallback phrase fired exactly as designed.

The gap was in data collection, not the pipeline. I planned to include Hub U District as a source and didn't scrape it. To fix it: add `documents/apartmentratings_hub_u_district.txt` and rebuild the index. No pipeline changes needed.

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
