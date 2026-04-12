import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework.orchestrations import GroupChatBuilder, GroupChatState
from agent_framework import AgentResponseUpdate, Message

load_dotenv()

def round_robin_selector(state: GroupChatState) -> str:
    """현재 라운드 인덱스를 기준으로 다음 발표자를 선택하는 라운드 로빈 방식의 선택 기능입니다."""

    participant_names = list(state.participants.keys())
    return participant_names[state.current_round % len(participant_names)]

# 1) OpenAIChatClient를 사용하여 에이전트를 생성합니다.
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    researcher_agent = client.as_agent(
        name="조사자",
        description="관련 배경 정보를 수집합니다.",
        instructions="질문에 답하는데 도움이 되는 간결한 사실들을 수집하세요. 간결하고 사실에 입각해서 작성하세요.",
    )

    writer_agent = client.as_agent(
        name="작가",
        description="수집한 정보를 바탕으로 다듬어진 답변을 종합합니다.",
        instructions="제공된 메모를 활용하여 명확하고 체계적인 답변을 작성하십시오. 모든 내용을 빠짐없이 다루십시오.",
    )
    
    workflow = GroupChatBuilder(
        participants=[researcher_agent, writer_agent],
        termination_condition=lambda conversation: len(conversation) >= 4,
        selection_func=round_robin_selector,
    ).build()
    
    task = "파이썬에서 async/await를 사용할 때의 주요 이점은 무엇인가요?"

    print(f"작업: {task}\n")
    print("=" * 80)

    final_conversation: list[Message] = []
    last_author: str | None = None

    # 스트리밍을 활성화한 상태로, 워크플로우를 실행하세요.
    async for event in workflow.run(task, stream=True):
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            # 스트리밍 에이전트 업데이트 인쇄
            author = event.data.author_name
            if author != last_author:
                if last_author is not None:
                    print()
                print(f"[{author}]:", end=" ", flush=True)
                last_author = author
            print(event.data.text, end="", flush=True)
        elif event.type == "output" and isinstance(event.data, list):
            # 워크플로 완료 - 데이터는 메시지 목록입니다
            final_conversation = event.data

    if final_conversation:
        print("\n\n" + "=" * 80)
        print("마지막 대화:")
        for msg in final_conversation:
            print(f"\n[{msg.author_name}]\n{msg.text}")
            print("-" * 80)

    print("\n워크플로우 완료.")


asyncio.run(main())