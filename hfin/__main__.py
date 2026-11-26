"""python -m hfin [fetch|report|all]"""
import sys

from .fetch import fetch_all
from .report import build

cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
if cmd in ("fetch", "all"):
    print(f"Fetched {fetch_all()} values")
if cmd in ("report", "all"):
    print(build().to_string(index=False))
