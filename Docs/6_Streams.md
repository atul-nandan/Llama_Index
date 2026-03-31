## 🔥🔥🔥**Streaming Events**
```
=>  Streaming means sending results little-by-little instead of waiting for everything to finish.

=>  Workflows can take time because they may:
        call LLMs
        run multiple steps
        branch logic
        use tools
    So LlamaIndex allows steps to send progress updates while running.
```
🧠 Without Streaming:
```
User asks question
        ↓
Workflow runs for 10 seconds
        ↓
User sees NOTHING
        ↓
Final answer appears
```
🧠 With Streaming:
```
User asks question
        ↓
"Step one is happening..."
        ↓
"Thinking..."
        ↓
"Generating text..."
        ↓
Words appear live...
        ↓
Final result
```

## **🧠 The Main Tool: "Context" & "write_event_to_stream"**

**🔥 what is Context ?**
```
Every step receives=>    ctx: Context

Think of Context as: a communication channel to the outside world.
```
For More Please checkout: [ 5_Context.md ](5_Context.md)


**📡 Sending Streaming Updates**
```
Inside a step:

ctx.write_event_to_stream(
    ProgressEvent(msg="Step one is happening")
)

This means: 
    Send this message immediately to whoever is listening.
    The workflow continues running.
```
**🪄 What Happens Internally**
```
Step running
     ↓
Send ProgressEvent
     ↓
User receives update instantly
     ↓
Step continues working
```

## 🔥🔥🔥**How streaming works — step by step**
```
=> While your workflow runs in the background, you listen to a stream of events it emits. 

=> Every time a step calls ctx.write_event_to_stream(...), that event becomes available to whoever is listening outside.
```

**Step 1 — create a custom progress event**
```py
class ProgressEvent(Event):
    msg: str
# This is just a regular LlamaIndex event with a message field. You can put anything in it.
```
**Step 2 — write events to the stream inside your steps**
```py
python@step
async def step_one(self, ctx: Context, ev: StartEvent) -> FirstEvent:
    ctx.write_event_to_stream(ProgressEvent(msg="Step one is happening"))
    return FirstEvent(first_output="done")
```
For LLM streaming (word by word), you loop over the generator and emit one event per chunk:
```py
@step
async def step_two(self, ctx: Context, ev: FirstEvent) -> SecondEvent:
    llm = OpenAI(model="gpt-4o-mini")
    generator = await llm.astream_complete("Your prompt here")

    full_resp = ""
    async for response in generator:
        ctx.write_event_to_stream(ProgressEvent(msg=response.delta))  # one word at a time
        full_resp += response.delta

    return SecondEvent(response=full_resp)
```

**Step 3 — run the workflow and listen**
```py
async def main():
    w = MyWorkflow(timeout=30)
    handler = w.run(first_input="Start")   # starts in background, returns immediately

    async for ev in handler.stream_events():   # listen for all streamed events
        if isinstance(ev, ProgressEvent):
            print(ev.msg)                      # print as they arrive

    final_result = await handler             # get the final result after stream ends
    print("Final result:", final_result)
```
```
Key point: w.run() does not block — it returns a handler immediately. The workflow runs in the background. handler.stream_events() is where you actually receive events as they happen. The stream ends automatically when a StopEvent is published.
```

**Step 4 — handle failures and termination events**
```py
#If the workflow ends abnormally, special events are published to the stream before the exception is raised:

async for ev in handler.stream_events():
    if isinstance(ev, WorkflowTimedOutEvent):
        print(f"Timed out after {ev.timeout}s — steps still running: {ev.active_steps}")
    elif isinstance(ev, WorkflowCancelledEvent):
        print("Workflow was cancelled")
    elif isinstance(ev, WorkflowFailedEvent):
        print(f"Step '{ev.step_name}' failed after {ev.attempts} attempts")
        print(f"Error: {ev.exception_message}")

```
**🔥Understanding the Role of Verbose and TimeOut**
```
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
```

To Understand with Code Please checkout: [ 2_streams.py ](../3_Workflow/2_streams.py)