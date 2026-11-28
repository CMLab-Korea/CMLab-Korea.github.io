#!/usr/bin/env python3
"""Create upload folders and index site media from the editable catalogs."""
import argparse
import json
from pathlib import Path
import re
from shutil import copyfile
import subprocess
from tempfile import TemporaryDirectory, mkdtemp
from unicodedata import normalize

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}
CONVERTED_VIDEO_EXTENSIONS = {".mov", ".m4v", ".mkv", ".avi", ".mpg", ".mpeg", ".ogv", ".wmv"}
PAPERS = Path("assets/media/publications")
PAPER_PREVIEWS = Path("assets/media/publication-previews")
GALLERY = Path("assets/img/gallery")
GALLERY_PREVIEWS = Path("assets/media/gallery-previews")
GALLERY_NATIVE_IMAGES = IMAGE_EXTENSIONS | {".svg", ".apng", ".ico", ".jfif", ".jpe"}
GALLERY_CONVERTED_IMAGES = {".heic", ".heif", ".tif", ".tiff", ".bmp", ".jxl", ".jp2"}
FOLDER_LIMIT = 180
RETIRED_SITE = re.compile(r"(?<![\w-])cmlab\.cau\.ac\.kr(?=$|[./:#?\s\"'])", re.I)
SITES_IMAGE = re.compile(r"\.googleusercontent\.com/sitesv-images-rt/", re.I)
EDITORIAL_SOURCE_FIELDS = {"source_url", "source_site", "distinction_source", "source_links",
                           "source_media", "source_images"}


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


def relocate_media_folders(root, base, plans):
    directory = root / base
    directory.mkdir(parents=True, exist_ok=True)
    owners = {old for old, _ in plans if old is not None}
    if len(owners) != sum(old is not None for old, _ in plans):
        raise ValueError(f"Duplicate source folders in {base}")
    for old, new in plans:
        if (directory / new).exists() and old != new and new not in owners:
            raise FileExistsError(directory / new)

    # Preserve intermediate files if any filesystem operation interrupts the move.
    scratch = Path(mkdtemp(prefix=".folder-sync-", dir=directory))
    moved = []
    changes = {}
    for index, (old, new) in enumerate(plans):
        if old is not None and old != new and (directory / old).is_dir():
            temporary = scratch / str(index)
            (directory / old).rename(temporary)
            moved.append((temporary, directory / new))
            for file in temporary.rglob("*"):
                if file.is_file() and file.name != ".gitkeep":
                    child = file.relative_to(temporary)
                    changes[(base / old / child).as_posix()] = (base / new / child).as_posix()
    for temporary, target in moved:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.rename(target)
    scratch.rmdir()
    return changes


def update_media_aliases(manifest, changes):
    aliases = {old: changes.get(current, current)
               for old, current in manifest.get("legacy_paths", {}).items()}
    aliases.update(changes)
    manifest["legacy_paths"] = {old: current for old, current in aliases.items() if old != current}


def animated_gif(path):
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-read_intervals", "%+#2", "-show_entries", "frame=pts", "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return len(json.loads(probe.stdout).get("frames", [])) > 1


def browser_mp4(path):
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,pix_fmt", "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    streams = json.loads(probe.stdout).get("streams", [])
    return bool(streams and streams[0].get("codec_name") == "h264"
                and streams[0].get("pix_fmt") in ("yuv420p", "yuvj420p"))


def stage_publication_preview(paper):
    image, video = paper["teaser"], paper["teaser_video"]
    local_gif = image.startswith(f"{PAPERS.as_posix()}/") and image.lower().endswith(".gif")
    source = None
    if video.startswith(f"{PAPERS.as_posix()}/"):
        extension = Path(video).suffix.lower()
        if (extension in CONVERTED_VIDEO_EXTENSIONS or extension == ".gif"
                or (extension == ".mp4" and not browser_mp4(ROOT / video))):
            source = video
    elif not video and local_gif and animated_gif(ROOT / image):
        source = image

    poster = video if not image and video.startswith(f"{PAPERS.as_posix()}/") else None
    if local_gif and (source or video):
        poster = image
    if not (source or poster):
        return

    output = PAPER_PREVIEWS / str(paper["id"])
    (ROOT / output.parent).mkdir(parents=True, exist_ok=True)
    ffmpeg = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
    scale = "scale=w='min(iw,1280)':h='min(ih,1280)':force_original_aspect_ratio=decrease:force_divisible_by=2"
    if source:
        mp4 = output.with_suffix(".mp4")
        subprocess.run([
            *ffmpeg, "-i", str(ROOT / source), "-map", "0:v:0", "-map", "0:a:0?", "-vf", scale,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart", str(ROOT / mp4),
        ], check=True)
        paper["teaser_video"] = mp4.as_posix()
    if poster:
        still = output.with_suffix(".jpg")
        subprocess.run([
            *ffmpeg, "-i", str(ROOT / poster), "-map", "0:v:0", "-frames:v", "1",
            "-vf", scale, "-q:v", "3", "-update", "1", str(ROOT / still),
        ], check=True)
        paper["teaser"] = still.as_posix()


def index_publication_media(stage_previews=False):
    paper_file = ROOT / "data/publications.json"
    papers = load(paper_file)
    videos = VIDEO_EXTENSIONS | CONVERTED_VIDEO_EXTENSIONS if stage_previews else VIDEO_EXTENSIONS
    for paper in papers:
        folder = ROOT / PAPERS / paper["media_folder"]
        for field, extensions, preferred in (
            ("teaser", IMAGE_EXTENSIONS, "teaser"),
            ("teaser_video", videos, "preview"),
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
        if stage_previews:
            if not paper["teaser_video"]:
                gif = next(iter(assets(folder, {".gif"}, "preview")), None)
                if gif and animated_gif(ROOT / gif):
                    paper["teaser_video"] = gif
            stage_publication_preview(paper)
    save(paper_file, papers)


def gallery_preview(path, event_id, index):
    source = ROOT / path
    relative = GALLERY_PREVIEWS / event_id / f"{index}.jpg"
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in {".heic", ".heif"}:
        with TemporaryDirectory() as scratch:
            directory = Path(scratch)
            subprocess.run(["heif-convert", "-q", "88", str(source), str(directory / "image.jpg")], check=True)
            first = min(directory.glob("*.jpg"), key=filename_order)
            copyfile(first, target)
    else:
        subprocess.run([
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(source),
            "-frames:v", "1", "-vf", "scale='min(1600,iw)':-1", "-q:v", "3",
            "-update", "1", str(target),
        ], check=True)
    return relative.as_posix()


def index_gallery_media(stage_previews=False):
    gallery_file = ROOT / "data/gallery.json"
    manifest_file = ROOT / "data/media-migration.json"
    events = sorted(load(gallery_file), key=lambda event: event["date"], reverse=True)
    plans = []
    for rank, event in enumerate(events, 1):
        old = event.get("media_folder") or event["id"]
        if title_folder(old) != old or title_folder(event["id"]) != event["id"]:
            raise ValueError(f"Invalid gallery media folder {old!r}")
        number = len(events) + 1 - rank
        dates = event["date"]
        if event.get("end_date"):
            dates += " to " + event["end_date"]
        folder = title_folder(f'{rank:03d} [L{number}] {event["title"]} ({dates})')
        event["catalog_number"] = f"L{number}"
        event["media_folder"] = folder
        plans.append((Path(old), Path(folder)))
    changes = relocate_media_folders(ROOT, GALLERY, plans)
    manifest = load(manifest_file)
    update_media_aliases(manifest, changes)
    for event in events:
        folder = ROOT / GALLERY / event["media_folder"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch(exist_ok=True)
        media = assets(folder, GALLERY_NATIVE_IMAGES | GALLERY_CONVERTED_IMAGES | VIDEO_EXTENSIONS)
        if stage_previews:
            media = [gallery_preview(path, event["id"], index)
                     if Path(path).suffix.lower() in GALLERY_CONVERTED_IMAGES else path
                     for index, path in enumerate(media, 1)]
        event["media"] = media
        event.pop("images", None)
    save(gallery_file, events)
    save(manifest_file, manifest)


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


def omit_retired_site_sources(value):
    """Omit old site references from editorial fields in the staged catalog only."""
    if isinstance(value, list):
        return [omit_retired_site_sources(item) for item in value]
    if not isinstance(value, dict):
        return value

    def retired_source(item):
        text = json.dumps(item, ensure_ascii=False)
        return RETIRED_SITE.search(text) or SITES_IMAGE.search(text)

    result = {}
    for field, item in value.items():
        if field in EDITORIAL_SOURCE_FIELDS:
            if isinstance(item, list):
                item = [source for source in item if not retired_source(source)]
            elif retired_source(item):
                continue
        result[field] = omit_retired_site_sources(item)
    return result


def check_staged_site_links():
    """Clean editorial references and catch active links to the retired site."""
    for path in (ROOT / "data").glob("*.json"):
        record = load(path)
        public_record = omit_retired_site_sources(record)
        if public_record != record:
            save(path, public_record)

    text_suffixes = {".html", ".js", ".css", ".json", ".svg", ".xml", ".txt"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in text_suffixes:
            source = path.read_text(encoding="utf-8")
            if RETIRED_SITE.search(source) or "cmlab-web-assets/data/publication-stats.js" in source:
                raise ValueError(f"Retired CMLab site reference in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--publications-only", action="store_true")
    scope.add_argument("--gallery-only", action="store_true")
    scope.add_argument("--for-deploy", action="store_true")
    scope.add_argument("--sync-folders", action="store_true", help="Create and register upload folders")
    parser.add_argument("--site-dir", type=Path, help="Index a staged deployment directory")
    options = parser.parse_args()
    if options.site_dir:
        if not options.for_deploy:
            parser.error("--site-dir requires --for-deploy")
        ROOT = options.site_dir.resolve()
    if not options.gallery_only:
        from sync_publications import sync
        sync(ROOT)
        index_publication_media(stage_previews=bool(options.site_dir))
    if not options.publications_only:
        index_gallery_media(stage_previews=bool(options.site_dir))
    if not (options.publications_only or options.sync_folders or options.gallery_only):
        index_profile_photos()
    if options.site_dir:
        from validate_journal_metrics import validate_public_projection
        validate_public_projection(load(ROOT / "data/journals.json"))
        copy_legacy_media_paths()
        check_staged_site_links()
