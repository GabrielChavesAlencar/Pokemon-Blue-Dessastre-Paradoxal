"""Original Blue schematic; no donor art, font, pixels or navigation claims."""
import struct
import zlib

WIDTH, HEIGHT = 480, 320
PROVENANCE = b"Blue authored schematic v1"
# Original 5x7 glyphs for the labels.
FONT = {
    "A": (14,17,17,31,17,17,17), "B": (30,17,17,30,17,17,30),
    "C": (14,17,16,16,16,17,14), "D": (30,17,17,17,17,17,30),
    "E": (31,16,16,30,16,16,31), "F": (31,16,16,30,16,16,16),
    "G": (14,17,16,23,17,17,15), "H": (17,17,17,31,17,17,17),
    "I": (31,4,4,4,4,4,31), "J": (7,2,2,2,18,18,12),
    "K": (17,18,20,24,20,18,17), "L": (16,16,16,16,16,16,31),
    "M": (17,27,21,21,17,17,17), "N": (17,25,21,19,17,17,17),
    "O": (14,17,17,17,17,17,14), "P": (30,17,17,30,16,16,16),
    "Q": (14,17,17,17,21,18,13), "R": (30,17,17,30,20,18,17),
    "S": (15,16,16,14,1,1,30), "T": (31,4,4,4,4,4,4),
    "U": (17,17,17,17,17,17,14), "V": (17,17,17,17,17,10,4),
    "W": (17,17,17,21,21,21,10), "X": (17,17,10,4,10,17,17),
    "Y": (17,17,10,4,4,4,4), "Z": (31,1,2,4,8,16,31),
    " ": (0,0,0,0,0,0,0), "-": (0,0,0,31,0,0,0),
}
# Hand-authored overview, not donor coordinates or a traversal graph.
PLACES = (
    ("INDIGO", 54, 77, 20, 55), ("PEWTER", 122, 87, 99, 61),
    ("CERULEAN", 275, 83, 240, 55), ("VIRIDIAN", 117, 154, 48, 133),
    ("CELADON", 222, 154, 188, 129), ("SAFFRON", 285, 154, 259, 173),
    ("LAVENDER", 407, 154, 374, 129), ("PALLET", 117, 220, 52, 210),
    ("VERMILION", 285, 219, 258, 198), ("FUCHSIA", 227, 268, 193, 244),
    ("CINNABAR", 107, 268, 56, 244),
)


def render_wall_atlas():
    """Deterministic RGB PNG, no third-party Python dependencies."""
    pixels = bytearray(bytes((23, 39, 54)) * WIDTH * HEIGHT)

    def rect(x, y, w, h, color):
        if not (0 <= x <= x+w <= WIDTH and 0 <= y <= y+h <= HEIGHT):
            raise ValueError("Atlas drawing outside canvas")
        row = bytes(color) * w
        for yy in range(y, y+h):
            start = (yy*WIDTH+x)*3
            pixels[start:start+len(row)] = row

    def label(x, y, value, scale, color):
        for char in value:
            for dy, bits in enumerate(FONT[char]):
                for dx in range(5):
                    if bits & (1 << (4-dx)):
                        rect(x+dx*scale, y+dy*scale, scale, scale, color)
            x += 6*scale

    rect(10, 10, 460, 300, (35, 59, 73))
    rect(12, 12, 456, 33, (13, 27, 39))
    rect(12, 46, 456, 241, (24, 45, 57))
    for x in range(28, 467, 24):
        rect(x, 47, 1, 239, (35, 57, 68))
    for y in range(58, 287, 24):
        rect(13, y, 454, 1, (35, 57, 68))
    label(23, 20, "KANTO", 3, (240, 248, 246))
    label(343, 25, "BLUE - ATLAS", 1, (118, 217, 200))
    for name, x, y, tx, ty in PLACES:
        rect(x-4, y-4, 9, 9, (8, 20, 27))
        rect(x-2, y-2, 5, 5, (118, 217, 200))
        rect(tx-2, ty-2, len(name)*6+3, 11, (13, 27, 39))
        label(tx, ty, name, 1, (241, 244, 242))
    label(24, 296, "ESQUEMA - NAO INDICA ACESSOS", 1, (194, 212, 216))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data +
                struct.pack(">I", zlib.crc32(kind+data) & 0xffffffff))

    raw = b"".join(b"\x00" + pixels[y*WIDTH*3:(y+1)*WIDTH*3] for y in range(HEIGHT))
    # Fixed stored DEFLATE blocks keep bytes stable across zlib versions.
    blocks = [raw[i:i+65535] for i in range(0, len(raw), 65535)]
    compressed = b"\x78\x01" + b"".join(
        bytes((int(i == len(blocks)-1),)) +
        struct.pack("<HH", len(block), 65535-len(block)) + block
        for i, block in enumerate(blocks))
    compressed += struct.pack(">I", zlib.adler32(raw) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)) +
            chunk(b"tEXt", b"Description\x00" + PROVENANCE) +
            chunk(b"IDAT", compressed) + chunk(b"IEND", b""))
