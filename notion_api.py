from notion_client import Client
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

def get_today_status(group, start_date=None):
    """
    노션 DB에서 지정된 날짜 이후의 데이터를 가져옵니다.
    
    Args:
        group: 조 정보 (id, name, members 포함)
        start_date: 시작 날짜 ("2025-07-28" 형식, 없으면 오늘 날짜 사용)
    """
    if start_date is None:
        now = datetime.now()
        target_date = now.strftime("%Y-%m-%d")
        filter_condition = {"equals": target_date}
    else:
        # 날짜 형식 검증
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            filter_condition = {"on_or_after": start_date}
        except ValueError:
            raise ValueError(f"날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요. 입력값: {start_date}")
    
    results = []
    db_id = group["id"]
    members = group["members"]

    # Notion DB에서 지정된 날짜 이후 데이터 가져오기
    query = notion.databases.query(
        **{
            "database_id": db_id,
            "filter": {
                "and": [
                    {
                        "property": "작업날짜",  # 실제 노션 DB의 날짜 속성명에 맞게 수정 필요
                        "date": filter_condition
                    },
                    {
                        "property": "프로젝트 유형",
                        "select": {"does_not_equal": "미니플젝"}
                    }
                ]
            }
        }
    )
    # 각 row를 개별적으로 처리 (날짜별로 분리)
    for row in query["results"]:
        # 담당자 이름들 추출
        people = row["properties"]["담당자"]["people"]
        names = []
        if people:
            names = [person["name"].strip() for person in people]
        else:
            names = ["(담당자 없음)"]
            
        # 작업상태 추출
        status = row["properties"]["작업상태"].get("status", {}).get("name", "")
        # 작업날짜 추출
        work_date = ""
        if row["properties"]["작업날짜"]["date"]:
            work_date = row["properties"]["작업날짜"]["date"]["start"]
        # 결과 내용
        result_text = "\n".join([t["plain_text"] for t in row["properties"]["결과"]["rich_text"]])
        # 해결방법, 문제/이슈, 작업명
        solution_text = "\n".join([t["plain_text"] for t in row["properties"]["해결방법"]["rich_text"]])
        issue_text = "\n".join([t["plain_text"] for t in row["properties"]["문제/이슈"]["rich_text"]])
        title_list = row["properties"]["작업명"]["title"]
        title_text = title_list[0]["plain_text"] if title_list else ""

        # 각 담당자별로 개별 작업 항목을 생성
        for name in names:
            results.append({
                "조": group["name"],
                "이름": name,
                "작업날짜": work_date,
                "작업명": title_text,
                "문제/이슈": issue_text,
                "해결방법": solution_text,
                "결과 내용": result_text,
            })

    # 멤버 중 작업 기록이 없는 사람들도 포함
    existing_members = {result["이름"] for result in results}
    for member in members:
        if member not in existing_members:
            results.append({
                "조": group["name"],
                "이름": member,
                "작업날짜": "",
                "작업명": "",
                "문제/이슈": "",
                "해결방법": "",
                "결과 내용": "",
            })
    # 조, 이름 순으로 정렬
    results = sorted(results, key=lambda x: (int(x["조"]), x["이름"]))
    return results 