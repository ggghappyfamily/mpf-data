#!/usr/bin/env python3
"""
每日自動更新恒指 PE 數據
- 來源：億牛網 https://eniu.com/gu/hkhsi
- API：  https://eniu.com/chart/peindex/hkhsi/t/all
- 輸出：hsi_pe.csv（每日 PE，2000-12 起）
       hsi_pe_monthly.txt（每月最後交易日 PE，每行一個）
"""

import csv
import requests

API_URL = "https://eniu.com/chart/peindex/hkhsi/t/all"
START_DATE = "2000-12-01"


def main():
    r = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    data = r.json()

    # 過濾 2000-12 起嘅每日數據，並將 PE 轉做 float
    records = []
    for i, date in enumerate(data["date"]):
        if date >= START_DATE:
            records.append({"date": date, "pe": float(data["pe"][i])})

    # 寫入 CSV
    with open("hsi_pe.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "pe"])
        for rec in records:
            writer.writerow([rec["date"], rec["pe"]])

    # 寫入月度 txt：每月最後一筆記錄嘅 PE
    monthly = {}
    for rec in records:
        monthly[rec["date"][:7]] = rec["pe"]  # 以 YYYY-MM 為 key，最後一筆覆蓋

    with open("hsi_pe_monthly.txt", "w") as f:
        for ym in sorted(monthly.keys()):
            f.write(f"{monthly[ym]:.2f}\n")

    print(f"Updated {len(records)} daily records, {len(monthly)} monthly values")


if __name__ == "__main__":
    main()
