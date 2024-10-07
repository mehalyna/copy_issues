Here is the `README.md` file with instructions on how to use the `copy_issues.py` script:

---

# Copy Issues Script

This Python script allows you to copy issues from one GitHub repository (source) to another repository (target) using GitHub's API.

## Prerequisites

Before you can use the script, make sure you have the following:

1. **Python 3.x** installed on your system.
2. **Personal Access Token** from GitHub with `repo` permissions. You can generate one by following [this guide](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token).
3. **Source and target repositories** that you want to copy issues between.

## How to use

### 1. Clone this repository or copy the script
You can either clone the repository or download the script `copy_issues.py`.

```bash
git clone https://github.com/yourusername/copy-issues.git
cd copy-issues
```

### 2. Install necessary dependencies

The script relies on the `requests` and `json` libraries. You can install the required package using pip:

```bash
pip install requests
```

### 3. Set up your GitHub token and repository details

Edit the `copy_issues.py` script and replace the following values:

- `GITHUB_TOKEN`: Your personal GitHub access token (replace `"Your_Personal_Access_Token"`).
- `SOURCE_REPO`: The repository you want to copy issues **from** in the format `owner/repo` (e.g., `"yourusername/source-repo"`).
- `TARGET_REPO`: The repository you want to copy issues **to** in the format `owner/repo` (e.g., `"yourusername/target-repo"`).

### 4. Adjust batch settings (optional)

- `BATCH_SIZE`: The number of issues to process in each batch. Default is 10.
- `BATCH_DELAY`: The delay (in seconds) between batches to avoid GitHub's rate limiting. Default is 120 seconds.

### 5. Run the script

After setting up the configuration, you can run the script by executing the following command:

```bash
python copy_issues.py
```

The script will begin fetching issues from the source repository and copying them to the target repository.

### 6. Monitor progress

- The script will process the issues in batches, printing the progress for each batch and pausing between batches to avoid hitting GitHub API rate limits.
- If the issue creation fails, an error message will be displayed with the response code and details.

## Notes

- **Pull Requests:** GitHub considers pull requests as issues in the API. The script automatically skips copying any pull requests.
- **Labels:** The script will copy issue labels from the source repository to the target repository. Make sure that the labels already exist in the target repository.

## Example Usage

Let's say you want to copy issues from `yourusername/source-repo` to `yourusername/target-repo`, and you have set the token accordingly. After running the script, you will see the following output:

```
Issue 'Example Issue Title' created successfully in yourusername/target-repo.
Processed batch 1. Pausing for 120 seconds.
```

---

## Troubleshooting

- If the script fails to create issues, double-check your GitHub token permissions and repository access.
- Ensure your internet connection is stable to avoid issues with API calls.
  

