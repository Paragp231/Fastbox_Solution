"""
FastBox Delivery System Simulator
Python Assignment 2026

Simulates one day of delivery operations:
  - Reads a JSON input (data.json or any path passed as argument)
  - Assigns each package to the nearest agent (agent → warehouse Euclidean distance)
  - Simulates pickup + delivery, computing total distance per agent
  - Generates a report.json with per-agent stats and the best (most efficient) agent

Bonus features implemented:
  - Random delivery delays
  - ASCII route visualisation
  - Export top performer to top_performer.csv
"""

import json
import math
import csv
import random
import sys
import os


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def euclidean(a, b):
    """Return Euclidean distance between two [x, y] points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# ──────────────────────────────────────────────
# JSON Parsing  (handles both dict and list formats)
# ──────────────────────────────────────────────

def parse_input(path):
    """
    Read and normalise the input JSON.

    Supports two warehouse/agent formats found in the test cases:
      • dict  → {"W1": [x, y], ...}
      • list  → [{"id": "W1", "location": [x, y]}, ...]

    Returns three plain dicts:
      warehouses: {id: [x, y]}
      agents:     {id: [x, y]}
      packages:   [{id, warehouse_id, destination}]
    """
    with open(path, "r") as f:
        raw = json.load(f)

    # --- warehouses ---
    wh_raw = raw["warehouses"]
    if isinstance(wh_raw, dict):
        warehouses = {k: v for k, v in wh_raw.items()}
    else:  # list of objects
        warehouses = {w["id"]: w.get("location", w.get("coords", w.get("loc"))) for w in wh_raw}

    # --- agents ---
    ag_raw = raw["agents"]
    if isinstance(ag_raw, dict):
        agents = {k: v for k, v in ag_raw.items()}
    else:
        agents = {a["id"]: a.get("location", a.get("coords", a.get("loc"))) for a in ag_raw}

    # --- packages ---
    packages = []
    for p in raw["packages"]:
        packages.append({
            "id": p["id"],
            # test cases use either "warehouse" or "warehouse_id"
            "warehouse_id": p.get("warehouse_id", p.get("warehouse")),
            "destination": p["destination"],
        })

    return warehouses, agents, packages


# ──────────────────────────────────────────────
# Core Logic
# ──────────────────────────────────────────────

def assign_packages(packages, agents, warehouses):
    """
    For each package, find the agent whose current location is closest
    to the package's warehouse.  Ties broken by agent id (alphabetical).

    Returns a dict: {agent_id: [package, ...]}
    """
    assignment = {aid: [] for aid in agents}

    for pkg in packages:
        wh_id = pkg["warehouse_id"]
        wh_loc = warehouses[wh_id]

        # Distance from each agent to this package's warehouse
        best_agent = min(
            agents.keys(),
            key=lambda aid: (euclidean(agents[aid], wh_loc), aid)
        )
        assignment[best_agent].append(pkg)

    return assignment


def simulate_deliveries(assignment, agents, warehouses, random_delays=True):
    """
    Each agent travels:
        current_pos → warehouse → destination   (for every assigned package)

    The agent's position updates after each delivery so multi-package
    routes chain realistically.

    Returns a dict:
      {agent_id: {"packages_delivered": int, "total_distance": float,
                  "efficiency": float, "route": [(label, [x,y]), ...]}}
    """
    results = {}

    for aid, pkgs in assignment.items():
        pos = list(agents[aid])       # mutable copy
        total_dist = 0.0
        route = [("START", list(pos))]

        for pkg in pkgs:
            wh_loc = warehouses[pkg["warehouse_id"]]
            dest   = pkg["destination"]

            # Agent → warehouse
            d1 = euclidean(pos, wh_loc)
            total_dist += d1
            pos = list(wh_loc)
            route.append((f"Pickup {pkg['id']} @ {pkg['warehouse_id']}", list(pos)))

            # Optional random delay (adds 0–5 distance units of "idle time")
            if random_delays:
                delay = random.uniform(0, 5)
                total_dist += delay

            # Warehouse → destination
            d2 = euclidean(pos, dest)
            total_dist += d2
            pos = list(dest)
            route.append((f"Delivered {pkg['id']}", list(pos)))

        n = len(pkgs)
        # Efficiency = average distance per package (lower is better);
        # if no packages assigned, efficiency is 0.
        efficiency = round(total_dist / n, 2) if n > 0 else 0.0

        results[aid] = {
            "packages_delivered": n,
            "total_distance": round(total_dist, 2),
            "efficiency": efficiency,
            "route": route,
        }

    return results


def build_report(results):
    """
    Build the final report dict.
    best_agent = agent with lowest efficiency score (least distance per package)
    among agents who delivered at least one package.
    """
    report = {}
    for aid, data in results.items():
        report[aid] = {
            "packages_delivered": data["packages_delivered"],
            "total_distance": data["total_distance"],
            "efficiency": data["efficiency"],
        }

    # Best agent: lowest efficiency among those with deliveries
    active = {aid: d for aid, d in results.items() if d["packages_delivered"] > 0}
    if active:
        best = min(active, key=lambda aid: active[aid]["efficiency"])
    else:
        best = None

    report["best_agent"] = best
    return report


# ──────────────────────────────────────────────
# Bonus: ASCII Visualisation
# ──────────────────────────────────────────────

def ascii_map(warehouses, agents, packages, assignment, grid_size=20):
    """
    Render a rough ASCII grid showing warehouses (W), agents (A),
    and package destinations (P) scaled to grid_size×grid_size.
    """
    all_points = (
        list(warehouses.values()) +
        list(agents.values()) +
        [p["destination"] for p in packages]
    )
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    def scale(pt):
        sx = int((pt[0] - min_x) / max(max_x - min_x, 1) * (grid_size - 1))
        sy = int((pt[1] - min_y) / max(max_y - min_y, 1) * (grid_size - 1))
        return sx, sy

    grid = [["." for _ in range(grid_size)] for _ in range(grid_size)]

    for wid, loc in warehouses.items():
        x, y = scale(loc)
        grid[grid_size - 1 - y][x] = "W"

    for aid, loc in agents.items():
        x, y = scale(loc)
        grid[grid_size - 1 - y][x] = "A"

    for pkg in packages:
        x, y = scale(pkg["destination"])
        if grid[grid_size - 1 - y][x] == ".":
            grid[grid_size - 1 - y][x] = "P"

    lines = ["FastBox Route Map (W=Warehouse, A=Agent, P=Destination)"]
    lines.append("+" + "-" * grid_size + "+")
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + "-" * grid_size + "+")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# Bonus: Export top performer to CSV
# ──────────────────────────────────────────────

def export_top_performer(report, results, out_path="top_performer.csv"):
    best = report.get("best_agent")
    if not best:
        return
    data = report[best]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "agent_id", "packages_delivered", "total_distance", "efficiency"
        ])
        writer.writeheader()
        writer.writerow({
            "agent_id": best,
            "packages_delivered": data["packages_delivered"],
            "total_distance": data["total_distance"],
            "efficiency": data["efficiency"],
        })
    print(f"Top performer exported → {out_path}")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

def run(input_path, report_path="report.json", enable_delays=True, verbose=True):
    """Full pipeline: parse → assign → simulate → report → save."""

    # 1. Parse input
    warehouses, agents, packages = parse_input(input_path)
    if verbose:
        print(f"\n{'='*50}")
        print(f"Input: {input_path}")
        print(f"  Warehouses : {len(warehouses)}")
        print(f"  Agents     : {len(agents)}")
        print(f"  Packages   : {len(packages)}")

    # 2. Assign packages to nearest agent
    assignment = assign_packages(packages, agents, warehouses)
    if verbose:
        print("\nPackage Assignment:")
        for aid, pkgs in assignment.items():
            ids = [p["id"] for p in pkgs]
            print(f"  {aid} → {ids if ids else '(no packages)'}")

    # 3. Simulate deliveries
    results = simulate_deliveries(assignment, agents, warehouses,
                                  random_delays=enable_delays)

    # 4. Build report
    report = build_report(results)

    # 5. Save report
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    if verbose:
        print(f"\nReport saved → {report_path}")
        print(json.dumps(report, indent=2))

    # 6. ASCII map
    if verbose:
        print("\n" + ascii_map(warehouses, agents, packages, assignment))

    # 7. Export top performer CSV
    export_top_performer(report, results,
                         out_path=report_path.replace(".json", "_top.csv"))

    return report


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Default: base_case.json  →  report.json
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "report.json"

    if not os.path.exists(input_file):
        print(f"Error: input file '{input_file}' not found.")
        sys.exit(1)

    random.seed(42)   # reproducible delays for testing
    run(input_file, output_file)
