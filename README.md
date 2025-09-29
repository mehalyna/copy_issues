# GitHub Issue Copier

A Python script for copying issues from one GitHub repository to another with proper error handling, rate limiting, and batch processing.

## Features

- **Secure Token Management**: Uses environment variables for GitHub token
- **Rate Limiting**: Intelligent rate limiting with automatic backoff
- **Batch Processing**: Processes issues in batches to avoid API limits
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Logging**: Detailed logging to both file and console
- **Metadata Preservation**: Maintains original issue metadata
- **Pull Request Filtering**: Automatically excludes pull requests

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
python copy_issues.py
```

### Using Environment File

If using a `.env` file:

```bash
# On Windows
set GITHUB_TOKEN=your_token_here
set SOURCE_REPO=owner/source-repo
set TARGET_REPO=owner/target-repo
python copy_issues.py

# On Linux/Mac
export GITHUB_TOKEN=your_token_here
export SOURCE_REPO=owner/source-repo
export TARGET_REPO=owner/target-repo
python copy_issues.py
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

## Output

The script will:
- Log all operations to `issue_copy.log` and console
- Display progress for each batch
- Show success/failure counts at completion
- Include original issue metadata in copied issues

## Error Handling

The script handles:
- Rate limiting (automatic backoff)
- Network errors (with retries)
- API errors (with detailed logging)
- Invalid configurations (with clear error messages)

## Limitations

- Does not copy issue comments (GitHub API limitation)
- Does not preserve exact timestamps
- Requires write access to target repository
- Rate limited by GitHub API (5000 requests/hour for authenticated requests)

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
  

