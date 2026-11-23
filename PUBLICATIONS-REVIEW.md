# CMLab source migration review

The [Playwright run](https://github.com/CMLab-Korea/CMLab-Korea.github.io/actions/runs/45075739897) captured the rendered HTML. The [capture records](https://github.com/CMLab-Korea/CMLab-Korea.github.io/tree/c8e725e0fdcc2cab7c21b866b44e70e0f8d61afd/capture) preserve the Google Sites source order and provide paragraph text, URL labels and media references.

- 38 papers match the source sections in order, including 10 preprints, 20 conference papers and 8 journal papers. The journal and conference count agrees with the source summary.
- 129 publication source link occurrences and 39 paper image references are retained in the catalog. The 32 news records contain 45 source link occurrences. The homepage and /cmlab news entries matched.
- One paper has no source links. 5 peer-reviewed papers lack a usable official venue link in the preview. The cloud proxy blocked 121 of 153 distinct publication and news URLs during the link check. Thirty returned HTTP 200 and two returned errors as listed below. Proxy denials leave the origin status unknown.
- No duplicate paper IDs or normalized titles. The link renderer deduplicates exact URL repeats within each paper. Three corresponding-author markers link to an unrelated profile in the source. The catalog retains those URLs for review and displays the byline marks as text.
- MoRel uses “Bidirectional” in its title, as in its project repository. The source contains “Bidirectioanl” and the original CVF URL contains the same spelling. SoFoNO uses the source's January 2026 issue date even though a project README uses 2025. The page displays venue abbreviations with two-digit years.
- The six Oral and Highlight percentages come from the rendered source. The expandable venue ranking table reproduces the attached HTML, which names Google Scholar Metrics and contains nine fixed h5-index and Rank values. A live venue-ranking sync source remains to be identified.
- The paper image references preserve the original URLs and are available for later media review. The preview uses its five local posters and MoRel clip. Source video links are retained as links.
- The legacy page also has separate domestic publications, patent and software registration sections. The capture retains them. The publication catalog covers the requested Preprints / Under Review and Peer-reviewed Publications sections.

## Original URLs requiring review

| ID | Location | Observation | Original URL |
| --- | --- | --- | --- |
| URL1 | News · FLAIR | Source host includes a trailing dot. Confirm the intended news URL. | <https://cmlab-korea.github.io./FLAIR/> |
| URL2 | News · EcoSplat | The link points to SplineGS in two entries. | <https://kaist-viclab.github.io/splinegs-site/> |
| URL3 | News · MoCHA-former | The journal link points to SoFoNO. | <https://www.sciencedirect.com/science/article/pii/S0925231225026165> |
| URL4 | CHIMERA | GitHub returned HTTP 404. | <https://github.com/CMLab-Korea/ECCV26-CHIMERA> |
| URL5 | Deep SR-ITM | HTTP 403 in the link check. | <http://openaccess.thecvf.com/content_ICCV_2019/papers/Kim_Deep_SR-ITM_Joint_Learning_of_Super-Resolution_and_Inverse_Tone-Mapping_for_ICCV_2019_paper.pdf> |
| URL6 | Three byline markers | The corresponding-author mark links to a different person. | <https://weidixie.github.io/> |

### needs verification 1

MotionGrounder. Review the Video & Motion tag alongside Generative / Agentic AI.

### needs verification 15

DiffPS. Review the Generative / Agentic AI tag for diffusion-based person search.

### needs verification 17

Domain Generalization for Person Re-identification. Review the research tag for this person re-identification survey.

### needs verification 25

SPAM-Net. Review the Pixel-Level tag for SAR target recognition.

### needs verification 28

Deep SR-ITM. The original venue URL needs confirmation. See URL5 below.

### needs verification 29

CHIMERA. The original code URL needs confirmation. See URL4 below.

### needs verification 32

Chameleon. The rendered legacy byline omits Jeahun Sung, who appeared in the earlier project page capture. The migration uses the rendered legacy byline.

### needs verification 33

RefGC-SR². The rendered legacy byline includes Jeahun Sung and Dahyeon Kye. The earlier project-page byline omitted both. The migration uses the rendered legacy byline.

### needs verification 37

Training-free Style Control. The live entry says “coming soon” and supplies neither paper nor project URL.
