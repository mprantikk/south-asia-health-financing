"""Build charts (docs/*.png), REPORT.md and the key-numbers block in README.md."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .analysis import change, latest, scorecard, trend  # noqa: E402
from .checks import run_checks  # noqa: E402
from .config import COUNTRIES, FOCUS, INDICATORS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BLUE, ORANGE, AQUA, GREY = "#257de0", "#f47230", "#00b894", "#c2c2c2"
INK, INK2, GRID = "#191919", "#666666", "#ececec"
OOP, PC, GDP, GOV = "SH.XPD.OOPC.CH.ZS", "SH.XPD.CHEX.PC.CD", "SH.XPD.CHEX.GD.ZS", "SH.XPD.GHED.CH.ZS"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GREY, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "figure.dpi": 150,
})


def _title(ax, title, subtitle):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK, pad=22)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9.5, color=INK2)


def chart_oop_trend(df: pd.DataFrame, path: Path) -> None:
    t = trend(df, OOP, [FOCUS, "SAS", "WLD"])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for iso, color, label in [(FOCUS, BLUE, "Bangladesh"), ("SAS", ORANGE, "South Asia"), ("WLD", AQUA, "World")]:
        if iso in t:
            s = t[iso].dropna()
            ax.plot(s.index, s.values, color=color, lw=2)
            ax.annotate(f"{label} {s.iloc[-1]:.0f}%", (s.index[-1], s.iloc[-1]), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="x", visible=False)
    _title(ax, "Out-of-pocket share of health spending", "Share of all health spending paid directly by households")
    ax.margins(x=0.02)
    fig.subplots_adjust(right=0.8)
    fig.text(0.01, 0.01, "Source: World Bank WDI (WHO Global Health Expenditure Database)", fontsize=8, color=INK2)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def chart_latest_bars(df: pd.DataFrame, code: str, path: Path, fmt, title: str, subtitle: str) -> None:
    lat = latest(df)
    sub = lat[(lat.indicator == code) & (lat.iso3.isin(COUNTRIES))].sort_values("value")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = [BLUE if i == FOCUS else GREY for i in sub.iso3]
    bars = ax.barh(sub.country, sub.value, color=colors, height=0.62)
    for b, v, yr in zip(bars, sub.value, sub.year):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f"  {fmt(v)} ({yr})", va="center", fontsize=9, color=INK)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, sub.value.max() * 1.25)
    ax.xaxis.set_major_formatter(lambda v, _: fmt(v))
    _title(ax, title, subtitle)
    fig.text(0.01, 0.01, "Source: World Bank WDI · latest available year in brackets", fontsize=8, color=INK2)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def insights(df: pd.DataFrame, card: pd.DataFrame) -> list[str]:
    c = card.set_index("indicator")
    out = []
    if OOP in c.index:
        r = c.loc[OOP]
        out.append(f"Households pay **{r.bangladesh:.0f}%** of all health spending out of pocket in Bangladesh ({r.year}), "
                   f"against a South Asia median of {r.south_asia_median:.0f}% and a world figure of {r.world:.0f}%. "
                   f"That ranks Bangladesh **{r.rank_in_south_asia}** in the region (1 = lowest burden).")
        ch = change(df, OOP, FOCUS)
        if ch:
            direction = "up" if ch[3] > ch[1] else "down"
            out.append(f"The out-of-pocket share has moved {direction} from {ch[1]:.0f}% in {ch[0]} to {ch[3]:.0f}% in {ch[2]}.")
    if GOV in c.index:
        r = c.loc[GOV]
        out.append(f"Government pays only **{r.bangladesh:.0f}%** of health spending (South Asia median {r.south_asia_median:.0f}%), "
                   "which is the other side of the same coin.")
    if PC in c.index and GDP in c.index:
        p, g = c.loc[PC], c.loc[GDP]
        out.append(f"Total health spending is **US${p.bangladesh:,.0f} per person** ({g.bangladesh:.1f}% of GDP), "
                   f"rank {p.rank_in_south_asia} in South Asia.")
    return out


def _fmt(v, unit):
    if v is None or pd.isna(v):
        return "–"
    return f"${v:,.0f}" if unit == "US$" else f"{v:,.1f}"


def write_report(df: pd.DataFrame, card: pd.DataFrame, fetched_at: str, check_summary: list[str]) -> str:
    lines = [
        "# Health financing benchmark: Bangladesh vs South Asia",
        "",
        f"_Generated automatically from World Bank open data · fetched {fetched_at} · {', '.join(check_summary)}_",
        "",
        "## Key findings",
        "",
        *[f"- {i}" for i in insights(df, card)],
        "",
        "## Scorecard (latest available year)",
        "",
        "| Indicator | Year | Bangladesh | South Asia median | South Asia | Lower middle income | World | Rank in South Asia |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in card.itertuples():
        mark = "🟢" if r.better_than_median else "🔴"
        lines.append(f"| {r.name} | {r.year} | {mark} {_fmt(r.bangladesh, r.unit)} | {_fmt(r.south_asia_median, r.unit)} | "
                     f"{_fmt(r.south_asia_aggregate, r.unit)} | {_fmt(r.lower_middle_income, r.unit)} | {_fmt(r.world, r.unit)} | {r.rank_in_south_asia} |")
    lines += ["", "🟢 better than the South Asia median · 🔴 worse. Rank 1 = best in the region for that indicator.",
              "", "![Out-of-pocket trend](docs/oop_trend.png)", "", "![Out-of-pocket by country](docs/oop_latest.png)",
              "", "![Spending per person](docs/spend_per_capita.png)", ""]
    return "\n".join(lines)


def update_readme_block(readme: Path, block: str) -> None:
    text = readme.read_text()
    new = re.sub(r"(<!-- KEY-NUMBERS:START -->).*?(<!-- KEY-NUMBERS:END -->)",
                 lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}", text, flags=re.S)
    readme.write_text(new)


def build(data_path: Path = ROOT / "data" / "health_financing.csv") -> pd.DataFrame:
    df = pd.read_csv(data_path)
    check_summary = run_checks(df)
    card = scorecard(df)
    DOCS.mkdir(exist_ok=True)
    chart_oop_trend(df, DOCS / "oop_trend.png")
    chart_latest_bars(df, OOP, DOCS / "oop_latest.png", lambda v: f"{v:.0f}%",
                      "Out-of-pocket share by country", "Lower is better: less financial risk for households")
    chart_latest_bars(df, PC, DOCS / "spend_per_capita.png", lambda v: f"${v:,.0f}",
                      "Health spending per person (US$)", "Current health expenditure per capita")
    fetched = (ROOT / "data" / "FETCHED_AT").read_text().strip() if (ROOT / "data" / "FETCHED_AT").exists() else "n/a"
    (ROOT / "REPORT.md").write_text(write_report(df, card, fetched, check_summary))
    card.to_csv(ROOT / "data" / "scorecard.csv", index=False)
    if (ROOT / "README.md").exists():
        update_readme_block(ROOT / "README.md", "\n".join(f"- {i}" for i in insights(df, card)) + f"\n\n_Data fetched {fetched}._")
    return card


if __name__ == "__main__":
    print(build().to_string(index=False))
