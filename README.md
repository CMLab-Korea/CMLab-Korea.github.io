# CMLab website

Static website for the Creative Vision & Multimedia Lab at Chung-Ang University. The site uses editable JSON catalogs and supports dark and light themes. It requires no build dependencies.

## Local preview

Run `python3 -m http.server 8000` from the repository root, then open `http://localhost:8000`. Serving over HTTP allows the browser to load the JSON data. The custom 404 page uses root-relative navigation for the organization's root GitHub Pages site.

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

The preview bundles the lab's official logo from the [branding repository](https://github.com/CMLab-Korea/cmlab-web-assets/tree/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/branding). Media credits and source links are in the migration manifest. Publication and career-wide PI Scholar metrics load the existing public scripts produced by the [asset repository](https://github.com/CMLab-Korea/cmlab-web-assets). Publication counts fall back to the bundled snapshot, and unavailable Scholar values display an em dash.

## Home updates

Home selects two preprints and two peer-reviewed papers from the first six of each group in `data/publications.json`. Keep the catalog in publication order. Titles, links, posters and videos come from the same entries as Publications. Set `manuscripts_in_preparation` in `data/research-output.json` to update both Home and Publications.

Add news to `data/news.json` with a `YYYY-MM` or `YYYY-MM-DD` date, headline, and category. The site displays the month and year. Entries in the same month follow catalog order. The lab opening entry uses `show_day` to display its original date. Use Publication, Award, Funding, People, Event, or Service as applicable. Keep an optional `source_url` for editorial verification. Home displays the latest ten entries and offers the rest when available.

Home’s Research Vision figure uses responsive WebP derivatives and links to the original-resolution image. The asset repository file has a PNG extension and contains JPEG data. [Source figure](https://github.com/CMLab-Korea/cmlab-web-assets/blob/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/research/01-%5B26.10%5D%20CMLab%20Research%20Areas.png)

## Publications migration

`data/publications.json` is the editable site catalog. Keep the stable paper ID and list order. Keep the original C/J number in `catalog_number` on peer-reviewed entries. Store the full title separately from the optional `short` nickname. For a new or substantially updated manuscript, set `listed_on` to the date CMLab lists it. The site prioritizes manuscripts with Jihyong Oh as last and corresponding author, then newer listings. Use `*` for equal contribution and `+` or `†` for corresponding authors. Set `use_current_collaborator_affiliations` when the paper should derive institution badges from its coauthors in the Research Network. Store official, project, arXiv, code and dataset links in their corresponding URL fields. Use `areas` for the research tags and `teaser` / `teaser_video` for the verified publication media. Home reads the same catalog.

`scripts/collect_cmlab_sources.py` captures rendered source HTML and structured evidence. Run it in a Python environment with Playwright Chromium installed and pass `--output capture`. For Chrome exports, pass `--publications-html`, `--home-html` or `--lab-html` with the saved page file. Review the candidates against their source HTML before transferring them into the catalog. The Actions run retains the HTML in its archive.

After the catalog is complete and approved, migrate the Home At a Glance publication counts to `data/publications.json` before retiring the legacy site. Keep the career-wide PI citation metrics and venue metrics distinct.

## Projects and media

- Keep display names, aliases, contact links, portraits and semesters in `data/people.json`. Keep collaborator profile links and their institution IDs in `data/collaborators.json` and institution marks in `data/institutions.json`. Papers link authors and People lists collaborative work by matching the catalog’s bylines to those names and aliases. Publication logos correspond to source affiliations tracked on the paper.
- Upload paper media to its full-title folder under [assets/media/publications](assets/media/publications). Each card uses up to one image and one video. For multiple candidates, `teaser.*` and `preview.*` take precedence, then the first filename in natural order. Prepare media at a 16:10 ratio when practical.
- Keep the original project IDs in `data/projects.json`. Start and end dates or months are inclusive in Asia/Seoul. Use `YYYY-MM-DD` when the exact period is known. Cards display the month and year. Project organization logos are in `assets/img/project-orgs/`.
- Upload Lab Life images and videos to the event-title-and-date folder under [assets/img/gallery](assets/img/gallery). Number files to set the order, such as `01.jpg`, `02.mp4`, and `03.webp`. Gallery controls appear when an event has multiple items.
- Both catalogs accept PNG, JPEG, WebP, GIF, AVIF, MP4, and WebM. Publication folders also accept MOV uploads. Use GitHub's **Add file → Upload files** and merge to `main`. GitHub Pages indexes the files automatically. The Pages build uses FFmpeg to prepare browser-compatible MP4 previews from MOV and standalone animated GIFs while keeping the original uploads in place.
- Publication videos start silently when their cards come into view and loop. Use the player controls to pause a preview. The page respects the device's reduced-motion setting.
- For a new paper or event, add its record to the catalog, run `python3 scripts/index_site_media.py --sync-folders`, and commit the generated folder with the record. The catalog stores the folder name in `media_folder` so title edits can retain the existing upload path. Folder names use hyphens in place of reserved punctuation such as `:` and `/`.
- For Eunseong Cho, upload one file named `eunseong-cho.png`, `eunseong-cho.jpg`, or `eunseong-cho.webp` to `assets/img/people/`. GitHub Pages packaging indexes the portrait automatically.
- Run `python3 scripts/index_site_media.py` to preview media uploads locally. Use `--publications-only` to index the paper catalog on its own. To generate the same MOV and GIF previews as Pages, copy the site files to a staging folder and index that folder with `--for-deploy --site-dir`. FFmpeg and FFprobe are required for that build. Teaching records and the university’s Outstanding Instructor links live in `data/courses.json`.

## Visitor statistics

The footer supports total and daily visitor counts and a public country and page breakdown. Follow the [Korean dashboard walkthrough](analytics/SETUP_KO.md) or connect the [visitor counter backend](analytics/README.md) and set its HTTPS endpoint in `data/visitor-settings.json` to enable live counts.

## Release review

See [REVIEW.md](REVIEW.md) for confirmed source matches and open checks. Follow [AGENTS.md](AGENTS.md) for ongoing updates.

After approval, select GitHub Actions as the Pages source for the website repository if needed. The included workflow deploys only from `main`. Review the deployment and verify the root website, a missing URL, and live metric loading before considering any legacy-site migration. University DNS and the legacy site remain outside this release.
