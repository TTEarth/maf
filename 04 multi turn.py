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
        name="ConversationAgent",
        instructions="당신은 친절한 비서입니다.",
    )
    
    # 대화 기록을 유지하기 위한 세션을 생성합니다.
    session = agent.create_session()

    # 첫 번째 질문과 답변
    result = await agent.run("내 이름은 재석이고, 나는 탁구를 좋아해", session=session)
    print(f"Agent: {result}\n")
    
    # 두 번째 질문에서는 세션을 통해 이전 대화 내용을 기억합니다. 사용자의 이름과 취미를 기억해야 합니다.
    result = await agent.run("나에 대해서 무엇을 기억하니?", session=session)
    print(f"Agent: {result}")

asyncio.run(main())