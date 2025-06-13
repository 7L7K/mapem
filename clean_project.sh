#!/bin/bash
# clean_project.sh
# Usage: ./clean_project.sh /path/to/project

TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ]; then
  echo "Usage: $0 /path/to/project"
  exit 1
fi

echo "Cleaning junk from $TARGET_DIR..."

# Delete junk directories
find "$TARGET_DIR" -type d \( -name "__MACOSX" -o -name "__pycache__" -o -name ".git" -o -name "node_modules" \) -exec rm -rf {} +

# Delete junk files
find "$TARGET_DIR" -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "*.zip" -o -name "*.rar" -o -name "*.7z" \) -delete

echo "Done cleaning."

