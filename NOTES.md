Today I'm building the simplest possible memory. No retrieval, no summarization, no token limits. Just a list.

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