# Notion 주차별 데일리 스크럼 추적 및 요약 시스템

## 주요 기능

- **다중 팀 지원**: 여러 조(팀)의 Notion 데이터베이스를 동시에 모니터링
- **AI 기반 요약**: OpenAI GPT를 활용한 자동 업무 요약
- **기간별 데이터 수집**: 특정 날짜부터 또는 당일 데이터만 선택적 수집
- **CSV 출력**: 결과를 CSV 파일로 자동 저장하여 추가 분석 가능

## 프로젝트 구조

```
notion_tracking/
├── main.py                    # 메인 실행 파일
├── notion_api.py             # Notion API 연동 모듈
├── config.py                 # 팀 설정 파일
├── requirements.txt          # 의존성 패키지 목록
├── .env                      # 환경 변수 파일
├── .gitignore               # Git 무시 파일 목록
└── README.md                # 프로젝트 설명서
```

## 설치 방법

1. **레포지토리 클론**
   ```bash
   git clone <repository-url> ./
   ```

2. **의존성 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정**
   
   프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:
   
   ```env
   NOTION_API_KEY=your_notion_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```
4. **팀 정보 입력**

`config.py` 파일에서 각 팀의 정보를 설정하세요:

```python
GROUPS = [
    {
        "id": "notion_database_id",      # Notion 데이터베이스 ID
        "name": "1",                     # 팀 번호
        "members": ["팀원1", "팀원2"]    # 팀원 목록
    }
]
```

## 사용 방법

1. **프로그램 실행**
   ```bash
   python main.py
   ```

2. **날짜 입력**
   - 특정 날짜부터 데이터 수집: `2025-01-01` 형식으로 입력
   - 당일 데이터만 수집: 빈 값으로 엔터 입력

3. **결과 확인**
   - 콘솔에서 실시간 처리 현황 확인
   - 생성된 CSV 파일에서 상세 결과 확인

## 출력 파일

- **파일명**: `notion_weekly_summary_YYYYMMDD.csv`
- **내용**: 
  - 조별, 팀원별 업무 현황
  - 날짜별 작업 기록
  - AI 생성 업무 요약

## Notion 데이터베이스 요구사항

프로그램이 올바르게 작동하려면 Notion 데이터베이스에 다음 속성들이 필요합니다:

- **작업날짜** (Date): 작업 수행 날짜
- **담당자** (People): 작업 담당자
- **작업명** (Title): 작업 제목
- **문제/이슈** (Rich Text): 발생한 문제나 이슈
- **해결방법** (Rich Text): 문제 해결 방법
- **결과** (Rich Text): 작업 결과
- **작업상태** (Status): 작업 진행 상태
- **프로젝트 유형** (Select): 프로젝트 분류"# weeklyscrum-tracking" 
