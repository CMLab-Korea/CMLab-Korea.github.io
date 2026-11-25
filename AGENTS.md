# CMLab Website: Persistent Instructions for Codex

## Purpose
Maintain the official public website of the Creative Vision & Multimedia Lab (CMLab), operated by its PI at Chung-Ang University. Deliver an attractive, fast, accessible, and maintainable research-lab website that attracts excellent prospective graduate students, academic collaborators, and industry partners.

## Source of truth and repositories
- Primary website repository: `CMLab-Korea/CMLab-Korea.github.io` (to be created by the owner if not present).
- Existing media/metrics repository: `CMLab-Korea/cmlab-web-assets`. DO NOT rewrite its existing Actions or data generators without a separate request.
- Existing legacy public website: `https://cmlab.cau.ac.kr/`. Keep this live and unchanged unless the owner explicitly approves a migration and the institution authorizes DNS changes.
- Existing metrics are exposed by public JS assets `https://cmlab-korea.github.io/cmlab-web-assets/data/publication-stats.js` and `.../data/scholar-stats.js`. Do not put API keys into client-side code.
- An initial static HTML/CSS/JS website prototype was produced in the companion ZIP. It is a design and content starting point, not a fully verified canonical database.

## Information architecture
Top level: Home, Research, Publications, People, Join Us, Collaborate.
Secondary content: Lab Life/Gallery and Teaching/Courses. Keep existing contact channels available from appropriate pages and the footer.

## Brand and visual direction
- Dark, modern, high-contrast look, not a direct copy of reference sites.
- Base near-black `#070B17`, CMLab navy `#0D207F`, electric blue `#2962FF`, restrained ice blue `#80A7FF`, occasional accent violet `#8E75FF`.
- Official logo should use the existing brand asset in `cmlab-web-assets/branding/`.
- Preserve fast page loads and provide responsive mobile layouts, keyboard access, readable typography, reduced-motion support, and meaningful alt text.
- Use actual verified CMLab paper teasers, images, GIFs or MP4s. Never depict stock images as real laboratory output. Prioritize poster images and lazy load / pause offscreen video loops.

## Research areas (exact names)
1. Pixel-Level Intelligence
2. Video & Motion Intelligence
3. 3D/4D World Modeling
4. Generative & Agentic Visual AI
Real-World AI Systems and Industry Translation is a cross-cutting application direction.

## People
- Show current directly supervised graduate researchers and research interns only, subject to checking names against up-to-date official records. Previously published count was 8 direct graduate students and 3 interns, but this is a snapshot requiring verification.
- DO NOT reinstate the previously listed 11 co-supervised students from Prof. Eom's lab. The PI explicitly requested their removal because direct co-supervision is no longer active.
- Give individuals correct links, lab roles, and research interests only when verified.
- Collaborators should be grouped by affiliation using verified institutions and people. Institutional logos must not imply formal institutional partnership without supporting evidence.

## Publications
- Source is the CMLab legacy Publications page. Snapshot: 28 peer-reviewed papers (20 top-tier conference, 8 international journal) + 10 under-review/preprints (Nov 2026). Reverify counts before promoting to current facts.
- Venue at left (e.g. CVPR '26); small verified teaser/poster/MP4 at center; title, authors, venue distinction, year, Paper/Project/Code links, optional collaboration affiliation chips at right.
- Highlight CMLab student first/co-first authors and the PI based on verified authorship. Preserve equal-contribution and corresponding-author symbols where known. Do not infer co-authorship roles.
- Prefer 'SCIE-indexed Journal Papers' only when all included journals are verified to meet that definition. Otherwise use 'Journal Papers'.
- Search, year/venue/research-area filters, load performance, structured JSON content and accurate metadata are priorities.

## Metrics
- Preserve existing public Publications metric sync and Scholar metric sync.
- PI citations/h-index are career-wide, not lab-only; add subtle attribution without bulky duplicate cards.
- Ongoing Research Projects manually supplied as 8, graduate student number subject to active roster verification.
- Do not manufacture numerical values or change definitions without owner review.

## Collaboration / student recruitment
- Student-facing Join Us: opportunities, expectations, research mentoring, publications and application instructions. No promises of acceptance, scholarships or publication outcomes.
- Collaborate: practical CV capabilities, demonstrated projects, verified collaborations and an obvious contact path.

## Engineering & change management
- Never modify DNS or retire `cmlab.cau.ac.kr` without explicit written approval.
- Develop in a feature branch and open a PR by default. Verify the changes and applicable checks, then merge and confirm deployment without waiting for owner review unless the owner asks to preview or hold the change. In the final update, link directly to the affected live page.
- Do not overwrite the old assets repo and its GitHub Actions. Keep publication URLs and old paths working during migration planning.
- Treat user-provided initial v1.1 archive as preliminary. Check every publication, collaborator, student and link before production launch.
- For small future data updates, change the relevant structured data entry only and follow the same verification and publication workflow.
- When adding a paper or Lab Life event, run `python3 scripts/index_site_media.py --sync-folders` and commit the generated title-based upload folder with the catalog record.
- When the owner announces a paper acceptance or public release, match it to its existing publication ID and add a `publication_updates` entry to the news record with the verified venue and public links available at the time. Run `python3 scripts/sync_publications.py` and include the catalog and folder moves in the same PR. Confirm the new catalog number, status and live paper link after deployment.
- Use precise date in update logs; do not silently rewrite existing people, paper or recruitment facts.

## Basic local checks
The v1.1 prototype is static: `python3 -m http.server 8000`, then test desktop and mobile, navigation, publication filters, visible media, page errors, and external links. Build/deployment is via `.github/workflows/deploy.yml` for GitHub Pages.
