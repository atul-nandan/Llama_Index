import asyncio
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


def multiply(a: float, b: float) -> float:
    """Multiply two numbers and returns the product"""
    return a * b


def add(a: float, b: float) -> float:
    """Add two numbers and returns the sum"""
    return a + b

# Defining the model 
llm=Groq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
    )

# Defining the Agent 
agent = FunctionAgent(
    tools=[multiply,add],
    llm=llm,
    system_prompt="You are a helpful assistant that can multiply two numbers.",
)

async def main():
    response = await agent.run(user_msg="What is 20+(2*4)?")
    print("Output :",response)

   

if __name__ == "__main__":
    asyncio.run(main())
    
    