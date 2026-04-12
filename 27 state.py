import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework import Agent, WorkflowBuilder, Workflow

load_dotenv()


def create_workflow() -> Workflow:
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    # 콘텐츠를 생성하는 작가 에이전트를 만드세요
    writer_agent = Agent(
        client=client,
        name="작가",
        instructions=(
            "당신은 뛰어난 콘텐츠 작가입니다. 새로운 콘텐츠를 제작하고 피드백을 바탕으로 기존 콘텐츠를 수정합니다."
        ),
    )

    # 피드백을 제공하는 검토자 에이전트를 생성하세요.
    reviewer_agent = client.as_agent(
        name="검토자",
        instructions=(
            "당신은 뛰어난 콘텐츠 검토자입니다. "
            "제공된 콘텐츠에 대해 작가에게 실행 가능한 피드백을 제공합니다. "
            "피드백은 가능한 한 간결하게 제공하세요."
        ),
    )

    # 에이전트를 실행자로 활용하여 워크플로우를 구축하세요.
    return WorkflowBuilder(start_executor=writer_agent).add_edge(writer_agent, reviewer_agent).build()


async def main():
    # 각 워크플로우에는 자체 에이전트 인스턴스와 스레드가 있습니다.
    workflow_a = create_workflow()
    workflow_b = create_workflow()
    
    # 워크플로우 실행
    print("워크플로우 A 시작...")
    result_a = await workflow_a.run("새로운 전기 SUV의 슬로건을 만들어 보세요.")
    print("워크플로우 A 결과:", result_a)
    
    print("\n워크플로우 B 시작...")
    result_b = await workflow_b.run("합리적인 가격에 운전의 재미까지 더한 새로운 전기 SUV의 슬로건을 만들어 보세요.")
    print("워크플로우 B 결과:", result_b)

if __name__ == "__main__":
    asyncio.run(main())
