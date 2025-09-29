#!/usr/bin/env python3
"""
Demo script to show how dependency parsing works.
This script analyzes issue text and shows what dependencies would be detected.
"""

import re
from typing import List

# Default dependency patterns
DEPENDENCY_PATTERNS = [
    r'(?:blocks?|blocking|blocked by|depends on|requires?)\s*:?\s*#(\d+)',
    r'parent\s*:?\s*#(\d+)',
    r'subtask\s+of\s*:?\s*#(\d+)',
    r'related\s+to\s*:?\s*#(\d+)',
]

def parse_dependencies(text: str) -> List[int]:
    """Parse text for dependency references."""
    dependencies = []
    
    for pattern in DEPENDENCY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            try:
                dep_id = int(match)
                if dep_id not in dependencies:
                    dependencies.append(dep_id)
            except ValueError:
                continue
    
    return dependencies

def demo_dependency_parsing():
    """Demonstrate dependency parsing with sample texts."""
    sample_texts = [
        "This feature blocks #123 and depends on #456",
        "Subtask of #789",
        "Parent: #100",
        "Related to #200 and #300",
        "This issue requires #400 to be completed first",
        "Blocking: #500",
        "This task is blocked by #600",
        "Multiple dependencies: blocks #700, depends on #800, parent #900"
    ]
    
    print("Dependency Parsing Demo")
    print("=" * 50)
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n{i}. Text: '{text}'")
        dependencies = parse_dependencies(text)
        if dependencies:
            print(f"   Found dependencies: {dependencies}")
        else:
            print("   No dependencies found")
    
    print("\n" + "=" * 50)
    print("Dependency patterns used:")
    for i, pattern in enumerate(DEPENDENCY_PATTERNS, 1):
        print(f"{i}. {pattern}")

if __name__ == "__main__":
    demo_dependency_parsing()
