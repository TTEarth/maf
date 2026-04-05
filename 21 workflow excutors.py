import asyncio
# import os
# from dotenv import load_dotenv
# from agent_framework.openai import OpenAIChatClient
from agent_framework import (
    Executor,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
)

# load_dotenv()

class UpperCase(Executor):
    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """입력값을 대문자로 변환하여 다음 노드로 전달합니다."""
        result = text.upper()
        await ctx.send_message(result)
        
@executor(id="reverse_text_executor")
async def reverse_text(text: str, ctx: WorkflowContext[str]) -> None:
    """입력 문자열을 역순으로 만들고 워크플로 출력을 생성합니다."""
    result = text[::-1]
    await ctx.yield_output(result)
    
class ExclamationAdder(Executor):
    @handler(input=str, output=str)
    async def add_exclamation(self, message, ctx) -> None:  # type: ignore
        """입력값에 느낌표를 추가하세요."""
        result = f"{message}!!!"
        await ctx.send_message(result)  # type: ignore

def create_workflow() -> Workflow:
    """격리된 상태를 가진 새로운 워크플로우를 생성합니다."""
    upper_case = UpperCase(id="upper_case_executor")
    
    builder = WorkflowBuilder(start_executor=upper_case)
    builder.add_edge(upper_case, reverse_text)
    workflow = builder.build()

    return workflow


async def main():
    # client = OpenAIChatClient(
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     model=os.getenv("OPENAI_MODEL")
    # )
    
    workflow1 = create_workflow()
    
    print("Workflow 1 (introspection-based types):")
    events1 = await workflow1.run("hello world")
    print(events1.get_outputs())
    print("Final state:", events1.get_final_state())
    
    upper_case = UpperCase(id="upper_case_executor")
    exclamation_adder = ExclamationAdder(id="exclamation_adder")
    
    workflow2 = (
        WorkflowBuilder(start_executor=upper_case)
        .add_edge(upper_case, exclamation_adder)
        .add_edge(exclamation_adder, reverse_text)
        .build()
    )
    
    print("\nWorkflow 2 (explicit @handler types):")
    events2 = await workflow2.run("hello world")
    print(events2.get_outputs())
    print("Final state:", events2.get_final_state())

asyncio.run(main())