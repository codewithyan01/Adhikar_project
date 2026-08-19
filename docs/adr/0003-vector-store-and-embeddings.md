# ADR-003: Vector store & embedding model choice
Date: 2026-08-19
Status: Accepted

## Context
Adhikar requires semantic retrieval over structured civic datasets (~700+ government welfare schemes in MyScheme and dozens of legal aid/rights explainers in the Rights KB). In a hackathon demo setting, external network latency, hosted database rate limits, API billing hurdles, and offline staging failures pose high risks to live demonstrations. We needed a vector storage and embedding strategy optimized for rapid startup, zero network dependency, and deterministic local performance.

## Decision
We decided to use an embedded local **ChromaDB** instance (`PersistentClient` stored in `./data/chroma_db`) paired with the local ONNX-based **`all-MiniLM-L6-v2`** embedding model:
1. **Local Persistent Storage:** All vectors and metadata are stored directly on the local filesystem.
2. **Local Inference:** Embeddings are generated locally using the default Chroma ONNX pipeline without relying on external cloud embedding API calls.

## Alternatives Considered
- **Hosted Cloud Vector Databases (Pinecone / Weaviate / Qdrant Cloud):**
  - *Why rejected:* Requires cloud API keys, active internet connection during evaluation, introduces 200-500ms network roundtrip overhead per query, and risks breaking if internet connectivity hiccups during judging.
- **In-Memory Exact Cosine Search (Numpy / Faiss only):**
  - *Why rejected:* ChromaDB provides a clean metadata filtering interface, persistent storage on disk, and collection isolation out-of-the-box while maintaining in-process performance.

## Consequences
- **Positive:** Zero configuration setup for developers and judges; 100% demo stability with zero external network dependencies for retrieval.
- **Positive:** Sub-20ms vector queries for datasets within our target scope (~700 - 5,000 documents).
- **Trade-off:** First-time initialization downloads the lightweight ~79MB ONNX embedding weights to the local cache.
