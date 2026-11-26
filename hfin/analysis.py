"""Benchmarks: latest values, Bangladesh's rank in South Asia, gaps and trends."""

from __future__ import annotations

import pandas as pd

from .config import COUNTRIES, FOCUS, INDICATORS


def load(path) -> pd.DataFrame:
    return pd.read_csv(path)


def latest(df: pd.DataFrame) -> pd.DataFrame:
    """Most recent value for each country and indicator."""
    idx = df.groupby(["iso3", "indicator"]).year.idxmax()
    return df.loc[idx].reset_index(drop=True)


def scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """One row per indicator: Bangladesh vs the South Asia median and aggregates, plus rank."""
    lat = latest(df)
    rows = []
    for code, (name, unit, higher_better) in INDICATORS.items():
        sub = lat[lat.indicator == code]
        peers = sub[sub.iso3.isin(COUNTRIES)]
        focus = peers[peers.iso3 == FOCUS]
        if focus.empty:
            continue
        val = float(focus.value.iloc[0])
        ranked = peers.sort_values("value", ascending=not higher_better).reset_index(drop=True)
        rank = int(ranked.index[ranked.iso3 == FOCUS][0]) + 1
        median = float(peers.value.median())
        agg = lambda iso: (float(sub[sub.iso3 == iso].value.iloc[0]) if (sub.iso3 == iso).any() else None)
        rows.append({
            "indicator": code,
            "name": name,
            "unit": unit,
            "year": int(focus.year.iloc[0]),
            "bangladesh": round(val, 1),
            "south_asia_median": round(median, 1),
            "south_asia_aggregate": None if agg("SAS") is None else round(agg("SAS"), 1),
            "lower_middle_income": None if agg("LMC") is None else round(agg("LMC"), 1),
            "world": None if agg("WLD") is None else round(agg("WLD"), 1),
            "rank_in_south_asia": f"{rank} of {len(peers)}",
            "better_than_median": (val >= median) if higher_better else (val <= median),
        })
    return pd.DataFrame(rows)


def trend(df: pd.DataFrame, code: str, isos: list[str]) -> pd.DataFrame:
    """Wide year x country table for one indicator."""
    sub = df[(df.indicator == code) & (df.iso3.isin(isos))]
    return sub.pivot_table(index="year", columns="iso3", values="value").sort_index()


def change(df: pd.DataFrame, code: str, iso: str, years: int = 10) -> tuple[int, float, int, float] | None:
    """(start_year, start_value, end_year, end_value) over roughly `years` years."""
    s = df[(df.indicator == code) & (df.iso3 == iso)].sort_values("year")
    if s.empty:
        return None
    end = s.iloc[-1]
    start_candidates = s[s.year <= end.year - years]
    start = start_candidates.iloc[-1] if not start_candidates.empty else s.iloc[0]
    return int(start.year), float(start.value), int(end.year), float(end.value)
