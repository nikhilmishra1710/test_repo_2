import os
import subprocess
import sys
import re
from typing import List, Tuple
import json
import requests

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
                output += f"{filepath}:{lineno}: {line}"
                count += 1
    except subprocess.CalledProcessError as e:
        print(f"Failed to parse diff for {filepath}: {e}")
    return count, output

def post_sticky_comment(violations: List[dict], total_violations: int) -> None:
    header = "<!-- logging-info-warning -->"
    if total_violations == 0:
        body = f"{header}\nNo `logging.info` violations found."
    else:    
        details = json.dumps(violations, indent=2)
        body = f"{header}\n⚠️ Detected {total_violations} `logging.info` statements in the code.\n```json\n{details}\n```"
    
    try:
        repo = os.environ.get("GITHUB_REPOSITORY")
        pr_number = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_REF", "").split("/")[-1]
        token = os.environ.get("GITHUB_TOKEN")

        if not all([repo, pr_number, token]):
            print("Missing GITHUB_REPOSITORY, PR_NUMBER, or GITHUB_TOKEN")
            return

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = requests.get(comments_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch comments: {response.text}")
            return

        comments = response.json()
        comment_id = None
        for comment in comments:
            if comment["body"].startswith(header):
                comment_id = comment["id"]
                break

        if comment_id:
            update_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
            response = requests.patch(update_url, headers=headers, json={"body": body})
            if response.status_code != 200:
                print(f"Failed to update comment: {response.text}")
        else:
            response = requests.post(comments_url, headers=headers, json={"body": body})
            if response.status_code != 201:
                print(f"Failed to create comment: {response.text}")
    except Exception as e:
        print(f"Failed to post comment: {e}")
        return

def main():
    diff_range = os.environ.get("DIFF_RANGE", "HEAD^..HEAD")
    changed_files = get_changed_files(diff_range)
    
    if not changed_files:
        print("No Python files changed in the specified diff range.")
        print("::set-output name=logging_info_violations_details::[]")
        print("::set-output name=failed::false")
        print("::set-output name=logging_info_violations_count::0")
        return
    total_violations = 0
    violations = []
    for file in changed_files:
        if os.path.exists(file):
            count, output = check_logging_info(file, diff_range)
            if count > 0:
                total_violations += count
                op = output.split(':')
                violations.append({"file": op[0], "line": op[1], "details": op[2].strip()})

    if total_violations == 0:
        print("No `logging.info` violations found.")
        print("::set-output name=logging_info_violations_details::[]")
        print("::set-output name=failed::false")
        print("::set-output name=logging_info_violations_count::0")
        return
    
    print(f"::set-output name=logging_info_violations_details::{json.dumps(violations)}")
    print(f"::set-output name=failed::true")
    print(f"::set-output name=logging_info_violations_count::{len(violations)}")
    
    post_sticky_comment(violations, total_violations)


if __name__ == "__main__":
    main()
