import asyncio
import os
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="HelloAgent",
        instructions="당신은 친절한 비서입니다.",
    )
    # result = await agent.run("What is the capital of korea?")
    # print(result)
    
    # 스트리밍: 토큰이 생성되는 즉시 수신합니다.
    print("Agent (streaming): ", end="", flush=True)
    async for chunk in agent.run("경북소프트웨어고등학교에 산다는 AI 악동들에 대한 이야기를 들려줘", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()
    

asyncio.run(main())