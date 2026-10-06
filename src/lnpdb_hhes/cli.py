"""CPU-only command-line entry point."""

import argparse
import json
import sys
from urllib.error import URLError
from .data import DataError, fetch_snapshot, load_snapshot
from .benchmark import run_benchmark
from .candidates import run_candidates, evaluate_curated
from .lab import write_template, assess_file


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit published LiON predictions and curate formulation comparisons.")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="Download four pinned, checksum-verified public CSV files.")
    fetch.add_argument("--data-dir", default="data/raw/single_split")
    fetch.add_argument("--refresh", action="store_true")
    for name, help_text in [("benchmark", "Recalculate metrics for published predictions."),
                            ("candidates", "Find unreviewed formulation-comparison candidates."),
                            ("evaluate-curated", "Evaluate groups explicitly included after source review.")]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--data-dir", default="data/raw/single_split")
        p.add_argument("--out", default=f"outputs/{name}")
        if name == "benchmark":
            p.add_argument("--no-figures", action="store_true")
        elif name == "candidates":
            p.add_argument("--vary", choices=["all", "helper-cholesterol"], default="all")
        else:
            p.add_argument("--curation", required=True)
            p.add_argument("--observed-tie-tolerance", type=float, default=0.0)
            p.add_argument("--predicted-tie-tolerance", type=float, default=0.0)
    template = sub.add_parser("lab-template", help="Create a blank local lab metadata template.")
    template.add_argument("--out", default="data/private/formulations.csv")
    lab = sub.add_parser("assess-lab", help="Check lab metadata; does not predict efficacy.")
    lab.add_argument("--input", required=True)
    lab.add_argument("--out", default="outputs/lab/metadata_review.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            result = fetch_snapshot(args.data_dir, args.refresh)
        elif args.command == "lab-template":
            result = write_template(args.out)
        elif args.command == "assess-lab":
            result = assess_file(args.input, args.out)
        else:
            snapshot = load_snapshot(args.data_dir)
            if args.command == "benchmark":
                result = run_benchmark(snapshot, args.out, not args.no_figures)
            elif args.command == "candidates":
                result = run_candidates(snapshot, args.out, args.vary)
            else:
                result = evaluate_curated(snapshot, args.curation, args.out,
                                          args.observed_tie_tolerance, args.predicted_tie_tolerance)
        print(json.dumps(result, indent=2, allow_nan=False))
        if args.command == "assess-lab" and any(row["errors"] for row in result["rows"]):
            return 2
        return 0
    except (DataError, OSError, URLError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
