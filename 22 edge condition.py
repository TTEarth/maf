# 1단계: 필요한 종속성 가져오기
import asyncio
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from typing import Any
from typing_extensions import Never
from pydantic import BaseModel

from agent_framework import (
    Agent,  # AI 에이전트의 기본 클래스
    AgentExecutor,
    AgentExecutorRequest,  # Input message bundle for an AgentExecutor
    AgentExecutorResponse,
    Message,
    WorkflowBuilder,  # Fluent builder for wiring executors and edges
    WorkflowContext,  # Per-run context and event bus
    executor,  # Decorator to declare a Python function as a workflow executor
)

load_dotenv()

# 2단계 : 데이터 모델 정의
class DetectionResult(BaseModel):
    """스팸 탐지 결과를 나타냅니다."""
    #is_spam은 엣지 조건에 따라 라우팅 결정을 내리는데 영향을 미칩니다.
    is_spam: bool = None
    # 탐지기에서 얻은 사람이 읽을 수 있는 설명
    reason: str = None
    # 에이전트는 하위 에이전트가 콘텐츠를 다시 로드하지 않고 작동할 수 있도록 원본 이메일을 포함해야 합니다.
    email_content: str = None


class EmailResponse(BaseModel):
    """이메일 어시스턴트의 응답을 나타냅니다."""
    # 사용자가 복사하거나 보낼 수 있는 답장 초안
    response: str = None

# 3단계: 조건 함수 만들기   
def get_condition(expected_result: bool):
    """DetectionResult.is_spam을 기반으로 라우팅하는 조건 호출 가능 객체를 생성합니다."""

    # 반환된 함수는 엣지 술어로 사용됩니다.
    # 상위 실행기가 생성한 값을 그대로 받습니다.
    def condition(message: Any) -> bool:
        # 방어적 가드. AgentExecutor 응답이 아닌 응답이 나타나면 막다른 길을 피하기 위해 엣지를 통과시킵니다.
        if not isinstance(message, AgentExecutorResponse):
            return True

        try:
            # 에이전트 JSON 텍스트에서 구조화된 DetectionResult를 파싱하는 것을 권장합니다.
            # model_validate_json을 사용하면 타입 안전성이 보장되고 형식이 잘못된 경우 예외가 발생합니다.
            detection = DetectionResult.model_validate_json(message.agent_run_response.text)
            # 스팸 플래그가 예상 경로와 일치하는 경우에만 라우팅합니다.
            return detection.is_spam == expected_result
        except Exception:
            # 구문 분석 오류 발생시 종료되도록 하여, 잘못된 경로로 연결되는 것을 방지합니다.
            # False를 반환하면 이 엣지가 활성화되지 않습니다.
            return False

    return condition

# 4단계: 핸들러 실행기 생성하기
@executor(id="send_email")
async def handle_email_response(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """정상적인 이메일에는 전문적인 답변을 작성하여 대응하세요."""
    # 이메일 어시스턴트의 하위 단계입니다. 유효성이 검증된 EmailResponse를 파싱하고 워크플로 출력을 생성합니다.
    email_response = EmailResponse.model_validate_json(response.agent_run_response.text)
    await ctx.yield_output(f"Email sent:\n{email_response.response}")


@executor(id="handle_spam")
async def handle_spam_classifier_response(response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
    """스팸 메일은 적절하게 표시하여 처리하세요."""
    # 스팸 경로. DetectionResult를 확인하고 워크플로 출력을 생성합니다. 스팸이 아닌 입력이 실수로 들어가는 것을 방지합니다.
    detection = DetectionResult.model_validate_json(response.agent_run_response.text)
    if detection.is_spam:
        await ctx.yield_output(f"Email marked as spam: {detection.reason}")
    else:
        # 이는 라우팅 조건자와 실행기 계약이 동기화되지 않았음을 나타냅니다.
        raise RuntimeError("이 실행기는 스팸 메시지만 처리해야 합니다.")


@executor(id="to_email_assistant_request")
async def to_email_assistant_request(
    response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]
) -> None:
    """스팸 탐지 응답을 이메일 어시스턴트 요청으로 변환합니다."""
    # 탐지 결과를 분석하고 어시스턴트를 위해 이메일 내용을 추출합니다.
    detection = DetectionResult.model_validate_json(response.agent_run_response.text)

    # 원래 이메일 내용을 사용하여, 이메일 도우미에 대한 새 요청을 생성하세요.
    request = AgentExecutorRequest(
        messages=[Message(role="user", contents=[detection.email_content])],
        should_respond=True
    )
    await ctx.send_message(request)
  
# 5단계: AI 에이전트 만들기
async def main():
    client = OpenAIChatClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL")
    )
    
    # 에이전트 1. 스팸을 분류하고 DetectionResult 객체를 반환합니다.
    # response_format은 LLM이 Pydantic 모델에서 파싱 가능한 JSON을 반환하도록 합니다.
    spam_detection_agent = AgentExecutor(
        client.as_agent(
            instructions=(
                "스팸 메일을 식별하는 스팸 감지 도우미입니다. "
                "항상 is_spam(bool), reason(string), email_content(string) 필드를 포함하는 JSON을 반환해야 합니다. "
                "email_content 필드에는 원본 이메일 내용을 포함해야 합니다."
            ),
            default_options={"response_format": DetectionResult},
        ),  
        id="spam_detection_agent",
    )
    
    # 에이전트 2. 전문적인 답변을 작성합니다. 또한 신뢰성을 위해 구조화된 JSON 형식으로 출력합니다.
    email_assistant_agent = AgentExecutor(
        client.as_agent(
            instructions=(
                "이메일 어시스턴트로서 사용자가 이메일에 전문적인 답변을 작성하도록 돕습니다. "
                "입력은 'email_content'를 포함하는 JSON 객체일 수 있으며, 해당 내용을 기반으로 답변을 작성하세요. "
                "작성된 답변은 'response'라는 단일 필드를 포함하는 JSON 형식으로 반환해야 합니다."
            ),
            default_options={"response_format": EmailResponse},
        ),
        id="email_assistant_agent",
    )
    
     
    #6단계: 조건부 워크플로 빌드
    # 워크플로 그래프를 구축합니다.
    # 스팸 감지기에서 시작합니다.
    # 스팸이 아니면, 새로운 AgentExecutorRequest를 생성하는 트랜스포머로 이동한 후, 이메일 어시스턴트를 호출하고 최종 처리합니다.
    # 스팸이면, 스팸 처리기로 바로 이동하여 최종 처리합니다.
    workflow = (
        WorkflowBuilder(start_executor=spam_detection_agent)
        # 스팸 방지 경로: 응답 변환 -> 지원 요청 -> 지원 담당자 -> 이메일 전송
        .add_edge(spam_detection_agent, to_email_assistant_request, condition=get_condition(False))
        .add_edge(to_email_assistant_request, email_assistant_agent)
        .add_edge(email_assistant_agent, handle_email_response)
        # 스팸 경로: 스팸 처리기로 전송
        .add_edge(spam_detection_agent, handle_spam_classifier_response, condition=get_condition(True))
        .build()
    )
    
    # 7단계: 워크플로 실행
    # 샘플 리소스 파일에서 이메일 내용을 읽습니다.
    # 이렇게 하면 모델이 실행될 때마다, 동일한 이메일을 보게 되므로, 샘플이 결정론적으로 유지됩니다.
    email = """
        제목: 팀 회의 후속 조치 사항

        안녕하세요, 사라님.

        오늘 아침 팀 회의 후속 조치 사항으로 다음 내용을 공유하고자 합니다.
        

        1. 금요일까지 프로젝트 일정 업데이트
        2. 다음 주 고객 프레젠테이션 일정 확정
        3. 4분기 예산 배정 검토

        궁금한 점이 있거나 회의에서 빠진 내용이 있으면 알려주세요.

        감사합니다.

        알렉스 존슨
        프로젝트 매니저
        테크 솔루션즈

        alex.johnson@techsolutions.com

        (555) 123-4567    
        """
    
    # email = """
    #     제목: 무료 돈을 받으세요!
        
    #     안녕하세요, 
    #     당신은 행운의 당첨자입니다! 지금 바로 이 이메일에 회신하여 무료 돈을 받으세요.
    #     이 기회를 놓치지 마세요!
    #     감사합니다.
    #     사기꾼 드림 
    #     """

    # 워크플로를 실행합니다. 시작 객체가 AgentExecutor이므로 AgentExecutorRequest를 전달합니다.
    # 워크플로는 유휴 상태(더 이상 수행할 작업이 없는 상태)가 되면 완료됩니다.
    request = AgentExecutorRequest(messages=[Message(role="user", contents=[email])], should_respond=True)
    events = await workflow.run(request)
    outputs = events.get_outputs()
    if outputs:
        print(f"Workflow output: {outputs[0]}") 

asyncio.run(main())