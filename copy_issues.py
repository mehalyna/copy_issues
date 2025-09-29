import os
import time
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('issue_copy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration class for the issue copying script."""
    github_api_url: str = "https://api.github.com"
    source_repo: str = "Project-Stage-Academy/Forum-Project-Stage-Fullstack"
    target_repo: str = "Project-Stage-Academy/UA-4148-bravo"
    github_token: str = ""
    batch_size: int = 10
    batch_delay: int = 60
    max_retries: int = 3
    retry_delay: int = 5

    def __post_init__(self):
        """Load configuration from environment variables."""
        self.github_token = os.getenv('GITHUB_TOKEN', self.github_token)
        self.source_repo = os.getenv('SOURCE_REPO', self.source_repo)
        self.target_repo = os.getenv('TARGET_REPO', self.target_repo)
        
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")

class GitHubIssueManager:
    """Manages GitHub issue operations with proper error handling and rate limiting."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            "Authorization": f"token {self.config.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Issue-Copier/1.0"
        })
        
        return session
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limiting by checking response headers and waiting if needed."""
        if response.status_code == 429:
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            wait_time = max(reset_time - int(time.time()), 1)
            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    def get_issues_from_source_repo(self) -> List[Dict[str, Any]]:
        """Fetch all issues from the source repository with pagination."""
        issues = []
        page = 1
        
        logger.info(f"Starting to fetch issues from {self.config.source_repo}")
        
        while True:
            url = f"{self.config.github_api_url}/repos/{self.config.source_repo}/issues"
            params = {
                'page': page,
                'state': 'all',
                'per_page': 100  # Maximum allowed per page
            }
            
            try:
                response = self.session.get(url, params=params)
                self._handle_rate_limit(response)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch issues from {self.config.source_repo}: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    break

                page_issues = response.json()

                # Break if there are no more issues
                if not page_issues:
                    break

                issues.extend(page_issues)
                logger.info(f"Fetched page {page} with {len(page_issues)} issues")
                page += 1
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching issues: {e}")
                break
        
        logger.info(f"Total issues fetched: {len(issues)}")
        return issues

    def create_issue_in_target_repo(self, issue: Dict[str, Any]) -> bool:
        """Create a new issue in the target repository."""
        issue_data = {
            "title": issue["title"],
            "body": self._prepare_issue_body(issue),
            "labels": [label["name"] for label in issue.get("labels", [])]
        }
        
        url = f"{self.config.github_api_url}/repos/{self.config.target_repo}/issues"
        
        try:
            response = self.session.post(url, json=issue_data)
            self._handle_rate_limit(response)
            
            if response.status_code == 201:
                logger.info(f"Issue '{issue['title']}' created successfully in {self.config.target_repo}")
                return True
            else:
                logger.error(f"Failed to create issue '{issue['title']}': {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while creating issue '{issue['title']}': {e}")
            return False
    
    def _prepare_issue_body(self, issue: Dict[str, Any]) -> str:
        """Prepare the issue body with metadata."""
        body = issue.get("body", "")
        
        # Add metadata about the original issue
        metadata = f"\n\n---\n**Original Issue:** {issue.get('html_url', '')}\n"
        metadata += f"**Created by:** {issue.get('user', {}).get('login', 'Unknown')}\n"
        metadata += f"**Original creation date:** {issue.get('created_at', 'Unknown')}\n"
        
        return body + metadata
    
    def copy_issues(self) -> None:
        """Copy issues from the source repository to the target repository in batches."""
        logger.info("Starting issue copying process...")
        
        issues = self.get_issues_from_source_repo()

        if not issues:
            logger.warning("No issues found in the source repository.")
            return

        # Filter out pull requests
        actual_issues = [issue for issue in issues if "pull_request" not in issue]
        logger.info(f"Found {len(actual_issues)} actual issues (excluding PRs)")

        successful_copies = 0
        failed_copies = 0

        # Batch processing
        for i in range(0, len(actual_issues), self.config.batch_size):
            batch = actual_issues[i:i + self.config.batch_size]
            batch_num = i // self.config.batch_size + 1
            
            logger.info(f"Processing batch {batch_num} ({len(batch)} issues)")
            
            for issue in batch:
                if self.create_issue_in_target_repo(issue):
                    successful_copies += 1
                else:
                    failed_copies += 1
                
                # Small delay between individual issue creation
                time.sleep(1)

            if i + self.config.batch_size < len(actual_issues):
                logger.info(f"Batch {batch_num} completed. Pausing for {self.config.batch_delay} seconds...")
                time.sleep(self.config.batch_delay)

        logger.info(f"Issue copying completed! Successfully copied: {successful_copies}, Failed: {failed_copies}")

def main():
    """Main entry point for the script."""
    try:
        config = Config()
        manager = GitHubIssueManager(config)
        manager.copy_issues()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
