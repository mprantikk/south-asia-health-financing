"""What we pull and who we compare. Edit here to change the benchmark."""

FOCUS = "BGD"

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "PAK": "Pakistan",
    "NPL": "Nepal",
    "LKA": "Sri Lanka",
    "BTN": "Bhutan",
    "MDV": "Maldives",
    "AFG": "Afghanistan",
}

# World Bank aggregates used as reference lines
AGGREGATES = {
    "SAS": "South Asia",
    "LMC": "Lower middle income",
    "WLD": "World",
}

# indicator code: (short name, unit, higher_is_better)
INDICATORS = {
    "SH.XPD.CHEX.GD.ZS": ("Health spending, % of GDP", "%", True),
    "SH.XPD.CHEX.PC.CD": ("Health spending per person, US$", "US$", True),
    "SH.XPD.OOPC.CH.ZS": ("Out-of-pocket share of health spending", "%", False),
    "SH.XPD.GHED.CH.ZS": ("Government share of health spending", "%", True),
    "SH.MED.PHYS.ZS": ("Physicians per 1,000 people", "per 1,000", True),
    "SH.UHC.SRVS.CV.XD": ("UHC service coverage index", "index 0-100", True),
    "SP.DYN.LE00.IN": ("Life expectancy at birth", "years", True),
}

START_YEAR = 2000
API = "https://api.worldbank.org/v2"
