"""
Milestones 3 & 4 — Document ingestion, chunking, embedding, and retrieval.

Run this file directly to load, chunk, embed, store, and test retrieval:
    python pipeline.py
"""

import os
import re
from collections import Counter

import chromadb
from sentence_transformers import SentenceTransformer


DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 200    # words (~240 tokens, safely within all-MiniLM-L6-v2's 256-token hard limit)
OVERLAP = 30        # words — used only by the legacy chunk_text(); natural-boundary chunkers don't need it
MIN_CHUNK_WORDS = 15  # drop chunks shorter than this (e.g. one-liner Reddit comments)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_documents(documents_dir=DOCUMENTS_DIR):
    """
    Load every .txt file in documents_dir.

    Returns a list of dicts:
        source   — filename without .txt
        building — building name extracted from "Building: ..." header line, or None
        text     — cleaned body text with instructions blocks stripped
    """
    documents = []
    for filename in sorted(os.listdir(documents_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(documents_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            continue

        source = filename[:-4]

        # Extract building name from the first few header lines before anything else
        building = None
        for line in raw.splitlines()[:10]:
            if line.startswith("Building:"):
                building = line.split(":", 1)[1].strip()
                break

        # Strip the instructions block in the manual-fill templates.
        # Everything before and including the sentinel line is dropped.
        sentinel = "PASTE REVIEWS BELOW THIS LINE:"
        if sentinel in raw:
            _, _, text = raw.partition(sentinel)
            text = text.strip()
        else:
            text = raw

        # Collapse excess whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        if not text:
            continue

        # Prepend building name so every chunk from this doc carries the context.
        # This addresses the "generic retrieval across buildings" risk in planning.md.
        if building:
            text = f"Building: {building}\n\n" + text

        documents.append({
            "source": source,
            "building": building,
            "filepath": filepath,
            "text": text,
        })

    return documents


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

def _make_chunk(source, building, idx, text):
    text = text.strip()
    return {
        "id": f"{source}_chunk_{idx:03d}",
        "source": source,
        "building": building,
        "text": text,
        "word_count": len(text.split()),
    }


def _sentence_chunks(text, source, building, chunk_size, start_idx):
    """
    Fallback: split text at sentence boundaries when a single block exceeds
    chunk_size words. Guarantees no mid-sentence cuts.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    idx = start_idx
    current = []
    count = 0

    for sent in sentences:
        words = sent.split()
        if not words:
            continue
        if count + len(words) > chunk_size and current:
            chunks.append(_make_chunk(source, building, idx, " ".join(current)))
            idx += 1
            current = [sent]
            count = len(words)
        else:
            current.append(sent)
            count += len(words)

    if current:
        chunks.append(_make_chunk(source, building, idx, " ".join(current)))

    return chunks


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------

def chunk_text(text, source, chunk_size=CHUNK_SIZE, overlap=OVERLAP, building=None):
    """
    Word-based overlapping chunker (original implementation).
    Kept for reference; build_chunks() no longer calls this by default.
    Use chunk_reviews() or chunk_article() instead.
    """
    words = text.split()
    chunks = []
    start = 0
    idx = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append({
            "id": f"{source}_chunk_{idx:03d}",
            "source": source,
            "building": building,
            "text": " ".join(chunk_words),
            "word_count": len(chunk_words),
        })
        idx += 1
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def chunk_reviews(text, source, building=None, chunk_size=CHUNK_SIZE):
    """
    Split apartmentratings text into one chunk per review.

    Reviews are delimited by '---' lines. Each chunk gets the building name
    prepended so it's fully self-contained for retrieval. Falls back to
    sentence-boundary splitting for any review that exceeds chunk_size words.
    """
    building_prefix = f"Building: {building}\n\n" if building else ""

    blocks = re.split(r"\n?---\n?", text)

    chunks = []
    idx = 0

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Skip blocks that contain no review content (e.g. the building header)
        if "Reviewer:" not in block and "Review:" not in block:
            continue

        chunk_str = f"{building_prefix}{block}"
        word_count = len(chunk_str.split())

        if word_count > chunk_size:
            sub = _sentence_chunks(chunk_str, source, building, chunk_size, idx)
            chunks.extend(sub)
            idx += len(sub)
        else:
            chunks.append(_make_chunk(source, building, idx, chunk_str))
            idx += 1

    return chunks


def chunk_reddit(text, source, building=None, chunk_size=CHUNK_SIZE):
    """
    Split Reddit thread documents into one chunk per post or comment.

    Requires '---' delimiters between posts and between individual comments in
    the source file. Blocks whose non-empty lines are all metadata headers
    (Source:, TOP COMMENTS:, THREAD N:, etc.) are silently skipped.
    Falls back to sentence-boundary splitting for blocks over chunk_size words.
    """
    _HEADER_LINE = re.compile(
        r"^(Source:|Title:|Date:|URL:|Subreddit:|Posted by:|TOP COMMENTS:|THREAD \d+:)"
    )

    blocks = re.split(r"\n?---\n?", text)
    chunks = []
    idx = 0

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not any(not _HEADER_LINE.match(l) for l in lines):
            continue  # skip metadata-only blocks

        word_count = len(block.split())
        if word_count > chunk_size:
            sub = _sentence_chunks(block, source, building, chunk_size, idx)
            chunks.extend(sub)
            idx += len(sub)
        else:
            chunks.append(_make_chunk(source, building, idx, block))
            idx += 1

    return chunks


def chunk_article(text, source, building=None, chunk_size=CHUNK_SIZE):
    """
    Split article/guide/forum text at paragraph boundaries, never mid-sentence.

    Accumulates paragraphs until the next one would push past chunk_size, then
    flushes. Single paragraphs that already exceed chunk_size are split at
    sentence boundaries instead. Separator-only lines ('---') are ignored.
    """
    raw_paras = re.split(r"\n+", text)
    paragraphs = [
        p.strip() for p in raw_paras
        if p.strip() and not re.fullmatch(r"-+", p.strip())
    ]

    chunks = []
    idx = 0
    current_paras = []
    current_count = 0

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        if len(words) > chunk_size:
            # Flush accumulated paragraphs first
            if current_paras:
                chunks.append(_make_chunk(source, building, idx, "\n\n".join(current_paras)))
                idx += 1
                current_paras = []
                current_count = 0
            # Split this oversized paragraph at sentence boundaries
            sub = _sentence_chunks(para, source, building, chunk_size, idx)
            chunks.extend(sub)
            idx += len(sub)
        elif current_count + len(words) > chunk_size:
            # Adding this paragraph would exceed the limit — flush first
            chunks.append(_make_chunk(source, building, idx, "\n\n".join(current_paras)))
            idx += 1
            current_paras = [para]
            current_count = len(words)
        else:
            current_paras.append(para)
            current_count += len(words)

    if current_paras:
        chunks.append(_make_chunk(source, building, idx, "\n\n".join(current_paras)))

    return chunks


# ---------------------------------------------------------------------------
# Build all chunks
# ---------------------------------------------------------------------------

def build_chunks(documents, chunk_size=CHUNK_SIZE, overlap=OVERLAP, min_words=MIN_CHUNK_WORDS):
    """
    Chunk all documents using the appropriate strategy:
      - apartmentratings_* : one chunk per review  (chunk_reviews)
      - reddit_*           : one chunk per comment  (chunk_reddit)
      - everything else    : paragraph-boundary     (chunk_article)

    Chunks shorter than min_words are dropped (catches one-liner Reddit comments
    and other noise that can't be meaningfully retrieved).
    """
    all_chunks = []
    for doc in documents:
        if doc["source"].startswith("apartmentratings_"):
            all_chunks.extend(
                chunk_reviews(doc["text"], doc["source"], doc["building"], chunk_size)
            )
        elif doc["source"].startswith("reddit_"):
            all_chunks.extend(
                chunk_reddit(doc["text"], doc["source"], doc["building"], chunk_size)
            )
        else:
            all_chunks.extend(
                chunk_article(doc["text"], doc["source"], doc["building"], chunk_size)
            )
    return [c for c in all_chunks if c["word_count"] >= min_words]


# ---------------------------------------------------------------------------
# Embedding and vector store
# ---------------------------------------------------------------------------

CHROMA_COLLECTION = "udistrict_housing"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_embedding_model(model_name=EMBEDDING_MODEL):
    """Load the sentence-transformers model. Downloads on first run, cached after."""
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    print("Model loaded.")
    return model


def embed_and_store(chunks, model, collection_name=CHROMA_COLLECTION):
    """
    Embed all chunks and upsert into a local ChromaDB collection.

    Each chunk is stored with:
        id        — unique chunk identifier (e.g. apartmentratings_hub_chunk_003)
        embedding — 384-dim vector from all-MiniLM-L6-v2
        document  — the raw chunk text (ChromaDB's term for the content field)
        metadata  — source, building, chunk position extracted from the id
    """
    client = chromadb.Client()
    # cosine distance matches how sentence-transformers embeddings are designed to be compared
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    ids = [c["id"] for c in chunks]
    metadatas = [
        {
            "source": c["source"],
            "building": c["building"] or "",
            "word_count": c["word_count"],
            # chunk index is the numeric suffix in the id (e.g. 003 → 3)
            "chunk_index": int(c["id"].rsplit("_", 1)[-1]),
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} chunks in collection '{collection_name}'.")
    return collection


def retrieve(query, collection, model, top_k=5):
    """
    Embed query and return the top_k most similar chunks from ChromaDB.

    Returns a list of dicts with keys: id, text, source, building, distance.
    """
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "building": results["metadatas"][0][i]["building"],
            "distance": results["distances"][0][i],
        })
    return hits


def print_retrieval_results(query, hits):
    print(f"\nQuery: {query!r}")
    print("=" * 64)
    for rank, hit in enumerate(hits, 1):
        print(f"\n[{rank}] {hit['id']}  (distance: {hit['distance']:.4f})")
        print(f"    Source:   {hit['source']}")
        print(f"    Building: {hit['building'] or '—'}")
        print(f"\n{hit['text'][:400]}{'...' if len(hit['text']) > 400 else ''}")
        print("-" * 64)


# ---------------------------------------------------------------------------
# Inspection helpers
# ---------------------------------------------------------------------------

def print_load_summary(documents):
    print(f"{'SOURCE':<45} {'WORDS':>6}  BUILDING")
    print("-" * 75)
    for d in documents:
        words = len(d["text"].split())
        building = d["building"] or "—"
        print(f"{d['source']:<45} {words:>6}  {building}")
    print(f"\n{len(documents)} documents loaded.")


def print_chunk_summary(chunks):
    counts = Counter(c["source"] for c in chunks)
    word_counts = [c["word_count"] for c in chunks]

    print(f"\n{'SOURCE':<45} {'CHUNKS':>6}")
    print("-" * 55)
    for source, count in sorted(counts.items()):
        print(f"{source:<45} {count:>6}")

    print(f"\nTotal chunks : {len(chunks)}")
    print(f"Min words    : {min(word_counts)}")
    print(f"Max words    : {max(word_counts)}")
    print(f"Avg words    : {sum(word_counts) / len(word_counts):.0f}")


def inspect_chunks(chunks, n=5, seed=42):
    """Print n randomly selected chunks for manual quality review."""
    import random
    rng = random.Random(seed)
    sample = rng.sample(chunks, min(n, len(chunks)))
    for c in sample:
        print(f"\n{'=' * 64}")
        print(f"ID:       {c['id']}")
        print(f"Source:   {c['source']}")
        print(f"Building: {c['building'] or '—'}")
        print(f"Words:    {c['word_count']}")
        print(f"\n{c['text']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 64)
    print("MILESTONES 3 & 4 — Ingestion, chunking, embedding, retrieval")
    print("=" * 64)

    print("\n--- Loading documents ---\n")
    docs = load_documents()
    print_load_summary(docs)

    print("\n--- Chunking ---")
    chunks = build_chunks(docs)
    print_chunk_summary(chunks)

    print("\n--- Sample chunks (manual inspection) ---")
    inspect_chunks(chunks, n=5)

    print("\n\n" + "=" * 64)
    print("MILESTONE 4 — Embedding and retrieval")
    print("=" * 64)

    model = load_embedding_model()
    collection = embed_and_store(chunks, model)

    # Run the 5 evaluation questions from planning.md
    eval_queries = [
        "What do students say about maintenance responsiveness at Hub U District?",
        "Which U-District landlords or buildings have the most complaints about deposit disputes?",
        "How much should I expect to pay for a studio apartment in the U-District?",
        "What rights do I have as a tenant in Seattle if my landlord doesn't make repairs?",
        "What specific complaints do students have about The Standard and other U-District high-rises?",
    ]

    print("\n--- Retrieval evaluation (top-5 per query) ---")
    for q in eval_queries:
        hits = retrieve(q, collection, model, top_k=5)
        print_retrieval_results(q, hits)
