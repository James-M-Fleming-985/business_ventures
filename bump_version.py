#!/usr/bin/env python3
"""
Version management script for Causal Affect Platform
Matches the versioning pattern used in life_quality project
"""
import sys
from pathlib import Path


def read_version():
    """Read current version from VERSION file"""
    version_file = Path(__file__).parent / "VERSION"
    return version_file.read_text().strip()


def write_version(version):
    """Write version to VERSION file"""
    version_file = Path(__file__).parent / "VERSION"
    version_file.write_text(version + "\n")


def increment_version(part="patch"):
    """
    Increment version number
    part: "major", "minor", or "patch" (default)
    """
    version = read_version()
    major, minor, patch = map(int, version.split("."))
    
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    write_version(new_version)
    return new_version


def main():
    """CLI interface for version management"""
    if len(sys.argv) < 2:
        print(f"Current version: {read_version()}")
        print("\nUsage:")
        print("  python bump_version.py show        - Show current version")
        print("  python bump_version.py patch       - Increment patch (2.0.14 → 2.0.15)")
        print("  python bump_version.py minor       - Increment minor (2.0.14 → 2.1.0)")
        print("  python bump_version.py major       - Increment major (2.0.14 → 3.0.0)")
        print("  python bump_version.py set X.Y.Z   - Set specific version")
        return
    
    command = sys.argv[1]
    
    if command == "show":
        print(read_version())
    elif command == "set" and len(sys.argv) == 3:
        new_version = sys.argv[2]
        write_version(new_version)
        print(f"Version set to: {new_version}")
    elif command in ["patch", "minor", "major"]:
        new_version = increment_version(command)
        print(f"Version bumped to: {new_version}")
        print(f"\nNext steps:")
        print(f"  1. git add -A")
        print(f'  2. git commit -m "v{new_version}: Your change description"')
        print(f"  3. railway up  (or Railway will auto-deploy from GitHub)")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
