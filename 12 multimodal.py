import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework import Message, Content

load_dotenv()

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="VisionAgent",
        instructions="당신은 이미지를 분석할 수 있는 유용한 에이전트입니다.",
    )
    
    message = Message(
        role="user",
        contents=[
            Content.from_text(text="이 이미지에서 무엇이 보이시나요?"),
            Content.from_uri(
                uri="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/%EA%B2%BD%EB%B3%B5%EA%B6%81_%EA%B4%91%ED%99%94%EB%AC%B8_%28cropped%29.jpg/1280px-%EA%B2%BD%EB%B3%B5%EA%B6%81_%EA%B4%91%ED%99%94%EB%AC%B8_%28cropped%29.jpg",
                media_type="image/jpeg"
            )
        ]
    )
    
    result = await agent.run(message)
    print(result.text)

asyncio.run(main())