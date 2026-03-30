## 🔥🔥🔥LlamaIndex — Context, ctx, and store

### 🔥 The core idea in one line

`Context` is a **shared notepad** passed to every step in a workflow.
`ctx` is your variable holding it inside a step.
`ctx.store` is where you actually read and write data.

---

### 🔥 Mental model

```
Workflow Run
   │
   └── Context (ctx)
          │
          └── store  ← shared memory
                ├── user_query
                ├── retrieved_docs
                └── final_answer
```

```
workflow.run(ctx=ctx)
         │
         ▼
   ┌─────────────┐
   │   Context   │  ← the shared notepad object
   │             │
   │  .store ────┼──► {"user_name": "Alice", "score": 10, ...}
   │             │        ▲            ▲
   │  step_one ──┼─── set("user_name", "Alice")
   │  step_two ──┼─── get("user_name")  →  "Alice"
   │             │
   │  .is_running = True
   │  .write_event_to_stream(...)   ← push progress to UI
   │  .collect_events(...)          ← wait for multiple events
   └─────────────┘
```

---

### 🔥 ctx.store — the only thing you use 90% of the time

Three operations you need:

```python
# Write something
await ctx.store.set("my_key", some_value)

# Read it back (from any step)
value = await ctx.store.get("my_key")

# Read + modify safely (when multiple steps run at the same time)
async with ctx.store.edit_state() as state:
    state["counter"] = state.get("counter", 0) + 1
```

Think of it as a Python dict that any step can access — but async and thread-safe.

 **🔥 Concrete example**

```python
from llama_index.core.workflow import Workflow, step, Context
from llama_index.core.workflow.events import StartEvent, StopEvent

class MyWorkflow(Workflow):

    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> StopEvent:
        await ctx.store.set("user_name", "Alice")
        await ctx.store.set("score", 0)
        return StopEvent(result="done")

    @step
    async def step_two(self, ctx: Context, ev: SomeEvent) -> StopEvent:
        name  = await ctx.store.get("user_name")   # → "Alice"
        score = await ctx.store.get("score")        # → 0

        await ctx.store.set("score", score + 10)
        return StopEvent(result=f"{name} scored {score + 10}")
```

---

### **🔥The 4 things that actually matter on Context**

| Property / method | What it does |
|---|---|
| `ctx.store` | The key-value notepad shared across all steps |
| `ctx.is_running` | `True` while the workflow is executing |
| `ctx.write_event_to_stream(ev)` | Push a progress event to the UI / handler |
| `ctx.collect_events(ev, [TypeA, TypeB])` | Wait until all listed event types have arrived, then return them together |

---

**🔥Memory across multiple runs**

Normally each `workflow.run()` starts fresh. Create a `Context` yourself and pass it in to make the workflow **remember everything** between runs:

```python
ctx = Context(my_workflow)   # create once, reuse forever

# Run 1
await workflow.run(user_msg="Hi, my name is Alice", ctx=ctx)

# Run 2 — the workflow still knows the name!
result = await workflow.run(user_msg="What's my name?", ctx=ctx)
# → "Your name is Alice"
```

This is how you build chatbots and multi-turn agents with LlamaIndex workflows.

---

**🔥 Save and restore (for databases)**

```python
# Save context to your database
snapshot = ctx.to_dict()            # converts everything to a plain dict
db.save("session_123", snapshot)    # store wherever you want

# Later, restore it and continue
snapshot = db.load("session_123")
ctx = Context.from_dict(my_workflow, snapshot)
result = await workflow.run(..., ctx=ctx)   # picks up exactly where it left off
```



## 🔥The 3 internal "faces"

`Context` switches behaviour depending on where you are in the workflow.
You don't touch these directly — LlamaIndex manages them automatically.

| Where you are | Face active | What you can do |
|---|---|---|
| Before `workflow.run()` | `PreContext` | Configure / set up only |
| Inside a `@step` function | `InternalContext` | Read/write store, collect events, stream events |
| In handler code outside steps | `ExternalContext` | Send events in, check `is_running`, get result |

If you call a step-only method from outside a step, you get a clear `ContextStateError`.


## 🔥InMemoryStateStore — full API

This is the object behind `ctx.store`.

| Method | What it does |
|---|---|
| `await ctx.store.get("key")` | Read a value (supports dot-paths like `"user.profile.name"`) |
| `await ctx.store.set("key", val)` | Write a value (supports dot-paths) |
| `async with ctx.store.edit_state() as s:` | Atomic read-modify-write under a lock — safe for concurrent steps |
| `ctx.store.get_state()` | Get the entire state model at once |
| `ctx.store.set_state(model)` | Replace the entire state model (merge semantics for typed Pydantic models) |
| `await ctx.store.clear()` | Wipe all stored data |


## 🔥Typed state (advanced)

Instead of plain dict keys you can use a Pydantic model for type safety:

```python
from pydantic import BaseModel
from llama_index.core.workflow import Context

class MyState(BaseModel):
    user_name: str = ""
    score: int = 0

# Use it as a generic type
ctx: Context[MyState]

async with ctx.store.edit_state() as state:
    state.score += 10   # fully typed — IDE autocomplete works
```


## 🔥 collect_events — waiting for multiple events
```
Use when a step can receive multiple event types and should only proceed once all arrive:
```

```python
@step
async def synthesize(
    self, ctx: Context, ev: QueryEvent | RetrieveEvent
) -> StopEvent | None:
    events = ctx.collect_events(ev, [QueryEvent, RetrieveEvent])
    if events is None:
        return None     # still waiting for the other event type

    query_ev, retrieve_ev = events
    # now proceed with both
    return StopEvent(result="synthesized")
```



## 🔥write_event_to_stream — streaming progress to UI

```python
@step
async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
    ctx.write_event_to_stream(SomeProgressEvent(msg="Step started"))
    # ... do work ...
    return StopEvent(result="ok")

# In your handler / server:
handler = workflow.run(...)
async for ev in handler.stream_events():
    print(ev)   # receives all streamed events in real time
```


## 🔥Context vs StorageContext — don't confuse them

| | `Context` | `StorageContext` |
|---|---|---|
| Lives in | Workflows / Agents | Index building (RAG) |
| What it holds | Runtime state + event bus | Vector store, doc store, index store |
| You use it when | Running a workflow | Building / persisting an index |

```python
# StorageContext — completely separate, used for RAG indexes
from llama_index.core import StorageContext, VectorStoreIndex

storage_context = StorageContext.from_defaults(vector_store=my_vector_store)
index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
storage_context.persist("./my_index")
```


## 🔥 Context vs Memory

| | `Context` | `Memory` |
|---|---|---|
| Holds | Any key-value state + runtime info | `ChatMessage` objects (conversation history) |
| Scope | Entire workflow | Agent chat turns |
| Serializable | Yes, fully | Yes |

In practice, agents use **both** together:

```python
response = await agent.run("Hello!", ctx=ctx, memory=memory)
```


**Quick reference — constructor params**

```python
ctx = Context(
    workflow,                  # required — the workflow this context belongs to
    previous_context=None,     # optional — dict snapshot to resume from
    serializer=None,           # optional — JsonSerializer (default) or PickleSerializer
)
```



**Serializers**

| Serializer | When to use |
|---|---|
| `JsonSerializer` (default) | Safe for databases, cross-environment, recommended |
| `PickleSerializer` | Handles arbitrary Python objects, but not safe across Python versions |

```python
from llama_index.core.workflow.context import JsonSerializer

snapshot = ctx.to_dict(serializer=JsonSerializer())
```

---

 **known_unserializable_keys**

A class-level constant `= ("memory",)`.
Keys listed here are **skipped during serialization** — they hold objects
(like open LLM connections or asyncio state) that can't be pickled or JSON-encoded.
You don't set this yourself; it's built into the `Context` class.
