# agent-memory

A from-scratch agent memory framework built to make AI agent memory mechanism feel obvious instead of magical.

## Why this exists

Most agent frameworks hand you a `Memory` class. This project rebuilds memory from scratch: unbounded list → sliding window → summarization → semantic retrieval → disk persistence. Each layer was built specifically to feel its predecessor's limitation before reaching for the next abstraction.

## Quick Start

```bash
git clone https://github.com/Homer212416/agent-from-scratch
cd agent-from-scratch
cp .env.example .env  
# then add your API key into .env
uv run main.py
```

That's it.

## Architecture

The agent is composed of two independent memory components: a bounded conversation window with automatic summarization, and a persistent semantic retrieval store. The `Agent` class orchestrates both — neither component knows the other exists.

```
┌─────────────────────────────────────────────────┐
│                     Agent                       │
├─────────────────────────────────────────────────┤
│  ConversationMemory         SemanticRetrieval   │
│  ├─ working window           ├─ embeddings      │
│  └─ summarization (on full)  └─ JSON persistence│
└─────────────────────────────────────────────────┘
```

On each message: relevant past context is retrieved, the message is added to both the working window and the retrieval store, the full prompt is assembled (summary + retrieved docs + recent messages), and the LLM is called.

## What this is not

- Not optimized or benchmarked for production scale
- No multi-agent support — single agent only
- Persistence uses JSON, not a vector database — a deliberate choice that work well for up to ~10k documents

## Read more

Article forthcoming.

## License

MIT