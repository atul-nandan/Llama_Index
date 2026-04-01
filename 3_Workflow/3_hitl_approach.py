import asyncio

# ─────────────────────────────────────────────
# Fake event classes (mimicking llama-index style)
# ─────────────────────────────────────────────

class StartEvent:
    pass

class StopEvent:
    def __init__(self, result):
        self.result = result

class InputRequiredEvent:
    def __init__(self, prefix):
        self.prefix = prefix           # the question shown to the user

class HumanResponseEvent:
    def __init__(self, response):
        self.response = response       # what the human typed


# ─────────────────────────────────────────────
# APPROACH 1 — Simple Streaming (two steps)
# Best for: CLI tools, simple scripts
# ─────────────────────────────────────────────

async def approach_1():
    print("\n" + "="*50)
    print("APPROACH 1: Simple Streaming")
    print("="*50)

    # Simulate: step1 fires an InputRequiredEvent
    async def step1(ev: StartEvent) -> InputRequiredEvent:
        print("[Workflow] step1 running...")
        return InputRequiredEvent(prefix="What is your name? ")

    # Simulate: step2 handles the human response
    async def step2(ev: HumanResponseEvent) -> StopEvent:
        print("[Workflow] step2 running...")
        return StopEvent(result=f"Hello, {ev.response}!")

    # --- Main loop ---
    event = await step1(StartEvent())           # workflow starts

    if isinstance(event, InputRequiredEvent):
        print(f"[You] Prompt received: '{event.prefix}'")
        user_input = input(event.prefix)        # collect from human
        human_event = HumanResponseEvent(response=user_input)

    final = await step2(human_event)            # workflow resumes
    print(f"[Result] {final.result}")


# ─────────────────────────────────────────────
# APPROACH 2 — Stop & Resume (serialized state)
# Best for: web apps, async systems where response
# arrives much later (e.g. via HTTP POST)
# ─────────────────────────────────────────────

async def approach_2():
    print("\n" + "="*50)
    print("APPROACH 2: Stop & Resume (serialized state)")
    print("="*50)

    # Simulate step1
    async def step1(ev: StartEvent) -> InputRequiredEvent:
        print("[Workflow] step1 running...")
        return InputRequiredEvent(prefix="Enter a number: ")

    # Simulate step2
    async def step2(ev: HumanResponseEvent) -> StopEvent:
        print("[Workflow] step2 running...")
        return StopEvent(result=f"You entered: {ev.response}")

    # --- Phase 1: run until question is asked, then STOP ---
    event = await step1(StartEvent())

    if isinstance(event, InputRequiredEvent):
        # Serialize context (in real code: ctx.to_dict() → store in DB/Redis)
        saved_state = {"prefix": event.prefix, "step": "waiting_for_human"}
        print(f"[Workflow] Paused. State saved: {saved_state}")
        print("[Workflow] cancel_run() called — workflow is frozen.")

    # ... imagine a web request comes in later ...
    print("\n[...time passes... HTTP POST arrives with user's answer...]\n")

    # --- Phase 2: restore context and resume ---
    # (In real code: Context.from_dict(workflow, ctx_dict))
    restored_prefix = saved_state["prefix"]
    print(f"[Restored] Workflow resumed. Original question was: '{restored_prefix}'")

    user_input = input(restored_prefix)         # simulate the delayed human response
    human_event = HumanResponseEvent(response=user_input)

    final = await step2(human_event)            # resume workflow
    print(f"[Result] {final.result}")


# ─────────────────────────────────────────────
# APPROACH 3 — wait_for_event (single step)
# ⚠ WARNING: code before wait_for_event runs TWICE
#   Make sure it's idempotent (safe to repeat)
# ─────────────────────────────────────────────

async def approach_3():
    print("\n" + "="*50)
    print("APPROACH 3: wait_for_event (single step)")
    print("="*50)

    # Simulated wait_for_event — runs setup code, pauses, then resumes
    async def ask_user(ev: StartEvent) -> StopEvent:

        # ⚠ This block runs TWICE (once to reach the waiter, once on resume)
        # So it MUST be idempotent — no side effects like DB writes here!
        print("[Step] Setup code running... (this runs twice in real impl)")

        # Simulate wait_for_event pausing and waiting for human input
        print("[Step] wait_for_event() called — sending InputRequiredEvent")
        waiter_event = InputRequiredEvent(prefix="Pick a color: ")

        # Simulate the pause: in reality an internal exception halts execution
        print("[Step] (paused internally, waiting for HumanResponseEvent...)")
        user_input = input(waiter_event.prefix)         # human responds

        # Simulate resume after HumanResponseEvent arrives
        response_event = HumanResponseEvent(response=user_input)
        print("[Step] Resumed after human response.")

        return StopEvent(result=f"You picked: {response_event.response}")

    final = await ask_user(StartEvent())
    print(f"[Result] {final.result}")


# ─────────────────────────────────────────────
# Run all three
# ─────────────────────────────────────────────

async def main():
    await approach_1()
    await approach_2()
    await approach_3()

asyncio.run(main())