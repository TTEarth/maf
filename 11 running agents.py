import asyncio
import os
# from agent_framework.openai import OpenAIChatClient
from agent_framework.openai import OpenAIChatClient, OpenAIChatOptions
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="HelloAgent",
        instructions="당신은 도움을 주는 친절한 비서입니다. 간결하게 답을 하세요.",
        default_options={
        "temperature": 0.7,
        "max_tokens": 500
    }
    )
    
    options: OpenAIChatOptions = {
    "temperature": 0.3,
    "max_tokens": 150,
    "model": "gpt-4o",
    "presence_penalty": 0.5,
    "frequency_penalty": 0.3
    }
    
    response = await agent.run("대한민국의 수도는?", options=options)
    print(response)
    print(len(response.messages))

    # Access individual messages
    for message in response.messages:
        print(f"Role: {message.role}, Text: {message.text}")

asyncio.run(main())