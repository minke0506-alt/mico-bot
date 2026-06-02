import requests
from datetime import datetime, timedelta
import os

DART_API_KEY = os.getenv("DART_API_KEY")

DONGKOOK_CORP_CODE = "00264529"  # 미코
DONGKOOK_STOCK_CODE = "059090"

IMPORTANT_KEYWORDS = [
    "임상", "식약처", "허가", "계약", "인수", "합병",
    "유상증자", "무상증자", "자기주식", "배당",
    "대표이사", "소송", "공정거래", "횡령",
    "사업보고서", "분기보고서", "반기보고서",
]

def fetch_dart_disclosures(days_back=1):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days_back)

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": DONGKOOK_CORP_CODE,
        "bgn_de": start_date.strftime("%Y%m%d"),
        "end_de": end_date.strftime("%Y%m%d"),
        "page_count": 20,
    }

    res = requests.get(url, params=params).json()

    if res.get("status") != "000":
        print(f"DART API 오류: {res.get('message')}")
        return []

    disclosures = []
    for item in res.get("list", []):
        disclosures.append({
            "rcept_no": item["rcept_no"],
            "title": item["report_nm"],
            "date": item["rcept_dt"],
            "submitter": item["flr_nm"],
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item['rcept_no']}"
        })

    return disclosures

def classify_importance(title):
    for keyword in IMPORTANT_KEYWORDS:
        if keyword in title:
            return "🔴 HIGH"
    return "🟡 일반"

def format_dart_for_claude(disclosures):
    if not disclosures:
        return ""
    lines = []
    for d in disclosures:
        importance = classify_importance(d["title"])
        date_fmt = f"{d['date'][:4]}-{d['date'][4:6]}-{d['date'][6:]}"
        lines.append(f"[{importance}] {date_fmt} | {d['title']} | 제출: {d['submitter']}")
    return "\n".join(lines)
