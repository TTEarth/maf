import asyncio
from pathlib import Path

from agent_framework.declarative import WorkflowFactory


async def main():
    """Run the greeting workflow."""
    # 워크플로우 팩토리를 생성하세요
    factory = WorkflowFactory()

    # YAML 파일에서 워크플로를 불러오기
    workflow_path = Path(__file__).parent / "16-workflow.yaml"
    print(f"Loading workflow from: {workflow_path}")
    workflow = factory.create_workflow_from_yaml_path(workflow_path)

    print(f"Loaded workflow: {workflow.name}")
    print("-" * 40)

    # 이름을 입력하여 실행하세요
    result = await workflow.run({"name": "Alice"})
    for output in result.get_outputs():
        print(f"Output: {output}")


if __name__ == "__main__":
    asyncio.run(main())