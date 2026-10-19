"""Convert lxe's expert-rank.json (dsx builds) into the rank file Xolotl's --rank flag reads.

expert-rank.json is a list of [layer, expert, score] sorted hottest first. Xolotl's rank file is the same order as
little-endian int32 pairs (layer, expert), 8 bytes each.

  python scripts\\rank_json_to_bin.py D:\\models\\dsv41-1017-dsx\\expert-rank.json D:\\models\\dsv41-1017-dsx\\rank-dsx.bin
"""
import json
import struct
import sys

src, dst = sys.argv[1], sys.argv[2]
rows = json.load(open(src, encoding="utf-8"))
pairs = {(layer, expert) for layer, expert, _ in rows}
if len(pairs) != len(rows):
    sys.exit("duplicate (layer, expert) entries in the ranking")
if any(rows[i][2] < rows[i + 1][2] for i in range(len(rows) - 1)):
    sys.exit("the ranking is not sorted hottest first")
with open(dst, "wb") as f:
    for layer, expert, _ in rows:
        f.write(struct.pack("<ii", layer, expert))
print(f"{dst}: {len(rows)} experts, {8 * len(rows)} bytes "
      f"(layers {min(r[0] for r in rows)}-{max(r[0] for r in rows)}, experts {min(r[1] for r in rows)}-{max(r[1] for r in rows)})")
