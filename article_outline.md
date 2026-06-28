# Article Outline (draft — react to this, don't just accept it)

**Working title (pick one or remix):**
- "I Built an Agent's Memory From Scratch, One Broken Layer at a Time"
- "Four Ideas, Ten Days: What's Actually Inside an Agent's Memory"

**Subtitle:**
"What sliding windows, summarization, and embeddings actually look like once you build
them yourself instead of importing them."

---

### 1. Opening (~150 words)
- Lead with demystification directly, argument-first, not story-first: every agent memory
  system boils down to a small number of plain ideas — keep a list, trim it, compress it, look
  things up by meaning. That's the whole foundation underneath the abstractions.
- Personal stance, still in your voice, just not anecdote-first: "I didn't really believe this
  until I built each one myself, over ten days, badly, watching exactly where each one breaks."
- Promise: by the end, the reader will understand why each layer exists — not as an abstract
  concept, but as a direct fix to a specific failure you can point to.

### 2. Why I did this (~200 words)
- Now mostly personal motivation, since section 1 already made the universal claim — don't
  restate the demystification thesis here, build on it.
- Contrast with checkbox-style framework use: import a `Memory` class, configure three params,
  ship it, never know what's actually happening underneath.
- One line on who you are: CS master's student, came from journalism, building toward agent
  systems engineering. One line, not five.

### 3. Layer 1: the dumbest possible memory (~250 words)
- Just a Python list of `{role, content}` dicts. No retrieval, no summarization, no limits.
- Worked fine for 12 turns — held a name, a nickname, a reminder, correctly, the whole time.
- The numbers: 328 chars at turn 1 → 5,679 chars at turn 12. Roughly linear growth.
- The point: the failure here is *latent*, not visible yet. You can't feel why bounding memory
  matters until you've run the unbounded version long enough to watch the number keep climbing
  with no end in sight.

### 4. Layer 2: sliding window (~250 words)
- First eviction policy: drop oldest user+assistant *pairs*, not single messages — avoids
  leaving an orphaned reply with no question in front of it.
- Lead with the short-term-memory framing here: this window is the system's short-term memory —
  vivid, immediate, but small. Briefly tease OS scheduling (FIFO eviction = "oldest job goes
  first, no exceptions") as the systems-side name for the same idea, without fully developing it
  yet — full development comes in section 8.
- Pain point: forgetting becomes predictable but purely *positional* — a 100-turn-old important
  fact gets dropped before a 2-turn-old throwaway one, just because it's older. The system has
  no concept yet of "this matters more."

### 5. Layer 3: summarization (~300 words)
- The design decisions, briefly: trigger at a high-watermark (~80% full, not 100%); summarize
  in batches, not one message at a time, so the model has enough signal to judge importance.
- The real bug as a concrete moment: the summary was being generated correctly the whole time —
  it just wasn't being sent to the model, because of one wrong variable name in a function call.
  Looked exactly like "forgetting." Wasn't.
- The "alive" nugget from Q1: summarization is different in *kind* from the other layers, not
  just degree. Sliding windows and retrieval are math — slicing, hashing, vector distance.
  Summarization is the one layer where the system has to think to remember; it calls on the
  very same kind of intelligence it's trying to manage, to manage it.
- Pain point: summary-of-summary degradation. Facts survive a few compression cycles, then
  start to erode.

### 6. Layer 4: semantic retrieval (~400 words — this is now the heaviest section, that's fine)
- Open with the full story, told in place, now that the reader has context for why it matters:
  on Day 4, told the agent the dog's name was Puppy. A few turns later, asked what the pet was
  called. Nothing. Zero retrieval, total silence — not because the agent forgot, but because
  "pet" and "dog" share zero letters, and that was the only thing the keyword retriever knew
  how to check.
- Keyword retrieval mechanics, briefly: score by shared word overlap. Same shape as KNN,
  different metric. Works when the words match. Fails completely otherwise — exactly as above.
- The fix: cosine similarity, in plain terms — meaning becomes geometry. Closer vectors = closer
  meaning, regardless of shared spelling. "Pet" and "dog" end up close together because they
  appear in similar contexts across millions of documents.
- The centerpiece finding: semantic retrieval has **no "I don't know" option**. Asked the agent
  about Python's GIL — completely unrelated to anything stored — and it still returned
  dog-related documents, because top-k always returns *something*. There's no built-in
  relevance threshold. It can't say "nothing fits"; it just returns the least-wrong thing
  available.
- The tradeoff, argued honestly both ways: semantic handles synonyms and vague reference that
  keyword flatly can't — but it adds a model dependency, and that "always returns something"
  behavior can quietly inject irrelevant noise into a prompt.

### 7. Layer 5: persistence (~250 words)
- JSON, not a vector DB — and why: debuggable, portable, fine under ~10k documents.
- The centerpiece finding of the whole project: the save/load bottleneck crossover. At 100
  documents, loading is *slower* than saving (the embedding model's fixed startup cost
  dominates). At 10,000 documents, it flips — saving becomes slower (serializing thousands of
  vectors to JSON text now dominates). The bottleneck literally changes character as the store
  grows.
- Tie back to the lead analogy here: this is where short-term memory gets a long-term partner.
  The working window is fast but limited and disappears when the session ends; the retrieval
  store is durable but slower to "wake up" — same shape as how human memory actually works.
- Pain point: sessions vs. identity. A fresh session starts with an empty working memory but a
  full retrieval history — which raises a question this project doesn't fully answer yet:
  what does "the agent" even mean across sessions?

### 8. The architecture that emerged (~200 words)
- Fully resolve the analogies here, having teased them earlier: short-term/long-term memory as
  the umbrella framing; OS-scheduling (FIFO eviction, and the "priority" idea I never built) as
  the systems-side name for the same tradeoff; write-back vs. write-through for the save-on-quit
  design specifically.
- Composition over inheritance: the `Agent` class holds a memory component and a retrieval
  component as attributes — it doesn't extend either one. Neither component knows the other
  exists. "Agent is a memory" isn't true; Agent *uses* one, alongside other things.
- The "fail loud, not silent" thread that ran through the whole second half of the project:
  corrupted save files, missing API keys, and mismatched embedding models all raise specific,
  actionable errors rather than degrading quietly — because this is a library other developers
  will sit code on top of, not an end-user product that should hide its failures.

### 9. What I'd build next (~150 words)
- The two-memory-categories observation: within-session memory (summary) vs. across-session
  memory (retrieval store) are genuinely different problems, and this project only loosely
  connects them right now.
- Honest scope: this is a learning artifact built to expose the mechanics, not a LangChain
  replacement, not benchmarked, not built for scale beyond ~10k documents.
- Light tease of where this could go next, without overcommitting to a roadmap.

### 10. Closing (~100 words)
- One sentence on what ten days actually taught: most of what sounds like AI magic is a small
  number of plain ideas, stacked, and you only really understand the stack once you've built
  it badly first and watched exactly where it breaks.
- Link to the repo.
- Closing line as an invitation, not a sales pitch — something like: "If you've been meaning to
  build this yourself instead of importing it, the repo's right there."

---

**Total estimate: ~2,250 words across sections (roadmap target ~2,500 — close enough, can pad
naturally during drafting if a section earns more room, especially section 6 or 7).**