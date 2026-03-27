import asyncio
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.groq import Groq
from llama_index.tools.tavily_research import TavilyToolSpec
from llama_index.core.agent.workflow import AgentStream,AgentOutput
from llama_index.core.tools import FunctionTool 
from dotenv import load_dotenv
import os

load_dotenv()

llm = Groq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)

tavily_tool = TavilyToolSpec(api_key=os.getenv("TAVILY_API_KEY"))


workflow = FunctionAgent(
    tools=tavily_tool.to_tool_list(),
    llm=llm,
    system_prompt="""You are a helpful assistant that will search on the internet.""",
)

async def main():
    handler =   workflow.run(user_msg="What is the weather in dehradun")
    # print(handler)
    
    async for event in handler.stream_events():
        if isinstance(event,AgentStream):
            print(event.delta, end="", flush=True)
            
            
if __name__ == "__main__":
    asyncio.run(main())
    
# Output 
# **Current weather in Dehradun (as of Mar 19 2026, 5:27 pm IST)**  

# - **Condition:** Light rain, overcast  
# - **Temperature:** 78 °F (≈ 25.6 °C)  
# - **Feels‑like:** 79 °F (≈ 26.1 °C)  
# - **Wind:** Calm (no wind)  
# - **Humidity:** 47 %  
# - **Visibility:** 2 mi (≈ 3.2 km)  
# - **Pressure:** 29.79 inHg (≈ 1010 hPa)  

# **Short‑term outlook (next 48 h)**  
# - Expect passing showers and overcast skies, with temperatures ranging from 52 °F (≈ 10.6 °C) to 71 °F (≈ 21.7 °C).  
# - Rain probability peaks at 49 % around 7 pm, dropping to 24 % by 10 pm.  

# *Source: Time & Date weather page for Dehradun.*
    
    
#****************------------------------------******************

"""   -------------------TAVILY-------------------- 
🔍 What Tavily does
        Provides real-time web search results
        Returns concise, AI-ready summaries instead of cluttered pages
        Helps LLMs retrieve up-to-date information
        Reduces hallucinations by grounding answers in real data

🤖 Why it's useful
        When AI models need fresh or factual info (news, prices, trends), they can call Tavily’s API to:
        Search the web
        Extract key insights
        Use that data in responses

🧠 Simple example
        Instead of:
        “Search Google → parse pages → extract info”

        With Tavily:
        “Ask Tavily → get structured answer instantly”

"""

""" ------------ Agent-Stream --------------- 

    👉 AgentStream is used for streaming the agent's output step-by-step instead of waiting for the full response.

    Normal Behavior (without streaming)
        response = await agent.run("What is 2 + 2?")
        print(response) //Output:  4
        
        👉 You only get output after everything is done
        ⏳ User waits until full response is ready
        
    ⚡ With AgentStream
        👉 You get real-time partial output
        token by token
        step by step
        tool usage + reasoning
"""

""" 
***********---------AgentStream vs AgentOutput-----------************

🔹 AgentOutput
        👉 Final result of the agent
        Comes once
        Contains the final answer
        What you typically want in simple use cases

        Example:
        if isinstance(event, AgentOutput):
            print(event.response)

        ✅ Think: “Done. Here's your answer.”


🔹 AgentStream

        👉 Intermediate streaming events
        Comes multiple times
        Used during execution
        Includes:
            Partial LLM tokens
            Tool calls
            Reasoning steps

        Example:
        if isinstance(event, AgentStream):
            print(event.delta)   # partial tokens

        ✅ Think: “Typing… thinking… calling tool…”

        🔥🔥🔥🔥🔥🔥 Simple Analogy 🔥🔥🔥🔥🔥🔥🔥
        Concept	Real-world analogy
        AgentStream	Someone typing on WhatsApp 💬
        AgentOutput	Final sent message ✅

"""