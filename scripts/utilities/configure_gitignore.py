#!/usr/bin/env python3
"""
Git Ignore Configuration Utility

This script helps configure .gitignore settings for the Advanced Timetable Scheduling System.
It provides options to ignore/unignore testing scripts and development documentation.
"""

import os
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current_dir = Path(__file__).parent
    # Go up from scripts/utilities/ to project root
    return current_dir.parent.parent

def read_gitignore():
    """Read the current .gitignore file."""
    gitignore_path = get_project_root() / ".gitignore"
    if gitignore_path.exists():
        return gitignore_path.read_text(encoding='utf-8')
    return ""

def write_gitignore(content):
    """Write content to .gitignore file."""
    gitignore_path = get_project_root() / ".gitignore"
    gitignore_path.write_text(content, encoding='utf-8')

def toggle_ignore_pattern(content, pattern, ignore=True):
    """Toggle ignore pattern in gitignore content."""
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if ignore:
            # Add comment to ignore the pattern
            if line.strip() == f"# {pattern}":
                lines[i] = pattern
                modified = True
                print(f"✅ Now ignoring: {pattern}")
        else:
            # Remove comment to unignore the pattern
            if line.strip() == pattern:
                lines[i] = f"# {pattern}"
                modified = True
                print(f"✅ Now tracking: {pattern}")
    
    if not modified:
        print(f"⚠️  Pattern not found: {pattern}")
    
    return '\n'.join(lines)

def show_current_status():
    """Show current ignore status."""
    content = read_gitignore()
    
    print("\n📋 Current Git Ignore Status:")
    print("=" * 50)
    
    # Check testing scripts
    testing_patterns = [
        "scripts/testing/database/",
        "scripts/testing/api/", 
        "scripts/testing/data/"
    ]
    
    print("\n🧪 Testing Scripts:")
    for pattern in testing_patterns:
        if f"# {pattern}" in content:
            print(f"  📁 {pattern} - TRACKED")
        elif pattern in content:
            print(f"  🚫 {pattern} - IGNORED")
        else:
            print(f"  ❓ {pattern} - NOT CONFIGURED")
    
    # Check documentation
    doc_patterns = [
        "docs/UI_UX_FIXES_SUMMARY.md",
        "docs/FRONTEND_FIXES_SUMMARY.md",
        "docs/TIMETABLE_UI_FIXES.md",
        "docs/FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md",
        "docs/PROJECT_ORGANIZATION_SUMMARY.md",
        "docs/SCRIPT_ORGANIZATION_PLAN.md"
    ]
    
    print("\n📚 Development Documentation:")
    for pattern in doc_patterns:
        if f"# {pattern}" in content:
            print(f"  📄 {pattern.split('/')[-1]} - TRACKED")
        elif pattern in content:
            print(f"  🚫 {pattern.split('/')[-1]} - IGNORED")
        else:
            print(f"  ❓ {pattern.split('/')[-1]} - NOT CONFIGURED")

def main():
    """Main function."""
    print("🔧 Git Ignore Configuration Utility")
    print("=" * 40)
    
    if len(sys.argv) == 1:
        show_current_status()
        print("\n💡 Usage:")
        print("  python configure_gitignore.py status          - Show current status")
        print("  python configure_gitignore.py ignore-tests    - Ignore testing scripts")
        print("  python configure_gitignore.py track-tests     - Track testing scripts")
        print("  python configure_gitignore.py ignore-docs     - Ignore dev documentation")
        print("  python configure_gitignore.py track-docs      - Track dev documentation")
        print("  python configure_gitignore.py minimal         - Minimal repository (ignore tests & docs)")
        print("  python configure_gitignore.py full            - Full repository (track everything)")
        return
    
    command = sys.argv[1].lower()
    content = read_gitignore()
    
    if command == "status":
        show_current_status()
        
    elif command == "ignore-tests":
        print("\n🚫 Configuring to ignore testing scripts...")
        patterns = ["scripts/testing/database/", "scripts/testing/api/", "scripts/testing/data/"]
        for pattern in patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=True)
        write_gitignore(content)
        print("✅ Testing scripts will now be ignored")
        
    elif command == "track-tests":
        print("\n📁 Configuring to track testing scripts...")
        patterns = ["scripts/testing/database/", "scripts/testing/api/", "scripts/testing/data/"]
        for pattern in patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=False)
        write_gitignore(content)
        print("✅ Testing scripts will now be tracked")
        
    elif command == "ignore-docs":
        print("\n🚫 Configuring to ignore development documentation...")
        patterns = [
            "docs/UI_UX_FIXES_SUMMARY.md",
            "docs/FRONTEND_FIXES_SUMMARY.md", 
            "docs/TIMETABLE_UI_FIXES.md",
            "docs/FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md",
            "docs/PROJECT_ORGANIZATION_SUMMARY.md",
            "docs/SCRIPT_ORGANIZATION_PLAN.md"
        ]
        for pattern in patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=True)
        write_gitignore(content)
        print("✅ Development documentation will now be ignored")
        
    elif command == "track-docs":
        print("\n📄 Configuring to track development documentation...")
        patterns = [
            "docs/UI_UX_FIXES_SUMMARY.md",
            "docs/FRONTEND_FIXES_SUMMARY.md",
            "docs/TIMETABLE_UI_FIXES.md", 
            "docs/FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md",
            "docs/PROJECT_ORGANIZATION_SUMMARY.md",
            "docs/SCRIPT_ORGANIZATION_PLAN.md"
        ]
        for pattern in patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=False)
        write_gitignore(content)
        print("✅ Development documentation will now be tracked")
        
    elif command == "minimal":
        print("\n🎯 Configuring minimal repository (ignore tests & docs)...")
        # Ignore testing scripts
        test_patterns = ["scripts/testing/database/", "scripts/testing/api/", "scripts/testing/data/"]
        for pattern in test_patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=True)
        
        # Ignore development docs
        doc_patterns = [
            "docs/UI_UX_FIXES_SUMMARY.md",
            "docs/FRONTEND_FIXES_SUMMARY.md",
            "docs/TIMETABLE_UI_FIXES.md",
            "docs/FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md", 
            "docs/PROJECT_ORGANIZATION_SUMMARY.md",
            "docs/SCRIPT_ORGANIZATION_PLAN.md"
        ]
        for pattern in doc_patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=True)
            
        write_gitignore(content)
        print("✅ Minimal repository configuration applied")
        
    elif command == "full":
        print("\n📚 Configuring full repository (track everything)...")
        # Track testing scripts
        test_patterns = ["scripts/testing/database/", "scripts/testing/api/", "scripts/testing/data/"]
        for pattern in test_patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=False)
        
        # Track development docs
        doc_patterns = [
            "docs/UI_UX_FIXES_SUMMARY.md",
            "docs/FRONTEND_FIXES_SUMMARY.md",
            "docs/TIMETABLE_UI_FIXES.md",
            "docs/FACULTY_AVAILABILITY_CONSOLIDATION_SUMMARY.md",
            "docs/PROJECT_ORGANIZATION_SUMMARY.md", 
            "docs/SCRIPT_ORGANIZATION_PLAN.md"
        ]
        for pattern in doc_patterns:
            content = toggle_ignore_pattern(content, pattern, ignore=False)
            
        write_gitignore(content)
        print("✅ Full repository configuration applied")
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python configure_gitignore.py' to see available commands")

if __name__ == "__main__":
    main() 