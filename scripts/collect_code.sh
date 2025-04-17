#!/bin/bash

# Output path
OUTPUT_FILE="$HOME/mapem/code_dump.txt"
echo "🧾 Dumping source files into $OUTPUT_FILE..."
echo "" > "$OUTPUT_FILE"  # Reset file

# List of [absolute_file_path|description]
files=(
  "$HOME/mapem/frontend/genealogy-frontend/src/components/MapView.jsx|Main Leaflet map"
  "$HOME/mapem/frontend/genealogy-frontend/src/components/Sidebar.jsx|Filtering logic + sidebar UI"
  "$HOME/mapem/frontend/genealogy-frontend/src/components/Legend.jsx|Map icon meanings + toggles"
  "$HOME/mapem/frontend/genealogy-frontend/src/components/Header.jsx|Tree selector + theme toggle"
  "$HOME/mapem/frontend/genealogy-frontend/src/components/PersonPanel.jsx|Click-to-view details"
  "$HOME/mapem/backend/routes/movements.py|API to return movement paths"
  "$HOME/mapem/backend/utils/geopoints.py|Add path smoothing, etc."
  "$HOME/mapem/frontend/genealogy-frontend/src/styles/theme.css|Color, typography tokens"
)

# Loop to grab content
for entry in "${files[@]}"; do
  IFS='|' read -r path desc <<< "$entry"

  echo "📄 File: $path" >> "$OUTPUT_FILE"
  echo "🔍 Purpose: $desc" >> "$OUTPUT_FILE"
  echo "----------------------------------------" >> "$OUTPUT_FILE"

  if [ -f "$path" ]; then
    cat "$path" >> "$OUTPUT_FILE"
  else
    echo "⚠️ File not found: $path" >> "$OUTPUT_FILE"
  fi

  echo -e "\n\n" >> "$OUTPUT_FILE"
done

echo "✅ Code dump complete. Check here 👉 $OUTPUT_FILE"
