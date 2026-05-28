# FastBox Delivery System – Solution

## Files
- `delivery_system.py`  — Main solution (all tasks + bonus)
- `base_case.json`      — Base input from the assignment PDF
- `reports/`            — Pre-generated reports for base case + 10 test cases
- `test_cases/`         — All 10 test case JSON inputs

## How to Run

```bash
# Base case
python3 delivery_system.py base_case.json report.json

# Any test case
python3 delivery_system.py test_cases/test_case_1.json report.json
```

## Features Implemented

### Required Tasks (100%)
1. ✅ JSON parsing – handles both dict and list warehouse/agent formats
2. ✅ Euclidean nearest-agent assignment
3. ✅ Delivery simulation – agent → warehouse → destination, chained routes
4. ✅ Report generation with packages_delivered, total_distance, efficiency, best_agent
5. ✅ Saves report to report.json

### Bonus (all 3 implemented)
- ✅ Random delivery delays (seeded for reproducibility)
- ✅ ASCII route visualisation printed to console
- ✅ Top performer exported to `<report>_top.csv`

## Evaluation Criteria Coverage
| Criteria              | Weight | Implementation |
|-----------------------|--------|----------------|
| JSON parsing          | 10%    | `parse_input()` – handles 2 formats |
| Distance calculation  | 20%    | `euclidean()` – standard formula |
| Agent-package assign  | 25%    | `assign_packages()` – min dist to warehouse |
| Simulation & report   | 25%    | `simulate_deliveries()` + `build_report()` |
| Code clarity          | 10%    | Docstrings + inline comments throughout |
| Bonus creativity      | 10%    | Delays, ASCII map, CSV export |
