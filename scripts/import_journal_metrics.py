#!/usr/bin/env python3
"""Project approved S2Journal rows into the public registry, dry-run by default."""
import argparse
import csv
from datetime import date, datetime
import difflib
import json
import os
from pathlib import Path
import tempfile

from validate_journal_metrics import (ROOT, audit, journal_match, require,
                                      validate_public_projection, validate_record, validate_registry)

COLUMNS = ("journal_id issn eissn official_name data_year release_year release_date revision revision_date "
           "jif category_count category_completeness category rank total quartile s2_if_percent jif_percentile "
           "source source_url ranking last_verified verification_status public_authorized").split()
TEMPLATE = ROOT / "docs/jcr-metrics-template.csv"


def read_rows(path):
    if path.suffix.lower() == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ValueError("XLSX imports require openpyxl; CSV uses the standard library") from exc
        book = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            sheet = book["JCR"] if "JCR" in book.sheetnames else book.active
            return list(sheet.values)
        finally:
            book.close()
    require(path.suffix.lower() == ".csv", "Use a CSV or XLSX file")
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.reader(file))


def text(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return "" if value is None else str(value).strip()


def integer(value):
    require(value.lstrip("-").isascii() and value.lstrip("-").isdigit(), "Invalid integer field")
    return int(value)


def read_projection(path, journals):
    incoming = read_rows(path)
    require(incoming, "Missing input header")
    headers = [text(cell) for cell in incoming[0]]
    require(len(headers) == len(COLUMNS) and set(headers) == set(COLUMNS),
            "Use the public template columns; extra and duplicate columns are rejected")
    grouped, issues = {}, []
    for line, cells in enumerate(incoming[1:], 2):
        if not any(text(cell) for cell in cells):
            continue
        try:
            require(len(cells) == len(headers), "Invalid number of cells")
            row = dict(zip(headers, map(text, cells)))
            require(not any(value.startswith("=") for value in row.values()), "Formula cells are not accepted")
            require(row["public_authorized"].lower() == "true" and row["verification_status"] == "verified",
                    "Row has no verified public approval")
            matches = journal_match({**row, "type": "Journal", "venue": row["official_name"]}, journals)
            require(len(matches) == 1, "Ambiguous journal mapping" if matches else
                    "New or unmatched journal; review and register its public bibliography first")
            journal = matches[0]
            for field in ("issn", "eissn"):
                require(not row[field] or row[field].upper() == journal[field], "Journal identifier conflicts with registry")
            metric = {key: integer(row[key]) for key in ("data_year", "release_year", "revision", "category_count")}
            metric.update({key: row[key] for key in ("category_completeness", "source", "source_url", "ranking",
                                                     "last_verified", "verification_status")})
            metric.update(jif=float(row["jif"]), release_date=row["release_date"] or None,
                          revision_date=row["revision_date"] or None, public_authorized=True)
            rank = integer(row["rank"]) if row["rank"] else None
            total = integer(row["total"]) if row["total"] else None
            require(not (rank is not None and total is not None) or 1 <= rank <= total,
                    "Invalid category rank or total")
            category = dict(name=row["category"], rank=rank, total=total, quartile=row["quartile"],
                            s2_if_percent=float(row["s2_if_percent"].removesuffix("%")),
                            jif_percentile=float(row["jif_percentile"]) if row["jif_percentile"] else None,
                            rank_percent=100 * rank / total if rank is not None and total is not None else None,
                            methods={"s2_if_percent": "source", "jif_percentile": "official",
                                     "rank_percent": "rank / total * 100"})
            key = (journal["journal_id"], metric["data_year"], metric["revision"])
            old_metric, categories = grouped.setdefault(key, (metric, []))
            require(old_metric == metric, "Inconsistent edition metadata across category rows")
            categories.append(category)
        except ValueError as exc:
            message = str(exc)
            if "could not convert" in message or "invalid literal" in message:
                message = "Invalid numeric value"
            issues.append(f"Row {line}: {message}")
    require(not issues, "\n".join(issues))
    for key, (metric, categories) in grouped.items():
        record = {**metric, "categories": sorted(categories, key=lambda c: c["name"].casefold())}
        validate_record(record)
        yield key, record


def apply_projection(registry, path):
    journals = {j["journal_id"]: j for j in registry["journals"]}
    for (jid, data_year, revision), record in read_projection(path, registry["journals"]):
        records = journals[jid]["metrics"]
        prior = [r for r in records if r["data_year"] == data_year]
        same = next((r for r in prior if r["revision"] == revision), None)
        if same is not None:
            require({**same, "categories": sorted(same["categories"], key=lambda c: c["name"].casefold())}
                    == record, f"{jid} {data_year} revision {revision} already exists; use a new revision")
            continue
        require(revision > max((r["revision"] for r in prior), default=0),
                f"{jid} {data_year}: new revisions must increase")
        records.append(record)
        records.sort(key=lambda r: (r["data_year"], r["revision"]))
    validate_registry(registry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--registry", type=Path, default=ROOT / "data/journals.json")
    parser.add_argument("--apply", action="store_true", help="Write the approved projection after validation")
    parser.add_argument("--template", action="store_true", help="Print the CSV template")
    args = parser.parse_args()
    if args.template:
        print(TEMPLATE.read_text(encoding="utf-8"), end="")
        return
    if not args.input:
        parser.error("provide an approved input file or --template")
    try:
        before = args.registry.read_text(encoding="utf-8")
        registry = json.loads(before)
        validate_registry(registry)
        apply_projection(registry, args.input)
        validate_public_projection(registry)
        _, problems, missing = audit(registry, json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8")))
        after = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
        if before == after:
            print("No registry changes.")
        else:
            diff = difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile="current public registry", tofile="proposed public registry")
            print("".join(diff), end="")
            if args.apply:
                # Replace only after complete validation, without leaving a partial registry.
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.registry.parent,
                                                 delete=False) as file:
                    temporary = Path(file.name)
                    file.write(after)
                try:
                    temporary.chmod(args.registry.stat().st_mode & 0o777)
                    os.replace(temporary, args.registry)
                finally:
                    temporary.unlink(missing_ok=True)
            else:
                print("Dry-run: no file written.")
        print("Missing or incomplete common-edition metrics:", ", ".join(missing) or "none")
        for label, issue in problems:
            print(f"Journal review required for {label}: {issue}")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"Journal import rejected: {exc}\n")


if __name__ == "__main__":
    main()
