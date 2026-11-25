#!/usr/bin/env python3
"""Apply publication news and keep catalog numbers and upload folders in display order."""
import argparse
from collections import Counter
from pathlib import Path
import re
from tempfile import mkdtemp
from urllib.parse import urlsplit

from index_site_media import FOLDER_LIMIT, PAPERS, ROOT, load, save, shorten, title_folder

TYPES = {"Conference": "C", "Journal": "J"}
LINK_FIELDS = ("arxiv_url", "project_url", "venue_url", "code_url", "dataset_url")
GROUPS = ("01 Preprints and Under Review", "02 Peer-reviewed Publications")
ORDER_PREFIX = re.compile(r"^\d+ \[[UCJ]\d+\] ")


def public_url(value):
    parts = urlsplit(value or "")
    return parts.scheme in ("http", "https") and bool(parts.hostname) and not parts.username


def last_corresponding(paper):
    authors = re.split(r",\s*(?:and\s+)?|\s+and\s+", paper.get("authors", ""), flags=re.I)
    return bool(re.fullmatch(r"Jihyong Oh[*†‡+]*[†+][*†‡+]*", authors[-1].strip(), re.I))


def update_catalog(papers, news):
    by_id = {paper["id"]: paper for paper in papers}
    if len(by_id) != len(papers):
        raise ValueError("Duplicate publication IDs")
    maxima = Counter()
    assigned = set()
    for paper in papers:
        if paper["type"] in TYPES:
            number = paper["catalog_number"]
            if not re.fullmatch(TYPES[paper["type"]] + r"[1-9]\d*", number) or number in assigned:
                raise ValueError(f"Invalid or duplicate catalog number {number}")
            assigned.add(number)
            maxima[paper["type"]] = max(maxima[paper["type"]], int(number[1:]))

    # Apply older news first. On the same date, the later listed news applies first.
    promoted = {}
    for entry in sorted(reversed(news), key=lambda item: item["date"]):
        for update in reversed(entry.get("publication_updates", ())):
            if entry["category"] != "Publication" or update["id"] not in by_id:
                raise ValueError(f"Invalid publication news update for ID {update['id']}")
            paper = by_id[update["id"]]
            for field in LINK_FIELDS:
                if field in update:
                    if not public_url(update[field]):
                        raise ValueError(f"Invalid {field} for {paper['title']}")
                    paper[field] = update[field]
            if acceptance := update.get("acceptance"):
                kind = acceptance["type"]
                if kind not in TYPES or not acceptance["venue"].strip() or not acceptance["venue_short"].strip():
                    raise ValueError(f"Invalid acceptance venue for {paper['title']}")
                if not isinstance(acceptance["year"], int) or not 1900 <= acceptance["year"] <= 2200:
                    raise ValueError(f"Invalid acceptance year for {paper['title']}")
                if paper["type"] == "Preprint":
                    maxima[kind] += 1
                    paper["catalog_number"] = f"{TYPES[kind]}{maxima[kind]}"
                    print(f"{paper['catalog_number']} · {paper['title']} · {acceptance['venue_short']}")
                elif paper["type"] != kind:
                    raise ValueError(f"Acceptance changes the type of an already numbered paper: {paper['title']}")
                status = "Published" if paper.get("venue_url") or paper.get("status") == "Published" else "Accepted"
                paper.update(type=kind, status=status, venue=acceptance["venue"],
                             venue_short=acceptance["venue_short"], year=acceptance["year"],
                             accepted_on=entry["date"])
                promoted[paper["id"]] = len(promoted) + 1

    preprints = [paper for paper in papers if paper["type"] == "Preprint"]
    preprints.sort(key=lambda paper: (last_corresponding(paper), paper.get("listed_on", "")), reverse=True)
    for number, paper in zip(range(len(preprints), 0, -1), preprints):
        is_public = any(public_url(paper.get(field)) and paper[field] not in paper.get("unavailable_urls", [])
                        for field in ("arxiv_url", "project_url"))
        paper["venue_short"] = "Preprint" if is_public else "Manuscript"
        paper["catalog_number"] = f"U{number}"

    published = [paper for paper in papers if paper["type"] in TYPES]
    published.sort(key=lambda paper: (paper.get("accepted_on", ""), promoted.get(paper["id"], 0)), reverse=True)
    if len(preprints) + len(published) != len(papers):
        raise ValueError("Unknown publication type")
    return preprints, published


def validate_folder(name):
    path = Path(name)
    parts = path.parts
    if (len(parts) not in (1, 2) or (len(parts) == 2 and parts[0] not in GROUPS)
            or any(title_folder(part) != part for part in parts) or path.as_posix() != name):
        raise ValueError(f"Invalid publication folder {name!r}")
    return path


def sync_folders(root, sections, manifest):
    base = root / PAPERS
    base.mkdir(parents=True, exist_ok=True)
    plans = []
    for group, papers in zip(GROUPS, sections):
        for rank, paper in enumerate(papers, 1):
            old = validate_folder(paper["media_folder"]) if paper.get("media_folder") else None
            title = ORDER_PREFIX.sub("", old.name) if old else title_folder(paper["title"])
            prefix = f'{rank:03d} [{paper["catalog_number"]}] '
            new = Path(group) / (prefix + shorten(title, FOLDER_LIMIT - len(prefix.encode("utf-8"))))
            plans.append((paper, old, new))

    owners = {old for _, old, _ in plans if old is not None}
    if len(owners) != sum(old is not None for _, old, _ in plans):
        raise ValueError("Duplicate source publication folders")
    for _, old, new in plans:
        if (base / new).exists() and old != new and new not in owners:
            raise FileExistsError(base / new)

    aliases = manifest.setdefault("legacy_paths", {})
    changes = {}
    # Keep intermediate files recoverable if a filesystem error interrupts a move.
    scratch = Path(mkdtemp(prefix=".folder-sync-", dir=base))
    moved = []
    for paper, old, new in plans:
        if old is not None and old != new and (base / old).is_dir():
            temporary = scratch / str(paper["id"])
            (base / old).rename(temporary)
            moved.append((temporary, base / new))
            for file in temporary.rglob("*"):
                if file.is_file() and file.name != ".gitkeep":
                    child = file.relative_to(temporary)
                    changes[(PAPERS / old / child).as_posix()] = (PAPERS / new / child).as_posix()
    for temporary, target in moved:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.rename(target)
    scratch.rmdir()

    for paper, _, new in plans:
        folder = base / new
        folder.mkdir(parents=True, exist_ok=True)
        keep = folder / ".gitkeep"
        if not keep.exists():
            keep.touch()
        paper["media_folder"] = new.as_posix()
        for field in ("teaser", "teaser_video"):
            if paper.get(field) in changes:
                paper[field] = changes[paper[field]]

    for record in manifest.get("items", ()):
        for field in ("image", "video"):
            if record.get(field) in changes:
                record[field] = changes[record[field]]
    for old, current in list(aliases.items()):
        aliases[old] = changes.get(current, current)
    aliases.update(changes)
    manifest["legacy_paths"] = {old: current for old, current in aliases.items() if old != current}


def sync(root=ROOT):
    paper_file = root / "data/publications.json"
    manifest_file = root / "data/media-migration.json"
    manifest = load(manifest_file)
    sections = update_catalog(load(paper_file), load(root / "data/news.json"))
    sync_folders(root, sections, manifest)
    save(paper_file, sections[0] + sections[1])
    save(manifest_file, manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=ROOT)
    sync(parser.parse_args().site_dir.resolve())
