import asyncio
import os
from dotenv import load_dotenv

from llama_index.llms.groq import Groq
from llama_index.tools.tavily_research import TavilyToolSpec
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent,AgentWorkflow,AgentInput,AgentOutput,AgentStream,ToolCall,ToolCallResult
from llama_index.core.workflow import Context
from tavily import AsyncTavilyClient

load_dotenv()

llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)

tavily_tool = TavilyToolSpec(api_key=os.getenv("TAVILY_API_KEY"))

# --- create our Tools  ------------------------------------------------

async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key="tvly-...")
    return str(await client.search(query))


async def record_notes(ctx: Context, notes: str, notes_title: str) -> str:
    """Useful for recording notes on a given topic. Your input should be notes with a title to save the notes under."""
    async with ctx.store.edit_state() as ctx_state:
        if "research_notes" not in ctx_state["state"]:
                ctx_state["state"]["research_notes"] = {}
        ctx_state["state"]["research_notes"][notes_title] = notes
    return "Notes recorded."


async def write_report(ctx: Context, report_content: str) -> str:
    """Useful for writing a report on a given topic. Your input should be a markdown formatted report."""
    async with ctx.store.edit_state() as ctx_state:
        ctx_state["state"]["report_content"] = report_content
    return "Report written."


async def review_report(ctx: Context, review: str) -> str:
    """Useful for reviewing a report and providing feedback. Your input should be a review of the report."""
    async with ctx.store.edit_state() as ctx_state:
        ctx_state["state"]["review"] = review
    return "Report reviewed."



# --- create our specialist agents ------------------------------------------------
research_agent = FunctionAgent(
    name="ResearchAgent",
    description="Search the web and record notes.",
    system_prompt="You are a researcher… hand off to WriteAgent when ready.",
    llm=llm,
    tools=[search_web, record_notes],
    can_handoff_to=["WriteAgent"],
)

write_agent = FunctionAgent(
    name="WriteAgent",
    description="Writes a markdown report from the notes.",
    system_prompt="You are a writer… ask ReviewAgent for feedback when done.",
    llm=llm,
    tools=[write_report],
    can_handoff_to=["ReviewAgent", "ResearchAgent"],
)

review_agent = FunctionAgent(
    name="ReviewAgent",
    description="Reviews a report and gives feedback.",
    system_prompt="You are a reviewer…",  # etc.
    llm=llm,
    tools=[review_report],
    can_handoff_to=["WriteAgent"],
)

# --- wire them together ----------------------------------------------------------
agent_workflow = AgentWorkflow(
    agents=[research_agent, write_agent, review_agent],
    root_agent=research_agent.name,
    initial_state={
        "research_notes": {},
        "report_content": "Not written yet.",
        "review": "Review required.",
    },
)


async def main():

        # resp = await agent_workflow.run(
        # user_msg="Write me a report on the history of the web …"
        # )
        # print(resp)
        handler = agent_workflow.run(
        user_msg=(
        "Write me a report on the history of the internet. "
        "Briefly describe the history of the internet, including the development of the internet, the development of the web, "
        "and the development of the internet in the 21st century."
         ))

        current_agent = None
        current_tool_calls = ""
        async for event in handler.stream_events():
                if (
                        hasattr(event, "current_agent_name")
                        and event.current_agent_name != current_agent
                ):
                        current_agent = event.current_agent_name
                        print(f"\n{'='*50}")
                        print(f"🤖 Agent: {current_agent}")
                        print(f"{'='*50}\n")

                # if isinstance(event, AgentStream):
                #     if event.delta:
                #         print(event.delta, end="", flush=True)
                # elif isinstance(event, AgentInput):
                #     print("📥 Input:", event.input)
                elif isinstance(event, AgentOutput):
                        if event.response.content:
                                print("📤 Output:", event.response.content)
                        if event.tool_calls:
                                print(
                                "🛠️  Planning to use tools:",
                                [call.tool_name for call in event.tool_calls],
                                )
                elif isinstance(event, ToolCallResult):
                        print(f"🔧 Tool Result ({event.tool_name}):")
                        print(f"  Arguments: {event.tool_kwargs}")
                        print(f"  Output: {event.tool_output}")
                elif isinstance(event, ToolCall):
                        print(f"🔨 Calling Tool: {event.tool_name}")
                        print(f"  With arguments: {event.tool_kwargs}")

            
            
if __name__ == "__main__":
    asyncio.run(main())
    
    
"""
----------WorkFlow of this code --------------------
User Query
   ↓
ResearchAgent
   ↓ (search + notes)
WriteAgent
   ↓ (write report)
ReviewAgent
   ↓ (feedback)
WriteAgent (optional rewrite)
   ↓
Final Output


Think of main() like:
        🎬 Behind-the-scenes camera of a team working
                You see who is working (agent)
                What they decide (output)
                What tools they use
                What results they get
                
"""


"""
----------Function Agent vs ReAct Agent --------------

1. Function Agent 

=> FunctionAgent is an agent that uses structured function (tool) calling.
=> 👉 The LLM does not “think in text steps”, it directly outputs structured tool calls.
=> You define functions (tools) with clear schemas (name, inputs, outputs)


🧠 How it works
    The LLM:
        Chooses a function
        Fills arguments in JSON format
        Executes the function
        Uses the result to continue 
        
💡 When to use
        You want reliable, production-grade workflows
        You need strict input/output formats
        You are integrating APIs, databases, or automation
        
➡️ Internally:
        LLM selects get_weather
        Passes { "city": "Delhi" }
        Returns result cleanly

2.  ReAct Agent (Reason + Act approach)

=> ReActAgent implements the ReAct paradigm (Reasoning + Acting), introduced in the paper
=> 👉 The LLM explicitly reasons step-by-step in natural language before acting.

🧠 How it works
        The LLM generates a chain of thought loop:
        Thought → reasoning step
        Action → choose tool
        Observation → result
        Repeat until final answer
        
💡 When to use
        You want transparent reasoning
        Tasks require multi-step thinking
        Exploration / research-style queries

➡️ Internally:
        Thought: I need to find PM of India
        Action: search("PM of India")
        Observation: Narendra Modi
        Thought: Now find his age
        Action: search("Narendra Modi age")
        Observation: 73
        Final Answer: ...
        
Note :  If the LLM you are using supports tool calling, you can use the FunctionAgent class. 
        Otherwise, you can use the ReActAgent class.
        
"""