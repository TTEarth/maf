import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from pydantic import BaseModel

load_dotenv()

class PersonInfo(BaseModel):
    """Information about a person."""
    name: str | None = None
    age: int | None = None
    occupation: str | None = None

async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )

    agent = client.as_agent(
        name="HelpfulAgent",
        instructions="당신은 텍스트에서 인물 정보를 추출하는 유용한 도우미입니다.",
    )
    
    # person_info_schema = {
    #     "type": "object",
    #     "properties": {
    #         "name": {"type": "string"},
    #         "age": {"type": "integer"},
    #         "occupation": {"type": "string"},
    #     },
    #     "required": ["name", "age", "occupation"],
    # }
    
    response = await agent.run(
        "55세 소프트웨어 엔지니어인 이 재석 대한 정보를 제공해 주십시오.",
        options={"response_format": PersonInfo }
    )
    
    if response.value:
        person_info = response.value
        print(f"이름: {person_info.name}, 나이: {person_info.age}, 직업: {person_info.occupation}")
    else:
        print("응답에서 구조화된 데이터를 찾을 수 없습니다.")

asyncio.run(main())