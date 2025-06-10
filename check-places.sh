#!/bin/bash
places=(
  "compton, los angeles county, california, united states"
  "elwood, will county, illinois, united states"
  "moorehead lake dam, grenada county, mississippi, 38940, united states"
  "h w morehead road, scott county, mississippi, 39152, united states"
)

echo "raw,latitude,longitude,normalized,status"
for p in "${places[@]}"; do
  echo "Querying: $place"
  q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$p'''))")
  out=$(curl -s "http://localhost:5050/api/geocode?place=$q")
  lat=$(echo "$out" | jq -r '.latitude // ""')
  lng=$(echo "$out" | jq -r '.longitude // ""')
  norm=$(echo "$out" | jq -r '.normalized // ""')
  stat=$(echo "$out" | jq -r '.status')
  # escape commas in raw
  raw_esc=${p//,/\\,}
  echo "$raw_esc,$lat,$lng,$norm,$stat"
done
