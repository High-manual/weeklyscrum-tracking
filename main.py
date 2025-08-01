import os
import openai
import pandas as pd
import logging
from dotenv import load_dotenv
from notion_api import get_today_status
from datetime import datetime
from config import GROUPS

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def summarize_day(task, issue, method, result):
    try:
        # 실제 내용만 포함하도록 필터링
        content_parts = []
        if task and task.strip():
            content_parts.append(f"작업명: {task}")
        if issue and issue.strip():
            content_parts.append(f"문제: {issue}")
        if method and method.strip():
            content_parts.append(f"해결방법: {method}")
        if result and result.strip():
            content_parts.append(f"결과: {result}")
        
        if not content_parts:
            return "작업 내용 없음"
        
        prompt = (
            "다음은 하루 동안 수행한 작업입니다. 주어진 내용을 그대로 요약만 하세요. 추가 설명, 추측, 제안사항, 향후 계획 등은 절대 포함하지 마세요. 오직 주어진 사실만 간단히 정리하세요.\n\n"
            + "\n".join(content_parts) +
            "\n\n위 내용만 사용해서 1줄로 요약하세요. 없는 내용은 절대 추가하지 마세요."
        )
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 요약 전문가입니다. 주어진 내용만 사용하세요. 추측, 제안, 향후 계획, 추가 설명은 절대 하지 마세요. 오직 주어진 사실만 요약하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
    except Exception:
        logger.exception("하루 요약 중 오류 발생")
        return "요약 실패"

def summarize_overall(logs):
    try:
        prompt = (
            "다음은 한 담당자의 날짜별 작업 요약입니다.\n"
            "주어진 작업 내용만을 사용해서 요약하세요. 추측, 제안사항, 향후 계획, 개선 필요사항 등은 절대 추가하지 마세요.\n"
            "불릿 포인트 형식으로 실제 수행한 작업만 간단히 정리하세요.\n\n"
            "작업 요약:\n" + "\n".join(f"- {log}" for log in logs) +
            "\n\n위 내용만 사용해서 요약하세요. 없는 내용은 절대 추가하지 마세요. 최대 5줄로 요약하세요."
        )
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 요약 전문가입니다. 주어진 내용만 사용하세요. 추측, 제안, 향후 계획, 개선사항은 절대 하지 마세요. 오직 실제 수행한 작업만 요약하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
    except Exception:
        logger.exception("전체 요약 중 오류 발생")
        return "전체 요약 실패"

def process_weekly_summary(all_results):
    """
    수집된 데이터를 주차별로 그룹화하고 작업 기록과 요약을 생성합니다.
    """
    weekly_summary = {}
    
    # 사람별로 데이터 그룹화
    for result in all_results:
        person_key = f"{result['조']}_{result['이름']}"
        if person_key not in weekly_summary:
            weekly_summary[person_key] = {
                "조": result['조'],
                "이름": result['이름'],
                "날짜별_작업기록": [],
                "일별_요약": []
            }
        
        # 작업날짜가 있는 경우에만 처리
        if result['작업날짜']:
            # LLM으로 일별 작업을 자연스럽게 요약
            daily_summary = summarize_day(
                result['작업명'], 
                result['문제/이슈'], 
                result['해결방법'], 
                result['결과 내용']
            )
            
            # 날짜: LLM 요약 내용 형식으로 작성
            daily_record = f"{result['작업날짜']}: {daily_summary}"
            weekly_summary[person_key]["날짜별_작업기록"].append(daily_record)
            
            # 일별 요약도 같은 내용으로 저장 (전체 요약용, 날짜 제외)
            weekly_summary[person_key]["일별_요약"].append(daily_summary)
    
    # 최종 주차별 요약 데이터 생성
    final_results = []
    for person_key, data in weekly_summary.items():
        # 날짜별 작업기록을 하나의 문자열로 결합
        combined_records = "\n".join(data["날짜별_작업기록"])
        
        # 전체 요약 생성 (일별 요약들을 기반으로)
        if data["일별_요약"]:
            overall_summary = summarize_overall(data["일별_요약"])
        else:
            overall_summary = "작업 기록 없음"
        
        final_results.append({
            "조": data["조"],
            "이름": data["이름"],
            "날짜별_작업기록": combined_records,
            "요약": overall_summary
        })
    
    # 조, 이름 순으로 정렬
    final_results = sorted(final_results, key=lambda x: (int(x["조"]), x["이름"]))
    return final_results

def main():
    """
    메인 실행 함수
    """
    # config.py 파일에서 GROUPS 정보 읽기
    groups = GROUPS
    logger.info(f"총 {len(groups)}개 조의 정보를 읽어왔습니다.")
    
    # 사용자로부터 날짜 입력 받기
    print("데이터를 가져올 시작 날짜를 입력하세요 (YYYY-MM-DD 형식, 예: 2025-07-28):")
    print("빈 값으로 엔터를 누르면 오늘 날짜만 가져옵니다.")
    
    start_date = input().strip()
    if not start_date:
        start_date = None
        logger.info("오늘 날짜 데이터만 가져옵니다.")
    else:
        logger.info(f"{start_date} 이후 데이터를 가져옵니다.")
    
    # 각 조별로 데이터 수집 및 처리
    all_results = []
    for group in groups:
        try:
            logger.info(f"{group['name']}조 데이터 수집 중...")
            group_results = get_today_status(group, start_date)
            all_results.extend(group_results)
        except Exception as e:
            logger.error(f"{group['name']}조 데이터 수집 중 오류: {e}")
    
    if all_results:
        logger.info("주차별 요약 처리 중...")
        # 주차별 요약 데이터 생성
        weekly_results = process_weekly_summary(all_results)
        
        # 결과를 DataFrame으로 변환
        df = pd.DataFrame(weekly_results)
        
        # CSV 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"notion_weekly_summary_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"주차별 요약 결과가 {filename} 파일로 저장되었습니다.")
        
        # 결과 출력
        print("\n=== 주차별 요약 결과 ===\n")
        for result in weekly_results:
            print(f"조: {result['조']}, 이름: {result['이름']}")
            print(f"날짜별 작업기록:\n{result['날짜별_작업기록']}")
            print(f"요약:\n{result['요약']}")
            print("=" * 70)
    else:
        logger.info("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
