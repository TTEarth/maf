import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework import tool

load_dotenv()

@tool
def get_weather(location: str) -> str:
    """특정 위치의 날씨 정보를 가져옵니다."""
    return f"{location}의 날씨는 맑고, 기온은 25°C입니다."

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="WeatherAgent",
        instructions="당신은 날씨를 알려주는 비서입니다.",
        tools=[get_weather]
    )
    result = await agent.run("서울의 날씨를 알려줘")
    print(result)

asyncio.run(main())