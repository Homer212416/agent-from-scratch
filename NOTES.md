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