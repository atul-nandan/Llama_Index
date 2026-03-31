# ---- Workflow Imports ----
from llama_index.core.workflow import (
    Workflow,
    Context,
    step,
)
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

# ─────────────────────────────
# Global Settings
# ─────────────────────────────

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

Settings.llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
)

# ─────────────────────────────
# Events
# ─────────────────────────────

class FirstEvent(Event):
    first_output: str


class SecondEvent(Event):
    second_output: str
    response: str


class ProgressEvent(Event):
    msg: str


# ─────────────────────────────
# Workflow
# ─────────────────────────────

class MyWorkflow(Workflow):

    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> FirstEvent:
        print(ev.first_input) #"Start the workflow."
        ctx.write_event_to_stream(
            ProgressEvent(msg="Step one is happening")
        )

        return FirstEvent(first_output="First step complete.")
    
    # if you wants to print the fields of FirstEvent Class do "event=FirstEvent(....)" and then pass to "ctx.write_event_to_stream(event)"
    # @step
    # async def step_one(self, ctx: Context, ev: StartEvent) -> FirstEvent:
    #     print(ev.first_input)

    #     ctx.write_event_to_stream(
    #         ProgressEvent(msg="Step one is happening")
    #     )

    #     event = FirstEvent(first_output="First step complete.")
    #     ctx.write_event_to_stream(event)
    #     return event

    @step
    async def step_two(self, ctx: Context, ev: FirstEvent) -> SecondEvent:

        # use global LLM from Settings
        generator = await Settings.llm.astream_complete(
            "Please give me the first 3 paragraphs of Guliver travels, "
            "a book in the public domain."
        )

        full_resp = ""

        #Streaming each word in the generator
        async for response in generator:
            ctx.write_event_to_stream(
                ProgressEvent(msg=response.delta)
            )
            full_resp += response.delta

        ctx.write_event_to_stream(
            ProgressEvent(msg="Step Two is happening")
        )
        return SecondEvent(
            second_output="Second step complete",
            response=full_resp,
        )

    # Streaming fields of SecondEvent class 
    # @step
    # async def step_two(self, ctx: Context, ev: FirstEvent) -> SecondEvent:

    #     full_resp = ""
    #     ctx.write_event_to_stream(
    #         ProgressEvent(msg="Step Two is happening")
    #     )

    #     event = SecondEvent(
    #         second_output="Second step complete",
    #         response=full_resp,
    #     )
    #     ctx.write_event_to_stream(event)
    #     return event
    
    
    @step
    async def step_three(self, ctx: Context, ev: SecondEvent) -> StopEvent:
        ctx.write_event_to_stream(
            ProgressEvent(msg="Step three is happening")
        )

        return StopEvent(result="Workflow complete.")


# ─────────────────────────────
# Run Workflow
# ─────────────────────────────

async def main():
    # timeout=30 => This sets a maximum execution time for the workflow.
    # Meaning: If the workflow runs longer than 30 seconds, it will automatically stop.
    
    # verbose=True => Turns on debug logging.
    # You will see: step execution logs, event routing info, workflow progress, debugging messages
    # When "verbose=True" in console is like: 
            # Running step step_one
            # Step step_one produced event <class '__main__.FirstEvent'>
            # Running step step_two
            # Step step_two produced event <class '__main__.SecondEvent'>
            # Running step step_three
            # Step step_three produced event <class 'workflows.events.StopEvent'>
    
    w = MyWorkflow(timeout=30)
    # w = MyWorkflow(timeout=30, verbose=True)

    handler = w.run(first_input="Start the workflow.")

    async for ev in handler.stream_events():
        if isinstance(ev, ProgressEvent):
            print(ev.msg)
        if isinstance(ev, FirstEvent):
            print(ev.first_output)
        if isinstance(ev, SecondEvent):
            print(ev.response)

    final_result = await handler
    print("Final result:", final_result)


if __name__ == "__main__":
    asyncio.run(main())