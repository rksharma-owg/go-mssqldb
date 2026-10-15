"""Fork validation only: apply the upstream 15% gate with metric direction."""
import json
import re
import sys


def regressions(report):
    metric = None
    parsed = 0
    result = []
    for line in report.splitlines():
        header = re.search(r"│\s*(sec/op|B/s|B/op|allocs/op)\s*│", line)
        if header:
            metric = header[1]
            continue
        is_row = bool(re.search(r"^\S+-\d+\s+.*\(p=", line))
        if not is_row:
            continue
        if not metric:
            raise ValueError("Benchmark row has no supported metric section")
        if "~" in line:
            parsed += 1
            continue
        match = re.search(r"^([^\s│]+).*?([+-][0-9]+(?:\.[0-9]+)?)%\s+\(p=([0-9.]+)", line)
        if not match:
            raise ValueError("Unrecognized benchmark comparison row: " + line)
        parsed += 1
        name, delta, pvalue = match[1], float(match[2]), float(match[3])
        # Preserve the upstream exclusion for this high-variance microbenchmark.
        if name.startswith("TdsBuffer_Write_Large-"):
            continue
        regression = -delta if metric == "B/s" else delta
        if regression >= 15:
            result.append({"name": name, "metric": metric, "delta_percent": delta,
                           "p": pvalue, "line": line})
    if not re.search(r"│\s*(sec/op|B/s|B/op|allocs/op)\s*│", report):
        raise ValueError("No supported benchmark metric sections found")
    # A stable comparison can legitimately contain only '~' rows.
    if not parsed and not re.search(r"\S+-\d+\s+.*~.*\(p=", report):
        raise ValueError("No comparison rows found")
    return result


if __name__ == "__main__":
    with open(sys.argv[1]) as source:
        rows = regressions(source.read())
    print(json.dumps(rows, indent=2))
    raise SystemExit(bool(rows))
