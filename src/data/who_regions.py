"""ISO3 country code -> WHO region mapping.

Regions follow the six WHO regional offices:
  AFR  African Region
  AMR  Region of the Americas
  SEAR South-East Asia Region
  EUR  European Region
  EMR  Eastern Mediterranean Region
  WPR  Western Pacific Region
"""

ISO3_TO_WHO_REGION = {
    # African Region (AFR)
    "DZA": "AFR", "AGO": "AFR", "BEN": "AFR", "BWA": "AFR", "BFA": "AFR",
    "BDI": "AFR", "CPV": "AFR", "CMR": "AFR", "CAF": "AFR", "TCD": "AFR",
    "COM": "AFR", "COG": "AFR", "COD": "AFR", "CIV": "AFR", "GNQ": "AFR",
    "ERI": "AFR", "SWZ": "AFR", "ETH": "AFR", "GAB": "AFR", "GMB": "AFR",
    "GHA": "AFR", "GIN": "AFR", "GNB": "AFR", "KEN": "AFR", "LSO": "AFR",
    "LBR": "AFR", "MDG": "AFR", "MWI": "AFR", "MLI": "AFR", "MRT": "AFR",
    "MUS": "AFR", "MOZ": "AFR", "NAM": "AFR", "NER": "AFR", "NGA": "AFR",
    "RWA": "AFR", "STP": "AFR", "SEN": "AFR", "SYC": "AFR", "SLE": "AFR",
    "ZAF": "AFR", "SSD": "AFR", "TGO": "AFR", "UGA": "AFR", "TZA": "AFR",
    "ZMB": "AFR", "ZWE": "AFR",

    # Region of the Americas (AMR)
    "ATG": "AMR", "ARG": "AMR", "BHS": "AMR", "BRB": "AMR", "BLZ": "AMR",
    "BOL": "AMR", "BRA": "AMR", "CAN": "AMR", "CHL": "AMR", "COL": "AMR",
    "CRI": "AMR", "CUB": "AMR", "DMA": "AMR", "DOM": "AMR", "ECU": "AMR",
    "SLV": "AMR", "GRD": "AMR", "GTM": "AMR", "GUY": "AMR", "HTI": "AMR",
    "HND": "AMR", "JAM": "AMR", "MEX": "AMR", "NIC": "AMR", "PAN": "AMR",
    "PRY": "AMR", "PER": "AMR", "KNA": "AMR", "LCA": "AMR", "VCT": "AMR",
    "SUR": "AMR", "TTO": "AMR", "USA": "AMR", "URY": "AMR", "VEN": "AMR",

    # South-East Asia Region (SEAR)
    "BGD": "SEAR", "BTN": "SEAR", "PRK": "SEAR", "IND": "SEAR", "IDN": "SEAR",
    "MDV": "SEAR", "MMR": "SEAR", "NPL": "SEAR", "LKA": "SEAR", "THA": "SEAR",
    "TLS": "SEAR",

    # European Region (EUR)
    "ALB": "EUR", "AND": "EUR", "ARM": "EUR", "AUT": "EUR", "AZE": "EUR",
    "BLR": "EUR", "BEL": "EUR", "BIH": "EUR", "BGR": "EUR", "HRV": "EUR",
    "CYP": "EUR", "CZE": "EUR", "DNK": "EUR", "EST": "EUR", "FIN": "EUR",
    "FRA": "EUR", "GEO": "EUR", "DEU": "EUR", "GRC": "EUR", "HUN": "EUR",
    "ISL": "EUR", "IRL": "EUR", "ISR": "EUR", "ITA": "EUR", "KAZ": "EUR",
    "KGZ": "EUR", "LVA": "EUR", "LTU": "EUR", "LUX": "EUR", "MLT": "EUR",
    "MCO": "EUR", "MNE": "EUR", "NLD": "EUR", "MKD": "EUR", "NOR": "EUR",
    "POL": "EUR", "PRT": "EUR", "MDA": "EUR", "ROU": "EUR", "RUS": "EUR",
    "SMR": "EUR", "SRB": "EUR", "SVK": "EUR", "SVN": "EUR", "ESP": "EUR",
    "SWE": "EUR", "CHE": "EUR", "TJK": "EUR", "TUR": "EUR", "TKM": "EUR",
    "UKR": "EUR", "GBR": "EUR", "UZB": "EUR",

    # Eastern Mediterranean Region (EMR)
    "AFG": "EMR", "BHR": "EMR", "DJI": "EMR", "EGY": "EMR", "IRN": "EMR",
    "IRQ": "EMR", "JOR": "EMR", "KWT": "EMR", "LBN": "EMR", "LBY": "EMR",
    "MAR": "EMR", "OMN": "EMR", "PAK": "EMR", "QAT": "EMR", "SAU": "EMR",
    "SOM": "EMR", "SDN": "EMR", "SYR": "EMR", "TUN": "EMR", "ARE": "EMR",
    "YEM": "EMR", "PSE": "EMR",

    # Western Pacific Region (WPR)
    "AUS": "WPR", "BRN": "WPR", "KHM": "WPR", "CHN": "WPR", "COK": "WPR",
    "FJI": "WPR", "JPN": "WPR", "KIR": "WPR", "LAO": "WPR", "MYS": "WPR",
    "MHL": "WPR", "FSM": "WPR", "MNG": "WPR", "NRU": "WPR", "NZL": "WPR",
    "NIU": "WPR", "PLW": "WPR", "PNG": "WPR", "PHL": "WPR", "KOR": "WPR",
    "WSM": "WPR", "SGP": "WPR", "SLB": "WPR", "TON": "WPR", "TUV": "WPR",
    "VUT": "WPR", "VNM": "WPR",
}


def get_region(iso3: str) -> str:
    """Return the WHO region for an ISO3 code, or 'OTHER' if unmapped."""
    return ISO3_TO_WHO_REGION.get(iso3, "OTHER")
