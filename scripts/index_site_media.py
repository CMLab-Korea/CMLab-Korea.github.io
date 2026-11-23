#!/usr/bin/env python3
"""Register local paper and gallery media in the static site JSON catalogs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}


def assets(directory, extensions, stem=None):
    if not directory.is_dir():
        return []
    return sorted(
        path.relative_to(ROOT).as_posix()
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in extensions
        and (stem is None or path.stem == stem)
    )


def save(file, records):
    file.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_publication_media():
    paper_file = ROOT / "data/publications.json"
    papers = json.loads(paper_file.read_text(encoding="utf-8"))
    for paper in papers:
        directory = ROOT / "assets/media/publications" / f'paper-{paper["id"]}'
        for field, extensions, stem in (
            ("teaser", IMAGE_EXTENSIONS, "teaser"),
            ("teaser_video", VIDEO_EXTENSIONS, "preview"),
        ):
            matches = assets(directory, extensions, stem)
            if len(matches) > 1:
                raise ValueError(f"Choose one {stem} file in {directory.relative_to(ROOT)}")
            if matches:
                paper[field] = matches[0]
    save(paper_file, papers)


def index_gallery_media():
    gallery_file = ROOT / "data/gallery.json"
    events = json.loads(gallery_file.read_text(encoding="utf-8"))
    for event in events:
        directory = ROOT / "assets/img/gallery" / event["id"]
        event["images"] = assets(directory, IMAGE_EXTENSIONS)

    save(gallery_file, events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publications-only", action="store_true")
    options = parser.parse_args()
    index_publication_media()
    if not options.publications_only:
        index_gallery_media()
