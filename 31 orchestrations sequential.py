import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework.orchestrations import SequentialBuilder
from typing import Any, cast
from agent_framework import Message, WorkflowEvent

load_dotenv()

# 1) OpenAIChatClient를 사용하여 에이전트를 생성합니다.
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    writer_agent = client.as_agent(
        name="작가",
        instructions="당신은 간결한 카피라이터입니다. 주어진 주제에 맞춰 임팩트 있는 마케팅 문장 하나를 작성해 주세요.",
    )

    reviewer_agent = client.as_agent(
        name="검토자",
        instructions="당신은 사려 깊은 검토자입니다. 이전 어시스턴트 메시지에 대한 간략한 피드백을 남겨주세요.",
    )   
    
    
    # 2) 작성자 -> 검토자 순차적 워크플로 구축
    workflow = SequentialBuilder(participants=[writer_agent, reviewer_agent]).build()
    
    
    # 3) 최종 대화를 실행하고 출력합니다.
    outputs: list[list[Message]] = []
    async for event in workflow.run("저렴한 가격의 전기 자전거를 위한 슬로건을 작성하세요.", stream=True):
        if event.type == "output":
            outputs.append(cast(list[Message], event.data))

    if outputs:
        print("===== 마지막 대화 =====")
        messages: list[Message] = outputs[-1]
        for i, msg in enumerate(messages, start=1):
            name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
            print(f"{'-' * 60}\n{i:02d} [{name}]\n{msg.text}")

asyncio.run(main())