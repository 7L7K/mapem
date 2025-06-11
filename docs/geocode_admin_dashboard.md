# Geocode Admin Dashboard (v2 Plan)

This file outlines upcoming improvements for the geocode admin dashboard. The
notes below are extracted from design discussions and serve as a quick reference
for future development.

## SECTION 4: Data Audits + Deep Dives

Optional but great for diagnostics.

### 4a. Top Failing Places
List of most frequent unresolved names:

| Raw Name      | Count |
|---------------|------:|
| "Beat 2"      | 8     |
| "Boliver, MS" | 6     |

### 4b. Source Breakdown
Display a pie or bar chart of unresolved entries broken down by source:

- From GEDCOM
- From Census
- Manual entry
- AI suggestions

## SECTION 5: Batch Actions

Tools to speed up the admin workflow:

- 🔄 **Retry unresolved** using `fix_and_retry.py`
- 🧠 **Run fuzzy matching** on unresolved names
- 📤 **Export unresolved list** (JSONL/CSV)
- 📥 **Upload manual fixes** (load a new `manual_place_fixes.json`)
- 📊 **See retry success/fail counts**

## SECTION 6: Optional Permissions / Auth

If user accounts are added in the future:

- Restrict access to this dashboard unless `admin=True`
- When manual fixes are applied, log the username so changes are traceable

