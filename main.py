import os
from notion_client import Client
import yfinance as yf

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# Notion DB 속성명 (노션에서 만든 컬럼 이름과 동일해야 함)
PROP_TITLE = "Name"
PROP_DATE = "Date"
PROP_CLOSE = "Close"
PROP_CHG = "ChangePct"
PROP_SOURCE = "Source"

notion = Client(auth=NOTION_TOKEN)

def fetch_kospi_latest():
    t = yf.Ticker("^KS11")
    hist = t.history(period="10d")  # 휴일/주말 대비 넉넉히
    if hist.empty or len(hist) < 2:
        raise RuntimeError("KOSPI data not available (yfinance returned empty/too short).")

    last = hist.iloc[-1]
    prev = hist.iloc[-2]

    close = float(last["Close"])
    prev_close = float(prev["Close"])
    change_pct = ((close / prev_close) - 1.0) * 100.0 if prev_close != 0 else 0.0

    date_str = hist.index[-1].date().isoformat()  # YYYY-MM-DD
    return date_str, close, change_pct

def already_uploaded(date_str: str) -> bool:
    resp = notion.databases.query(
        database_id=NOTION_DATABASE_ID,
        filter={
            "property": PROP_DATE,
            "date": {"equals": date_str}
        },
        page_size=1
    )
    return len(resp.get("results", [])) > 0

def upload_row(date_str: str, close: float, change_pct: float):
    title = f"KOSPI {date_str}"
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            PROP_TITLE: {"title": [{"text": {"content": title}}]},
            PROP_DATE: {"date": {"start": date_str}},
            PROP_CLOSE: {"number": round(close, 2)},
            PROP_CHG: {"number": round(change_pct, 2)},
            PROP_SOURCE: {"rich_text": [{"text": {"content": "Yahoo Finance (^KS11)"}}]},
        },
    )

def main():
    date_str, close, change_pct = fetch_kospi_latest()
    upload_row(date_str, close, change_pct)
    print(f"Uploaded: {date_str} Close={close:.2f} ChangePct={change_pct:.2f}%")


if __name__ == "__main__":
    main()
