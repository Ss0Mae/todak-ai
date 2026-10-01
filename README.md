# todak-ai

토닥 AI 서버 (FastAPI + LangChain + MongoDB). 원본: [Todak-Chatbot/AI](https://github.com/Todak-Chatbot/AI) (팀 레포, 2025-05 종료).
이 레포는 그 포크이며 `main` 은 원본 그대로, 개선은 브랜치 `feature/async-streaming` 에 있다. 측정과 이야기는
[todak-lab](https://github.com/Ss0Mae/todak-lab) `STORY.md`.

## 포크에서 바꾼 것 (`feature/async-streaming`)

| 문제 (원본) | 변경 |
|---|---|
| `async def` 핸들러 안에서 OpenAI·MongoDB·TTS 를 동기 호출 → 이벤트 루프가 막혀 **동시성 1** | 1단계: 블로킹 핸들러를 `def` 로 (스레드풀) · 2단계: `/start_chat` 을 AsyncOpenAI + `astream` 으로 비동기 네이티브화 |
| 한 턴에 LLM 3회 직렬 (분석 → 상담사 → 주제 분류) | 주제 분류를 상담사 응답 생성과 병렬 실행 |
| 응답이 끝나야 한 번에 반환 | `POST /start_chat/stream` SSE (`{"type":"delta"}` … `{"type":"done"}`). 모델 출력의 `상담사 응답:` 마커 뒤 첫 줄만 흘리는 필터는 기존 정규식과 같은 규칙 (`agents/reply_extractor.py`, `tests/`) |
| 설정이 `conf.d/config.yaml` 파일에만 있어 컨테이너로 띄우기 어려움 | 파일 없으면 환경변수(`OPENAI_API_KEY`, `MONGODB_URI`, `CLOVA_*`) 폴백 |

바꾸지 않은 것: 프롬프트·페르소나·분석 로직, 음성(`/voice_chat`)·리포트·인사 경로의 동기 구현(스레드풀에서만 돌게 함).

---

2025-1학기 세종대학교 캡스톤 "심리상담 서비스" AI파트  
CapStone_Chat/  
CapStone/  
│   
├── app.py # FastAPI 서버 메인 파일 (API 라우터 정의)  
├── chat.py # 상담 세션 관리 및 대화 처리 (TherapySimulation 클래스)  
├── DB.py # MongoDB 연결 및 대화/사용자 정보 저장/조회 함수    
├── report.py # 채팅기록 분석결과 진행  
├── config.py # 설정 로드 (API 키, 환경변수 등)   
├── DockerFile # Docker 빌드 파일  
├── README.md # 프로젝트 소개 문서  
├── requirements.txt # 필요한 Python 패키지 목록  
│  
├── agents/ # 🤖 에이전트 관련 코드 모음  
│ ├── counselor_agent.py # 메인 상담사 응답 생성 (LLM 호출)  
│ ├── evaluator_agent.py # 대화 평가 및 요약 담당  
│ └── subllm_agent.py # 감정, 왜곡 등 서브 모델 분석  
│  
├── utils/ # 음성대화관련 코드   
├── tts_clova.py #Clova TTS API를 활용해 페르소나와 감정에 맞는 음성(mp3)을 생성 │  
├── starter/ # 먼저 말걸기 관련 코드   
├── generate_greet.py #사용자 정보와 상담 분석 결과를 바탕으로, 페르소나가 먼저 인사말을 생성해 대화를 시작하는 기능을 제공합니다.  
├── first.txt # 사용자 정보와 상담 데이터를 기반으로 챗봇이 먼저 인삿말을 생성하는 트리거 프롬프트  
│  
├── prompts/  
├── cure/ # 상담 기법 (치료 방식) 프롬프트  
│ ├── 없음.txt # 치료 전략이 아직 없을 경우  
│ ├── ACT.txt # 수용전념치료 (Acceptance & Commitment Therapy)  
│ ├── CBT.txt # 인지행동치료 (Cognitive Behavioral Therapy)  
│ ├── PCT.txt # 인간중심치료 (Person-Centered Therapy)  
│ ├── PDT.txt # 정신역동치료 (Psychodynamic Therapy)  
│ └── SFBT.txt # 해결중심치료 (Solution-Focused Brief Therapy)  
│  
├── react/ # 내담자의 반응 유형 (태도) 프롬프트  
│ ├── 없음.txt # 반응 없음 또는  
│ ├── 의존적.txt # 지나치게 의존적인 태도  
│ ├── 저항적.txt # 방어적, 회피적인 반응  
│ ├── 적대적.txt # 공격적, 반항적인 반응  
│ └── 협조적.txt # 긍정적이고 열린 태도  
│  
├── stage/ # 상담 단계별 프롬프트  
│ ├── 없음.txt # 단계 미정  
│ ├── 1단계.txt # 관계 형성 및 라포 구축 단계  
│ ├── 2단계.txt # 감정 탐색 및 문제 인식   
│ ├── 3단계.txt # 통찰 및 인지 재구성  
│ ├── 4단계.txt # 행동 변화 유도  
│ └── 5단계.txt # 상담 마무리 및 재발 방지  
│  
├── 8살_민지원.txt  
├── 26살_한여름.txt  
├── 55살_김서연.txt  
├── counselor_prompt.txt # 상담사 공통 응답 프레임워크  
├── evaluation_combined.txt # 평가 (감정 변화, 전략 평가 등) 통합 프롬프트  
├── prompt_builder.py # 위의 프롬프트들을 조립하여 GPT 입력 생성  
├── subllm_prompt.txt # 감정 분석/왜곡 탐지용 서브 LLM 프롬프트  
└── report_prompt.txt #내담자의 대화 내용을 바탕으로 상담 주제, 감정 비율, 인지 왜곡, 맞춤형 미션을 자동 분석하여 JSON 리포트를 생성하는 전문 심리상담 평가프롬프트입니다.  