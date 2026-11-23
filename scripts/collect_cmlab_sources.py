#!/usr/bin/env python3
"""Capture CMLab legacy source evidence without changing the curated website data."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://cmlab.cau.ac.kr"
SOURCES = {
    "publications": (ORIGIN + "/publications", r"Summary\s*:"),
    "home": (ORIGIN + "/", r"\bNews\b"),
    "lab": (ORIGIN + "/cmlab", r"\bNews\b"),
}

EXTRACT = r"""({savedHtml, sourceUrl, papers}) => {
  const doc = savedHtml === null ? document : new DOMParser().parseFromString(savedHtml, 'text/html');
  const absolute = value => {
    if (!value) return null;
    try { return new URL(value, sourceUrl).href; } catch { return null; }
  };
  const clean = s => s.trim().replace(/\s+/g, ' ');
  const text = el => clean(el.innerText || el.textContent || '');
  const normalize = s => s.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
  const links = element => [...element.querySelectorAll('a[href]')].map(a => ({
    label: text(a) || a.getAttribute('aria-label') || a.querySelector('img')?.alt || '',
    href: a.getAttribute('href'),
    url: absolute(a.getAttribute('href'))
  }));
  const media = element => [...element.querySelectorAll('img, video, source, iframe')].map(el => ({
    tag: el.localName,
    alt: el.getAttribute('alt') || el.getAttribute('title') || '',
    src: el.getAttribute('src'),
    url: absolute(el.currentSrc || el.getAttribute('src')),
    data_src: el.getAttribute('data-src'),
    srcset: el.getAttribute('srcset'),
    poster: el.getAttribute('poster'),
    poster_url: absolute(el.getAttribute('poster'))
  }));
  const content = doc.body;
  const blocks = [...content.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,[role="heading"]')];
  const sections = blocks.filter(el => text(el)).map(el => ({
    tag: el.tagName.toLowerCase(), text: text(el), links: links(el), media: media(el)
  }));
  const anchors = papers.map(paper => ({
    paper,
    anchor: blocks.find(el => normalize(text(el)).includes(normalize(paper.title)))
  }));
  const matches = anchors.map(({paper, anchor}) => {
    if (!anchor) return {id: paper.id, title: paper.title, review: 'Title match needed'};
    let scope = anchor;
    while (scope.parentElement && scope.parentElement !== content &&
           !anchors.some(other => other.anchor && other.anchor !== anchor &&
              scope.parentElement.contains(other.anchor))) {
      if (text(scope.parentElement).length > 4500) break;
      scope = scope.parentElement;
    }
    const byline = text(scope).match(/(?:Authors?|By)\s*:\s*([^\n]+?)(?=\s+(?:Venue|Project|Paper|Code|arXiv)\s*:|$)/i);
    return {
      id: paper.id, title: paper.title, authors: byline?.[1] || null,
      venue: paper.venue, year: paper.year, order: blocks.indexOf(anchor),
      nearby_text: text(scope), links: links(scope), media: media(scope),
      review: 'Verify byline, venue, link ownership and media from the captured HTML'
    };
  });
  return {title: doc.title, sections, links: links(content), media: media(content),
    publication_candidates: matches.sort((a, b) => (a.order ?? Infinity) - (b.order ?? Infinity)),
    dated_entries: sections.filter(block => /^\[?\s*\d{1,2}[./]\d{2,4}(?:[./]\d{4})?\s*\]/.test(block.text))
  };
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publications-html", type=Path)
    parser.add_argument("--home-html", type=Path)
    parser.add_argument("--lab-html", type=Path)
    parser.add_argument("--chromium", help="Use an existing Chromium executable")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    papers = json.loads((ROOT / "data/publications.json").read_text())
    failures = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        for name, (url, ready_text) in SOURCES.items():
            saved = getattr(args, name + "_html")
            if any((args.publications_html, args.home_html, args.lab_html)) and not saved:
                continue
            page = browser.new_page(viewport={"width": 1440, "height": 900}, locale="en-US")
            try:
                if saved:
                    rendered = saved.read_text(encoding="utf-8-sig")
                    page.goto("about:blank")
                else:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                    if response is None or not response.ok:
                        raise RuntimeError(f"HTTP {response.status if response else 'unknown'}")
                    rendered = page.content()
                    page.wait_for_function(
                        "pattern => new RegExp(pattern, 'i').test(document.body?.innerText || '')",
                        arg=ready_text, timeout=20_000,
                    )
                    rendered = page.content()
                (args.output / f"{name}.html").write_text(rendered)
                evidence = page.evaluate(EXTRACT, {
                    "savedHtml": rendered if saved else None,
                    "sourceUrl": url, "papers": papers if name == "publications" else [],
                })
                evidence["source_url"] = url
                evidence["capture_method"] = "saved HTML" if saved else "Playwright Chromium"
                if not saved:
                    evidence["frames"] = []
                    for frame in page.frames[1:]:
                        if frame.url == "about:blank":
                            continue
                        try:
                            frame_evidence = frame.evaluate(EXTRACT, {
                                "savedHtml": None, "sourceUrl": frame.url, "papers": [],
                            })
                            evidence["frames"].append({"url": frame.url, "evidence": frame_evidence})
                        except Exception as exc:
                            evidence["frames"].append({"url": frame.url, "error": str(exc).splitlines()[0]})
                (args.output / f"{name}.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
                print(f"{name}: {len(evidence['links'])} links, {len(evidence['media'])} media references")
            except Exception as exc:
                failures[name] = str(exc).splitlines()[0]
                print(f"{name}: {failures[name]}")
            finally:
                page.close()
        browser.close()
    (args.output / "failures.json").write_text(json.dumps(failures, indent=2) + "\n")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
