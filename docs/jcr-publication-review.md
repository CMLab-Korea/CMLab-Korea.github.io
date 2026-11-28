# SCIE evidence and JCR disclosure review

Publication-year SCIE evidence and the site's common JCR edition are independent. The summary counts all Journal records as general journal papers. It uses **SCIE-INDEXED JOURNAL PAPERS** only when every journal paper in that total is published and has verified, publicly approved indexed status for its own publication year. When the catalog changes, the label is evaluated again. Accepted papers remain in the catalog and its general totals, and are excluded from the published JCR overview, badge and metrics counts.

## Publication-year evidence checklist

Check each year against a dated Clarivate coverage record or another authoritative source that explicitly identifies the SCIE collection, journal and year. A current list entry or a publisher's current indexing page does not establish historical coverage. At this review, public-source requests from the workspace returned HTTP 403. All evidence below remains unconfirmed.

| Journal | Publication years | Catalog records | Lookup starting points |
|---|---|---|---|
| IEEE TPAMI | 2025, 2026 | J4, J8 | [IEEE Computer Society](https://www.computer.org/csdl/journal/tp), ISSN 0162-8828 |
| IEEE TCSVT | 2021, 2026 | J1, J7 | [IEEE Xplore](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=76), ISSN 1051-8215 |
| Neurocomputing | 2025, 2026 | J3, J5, J6 | [ScienceDirect](https://www.sciencedirect.com/journal/neurocomputing), ISSN 0925-2312 |
| Remote Sensing | 2021 | J2 | [MDPI](https://www.mdpi.com/journal/remotesensing/indexing), eISSN 2072-4292 |

[Clarivate Master Journal List](https://mjl.clarivate.com/home) is a lookup starting point. Keep dated evidence in an approved private workspace. Enter a year-specific registry record only once the status and evidence are verified and its public disclosure is approved. Keep unknown years absent, and use `not_indexed` only when supported by verified evidence.

## Private staging to public projection

1. Keep S2Journal exports, screenshots and notes in the approved private workspace. Have the owner record the source, review date, rights decision and permitted fields for the website and any export destination. Possession of the source data does not establish publishing rights.
2. For the 2025 JCR data / 2026 release, check the owner-reported category counts against the source: TPAMI 2, TCSVT 1, Neurocomputing 1, Remote Sensing 4. Verify every Category individually. Leave rank, total and official JIF percentile blank when unavailable. Do not mark a partial Category set complete.
3. Copy only verified and permitted fields into the [CSV template](jcr-metrics-template.csv), one row per Category. Retain the evidence for the approval in the private workspace. Set `public_authorized=true` only after the owner has confirmed that the row's proposed fields and source reference may be disclosed publicly. The importer requires this decision and cannot grant it.
4. Run the import dry-run on the **approved projection** and inspect the diff before applying. Review the public JSON and stage only approved changes through a PR. Keep restricted values out of the repository, PR, Actions logs and Pages artifacts.

See the [input guide](jcr-metrics-input.md) for the column formats and dry-run command.
