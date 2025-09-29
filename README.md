# GitHub Issue Copier with Dependency Support

A Python script for copying issues from one GitHub repository to another with proper error handling, rate limiting, batch processing, and **dependency relationship preservation**.

## Features

- **Dependency Preservation**: Automatically detects and preserves issue dependencies
- **Topological Sorting**: Copies parent issues before child issues
- **Reference Updates**: Updates issue references in copied content
- **Secure Token Management**: Uses environment variables for GitHub token
- **Rate Limiting**: Intelligent rate limiting with automatic backoff
- **Batch Processing**: Processes issues in batches to avoid API limits
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Logging**: Detailed logging to both file and console
- **Metadata Preservation**: Maintains original issue metadata
- **Pull Request Filtering**: Automatically excludes pull requests

## Dependency Support

The script recognizes these dependency patterns in issue titles and descriptions:

- `blocks #123` or `blocking #123`
- `blocked by #123`
- `depends on #123`
- `requires #123`
- `parent: #123`
- `subtask of #123`
- `related to #123`

### How Dependencies Work

1. **Detection**: Scans all issues for dependency patterns
2. **Graph Building**: Creates a dependency graph showing relationships
3. **Topological Sort**: Orders issues so parents are copied before children
4. **Reference Updates**: Updates issue numbers in copied content to match new repository
5. **Comments**: Adds explanatory comments to maintain relationship context

## Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token with `repo` permissions
- Access to both source and target repositories

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/copy-issues.git
cd copy-issues
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Required
GITHUB_TOKEN=your_github_personal_access_token_here
SOURCE_REPO=owner/source-repository
TARGET_REPO=owner/target-repository

# Optional (these have defaults)
BATCH_SIZE=10
BATCH_DELAY=60
MAX_RETRIES=3
```

### Getting a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select the `repo` scope for full repository access
4. Copy the generated token

## Usage

### Basic Usage

Set your environment variables and run:

```bash
python copy_issues/copy_issues.py
```

### Testing Dependencies

Test dependency parsing patterns:

```bash
python demo_dependencies.py
```

### Using Environment File

If using a `.env` file:

```bash
# On Windows
set GITHUB_TOKEN=your_token_here
set SOURCE_REPO=owner/source-repo
set TARGET_REPO=owner/target-repo
python copy_issues/copy_issues.py

# On Linux/Mac
export GITHUB_TOKEN=your_token_here
export SOURCE_REPO=owner/source-repo
export TARGET_REPO=owner/target-repo
python copy_issues/copy_issues.py
```

## Dependency Examples

### Example Issue Content

**Original Issue #123:**
```
Title: Implement user authentication
Body: This feature blocks #124 and depends on #100
```

**Original Issue #124:**
```
Title: Create user dashboard
Body: Subtask of #123. This requires user auth to be completed.
```

### After Copying

**New Issue #456 (was #123):**
```
Title: Implement user authentication
Body: This feature blocks #457 and depends on #455

---
Original Issue: https://github.com/source/repo/issues/123
Created by: developer1
Original creation date: 2025-01-15T10:30:00Z
Original dependencies: #100
```

**New Issue #457 (was #124):**
```
Title: Create user dashboard  
Body: Subtask of #456. This requires user auth to be completed.

---
Original Issue: https://github.com/source/repo/issues/124
Created by: developer2
Original creation date: 2025-01-15T11:00:00Z
Original dependencies: #123
```

Plus comments:
- Issue #456 gets comment: "This issue blocks #457 (originally #124)"
- Issue #457 gets comment: "This issue depends on #456 (originally #123)"
```

```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | Required | Your GitHub Personal Access Token |
| `SOURCE_REPO` | Required | Source repository (owner/repo) |
| `TARGET_REPO` | Required | Target repository (owner/repo) |
| `BATCH_SIZE` | 10 | Number of issues per batch |
| `BATCH_DELAY` | 60 | Seconds to wait between batches |
| `MAX_RETRIES` | 3 | Maximum retry attempts for failed requests |

### Dependency Patterns

The script uses these regex patterns to detect dependencies:

1. `(?:blocks?|blocking|blocked by|depends on|requires?)\s*:?\s*#(\d+)`
2. `parent\s*:?\s*#(\d+)`
3. `subtask\s+of\s*:?\s*#(\d+)`
4. `related\s+to\s*:?\s*#(\d+)`

You can test these patterns using the included demo script.

## Output

The script will:
- Analyze all issues for dependency relationships
- Log the dependency graph and sorting process  
- Display progress for each issue (in dependency order)
- Show success/failure counts at completion
- Include original issue metadata in copied issues
- Add explanatory comments about dependencies
- Provide a dependency mapping summary

## Dependency Processing

1. **Analysis Phase**: Scans all issues for dependency patterns
2. **Graph Building**: Creates parent→child relationship mapping
3. **Topological Sort**: Orders issues so dependencies are copied first
4. **Copy Phase**: Creates issues in dependency order
5. **Reference Update**: Updates issue numbers in content
6. **Comment Addition**: Adds relationship context comments
7. **Summary Report**: Shows old→new issue number mappings

## Error Handling

The script handles:
- Rate limiting (automatic backoff)
- Network errors (with retries)
- API errors (with detailed logging)
- Invalid configurations (with clear error messages)

## Limitations

- Does not copy issue comments (GitHub API limitation, except dependency comments)
- Does not preserve exact timestamps
- Requires write access to target repository
- Rate limited by GitHub API (5000 requests/hour for authenticated requests)
- Circular dependencies are handled but may not preserve exact order
- Complex dependency patterns may require manual review

## Security Notes

- Never commit your GitHub token to version control
- Use environment variables or secure credential storage
- Review target repository permissions before running
- Consider running on a small batch first to test

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check token permissions and repository access
2. **Rate Limiting**: Increase `BATCH_DELAY` or reduce `BATCH_SIZE`
3. **Network Errors**: Check internet connection and GitHub status
4. **Token Issues**: Verify token is valid and has correct scopes

### Debug Mode

Enable debug logging by modifying the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
  

