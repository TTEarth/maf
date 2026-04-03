import asyncio

from agent_framework import (
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
)
from typing_extensions import Never

"""
첫 번째 워크플로 - 엣지를 사용하여 실행기 연결하기

이 예제는 다음 두 단계로 구성된 최소한의 워크플로를 구축합니다.
1. 텍스트를 대문자로 변환(클래스 기반 실행기)
2. 텍스트를 반전(함수 기반 실행기)

외부 서비스는 필요하지 않습니다.
"""


# <create_workflow>
# 1단계: 텍스트를 대문자로 변환하는 클래스 기반 실행기
class UpperCase(Executor):
    def __init__(self, id: str):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Convert input to uppercase and forward to the next node."""
        await ctx.send_message(text.upper())


# 2단계: 문자열을 뒤집고 출력을 생성하는 함수 기반 실행기
@executor(id="reverse_text")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Reverse the string and yield the final workflow output."""
    await ctx.yield_output(text[::-1])


def create_workflow():
    """Build the workflow: UpperCase → reverse_text."""
    upper = UpperCase(id="upper_case")
    return WorkflowBuilder(start_executor=upper).add_edge(upper, reverse_text).build()
# </create_workflow>


async def main() -> None:
    # <run_workflow>
    workflow = create_workflow()

    events = await workflow.run("hello world")
    print(f"Output: {events.get_outputs()}")
    print(f"Final state: {events.get_final_state()}")
    # </run_workflow>

    """
    Expected output:
      Output: ['DLROW OLLEH']
      Final state: WorkflowRunState.IDLE
    """


if __name__ == "__main__":
    asyncio.run(main())