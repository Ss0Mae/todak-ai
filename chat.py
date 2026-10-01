import json
from pathlib import Path
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from config import load_config
from agents.subllm_agent import SubLLMAgent
from config import get_config, set_openai_api_key
from DB import get_chat_log, save_chat_log
from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime, timedelta, timezone
import os
import asyncio
from agents.subllm_agent import classify_topic, classify_topic_async # 새로 만든 함수가 있는 파일에서 import

# API 키 설정
set_openai_api_key()
kst = timezone(timedelta(hours=9))

# TherapySimulation 클래스에서 사용자 정보 확인
class TherapySimulation:
    def __init__(self, persona: str, chatId: int, userId: int, name: str, age: int, gender: str):
        self.persona = persona
        self.chatId = chatId
        self.userId = userId
        self.name = name
        self.age = age
        self.gender = gender
        self.history = []

        # Load chat log if it exists
        chat_log = get_chat_log(self.chatId)
        self.counselor_agent = CounselorAgent(
            client_info = f"이름: {self.name}, 나이: {self.age}세, 성별: {self.gender}",
            persona=self.persona
        )

        if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
            self.history = chat_log
        else:
            self.history = []

        # SubLLM analysis
        self.subllm_agent = SubLLMAgent()
        self.evaluator_agent = EvaluatorAgent()

    def run_single_turn(self, message: str):
        result = self.counselor_agent.generate_response(self.history, message)
        reply = result["reply"]
        analysis = result["analysis"]

        topic_result = classify_topic(message)

        user_entry = {
            "role": "client",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "topic": topic_result
        }

        bot_entry = {
            "role": "counselor",
            "message": reply,
            "timestamp":datetime.now(kst).isoformat(),
            "persona": self.persona  # 현재 사용된 페르소나 저장
        }

        self.history.extend([user_entry, bot_entry])
        save_chat_log(self.userId, self.chatId, user_entry, bot_entry)

        return {
            "reply": reply,
            "emotion": analysis.get("감정", "없음")
        }

    async def stream_turn(self, message: str):
        """run_single_turn의 스트리밍 판. 주제 분류는 응답 생성과 병렬로 돈다.

        {"type":"delta","content":...} 를 흘리고 마지막에 {"type":"done","reply":...,"emotion":...} 를 낸다.
        저장(MongoDB)은 응답이 끝까지 생성된 뒤에만 한다 — 중간에 끊긴 턴은 남기지 않는다.
        """
        topic_task = asyncio.create_task(classify_topic_async(message))
        analysis = {}
        parts = []
        async for kind, payload in self.counselor_agent.stream_response(self.history, message):
            if kind == "analysis":
                analysis = payload
            else:
                parts.append(payload)
                yield {"type": "delta", "content": payload}
        reply = "".join(parts).strip()
        topic_result = await topic_task
        user_entry = {
            "role": "client",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "topic": topic_result
        }
        bot_entry = {
            "role": "counselor",
            "message": reply,
            "timestamp": datetime.now(kst).isoformat(),
            "persona": self.persona
        }
        self.history.extend([user_entry, bot_entry])
        await asyncio.to_thread(save_chat_log, self.userId, self.chatId, user_entry, bot_entry)
        yield {"type": "done", "reply": reply, "emotion": analysis.get("감정", "없음")}


async def stream_response_from_input(persona: str, chatId: int, userId: int, name: str, age: int,
                                     gender: str, message: str):
    # 생성자가 MongoDB를 동기로 읽으므로 스레드로 뺀다
    sim = await asyncio.to_thread(TherapySimulation, persona, chatId, userId, name, age, gender)
    async for event in sim.stream_turn(message):
        yield event


def generate_response_from_input(persona: str, chatId: int, userId: int, name: str, age: int, 
                                 gender: str, message: str):
    sim = TherapySimulation(
        persona=persona,
        chatId=chatId,
        userId=userId,
        name=name,
        age=age,
        gender=gender
    )
    return sim.run_single_turn(message)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", default=None)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)  # chat_id 추가
    parser.add_argument("--user_id", required=True)  # 사용자 이름
    args = parser.parse_args()

#    run_chat_with_args(args.output_file, args.persona_type, args.chat_id, args.user_id)