# Artifact Radar — Evidence Snapshots

Artifact Radar v7 stores structured observation snapshots under this directory.

Each `<record_fingerprint>.json` keeps up to 12 distinct observed states for that source/artifact record.

Snapshots may include:
- source/page title
- meta description
- image URLs
- page price text and currency
- provenance-related excerpt
- deterministic evidence/risk fields
- source status, HTTP status and content hash
- observation timestamps

These snapshots are technical observations. A detected change does not establish intent, deletion, illicit activity, or misconduct. Dynamic pages, localisation, advertising, redesigns, or other legitimate updates can cause differences.

The crawler commits snapshot files through GitHub Actions alongside `data.json`, `history.json`, and `source_history.json`.
