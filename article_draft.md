# Article Draft Material — raw, unstructured

(Pulled together from 10 days of NOTES.md + build conversation. Not organized yet.
Just gathering. Add anything missing, cut anything that's not actually yours.)

---

## Day 1 — The dumbest possible memory

- Just a Python list of {role, content} dicts. No retrieval, no summarization, no limits.
- Worked fine for a 12-turn conversation — held name, a nickname I gave the assistant ("Nick"),
  and a reminder ("see your uncle tonight") correctly across the whole thing.
- Context length grew from 328 chars (turn 1) to 5,679 chars (turn 12) — roughly linear growth,
  no sign of slowing.
- The failure isn't visible yet at 12 turns. It's latent — it's a ticking cost, not a broken
  feature. That's the whole point of building this version first: you can't feel the problem
  until you've felt the version that doesn't have it.

## Day 2 — Sliding window

- First eviction policy: drop oldest user+assistant *pairs*, not single messages — dropping a
  single message risks leaving an orphaned assistant reply with no question before it, which
  confuses the model.
- High-level finding: forgetting is now predictable but *positional*, not *importance-based*.
  A 100-turn-old reminder gets dropped before a 2-turn-old throwaway calculation, just because
  it's older — the system has no concept of "this matters more."
- My own analogy at the time: "it's really like doing CPU scheduling. The very basic is FIFO,
  and then priority or other methods." Sliding window = FIFO eviction. The "marked messages"
  idea I proposed (protect some messages from eviction regardless of age) = priority scheduling.
  Summarization (next day) = closer to compression/paging, not just eviction.
- Stable context size confirmed empirically — plateaued around the same character count once
  the window filled, instead of growing forever.

## Day 3 — Summarization

- Design choice: trigger at ~80% of the token budget (a "high watermark"), not at 100% — gives
  breathing room instead of being perpetually at the edge.
- Batch summarization (multiple messages at once) gives the model more signal to judge what
  actually matters, vs. summarizing one isolated message at a time.
- Real bug, found through testing, not foresight: `agent.py` was calling
  `messages=memory.messages` instead of `messages=memory.get_context()` — the summary was being
  generated correctly the whole time, just never actually sent to the LLM. Looked like
  "forgetting," was actually a wiring bug.
- After the fix: identity facts and assigned tasks survived multiple summarization cycles within
  a session. But summary-of-summary degradation is real — compress enough times and even
  important details start to erode.
- The `summarizer` is a parameter (a function), not hardcoded to one LLM provider — arrived at
  this design from felt need (wanting to mock it during development before plugging in the real
  LLM), not from reading about LangChain's `Runnable` abstraction first. Same idea, different
  path to it.

## Day 4 — Naive keyword retrieval

- Design decision: the retrieval store holds only *user* messages, not assistant replies.
  Reasoning — user messages carry the dense, important facts (names, tasks, preferences); the
  model can always regenerate its own side of the conversation from context, but it can't
  regenerate a fact the user only said once. Storing everything would bloat the store with
  content that's reconstructable anyway.
- Score by shared word count between query and document (set intersection on lowercased,
  split words, minus a tiny stopword list). Same shape as KNN, different metric: "top-k by
  overlap" instead of "top-k by distance."
- The concrete failure, the one that matters most: stored "my dog's name is Pickle," queried
  "what's my pet called" — zero word overlap, zero retrieval. The fact has zero relationship to
  the query in word-space even though it's obviously the answer in meaning-space.
- This is the moment that makes semantic embeddings *necessary* to feel, not just understand
  abstractly.

## Day 5 — Semantic retrieval

- sentence-transformers, `all-MiniLM-L6-v2`, cosine similarity computed by hand in ~3 lines of
  numpy (no similarity library).
- The dog/pet case: solved instantly. "Pet" found "dog" because they're close in meaning-space
  even with zero shared words.
- The centerpiece finding: semantic retrieval has **no "I don't know" option**. Asked the agent
  about Python's GIL — totally unrelated to anything stored — and it still returned the
  dog-related documents, because top-k always returns *something*, even when the closest thing
  available is still far away. There's no relevance threshold built in by default; it forces a
  match.
- Real latency number: a single `search()` call took ~0.013s — orders of magnitude faster than
  the LLM call itself.
- The tradeoff, argued both ways: semantic handles synonyms, paraphrase, and vague reference
  ("they," "the animal") that keyword flatly cannot. But it adds a model dependency and can
  inject irrelevant noise into the prompt precisely because it can't say "nothing fits."
- Side debugging story: Intel Mac + Python 3.13 + `torch` wheel availability mismatch. Fixed by
  pinning the project to Python 3.11. Not core to the memory story, but a real "environment
  reality" moment.

## Day 6 — Persistence to disk

- JSON, with embeddings saved as nested float lists (not re-computed on load) — avoids paying
  the encoding cost again on every restart.
- Model name is stored alongside the data; loading with a mismatched model name raises a loud
  `ValueError` instead of silently producing meaningless similarity scores from two incompatible
  embedding spaces.
- **The bottleneck crossover — probably the single best finding of the whole project**:
  - At 100 documents: load (0.27s) is *slower* than save (0.07s). The fixed cost of spinning up
    the `SentenceTransformer` model dominates at small scale.
  - At 10,000 documents: save (6.2s) is *slower* than load (3.2s). Serializing thousands of
    384-dimensional float vectors to JSON text now dominates instead.
  - The bottleneck literally changes character as the store grows — small-scale and large-scale
    versions of "the same operation" are bound by completely different things.
- Crash test: Ctrl+C (unclean exit) loses any messages from that session, since save only
  happens on a clean `quit`. A deliberate "fast but crash-fragile" tradeoff, not an oversight.
- Metaphors that fit here: working memory vs. persistent store ≈ human short-term vs. long-term
  memory. Also: save-on-quit is closer to a write-back cache (writes accumulate, flush once at
  the end) than write-through (every write immediately persisted).

## Day 7 — Encapsulation into an Agent class

- One main public method: `chat()`. Everything else (`add_message`, `get_context`,
  summarization triggers) stays internal — the caller doesn't need to know any of it exists.
- Composition, not inheritance: "Agent is a memory" isn't true — Agent *uses* a memory, plus a
  retrieval store, plus an LLM client. It's a "has-a" relationship, not an "is-a" one.
- The interface-quality test that actually worked: if `main.py` ends up longer than ~30 lines,
  that's a signal the `Agent` class's interface isn't clean yet — not a reason to add more code
  to `main.py`.
- The Quick Start "That's it" test: if you can show three lines of usage code and just say
  "that's it," the interface design succeeded. If you need five more sentences to explain
  parameters first, it hasn't.

## Day 8 — Defaults and failure modes

- Consistent principle across multiple days, not just one decision: **fail loud, not silent**.
  - Corrupted save file → raises a clear `MemoryFileError` naming the exact problem and the
    fix, rather than silently rebuilding an empty store and losing history with no warning.
  - Missing/invalid API key → raises `APIKeyError` with the exact fix ("pass api_key=... or set
    the ZAI environment variable").
  - Model mismatch (Day 6) → same shape of error, same philosophy.
- The reasoning behind "fail loud": this is a framework other developers will import, not an
  end-user product. The caller needs precise, actionable information to decide what their own
  application should do next — a generic friendly error message would actually be *less* useful
  to them, not more polished.
- The real bug, found only by literally cloning the repo fresh and running it as a stranger
  would: a `return` statement placed after a `raise`, meaning a successful LLM call's result was
  always discarded — every single call, success or failure, ended up hitting the same exception.
  Code review never caught it. Running the "stranger experience" test did.

## Day 9 — README / positioning

- Core pitch framing: "demystification." RAG, sliding windows, summarization — these sound like
  fuzzy, advanced concepts until you actually build minimal versions of each; then they're
  genuinely simple, and the complexity people associate with them is mostly in the polished
  abstractions sitting on top, not in the core idea.
- Honesty as a credibility signal: explicitly stating what the project is *not* (not a LangChain
  replacement, not benchmarked, not production-scale, single-agent only) reads as more credible
  than vague claims of being "robust" or "production-ready."

## Day 10 — Cleanup, and one more real bug

- The search-before-add ordering in `chat()` isn't arbitrary: if you add the current message to
  the retrieval store *before* searching it, the query matches itself with cosine similarity
  1.0 — a perfect score — guaranteeing it crowds out genuinely relevant history. Order matters
  here for a precise, traceable reason, not just convention.
- General lesson about comments: comments that explain *why* a non-obvious decision was made
  (like the above) are worth keeping; comments that just restate *what* the next line does are
  noise once the code itself is already clear.

---

[NOT IN ARTICLE — candidates to cut or save for elsewhere, decide in Block 4]

- The Python generator-expression / `"\n".join()` syntax deep dive (Day 1) — good learning
  moment, not relevant to a reader who already knows Python.
- The Java vs. Python constructor-inheritance comparison (Day 10) — interesting tangent, not
  about memory systems specifically. Maybe a different, smaller post someday.
- The full back-and-forth debugging the `_call_llm` retry logic across several iterations
  (Day 8) — the *finding* (unreachable return) belongs in the article; the blow-by-blow of
  fixing it probably doesn't.
