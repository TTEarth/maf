import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from pathlib import Path
from agent_framework import SkillsProvider

load_dotenv()

# '기술' 디렉토리에서 필요한 기술을 찾아보세요.
skills_provider = SkillsProvider(
    skill_paths=Path(__file__).parent / "skills"
)

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="SkillsAgent",
        instructions="당신은 도움을 주는 친절한 비서입니다. 사용자의 질문에 답하기 위해 필요한 기술을 로드할 수 있습니다.",
        context_providers=[skills_provider],
    )
    
    # 에이전트는 경비 보고서 스킬을 로드하고 FAQ 자료를 읽습니다.
    result = await agent.run("팁은 환불받을 수 있나요? 택시비의 25%를 팁으로 줬어요.")
    print(result)

asyncio.run(main())