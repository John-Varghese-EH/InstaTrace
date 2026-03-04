"""
InstaTrace Export Module — JSON, CSV, TXT report generation.
Author: John-Varghese-EH
"""

import json
import csv
import os
import datetime
from ..config import C, print_status


def export_data(data, filename, fmt="json", label="data"):
    """
    Export data to a file in the specified format.

    Args:
        data:     Data to export (dict or list).
        filename: Output filename (without extension).
        fmt:      Format — 'json', 'csv', or 'txt'.
        label:    Label for the data type.

    Returns:
        str: Path to the created file.
    """
    os.makedirs("instatrace_reports", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = f"instatrace_reports/{filename}_{ts}"

    if fmt == "json":
        path = basename + ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    elif fmt == "csv":
        path = basename + ".csv"
        if isinstance(data, list) and data:
            keys = list(data[0].keys()) if isinstance(data[0], dict) else ["value"]
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                for row in data:
                    if isinstance(row, dict):
                        writer.writerow({k: str(v) for k, v in row.items()})
                    else:
                        writer.writerow({"value": str(row)})
        elif isinstance(data, dict):
            path = basename + ".csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Field", "Value"])
                for k, v in _flatten_dict(data).items():
                    writer.writerow([k, str(v) if v is not None else ""])
        else:
            path = basename + ".txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))

    elif fmt == "txt":
        path = basename + ".txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"InstaTrace Report — {label}\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            if isinstance(data, dict):
                for k, v in _flatten_dict(data).items():
                    f.write(f"{k:<35}: {v}\n")
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    f.write(f"\n--- #{i} ---\n")
                    if isinstance(item, dict):
                        for k, v in item.items():
                            f.write(f"  {k:<30}: {v}\n")
                    else:
                        f.write(f"  {item}\n")
            else:
                f.write(str(data))
    else:
        print_status(f"Unknown format: {fmt}", "error")
        return None

    print_status(f"Exported {label} → {path}", "success")
    return path


def _flatten_dict(d, parent_key="", sep="."):
    """Flatten nested dict keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            items.append((new_key, ", ".join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)
