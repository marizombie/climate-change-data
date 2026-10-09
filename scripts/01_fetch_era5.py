"""Fetch ERA5 daily temperature for twelve southern European cities, 1950-2025.

Source: Open-Meteo archive API (free, no key required, ERA5 reanalysis).
Writes one JSON per city-chunk to data/era5/ so partial progress survives a
restart, then assembles data/era5_daily.parquet.

The API rate-limits on request weight, so the fetch is chunked into 25-year
windows with a pause between calls. Re-running skips chunks already on disk.

Usage:  python scripts/01_fetch_era5.py
"""
import json, os, time, urllib.parse, urllib.request, urllib.error

CITIES = {
    "Athens": (37.98, 23.73), "Thessaloniki": (40.64, 22.94),
    "Rome": (41.90, 12.50), "Naples": (40.85, 14.27), "Palermo": (38.12, 13.36),
    "Madrid": (40.42, -3.70), "Seville": (37.39, -5.98), "Cordoba": (37.89, -4.78),
    "Barcelona": (41.39, 2.17), "Lisbon": (38.72, -9.14),
    "Marseille": (43.30, 5.37), "Valletta": (35.90, 14.51),
}
CHUNKS = [("1950-01-01", "1974-12-31"), ("1975-01-01", "1999-12-31"),
          ("2000-01-01", "2025-12-31")]
OUT = os.path.join("data", "era5")
BASE = "https://archive-api.open-meteo.com/v1/archive"
PAUSE = 12          # seconds between calls; raise if you hit HTTP 429
RETRIES = 4


def fetch(lat, lon, start, end):
    url = BASE + "?" + urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
        "timezone": "UTC",
    })
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)["daily"]
        except Exception as exc:                       # noqa: BLE001
            wait = PAUSE * (attempt + 1)
            print(f"   retry {attempt + 1}/{RETRIES} after {wait}s ({exc})")
            time.sleep(wait)
    raise RuntimeError(f"failed after {RETRIES} attempts: {start}..{end}")


def main():
    os.makedirs(OUT, exist_ok=True)
    for city, (lat, lon) in CITIES.items():
        for i, (start, end) in enumerate(CHUNKS):
            path = os.path.join(OUT, f"{city}_{i}.json")
            if os.path.exists(path):
                continue
            print(f"fetching {city} {start[:4]}-{end[:4]}")
            with open(path, "w") as fh:
                json.dump(fetch(lat, lon, start, end), fh)
            time.sleep(PAUSE)

    import pandas as pd
    frames = []
    for city in CITIES:
        for i in range(len(CHUNKS)):
            df = pd.DataFrame(json.load(open(os.path.join(OUT, f"{city}_{i}.json"))))
            df["city"] = city
            frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["time"] = pd.to_datetime(out["time"])
    out = out.sort_values(["city", "time"]).drop_duplicates(["city", "time"])
    out.to_parquet(os.path.join("data", "era5_daily.parquet"))
    print(f"wrote data/era5_daily.parquet  {out.shape[0]:,} rows, "
          f"{out.city.nunique()} cities, {out.time.min().date()}..{out.time.max().date()}")


if __name__ == "__main__":
    main()
