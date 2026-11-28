# JCR data entry guide

Download the [blank CSV template](jcr-metrics-template.csv). Prepare UTF-8 CSV or an XLSX sheet named `JCR` with identical headers. Use one row per Category and repeat journal edition metadata across its rows. All sample values below illustrate formats only. Use the general S2Journal JCR ranking.

| Column | Requirement | Meaning and example |
|---|---|---|
| `journal_id` | One matching route required | Stable registry identifier, e.g. `ieee-tpami`. Preferred when known. |
| `issn` | Alternative identifier | Print ISSN in `dddd-dddX` format, e.g. `0162-8828`. |
| `eissn` | Alternative identifier | Electronic ISSN, e.g. `1939-3539`. |
| `official_name` | Alternative identifier | Exact official name or registered alias, e.g. `IEEE TPAMI`. |
| `data_year` | Required | JCR data year, e.g. `2025`. |
| `release_year` | Required | JCR release year, e.g. `2026`. |
| `release_date` | Optional | Actual release date as `YYYY-MM-DD`, e.g. `2026-06-20`. |
| `revision` | Required | Positive integer, e.g. `1` for the initial edition and `2` for a correction. |
| `revision_date` | Optional | Actual revision date as `YYYY-MM-DD`; enter when known for as-of-date lookups. |
| `jif` | Required | Nonnegative number from the source, e.g. `8.0` in a test. |
| `category_count` | Required | Total number of categories listed by the source, e.g. `2`. |
| `category_completeness` | Required | `complete` when all source categories are represented; otherwise `partial`. |
| `category` | Required | Exact Category title, e.g. `Synthetic Vision Category` in a test. |
| `rank` | Optional | Reported positive integer rank, e.g. `3`. |
| `total` | Optional | Reported positive integer category size, e.g. `100`. |
| `quartile` | Required | Source quartile, one of `Q1`, `Q2`, `Q3`, `Q4`. |
| `s2_if_percent` | Required | Original S2Journal IF(%) in percent units, e.g. `5.0` or `5.0%`. |
| `jif_percentile` | Optional | Official JIF percentile on a 0–100 scale, e.g. `96.0`. |
| `source` | Required | `S2Journal`. |
| `source_url` | Required | Public HTTPS provenance URL, without query strings, login tokens or fragments. |
| `ranking` | Required | `jcr` for the general JCR ranking. |
| `last_verified` | Required | Actual date of verification as `YYYY-MM-DD`, e.g. `2026-06-21`. |
| `verification_status` | Required | `verified` after checking the source. |
| `public_authorized` | Required | `true` after confirming that the underlying values and the intended disclosure are permitted. |

Supply at least one identifier. Explicit ID takes precedence, then ISSN/eISSN, then official title and aliases. If rank, total or official percentile is unavailable, **leave that cell empty**. A verified, approved, complete set can still use its original S2Journal IF(%) and quartile. The rank-derived percentage stays blank until both rank and total are known. The official top percentage stays blank until the official percentile is known. Completeness refers to the set of categories. Preserve the genuine source values and do not mark a partial set complete.

Run the import in dry-run mode first from the repository root.

```bash
python3 -B scripts/import_journal_metrics.py /path/to/approved.csv
python3 -B scripts/validate_journal_metrics.py
```

Keep source exports and evidence in the approved private environment. Use `--apply` on the reviewed public projection only. For a new edition or correction, preserve previous years and revisions. Update `public_edition` after review when switching the site to a new common edition.
