"""Strip sensitive patterns from glean artifact files."""
import re
import sys
from pathlib import Path

# Patterns that indicate sensitive data
SENSITIVE_PATTERNS = [
    # URLs (except github.com/pcx-wave/glean)
    (r'https?://(?!github\.com/pcx-wave/glean)[^\s<>"\'()]+', '<url>'),
    # File paths (at least 2 segments or extension)
    (r'/(?:[^\s<>"\'()/]+/)+[^\s<>"\'()/]+', '<path>'),
    (r'/\w[\w.-]*\.\w{1,4}\b', '<path>'),
    # Email addresses
    (r'[\w.+-]+@[\w-]+\.[\w.-]+', '<email>'),
    # API keys, tokens (≥20 alphanumeric chars, or sk- prefixed)
    (r'\b(?:sk[-_])?[A-Za-z0-9]{20,}\b', '<credential>'),
    # IP addresses
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<ip>'),
    # Domain names (not common words)
    (r'\b[\w-]+\.(?:com|org|net|io|dev|app|ai|co|uk|fr|de|jp)(?::\d+)?\b', '<domain>'),
]

# Project-name-like words (PascalCase, >2 chars, not common)
# We only flag words that appear ≤2 times in common English
COMMON_WORDS = {
    "This", "That", "What", "When", "Where", "Which", "Who", "How",
    "Rule", "Check", "File", "Line", "Name", "Path", "Code", "User",
    "Data", "Type", "Mode", "Key", "Value", "Size", "Count", "Text",
    "Result", "Error", "Status", "Role", "Scope", "Task", "Model",
    "Class", "Func", "Funcs", "Const", "Var", "Param", "Args",
    "Read", "Write", "Exec", "Run", "Get", "Set", "List", "Find",
    "Host", "Port", "Addr", "From", "With", "Each", "Some", "None",
    "Then", "Than", "Also", "Just", "Only", "Over", "Under", "Into",
    "Does", "Done", "Has", "Had", "URL", "URI", "Host", "Auth",
    "Base", "Index", "Start", "Stop", "Step", "Page", "Link", "Node",
    "Test", "Spec", "Mock", "Stub", "View", "Page", "Site", "App",
}


def anonymize_text(text: str) -> str:
    """Replace sensitive patterns with placeholders."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def check_file(path: Path) -> list[str]:
    """Check a file for possible sensitive content. Return list of issues."""
    issues = []
    text = path.read_text()
    for pattern_str, _ in SENSITIVE_PATTERNS:
        matches = re.findall(pattern_str, text)
        for m in matches:
            issues.append(f"  {pattern_str[:40]:40s} -> {m}")
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 collector/anonymize.py <file.md|dir/> [--check]", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    check_only = "--check" in sys.argv

    if target.is_dir():
        files = sorted(target.glob("*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"Not found: {target}", file=sys.stderr)
        sys.exit(1)

    for f in files:
        if check_only:
            issues = check_file(f)
            if issues:
                print(f"{f.name}:")
                for i in issues:
                    print(i)
            else:
                print(f"{f.name}: clean")
        else:
            original = f.read_text()
            cleaned = anonymize_text(original)
            if cleaned != original:
                f.write_text(cleaned)
                print(f"{f.name}: anonymized")
            else:
                print(f"{f.name}: clean")


if __name__ == "__main__":
    main()
