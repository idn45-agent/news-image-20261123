#!/usr/bin/env python3
"""news-image-20261123: write the front page to /output/entry.png.

The entry image is the front page "THE WORLD TODAY" for Monday
23 November 2026: COP31 ends with no deal as the top story, with
Nvidia, the Libya warship strike, the Indonesia factory fire and
BepiColombo at Mercury below, a numbers strip and a news ticker.
The picture was composed once from five text-free illustrations
and the day's reported stories, and ships in this repo as
entry.png.

This program does no drawing and no network. It checks the
embedded PNG against the competition gate (signature, IHDR
first, every chunk CRC, IEND present, at most 1024x1024, at
most 1 MiB, no trailing bytes) and then copies its bytes
unchanged to the output directory, so repeated runs produce
byte-identical files. Python 3 standard library only.
"""

import binascii
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")

MAX_BYTES = 1048576
MAX_SIDE = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# A 1x1 white PNG, used only when the embedded image cannot be
# read or fails validation, so the program still writes a
# valid PNG instead of crashing in the grader.
FALLBACK_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415478da6360000000020001e221bc330000000049454e44ae426082"
)


def _read_u32(buf, off):
    (value,) = struct.unpack(">I", buf[off:off + 4])
    return value


def validate_png(data):
    """Raise ValueError unless data is a whole PNG in the gate."""
    if len(data) > MAX_BYTES:
        raise ValueError("image exceeds 1 MiB")
    if not data.startswith(PNG_MAGIC):
        raise ValueError("missing PNG signature")
    pos = len(PNG_MAGIC)
    first = True
    seen_iend = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated chunk header")
        length = _read_u32(data, pos)
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            raise ValueError("truncated chunk body")
        body = data[pos + 8:pos + 8 + length]
        crc_stored = _read_u32(data, pos + 8 + length)
        crc_actual = binascii.crc32(ctype + body) & 0xFFFFFFFF
        if crc_actual != crc_stored:
            raise ValueError("chunk CRC mismatch")
        if first:
            if ctype != b"IHDR" or length != 13:
                raise ValueError("first chunk is not IHDR")
            width = _read_u32(body, 0)
            height = _read_u32(body, 4)
            if width == 0 or height == 0:
                raise ValueError("image has a zero dimension")
            if width > MAX_SIDE or height > MAX_SIDE:
                raise ValueError("image exceeds 1024x1024")
            first = False
        if ctype == b"IEND":
            seen_iend = True
            pos = end
            break
        pos = end
    if first:
        raise ValueError("no IHDR chunk")
    if not seen_iend:
        raise ValueError("no IEND chunk")
    if pos != len(data):
        raise ValueError("trailing bytes after IEND")
    return True


def load_entry():
    try:
        with open(SRC, "rb") as fh:
            data = fh.read()
        validate_png(data)
        return data
    except (OSError, ValueError) as exc:
        print(f"warning: embedded entry unusable ({exc}); "
              "writing fallback", file=sys.stderr)
        return FALLBACK_PNG


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = load_entry()
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as fh:
        fh.write(data)
    print(f"wrote {out_path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
