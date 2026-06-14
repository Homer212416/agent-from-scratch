Today I'm building the simplest possible memory. No retrieval, no summarization, no token limits. Just a list.

-- day 1 --

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

-- day 2 --

Question 1: Should the limit be measured in number of messages or number of tokens/characters? Pick one and write down why.

Answer: I think it should be the number of tokens. Since the API limit or context window is measured by tokens, it is reasonable the same for the limit.

(Token counting requires either a library (tiktoken) or an approximation (len(content) / 4). Number of messages is cruder but simpler.

Question 2: When the limit is hit, do you drop the oldest message, the oldest user+assistant pair, or something else? Why?

Answer: I choose to drop the oldest messages but except the marked ones.

(for today's code, keep it simple — no marking system yet. Just drop the oldest user+assistant pair. Dropping a single message could leave an orphaned assistant reply that would confuse the model. Dropping the pair keeps the conversation structure clean.)

Question 3: Should the system prompt / initial instructions be exempt from the limit? Why or why not?

Answer: Yes, it should be. Otherwise the model forgot some important context.
