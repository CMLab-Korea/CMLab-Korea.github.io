#!/usr/bin/env python3
"""Create upload folders and index site media from the editable catalogs."""
import argparse
import json
from pathlib import Path
import re
from shutil import copyfile
import subprocess
from unicodedata import normalize

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}
CONVERTED_VIDEO_EXTENSIONS = {".mov", ".m4v", ".mkv", ".avi", ".mpg", ".mpeg", ".ogv", ".wmv"}
PAPERS = Path("assets/media/publications")
PAPER_PREVIEWS = Path("assets/media/publication-previews")
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

    poster = source if not image else None
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
    from sync_publications import sync
    sync(ROOT)
    index_publication_media(stage_previews=bool(options.site_dir))
    if not options.publications_only:
        index_gallery_media(create=options.sync_folders)
    if not options.publications_only and not options.sync_folders:
        index_profile_photos()
    if options.site_dir:
        copy_legacy_media_paths()
