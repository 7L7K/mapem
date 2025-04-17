#!/bin/bash

TARGET_DIR="$HOME/mapem/frontend/genealogy-frontend/src/components"
OUTPUT_FILE="$HOME/Desktop/component_contents.txt"

echo "📝 Writing file names + contents from $TARGET_DIR into $OUTPUT_FILE..."

> "$OUTPUT_FILE" # Clear out the old file

for file in "$TARGET_DIR"/*; do
  if [[ -f "$file" ]]; then
    echo "===== FILE: $file =====" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
  fi
done

echo "✅ Done. Full contents dumped to $OUTPUT_FILE"
