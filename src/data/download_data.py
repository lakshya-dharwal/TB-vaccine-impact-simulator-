"""Download the tracked OWID datasets used by TB Futures."""

import os

import requests

os.makedirs("data", exist_ok=True)

URLS = {
    "incidence-of-tuberculosis-sdgs.csv": "https://ourworldindata.org/grapher/incidence-of-tuberculosis-sdgs.csv?v=1&csvType=full&useColumnShortNames=false",
    "bcg-immunization-coverage-for-tb-among-1-year-olds.csv": "https://ourworldindata.org/grapher/bcg-immunization-coverage-for-tb-among-1-year-olds.csv?v=1&csvType=full&useColumnShortNames=false",
    "gdp-per-capita-worldbank.csv": "https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?v=1&csvType=full&useColumnShortNames=false",
    "population.csv": "https://ourworldindata.org/grapher/population.csv?v=1&csvType=full&useColumnShortNames=false",
    "sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv": "https://ourworldindata.org/grapher/sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv?v=1&csvType=full&useColumnShortNames=false",
}

HEADERS = {"User-Agent": "Mozilla/5.0"}


def main():
    failures = []
    for filename, url in URLS.items():
        print(f"Downloading {filename}...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException as exc:
            print(f"FAILED {filename} — {exc}")
            failures.append((filename, url))
            continue
        if response.status_code == 200:
            with open(os.path.join("data", filename), "wb") as f:
                f.write(response.content)
            print(f"Saved {filename}")
        else:
            print(f"FAILED {filename} — status {response.status_code}")
            failures.append((filename, url))

    if failures:
        print("\n" + "=" * 70)
        print("Some downloads failed. Download each URL below in a browser and save")
        print("it with the given filename into data/.\n")
        for filename, url in failures:
            print(f"  {filename}\n    {url}\n")
        print("=" * 70)
    else:
        print("\nAll tracked OWID datasets downloaded into data/.")


if __name__ == "__main__":
    main()
