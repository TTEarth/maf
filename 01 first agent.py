import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

load_dotenv()

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="HelloAgent",
        instructions="당신은 도움을 주는 친절한 비서입니다. 간결하게 답을 하세요.",
    )
    result = await agent.run("대한민국의 수도는?")
    print(result)

asyncio.run(main())