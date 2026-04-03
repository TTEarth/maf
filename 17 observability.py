import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework.observability import configure_otel_providers
from agent_framework.observability import get_tracer, get_meter
from random import randint
from typing import Annotated
from agent_framework import Agent, tool
from opentelemetry.trace import SpanKind
from opentelemetry.trace.span import format_trace_id
from pydantic import Field
from agent_framework.observability import create_resource, enable_instrumentation

load_dotenv()

@tool(approval_mode="never_require")
async def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    await asyncio.sleep(randint(0, 10) / 10.0)  # Simulate a network call
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def main():
    # OTEL_EXPORTER_OTLP_* 환경 변수를 자동으로 읽습니다.
    configure_otel_providers(enable_console_exporters=True)

    questions = ["What's the weather in Amsterdam?", "and in Paris, and which is better?", "Why is the sky blue?"]

    with get_tracer().start_as_current_span("Scenario: Agent Chat", kind=SpanKind.CLIENT) as current_span:
        print(f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")

        agent = Agent(
            client=OpenAIChatClient(api_key=os.getenv("OPENAI_API_KEY"),model=os.getenv("OPENAI_MODEL")),
            tools=get_weather,
            name="WeatherAgent",
            instructions="You are a weather assistant.",
            id="weather-agent",
        )
        thread = agent.create_session()
        for question in questions:
            print(f"\nUser: {question}")
            print(f"{agent.name}: ", end="")
            async for update in agent.run(
                question,
                session=thread,
                stream=True,
            ):
                if update.text:
                    print(update.text, end="")

asyncio.run(main())