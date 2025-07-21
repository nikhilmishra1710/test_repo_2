import os
import subprocess
import sys
import re
from typing import List, Tuple


def get_changed_files(diff_range: str) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", diff_range],
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )
    return [f.strip() for f in result.stdout.splitlines() if f.endswith(".py")]


def parse_diff_with_line_numbers(filepath: str, diff_range: str) -> List[Tuple[int, str]]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", diff_range, "--", filepath],
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )

    added_lines = []
    current_line = None
    for line in result.stdout.splitlines():
        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                current_line = int(match.group(1)) - 1
        elif line.startswith('+') and not line.startswith('+++'):
            if current_line is not None:
                current_line += 1
                added_lines.append((current_line, line[1:].rstrip()))
        elif not line.startswith('-') and not line.startswith('---') and line != "\\ No newline at end of file":
            if current_line is not None:
                current_line += 1

    return added_lines


def check_logging_info(filepath: str, diff_range: str) -> int:
    count = 0
    output = ""
    try:
        added_lines = parse_diff_with_line_numbers(filepath, diff_range)
        for lineno, line in added_lines:
            line = line.strip()
            if line.startswith("logging.info(") and not line.endswith("#--- IGNORE ---"):
                print(f"{filepath}:{lineno}: {line}")
                print(f"::error file={filepath},line={lineno}::Avoid using logging.info in production code.")
                output += f"{filepath}:{lineno}: {line};"
                count += 1
    except subprocess.CalledProcessError as e:
        print(f"Failed to parse diff for {filepath}: {e}", file=sys.stderr)
    return count, output


def main():
    diff_range = os.environ.get("DIFF_RANGE", "HEAD^..HEAD")
    changed_files = get_changed_files(diff_range)

    file_counts = {}
    total_violations = 0
    op = ""
    for file in changed_files:
        if os.path.exists(file):
            count, output = check_logging_info(file, diff_range)
            if count > 0:
                file_counts[file] = count
                total_violations += count
                op += output

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"logging_info_violations_count={total_violations}\n") 
            f.write(f"logging_info_violations_details={op}\n")
            f.write(f"failed={'true' if total_violations > 0 else 'false'}\n")


if __name__ == "__main__":
    main()
