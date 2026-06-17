"""(Optional) refresh the OWID source datasets used by TB Futures.

The source data is already committed under data/, so this script is only needed to
refresh it from Our World in Data. It writes the five OWID grapher CSVs into data/
using the same filenames process_data.py expects. The WHO notifications file
(who_tb_data_merged.csv) is maintained separately in the repo.

If a download fails (e.g. behind a network egress allowlist), the exact URL is
printed so it can be fetched manually.
"""

import os

import requests

os.makedirs("data", exist_ok=True)

BASE = "https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"
SLUGS = [
    "incidence-of-tuberculosis-sdgs",
    "bcg-immunization-coverage-for-tb-among-1-year-olds",
    "gdp-per-capita-worldbank",
    "population",
    "sites-providing-rapid-tuberculosis-diagnostics-per-million-people",
]

headers = {"User-Agent": "Mozilla/5.0"}


def main():
    failures = []
    for slug in SLUGS:
        url = BASE.format(slug=slug)
        dest = f"data/{slug}.csv"
        print(f"Downloading {slug}.csv ...")
        try:
            r = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            print(f"FAILED {slug} — {exc}")
            failures.append((dest, url))
            continue
        if r.status_code == 200:
            with open(dest, "wb") as f:
                f.write(r.content)
            print(f"Saved {dest}")
        else:
            print(f"FAILED {slug} — status {r.status_code}")
            failures.append((dest, url))

    if failures:
        print("\n" + "=" * 70)
        print("Some downloads failed. Fetch each URL in a browser and save to the path:")
        for dest, url in failures:
            print(f"  {dest}\n    {url}\n")
        print("If sandboxed, add 'ourworldindata.org' to your network egress allowlist.")
        print("=" * 70)
    else:
        print("\nAll source datasets refreshed into data/.")


if __name__ == "__main__":
    main()
