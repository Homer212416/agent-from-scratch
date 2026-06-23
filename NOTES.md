Today I'm building the simplest possible memory. No retrieval, no summarization, no token limits. Just a list.

## -- day 1 --

Questions:

1. How long did the context get by turn 10? 
It grows to 6552 chars after the last turn of chat.

2. Did it forget anything it shouldn't? Remember anything useless? 
It remembers everything well.

(but think about turn 100. It will remember what you had for breakfast on turn 3. That's not useful anymore. "Remembers everything" becomes a problem at scale.)

3. What's the first thing that would break in a 100-turn conversation?
I think the context would break. 200K context window means more or less 200,000 chars.

(but the real break comes earlier. Most APIs have a token limit per request, not a char limit. Roughly 1 token ≈ 4 chars, so 200K chars ≈ 50K tokens. You'd hit API limits or slow responses well before that. Also cost — every turn you're paying for the entire history again.)

4. If you had to improve this with one change, what would it be?
I would let it write the summarization of the memory when it is needed.

## -- day 2 --

Question 1: Should the limit be measured in number of messages or number of tokens/characters? Pick one and write down why.

Answer: I think it should be the number of tokens. Since the API limit or context window is measured by tokens, it is reasonable the same for the limit.

(Token counting requires either a library (tiktoken) or an approximation (len(content) / 4). Number of messages is cruder but simpler.

Question 2: When the limit is hit, do you drop the oldest message, the oldest user+assistant pair, or something else? Why?

Answer: I choose to drop the oldest messages but except the marked ones.

(for today's code, keep it simple — no marking system yet. Just drop the oldest user+assistant pair. Dropping a single message could leave an orphaned assistant reply that would confuse the model. Dropping the pair keeps the conversation structure clean.)

Question 3: Should the system prompt / initial instructions be exempt from the limit? Why or why not?

Answer: Yes, it should be. Otherwise the model forgot some important context.

1. What's the new failure mode? (Yesterday's was "grows forever")
Answer: it forgets the early info as the context hits the max

2. When it forgot something, could you predict what it would forget?
Answer: it forgets the ealiest info in the context

3. If your only tool is "drop old messages," what information would you want to preserve anyway?
Answer: I want to perserve the impontant info like identity, user info, the shedule of the user, etc.

4. Does summarization feel necessary now? Why?
Answer: Yes. Otherwise it losts important context.

Memory management in agents maps almost directly to OS scheduling:

Yesterday (unbounded) — no scheduler, just let everything pile up until crash
Today (sliding window) — FIFO eviction, drop oldest regardless of importance
Your "marked messages" idea — priority scheduling, protect important jobs
Summarization (Day 3) — compression, like memory paging — you don't throw data away, you compress and swap it out

## -- day 3 --

Q1: When does summarization run? After every message? When the window is full? When you cross a threshold? Pick one and write down why.
Answer: I think the summarization should run when hitting the context max or maybe reaching the 80% of the context max. I don't have a reason but I heard that it is a common way to do it.
(the actual reason: If you wait until 100% full, every new message immediately triggers summarization — you're always at the edge. At 80%, you have a buffer. You summarize early, drop the old messages, and have room to breathe before the next trigger.)

Q2: What gets summarized — just the messages about to be evicted, or everything older than N turns including past summaries? Pick one and why.
Answer: I think we could summarize the several messages at once. If we just summarize the one about to be evicted, the summarization threshold would be reached soon. And another advantage of summrizing several messages at once is that the model can tell which is the important info than summarizing just one.
(what about past summaries? Over a long conversation you'll accumulate:
Summary 1 (from turn 1-10)
Summary 2 (from turn 11-20)
Summary 3 (from turn 21-30)
Do you keep all summaries growing, or do you fold the new summary into the old one? That's the summary-of-summaries problem the roadmap mentions. For today, just accumulate them.)

Q3: Where does the summary live in the final prompt? Above the conversation, as a special "system" note, somewhere else?
Answer: In our case, since we don't evict summary, treat the summary as special system note is fine.
(Since you don't have a real system prompt yet — just replace position 0 each time a new summary is generated.)

Q4: Write out the actual LLM prompt for the summarization step as a string. What do you tell the model to do?
Answer: If there are N messages in the context, summarize the important info from the first messaget to the N-1 message and generate the summarization. Leave the latest message untouched. The important info should include but not limit to user and agent's identities, the undone the user assigned, other info that the user emphasizes.
(prompt = f"""You are a memory summarizer. Given the following conversation, 
extract and summarize the important information concisely.

Focus on:
- User and assistant identities and names
- Any tasks or todos the user mentioned
- Key facts the user emphasized
- Anything the user might ask about later

Conversation:
{messages_text}

Write a concise summary in 3-5 sentences."""

you're summarizing the oldest batch that's about to be evicted, while keeping the recent window intact. 
The question is just where you draw the line — how many recent messages to keep untouched. That's your max_messages parameter doing its job.

I choose to keep the last one pair of messages.)

### evaluation

- 1. What did the summary get right? What did it miss?
It gets all the important info right and miss the details of average conversations.
- 2. Did summary-of-summary degradation appear?
Yes, over time, summary-of-summary lost details.
- 3. Did important facts (identity, tasks) survive summarization over time?
Yes. They survive my test of multiple turns.
- 4. Does a separate persistent-facts store feel necessary now?
Not yet. I think it would be needed when there is a new session.

## -- day 4 --

### design

Q1: What goes into the retrieval store? All messages? Only user messages? Only summarized chunks? Pick one and say why.
A: user messages. To store all messages would make the database too bloated over time, but user messages usually contain important info from the users. And the model can regenerate the answer based on the user prompt. Summarized chunks are not necessary in this case since there is no tool calling or web-search. Everything is either generated or input by the user.
(assistant messages sometimes contain important info too — like if the agent confirmed a plan, gave a specific recommendation, or the user said "yes, do that." But user messages as the primary store is a reasonable v0 choice.)

Q2: What triggers retrieval? Every turn? Only when the user asks something? Pick one and why.
A: Can we use a self prompt to trigger retrieval. For example, when the user asked something not in the context. The model would generate a self prompt to start retrival. But to be simple, the agent always trigger retrieval when the user asks something about the personal domain. For example, the user's preference. In the other hand, no retrieval for public domain or common sense.
(self-prompting to trigger retrieval — is actually a real technique called agentic RAG or retrieval on demand. The model decides when it needs to retrieve. That's a more advanced pattern worth writing in NOTES.md as a future idea.
But you're right to simplify for today. The problem with "only personal domain" is: how does the code know it's a personal question? That judgment requires another LLM call or a classifier — too complex for v0.
Pick the simplest trigger: every turn. Always retrieve, always prepend. You'll feel the redundancy during the stress test, and that feeling will tell you why smarter triggering matters.)

(You arrived at this idea unprompted, which is notable. Right now in the industry, when to retrieve is one of the hottest architectural questions — most production systems are moving from "always retrieve" to "retrieve when needed." You named the pattern before being taught it. Put a flag in NOTES.md for this — it might become a Project 2 angle, or a follow-up article.)

Q3: How many results do you return? Top 1? Top 3? Top 5? Why?
A: Top 3. Top 1 can be not precise. Top 3 has some redundant but top 5 is too redundant.

Q4: Where in the final prompt does retrieved content go? Same place as the summary, or a different section labeled differently?
A: Same place as the summary. Since we do retrieval every time and the retrieval already contain the use info. Summary is not necessary any more. 
(push back on yourself a little. Retrieval only returns what's relevant to the current query. Summary captures everything important regardless of what's being asked right now.
They serve different purposes:
Summary — persistent background context, always present
Retrieval — query-specific context, pulled on demand
For today keep both, but put them in different labeled sections.)

Q5: If retrieval pulls back a message from 50 turns ago — but that message has been summarized and evicted — what happens? Do you store the original even after eviction, or only what's still in the window?
A: Store the original after eviction. We do eviction because the context window is very limit, but the vector DB can be much bigger, it can store long term memory.

- Observation:
"dog" and "pet" have zero word overlap so score = 0, nothing retrieved. The retrieval store has "my dog's name is Pickle" but the query "do I have a pet" shares no meaningful words with it.
This is precisely why semantic embeddings exist. In vector space:

"dog" and "pet" are close neighbors
"Pickle" and "dog name" are related concepts

Keyword matching only sees surface form. Embeddings capture meaning.

### evaluation
Q1: When did keyword retrieval work well?
A: When the keywords in documents and query are exactly the same.

Q2: When did it fail? Be specific about why it failed in each case.
A: It fails there is none same keywords between documents and queries. For example, I told the agent about my dog. When I asked about my pet, it didn't retrieve anything.

Q3: What does this tell you about why semantic embeddings exist?
A: Yes. Semantic embeddings ensure semantic retrievals.
(The deeper point is: embeddings map words to points in vector space where meaning determines distance, not spelling. "Dog" and "pet" end up close together because they appear in similar contexts across millions of documents. )

Q4: Did retrieval interact strangely with the summary? Any redundancy?
A: Yes. There are redundacies between retrievals and summary, but the model handle them well in my tests.
(The better question is: what's the cost of adding embeddings? You need a model to generate them, storage to keep them, and a similarity search library. Is that complexity worth it for your use case? That's the real architectural tension.)

Q5: What's the next architectural question this opens up?
A: Is it necessary to have a semantic retrieval?

## -- day 5 --

### design
Q1: Which embedding model? Local (sentence-transformers with all-MiniLM-L6-v2) or API (OpenAI/DeepSeek embeddings)? Pick one and say why.
A: API is fine. I don't think my device is suitable to run a model locally. 
(all-MiniLM-L6-v2 is only 22 million parameters — tiny by today's standards. It runs on CPU without any GPU needed, and even old hardware handles it.)

Q2: What similarity metric? Cosine similarity is standard — use it. Note why cosine and not Euclidean.
A: Cosine is the standard way to calculate the similarity between vectors. Euclidean is good for the distance between dots but not for vectors.
(Euclidean distance — straight-line distance between two points. Sensitive to magnitude (how "long" the vector is).
Cosine similarity — measures the angle between two vectors, ignoring their length entirely.
Why does this matter for embeddings? Two sentences can point in the same semantic direction but have different magnitudes (one embedding vector might just be "longer" due to sentence length or model quirks). Cosine only cares about direction — are they pointing the same way in meaning-space — not how long the vectors are.)

Q3: Do you embed on add() or only at search time? Pick one and say why.
A: We need to embed on add(). So the documents only are embeded once rather than embeded every time there is a search.

Q4: What happens to old embeddings if you re-embed with a different model later?
A: We have to redo the embedding again since different models generate different embeddings.
(Model A's "dog" vector and Model B's "dog" vector live in completely different, incompatible spaces — comparing them with cosine similarity would give meaningless numbers.)

### evaluation

Q1: the core thesis of today: does "pet" find "dog" now?
A: Yes. (That's the moment. Keyword matching failed on this exact case yesterday — zero overlap between "pet" and "dog". Today, semantic embeddings found it because "pet" and "dog" live close together in meaning-space.)

Q2: Comparison.
A: Keyword retrieval failed every single time after the exact-match case — "animal", "pet", "they in the house" all returned empty. Semantic retrieval caught all of them, even pulling in relevant context for "they" referring to wife and dog together.

Q3: Irrelevant query.
A: Semantic still returned the dog-related documents even though they're completely irrelevant to Python's GIL. It can't say "nothing matches" — it always returns the top-k closest by cosine similarity, even when the closest thing is still far away. That's an important limitation to note: semantic retrieval has no built-in relevance threshold, it just returns "closest of what exists," which could be junk if nothing is actually close.

Q: Concrete examples where semantic beat keyword
A: If 'dog' is stored but 'pet' is queried, semantic beat keyword with no doubts.

Q: Concrete examples where they returned the same thing
A: When keyword is in the query. For example, 'dog' is queried.

Q: Did semantic ever return something weird/irrelevant?
A: Yes!
(when you asked about Python's GIL, semantic retrieval still returned the dog-related documents because it always returns top-k by similarity, even when nothing is actually relevant. There's no "I don't know" option built in — it forces a match. That's the real lesson here, write it down explicitly.)

Q: Latency cost — try timing a search() call if you want a number
A: Very fast. Much faster than LLM response.
(Search took: 0.0130s)

Q: The real question — is semantic retrieval worth the complexity for your use case? Argue both sides.
A: Yes, it can retrieve info with vague meaning.
   No, a model is needed and naive solution can retrieve in a lot of senarios and doesn't need a model.
(For: Semantic retrieval handles paraphrasing, synonyms, and vague references ("they", "the animal") that keyword matching completely misses. As conversations get longer and more natural, exact word overlap becomes rarer.
Against: It adds a model dependency (download, memory footprint, inference time even if small), and it always returns something even when nothing is relevant — which can inject noise into the prompt. For small, short conversations where users tend to reuse the same words, keyword matching might be "good enough" and far simpler to debug and reason about.)

## -- day 6 --

### -- design --

Q1: What format? JSON, SQLite, pickle, plaintext? Pick one and justify in 2-3 lines. (Hint: think about debuggability, portability, and what you'd want when something goes wrong.)
A: JSON. JSON is very easy to manupilate in python and familiar by LLM. SQLite is also a good choice but too heavy for such a small project. Pickle is not easy to use since it does not have good structure. Plaintext doesn't have structure either.
(JSON is also human-readable — you can open the file in a text editor and see exactly what's stored, which matters when debugging "why did my agent forget something." Pickle and SQLite require tooling to inspect; JSON doesn't.)

Q2: What gets persisted? Just the retrieval store? Working window too? Summary? All three? Why?
A: Just the retrieal store. Working window and summary are for the current session not for cross sessions.
(One thing to think through: if only the retrieval store persists, what happens to your dog's name on a fresh session? It's in the summary, not necessarily in the retrieval store (since you only added user messages to the store, and the summary is a separate generated text). So when the user starts a new session tomorrow, the summary is gone — does the retrieval store alone capture everything important?)

Q3: When does saving happen? On every message, on a timer, on shutdown, manually? Pick one. Tradeoffs: every message = safe but slow; on shutdown = fast but crash-fragile.
A: when shutdown. Since the shutdown is soft, when the input is 'quit', it is safe to trigger saving then. On every message would be too slow. On a timer might disrupt user's process.
(you're choosing the "fast but crash-fragile" option intentionally. That's fine; Block 3 will specifically test what happens when the process dies uncleanly (Ctrl+C) instead of a clean quit. You'll feel the consequence of this choice firsthand soon.)

Q4: How do embeddings get persisted? Re-compute on load, or save the vectors too? What's the tradeoff?
A: It's a classic time and space trade-off. I choose re-comput onload. Since we have chosen JSON, it's for storing text. If we need to store vectors, a vector DB would be needed.
(JSON can absolutely store numbers, including nested arrays of floats. A vector like [0.123, -0.456, 0.789, ...] is just a list, and JSON handles lists natively:
No vector database needed — that's only necessary at scale with similarity search optimizations.
So the real tradeoff is:
Re-compute on load: Smaller file size, but every restart costs embedding time.
Save vectors too: Larger file size, but instant load — no re-encoding needed.)
After reconsidering, let's try with saving vectors.
generalized insight -- "Embeddings are the idea that meaning can be represented as geometry."

Q5: What does "session" mean now? One user, one conversation, one process? If the user starts a new conversation tomorrow, what gets loaded — everything, or only the persistent layer?
A: It means one process. When we start a session, in the backend, there is a process. If a new converstion is started, only persistent layer loaded, others are lost.
(One session = one process = one ConversationMemory instance (working window + summary, ephemeral). 
The SemanticRetrievalStore persists across processes/sessions via disk. 
New session starts with empty working memory but full retrieval history.)

### -- evaluation --

scaling — at 10,000 documents, the model loading time stays roughly constant (it's a fixed cost), but JSON parsing and converting 10,000 embeddings back to numpy arrays will grow.

Q1: What broke in the crash test? Worst-case data loss?
The current session retrieval storage is lost, which is the worst-case.
(accurate, but be precise: it's not the retrieval storage that's lost (that only updates on save() calls within the session anyway) — it's specifically any messages from that crashed session that hadn't been saved yet.)

Q2: Did model-mismatch fail loudly? (Yes — already confirmed)
Yes, it raises the error.

Q3: How long does load take with 100 messages? Will it scale to 10,000?
At 100 docs: load (0.27s) > save (0.07s) — model loading is the fixed cost that dominates.
At 10,000 docs: save (6.2s) > load (3.2s) — serialization cost now dominates and outpaces the fixed model cost.
The crossover point matters: your bottleneck literally changes character as the store grows.
(model-loading dominates at small scale, serialization dominates at large scale!!!)
(Most articles say "use a vector database for scale" without showing you when and why the simple approach breaks. You have actual numbers from a real system you built.)

Q4: Now that persistence exists, did your framing of "working window" shift? Write a paragraph.
Yes. Working window is like people's working memory, it is detailed but limited. With storage on disk, incompleted, taking loading-time, the memory is more like a completed human memory.
(working memory (your ConversationMemory) is like short-term human memory — vivid, immediate, but limited and temporary. The persistent retrieval store is like long-term memory — slower to access (the embedding model has to "wake up"), but durable. )

- article material: metaphors for what you've built. You've already got OS scheduling (Day 2) and L1/L2 cache (earlier). Today added human short-term/long-term memory. your system is "write-back" (saves accumulate and only flush at the end) rather than "write-through" (every write immediately persisted). 

## -- dat 7 --

### -- design --
Q1: What should the minimal public interface of your Agent class be? Write out the method signatures.
A: 
agent.summarize()->:None
agent.load_memory(path:str)->:None
agent.dump_memory(path:str)->:None
agent.run()->:str
( 
(chat) instead of separate run(), summarize(), load_memory(), dump_memory().
Because summarization, loading, and saving are implementation details the user shouldn't need to know about or call directly.
Loading happens automatically in __init__. Saving happens in a close() method.
So the actual minimal interface is just:
chat(self, user_message: str) -> str: ...
def save(self) -> None: ...
def close(self) -> None: ...
)
(用框架使用者的视角看API：用户用你的 framework 想做的事是和 agent 对话。他们不需要知道你内部有 memory、有 summarization、有 retrieval store。这些是你的工程问题，不是他们的问题。
你还在用"我作为开发者要怎么实现"的视角思考，而不是用"用户要怎么用，数据流要怎么走"的视角。
这是从 component-builder 到 framework-designer 的关键认知差。)

Q2: What does Agent.__init__ accept as parameters? Which have defaults, which are required?
A: model_name:str, load_context:boolean, storage_path:str="storage.json", system_prompt:str, number_of_retrieved=3
(
api_key — has to be required, no sensible default exists (it's secret, per-user)
model_name — could default to whatever you've been using
storage_path — default ("storage.json")
system_prompt — could default to None or a generic empty default
number_of_retrieved (top_k) — could default to 3
load_context (boolean) — could default to True, since "if a save file exists, load it" is the sensible behavior
)

Q3: What's the relationship between ConversationMemory and SemanticRetrievalStore inside Agent? Does Agent hold them as attributes (composition), inherit from them, or something else? Why?
A: They compensate with each other to form the entire memory. Yes, it holds them as attributes. Agent is a memory (inheritance) is not fair, composition is more reasonable. Since agent is very different from the memory.

Q4: When a user sends a message, what's the internal processing flow in Agent.chat()? List the steps: 1, 2, 3...
A: 
step 1: load the retrival memory 
step 2: if context is full, summarize by doing a llm call
step 3: form the conversation context
step 4: call the llm to generate the reply
(
1. Receive user_message
2. Retrieve relevant past context from SemanticRetrievalStore.search(user_message)
3. Add the user message to ConversationMemory (this is also where summarization gets triggered internally if the window is full)
4. Add the user message to SemanticRetrievalStore too (so it's searchable in future turns)
5. Build the final prompt — combine: summary + retrieved docs + working window messages
6. Call the LLM with that combined prompt
7. Add the assistant's reply to ConversationMemory
8. Return the reply to the caller
)

Q5: Should the LLM call be abstracted out? Right now it's hardcoded to ZhipuAI, but you've discussed model-agnostic design before. Do it today or not?
A: Yes, we should do it today.
(keep it minimal. Just wrap the ZhipuAI call in a private method — that satisfies the roadmap's anti-goal ("don't build a model abstraction layer") while still giving you a single point of change if you ever do need to switch later.)

## -- day 8 -- 

### -- design -- 
Q1: When a stranger runs your agent, what's most likely to break? List 5+ failure modes.
A: 
1. They don't know how to set the LLM API Key. In our case, we already have one in the .env.
2. They don't use ZhipuAI, which we're using. Maybe a compatible API is needed.
3. They use control + c to end the process which breaks the saving logic.
4. In the second session, they ask about a reply in the first session, which is never stored.
5. They haven't install the dependencies.
6. The model they use may not understand the prompt well.
(
Genuinely strong catches:
#1 (API key setup confusion) — directly addressed by today's work
#3 (Ctrl+C breaks saving) — real, you found this yourself on Day 6
#5 (dependencies not installed) — real first-contact friction
A few the roadmap specifically hints at that you're missing:
Wrong/invalid API key (different from "not set" — the key exists but is rejected by the API)
ZhipuAI service down or network drop — what happens when the API call itself fails mid-request?
Corrupted save file — what if agent_memory.json gets manually edited and becomes invalid JSON?
Wrong Python version — you hit this exact problem yourself on Day 5 (torch wheel mismatch)!
)

Q2: For each failure, should it fail loud or degrade gracefully? Give your reasoning for at least a few of them.
A:
- API key setup confusion and Wrong/invalid API key / ZhipuAI service down or network drop should fail loudly otherwise nothing is generated.
- Ctrl+C breaks saving, maybe we can give a warning but let the user make the decision
- dependencies not installed and Wrong Python version. Fail loudly or it breaks.
- Corrupted save file — what if agent_memory.json gets manually edited and becomes invalid JSON? Fall back to without long-term memory and tell the use the truth. No need to exit since the agent still works.
- The most important, this framework is for developers rather than end users and this is why "fail loud" is correct.

(recondieration: corrupted save file needs failing loudly: "Your memory file is corrupted, here's the exact path, fix it or delete it to start fresh.")

Q3: In __init__, which parameters deserve sensible defaults? Which must the user provide?
A:
api_key must be provided by the user
model can be with default if we stick to ZhipuAI, if we make it flexible, it's better to let the user provide
max_tokens defaults with a heuristic value
persist_path has defaults at the same dir
top_k has sensible defaults

(
For the api_key, user passes nothing (Agent() or doesn't include the parameter) → api_key defaults to None → the code falls back to checking .env via os.getenv(...)
if both fail — no explicit key passed AND no .env variable set — only then does it raise the loud error: "API key required. Either pass api_key=... or set the ZHIPU_API_KEY environment variable."
)

Q4: How does your framework communicate errors? Just raise generic Exception? Or custom error types like AgentError, MemoryError, RetrievalError?
A: Absolutely custom error types. A few more lines of code would get a lot of convenience in debugging.

(For today, keep it minimal per the anti-goals — maybe 2-3 custom types is enough, not a deep hierarchy:
AgentError
APIKeyError
MemoryFileError
)

### -- evaluation -- 

1. cd /tmp
git clone <your-repo-url> test-fresh
cd test-fresh
git checkout feat/memory-v0

clone the repo fresh 
then try to run it

➜  test-fresh git:(feat/memory-v0) uv run main.py
Using CPython 3.11.15
Creating virtual environment at: .venv
Installed 66 packages in 4.51s
Traceback (most recent call last):
  File "/private/tmp/test-fresh/main.py", line 22, in <module>
    main()
  File "/private/tmp/test-fresh/main.py", line 7, in main
    agent = Agent(api_key=os.getenv("ZAI"))
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/test-fresh/agent.py", line 28, in __init__
    raise APIKeyError(
errors.APIKeyError: API key required. Either pass api_key=... or set the ZAI environment variable in your .env file.

Finding: Dependencies installed silently and automatically via uv run — no manual uv add needed by the stranger. 

2. after setting up api key

➜  test-fresh git:(feat/memory-v0) uv run main.py      
Agent ready. Type 'quit' to exit.
Hi, my name is Homer.

errors.AgentError: LLM call failed after 2 attempts: None

3. should auth errors skip retry?
No. We don't know if it is an auth failure or a network problem until it happens. Retry is worth.

## -- day 9 --

Q1: What's the one-sentence pitch? Not "an agent framework" — what does yours uniquely offer?
A: RAG? Long/short memory? Slinding Window? Those fuzzy concepts you may hear a lot but have no ideas, once you start to build from scratch, these are very simple stuff.

(
A strong pitch usually answers: what is this, specifically, and what makes it different? Try compressing your idea into something closer to:

"An agent memory framework built from scratch, layer by layer — sliding window, summarization, retrieval, persistence — so you feel exactly why each one exists instead of just importing it."

Or shorter:

"A from-scratch agent memory framework designed to make RAG, summarization, and retrieval feel obvious instead of magical."
)

core idea: demystification

Q2: What goes in the README, and what gets deferred to the article? The deep "why" lives in the Medium piece — the README is the entry point.

A: 
In the README:
- How to use the framework. clone the repo, add api key to .env, install uv, uv run main.py
- Explain the architecture
- Explain the scope of the repo

B: 
- Explain the architecture
- Explain the key decisions in the process
- Explain the advantages and disadvantages
- Explain where to modify to have different behaviors

(
One refinement worth noting: "Explain the architecture" appears in both your README list and your article list, which is fine, but the depth should differ sharply.
README architecture section: just enough to show "I have a real, coherent structure" — a short paragraph plus maybe a simple diagram, like the roadmap's ASCII box example. Just naming the four layers and how they connect.
Article architecture section: this is where the OS-scheduling analogy, the L1/L2 cache metaphor, the human short-term/long-term memory comparison, the "bottleneck crossover" finding from Day 6 — all of that depth lives there, with the actual reasoning and tradeoffs you debated across 9 days.
)

Q3: Should the README include the OS scheduling / L1-L2 cache / write-back analogies you developed? Or save them entirely for the article?
A: No. These are for the article.

Q4: What's the honest scope claim? Don't oversell. What's the accurate, credible way to describe what this project actually is and isn't?
A:  it's not LangChain, not production-scale, not benchmarked, single-agent only, JSON-based not a vector DB ... 
it's mainly for understanding what an agent is and the mechanisms.

("A from-scratch agent memory framework built to expose how memory systems actually work — not a production-ready replacement for LangChain or CrewAI. It uses JSON persistence (not a vector DB), supports a single agent only, and hasn't been benchmarked or tested at scale (10k+ documents).")

## -- materials --

You now have four mental models stacked on this project:
OS scheduling (Day 2)
L1/L2 cache (Day 4)
Short-term/long-term human memory (Day 6)
Write-back vs write-through (Day 6)
