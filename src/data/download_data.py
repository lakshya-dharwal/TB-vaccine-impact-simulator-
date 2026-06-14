"""Download the OWID source datasets for TB Futures.

TB notifications, population, region, and income level all come from
data/raw/who_tb_data_merged.csv (tracked in the repository). The only two
datasets fetched here are BCG coverage and HIV prevalence from Our World in
Data. If a download fails, the exact URL is printed so it can be fetched
manually and dropped into data/raw/.
"""

import os

import requests

os.makedirs("data/raw", exist_ok=True)

# Our World in Data — BCG coverage by country by year
bcg_url = "https://ourworldindata.org/grapher/bcg-immunization-coverage.csv?v=1&csvType=full&useColumnShortNames=true"
# Our World in Data — HIV prevalence by country by year
hiv_url = "https://ourworldindata.org/grapher/share-of-population-with-hiv.csv?v=1&csvType=full&useColumnShortNames=true"

urls = {
    "bcg_coverage.csv": bcg_url,
    "hiv_prevalence.csv": hiv_url,
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
        print("the file with the given name into the data/raw/ folder:\n")
        for filename, url in failures:
            print(f"  {filename}\n    {url}\n")
        print("If you are running in a sandboxed environment, add")
        print("'ourworldindata.org' to your network egress allowlist and re-run.")
        print("=" * 70)
    else:
        print("\nAll datasets downloaded successfully into data/raw/.")


if __name__ == "__main__":
    main()
