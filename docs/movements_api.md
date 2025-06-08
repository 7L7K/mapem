# Movements API

`GET /api/movements/<treeId>` now accepts extra query parameters to narrow or group
results.

### Parameters
- `personIds` – comma separated list of individual ids to limit the query.
- `familyId`  – id of a family; all members are included automatically.
- `grouped`   – if set to `person` or `family`, movements are returned grouped
  by that entity instead of a flat list.

Other existing filters (eventTypes, year range, etc.) remain unchanged.
