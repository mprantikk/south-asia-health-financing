"""Data quality checks on the tidy dataset. Raise on failure."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from .config import AGGREGATES, COUNTRIES, FOCUS, INDICATORS


class DataQualityError(Exception):
    pass


def run_checks(df: pd.DataFrame, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    problems = []
    if df.duplicated(["iso3", "indicator", "year"]).any():
        problems.append("duplicate iso3/indicator/year rows")
    missing_ind = set(INDICATORS) - set(df.indicator)
    if missing_ind:
        problems.append(f"indicators with no data: {sorted(missing_ind)}")
    pct = df[df.indicator.map(lambda c: INDICATORS.get(c, ("", ""))[1] == "%")]
    if ((pct.value < 0) | (pct.value > 100)).any():
        problems.append("percentage outside 0-100")
    if (df.value < 0).any():
        problems.append("negative values")
    focus = df[df.iso3 == FOCUS]
    for code in INDICATORS:
        sub = focus[focus.indicator == code]
        if sub.empty:
            problems.append(f"{FOCUS} has no data for {code}")
        elif sub.year.max() < today.year - 6:
            problems.append(f"{FOCUS} {code} is stale (latest {sub.year.max()})")
    countries_with_data = set(df.iso3) & set(COUNTRIES)
    if len(countries_with_data) < len(COUNTRIES) - 1:
        problems.append(f"only {len(countries_with_data)} of {len(COUNTRIES)} countries have data")
    if "SAS" not in set(df.iso3) and not (set(AGGREGATES) & set(df.iso3)):
        problems.append("no regional aggregate data")
    if problems:
        raise DataQualityError("; ".join(problems))
    return [f"{len(df):,} values", f"{df.iso3.nunique()} countries/aggregates", f"{df.indicator.nunique()} indicators"]
