import asyncio
from llama_index.core.agent.workflow import FunctionAgent, ReActAgent
from llama_index.llms.groq import Groq
from llama_index.core.workflow import Context
from llama_index.core.workflow import JsonSerializer
from dotenv import load_dotenv
import os

load_dotenv()


# Defining the model 
llm=Groq(
        # model="llama-3.1-8b-instant",
         model="llama-3.3-70b-versatile",  # Much more reliable
        api_key=os.getenv("GROQ_API_KEY")
    )

# Dummy tool for FunctionAgent
# def dummy_tool(input: str) -> str:
#     """A placeholder tool."""
#     return input

# Defining the Agent 

# FunctionAgent -> it should be used only when we are using/passing a "tool" , otherwise use a "dummy tool"
# agent = FunctionAgent(
#     tools=[FunctionTool.from_defaults(fn=dummy_tool)],
#     llm=llm,
#     system_prompt="You are a helpful assistant ",
# )

# ReActAgent => It should be used for tool-less or simple agents and avoids the tool_choice issue entirely
agent = ReActAgent(
    llm=llm,
    system_prompt="You are a helpful assistant",
)


async def main():

    ctx = Context(agent)

    await agent.run("My name is Logan", ctx=ctx)
    response = await agent.run("What is my name?", ctx=ctx)

    print("Memory:", response)
     # convert our Context to a dictionary object 
    ctx_dict = ctx.to_dict(serializer=JsonSerializer())
    print("Printing serialized data of jsonserializer()")
    # print(ctx_dict)

    # create a new Context from the dictionary
    restored_ctx = Context.from_dict(
        agent, ctx_dict, serializer=JsonSerializer()
    )

    response3 = await agent.run(user_msg="What's my name?",ctx=restored_ctx)
    print(response3)

if __name__ == "__main__":
    asyncio.run(main())
    
    
#****************------------------------------******************
""" ------------ Maintaining state for a long period of time ---------------


1.  The Context is serializable, so it can be saved to a database, file, etc. and loaded back in later.
    👉 It does NOT automatically save over longer periods
    It only becomes “long-term” if you explicitly store it somewhere.
        You serialize it (to_dict)
        You store it (file/DB)
        You reload it later (from_dict)
    
    till now : 
    ctx = Context(agent)
        👉 Memory lives in RAM only
        Program running → memory exists ✅  
        Program stops → memory gone ❌
        So, Right now You are NOT maintaining state over long periods

    
2.  what does “maintaining state over longer periods” mean?

    It means: Time gap exists ⏳  -> Program restarted 🔁  -> Memory still works 🧠

        👉 You take this:
        ctx_dict = ctx.to_dict(...)

        👉 And store it somewhere persistent like: File (JSON) 📁, Database 🗄️, Cloud storage ☁️
        Then use the stored data to load in Context data
        
        ⚠️ Important Clarification
            👉 LlamaIndex is only giving you the tools
            It does NOT: auto-save ❌, auto-load ❌
            
            👉 YOU must do it manually in your memory/storage area using :
                save (json.dump)
                load (json.load) 
                
3.  Understanding Real Long-Term Flow

        🟢 Session 1 (today)
        
        ctx = Context(agent)
        await agent.run("My name is Logan", ctx=ctx)
        ctx_dict = ctx.to_dict(serializer=JsonSerializer())

        # SAVE
        with open("memory.json", "w") as f:
            json.dump(ctx_dict, f)
            
            
        🔵 Session 2 (tomorrow / after restart)
        
        # LOAD
        with open("memory.json", "r") as f:
            ctx_dict = json.load(f)

        # RESTORE
        ctx = Context.from_dict(agent, ctx_dict, serializer=JsonSerializer())
        response = await agent.run("What is my name?", ctx=ctx)

        👉 Output: Logan




"""

