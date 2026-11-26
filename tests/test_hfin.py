"""Offline tests. Fixtures are small made-up values in the World Bank API shape,
not real statistics."""

import datetime as dt

import pandas as pd
import pytest

from hfin.analysis import change, latest, scorecard
from hfin.checks import DataQualityError, run_checks
from hfin.config import COUNTRIES, INDICATORS
from hfin.fetch import parse_page


def api_record(iso, code, year, value):
    return {"indicator": {"id": code, "value": "x"}, "country": {"id": iso[:2], "value": iso},
            "countryiso3code": iso, "date": str(year), "value": value, "unit": "", "obs_status": "", "decimal": 1}


def test_parse_page_skips_nulls_and_reads_pages():
    payload = [{"page": 1, "pages": 3, "per_page": 2, "total": 5},
               [api_record("BGD", "SH.XPD.OOPC.CH.ZS", 2021, 73.0), api_record("BGD", "SH.XPD.OOPC.CH.ZS", 2022, None)]]
    rows, pages = parse_page(payload)
    assert pages == 3
    assert rows == [{"iso3": "BGD", "country": "BGD", "indicator": "SH.XPD.OOPC.CH.ZS", "year": 2021, "value": 73.0}]


def test_parse_page_raises_on_api_error():
    with pytest.raises(ValueError, match="Invalid value"):
        parse_page([{"message": [{"id": "120", "value": "Invalid value"}]}])


@pytest.fixture
def tidy():
    rows = []
    for i, iso in enumerate(list(COUNTRIES) + ["SAS", "LMC", "WLD"]):
        for code in INDICATORS:
            for year in (2012, 2017, 2021):
                base = 20 + i * 5 + (year - 2012)
                rows.append({"iso3": iso, "country": iso, "indicator": code, "year": year, "value": float(min(base, 95))})
    return pd.DataFrame(rows)


def test_checks_pass_on_clean_data(tidy):
    summary = run_checks(tidy, today=dt.date(2025, 1, 1))
    assert summary[2] == f"{len(INDICATORS)} indicators"


def test_checks_catch_duplicates_ranges_and_staleness(tidy):
    bad = pd.concat([tidy, tidy.iloc[[0]]])
    with pytest.raises(DataQualityError, match="duplicate"):
        run_checks(bad, today=dt.date(2025, 1, 1))
    bad = tidy.copy()
    bad.loc[bad.indicator == "SH.XPD.OOPC.CH.ZS", "value"] = 140.0
    with pytest.raises(DataQualityError, match="0-100"):
        run_checks(bad, today=dt.date(2025, 1, 1))
    with pytest.raises(DataQualityError, match="stale"):
        run_checks(tidy, today=dt.date(2035, 1, 1))


def test_latest_takes_most_recent_year(tidy):
    lat = latest(tidy)
    assert lat.year.unique().tolist() == [2021]
    assert len(lat) == tidy.groupby(["iso3", "indicator"]).ngroups


def test_scorecard_rank_respects_direction(tidy):
    card = scorecard(tidy).set_index("indicator")
    # BGD has the smallest values in the fixture: best where lower is better, worst where higher is better
    n = len(COUNTRIES)
    assert card.loc["SH.XPD.OOPC.CH.ZS", "rank_in_south_asia"] == f"1 of {n}"
    assert card.loc["SH.XPD.CHEX.GD.ZS", "rank_in_south_asia"] == f"{n} of {n}"
    assert bool(card.loc["SH.XPD.OOPC.CH.ZS", "better_than_median"])


def test_change_uses_value_about_ten_years_back(tidy):
    assert change(tidy, "SH.XPD.OOPC.CH.ZS", "BGD") == (2012, 20.0, 2021, 29.0)
