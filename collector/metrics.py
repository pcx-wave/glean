#!/usr/bin/env python3
"""Aggregate friction density per model family across recent sessions.

Usage:
  python3 collector/metrics.py --days 7
  python3 collector/metrics.py --days 7 --dry-run
"""

import argparse
import csv
import os
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import scan_session


MODEL_FAMILIES = ['fable', 'opus', 'sonnet', 'haiku']


def _model_family(dominant_model: str) -> str:
    dm = dominant_model.lower()
    for family in MODEL_FAMILIES:
        if family in dm:
            return family
    return 'other'


def _friction_density(signals: dict) -> float:
    total = signals['tool_errors'] + signals['edit_loop'] + signals['corrections'] * 5
    lines = max(signals['line_count'], 1)
    return total * 1000 / lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Aggregate friction density per model family over a time window')
    parser.add_argument('--root', default=os.path.expanduser('~/.claude/projects'),
                        help='Root directory to scan for session logs')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to look back (default 7)')
    parser.add_argument('--min-size-kb', type=int, default=20,
                        help='Skip files smaller than this in KB (default 20)')
    parser.add_argument('--out', default=os.path.expanduser('~/glean/metrics/friction.csv'),
                        help='Output CSV path (default ~/glean/metrics/friction.csv)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print table only, do not write CSV')
    args = parser.parse_args()

    root = Path(args.root)
    cutoff = date.today() - timedelta(days=args.days)
    min_size = args.min_size_kb * 1024
    today_str = date.today().isoformat()

    # Collect JSONL files within the time window
    families = {}  # family -> list of dicts with density, lines, errors, corrections

    for jsonl_path in root.rglob('*.jsonl'):
        if not jsonl_path.is_file():
            continue
        size = jsonl_path.stat().st_size
        if size < min_size:
            continue
        mtime = jsonl_path.stat().st_mtime
        file_date = date.fromtimestamp(mtime)
        if file_date < cutoff:
            continue

        signals = scan_session(str(jsonl_path))
        dm = signals['dominant_model']
        if not dm:
            continue

        family = _model_family(dm)
        density = _friction_density(signals)
        families.setdefault(family, []).append({
            'density': density,
            'lines': signals['line_count'],
            'errors': signals['tool_errors'],
            'corrections': signals['corrections'],
        })

    if not families:
        print(f'No sessions found in the last {args.days} days.')
        sys.exit(0)

    # Compute aggregates per family
    aggregates = []
    for family, entries in sorted(families.items()):
        n = len(entries)
        total_lines = sum(e['lines'] for e in entries)
        densities = sorted(e['density'] for e in entries)
        mean_density = statistics.mean(densities)
        median_density = statistics.median(densities)
        p90_idx = int(0.9 * (n - 1))
        p90_density = densities[p90_idx]
        total_errors = sum(e['errors'] for e in entries)
        total_corrections = sum(e['corrections'] for e in entries)

        aggregates.append({
            'family': family,
            'sessions': n,
            'total_lines': total_lines,
            'mean_density': round(mean_density, 2),
            'median_density': round(median_density, 2),
            'p90_density': round(p90_density, 2),
            'tool_errors': total_errors,
            'corrections': total_corrections,
        })

    # Print window period
    print(f'Window: {cutoff.isoformat()} to {today_str}  ({args.days} days)')
    print()

    # Print human-readable table
    header = f'{"family":>12}  {"sessions":>8}  {"lines":>8}  {"mean_d":>8}  {"med_d":>8}  {"p90_d":>8}  {"errors":>8}  {"corr":>8}'
    print(header)
    print('-' * len(header))
    for a in aggregates:
        print(f'{a["family"]:>12}  {a["sessions"]:>8}  {a["total_lines"]:>8}  '
              f'{a["mean_density"]:>8}  {a["median_density"]:>8}  '
              f'{a["p90_density"]:>8}  {a["tool_errors"]:>8}  {a["corrections"]:>8}')
    print()

    if args.dry_run:
        print('Dry run — no CSV written.')
        sys.exit(0)

    # CSV handling
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'date', 'window_days', 'family', 'sessions', 'total_lines',
        'mean_density', 'median_density', 'p90_density', 'tool_errors',
        'corrections',
    ]

    # Read existing rows to determine which (date, family) pairs already exist
    existing_keys = set()
    if out_path.exists():
        with out_path.open('r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_keys.add((row['date'], row['family']))

    # Append new rows, skipping already-recorded families
    with out_path.open('a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if out_path.stat().st_size == 0:
            writer.writeheader()

        for a in aggregates:
            key = (today_str, a['family'])
            if key in existing_keys:
                print(f'{a["family"]}: already recorded today (skipping)')
                continue
            writer.writerow({
                'date': today_str,
                'window_days': args.days,
                'family': a['family'],
                'sessions': a['sessions'],
                'total_lines': a['total_lines'],
                'mean_density': a['mean_density'],
                'median_density': a['median_density'],
                'p90_density': a['p90_density'],
                'tool_errors': a['tool_errors'],
                'corrections': a['corrections'],
            })

    print(f'Appended to {out_path.resolve()}')


if __name__ == '__main__':
    main()
