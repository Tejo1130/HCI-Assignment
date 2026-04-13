import json
import time
import importlib
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(__file__))

import makemytrip_selenium as mmt_module
import goibibo_selenium    as gib_module

def run_all():
    print("\n" + "═" * 64)
    print("  HCI ASSIGNMENT – PART A  |  WEB AUTOMATION COMPARISON")
    print("  Task: HYD → DEL, 15 June 2026, 1 Adult, Economy, Cheapest")
    print("═" * 64)

    results = []

    print("\n[1/2]  Running MakeMyTrip …\n")
    try:
        mmt_result = mmt_module.run_makemytrip()
        mmt_module.print_report(mmt_result)
        results.append(mmt_result)
    except Exception as e:
        print(f"  ERROR during MakeMyTrip run: {e}")
        mmt_result = mmt_module.TaskResult(error=str(e))
        results.append(mmt_result)

    print("\n[2/2]  Running Goibibo …\n")
    try:
        gib_result = gib_module.run_goibibo()
        gib_module.print_report(gib_result)
        results.append(gib_result)
    except Exception as e:
        print(f"  ERROR during Goibibo run: {e}")
        gib_result = gib_module.TaskResult(error=str(e))
        results.append(gib_result)

    print("\n" + "═" * 64)
    print("  COMPARISON SUMMARY  |  Web Implementations")
    print("═" * 64)
    print(f"  {'Metric':<30}  {'MakeMyTrip':>15}  {'Goibibo':>15}")
    print(f"  {'─'*30}  {'─'*15}  {'─'*15}")
    print(f"  {'Total Steps':<30}  {mmt_result.total_steps:>15}  {gib_result.total_steps:>15}")
    print(f"  {'Total Time (s)':<30}  {mmt_result.total_time_s:>15.1f}  {gib_result.total_time_s:>15.1f}")
    print(f"  {'Interruptions':<30}  {len(mmt_result.interruptions):>15}  {len(gib_result.interruptions):>15}")
    print(f"  {'Cheapest Fare':<30}  {(mmt_result.cheapest_flight or 'N/A')[:15]:>15}  "
          f"{(gib_result.cheapest_flight or 'N/A')[:15]:>15}")

    same_flight = (
        mmt_result.cheapest_flight is not None
        and gib_result.cheapest_flight is not None
        and mmt_result.cheapest_flight == gib_result.cheapest_flight
    )
    print(f"\n  Same cheapest flight on both platforms: {'YES' if same_flight else 'NO / UNKNOWN'}")
    print("═" * 64)

    output = {
        "run_timestamp": datetime.now().isoformat(),
        "task": {
            "origin": "Hyderabad (HYD)",
            "destination": "Delhi (DEL)",
            "date": "15 June 2026",
            "adults": 1,
            "class": "Economy",
        },
        "results": [
            {
                "platform": r.platform,
                "interface": r.interface,
                "total_steps": r.total_steps,
                "total_time_s": r.total_time_s,
                "interruptions": r.interruptions,
                "cheapest_flight": r.cheapest_flight,
                "error": r.error,
                "steps": [
                    {
                        "index": s.index,
                        "description": s.description,
                        "cumulative_s": s.cumulative_s,
                        "note": s.note,
                    }
                    for s in r.steps
                ],
            }
            for r in results
        ],
    }

    out_path = os.path.join(os.path.dirname(__file__), "web_comparison_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    run_all()