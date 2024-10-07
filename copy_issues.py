import time
import requests
import json

# Configuration
GITHUB_API_URL = "https://api.github.com"
SOURCE_REPO = "your_source_repo"  # Format: owner/repo
TARGET_REPO = "your_target_repo"  # Format: owner/repo
GITHUB_TOKEN = "your_personal_access_token"  # Personal Access Token
BATCH_SIZE = 10  # Number of issues to process per batch
BATCH_DELAY = 120  # Delay (in seconds) between batches to avoid rate limits

# Headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_issues_from_source_repo():
    """Fetch all issues from the source repository."""
    issues = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/repos/{SOURCE_REPO}/issues?page={page}&state=all"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch issues from {SOURCE_REPO}: {response.status_code}")
            return []

        page_issues = response.json()

        # Break if there are no more issues
        if not page_issues:
            break

        issues.extend(page_issues)
        page += 1
    return issues

def create_issue_in_target_repo(issue):
    """Create a new issue in the target repository."""
    issue_data = {
        "title": issue["title"],
        "body": issue.get("body", ""),  # Issue description
        "labels": [label["name"] for label in issue.get("labels", [])]  # Copy labels
    }
    url = f"{GITHUB_API_URL}/repos/{TARGET_REPO}/issues"
    response = requests.post(url, headers=HEADERS, data=json.dumps(issue_data))

    if response.status_code == 201:
        print(f"Issue '{issue['title']}' created successfully in {TARGET_REPO}.")
    else:
        print(f"Failed to create issue '{issue['title']}': {response.status_code} {response.text}")

def copy_issues():
    """Copy issues from the source repository to the target repository in batches."""
    issues = get_issues_from_source_repo()

    if not issues:
        print("No issues found in the source repository.")
        return

    # Batch processing
    for i in range(0, len(issues), BATCH_SIZE):
        batch = issues[i:i + BATCH_SIZE]
        
        for issue in batch:
            # Skip pull requests (GitHub issues API includes PRs as issues)
            if "pull_request" in issue:
                continue

            create_issue_in_target_repo(issue)

        print(f"Processed batch {i // BATCH_SIZE + 1}. Pausing for {BATCH_DELAY} seconds.")
        time.sleep(BATCH_DELAY)  # Pause after each batch to avoid rate limits

if __name__ == "__main__":
    copy_issues()
