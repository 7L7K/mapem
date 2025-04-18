const fs = require('fs');

const isValidLatLng = (lat, lng) => {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 && lat <= 90 &&
    lng >= -180 && lng <= 180
  );
};

const data = JSON.parse(fs.readFileSync('./movements.json', 'utf-8'));

let badCount = 0;

data.forEach((m, i) => {
  if (!isValidLatLng(m.lat, m.lng)) {
    console.log(`❌ Invalid coords at index ${i}:`, m);
    badCount++;
  }
});

console.log(`✅ Done. Found ${badCount} invalid entries.`);

