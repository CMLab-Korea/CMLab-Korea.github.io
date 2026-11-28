# CMLab website

Static website for the Creative Vision & Multimedia Lab at Chung-Ang University. The site uses editable JSON catalogs and supports dark and light themes. It requires no build dependencies.

## Local preview

Run `python3 -m http.server 8000` from the repository root, then open `http://localhost:8000`. Serving over HTTP allows the browser to load the JSON data. The custom 404 page uses root-relative navigation for the organization's root GitHub Pages site.

## Data security

1. Manage data according to the current repository's visibility and access permissions.
2. Store only lab materials approved for public release in a public repository.
3. Keep personal materials, internal strategy documents, evaluation materials, unpublished documents, and access-restricted data out of this repository and its sync workflows.
4. Treat every branch, hidden folder, GitHub Actions artifact, issue, pull request, and commit message in a public repository as potentially public.
5. Before importing data from an external repository, confirm that public release and synchronization are both authorized.
6. Keep API keys, tokens, credentials, and sensitive raw data out of Git commits.
7. Verify the destination repository and its visibility before transferring or pushing data to it.
8. Copy or combine data across workspaces with different access permissions only with explicit authorization.
9. Obtain authorization before deleting existing data or user work or changing repository visibility.
10. If a security issue is suspected, stop automated deployments and pushes and notify the user.

## Content maintenance

| File | Content |
| --- | --- |
| `data/publications.json` | Titles, authors, venues, catalog numbers, research areas, links and teaser paths |
| `data/publication-archive.json` | Numbered regional publications, software registrations and patents |
| `data/projects.json` | Projects, roles, funding organizations and project dates |
| `data/people.json` | Directly supervised graduate researchers and interns |
| `data/collaborators.json` | People, affiliations and associated projects |
| `data/news.json` | Selected news |
| `data/media-migration.json` | Original project asset paths, revisions, licenses and adaptations |

The preview bundles the lab's official logo from the [branding repository](https://github.com/CMLab-Korea/cmlab-web-assets/tree/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/branding). Media credits and source links are in the migration manifest. Home and Publications calculate their counts from the deployed publication catalog. Home loads career-wide PI Scholar metrics from the [asset repository](https://github.com/CMLab-Korea/cmlab-web-assets) and shows an em dash if those metrics are unavailable.

## Home updates

Home selects two preprints and two peer-reviewed papers from the first six of each group in `data/publications.json`. Keep the catalog in publication order. Titles, links, posters and videos come from the same entries as Publications. Set `manuscripts_in_preparation` in `data/research-output.json` to update both Home and Publications.

Add news to `data/news.json` with a `YYYY-MM` or `YYYY-MM-DD` date, headline, and category. The site displays the month and year. Entries in the same month follow catalog order. The lab opening entry uses `show_day` to display its original date. Use Publication, Award, Funding, People, Event, or Service as applicable. Keep an optional `source_url` for editorial verification. Home displays the latest ten entries and offers the rest when available.

Home’s Research Vision figure uses responsive WebP derivatives and links to the original-resolution image. The asset repository file has a PNG extension and contains JPEG data. [Source figure](https://github.com/CMLab-Korea/cmlab-web-assets/blob/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/research/01-%5B26.10%5D%20CMLab%20Research%20Areas.png)

## Publications migration

`data/publications.json` is the editable site catalog. Keep each paper's stable numeric `id`, original C/J catalog number, full title and optional `short` nickname. For a new or substantially updated manuscript, set `listed_on` to the listing date. The catalog gives priority to papers with Jihyong Oh as last and corresponding author, then newer listings, and numbers this section from `U1` at the bottom. A verified `arxiv_url` or `project_url` changes its label from Manuscript to Preprint. Use `*` for equal contribution and `+` or `†` for corresponding authors. Set `use_current_collaborator_affiliations` when the paper should derive institution badges from its coauthors in the Research Network. Use `areas` for the research tags and `teaser` / `teaser_video` for verified media. Home reads the same catalog.

For a publication news item, use `publication_updates` with the existing paper IDs, verified links, and an optional acceptance. Each acceptance moves that paper to Peer-reviewed Publications, assigns the next C or J number, and moves its upload folder while retaining existing Pages media URLs. Keep the announcement and catalog changes together by running `python3 scripts/sync_publications.py` before committing. The Pages workflow applies the same sync to the deployment copy after a merge. Commit any source catalog and folder changes through a pull request. In the news headline, link the paper nickname to its project page when available and the venue name to the venue website. The deployment run summary lists any numbers assigned during packaging.

```json
{
  "date": "2027-02",
  "category": "Publication",
  "headline": ["Example Paper has been accepted to Example Conference 2027."],
  "publication_updates": [
    {
      "id": 123,
      "acceptance": {
        "type": "Conference",
        "venue": "Example Conference",
        "venue_short": "ExampleConf'27",
        "year": 2027
      }
    }
  ]
}
```

Use `Journal` for a journal acceptance. For a release announcement, add only the paper ID and the new `arxiv_url` or `project_url`. Put an official paper page in `venue_url` once it is public.

`scripts/collect_cmlab_sources.py` captures rendered source HTML and structured evidence. Run it in a Python environment with Playwright Chromium installed and pass `--output capture`. For Chrome exports, pass `--publications-html`, `--home-html` or `--lab-html` with the saved page file. Review the candidates against their source HTML before transferring them into the catalog. The Actions run retains the HTML in its archive.

The Pages build excludes legacy-site and captured Google Sites image references from editorial source fields in the staged catalog. The source files in this repository retain those references for migration records. Keep the career-wide PI citation metrics and venue metrics distinct.

## Projects and media

- Keep display names, aliases, contact links, portraits and semesters in `data/people.json`. Keep collaborator profile links and their institution IDs in `data/collaborators.json` and institution marks in `data/institutions.json`. Papers link authors and People lists collaborative work by matching the catalog’s bylines to those names and aliases. Publication logos correspond to source affiliations tracked on the paper.
- Upload paper media to its numbered full-title folder under [assets/media/publications](assets/media/publications). The first number sorts the folder in the same order as the website. The bracketed U, C or J number is the paper's catalog label. The current upload path is in `media_folder`. Each card uses up to one image and one video. For multiple candidates, `teaser.*` and `preview.*` take precedence, then the first filename in natural order. Prepare media at a 16:10 ratio when practical.
- Keep the original project IDs in `data/projects.json`. Start and end dates or months are inclusive in Asia/Seoul. Use `YYYY-MM-DD` when the exact period is known. Cards display the month and year. Project organization logos are in `assets/img/project-orgs/`.
- Upload Lab Life media to its numbered event folder under [assets/img/gallery](assets/img/gallery). The leading sort number follows newest-first display order, and the bracketed L number starts with the oldest event. Use filenames such as `01.jpg`, `02.HEIC`, and `03.webp` to set the order. The first file opens the album. Multiple items rotate every three seconds, and the album has pause, previous, and next controls. Pages converts HEIC, HEIF, TIFF, BMP, JPEG XL, and JPEG 2000 uploads to browser previews.
- For Lab Life, use `YYYY-MM-DD` or `YYYY-MM` in `date`, plus `end_date` for a range. Keep each event ID stable. Use `title`, `location` and `summary` for the English card, and optional `title_ko` and `summary_ko` for the expanded album. Add verified `participants` using their People names, and use `links` entries containing `paper_id` to resolve publication project and venue links. Add `venue_url` or `venue_label` to override the default venue link or label where appropriate.
- Both catalogs accept PNG, JPEG, WebP, GIF, AVIF, MP4, and WebM. Publication folders also accept MOV, M4V, MKV, AVI, MPG, MPEG, OGV, and WMV. Use GitHub's **Add file → Upload files** and merge to `main`. GitHub Pages indexes the files automatically and prepares compatible MP4 previews for these additional video formats and standalone animated GIFs.
- Publication videos start silently when their cards come into view and loop. Use the player controls to pause a preview. The page respects the device's reduced-motion setting.
- For a new paper or event, add its record to the catalog, run `python3 scripts/index_site_media.py --sync-folders`, and commit the generated folder with the record. Folder names use hyphens in place of reserved punctuation such as `:` and `/`.
- For Eunseong Cho, upload one file named `eunseong-cho.png`, `eunseong-cho.jpg`, or `eunseong-cho.webp` to `assets/img/people/`. GitHub Pages packaging indexes the portrait automatically.
- Run `python3 scripts/index_site_media.py` to preview media uploads locally. Use `--publications-only` to index the paper catalog on its own. To generate the same MOV and GIF previews as Pages, copy the site files to a staging folder and index that folder with `--for-deploy --site-dir`. FFmpeg and FFprobe are required for that build. Teaching records and the university’s Outstanding Instructor links live in `data/courses.json`.

## Visitor statistics

The footer supports total and daily visitor counts and a public country and page breakdown. Follow the [Korean dashboard walkthrough](analytics/SETUP_KO.md) or connect the [visitor counter backend](analytics/README.md) and set its HTTPS endpoint in `data/visitor-settings.json` to enable live counts.

## Release review

See [REVIEW.md](REVIEW.md) for confirmed source matches and open checks. Follow [AGENTS.md](AGENTS.md) for ongoing updates.

After approval, select GitHub Actions as the Pages source for the website repository if needed. The included workflow deploys only from `main`. Review the deployment and verify the root website, a missing URL, and live metric loading before considering any legacy-site migration. University DNS and the legacy site remain outside this release.

## Journal metrics maintenance

`data/journals.json` is the public source of truth for journal identity, year-specific SCIE evidence and approved JCR editions. Only published journal papers receive metric badges or count toward the metrics overview. The overview is visible once at least one published paper has eligible data. The site uses one explicit edition for all journals (`2025` data, `2026` release initially). An edition lacking a verified, approved, complete record for a journal displays no value for that journal. Existing paper records, Scholar metrics and historical IF notes in `source_venue` remain independent.

- To add a journal, add a stable `journal_id`, official name, verified aliases, ISSN/eISSN where known, and public bibliographic provenance. Set `verification_status` to `verified` only after checking the source and record the date. Use empty `scie` and `metrics` arrays for unavailable evidence. Enter SCIE evidence separately by year, with `status` set to `indexed` or `not_indexed`, verification date, source, public URL and explicit approval. The publication matcher checks explicit ID, supplied ISSN/eISSN, official name, then aliases. Keep a mapping manual if it cannot be resolved unambiguously.
- Fill [the CSV template](docs/jcr-metrics-template.csv) with **one row per category per journal, year and revision**. See the [column guide](docs/jcr-metrics-input.md) for optional fields and formats. Use the general S2Journal JCR ranking (`source=S2Journal`, `ranking=jcr`). A CSV or XLSX export can be imported after projecting its approved fields into the template headers. XLSX uses the `JCR` sheet or the active sheet and requires `openpyxl`. CSV needs Python's standard library only. Release/revision dates, rank, total and official percentile may be blank when unavailable. Use an HTTPS public source URL without login tokens or query strings.
- Before sharing or importing, confirm the right to publish **each** field, including category data and any derived or exported values. Keep vendor originals and evidence files in an approved private environment. Use `verification_status=verified` and `public_authorized=true` only for reviewed, publishable values. Supply the total source category count and mark the record `partial` if any category is absent. A partial record remains historical data and does not produce a representative badge.
- Run `python3 -B scripts/import_journal_metrics.py /path/to/approved.csv` for a dry-run diff. It rejects extra columns, ambiguous or new journal mappings, unapproved rows and invalid values. Run with `--apply` only after review. Use `python3 -B scripts/validate_journal_metrics.py` to check the registry and report journal mapping and metric coverage.
- Add each annual release as a new data year and keep prior years. For a correction, enter a higher revision, with the actual revision date if known, and include the complete replacement set of category rows. Set `public_edition` once for the website after review. JIF and the selected category's original S2Journal IF(%), rank and quartile come from that edition. Official JIF percentile and the computed rank percentage are separate fields. The program uses `100 − official percentile` only for the official top-percent representation.
- Future exports can reuse the selectors in `assets/js/journal-metrics.js` for the configured common edition, an explicit historical year, a publication's year, or the edition and revision available on an ISO cutoff date. The date-based lookup needs authoritative release/revision dates. Preserve the selected edition, revision and category as report metadata. Report exports require their own license and disclosure check.

For the SCIE evidence checklist, public label policy and private-to-public review process, see [SCIE and disclosure review](docs/jcr-publication-review.md).

Site staging validates `data/journals.json` and copies the existing allowlisted site directories. Keep fixtures in `tests/` and approved import templates in `docs/`; neither directory is staged for Pages.
