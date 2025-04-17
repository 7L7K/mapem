# 📍 MapEm Location Cleanup Guide (Mississippi Case Study)

This guide documents the common issues, fixes, and best practices when cleaning location data from GEDCOM files. It is based on deep auditing of Mississippi-related entries from the Eichelberger Tree upload.

---

## ✅ CLEANUP CHECKLIST

| Task | Description |
|------|-------------|
| **Normalize spacing & casing** | Fix all-caps (`MISSISSIPPI → Mississippi`), remove extra spaces and double commas |
| **Collapse duplicates** | Standardize `"Choctaw, MS"` as `"Choctaw County, Mississippi"` |
| **Resolve 'Beat' entries** | Link `Beat X` to known cities and counties (from 1910–1930 census maps) |
| **Fix broken strings** | Add missing commas, remove question marks and typos |
| **Accept valid vague entries** | `"Mississippi"` or `"Mississippi, USA"` accepted if no other info available |
| **Reject/flag placeholders** | Discard or log `"USA"`, `"UNKNOWN"`, or `", ,"` formats |
| **Patch known typos** | `"Attla"` → `Attala`, `"mcool"` → `McCool`, `"mississppi"` → `Mississippi` |
| **Deduplicate entries** | Remove redundant fragments like `"Beat 3, Beat 3"` |
| **Cross-reference with context** | Use surname, family unit, and date to guess vague locations |
| **Log unresolved** | Output unresolved or fuzzy entries to `unresolved_locations.json`

---

## 🔍 PROBLEMS FOUND (Real Examples)

### 🔴 1. Vague/Generic
- `"Mississippi"` (500+ people) — too broad unless tied to early 1800s events
- `"Mississippi, USA"` — accepted in GEDCOMs but generic

### 🟠 2. Broken/Malformed
- `"McCool Mississippi  Attala USA"` — no commas
- `", , Mississippi"` — empty segments
- `"Mississippi, USA ?"` — invalid suffix

### 🟣 3. Complex Beats
- `"Beat 1, Hattiesburg, Forrest, Mississippi"` — ✅ useful
- `"Beat 3, Beat 3, Madison, Mississippi"` — ❌ redundant
- `"Beat 4"` — vague without county

### 🟡 4. Duplicates
- `"Ackerman, Choctaw, Mississippi"`  
- `"Ackerman, Choctaw County, Mississippi, USA"`  
- ➜ all mapped to: `Ackerman, Choctaw County, Mississippi`

### 🟤 5. Misspelled
- `"Attla"` → `Attala`
- `"mississppi"` → `Mississippi`
- `"Canton Madis"` → `Canton, Madison County`

---

## 💡 Best Practices for Future Cleanup Scripts

- Build a lookup table for:
  - Beat-to-county mappings
  - Typos → corrections
  - Cities → counties
- Use regex to find:
  - Duplicated words (`Beat 2, Beat 2`)
  - Broken comma patterns
- Apply fuzzy matching to similar strings (`mcool` ≈ `McCool`)
- Auto-log unmatched into `unresolved_locations.json`
- Attach timestamps, tree_id, and source tag (BIRT, DEAT) when logging

---

## 📁 Folder Suggestions for Project

- `data/manual_place_fixes.json` — manual overrides
- `data/unresolved_locations.json` — log unresolved entries
- `docs/location_cleanup_guide.md` — this file
- `scripts/fix_locations.py` — CLI tool for batch cleaning

---

## ✅ Sample Normalized Output

```json
{
  "raw": "McCool Mississippi  Attala USA",
  "normalized": "McCool, Attala County, Mississippi",
  "status": "resolved",
  "source_tag": "BIRT",
  "tree_id": 1
}
