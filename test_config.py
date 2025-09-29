#!/usr/bin/env python3
"""
Test script to validate GitHub Issue Copier configuration.
Run this before using the main script to ensure everything is set up correctly.
"""

import os
import requests
import sys
from copy_issues import Config, GitHubIssueManager

def test_configuration():
    """Test the configuration and GitHub API access."""
    print("Testing GitHub Issue Copier configuration...")
    print("-" * 50)
    
    try:
        # Test configuration loading
        config = Config()
        print("✓ Configuration loaded successfully")
        print(f"  Source repo: {config.source_repo}")
        print(f"  Target repo: {config.target_repo}")
        print(f"  Batch size: {config.batch_size}")
        print(f"  Batch delay: {config.batch_delay} seconds")
        
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    try:
        # Test GitHub API access
        manager = GitHubIssueManager(config)
        
        # Test source repository access
        url = f"{config.github_api_url}/repos/{config.source_repo}"
        response = manager.session.get(url)
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✓ Source repository access: {repo_data['full_name']}")
            print(f"  Description: {repo_data.get('description', 'No description')}")
            print(f"  Open issues: {repo_data.get('open_issues_count', 0)}")
        else:
            print(f"✗ Cannot access source repository: {response.status_code}")
            return False
        
        # Test target repository access
        url = f"{config.github_api_url}/repos/{config.target_repo}"
        response = manager.session.get(url)
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✓ Target repository access: {repo_data['full_name']}")
            print(f"  Description: {repo_data.get('description', 'No description')}")
            
            # Check write permissions
            if repo_data.get('permissions', {}).get('push', False):
                print("✓ Write permissions confirmed")
            else:
                print("⚠ Warning: Write permissions not confirmed")
        else:
            print(f"✗ Cannot access target repository: {response.status_code}")
            return False
        
        # Test rate limiting info
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset_time = response.headers.get('X-RateLimit-Reset')
        if remaining and reset_time:
            print(f"✓ API rate limit: {remaining} requests remaining")
        
        print("-" * 50)
        print("✓ All tests passed! Configuration is valid.")
        return True
        
    except Exception as e:
        print(f"✗ Error testing API access: {e}")
        return False

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)
