from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', api_key=os.getenv('GEMINI_API_KEY'))

async def main():
    # Create agent with the model
    agent = Agent(
        task="""
        First, search for the cheapest and best ski resort in Colorado.
        Could you make a reservation at this resort for a cabin on 12/13/25.
        """,
        llm=llm
    )
    result = await agent.run()
    
    print(result)

# Run the async function
asyncio.run(main())