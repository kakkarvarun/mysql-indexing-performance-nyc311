# scripts/normalize_csv.py
import csv, sys, argparse, re

TARGET_HEADERS = [
    "Created Date", "Closed Date", "Complaint Type", "Descriptor",
    "Borough", "Incident Zip", "Status", "Resolution Description",
    "Latitude", "Longitude"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    args = ap.parse_args()

    # open with newline='' so csv handles newlines correctly (writes CRLF on Windows)
    with open(args.src, "r", encoding="utf-8", newline="") as fin, \
         open(args.dst, "w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        # map headers case-insensitively
        field_map = {h.lower(): h for h in reader.fieldnames or []}

        def pick(row, name):
            # grab by exact header if present, else by case-insensitive key
            if name in row:
                return row[name]
            l = name.lower()
            return row.get(field_map.get(l, ""), "")

        writer = csv.writer(fout)
        writer.writerow(TARGET_HEADERS)
        for r in reader:
            out_row = [
                pick(r, "Created Date"),
                pick(r, "Closed Date"),
                pick(r, "Complaint Type"),
                pick(r, "Descriptor"),
                pick(r, "Borough"),
                pick(r, "Incident Zip"),
                pick(r, "Status"),
                pick(r, "Resolution Description"),
                pick(r, "Latitude"),
                pick(r, "Longitude"),
            ]
            writer.writerow(out_row)

if __name__ == "__main__":
    main()
