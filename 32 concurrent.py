import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework.orchestrations import ConcurrentBuilder
from typing import cast
from agent_framework import Message, WorkflowEvent

load_dotenv()

# 1) OpenAIChatClient를 사용하여 세 개의 도메인 에이전트를 생성합니다.
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    researcher_agent = client.as_agent(
        name="조사자",
        instructions="당신은 시장 및 제품 조사 전문가입니다. 주어진 주제에 대해 간결하고 사실에 입각한 통찰력, 기회 및 위험 요소를 제시하십시오.",
    )

    marketer_agent = client.as_agent(
        name="마케터",
        instructions="당신은 창의적인 마케팅 전략가입니다. 주어진 과제에 맞춰 매력적인 가치 제안과 타겟 메시지를 만들어 보세요.",
    )   

    legal_agent = client.as_agent(
        name="법률 전문가",
        instructions="당신은 신중한 법률/규정 준수 검토자입니다. 제시된 내용을 바탕으로 제약 조건, 면책 조항 및 정책 관련 우려 사항을 강조하십시오.",
    )   
    
    # 2) 세 개의 도메인 에이전트를 동시에 실행하는 병렬 워크플로 구축
    # 참가자는 에이전트(SupportsAgentRun 유형) 또는 실행자입니다.
    workflow = ConcurrentBuilder(participants=[researcher_agent, marketer_agent, legal_agent]).build()
    
    
    # 3) 단일 프롬프트로 실행하고, 진행 상황을 스트리밍하며, 최종적으로 결합된 메시지를 보기 좋게 출력합니다.
    output_data: list[Message] | None = None
    async for event in workflow.run("저희는 도심 통근자를 위한 저렴한 가격의 새로운 전기 자전거를 출시합니다.", stream=True):
        if event.type == "output":
            output_data = event.data

    if output_data:
        print("===== 최종 집계된 대화(메시지) =====")
        messages: list[Message] = cast(list[Message], output_data)
        for i, msg in enumerate(messages, start=1):
            name = msg.author_name if msg.author_name else "user"
            print(f"{'-' * 60}\n\n{i:02d} [{name}]:\n{msg.text}")

asyncio.run(main())