#!/bin/bash
# Regenerate gleanin/SKILL.md from glean/artifacts/*.md and protocol directories
#
# Usage:
#   bash ~/.claude/skills/gleanin/sync.sh
#
# Reads artifacts from GLEAN_DIR/artifacts/ and rewrites the Rules section
# in this skill's SKILL.md. GLEAN_DIR defaults to the repo containing this
# script, resolved through symlinks (so it works whether invoked from the
# repo directly or via the ~/.claude/skills/gleanin symlink).
# Each artifact section renders rule (<=5 lines) + check (<=1 line).
#
# Also reads protocol files from GLEAN_PROTOCOL_DIRS (colon-separated, defaults
# to $HOME/distillation/artifacts:$HOME/fable-build/rules) and generates a
# Protocol index block for unique files not already present as artifacts.
set -u

SKILL_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
GLEAN_DIR="${GLEAN_DIR:-$(dirname "$SKILL_DIR")}"
ARTIFACTS_DIR="$GLEAN_DIR/artifacts"
SKILL_FILE="$SKILL_DIR/SKILL.md"
PROTOCOL_DIRS="${GLEAN_PROTOCOL_DIRS:-$HOME/distillation/artifacts:$HOME/fable-build/rules}"

if [ ! -d "$ARTIFACTS_DIR" ]; then
  echo "No artifacts dir at $ARTIFACTS_DIR. Nothing to sync."
  exit 0
fi

ARTIFACTS_DIR="$ARTIFACTS_DIR" SKILL_FILE="$SKILL_FILE" PROTOCOL_DIRS="$PROTOCOL_DIRS" python3 << 'PY'
import os, sys, glob

artifacts_dir = os.environ['ARTIFACTS_DIR']
skill_file = os.environ['SKILL_FILE']
protocol_dirs_raw = os.environ['PROTOCOL_DIRS']

# --- Phase 1: Parse artifacts ---
rules = []
for f in sorted(glob.glob(os.path.join(artifacts_dir, '*.md'))):
    name = os.path.splitext(os.path.basename(f))[0].replace('-', ' ').title()
    with open(f) as fh:
        content = fh.read()

    lines = content.split('\n')
    in_frontmatter = False
    collecting = False
    what = []
    rule = []
    check = []
    current = None

    for line in lines:
        s = line.strip()
        if s == '---':
            if not collecting:
                in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if s.startswith('# ') and not collecting:
            continue

        if s.startswith('**What went wrong:**'):
            collecting = True
            current = 'what'
            what.append(s.split(':**', 1)[1].strip() if ':**' in s else '')
            continue
        if s.startswith('**Rule:**'):
            current = 'rule'
            rest = s.split(':**', 1)[1].strip() if ':**' in s else ''
            if rest:
                rule.append(rest)
            continue
        if s.startswith('**Check:**'):
            current = 'check'
            rest = s.split(':**', 1)[1].strip() if ':**' in s else ''
            if rest:
                check.append(rest)
            continue

        if not collecting:
            continue

        # Stop at unknown bold header
        if s.startswith('**') and ':**' in s:
            break

        if current == 'what':
            what.append(s)
        elif current == 'rule':
            rule.append(s)
        elif current == 'check':
            check.append(s)

    rule_text = '\n'.join(r for r in rule if r.strip())[:600]
    check_text = ' '.join(c for c in check if c).strip()[:200]

    rules_text = f'**Rule:**\n{rule_text}\n\n**Check:** {check_text}'
    rules.append((name, rules_text))

# --- Phase 2: Collect artifact stems for deduplication ---
artifact_stems = set()
for f in glob.glob(os.path.join(artifacts_dir, '*.md')):
    stem = os.path.splitext(os.path.basename(f))[0]
    artifact_stems.add(stem)

# --- Phase 3: Parse protocol directories ---
protocol_entries = []

def extract_trigger(content):
    """First non-empty, non-heading, non-frontmatter line; cut at first '. '; hard-cap 160 chars."""
    in_fm = False
    for line in content.split('\n'):
        s = line.strip()
        if s == '---':
            in_fm = not in_fm
            continue
        if in_fm:
            continue
        if s.startswith('#'):
            continue
        if not s:
            continue
        # strip a leading list marker so "1. " is not taken as a sentence end
        first = s.split(' ', 1)
        if len(first) == 2 and first[0].rstrip('.').isdigit():
            s = first[1]
        elif s[:2] in ('- ', '* '):
            s = s[2:]
        idx = s.find('. ')
        if idx != -1:
            s = s[:idx + 1]
        return s[:160]
    return ''

def extract_display_name(stem, content):
    """First '# ' line; strip '# ' and optional leading 'Rule: '; fallback to stem with dashes."""
    for line in content.split('\n'):
        s = line.strip()
        if s.startswith('# '):
            name = s[2:]
            if name.startswith('Rule: '):
                name = name[6:]
            return name
    return stem.replace('-', ' ')

protocol_dirs = [d for d in protocol_dirs_raw.split(':') if d]
for pdir in protocol_dirs:
    if not os.path.isdir(pdir):
        continue
    for f in sorted(glob.glob(os.path.join(pdir, '*.md'))):
        stem = os.path.splitext(os.path.basename(f))[0]
        if stem in artifact_stems:
            continue  # dedupe: inlined compact rule wins
        with open(f) as fh:
            content = fh.read()
        name = extract_display_name(stem, content)
        trigger = extract_trigger(content)
        display_path = f.replace(os.path.expanduser('~'), '~', 1)
        entry = f'- **{name}** — {trigger} → read {display_path}'
        protocol_entries.append(entry)

# --- Phase 4: Build rules block ---
start_marker = '<!-- Rules are auto-generated'
end_marker = '<!-- end gleanin rules -->'

new_rules = '<!-- Rules are auto-generated by sync.sh. Do not edit manually. -->\n'
for name, text in rules:
    new_rules += f'\n### {name}\n\n{text}\n'
new_rules += '\n<!-- end gleanin rules -->'

# --- Phase 5: Build protocol block ---
proto_start = '<!-- Protocol index auto-generated by sync.sh. Do not edit manually. -->'
proto_end = '<!-- end protocol index -->'

if protocol_entries:
    proto_block = (proto_start + '\n\n## Protocol index\n\n'
                   'Trigger-loaded protocols. When a trigger matches the current task, Read the file before proceeding.\n\n'
                   + '\n'.join(protocol_entries) + '\n\n'
                   + proto_end)
else:
    proto_block = ''

# --- Phase 6: Read, replace, write ---
with open(skill_file) as f:
    original = f.read()

# Replace rules block
if start_marker in original and end_marker in original:
    before = original.split(start_marker)[0]
    after = original.split(end_marker, 1)[1]
    intermediate = before + new_rules + after
else:
    header, _, footer = original.partition('## Rules')
    intermediate = header + '## Rules\n\n' + new_rules + '\n' + footer

# Replace / insert / remove protocol block
if proto_block:
    if proto_start in intermediate and proto_end in intermediate:
        before = intermediate.split(proto_start)[0]
        after = intermediate.split(proto_end, 1)[1]
        result = before + proto_block + after
    else:
        result = intermediate.replace('<!-- end gleanin rules -->',
                                      '<!-- end gleanin rules -->\n\n' + proto_block)
else:
    if proto_start in intermediate and proto_end in intermediate:
        before = intermediate.split(proto_start)[0]
        after = intermediate.split(proto_end, 1)[1]
        result = before + after
    else:
        result = intermediate

with open(skill_file, 'w') as f:
    f.write(result)

count_rules = len(rules)
count_protos = len(protocol_entries)
print(f'gleanin: synced {count_rules} artifacts + {count_protos} protocols into SKILL.md')
PY
