### 1. Opening (~150 words)
- Lead with demystification directly, argument-first, not story-first: every agent memory
  system boils down to a small number of plain ideas — keep a list, trim it, compress it, look
  things up by meaning. That's the whole foundation underneath the abstractions.
- Personal stance, still in your voice, just not anecdote-first: "I didn't really believe this
  until I built each one myself, over ten days, badly, watching exactly where each one breaks."
- Promise: by the end, the reader will understand why each layer exists — not as an abstract
  concept, but as a direct fix to a specific failure you can point to.

You most likely hear these words as LLM agents getting more and more popular these days, long/short memory, semantic retrieval, sliding window, summarization, etc. These terms most regard the memory system of the agents. Although the words sound fuzzy, they are no more than some application of the very basic and common mechanisms in computer science.

### 2. Why I did this (~200 words)
- Now mostly personal motivation, since section 1 already made the universal claim — don't
  restate the demystification thesis here, build on it.
- Contrast with checkbox-style framework use: import a `Memory` class, configure three params,
  ship it, never know what's actually happening underneath.
- One line on who you are: CS master's student, came from journalism, building toward agent
  systems engineering. One line, not five.

Even the industry-level LLM agents' memory system boils down to a small number of plain ideas — keep a list, trim it, compress it, look things up by meaning. That's the whole foundation underneath the abstractions. I didn't realize this until I built each one myself. Follow the article and build one by yourself, you would get exactly the same feeling.


### 3. Layer 1: the dumbest possible memory (~250 words)
- Just a Python list of `{role, content}` dicts. No retrieval, no summarization, no limits.
- Worked fine for 12 turns — held a name, a nickname, a reminder, correctly, the whole time.
- The numbers: 328 chars at turn 1 → 5,679 chars at turn 12. Roughly linear growth.
- The point: the failure here is *latent*, not visible yet. You can't feel why bounding memory
  matters until you've run the unbounded version long enough to watch the number keep climbing
  with no end in sight.

The dumbest but workable memory of an AI agent is no more than a list. As the conversation goes, it keeps appending the content into the list. In a new LLM call, the list is resctured to text and fed it to model as context. Such that, the model has knowledge of what in the previous rounds of chat. 

In my experiment, the dumbest memory worked fine for 12 turns, held a name, a nickname, a reminder, correctly, the whole time. The size of the memory grows from 328 chars at turn 1 to 5,679 chars at turn 12. Roughly linear growth. Nevertheless, the failure is easy to predict. If we run the unbounded version long enough, the context would explode. The cost of each LLM call would skyrocket. And eventually it would hit the context limit.

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

Sliding window is adding eviction policy to the memory mechanism above. I choose to evict pairs of questions and answers avoiding living an orphaned reply with no question in front of it. The most natural eviction policy for a memory system is First In First Out(FIFO). When eviction triggered, the oldest memory will be dropped. Thinking of it as the short memory of human beings, old memory fade out as new memory come in. The drawback of the sliding window memory is obvious, important info will be forgotten just because it is old.
  

### 5. Layer 3: summarization (~300 words)
- The "alive" nugget: summarization is different in kind from the other layers, not
  just degree. Sliding windows and retrieval are math — slicing, hashing, vector distance.
  Summarization is the one layer where the system has to think to remember; it calls on the
  very same kind of intelligence it's trying to manage, to manage it.
- The design decisions, briefly: trigger at a high-watermark (~80% full, not 100%);
  summarize in batches, not one message at a time, so the model has enough signal to
  judge importance.
- Pain point: summary-of-summary degradation. Facts survive a few compression cycles,
  then start to erode.

To solve the problem, summarization mechanism is called up. Summarization is differnt in kind from the other layers, not just degree. Sliding windows and retrieval are math - slicing, hashing, vector distance.  Summarization is the one layer where the system has to think to remember; it calls on the very same kind of intelligence it's trying to manage, to manage it.
Summarization is triggered at a high-watermark (I choose 80% of the context window, which is almost an industry convention now.) 80% is good. When it's too high, let's say 100%, when it's 99% full, the summarization is not triggered, but then the next message will overflow. If it's too low, the summarization cannot get enough signals, such that it cannot decide which is important info.
But summarization degrade as it triggers multiple times, the summarization got summarized again and again. It is called summary-of-summary degradation. Facts start to erode over time, especailly details, the memory gets vague.

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

  (I put persistence before retrieval delibrately)
  Now we have short-term memory, but long-term memory is missing. No memory is persistance. Once it is lost, it is lost forever for the agent. So we need to store the memory and find a way to retrieve it. Storage is straightforward, I store the memory as a json file, the other options are md files or a database. Json files are easy to handle and light weight, work well for such a small project. To retrieve the persisted memory is not that straightforward, we cannot just load all the memory from the file, otherwise the large number of memory would burst the context window. We need to find a way of retrieval.

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


The dumbest solution is retrieve the one with the most number of overlapping words with the query. For example, "My dog's name is Picle." "The sky is blue." And the query is that "What is the name of my dog?" Then "My dog's name is Picle." will be retrieved because there are three overlapping words, "my", "dog" and "name". The coding solution becomes trivial now, use a score to measure the number of overlapping words, then sort and pick the top K memory as retrieval.
It seems work well, with both short term and long term memory, until I ran into this problem in the Day 4 of the development. I asked the model, "what is our puppy called?" Nothing is retrieved while there is no overlapping words. In other words, the dumb solution does not recognize the semantic relationship between the words. 
As we know, words are tokenized and represented as vectors in the representation space of the LLM. The words with similar semantics tend to be close in distance. "puppy" and "dog" end up close together because they appear in similar contexts across millions of documents. 
So the semantic retrieval works in this way: we tokenize each piece of query and memory, and compute the similarity between the query and memory. One thing to notice, we use cosine similarity rather than euclidean distance to measure the similarity, there is a reason behind the choice, we would to explain here, just take it as given. Replace the similarity score with the naive score in the dumb solution, it agent can retrieve those memory with the most semantic similarity. In this way, "My dog's name is Picle." is successfully retrieved when the query is "what is our puppy called?" 
One drawback of this semantic retrival is that it always retrieves something even though there is nothing relevant. Because it always retrieves those memory with the highest scores.  "I asked about Python's GIL, and it still retrieves my dog's name and load it into context". Try it and you'll see. 

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

The complete architecture of the memory system emerged now. The short-term/long-term memory with semantic retrieval. The rest work is the just assemble the components into an agent, with proper exception handling. I choose failing loudly in this project, since it aims to be used by programmers rather than end users. The missing API keys and mismatched embedding models would raise errors.
[EXPAND IN POLISH] (The composition-over-inheritance point got dropped entirely, and the "fail loud" reasoning is there but compressed to one sentence. Both of those were strong beats in the outline. )

### 9. What I'd build next (~150 words)
- The two-memory-categories observation: within-session memory (summary) vs. across-session
  memory (retrieval store) are genuinely different problems, and this project only loosely
  connects them right now.
- Honest scope: this is a learning artifact built to expose the mechanics, not a LangChain
  replacement, not benchmarked, not built for scale beyond ~10k documents.
- Light tease of where this could go next, without overcommitting to a roadmap.

Honestly speaking, this is a learning artifact built to expose the mechanics, not an industry-level work. More memory mechanisms are worth to try, vector DB, etc. And it's far less than the entire picture of agent engineering. Memory is important, but just a corner of the agent. Tool calling, skills, environment are interesting topics as well.


### 10. Closing (~100 words)
- One sentence on what ten days actually taught: most of what sounds like AI magic is a small
  number of plain ideas, stacked, and you only really understand the stack once you've built
  it badly first and watched exactly where it breaks.
- Link to the repo.
- Closing line as an invitation, not a sales pitch — something like: "If you've been meaning to
  build this yourself instead of importing it, the repo's right there."

  The first I heard about the memory of AI agent, I was thinking of it as something advanced and not easy to get it down. Now I'm relieved, it is a small number of plain ideas. You only really understand the stack once you've built
  it badly first and watched exactly where it breaks. If you've been meaning to build this yourself, the repo's right there.
