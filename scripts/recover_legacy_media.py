#!/usr/bin/env python3
"""Recover public legacy images with bounded downloads and record the source URLs."""
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

GALLERY = "https://cmlab.cau.ac.kr/gallery"
PUBLICATIONS = "https://cmlab.cau.ac.kr/publications"
MAX_BYTES = 16 * 1024 * 1024


def available(url):
    parsed = urlsplit(url or "")
    return parsed.scheme == "https" and parsed.netloc in {
        "lh7-us.googleusercontent.com", "lh3.googleusercontent.com"
    } and parsed.path.startswith("/sitesv-images-rt/")


def capture(job):
    url, filename, referer = job
    record = {"source": url, "file": filename}
    try:
        request = Request(url, headers={"Referer": referer, "User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=9) as response:
            if not available(response.geturl()):
                return {**record, "status": "unexpected redirect"}
            content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            return {**record, "status": "over size limit"}
        with Image.open(BytesIO(content)) as image:
            if getattr(image, "is_animated", False):
                return {**record, "status": "animated source requires manual encoding"}
            image = ImageOps.exif_transpose(image)
            image.thumbnail((1200, 960), Image.Resampling.LANCZOS)
            out = Path("capture/media") / filename
            out.parent.mkdir(parents=True, exist_ok=True)
            image.save(out, "WEBP", quality=84)
        return {**record, "status": "saved"}
    except HTTPError as error:
        return {**record, "status": f"HTTP {error.code}"}
    except (OSError, ValueError, UnidentifiedImageError) as error:
        return {**record, "status": type(error).__name__}


def main():
    jobs = []
    for event in json.loads(Path("data/gallery.json").read_text()):
        for i, url in enumerate(event["source_images"], 1):
            if available(url):
                jobs.append((url, f'gallery/{event["id"]}/source-{i:03}.webp', GALLERY))
    for paper in json.loads(Path("data/publications.json").read_text()):
        if paper.get("teaser") or paper.get("teaser_video"):
            continue
        urls = [m["url"] for m in paper["source_media"] if available(m.get("url"))]
        if len(urls) == 1:
            jobs.append((urls[0], f'publications/paper-{paper["id"]}/teaser.webp', PUBLICATIONS))
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(capture, jobs))
    Path("capture").mkdir(exist_ok=True)
    Path("capture/media-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(Counter(r["status"] for r in results))


if __name__ == "__main__":
    main()
