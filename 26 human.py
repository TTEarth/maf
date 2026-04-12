import asyncio
# import os
# from dotenv import load_dotenv
# from agent_framework.openai import OpenAIChatClient

from dataclasses import dataclass

from agent_framework import (
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)

# .env 파일에서 환경 변수를 불러오기
# load_dotenv()

@dataclass
class NumberSignal:
    hint: str  # "init", "above", or "below"


class JudgeExecutor(Executor):
    def __init__(self, target_number: int):
        super().__init__(id="judge")
        self._target_number = target_number
        self._tries = 0

    @handler
    async def handle_guess(self, guess: int, ctx: WorkflowContext[int, str]) -> None:
        self._tries += 1
        if guess == self._target_number:
            await ctx.yield_output(f"{self._target_number}를 {self._tries}번 시도 끝에 찾았습니다!")
        elif guess < self._target_number:
            await ctx.request_info(request_data=NumberSignal(hint="below"), response_type=int)
        else:
            await ctx.request_info(request_data=NumberSignal(hint="above"), response_type=int)

    @response_handler
    async def on_human_response(
        self,
        original_request: NumberSignal,
        response: int,
        ctx: WorkflowContext[int, str],
    ) -> None:
        await self.handle_guess(response, ctx)


judge = JudgeExecutor(target_number=42)
workflow = WorkflowBuilder(start_executor=judge).build()


from collections.abc import AsyncIterable

from agent_framework import WorkflowEvent

async def process_event_stream(stream: AsyncIterable[WorkflowEvent]) -> dict[str, int] | None:
    """Process events from the workflow stream to capture requests."""
    requests: list[tuple[str, NumberSignal]] = []
    async for event in stream:
        if event.type == "request_info":
            requests.append((event.request_id, event.data))

    # 보류 중인 사용자 피드백 요청을 처리합니다.
    if requests:
        responses: dict[str, int] = {}
        for request_id, request in requests:
            while True:
                raw = input(f"힌트({request.hint})를 받았습니다. 다음 추측 숫자를 입력하세요: ").strip()
                try:
                    guess = int(raw)
                    break
                except ValueError:
                    print("정수를 입력해 주세요.")
            responses[request_id] = guess
        return responses

    return None

async def main():
    # 초기 추측값을 사용하여 워크플로의 첫 번째 실행을 시작합니다.
    # 실행은 격리되지 않으며, 여러 번 실행을 호출하는 동안 상태가 유지됩니다.  
    stream = workflow.run(25, stream=True)

    pending_responses = await process_event_stream(stream)
    while pending_responses is not None:
        # 더 이상 제공할 사람이 피드백을 주지 않을 때까지 워크플로를 실행합니다.
        # 그러면 이 워크플로가 완료됩니다.
        stream = workflow.run(stream=True, responses=pending_responses)
        pending_responses = await process_event_stream(stream)

if __name__ == "__main__":
    asyncio.run(main())