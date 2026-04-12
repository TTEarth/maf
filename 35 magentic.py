import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework.orchestrations import MagenticBuilder, MagenticProgressLedger
import json
from typing import cast
from agent_framework import (
    AgentResponseUpdate,
    Message,
    WorkflowEvent,
)

load_dotenv()


# 1) OpenAIChatClient를 사용하여 에이전트를 생성합니다.
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    researcher_agent = client.as_agent(
        name="조사자",
        description="연구 및 정보 수집 전문가입니다.",
        instructions="당신은 조사자입니다. 추가적인 계산이나 정량적 분석 없이 정보를 찾아냅니다.",
    )

    coder_agent = client.as_agent(
        name="코더",
        description="데이터를 처리하고 분석하기 위해 코드를 작성하고 실행하는 유용한 도우미입니다.",
        instructions="코드를 사용하여 문제를 해결하십시오. 자세한 분석 및 계산 과정을 제시해 주십시오.",
        tools=client.get_code_interpreter_tool(),
    )
    
    # 오케스트레이션을 위한 관리자 에이전트를 생성합니다.
    manager_agent = client.as_agent(
        name="마젠틱매니저",
        description="조사 및 코딩 워크플로를 조정하는 오케스트레이터입니다.",
        instructions="팀을 조정하여 복잡한 작업을 효율적으로 완료하십시오.",
    )
    
    # 2) 작성자 -> 검토자 순차적 워크플로 구축
    workflow = MagenticBuilder(
        participants=[researcher_agent, coder_agent],
        intermediate_outputs=True,
        manager_agent=manager_agent,
        max_round_count=10,
        max_stall_count=3,
        max_reset_count=2,
    ).build()
    
    task = (
        "다양한 머신러닝 모델 아키텍처의 에너지 효율성에 대한 보고서를 작성 중입니다."
        "ResNet-50, BERT-base, GPT-2의 표준 데이터셋(예: ResNet의 경우 ImageNet,"
        "BERT의 경우 GLUE, GPT-2의 경우 WebText)에서의 학습 및 추론 에너지 소비량을 비교하십시오."
        "그런 다음, Azure Standard_NC6s_v3VM에서 24시간 동안 학습한다고 가정했을 때"
        "각 모델과 관련된 CO2 배출량을 추정하십시오."
        "명확성을 위해 표를 제공하고, 작업 유형(이미지 분류, 텍스트 분류, 텍스트 생성)별로 가장 에너지 효율적인 모델을 추천하십시오."
    )

    # 스트리밍 모드에서 출력을 보기 좋게 표시하려면 마지막 실행기를 추적하세요.
    last_message_id: str | None = None
    output_event: WorkflowEvent | None = None
    async for event in workflow.run(task, stream=True):
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            message_id = event.data.message_id
            if message_id != last_message_id:
                if last_message_id is not None:
                    print("\n")
                print(f"- {event.executor_id}:", end=" ", flush=True)
                last_message_id = message_id
            print(event.data, end="", flush=True)

        elif event.type == "magentic_orchestrator":
            print(f"\n[마젠틱 오케스트레이션 이벤트] 유형: {event.data.event_type.name}")
            if isinstance(event.data.content, Message):
                print(f"계획을 검토하십시오:\n{event.data.content.text}")
            elif isinstance(event.data.content, MagenticProgressLedger):
                print(f"진행 상황 원장을 검토하십시오:\n{json.dumps(event.data.content.to_dict(), indent=2)}")
            else:
                print(f"마젠틱 오케스트레이션에서 알 수 없는 데이터 유형입니다: {type(event.data.content)}")
            
            # 사용자가 계속 진행하기 전에 계획/진행 상황을 확인할 수 있도록 하는 블록입니다.
            # 참고: 이는 데모용이며, 사용자 상호 작용을 처리하는 권장 방식이 아닙니다.
            # 계획 단계에서 적절한 사용자 상호 작용을 위해서는 `with_plan_review`를 참조하십시오.
            await asyncio.get_event_loop().run_in_executor(None, input, "계속하려면 Enter 키를 누르십시오...")

        elif event.type == "output":
            output_event = event

    # Magnetic 워크플로의 출력은 채팅 메시지 목록이며, 오케스트레이터에서 생성된 최종 메시지는 단 하나뿐입니다.
    output_messages = cast(list[Message], output_event.data)
    output = output_messages[-1].text
    print(output)


asyncio.run(main())