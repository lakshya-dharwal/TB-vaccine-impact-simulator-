"""Download the optional OWID covariate datasets for TB Futures.

The TB target, population, region, and income level all come from
data/raw/who_tb_data_merged.csv (tracked in the repository). Everything below is
OPTIONAL: each covariate is merged in by process_data.py only if its file ends
up in data/raw/. If a download fails (e.g. behind a network egress allowlist),
the exact URL is printed so it can be fetched manually and dropped into
data/raw/. The pipeline simply skips any covariate whose file is absent.
"""

import os

import requests

os.makedirs("data/raw", exist_ok=True)

bcg_url = "https://ourworldindata.org/grapher/bcg-immunization-coverage-for-tb-among-1-year-olds.csv?v=1&csvType=full&useColumnShortNames=true"
hiv_url = "https://ourworldindata.org/grapher/share-of-population-with-hiv.csv?v=1&csvType=full&useColumnShortNames=true"
gdp_url = "https://ourworldindata.org/grapher/gdp-per-capita-worldbank.csv?v=1&csvType=full&useColumnShortNames=true"
health_url = "https://ourworldindata.org/grapher/health-expenditure-and-financing.csv?v=1&csvType=full&useColumnShortNames=true"

urls = {
    "bcg_coverage.csv": bcg_url,
    "hiv_prevalence.csv": hiv_url,
    "gdp_per_capita.csv": gdp_url,
    "health_expenditure.csv": health_url,
}

headers = {"User-Agent": "Mozilla/5.0"}


def main():
    failures = []
    for filename, url in urls.items():
        print(f"Downloading {filename}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            print(f"FAILED {filename} — {exc}")
            failures.append((filename, url))
            continue
        if response.status_code == 200:
            with open(f"data/raw/{filename}", "wb") as f:
                f.write(response.content)
            print(f"Saved {filename}")
        else:
            print(f"FAILED {filename} — status {response.status_code}")
            failures.append((filename, url))

    if failures:
        print("\n" + "=" * 70)
        print("Some downloads failed. Download each URL below in a browser and save")
        print("it with the given name into data/raw/. Any covariate you skip is simply")
        print("left out of the model — that is fine.\n")
        for filename, url in failures:
            print(f"  {filename}\n    {url}\n")
        print("If sandboxed, add 'ourworldindata.org' to your network egress allowlist.")
        print("=" * 70)
    else:
        print("\nAll optional covariate datasets downloaded into data/raw/.")


if __name__ == "__main__":
    main()
