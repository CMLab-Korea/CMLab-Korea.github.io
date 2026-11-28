#!/usr/bin/env python3
"""Validate the public JCR projection and report catalog matching and coverage."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, expected):
    require(isinstance(value, dict) and value.keys() == set(expected.split()),
            "Fields do not match the public journal schema")


def norm(value):
    return " ".join(re.sub(r"[^\w]+|_", " ", unicodedata.normalize("NFKC", value).lower()).split())


def serial(value):
    return str(value or "").strip().upper().replace("-", "")


def valid_issn(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9]{4}-[0-9]{3}[0-9X]", value)) and (
        sum(int(c) * (8 - i) for i, c in enumerate(serial(value)[:7]))
        + (10 if value[-1] == "X" else int(value[-1]))
    ) % 11 == 0


def journal_match(paper, journals):
    if paper.get("type") != "Journal":
        return []
    if paper.get("journal_id"):
        return [j for j in journals if j["journal_id"] == paper["journal_id"]]
    identifiers = {serial(paper.get(k)) for k in ("issn", "eissn")} - {""}
    if identifiers:
        return [j for j in journals if any(serial(j[k]) in identifiers for k in ("issn", "eissn"))]
    names = {norm(paper.get("venue") or ""),
             norm(re.sub(r"['’]\d{2,4}$", "", paper.get("venue_short") or ""))} - {""}
    official = [j for j in journals if norm(j["official_name"]) in names]
    return official or [j for j in journals if any(norm(alias) in names for alias in j["aliases"])]


def year(value):
    return type(value) is int and 1900 <= value <= 2200


def num(value, upper=math.inf):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= upper


def iso(value, optional=False):
    if value is None and optional:
        return None
    require(isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)), "Invalid ISO date")
    return date.fromisoformat(value)


def public_url(value):
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    return parts.scheme == "https" and bool(parts.hostname) and not (
        parts.username or parts.password or parts.query or parts.fragment
    )


def validate_record(record):
    keys(record, "data_year release_year release_date revision revision_date jif category_completeness category_count "
         "categories source source_url ranking last_verified verification_status public_authorized")
    require(year(record["data_year"]) and record["release_year"] == record["data_year"] + 1,
            "JCR release year must follow the data year")
    release_date = iso(record["release_date"], optional=True)
    verified_date = iso(record["last_verified"])
    revision_date = iso(record["revision_date"], optional=True)
    require(verified_date.year >= record["release_year"], "Verification precedes JCR edition")
    require(not release_date or (release_date.year == record["release_year"] and release_date <= verified_date),
            "Invalid JCR release date")
    require(type(record["revision"]) is int and record["revision"] > 0, "Invalid revision")
    require(not revision_date or (record["release_year"] <= revision_date.year and revision_date <= verified_date
            and (not release_date or release_date <= revision_date)), "Invalid revision date")
    require(record["source"] == "S2Journal" and record["ranking"] == "jcr" and public_url(record["source_url"]),
            "Use the general S2Journal JCR ranking and a public HTTPS source URL")
    require(record["public_authorized"] is True and record["verification_status"] == "verified",
            "Metric is not verified and approved for public display")
    require(num(record["jif"]), "Invalid JIF")
    categories = record["categories"]
    require(isinstance(categories, list) and categories, "Empty category list")
    count = record["category_count"]
    require(type(count) is int and count >= len(categories) and record["category_completeness"] in ("partial", "complete"),
            "Invalid category coverage")
    require((count == len(categories)) == (record["category_completeness"] == "complete"),
            "Category count conflicts with completeness")
    seen = set()
    for category in categories:
        keys(category, "name rank total quartile s2_if_percent jif_percentile rank_percent methods")
        name = category["name"]
        require(isinstance(name, str) and norm(name) and norm(name) not in seen, "Missing or duplicate category")
        seen.add(norm(name))
        rank, total = category["rank"], category["total"]
        require(all(v is None or (type(v) is int and v > 0) for v in (rank, total))
                and (rank is None or total is None or rank <= total), "Invalid category rank or total")
        require(category["quartile"] in ("Q1", "Q2", "Q3", "Q4"), "Invalid source quartile")
        require(num(category["s2_if_percent"], 100), "Invalid S2Journal IF percentage")
        require(category["jif_percentile"] is None or num(category["jif_percentile"], 100),
                "Invalid official JIF percentile")
        rank_percent = category["rank_percent"]
        require(rank_percent is None if rank is None or total is None else
                num(rank_percent, 100) and math.isclose(rank_percent, 100 * rank / total, abs_tol=1e-8),
                "Rank-based percentage disagrees with rank and total")
        require(category["methods"] == {"s2_if_percent": "source", "jif_percentile": "official",
                                       "rank_percent": "rank / total * 100"}, "Invalid calculation method")


def validate_registry(registry):
    keys(registry, "schema_version public_edition journals")
    require(type(registry["schema_version"]) is int and registry["schema_version"] == 1, "Unsupported schema")
    edition = registry["public_edition"]
    keys(edition, "data_year release_year")
    require(year(edition["data_year"]) and edition["release_year"] == edition["data_year"] + 1,
            "Invalid shared edition")
    require(isinstance(registry["journals"], list), "Missing journals list")
    seen_ids, seen_issns, seen_names = set(), {}, {}
    for journal in registry["journals"]:
        keys(journal, "journal_id official_name aliases issn eissn bibliography scie metrics")
        jid = journal["journal_id"]
        require(isinstance(jid, str) and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", jid))
                and jid not in seen_ids, "Invalid or duplicate journal ID")
        seen_ids.add(jid)
        require(isinstance(journal["aliases"], list), "Invalid aliases")
        for name in [journal["official_name"], *journal["aliases"]]:
            require(isinstance(name, str) and bool(norm(name))
                    and seen_names.setdefault(norm(name), jid) == jid, "Blank or ambiguous journal name")
        for value in (journal["issn"], journal["eissn"]):
            require(value is None or (valid_issn(value) and seen_issns.setdefault(value, jid) == jid),
                    "Invalid or duplicate ISSN")
        source = journal["bibliography"]
        keys(source, "source source_url verification_status last_verified")
        require(isinstance(source["source"], str) and source["source"].strip()
                and public_url(source["source_url"]) and source["verification_status"] in ("verified", "provided"),
                "Invalid bibliographic provenance")
        iso(source["last_verified"], optional=source["verification_status"] == "provided")
        require(isinstance(journal["scie"], list) and isinstance(journal["metrics"], list), "Invalid journal history")
        scie_years, revisions = set(), set()
        for status in journal["scie"]:
            keys(status, "year status verification_status public_authorized source source_url last_verified")
            require(year(status["year"]) and status["year"] not in scie_years and status["status"] in
                    ("indexed", "not_indexed") and status["verification_status"] == "verified"
                    and status["public_authorized"] is True and isinstance(status["source"], str)
                    and status["source"].strip() and public_url(status["source_url"]), "Invalid SCIE evidence")
            iso(status["last_verified"])
            scie_years.add(status["year"])
        for record in journal["metrics"]:
            validate_record(record)
            key = (record["data_year"], record["revision"])
            require(key not in revisions, "Duplicate JCR edition revision")
            revisions.add(key)


def validate_public_projection(registry):
    validate_registry(registry)
    for journal in registry["journals"]:
        for entry in [journal["bibliography"], *journal["scie"], *journal["metrics"]]:
            host = urlsplit(entry["source_url"]).hostname.lower().rstrip(".")
            require(host not in {"localhost", "example.com", "example.org", "example.net"}
                    and not host.endswith((".invalid", ".test", ".example", ".localhost")),
                    "Test or placeholder provenance cannot enter the public projection")


def select_metric(journal, edition, *, mode="common", year=None, publication_year=None, as_of=None):
    if mode not in ("common", "historical", "publication", "asOf"):
        return None
    eligible = []
    for record in journal["metrics"]:
        if not (record["verification_status"] == "verified" and record["public_authorized"] is True
                and record["source"] == "S2Journal" and record["ranking"] == "jcr"):
            continue
        if mode == "asOf":
            available = record["release_date"] if record["revision"] == 1 else record["revision_date"]
            if not (available and as_of and available <= as_of):
                continue
        else:
            target = {"historical": year, "publication": publication_year, "common": edition["data_year"]}[mode]
            if record["data_year"] != target or (mode == "common" and record["release_year"] != edition["release_year"]):
                continue
        eligible.append(record)
    record = max(eligible, key=lambda r: (r["data_year"], r["revision"]), default=None)
    if not record:
        return None
    try:
        validate_record(record)
    except (ValueError, KeyError, TypeError):
        return None
    if record["category_completeness"] != "complete":
        return None
    category = min(record["categories"], key=lambda c: (c["s2_if_percent"], norm(c["name"]), c["name"]))
    return record, category


def audit(registry, papers):
    journals = registry["journals"]
    edition = registry["public_edition"]
    counts = {j["journal_id"]: 0 for j in journals}
    problems = []
    for paper in papers:
        if paper["type"] != "Journal":
            continue
        matches = journal_match(paper, journals)
        if len(matches) != 1:
            problems.append((paper.get("catalog_number", paper.get("id")), "ambiguous" if matches else "unmatched"))
        else:
            counts[matches[0]["journal_id"]] += 1
    missing = []
    for journal in journals:
        if select_metric(journal, edition) is None:
            missing.append(journal["journal_id"])
    return counts, problems, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / "data/journals.json")
    parser.add_argument("--publications", type=Path, default=ROOT / "data/publications.json")
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        validate_public_projection(registry)
        counts, problems, missing = audit(registry, json.loads(args.publications.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"Journal validation failed: {exc}\n")
    print("Catalog match counts:", json.dumps(counts))
    print("Missing or incomplete common-edition metrics:", ", ".join(missing) or "none")
    for label, issue in problems:
        print(f"Journal review required for {label}: {issue}")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
