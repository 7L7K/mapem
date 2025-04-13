#!/bin/bash
set -e

# Paths
ZIP_PATH="$HOME/mapem/zip/frontend-backup.zip"
TARGET_DIR="$HOME/mapem/frontend"
TMP_DIR="$TARGET_DIR/__temp_patch"
LOG_FILE="$TARGET_DIR/frontend_patch_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="$TARGET_DIR/src_vite_backup_$(date +%Y%m%d_%H%M%S)"

echo "📦 [1] Unzipping archive to: $TMP_DIR"
unzip -q "$ZIP_PATH" -d "$TMP_DIR"

# Confirm the extracted path is correct
SRC_PATH="$TMP_DIR/frontend-backup/genealogy-frontend/src"
if [ ! -d "$SRC_PATH" ]; then
  echo "❌ Could not find expected src directory at $SRC_PATH"
  exit 1
fi

# Backup existing frontend/src folder
if [ -d "$TARGET_DIR/src" ]; then
  echo "🧼 [2] Backing up existing src/ → $BACKUP_DIR"
  mv "$TARGET_DIR/src" "$BACKUP_DIR"
else
  echo "ℹ️ [2] No existing src/ folder found — skipping backup"
fi

# Copy with logging
echo "📁 [3] Copying files to $TARGET_DIR/src"
mkdir "$TARGET_DIR/src"
find "$SRC_PATH" -type f | while read -r file; do
  REL_PATH="${file#$SRC_PATH/}"
  DEST_PATH="$TARGET_DIR/src/$REL_PATH"
  mkdir -p "$(dirname "$DEST_PATH")"
  cp "$file" "$DEST_PATH"
  echo "✅ Copied: $REL_PATH" >> "$LOG_FILE"
done

# Cleanup
echo "🧹 [4] Removing temp folder: $TMP_DIR"
rm -rf "$TMP_DIR"

# Done
echo "🎉 Patch complete!"
echo "📜 Log saved at: $LOG_FILE"
echo "🗃️ Backup of old src/ saved at: $BACKUP_DIR"
echo "👉 To run the app: cd $TARGET_DIR && npm install && npm run dev"
