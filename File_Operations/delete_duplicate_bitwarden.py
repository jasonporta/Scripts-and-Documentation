#!/usr/bin/env python3
"""
Remove duplicate entries from a Bitwarden JSON export.

Bitwarden export items have a "type" field:
    1 = Login
    2 = Secure Note
    3 = Card
    4 = Identity

Two items are considered duplicates if they share the same type and the
same "signature" of relevant fields (see build_signature). The FIRST
occurrence of each duplicate is kept; later ones are dropped.

Usage:
    python delete_duplicate_bitwarden.py input.json -o output.json
    python delete_duplicate_bitwarden.py input.json -o output.json --dry-run

IMPORTANT: This script only works correctly on an UNENCRYPTED Bitwarden
export ("encrypted": false in the JSON). If your export is
password-protected/encrypted, decrypt/export again as unencrypted JSON
first (Bitwarden > Tools > Export Vault > .json, not the encrypted
option).
"""

import argparse
import json
import sys
from collections import defaultdict

TYPE_NAMES = {1: "Login", 2: "Secure Note", 3: "Card", 4: "Identity"}


def norm(value):
    """Normalize a string field for comparison (case/whitespace-insensitive)."""
    if value is None:
        return ""
    return str(value).strip().lower()


def build_signature(item):
    """
    Build a tuple that identifies "the same entry" for dedup purposes.
    Adjust this function if you want looser/stricter matching.
    """
    item_type = item.get("type")
    name = norm(item.get("name"))

    if item_type == 1:  # Login
        login = item.get("login") or {}
        username = norm(login.get("username"))
        password = login.get("password") or ""  # keep case-sensitive
        uris = login.get("uris") or []
        uri_set = frozenset(norm(u.get("uri")) for u in uris if u.get("uri"))
        return ("login", name, username, password, uri_set)

    if item_type == 2:  # Secure Note
        notes = norm(item.get("notes"))
        return ("note", name, notes)

    if item_type == 3:  # Card
        card = item.get("card") or {}
        return (
            "card",
            name,
            norm(card.get("cardholderName")),
            norm(card.get("brand")),
            norm(card.get("number")),
            norm(card.get("expMonth")),
            norm(card.get("expYear")),
        )

    if item_type == 4:  # Identity
        identity = item.get("identity") or {}
        return (
            "identity",
            name,
            norm(identity.get("firstName")),
            norm(identity.get("lastName")),
            norm(identity.get("email")),
            norm(identity.get("phone")),
        )

    # Fallback: unknown type, just compare by name + full JSON blob
    return ("other", name, json.dumps(item, sort_keys=True))


def delete_items(items):
    """
    Return (kept_items, removed_items) — first occurrence of each
    signature is kept, later duplicates are removed.
    """
    seen = {}
    kept = []
    removed = []

    for item in items:
        sig = build_signature(item)
        if sig in seen:
            removed.append(item)
        else:
            seen[sig] = item
            kept.append(item)

    return kept, removed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Path to the Bitwarden JSON export file")
    parser.add_argument("-o", "--output", help="Path to write the deduplicated JSON (default: <input>.deleted.json)")
    parser.add_argument("--dry-run", action="store_true", help="Report duplicates without writing an output file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("encrypted"):
        print("ERROR: This export is marked as encrypted. Re-export your vault as an", file=sys.stderr)
        print("unencrypted JSON file (Bitwarden > Tools > Export Vault) and try again.", file=sys.stderr)
        sys.exit(1)

    items = data.get("items", [])
    kept, removed = delete_items(items)

    print(f"Total items:      {len(items)}")
    print(f"Duplicates found: {len(removed)}")
    print(f"Items kept:       {len(kept)}")

    if removed:
        print("\nRemoved duplicates:")
        by_type = defaultdict(int)
        for item in removed:
            by_type[item.get("type")] += 1
            name = item.get("name", "(no name)")
            type_label = TYPE_NAMES.get(item.get("type"), "Unknown")
            print(f"  - [{type_label}] {name} (id={item.get('id')})")
        print("\nSummary by type:")
        for t, count in by_type.items():
            print(f"  {TYPE_NAMES.get(t, 'Unknown')}: {count}")

    if args.dry_run:
        print("\nDry run — no output file written.")
        return

    output_path = args.output or (args.input.rsplit(".json", 1)[0] + ".deleted.json")
    data["items"] = kept
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nDeduplicated export written to: {output_path}")
    print("Review it, then re-import into Bitwarden (this does not modify your live vault).")


if __name__ == "__main__":
    main()
