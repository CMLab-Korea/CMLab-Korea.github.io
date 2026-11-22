# CMLab GitHub Website: Codex Handoff / 개발 인수인계

**Snapshot:** 2026-11-22. This is a task handoff, not a verbatim transfer of ChatGPT conversation history.

## 1. 목표 / Goal
- 기존 `https://cmlab.cau.ac.kr/`(Google Sites) 주소를 유지한 채 새 GitHub 기반 정적 웹사이트를 구축하고 검토한다.
- 향후 소속 기관이 바뀌더라도 소스를 재활용할 수 있는 독립적 브랜드 및 콘텐츠 구조.
- 우수 대학원생 모집, 국내외 연구자 공동연구, 산학협력을 함께 유도한다.

## 2. Current technical state
- GitHub organization: `CMLab-Korea`.
- Established public asset repository: `CMLab-Korea/cmlab-web-assets`; current logo, one research image, and automated JS publication/Scholar metrics there.
- New site repository requested: `CMLab-Korea/CMLab-Korea.github.io`. GitHub repository creation is a required user action if it does not exist.
- Existing Google Sites is live. Do not modify domain/DNS or remove existing content without approval.
- Earlier ChatGPT GitHub repository branch creation failed with HTTP 403, and linked Codex/GitHub application may require organization access. Verify environment repo selection and push permissions.
- v1.1 ZIP included with this handoff contains 9 static HTML pages, CSS, JS, structured data and GitHub Pages deployment workflow. Not yet uploaded or published to GitHub as a new website.

## 3. Website information architecture
Navigation: **Home / Research / Publications / People / Join Us / Collaborate**.
Secondary: **Life at CMLab / Teaching**, plus address and contact in footer.
Theme: near black background, navy `#0D207F`, electric blue, restrained ice blue and violet, polished not overanimated.
Research areas: Pixel-Level Intelligence; Video & Motion Intelligence; 3D/4D World Modeling; Generative & Agentic Visual AI.

## 4. Specific owner decisions
- List ONLY currently directly supervised students, excluding 11 legacy co-supervised students from Prof. Eom's lab. The prior 8 graduate + 3 intern counts are snapshots and should be verified.
- Publications: leftmost badge such as CVPR '26, small real teaser GIF/WebP/MP4/poster, metadata and links to the right. Highlight CMLab student first authors and the PI, preserve first/corresponding marks, and show external collaborators/affiliations accurately.
- Collaborators: readable, affiliation-grouped cards; verified institutional logos if legally and practically appropriate. Do not imply formal institutional agreements.
- Distinct Join Us and Collaborate landing pages.
- Existing Publication statistics 28/20/8/10 and Scholar Citations/h-index use public JS from the asset repository. Do NOT place SerpApi secret in website code.
- Manual ongoing research topic count = 8.

## 5. Asset migration policy
- Reuse original visuals and demo video from verified CMLab paper pages, GitHub repositories and original lab media. Do not assume Google Sites googleusercontent embeds can always be downloaded (some requests returned 403).
- Keep source provenance, licensing and usable alt text. Optimize PNG/WebP posters and MP4 loops for size. Never show illustrative stock images as real CMLab work.
- Keep asset provenance map in `data/media-migration.json` and mark missing media as TODO rather than inventing.

## 6. Acceptance criteria / First Codex task
1. Connect/review GitHub repository `CMLab-Korea/CMLab-Korea.github.io` and asset repo.
2. Import the bundled site files at repository ROOT. The ZIP should be extracted first, not committed as one opaque ZIP.
3. Review `AGENTS.md`, `README.md`, `data/` and external URLs. Keep all legacy sites unchanged.
4. Validate browser behavior: mobile/desktop, accessible nav, research content, publication filters, citations metrics and links.
5. Verify content from the legacy site and correct clearly mismatched names or metadata. Identify unverifiable items in a TODO report.
6. Open a draft PR and show screenshots/diff for approval before publication. Do not change university DNS.
7. Enable GitHub Pages after approval, verify `https://cmlab-korea.github.io/` and report exact URL.

## 7. Future everyday operations
- Add student: modify `data/people.json`, images if authorized, test, PR.
- Publish paper: modify `data/publications.json`, verified venue/year/authorship/teaser/media and links, test, PR.
- Update collaborator: modify `data/collaborators.json`, verify affiliation, test, PR.
- Update media: add source, ensure appropriate rights, optimize and link, test, PR.
- Update theme/layout: CSS and page code on a branch, review desktop/mobile, PR.
- Preserve old GitHub Actions and live domain unless owner explicitly authorizes changing them.

## 8. Files
`AGENTS.md` provides durable Codex instructions. `README.md` and `SETUP_KO.md` describe initial website. `data/*.json` contains editable content. `assets/css/style.css` and `assets/js/site.js` control styling and interactions. `.github/workflows/deploy.yml` handles GitHub Pages deployment.

## English quick handoff
Build and maintain a publication-rich dark themed CMLab site, with accurate students/collaborators, verified demo media, transparent Google Scholar metrics, and production-quality GitHub Pages deployment. Preserve the existing university website and asset metrics workflows. Use PR-based review and maintain `AGENTS.md` as the repository's standing instructions.
