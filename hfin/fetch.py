"""Extract: World Bank Indicators API -> tidy CSV.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
Response shape: [ {page, pages, per_page, total, ...}, [ {indicator, country,
countryiso3code, date, value, ...}, ... ] ]
"""

from __future__ import annotations

import csv
import datetime as dt
import time
from pathlib import Path

import requests

from .config import AGGREGATES, API, COUNTRIES, INDICATORS, START_YEAR

DATA = Path(__file__).resolve().parent.parent / "data"
FIELDS = ["iso3", "country", "indicator", "year", "value"]
# Some aggregates come back without an ISO3 code, only the World Bank's 2-character id
AGGREGATE_IDS = {"XN": "LMC", "8S": "SAS", "1W": "WLD"}


def parse_page(payload: list) -> tuple[list[dict], int]:
    """Turn one API page into tidy rows; return (rows, total_pages)."""
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        message = payload[0].get("message") if isinstance(payload, list) and payload else payload
        raise ValueError(f"Unexpected API response: {message}")
    meta, records = payload
    rows = []
    for r in records:
        if r.get("value") is None:
            continue
        rows.append({
            "iso3": r.get("countryiso3code") or AGGREGATE_IDS.get(r["country"]["id"], r["country"]["id"]),
            "country": r["country"]["value"],
            "indicator": r["indicator"]["id"],
            "year": int(r["date"]),
            "value": float(r["value"]),
        })
    return rows, int(meta.get("pages", 1))


def _get(url: str, params: dict, session: requests.Session, retries: int = 3) -> list:
    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def fetch_indicator(code: str, session: requests.Session) -> list[dict]:
    codes = ";".join(list(COUNTRIES) + list(AGGREGATES))
    url = f"{API}/country/{codes}/indicator/{code}"
    params = {"format": "json", "per_page": 1000, "date": f"{START_YEAR}:{dt.date.today().year}"}
    rows, pages = parse_page(_get(url, params, session))
    for page in range(2, pages + 1):
        more, _ = parse_page(_get(url, {**params, "page": page}, session))
        rows += more
    return rows


def fetch_all(out: Path = DATA / "health_financing.csv") -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with requests.Session() as s:
        for code in INDICATORS:
            got = fetch_indicator(code, s)
            print(f"{code}: {len(got)} values")
            rows += got
    rows.sort(key=lambda r: (r["indicator"], r["iso3"], r["year"]))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    (out.parent / "FETCHED_AT").write_text(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d") + "\n")
    return len(rows)


if __name__ == "__main__":
    print(f"Wrote {fetch_all()} rows")
