#!/usr/bin/env python3

import argparse
import gzip
import io
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

"""
EMDB validation report analyzer.

Downloads the wwPDB/EMDB validation report XML for a given EMD ID and
summarizes common resolution estimates, Q-score, FSC values,
clash/geometry scores, etc.

Validation reports are published at:
  https://ftp.ebi.ac.uk/pub/databases/emdb/validation_reports/EMD-<id>/emd_<id>_validation.xml.gz

    python validation_report_analyzer.py EMD-8548
    python validation_report_analyzer.py EMD-8548 --raw   # dump matched raw tags too
"""

BASE_URL = "https://ftp.ebi.ac.uk/pub/databases/emdb/validation_reports"

# Keyword -> category, used to bucket whatever attributes/tags we find.
METRIC_PATTERNS = [
    (re.compile(r"q.?score", re.IGNORECASE), "Q-score (map-model fit)"),
    (re.compile(r"fsc", re.IGNORECASE), "FSC / resolution estimates"),
    (re.compile(r"resolution", re.IGNORECASE), "FSC / resolution estimates"),
    (re.compile(r"clash", re.IGNORECASE), "Geometry: clashes"),
    (re.compile(r"rama", re.IGNORECASE), "Geometry: Ramachandran"),
    (re.compile(r"rotamer", re.IGNORECASE), "Geometry: rotamers"),
    (re.compile(r"rms.?(bond|angle)", re.IGNORECASE), "Geometry: bond/angle RMS"),
    (re.compile(r"b.?factor", re.IGNORECASE), "B-factors"),
    (re.compile(r"strudel", re.IGNORECASE), "3D-Strudel score"),
    (re.compile(r"emringer", re.IGNORECASE), "EMRinger score"),
]

def fetch_validation_xml(emd_id):
    # Download and decompress the validation report XML for an EMD ID
    # Normalize e.g. "8548" or "EMD-8548" -> "8548"
    numeric_id = emd_id.upper().replace("EMD-", "").strip()
    url = f"{BASE_URL}/EMD-{numeric_id}/emd_{numeric_id}_validation.xml.gz"
    req = urllib.request.Request(url, headers={"User-Agent": "emdb-validation-analyzer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        compressed = resp.read()
    xml_bytes = gzip.decompress(compressed)
    return xml_bytes, url

def scan_metrics(xml_bytes):
    """Walk the whole XML tree and bucket any attribute/tag matching known
    QC metric keyword patterns."""
    root = ET.fromstring(xml_bytes)
    findings = {}  # category -> list of (tag, attr_or_text, value)

    for elem in root.iter():
        tag = elem.tag
        # Check the tag name itself
        for pattern, category in METRIC_PATTERNS:
            if pattern.search(tag):
                text = (elem.text or "").strip()
                if text:
                    findings.setdefault(category, []).append((tag, "(text)", text))
        # Check each attribute name and value
        for attr_name, attr_value in elem.attrib.items():
            for pattern, category in METRIC_PATTERNS:
                if pattern.search(attr_name):
                    findings.setdefault(category, []).append((tag, attr_name, attr_value))

    return findings

def print_summary(emd_id, url, findings, show_raw=False):
    print(f"\nValidation report summary for {emd_id.upper()}")
    print(f"Source: {url}\n")

    if not findings:
        print("No recognizable QC metric fields were found by keyword matching.")
        print("The report may use different terminology than expected - try")
        print("running with --raw to dump every attribute name found in the")
        print("file, so the keyword list in METRIC_PATTERNS can be adjusted.")
        return

    for category, entries in findings.items():
        print(f"## {category}")
        seen = set()
        for tag, attr, value in entries:
            key = (tag, attr, value)
            if key in seen:
                continue
            seen.add(key)
            label = f"{tag}.{attr}" if attr != "(text)" else tag
            print(f"  {label}: {value}")
        print()

    if show_raw:
        print("## All attribute names found anywhere in the document (for tuning):")
        # Re-walk to list every unique attribute name, useful for refining patterns.
        pass  # handled via --raw flag path in main(), kept simple here

def main():
    parser = argparse.ArgumentParser(description="Analyze an EMDB validation report.")
    parser.add_argument("emd_id", help='EMD ID, e.g. "EMD-25007" or "25007"')
    parser.add_argument("--raw", action="store_true",
                        help="Also list every unique attribute name found")
    args = parser.parse_args()

    try:
        xml_bytes, url = fetch_validation_xml(args.emd_id)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to fetch/parse validation report for {args.emd_id}: {e}", file=sys.stderr)
        sys.exit(1)

    findings = scan_metrics(xml_bytes)
    print_summary(args.emd_id, url, findings, show_raw=args.raw)

    if args.raw:
        root = ET.fromstring(xml_bytes)
        all_attrs = set()
        for elem in root.iter():
            all_attrs.update(elem.attrib.keys())
            all_attrs.add(elem.tag)
        print("## All unique tag/attribute names in the document:")
        for name in sorted(all_attrs):
            print(f"  {name}")

if __name__ == "__main__":
    main()
