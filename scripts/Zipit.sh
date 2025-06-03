#!/bin/bash
# 📍 Destination for backups
DEST_DIR="$HOME/mapem/zip_gpt"
mkdir -p "$DEST_DIR"

# 🕒 Timestamped name
NOW=$(date +"%Y%m%d_%H%M%S")
ZIP_PATH="$DEST_DIR/highlighted_backup_$NOW.zip"

# 🗂 Include entire backend root + all subfolders
FOLDERS=(
  "$HOME/mapem/backend"           # now includes db.py, main.py, config.py
  "$HOME/mapem/backend/models"
  "$HOME/mapem/backend/routes"
  "$HOME/mapem/backend/services"
  "$HOME/mapem/backend/utils"
  "$HOME/mapem/backend/tasks"
  "$HOME/mapem/backend/data"
  "$HOME/mapem/frontend/public"
  "$HOME/mapem/frontend/src"
  "$HOME/mapem/scripts"
  "$HOME/mapem/test"
  "$HOME/mapem/test/features"
  "$HOME/mapem/test/routes"
  "$HOME/mapem/test/services"
)

# 🧹 Clean up old zips (>3 days)
find "$DEST_DIR" -name "highlighted_backup_*.zip" -mtime +3 -delete

# 🗜 Zip it all up
echo "📦 Zipping to $ZIP_PATH"
zip -r "$ZIP_PATH" "${FOLDERS[@]}"

echo "✅ Backup complete: $ZIP_PATH"

