import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework import Agent

load_dotenv()

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="o3"
    )
      
    agent = client.as_agent(
        name="researchAgent",
        instructions="당신은 도움을 주는 리서치 비서입니다.",
    )
    
    session = agent.create_session()
    
    # 백그라운드 실행을 시작하면 즉시 결과가 반환됩니다.
    response = await agent.run(
        messages="상대성 이론을 두 문장으로 간략하게 설명하세요.",
        session=session,
        options={"background": True},
    )

    # 작업이 완료될 때까지 폴링하세요
    while response.continuation_token is not None:
        await asyncio.sleep(2)
        response = await agent.run(
            session=session,
            options={"continuation_token": response.continuation_token},
        )

    # 완료 — response.text에 최종 결과가 포함되어 있습니다.
    print(response.text)
    
asyncio.run(main())