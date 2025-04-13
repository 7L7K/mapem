#!/bin/bash

# Save this as dump_backend_files.sh and run it from the root of your project

OUTPUT="backend_code_dump.txt"
> "$OUTPUT"

echo "🧠 Dumping key backend files to: $OUTPUT"
echo "=====================================================" >> "$OUTPUT"
echo "📂 backend/scripts/geocode_missing_locations.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/scripts/geocode_missing_locations.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo -e "\n=====================================================" >> "$OUTPUT"
echo "📂 backend/app.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/app.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo -e "\n=====================================================" >> "$OUTPUT"
echo "📂 backend/routes/upload_tree.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/routes/upload_tree.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo -e "\n=====================================================" >> "$OUTPUT"
echo "📂 backend/geocode.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/geocode.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo -e "\n=====================================================" >> "$OUTPUT"
echo "📂 backend/db.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/db.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo -e "\n=====================================================" >> "$OUTPUT"
echo "📂 backend/models.py" >> "$OUTPUT"
echo "=====================================================" >> "$OUTPUT"
cat backend/models.py >> "$OUTPUT" 2>/dev/null || echo "[FILE MISSING]" >> "$OUTPUT"

echo "✅ Dump complete! File saved as $OUTPUT"

