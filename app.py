"""
Milestone 5 — Generation and CLI interface.

Wires the retrieval pipeline (pipeline.py) to the Groq LLM and exposes an
interactive Q&A loop.  Source attribution is assembled from chunk metadata
so it is always present regardless of what the LLM outputs.

Usage:
    python app.py              # interactive Q&A loop
    python app.py --eval       # run all 5 evaluation questions and exit

Requires a GROQ_API_KEY in a .env file at the project root:
    GROQ_API_KEY=gsk_...
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from pipeline import (
    build_chunks,
    embed_and_store,
    load_documents,
    load_embedding_model,
    retrieve,
)

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# ---------------------------------------------------------------------------
# Grounding — this prompt must enforce context-only answers, not merely
# suggest them.  The critical constraints are:
#   1. ONLY the passages below — never training knowledge
#   2. Explicit fallback phrase when the answer isn't present
#   3. No speculation or inference beyond what is stated
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a housing assistant for UW students researching apartments in Seattle's \
University District. Your job is to answer questions accurately and honestly.

IMPORTANT RULES — follow these exactly:
1. Answer using ONLY the context passages provided in the user message.
   Do NOT use any knowledge from your training data, even if you are confident \
   it is correct.
2. If the answer is clearly supported by the passages, give a direct, specific answer.
3. If the passages contain only partial information, share only what is directly stated.
4. If the answer is NOT present in the passages, respond with exactly:
   "I don't have information about that in my sources."
   Do not guess, speculate, or fill gaps with general knowledge.
5. Do NOT add source citations inside your answer text — sources are listed \
   separately by the application.
"""


# ---------------------------------------------------------------------------
# Context and source formatting
# ---------------------------------------------------------------------------

def format_context(hits):
    """Format retrieved chunks as a numbered block to inject into the user turn."""
    parts = []
    for i, hit in enumerate(hits, 1):
        label = hit["building"] or hit["source"]
        parts.append(f"[Passage {i} — {label}]\n{hit['text']}")
    return "\n\n".join(parts)


def format_sources(hits):
    """
    Build the source list directly from chunk metadata.

    This is programmatically guaranteed — it does not depend on the LLM
    mentioning sources in its answer.
    """
    seen = set()
    sources = []
    for hit in hits:
        key = hit["source"]
        if key not in seen:
            seen.add(key)
            label = hit["source"]
            if hit["building"]:
                label += f"  ({hit['building']})"
            sources.append(label)
    return sources


# ---------------------------------------------------------------------------
# Core ask function
# ---------------------------------------------------------------------------

def ask(query, collection, embedding_model, groq_client):
    """
    Retrieve relevant chunks, call the LLM, and return a result dict:
        answer  — LLM-generated text grounded in retrieved passages
        sources — source identifiers assembled from chunk metadata (not LLM output)
        hits    — raw retrieval results for inspection
    """
    hits = retrieve(query, collection, embedding_model, top_k=TOP_K)
    context = format_context(hits)
    sources = format_sources(hits)

    user_message = (
        f"Context passages:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using ONLY the passages above. "
        "If the answer is not in the passages, say "
        "'I don't have information about that in my sources.'"
    )

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()
    return {"answer": answer, "sources": sources, "hits": hits}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_answer(result):
    print("\n" + "=" * 64)
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  • {s}")
    print("=" * 64)


# ---------------------------------------------------------------------------
# Evaluation run
# ---------------------------------------------------------------------------

EVAL_QUESTIONS = [
    "What do students say about maintenance responsiveness at Hub U District?",
    "Which U-District landlords or buildings have the most complaints about deposit disputes?",
    "How much should I expect to pay for a studio apartment in the U-District?",
    "What rights do I have as a tenant in Seattle if my landlord doesn't make repairs?",
    "What specific complaints do students have about The Standard and other U-District high-rises?",
]


def run_eval(collection, embedding_model, groq_client):
    print("\n" + "=" * 64)
    print("MILESTONE 5 — Evaluation (5 test questions)")
    print("=" * 64)
    for i, q in enumerate(EVAL_QUESTIONS, 1):
        print(f"\n[Q{i}] {q}")
        result = ask(q, collection, embedding_model, groq_client)
        print_answer(result)


# ---------------------------------------------------------------------------
# Interactive CLI loop
# ---------------------------------------------------------------------------

def cli_loop(collection, embedding_model, groq_client):
    print("\nU-District Housing Guide")
    print("Ask anything about apartments, landlords, pricing, or tenant rights.")
    print("Type 'quit' or press Ctrl+C to exit.\n")
    while True:
        try:
            query = input("Your question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break
        result = ask(query, collection, embedding_model, groq_client)
        print_answer(result)


# ---------------------------------------------------------------------------
# Gradio web interface
# ---------------------------------------------------------------------------

def launch_gradio(collection, embedding_model, groq_client):
    import gradio as gr

    def handle_query(question):
        if not question.strip():
            return "", ""
        result = ask(question, collection, embedding_model, groq_client)
        sources = "\n".join(f"• {s}" for s in result["sources"])
        return result["answer"], sources

    with gr.Blocks(title="U-District Housing Guide") as demo:
        gr.Markdown(
            "## U-District Housing Guide\n"
            "Ask questions about apartments, landlords, pricing, and tenant rights "
            "in Seattle's University District. Answers are sourced from student reviews, "
            "The Daily UW, and UW housing guides."
        )
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. What do students say about maintenance at Campus Apartments?",
        )
        btn = gr.Button("Ask", variant="primary")
        answer = gr.Textbox(label="Answer", lines=8)
        sources = gr.Textbox(label="Retrieved from", lines=4)
        btn.click(handle_query, inputs=inp, outputs=[answer, sources])
        inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    demo.launch()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print(
            "Error: GROQ_API_KEY not set.\n"
            "Create a .env file in this directory with:\n"
            "    GROQ_API_KEY=gsk_..."
        )
        sys.exit(1)

    print("Building index (load → chunk → embed → store)...")
    docs = load_documents()
    chunks = build_chunks(docs)
    embedding_model = load_embedding_model()
    collection = embed_and_store(chunks, embedding_model)
    print(f"Index ready: {collection.count()} chunks.\n")

    groq_client = Groq(api_key=api_key)

    if len(sys.argv) > 1 and sys.argv[1] == "--eval":
        run_eval(collection, embedding_model, groq_client)
    elif len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli_loop(collection, embedding_model, groq_client)
    else:
        launch_gradio(collection, embedding_model, groq_client)
