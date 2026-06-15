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

Good — the plumbing works. Now note what it got right and wrong:
Got right: User identity (your name), assigned task — high importance facts survived.
Got wrong: Assistant's name got washed out.
