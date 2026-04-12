import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest
from typing import cast, Annotated
from agent_framework import Message, WorkflowEvent
from agent_framework import tool

load_dotenv()

@tool
def process_refund(order_number: Annotated[str, "환불 처리할 주문 번호"]) -> str:
    """주어진 주문 번호에 대한 환불 처리를 시뮬레이션하는 함수입니다."""
    return f"주문 번호 {order_number}에 대한 환불이 성공적으로 처리되었습니다."

@tool
def check_order_status(order_number: Annotated[str, "상태를 확인할 주문 번호"]) -> str:
    """주어진 주문 번호의 상태를 확인하는 시뮬레이션 함수입니다."""
    return f"주문 번호 {order_number}는 현재 처리 중이며, 영업일 기준 2일 이내에 배송될 예정입니다."

@tool
def process_return(order_number: Annotated[str, "반품을 처리할 주문 번호"]) -> str:
    """주어진 주문 번호에 대한 반품 처리를 시뮬레이션하는 함수입니다."""
    return f"주문 번호 {order_number}에 대한 반품이 성공적으로 접수되었습니다. 반품 안내는 이메일로 발송됩니다."


# 1) OpenAIChatClient를 사용하여 4개의 도메인 에이전트를 생성합니다.
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )
  
    # 분류/조정 에이전트 생성
    triage_agent = client.as_agent( 
        instructions=( 
            "당신은 최전선 고객 지원 담당자입니다. 고객이 설명한 문제에 따라 적절한 전문 상담원에게 문제를 연결해 주세요." 
        ), 
        description="일반 문의를 처리하는 심사 에이전트입니다.", 
        name="triage_agent",
        )

    # 환불 전문가: 환불을 요청합니다.
    refund_agent = client.as_agent( 
        instructions="환불 요청을 처리하고 있습니다.", 
        description="환불 요청을 처리하는 에이전트입니다.", 
        name="refund_agent", 
        # 실제 에이전트에서는 다양한 도구를 사용할 수 있지만, 여기서는 간단하게 설명합니다. 
        tools=[process_refund],
    )

    # 주문/배송 전문가: 배송 관련 문제를 해결합니다.
    order_agent = client.as_agent( 
        instructions="주문 및 배송 문의를 처리합니다.", 
        description="주문 추적 및 배송 문제를 처리하는 에이전트입니다.", 
        name="order_agent", 
        # 실제 에이전트에서는 다양한 도구를 사용할 수 있지만, 여기서는 간단하게 설명합니다. 
        tools=[check_order_status],
    )

    # 반품 전문가: 반품 요청을 처리해 드립니다.
    return_agent = client.as_agent( 
        instructions="제품 반품 요청을 관리합니다.", 
        description="반품 처리를 담당하는 에이전트입니다.", 
        name="return_agent", 
        # 실제 에이전트에서는 다양한 도구를 사용할 수 있지만 여기서는 간단하게 설명합니다. 
        tools=[process_return],
    )   
    
    # 2) 세 개의 도메인 에이전트를 동시에 실행하는 병렬 워크플로 구축
    # 핸드오프 워크플로우를 구축하세요
    workflow = (
        HandoffBuilder(
            name="customer_support_handoff",
            participants=[triage_agent, refund_agent, order_agent, return_agent],
            termination_condition=lambda conversation: len(conversation) > 0 and "welcome" in conversation[-1].text.lower(),
        )
        .with_start_agent(triage_agent) # 분류 시스템은 초기 사용자 입력을 받습니다.
        # 분류 시스템은 환불 담당자에게 직접 연결할 수 없습니다.
        .add_handoff(triage_agent, [order_agent, return_agent])
        # 반품 담당자만이 환불 담당자에게 인계할 수 있습니다. (반품 후 환불을 원하는 사용자)
        .add_handoff(return_agent, [refund_agent])
        # 모든 전문의는 추가 라우팅를 위해 분류팀에 다시 핸드오프할 수 있습니다.
        .add_handoff(order_agent, [triage_agent])
        .add_handoff(return_agent, [triage_agent])
        .add_handoff(refund_agent, [triage_agent])
        .build()
    )
    
    # 초기 사용자 메시지로 워크플로 시작
    events = [event async for event in workflow.run("주문 관련해서 도움이 필요해요", stream=True)]

    # 이벤트를 처리하고, 보류 중인 입력 요청을 수집합니다.
    pending_requests = []
    for event in events:
        if event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
            pending_requests.append(event)
            request_data = event.data
            print(f"에이전트 {event.executor_id}가 입력을 기다리고 있습니다.")
            
            # 요청에는 입력을 요청하는 에이전트가 생성한 가장 최근 메시지가 포함되어 있습니다.
            for msg in request_data.agent_response.messages[-3:]:
                print(f"{msg.author_name}: {msg.text}")

    # 상호작용 루프: 요청에 응답
    while pending_requests:
        user_input = input("You: ")

        # 보류 중인 모든 요청에 ​​대한 답변을 보내세요
        responses = {req.request_id: HandoffAgentUserRequest.create_response(user_input) for req in pending_requests}
        # 워크플로를 조기에 종료하려면 `HandoffAgentUserRequest.terminate()`를 보낼 수도 있습니다.
        events = [event async for event in workflow.run(responses=responses, stream=True)]

        # 새로운 이벤트를 처리합니다
        pending_requests = []
        for event in events:
            # 새로운 입력 요청이 있는지 확인하세요
            if event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
                pending_requests.append(event)
                request_data = event.data
                print(f"에이전트 {event.executor_id}가 입력을 기다리고 있습니다.")
                # 요청에는 입력을 요청하는 에이전트가 생성한 가장 최근 메시지가 포함되어 있습니다.
                for msg in request_data.agent_response.messages[-3:]:
                    print(f"{msg.author_name}: {msg.text}")

asyncio.run(main())