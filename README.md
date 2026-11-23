# CMLab website

Static website for the Creative Vision & Multimedia Lab at Chung-Ang University. The site uses editable JSON catalogs and supports dark and light themes. It requires no build dependencies.

## Local preview

Run `python3 -m http.server 8000` from the repository root, then open `http://localhost:8000`. Serving over HTTP allows the browser to load the JSON data. The custom 404 page uses root-relative navigation for the organization's root GitHub Pages site.

## Content maintenance

| File | Content |
| --- | --- |
| `data/publications.json` | Titles, authors, venues, catalog numbers, research areas, links and teaser paths |
| `data/publication-archive.json` | Numbered regional publications, software registrations and patents |
| `data/projects.json` | Projects, roles, funding organizations and YYYY-MM project dates |
| `data/people.json` | Directly supervised graduate researchers and interns |
| `data/collaborators.json` | People, affiliations and associated projects |
| `data/news.json` | Selected news |
| `data/media-migration.json` | Original project asset paths, revisions, licenses and adaptations |

The preview bundles the lab's official logo from the [branding repository](https://github.com/CMLab-Korea/cmlab-web-assets/tree/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/branding). Media credits and source links are in the migration manifest. Publication and career-wide PI Scholar metrics load the existing public scripts produced by the [asset repository](https://github.com/CMLab-Korea/cmlab-web-assets). Publication counts fall back to the bundled snapshot, and unavailable Scholar values display an em dash.

## Home updates

Home selects two preprints and two peer-reviewed papers from the first six of each group in `data/publications.json`. Keep the catalog in publication order. Titles, links, posters and videos come from the same entries as Publications.

Add news to `data/news.json` with a `YYYY-MM` date, headline, and category. Use `YYYY-MM-DD` for the lab opening entry. Use Publication, Award, Funding, People, Event, or Service as applicable. Keep an optional `source_url` for editorial verification. Home displays the latest ten entries and offers the rest when available.

Home’s Research Vision figure uses responsive WebP derivatives and links to the original-resolution image. The asset repository file has a PNG extension and contains JPEG data. [Source figure](https://github.com/CMLab-Korea/cmlab-web-assets/blob/272aab0f610ca1f5fd5a2d5635cb4ceb9f4d99e6/research/01-%5B26.10%5D%20CMLab%20Research%20Areas.png)

## Publications migration

`data/publications.json` is the editable site catalog. Keep the stable paper ID and list order. Keep the original C/J number in `catalog_number` on peer-reviewed entries. Store the full title separately from the optional `short` nickname. Store official, project, arXiv, code and dataset links in their corresponding URL fields. Use `areas` for the research tags and `teaser` / `teaser_video` for the verified publication media. Home reads the same catalog.

`scripts/collect_cmlab_sources.py` captures rendered source HTML and structured evidence. Run it in a Python environment with Playwright Chromium installed and pass `--output capture`. For Chrome exports, pass `--publications-html`, `--home-html` or `--lab-html` with the saved page file. Review the candidates against their source HTML before transferring them into the catalog. The Actions run retains the HTML in its archive.

After the catalog is complete and approved, migrate the Home At a Glance publication counts to `data/publications.json` before retiring the legacy site. Keep the career-wide PI citation metrics and venue metrics distinct.

## Projects and media

- Keep display names, aliases, contact links, portraits and semesters in `data/people.json`. Keep collaborator profile links and their institution IDs in `data/collaborators.json` and institution marks in `data/institutions.json`. Papers link authors and People lists collaborative work by matching the catalog’s bylines to those names and aliases. Publication logos correspond to source affiliations tracked on the paper.
- Place a paper poster called `teaser.webp` (GIF and other browser-readable image formats are supported) and optional `preview.mp4` in `assets/media/publications/paper-<id>/`. The ID is the stable number in `data/publications.json`. Prepare media at a 16:10 ratio when practical.
- Keep the original project IDs in `data/projects.json`. Start and end months are inclusive in Asia/Seoul. Home, Publications and Projects use the same active-project count. Project organization logos are in `assets/img/project-orgs/`.
- Add numbered photo files such as `01.webp` and `02.webp` to the matching folder in `assets/img/gallery/`. The folder name matches the event ID in `data/gallery.json`. Gallery controls appear when an event has more than one image.
- GitHub Pages packaging indexes paper media automatically. To preview new uploads locally, run `python3 scripts/index_site_media.py --publications-only`. Run without the option to index gallery photos as well. Teaching records and the university’s Outstanding Instructor links live in `data/courses.json`.

## Visitor statistics

The footer supports total and daily visitor counts and a public country and page breakdown. Follow the [Korean dashboard walkthrough](analytics/SETUP_KO.md) or connect the [visitor counter backend](analytics/README.md) and set its HTTPS endpoint in `data/visitor-settings.json` to enable live counts.

## Release review

See [REVIEW.md](REVIEW.md) for confirmed source matches and open checks. Follow [AGENTS.md](AGENTS.md) for ongoing updates.

After approval, select GitHub Actions as the Pages source for the website repository if needed. The included workflow deploys only from `main`. Review the deployment and verify the root website, a missing URL, and live metric loading before considering any legacy-site migration. University DNS and the legacy site remain outside this release.
