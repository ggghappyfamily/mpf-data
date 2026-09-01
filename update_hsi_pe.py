#!/usr/bin/env python3
"""
每日自動更新恒指 PE 數據（for GitHub Actions）
- 來源：億牛網 https://eniu.com/gu/hkhsi
- API：  https://eniu.com/chart/peindex/hkhsi/t/all
- 輸出：hsi_pe.csv（每日 PE，2000-12 起）
       hsi_pe_monthly.txt（每月最後交易日 PE，每行一個）
       hsi_pe_weekly.txt（每週最後交易日 PE，每行一個）
       pe_array_for_pine.txt（Pine Script 週度 array 區塊，直接複製貼上）
       latest_pe_override.txt（本週最新 PE，可填入 Pine Script「當前 PE 覆蓋」）
"""

import csv
import requests
from datetime import datetime, timedelta

API_URL = "https://eniu.com/chart/peindex/hkhsi/t/all"
START_DATE = "2000-12-01"
VALUES_PER_LINE = 10


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


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
    with open("hsi_pe.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "pe"])
        for rec in records:
            writer.writerow([rec["date"], rec["pe"]])

    # 寫入月度 txt：每月最後一筆記錄嘅 PE
    monthly = {}
    for rec in records:
        monthly[rec["date"][:7]] = rec["pe"]  # 以 YYYY-MM 為 key，最後一筆覆蓋

    with open("hsi_pe_monthly.txt", "w", encoding="utf-8") as f:
        for ym in sorted(monthly.keys()):
            f.write(f"{monthly[ym]:.2f}\n")

    # 寫入週度 txt：每個曆法星期五（冇交易日就 forward-fill 最近一個交易日 PE）；只包含已完整收市嘅週
    latest_date = parse_date(records[-1]["date"])
    last_complete_friday = latest_date - timedelta(days=(latest_date.weekday() - 4) % 7)

    start_dt = parse_date(START_DATE)
    days_to_friday = (4 - start_dt.weekday()) % 7
    first_friday = start_dt + timedelta(days=days_to_friday)

    weekly_dates = []
    weekly_values = []
    current_friday = first_friday
    rec_idx = 0
    n = len(records)

    while current_friday <= last_complete_friday:
        # 搵最後一個交易日 <= 當前星期五
        while rec_idx < n and parse_date(records[rec_idx]["date"]) <= current_friday:
            rec_idx += 1
        weekly_values.append(records[rec_idx - 1]["pe"])
        weekly_dates.append(current_friday.strftime("%Y-%m-%d"))
        current_friday += timedelta(days=7)

    with open("hsi_pe_weekly.txt", "w", encoding="utf-8") as f:
        for v in weekly_values:
            f.write(f"{v:.2f}\n")

    # 生成 Pine Script 週度 array
    pine_lines = [
        "// ===== 恒指 PE 週度數據 =====",
        "// 數據源：億牛網口徑，每週最後交易日嘅 PE",
        f"// 起點：{weekly_dates[0]}（對應週五收市），Pine Script 以該週週一 timestamp 作為 array 基準",
        "// 更新：每週自動生成，去 https://github.com/ggghappyfamily/mpf-data 攞 pe_array_for_pine.txt，複製貼上取代下面區塊",
        f"var int   PE_START_TIME = timestamp(2000, 11, 27, 0, 0)  // {weekly_dates[0]} 嗰個禮拜嘅週一 UTC",
        "var int   MS_PER_WEEK   = 7 * 24 * 60 * 60 * 1000",
        "var float[] peData = array.from(",
    ]
    for i in range(0, len(weekly_values), VALUES_PER_LINE):
        chunk = weekly_values[i:i + VALUES_PER_LINE]
        formatted = ", ".join(f"{v:6.2f}" for v in chunk)
        if i + VALUES_PER_LINE >= len(weekly_values):
            pine_lines.append(f"    {formatted})")
        else:
            pine_lines.append(f"    {formatted},")

    with open("pe_array_for_pine.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(pine_lines) + "\n")

    # 最新 PE override
    with open("latest_pe_override.txt", "w", encoding="utf-8") as f:
        f.write(f"{weekly_values[-1]:.2f}\n")

    print(
        f"Updated {len(records)} daily records, "
        f"{len(monthly)} monthly values, "
        f"{len(weekly_values)} weekly values, "
        f"latest weekly PE = {weekly_values[-1]:.2f}"
    )


if __name__ == "__main__":
    main()
