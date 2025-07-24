import subprocess
import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")
owner = 'nikhilmishra1710'
repo_name = 'test_repo_2'
repo = 'nikhilmishra1710/test_repo_2'

def create_branch(branch_name: str) -> None:
    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to create branch {branch_name}: {result.stderr.strip()}")
        else:
            print(f"Successfully created branch {branch_name}.")
        
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to push branch {branch_name} to remote: {result.stderr.strip()}")
        else:
            print(f"Successfully pushed branch {branch_name} to remote.")
    except Exception as e:
        print(f"Failed to create branch {branch_name}")
        raise e

def set_branch(branch_name: str) -> None:
    try:
        result = subprocess.run(
            ["git", "checkout", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to checkout branch {branch_name}: {result.stderr.strip()}")
        else:
            print(f"Successfully checked out branch {branch_name}.")
    except Exception as e:
        print(f"Failed to checkout branch {branch_name}")
        raise e

def create_file(file_path: str, content: str) -> None:
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Successfully created file {file_path}.")
    except Exception as e:
        print(f"Failed to create file {file_path}")
        raise e

def commit(branch_name: str, message: str) -> None:
    try:
        result = subprocess.run(
            ["git", "add", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error adding files to commit: {result.stderr.strip()}")
            raise Exception(f"Failed to add files for commit: {result.stderr.strip()}")

        result = subprocess.run(
            ["git", "commit", "-m", message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to commit changes: {result.stderr.strip()}")
        else:
            print(f"Successfully committed changes on branch {branch_name}.")
            
        result = subprocess.run(
            ["git", "push", "origin", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to push changes to remote: {result.stderr.strip()}")
        else:
            print(f"Successfully pushed changes to remote on branch {branch_name}.")
    except Exception as e:
        print(f"Failed to commit changes on branch {branch_name}")
        raise e

def create_PR(branch_name: str, base_branch: str, title: str) -> int:
    try:
        
        print(f"Creating PR from {branch_name} to {base_branch} with title '{title}'.")
        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "title": title,
                "head": f"{owner}:{branch_name}",
                "base": base_branch,
                "body": f"Automated PR from {branch_name} to {base_branch}."
            }
        )
        if response.status_code != 201:
            raise Exception(f"Failed to create PR: {response.json()}")
        
        response_data = response.json()
        print(f"Successfully created PR from {branch_name} to {base_branch}: {response_data.get('html_url', 'No URL provided')}")
        
        return response_data.get('number', -1)
        
    except Exception as e:
        print(f"Failed to create PR")
        raise e

def delete_branch(branch_name: str) -> None:
    try:
        set_branch("test1")
        
        result = subprocess.run(
            ["git", "branch", "-D", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to delete branch {branch_name}: {result.stderr.strip()}")
        else:
            print(f"Successfully deleted branch {branch_name}.")
            
        result = subprocess.run(
            ["git", "push", "origin", "--delete", branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to delete remote branch {branch_name}: {result.stderr.strip()}")
        else:
            print(f"Successfully deleted remote branch {branch_name}.")
    except Exception as e:
        print(f"Failed to delete branch {branch_name}")
        raise e

def check_action_run(pr_number: int) -> None:
    try:
        print(f"Checking action run for PR #{pr_number}.")
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/actions/runs",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            params={"branch": "test1", "status": "completed"}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to fetch action runs: {response.json()}")
        
        runs = response.json().get('workflow_runs', [])
        if not runs:
            print("No completed action runs found.")
            return
        
        for run in runs:
            if run.get('pull_requests', [{}])[0].get('number') == pr_number:
                print(f"Action run found for PR #{pr_number}: {run.get('html_url', 'No URL provided')}")
                return
        
        print(f"No action run found for PR #{pr_number}.")
    except Exception as e:
        print(f"Failed to check action run for PR #{pr_number}")
        raise e

def main():
    try:
        create_branch("test4")
        set_branch("test1")
        
        create_branch("test5")
        
        set_branch("test4")
        
        create_file("testScript.py", "import logging\n\nlogging.debug('hello world')\nlogging.debug('Byee world')\n\nclass Test:\n    def test_logging(self):\n        logging.info('This is a test log')\n        assert True\n    \n    def test_another_logging(self):\n        logging.info('Another test log')\n        assert True\n    \n    def test_no_logging(self):\n        logging.info('This is not a tes t log')\n        assert True\n")

        commit("test4", "Add testScript.py with logging tests")

        pr_number = create_PR("test4", "test1", "Add testScript.py with logging tests")
        check_action_run(pr_number)
        
        delete_branch("test4")
        delete_branch("test5")
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    
if __name__ == "__main__":
    main()