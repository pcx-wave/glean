#!/usr/bin/env python3
"""Scan Claude Code session logs and flag sessions showing model friction."""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


CORRECTION_PATTERNS = [
    'request interrupted by user',
    ' wrong',
    'not what i',
    'instead of',
    'revert',
    'undo ',
    'stop ',
    "don't",
    'no, ',
    'non, ',
    'pas ce que',
]


def scan_session(path: str) -> dict:
    """Parse one jsonl file, return dict of signals."""
    signals = {
        'tool_errors': 0,
        'edit_loop': 0,
        'corrections': 0,
        'dominant_model': '',
        'last_entry_type': '',
        'line_count': 0,
    }

    models = []
    edit_counts = Counter()
    last_type = None
    line_count = 0

    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                entry_type = obj.get('type')
                if entry_type is None:
                    continue

                last_type = entry_type

                if entry_type == 'assistant':
                    msg = obj.get('message', {})
                    model = msg.get('model', '')
                    if model:
                        models.append(model)

                    content = msg.get('content', [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'tool_use':
                                name = block.get('name', '')
                                if name in ('Edit', 'Write'):
                                    inp = block.get('input', {})
                                    if isinstance(inp, dict):
                                        fp = inp.get('file_path')
                                        if fp:
                                            edit_counts[fp] += 1

                elif entry_type == 'user':
                    msg = obj.get('message', {})
                    content = msg.get('content')

                    # Count tool errors
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'tool_result':
                                if block.get('is_error', False):
                                    signals['tool_errors'] += 1

                    # Count corrections from plain string user messages
                    if isinstance(content, str):
                        lower_content = content.lower()
                        for pattern in CORRECTION_PATTERNS:
                            if pattern in lower_content:
                                signals['corrections'] += 1
                                break

    except (IOError, OSError):
        pass

    signals['line_count'] = line_count

    if edit_counts:
        signals['edit_loop'] = max(edit_counts.values())

    if models:
        most_common = Counter(models).most_common(1)
        signals['dominant_model'] = most_common[0][0]

    if last_type:
        signals['last_entry_type'] = last_type

    return signals


def main() -> None:
    parser = argparse.ArgumentParser(description='Scan Claude Code session logs for friction signals')
    parser.add_argument('--root', default=os.path.expanduser('~/.claude/projects'),
                        help='Root directory containing session logs')
    parser.add_argument('--min-sessions', type=int, default=60,
                        help='Minimum sessions to scan (sorted by recency)')
    parser.add_argument('--model-filter', default='sonnet',
                        help='Model substring to filter by (empty = all)')
    parser.add_argument('--min-size-kb', type=int, default=20,
                        help='Skip files smaller than this size in KB')

    args = parser.parse_args()

    root = Path(args.root)
    min_size = args.min_size_kb * 1024

    # Collect all session files, sorted by modification time (newest first)
    sessions = []
    for jsonl_path in root.rglob('*.jsonl'):
        if jsonl_path.is_file() and jsonl_path.stat().st_size >= min_size:
            mtime = jsonl_path.stat().st_mtime
            sessions.append((mtime, jsonl_path))

    sessions.sort(reverse=True)
    sessions = sessions[:args.min_sessions]

    results = []
    for mtime, jsonl_path in sessions:
        signals = scan_session(str(jsonl_path))
        model = signals['dominant_model']

        if args.model_filter and args.model_filter not in model:
            continue

        # Density: total friction per 1000 lines
        total = signals['tool_errors'] + signals['edit_loop'] + signals['corrections'] * 5
        lines = signals['line_count'] or 1
        density = total * 1000 / lines

        session_id = jsonl_path.stem[:12]
        project = jsonl_path.parent.name

        # Shorten project name
        short = project.replace('-home-pcx-pi-', '').replace('-home-pcx-pi', '').replace('-tmp-', '').replace('-workspace', '')
        results.append({
            'id': session_id,
            'project': short,
            'model': model or '?',
            'errors': signals['tool_errors'],
            'loop': signals['edit_loop'],
            'corr': signals['corrections'],
            'lines': lines,
            'density': density,
            'path': str(jsonl_path.resolve()),
        })

    # Sort by density (highest first)
    results.sort(key=lambda r: -r['density'])

    # Print table
    print(f"{'density':>7}  {'errors':>6}  {'loop':>4}  {'corr':>4}  {'lines':>5}  {'project':<30}  {'session'}")
    print(f"{'-'*7}  {'-'*6}  {'-'*4}  {'-'*4}  {'-'*5}  {'-'*30}  {'-'*12}")
    for r in results:
        print(f"{r['density']:>7.1f}  {r['errors']:>6}  {r['loop']:>4}  {r['corr']:>4}  {r['lines']:>5}  {r['project'][:30]:<30}  {r['id']}")

    print(f"\n{len(results)} sessions (model filter: '{args.model_filter}')")
    print("Pick a session by density and project context, then:")
    print("  cat <path> | claude -p \"$(cat prompt.md)\" --model fable > artifacts/<name>.md")


if __name__ == '__main__':
    main()
