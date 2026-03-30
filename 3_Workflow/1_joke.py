# ---- Workflow Imports (Correct Path) ----
from llama_index.core.workflow import Workflow, step
from llama_index.core.workflow.events import (
    Event,
    StartEvent,
    StopEvent,
)

# ---- LlamaIndex Settings ----
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq

# ---- Python ----
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

# Global Settings

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

Settings.llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
)

# Custom Event
# This defines a custom workflow event.
# An Event is a message object used to pass data between workflow steps.
# Think of it as:
# A container that carries information from one step to another.

class JokeEvent(Event):
    joke: str

# Workflow Definition

class JokeFlow(Workflow):

    @step
    async def generate_joke(self, ev: StartEvent) -> JokeEvent:
        topic = ev.topic

        prompt = f"Write your best joke about {topic}."
        response = await Settings.llm.acomplete(prompt)

        return JokeEvent(joke=str(response))

    @step
    async def critique_joke(self, ev: JokeEvent) -> StopEvent:
        joke = ev.joke

        prompt = f"Give a thorough analysis and critique of the following joke: {joke}"
        response = await Settings.llm.acomplete(prompt)

        return StopEvent(result=str(response))

# Async Entry Point 
async def main():
    w = JokeFlow(timeout=60, verbose=False)
    result = await w.run(topic="pirates")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
    
    
# ----------------------------------------------------------------------------------------------------------------
# Output
"""
**A deep‑dive into the joke**

> **Why did the pirate bring a ladder to the bar?
>  Because he heard the drinks were on the house—he just wanted to *raise* the stakes!**

---

## 1. Structure & Delivery

| Element | What it does | How it works in this joke |
|---------|--------------|---------------------------|
| **Setup** | “Why did the pirate bring a ladder to the bar?” | Classic “Why did X?” format. It primes the listener for a simple, literal answer (e.g., “to climb the bar”). |
| **Punchline** | “Because he heard the drinks were on the house—he just wanted to *raise* the stakes!” | The punchline delivers a double‑meaning pun that flips the expectation. |
| **Timing** | The joke is short, so the punchline lands almost immediately after the question. | The brevity keeps the audience from over‑thinking the setup, making the pun feel fresh. |

**Strengths**

* **Immediate payoff** – The joke is only two lines long, so the punchline arrives quickly, which is ideal for a quick laugh or a “dad‑joke” setting.
* **Clear setup** – The “pirate + ladder + bar” image is vivid and instantly recognizable, giving the audience a concrete mental picture to latch onto.        

**Weaknesses**

* **Predictability** – The “Why did X?” format is overused. If the audience is familiar with this trope, the joke may feel stale.
* **Pacing** – Because the punchline is delivered right after the question, there’s little room for a build‑up or a twist that could make the joke more surprising.

---

## 2. Wordplay & Double Entendre

| Phrase | Literal meaning | Figurative meaning | How it’s used |
|--------|-----------------|--------------------|---------------|
| **“On the house”** | Drinks served from the roof of the bar (i.e., free). | “Free” or “complimentary.” | Sets up the expectation that the drinks are free. | 
| **“Raise the stakes”** | Literally lift stakes (wooden posts). | Increase the risk or amount at stake. | The ladder is the tool that lets the pirate *physically* raise stakes. |

**Why it works**

* The pun hinges on the homonym “stakes” (wooden posts vs. risk). The ladder is a plausible tool for physically raising stakes, but it’s also a metaphor for increasing the stakes in a game or gamble.
* The phrase “on the house” is a common idiom, so the audience instantly knows the double meaning.

**Why it might feel forced**

* The ladder is a bit of a stretch as a pirate’s tool. Pirates are more associated with swords, parrots, and treasure chests, not ladders. The image feels slightly out‑of‑place, which can make the pun feel contrived.
* The pun is very “on‑the‑nose.” Some listeners might find it too obvious and respond with a groan rather than a laugh.

---

## 3. Cultural & Contextual Factors

| Factor | Impact |
|--------|--------|
| **Pirate tropes** | The joke relies on the stereotypical pirate image (eye patch, “Arr!”). This is universally understood, but also very generic. |
| **Bar culture** | “On the house” is a bar‑specific idiom. If the audience isn’t familiar with bar lingo, the joke loses a layer of humor. |
| **Ladder imagery** | Ladders are common in many jokes (e.g., “Why did the chicken cross the road?”). The ladder here is a visual cue that can help the joke land quickly. |

---

## 4. Audience & Setting

| Audience | Likely reaction | Why |
|----------|-----------------|-----|
| **Kids / family** | Laugh or giggle | The pun is simple, the pirate image is cute, and the joke is clean. |
| **Adults / bar crowd** | Mixed – some groan, some chuckle | The pun is a bit “dad‑joke” territory; adults might appreciate the wordplay but also recognize its simplicity. |
| **Pun‑savvy / comedy writers** | Mild amusement | The joke is a textbook example of a pun, but it doesn’t break new ground. |

---

## 5. Strengths & Weaknesses Summarized

| Strength | Weakness |
|----------|----------|
| **Clear, vivid imagery** – pirate + ladder + bar | **Predictable format** – “Why did X?” |
| **Dual‑meaning pun** – “on the house” + “raise the stakes” | **Ladder feels out of place** – not a typical pirate prop |
| **Short & punchy** – good for quick laughs | **Pun is obvious** – may elicit a groan |
| **Family‑friendly** – no offensive content | **Limited depth** – no surprise twist or deeper joke |

---

## 6. How to Improve / Variations

### 1. Add a Twist

> **Why did the pirate bring a ladder to the bar?**
> **Because he heard the drinks were on the house, so he wanted to climb the social ladder!**

*Why it helps:* The “social ladder” pun adds a second layer of wordplay and feels less forced.

### 2. Play with Pirate Lingo

> **Why did the pirate bring a ladder to the bar?**
> **Because he heard the drinks were on the house, and he wanted to *raise* the stakes—arr!**

*Why it helps:* The pirate exclamation (“arr!”) reinforces the character and gives a little extra punch.

### 3. Make the Ladder More Pirate‑ish

> **Why did the pirate bring a ladder to the bar?**
> **Because he heard the drinks were on the house, so he wanted to *climb* the treasure chest of free drinks!**

*Why it helps:* Replacing “ladder” with “climb” or “treasure chest” ties the prop more closely to pirate lore.

### 4. Use a Different Idiom


"""