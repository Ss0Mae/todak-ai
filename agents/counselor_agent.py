from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from agents.subllm_agent import SubLLMAgent
from prompts.prompt_builder import build_prompt_with_strategies
from agents.reply_extractor import ReplyExtractor
import os
import re
class CounselorAgent:
    def __init__(self, client_info, persona, model_name="gpt-4o-mini", temperature=0.7):
        self.client_info = client_info
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.subllm = SubLLMAgent()
        # Load persona prompt based on persona_type
        persona_path = f"prompts/{persona}.txt"
        with open(persona_path, "r", encoding="utf-8") as f:
            self.persona_prompt = f.read()

        self.prompt_template = self.load_prompt_template()

    def load_prompt_template(self):
        with open("prompts/counselor_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()

    # 감정과 인지 왜곡에 맞는 전략 결합
        return f"{emotion_strategy} {distortion_strategy}"
    
    def _build_prompt(self, history, current_input, analysis):
        formatted_history = "\n".join([
            f"{msg['role'].capitalize()}: {msg['message']}" for msg in history
        ])
        # 전략 프롬프트 조합 (위치 기반 인자 전달!)
        strategy_prompt = build_prompt_with_strategies(
            analysis["반응유형"],
            analysis["상담단계"],
            analysis["상담접근법"]
        )
        return self.prompt_template.format(
            persona_prompt=self.persona_prompt,
            client_info=self.client_info,
            history=formatted_history,
            current_input=current_input,
            emotion=analysis["감정"],
            distortion=analysis["인지왜곡"],
            strategy_prompt=strategy_prompt
        )

    def generate_response(self, history, current_input):
        # SubLLM 분석
        analysis = self.subllm.analyze(current_input)
        filled_prompt = self._build_prompt(history, current_input, analysis)
        # LLM 호출
        response = self.llm.invoke(filled_prompt)
        content = response.content if isinstance(response, AIMessage) else str(response)
        # 응답 추출
        reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
        reply = reply_match.group(1).strip() if reply_match else content.strip()
        return {
            "reply": reply,
            "analysis": analysis
            }

    async def stream_response(self, history, current_input):
        """generate_response의 스트리밍 판.

        ("analysis", dict) 를 먼저 내고, 이어서 상담사 응답 본문만 ("delta", str) 로 흘린다.
        모델 출력에서 '상담사 응답:' 마커 뒤 첫 줄만 통과시키는 규칙은 generate_response의 정규식과 같다.
        """
        analysis = await self.subllm.analyze_async(current_input)
        yield ("analysis", analysis)
        filled_prompt = self._build_prompt(history, current_input, analysis)
        extractor = ReplyExtractor()
        async for chunk in self.llm.astream(filled_prompt):
            text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            out = extractor.feed(text)
            if out:
                yield ("delta", out)
            if extractor.done:
                break
        tail = extractor.finish()
        if tail:
            yield ("delta", tail)
