import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework import AgentSession, BaseContextProvider, SessionContext
from typing import Any

load_dotenv()

class UserMemoryProvider(BaseContextProvider):
    """세션 상태에 사용자 정보를 기억하는 컨텍스트 제공자입니다."""

    DEFAULT_SOURCE_ID = "user_memory"

    def __init__(self):
        super().__init__(self.DEFAULT_SOURCE_ID)

    async def before_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        """저장된 사용자 정보를 기반으로 개인화 지침을 삽입합니다."""
        user_name = state.get("user_name")
        if user_name:
            context.extend_instructions(
                self.source_id,
                f"The user's name is {user_name}. Always address them by name.",
            )
        else:
            context.extend_instructions(
                self.source_id,
                "You don't know the user's name yet. Ask for it politely.",
            )

    async def after_run(
        self,
        *,
        agent: Any,
        session: AgentSession | None,
        context: SessionContext,
        state: dict[str, Any],
    ) -> None:
        """각 호출 후 사용자 정보를 추출하여 세션 상태에 저장합니다."""
        for msg in context.input_messages:
            text = msg.text if hasattr(msg, "text") else ""
            if isinstance(text, str) and "my name is" in text.lower():
                state["user_name"] = text.lower().split("my name is")[-1].strip().split()[0].capitalize()


async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="MemoryAgent",
        instructions="당신은 친절한 비서입니다.",
    )
    
    session = agent.create_session()

    # 서비스 제공업체는 아직 사용자를 알지 못하므로, 이름을 요청할 것입니다.
    result = await agent.run("Hello! What's the square root of 9?", session=session)
    print(f"Agent: {result}\n")

    # 이제 이름을 입력하세요. 제공업체는 해당 이름을 세션 상태에 저장합니다.
    result = await agent.run("My name is Alice", session=session)
    print(f"Agent: {result}\n")

    # 이후 호출은 개인 맞춤형으로 진행되며, 이름은 세션 상태를 통해 유지됩니다.
    result = await agent.run("What is 2 + 2?", session=session)
    print(f"Agent: {result}\n")

    # 세션 상태를 검사하여 공급자가 저장한 내용을 확인하세요.
    provider_state = session.state.get("user_memory", {})
    print(f"[Session State] Stored user name: {provider_state.get('user_name')}")


asyncio.run(main())