import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

import requests

SERVICE_KEY = os.environ.get("MOLIT_SERVICE_KEY", "").strip()
REGION_CODE = "27140"  # Daegu Dong-gu
TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
PAGE_SIZE = 1000
OUTPUT = Path("data/transactions.json")


def text(node, name):
    value = node.findtext(name)
    return value.strip() if value else ""


def number(value):
    try:
        return int(value.replace(",", "").strip())
    except (AttributeError, ValueError):
        return 0


def fetch_month(url, month):
    rows = []
    page = 1
    total = None
    while total is None or (page - 1) * PAGE_SIZE < total:
        params = {
            "serviceKey": SERVICE_KEY,
            "LAWD_CD": REGION_CODE,
            "DEAL_YMD": month,
            "pageNo": page,
            "numOfRows": PAGE_SIZE,
        }
        response = requests.get(url, params=params, timeout=40)
        if response.status_code != 200:
            raise RuntimeError(f"MOLIT API HTTP {response.status_code} for {month}")
        root = ET.fromstring(response.content)
        result_code = root.findtext(".//header/resultCode") or root.findtext(".//cmmMsgHeader/returnReasonCode")
        if result_code and result_code not in {"000", "00"}:
            message = root.findtext(".//header/resultMsg") or root.findtext(".//cmmMsgHeader/errMsg") or "API request failed"
            raise RuntimeError(f"MOLIT API error {result_code}: {message}")
        body = root.find(".//body")
        if body is None:
            raise RuntimeError(f"MOLIT API returned no body for {month}")
        total_text = body.findtext("totalCount")
        total = int(total_text or "0")
        items = body.findall("./items/item")
        rows.extend(items)
        if not items or len(items) < PAGE_SIZE:
            break
        page += 1
        time.sleep(0.15)
    return rows


def contract_date(item):
    y = text(item, "dealYear")
    m = text(item, "dealMonth").zfill(2)
    d = text(item, "dealDay").zfill(2)
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return ""


def normalize_trade(item):
    return {
        "aptName": text(item, "aptNm"),
        "legalDong": text(item, "umdNm"),
        "lotNo": text(item, "jibun"),
        "contractDate": contract_date(item),
        "areaM2": float(text(item, "excluUseAr") or 0),
        "floor": text(item, "floor"),
        "buildYear": text(item, "buildYear"),
        "priceManwon": number(text(item, "dealAmount")),
    }


def normalize_rent(item):
    return {
        "aptName": text(item, "aptNm"),
        "legalDong": text(item, "umdNm"),
        "lotNo": text(item, "jibun"),
        "contractDate": contract_date(item),
        "areaM2": float(text(item, "excluUseAr") or 0),
        "floor": text(item, "floor"),
        "buildYear": text(item, "buildYear"),
        "depositManwon": number(text(item, "deposit")),
        "monthlyRentManwon": number(text(item, "monthlyRent")),
        "contractType": text(item, "contractType"),
    }


def months_to_fetch(today):
    y, m = today.year, today.month
    out = []
    for _ in range(13):
        out.append(f"{y}{m:02d}")
        m -= 1
        if m == 0:
            y -= 1
            m = 12
    return list(reversed(out))


def main():
    if not SERVICE_KEY:
        raise RuntimeError("Set the GitHub Actions secret MOLIT_SERVICE_KEY before running this workflow.")
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    months = months_to_fetch(today)
    result = {
        "status": "ready",
        "generatedAt": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "regionCode": REGION_CODE,
        "months": {},
    }
    for month in months:
        sale_items = fetch_month(TRADE_URL, month)
        rent_items = fetch_month(RENT_URL, month)
        result["months"][f"{month[:4]}-{month[4:]}"] = {
            "sales": [row for item in sale_items if (row := normalize_trade(item))["aptName"] and row["areaM2"] > 0 and row["priceManwon"] > 0],
            "rentals": [row for item in rent_items if (row := normalize_rent(item))["aptName"] and row["areaM2"] > 0],
        }
        time.sleep(0.15)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Fetched official apartment transactions for {len(months)} months into {OUTPUT}.")


if __name__ == "__main__":
    main()
