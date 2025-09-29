import os
import time
import requests
import json
import logging
import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import defaultdict, deque

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
class IssueRelationship:
    """Represents a relationship between issues."""
    parent_id: int
    child_id: int
    relationship_type: str  # 'blocks', 'subtask', 'related', etc.

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
    # Dependency parsing patterns
    dependency_patterns: List[str] = field(default_factory=lambda: [
        r'(?:blocks?|blocking|blocked by|depends on|requires?)\s*:?\s*#(\d+)',
        r'parent\s*:?\s*#(\d+)',
        r'subtask\s+of\s*:?\s*#(\d+)',
        r'related\s+to\s*:?\s*#(\d+)',
    ])

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
        self.issue_mapping: Dict[int, int] = {}  # old_issue_id -> new_issue_id
        self.relationships: List[IssueRelationship] = []
        self.dependency_graph: Dict[int, Set[int]] = defaultdict(set)  # parent -> children
        
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

    def _parse_issue_dependencies(self, issue: Dict[str, Any]) -> List[int]:
        """Parse issue body and title for dependency references."""
        dependencies = []
        text_to_search = f"{issue.get('title', '')} {issue.get('body', '')}"
        
        for pattern in self.config.dependency_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    dep_id = int(match)
                    if dep_id not in dependencies:
                        dependencies.append(dep_id)
                        logger.debug(f"Found dependency: Issue #{issue['number']} depends on #{dep_id}")
                except ValueError:
                    continue
        
        return dependencies

    def _build_dependency_graph(self, issues: List[Dict[str, Any]]) -> None:
        """Build a dependency graph from all issues."""
        logger.info("Building dependency graph...")
        
        # Create a mapping of issue numbers to issues
        issue_lookup = {issue['number']: issue for issue in issues}
        
        for issue in issues:
            dependencies = self._parse_issue_dependencies(issue)
            
            for dep_id in dependencies:
                if dep_id in issue_lookup:
                    # Create relationship: dep_id is parent of current issue
                    relationship = IssueRelationship(
                        parent_id=dep_id,
                        child_id=issue['number'],
                        relationship_type='blocks'
                    )
                    self.relationships.append(relationship)
                    self.dependency_graph[dep_id].add(issue['number'])
                    logger.debug(f"Added dependency: #{dep_id} -> #{issue['number']}")
        
        logger.info(f"Found {len(self.relationships)} dependency relationships")

    def _topological_sort(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort issues in dependency order using topological sort."""
        logger.info("Sorting issues by dependencies...")
        
        # Create issue lookup
        issue_lookup = {issue['number']: issue for issue in issues}
        
        # Calculate in-degrees (number of dependencies)
        in_degree = defaultdict(int)
        for issue in issues:
            in_degree[issue['number']] = 0
        
        # Count dependencies
        for relationship in self.relationships:
            if relationship.child_id in in_degree:
                in_degree[relationship.child_id] += 1
        
        # Queue of issues with no dependencies
        queue = deque([issue for issue in issues if in_degree[issue['number']] == 0])
        sorted_issues = []
        
        while queue:
            current_issue = queue.popleft()
            sorted_issues.append(current_issue)
            
            # Reduce in-degree for all children
            for child_id in self.dependency_graph[current_issue['number']]:
                if child_id in issue_lookup:
                    in_degree[child_id] -= 1
                    if in_degree[child_id] == 0:
                        queue.append(issue_lookup[child_id])
        
        # Add any remaining issues (circular dependencies or isolated)
        remaining = [issue for issue in issues if issue not in sorted_issues]
        if remaining:
            logger.warning(f"Found {len(remaining)} issues with circular dependencies or not in graph")
            sorted_issues.extend(remaining)
        
        logger.info(f"Sorted {len(sorted_issues)} issues in dependency order")
        return sorted_issues

    def create_issue_in_target_repo(self, issue: Dict[str, Any]) -> Optional[int]:
        """Create a new issue in the target repository and return the new issue number."""
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
                new_issue = response.json()
                new_issue_number = new_issue['number']
                old_issue_number = issue['number']
                
                # Store the mapping
                self.issue_mapping[old_issue_number] = new_issue_number
                
                logger.info(f"Issue '{issue['title']}' created successfully: #{old_issue_number} -> #{new_issue_number}")
                return new_issue_number
            else:
                logger.error(f"Failed to create issue '{issue['title']}': {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while creating issue '{issue['title']}': {e}")
            return None
    
    def _prepare_issue_body(self, issue: Dict[str, Any]) -> str:
        """Prepare the issue body with metadata and updated dependency references."""
        body = issue.get("body", "")
        
        # Update dependency references in the body
        body = self._update_dependency_references(body)
        
        # Add metadata about the original issue
        metadata = f"\n\n---\n**Original Issue:** {issue.get('html_url', '')}\n"
        metadata += f"**Created by:** {issue.get('user', {}).get('login', 'Unknown')}\n"
        metadata += f"**Original creation date:** {issue.get('created_at', 'Unknown')}\n"
        
        # Add dependency information
        dependencies = self._parse_issue_dependencies(issue)
        if dependencies:
            metadata += f"**Original dependencies:** {', '.join([f'#{dep}' for dep in dependencies])}\n"
        
        return body + metadata

    def _update_dependency_references(self, text: str) -> str:
        """Update issue references in text to point to new issue numbers."""
        if not text:
            return text
        
        updated_text = text
        
        # Find all issue references and update them if we have a mapping
        for pattern in self.config.dependency_patterns:
            def replace_reference(match):
                old_issue_id = int(match.group(1))
                if old_issue_id in self.issue_mapping:
                    new_issue_id = self.issue_mapping[old_issue_id]
                    # Replace the issue number while keeping the rest of the match
                    return match.group(0).replace(f"#{old_issue_id}", f"#{new_issue_id}")
                return match.group(0)
            
            updated_text = re.sub(pattern, replace_reference, updated_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Also handle simple #123 references
        def replace_simple_reference(match):
            old_issue_id = int(match.group(1))
            if old_issue_id in self.issue_mapping:
                new_issue_id = self.issue_mapping[old_issue_id]
                return f"#{new_issue_id}"
            return match.group(0)
        
        updated_text = re.sub(r'#(\d+)', replace_simple_reference, updated_text)
        
        return updated_text

    def _add_dependency_comments(self) -> None:
        """Add comments to issues explaining their dependencies after all issues are created."""
        logger.info("Adding dependency comments to issues...")
        
        for relationship in self.relationships:
            old_parent_id = relationship.parent_id
            old_child_id = relationship.child_id
            
            # Check if both issues were successfully copied
            if old_parent_id in self.issue_mapping and old_child_id in self.issue_mapping:
                new_parent_id = self.issue_mapping[old_parent_id]
                new_child_id = self.issue_mapping[old_child_id]
                
                # Add comment to child issue
                comment_body = f"This issue depends on #{new_parent_id} (originally #{old_parent_id})"
                self._add_issue_comment(new_child_id, comment_body)
                
                # Add comment to parent issue
                comment_body = f"This issue blocks #{new_child_id} (originally #{old_child_id})"
                self._add_issue_comment(new_parent_id, comment_body)

    def _add_issue_comment(self, issue_number: int, comment_body: str) -> bool:
        """Add a comment to an issue."""
        url = f"{self.config.github_api_url}/repos/{self.config.target_repo}/issues/{issue_number}/comments"
        
        try:
            response = self.session.post(url, json={"body": comment_body})
            self._handle_rate_limit(response)
            
            if response.status_code == 201:
                logger.debug(f"Added comment to issue #{issue_number}")
                return True
            else:
                logger.warning(f"Failed to add comment to issue #{issue_number}: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error while adding comment to issue #{issue_number}: {e}")
            return False
    
    def copy_issues(self) -> None:
        """Copy issues from the source repository to the target repository in dependency order."""
        logger.info("Starting issue copying process with dependency handling...")
        
        issues = self.get_issues_from_source_repo()

        if not issues:
            logger.warning("No issues found in the source repository.")
            return

        # Filter out pull requests
        actual_issues = [issue for issue in issues if "pull_request" not in issue]
        logger.info(f"Found {len(actual_issues)} actual issues (excluding PRs)")

        # Build dependency graph
        self._build_dependency_graph(actual_issues)
        
        # Sort issues by dependencies
        sorted_issues = self._topological_sort(actual_issues)

        successful_copies = 0
        failed_copies = 0

        # Process issues in dependency order
        logger.info("Starting to copy issues in dependency order...")
        
        for i, issue in enumerate(sorted_issues):
            logger.info(f"Processing issue {i + 1}/{len(sorted_issues)}: #{issue['number']} - {issue['title']}")
            
            new_issue_number = self.create_issue_in_target_repo(issue)
            if new_issue_number:
                successful_copies += 1
            else:
                failed_copies += 1
            
            # Small delay between individual issue creation
            time.sleep(1)
            
            # Batch delay every N issues
            if (i + 1) % self.config.batch_size == 0 and (i + 1) < len(sorted_issues):
                batch_num = (i + 1) // self.config.batch_size
                logger.info(f"Completed batch {batch_num}. Pausing for {self.config.batch_delay} seconds...")
                time.sleep(self.config.batch_delay)

        logger.info(f"Issue copying completed! Successfully copied: {successful_copies}, Failed: {failed_copies}")
        
        # Add dependency comments after all issues are created
        if self.relationships and successful_copies > 0:
            logger.info("Adding dependency relationship comments...")
            self._add_dependency_comments()
            
        # Print dependency mapping summary
        self._print_dependency_summary()

    def _print_dependency_summary(self) -> None:
        """Print a summary of the dependency mappings."""
        if not self.relationships:
            logger.info("No dependencies found in the copied issues.")
            return
            
        logger.info("Dependency mapping summary:")
        logger.info("-" * 50)
        
        for relationship in self.relationships:
            old_parent = relationship.parent_id
            old_child = relationship.child_id
            
            if old_parent in self.issue_mapping and old_child in self.issue_mapping:
                new_parent = self.issue_mapping[old_parent]
                new_child = self.issue_mapping[old_child]
                logger.info(f"#{old_parent} -> #{new_parent} blocks #{old_child} -> #{new_child}")
            else:
                logger.warning(f"Incomplete mapping: #{old_parent} -> #{old_child} (some issues may have failed to copy)")
        
        logger.info("-" * 50)

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
