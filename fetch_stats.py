"""
Notion DB에서 진행 상태별 과제 수를 조회해 data.json으로 저장합니다.
GitHub Actions에서 실행되며, NOTION_TOKEN 환경변수가 필요합니다.

NOTION_DATABASE_ID: 전략과제 DB의 Notion 페이지 ID
  - Notion에서 해당 DB를 열고 URL에서 추출
  - 예: https://notion.so/workspace/XXXXXXXX → XXXXXXXX
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "0eb13c4f-c392-48b6-b3bf-d186847b0075")
STATUS_PROP = "진행 상태"

if not TOKEN:
    print("ERROR: NOTION_TOKEN 환경변수가 없습니다.", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def count_by_status(status_value: str) -> int:
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": STATUS_PROP,
            "status": {"equals": status_value},
        },
        "page_size": 1,
    }
    total = 0
    while True:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        total += len(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return total


def main():
    진행중 = count_by_status("진행중")
    보류   = count_by_status("보류")
    완료   = count_by_status("완료")
    삭제   = count_by_status("삭제")
    total  = 진행중 + 보류 + 완료 + 삭제

    stats = {
        "total":      total,
        "inProgress": 진행중,
        "hold":       보류,
        "done":       완료,
        "deleted":    삭제,
        "updatedAt":  datetime.now(timezone.utc).isoformat(),
    }

    out_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"✅ data.json 업데이트: {stats}")


if __name__ == "__main__":
    main()
