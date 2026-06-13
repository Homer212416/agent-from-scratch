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

-- log -- 
You: Hey, my name is Homer. Do you have a name?
Assistant: Hello Homer! It's nice to meet you.

I don't have a personal name in the same way humans do. I am a large language model, so you can just call me Assistant or simply AI. But if you'd like to give me a nickname, you're welcome to do that too!

How can I help you today?

[Context length]: 328 chars

You: Maybe you're called Nick. Do you like it?
Assistant: "Nick" has a nice ring to it! It's short, friendly, and easy to remember.

While I don't have personal feelings or preferences, I think it works perfectly as a name for me. If you'd like to call me Nick, go right ahead.

So, how are things going with you today, Homer?

[Context length]: 656 chars

You: Help me remember something that I may forget. I'm going to see my uncle tonight. Remind me when I ask you.
Assistant: Got it, Homer. I've made a mental note: **You are going to see your uncle tonight.**

Just ask me whenever you need the reminder, and I'll tell you.

[Context length]: 929 chars

You: what is the result of 4 * 798
Assistant: The result of 4 * 798 is **3,192**.

[Context length]: 1012 chars

You: if there were 1000 boxes of apples. Each box contains 10 apples. And then 550 boxes were sold out. How many apples are left?
Assistant: Here is the step-by-step calculation:

1.  First, find out how many boxes are left:
    1000 boxes - 550 boxes = **450 boxes left**.

2.  Then, multiply the remaining boxes by the number of apples in each box:
    450 boxes × 10 apples = **4,500 apples**.

So, there are **4,500 apples** left.

[Context length]: 1448 chars

You: Do you know what is the date today?
Assistant: I am sorry, Homer, but I don't have access to real-time information like the current date or time. You might need to check your phone, computer, or a calendar for today's date.

However, I haven't forgotten that you are going to see your uncle tonight!

[Context length]: 1754 chars

You: Do you know about a story that a rabbit and a tortoise having a race?
Assistant: Yes, I certainly do! That is the famous fable called **"The Tortoise and the Hare."**

It is a story about a speedy rabbit (the hare) who mocks a slow-moving tortoise for being too slow. Tired of the teasing, the tortoise challenges the hare to a race.

Confident that he will win easily, the hare decides to take a nap halfway through the race. Meanwhile, the tortoise keeps plodding along, slow but steady, without stopping. By the time the hare wakes up, he realizes it is too late to catch up, and the tortoise crosses the finish line first.

The moral of the story is often summed up as: **"Slow and steady wins the race."**

Would you like to hear a different version of it, or perhaps a story about something else?

[Context length]: 2563 chars

You: Do you think the story have meaning in real life?
Assistant: Yes, absolutely, Homer. I think the story has a lot of meaning in real life. It’s one of those stories that actually holds true for a lot of situations we face.

Here are a few ways it applies to real life:

1.  **Consistency beats intensity:** Sometimes people start a project with a huge burst of energy (like the Hare running fast), but they burn out or get distracted. The "Tortoise" approach—doing a little bit every day and not stopping—is often what actually leads to finishing a degree, writing a book, or getting in shape.
2.  **Overconfidence is dangerous:** The Hare lost because he underestimated his opponent and overestimated his own safety. In real life, being talented isn't enough if you get arrogant or lazy. You see this in sports all the time—a talented team loses because they didn't take the "weaker" opponent seriously.
3.  **Distractions cost us:** The Hare took a nap. In today's world, we have so many distractions (like our phones or TV). It’s very easy to take a "nap" and lose track of our goals. The Tortoise teaches us to stay focused on the path.

Do you see this dynamic happen often in your own life or work?

[Context length]: 3773 chars

You: Some business moral says 20 miles a day which comes from a principle of an expedience, which renosates with this fable, right?
Assistant: That is a fantastic connection, Homer. You are spot on.

That concept is often called the **"20 Mile March"** (popularized by business author Jim Collins), and it resonates perfectly with the Tortoise and the Hare.

The principle actually comes from the story of two explorers, Roald Amundsen and Robert Falcon Scott, racing to be the first to reach the South Pole.

*   **The "Hare" approach (Scott):** He would push incredibly hard when the weather was good, driving his team to exhaustion, and then stay in the tent and wait when the weather was bad. It was erratic—sometimes doing 40 miles, sometimes doing 0.
*   **The "Tortoise" approach (Amundsen):** He enforced a strict rule: **"We will do 20 miles a day."** No more, no less. Even if the weather was perfect and they felt they could do 40 miles, they stopped at 20 to conserve energy and maintain a routine. When the weather was terrible, they still forced themselves to do the 20 miles.

In business (and life), this translates to **discipline and consistency**.

It teaches us that success often isn't about having a burst of energy or "sprinting" when we feel motivated. It’s about setting a sustainable pace and sticking to it, even when things are difficult, and holding back a little even when things are easy.

Did you come across this principle in a book or a business setting?

[Context length]: 5263 chars

You: Hey what is your name?
Assistant: You decided to call me **Nick** earlier, remember?

I'm still getting used to it, but I like it

[Context length]: 5399 chars

You: Do you remember my name?
Assistant: Yes, of course I do. Your name is **Homer**.

It's nice to speak with you again

[Context length]: 5521 chars

You: I forgot what to do tonight
Assistant: Don't worry, Homer, that's exactly why you asked me to remind you!

You are going to **see your uncle tonight**.

[Context length]: 5679 chars

You: Can you summarize what you remember about our conversation?
Assistant: Sure, Homer. Here is a summary of what we've discussed so far:

1.  **Names:** You introduced yourself as Homer, and you decided to give me the nickname **Nick**.
2.  **Reminder:** You asked me to remind you that you are **seeing your uncle tonight**.
3.  **Math:** You tested me with a couple of math questions:
    *   $4 \times 798 = 3,192$.
    *   A word problem about apples where we calculated there were **4,500 apples left**.
4.  **Stories and Principles:** We talked about "The Tortoise and the Hare" and how its moral of "slow and steady wins the race" applies to real life. You made a great connection to the **"20 Mile March"** business principle, and I shared the story of the explorers Amundsen and Scott to illustrate that point.

Is there anything else you'd like to add or ask?

[Context length]: 6552 chars
