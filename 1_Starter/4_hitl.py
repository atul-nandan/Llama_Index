# -------HITL ==> Human In The Loop ----------------
import asyncio
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent
from llama_index.core.workflow import Context
from llama_index.llms.groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

# Defining the model 
llm=Groq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
    )

async def dangerous_task(ctx: Context) -> str:
    """A dangerous task that requires human confirmation."""

    # emit an event to the external stream to be captured
    ctx.write_event_to_stream(
        InputRequiredEvent(
            prefix="Are you sure you want to proceed? ",
            user_name="Laurie",
        )
    )

    # wait until we see a HumanResponseEvent
    response = await ctx.wait_for_event(
        HumanResponseEvent, requirements={"user_name": "Laurie"}
    )

    # act on the input from the event
    if response.response.strip().lower() == "yes":
        return "Dangerous task completed successfully."
    else:
        return "Dangerous task aborted."

workflow = AgentWorkflow.from_tools_or_functions(
    [dangerous_task],
    llm=llm,
    system_prompt="You are a helpful assistant that can perform dangerous tasks.",
)

async def main():
    handler = workflow.run(user_msg="I want to proceed with the dangerous task.")

    async for event in handler.stream_events():
        # capture InputRequiredEvent
        if isinstance(event, InputRequiredEvent):
            # capture keyboard input
            response = input(event.prefix)
            # send our response back
            handler.ctx.send_event(
                HumanResponseEvent(
                    response=response,
                    user_name=event.user_name,
                )
            )

    response = await handler
    print(str(response))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
    
"""  ------------Human In The Loop -----------------

What is HITL ?
=> Human In The Loop
=> It Talks about involvement of human at a particular Step, where AI cant take decision on its own
=> Imagine an AI writing an email:
        AI drafts the email
        It pauses and asks: “Should I send this?”
        Human says: “Yes” or “Edit this”
        AI acts based on that input
        👉 That pause + human input = Human-in-the-Loop

🔹 Simple explanation
        => AI does the task step-by-step
        => At particular step Human reviews, guides, or approves at certain steps for ex: Payment, Database access
        => Then AI continues

1. wait_for_event 
    => This is where your workflow actually stops and waits. and says: “I will not continue until I get the right response.”
    => It stops the Internal work flow and ask for a response.
    => it is used to wait for a HumanResponseEvent.
    => it is a Function / mechanism

2. waiter_event 
    => it is the event that is written to the event stream, to let the caller know that we are waiting for a response.
    => This is an event you emit to tell the outside world: “I'm currently waiting for input.”
    => It is an object. 

3. waiter_id 
    => it is a unique identifier for this specific wait call. It helps ensure that we only send one waiter_event for each waiter_id.
    => Multiple waits can exist (especially in async or multi-agent flows)
            It Ensures:
                Only one “waiting” signal is emitted
                The correct response resumes the correct step

4. requirements 
    =>argument is used to specify that we want to wait for a HumanResponseEvent with a specific user_name.

"""