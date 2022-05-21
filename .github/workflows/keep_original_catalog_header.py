import glob
import sys
from pathlib import Path

if len(sys.argv) != 5:
    print("Usage: keep_original_catalog_header.py <new-header-length> <new-locales-dir> <old-header-length> <old-locales-dir>")
    sys.exit(1)

new_header_length = int(sys.argv[1])
new_locales_path = sys.argv[2]
old_header_length = int(sys.argv[3])
old_locales_path = sys.argv[4]

for path in glob.glob(str(Path(new_locales_path) / "**" / "*.po"), recursive=True):
    if "en_US" in path:
        continue

    with open(path.replace(new_locales_path, old_locales_path), "r") as f:
        old_header = [f.readline() for _ in range(old_header_length)]

    with open(path, "r") as f:
        lines = f.readlines()

    revision_dates = lines[5:7]

    del lines[:new_header_length]

    old_header[4:6] = revision_dates
    lines = old_header + lines

    with open(path, "w") as f:
        f.writelines(lines)
