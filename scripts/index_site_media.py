#!/usr/bin/env python3
"""Create upload folders and index site media from the editable catalogs."""
import argparse
import json
from pathlib import Path
import re
from shutil import copyfile
from unicodedata import normalize

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}
PAPERS = Path("assets/media/publications")
GALLERY = Path("assets/img/gallery")
FOLDER_LIMIT = 180


def filename_order(path):
    chunks = re.split(r"(\d+)", path.name.casefold())
    return tuple(int(chunk) if n % 2 else chunk for n, chunk in enumerate(chunks))


def assets(directory, extensions, stem=None):
    if not directory.is_dir():
        return []
    files = (
        path for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in extensions
        and (stem is None or path.stem.casefold() == stem)
    )
    return [path.relative_to(ROOT).as_posix()
            for path in sorted(files, key=lambda path: (filename_order(path), path.name))]


def load(file):
    return json.loads(file.read_text(encoding="utf-8"))


def save(file, records):
    file.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def shorten(name, limit=FOLDER_LIMIT):
    return name.encode("utf-8")[:limit].decode("utf-8", errors="ignore").rstrip(" .")


def title_folder(title):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " - ", normalize("NFC", title))
    name = shorten(" ".join(name.split()).strip(" .-"))
    if re.fullmatch(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", name, re.I):
        name = "_" + name
    return name or "Untitled"


def register_folders(records, base, label, create=False):
    used = set()
    for record in records:
        name = record.get("media_folder")
        if name:
            if title_folder(name) != name or name.casefold() in used:
                raise ValueError(f"Invalid or duplicate media folder {name!r} in {base}")
            used.add(name.casefold())

    for record in records:
        name = record.get("media_folder")
        if not name:
            name = title_folder(label(record))
            if name.casefold() in used:
                suffix = f' [{record["id"]}]'
                name = title_folder(shorten(name, FOLDER_LIMIT - len(suffix.encode("utf-8"))) + suffix)
            if name.casefold() in used:
                raise ValueError(f"Duplicate media folder {name!r} in {base}")
            used.add(name.casefold())
            record["media_folder"] = name
        folder = ROOT / base / name
        if create:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / ".gitkeep").touch(exist_ok=True)
        yield record, folder


def index_publication_media(create=False):
    paper_file = ROOT / "data/publications.json"
    papers = load(paper_file)
    for paper, folder in register_folders(papers, PAPERS, lambda entry: entry["title"], create):
        for field, extensions, preferred in (
            ("teaser", IMAGE_EXTENSIONS, "teaser"),
            ("teaser_video", VIDEO_EXTENSIONS, "preview"),
        ):
            matches = assets(folder, extensions)
            if matches:
                paper[field] = next(
                    (path for path in matches if Path(path).stem.casefold() == preferred),
                    matches[0],
                )
            else:
                fallback = paper.get(field, "")
                if fallback.startswith(("http://", "https://")) or (fallback and (ROOT / fallback).is_file()):
                    continue
                paper[field] = ""
    save(paper_file, papers)


def index_gallery_media(create=False):
    gallery_file = ROOT / "data/gallery.json"
    events = load(gallery_file)
    for event, folder in register_folders(
        events, GALLERY, lambda entry: f'{entry["title"]} ({entry["date"]})', create
    ):
        if not folder.exists():
            folder = ROOT / GALLERY / event["id"]
        event["media"] = assets(folder, IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)
        event.pop("images", None)
    save(gallery_file, events)


def index_profile_photos():
    people_file = ROOT / "data/people.json"
    people = load(people_file)
    for person in people:
        if person.get("photo_upload"):
            target = ROOT / person["photo_upload"]
            matches = assets(target.parent, IMAGE_EXTENSIONS, target.name)
            if len(matches) > 1:
                raise ValueError(f"Choose one portrait file for {person['name']}")
            if matches:
                person["photo"] = matches[0]
    save(people_file, people)


def copy_legacy_media_paths():
    aliases = load(ROOT / "data/media-migration.json").get("legacy_paths", {})
    for old, current in aliases.items():
        original = ROOT / current
        alias = ROOT / old
        if original.is_file() and not alias.exists():
            alias.parent.mkdir(parents=True, exist_ok=True)
            copyfile(original, alias)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--publications-only", action="store_true")
    scope.add_argument("--for-deploy", action="store_true")
    scope.add_argument("--sync-folders", action="store_true", help="Create and register upload folders")
    parser.add_argument("--site-dir", type=Path, help="Index a staged deployment directory")
    options = parser.parse_args()
    if options.site_dir:
        if not options.for_deploy:
            parser.error("--site-dir requires --for-deploy")
        ROOT = options.site_dir.resolve()
    index_publication_media(create=options.sync_folders)
    if not options.publications_only:
        index_gallery_media(create=options.sync_folders)
    if not options.publications_only and not options.sync_folders:
        index_profile_photos()
    if options.site_dir:
        copy_legacy_media_paths()
