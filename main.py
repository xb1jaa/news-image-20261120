#!/usr/bin/env python3
"""news-image-20261120: sum up Friday 20 November 2026 in one image.

A newspaper front page drawn two ways: with Pillow (DejaVu fonts) when
it is installed, and with a pure-stdlib pixel renderer otherwise. The
grader runs python:3.13-slim, standard library only, so a PIL-only
program would fail there. Both paths draw the same page, the same
stories, at the same size, with no network and no randomness, so two
runs in the same environment write byte-identical PNGs.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Test the stdlib path locally: MAKEFUN_FORCE_STDLIB=1 MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (17, 17, 17)
GREY = (90, 88, 82)
RED = (163, 18, 26)
BLUE = (26, 58, 92)
LIGHT = (232, 228, 216)
SKY = (178, 214, 235)
OCEAN = (38, 84, 138)
LAND = (74, 140, 74)
GOLD = (212, 160, 32)

# Stories verified from the day's news wires (20 November 2026).
LEAD = (
    "CLIMATE  \u2022  ANTALYA",
    "COP31 DRAFT DROPS FOSSIL FUELS",
    "Final-day text omits any fossil-fuel phaseout and the $120bn "
    "adaptation target. Talks may run into the weekend.",
    RED,
)

COLUMNS = [
    # (kicker, headline, body, colour)
    ("JUSTICE  \u2022  THE HAGUE", "MYANMAR GUILTY OF GENOCIDE",
     "UN court rules the 2017 campaign against the Rohingya was "
     "genocide.", RED),
    ("DIPLOMACY  \u2022  SHENZHEN", "TRUMP, XI AND PUTIN MEET",
     "First trilateral summit ends with a four-point peace "
     "declaration.", BLUE),
    ("BUSINESS  \u2022  NEW YORK", "ANTHROPIC SOARS ON DEBUT",
     "Shares close 17% above the $83 IPO price in the biggest "
     "IPO ever.", BLUE),
]

PAIRS = [
    ("CONFLICT  \u2022  THE GULF", "IRAN WIDENS GULF ATTACKS",
     "Tanker strikes spread to Bahrain and Kuwait. The IEA calls "
     "it the biggest energy threat in history.", RED),
    ("MARKETS", "STOCKS SLIDE FOR FIFTH DAY",
     "S&P 500 falls 2.0% and Nikkei drops 4.68% as AI fears hit "
     "shares.", BLUE),
]

BRIEFS = [
    "SOMALIA EXPELS UAE ENVOY",
    "META RETHINKS 2030 NET-ZERO GOAL",
    "65,000 GAZA TENTS AWAIT ENTRY",
    "FIONA THE HIPPO DIES",
]


# ---------------------------------------------------------------- font (stdlib path)
# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows
# of 5 bits, '#' on and '.' off.
FONT_5X7 = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '\u2022': ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def wrap_text(text, max_width, measure):
    """Wrap text to lines fitting max_width (measure: text -> pixels)."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if measure(trial) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- backends
class PilBackend:
    """Draw with Pillow + DejaVu. Used locally, where Pillow is installed."""

    def __init__(self):
        from PIL import Image, ImageDraw
        self._Image = Image
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def font(self, size, bold=False, serif=False):
        key = (size, bold, serif)
        if key not in self._fonts:
            from PIL import ImageFont
            if serif:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
            elif bold:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            else:
                path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            self._fonts[key] = ImageFont.truetype(path, size)
        return self._fonts[key]

    def measure(self, text, size, bold=False, serif=False):
        return self.font(size, bold, serif).getlength(text)

    def rect(self, x, y, w, h, fill):
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill)

    def ellipse(self, x, y, w, h, fill):
        self.d.ellipse([x, y, x + w - 1, y + h - 1], fill=fill)

    def text(self, x, y, s, size, fill, bold=False, serif=False, centre=False):
        f = self.font(size, bold, serif)
        if centre:
            x = x - int(f.getlength(s) // 2)
        self.d.text((x, y), s, font=f, fill=fill)

    def save(self, path):
        self.img.save(path, format="PNG", compress_level=9)


class PixelBackend:
    """Draw into a plain RGB bytearray and encode PNG with zlib only."""

    def __init__(self):
        self.pix = bytearray(PAPER * (W * H))

    def _scale(self, size):
        return max(1, int(round(size / 7.0)))

    def measure(self, text, size, bold=False, serif=False):
        return len(text) * 6 * self._scale(size)

    def rect(self, x, y, w, h, fill):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        for yy in range(y0, y1):
            base = yy * W * 3
            for xx in range(x0, x1):
                o = base + xx * 3
                self.pix[o:o + 3] = bytes(fill)

    def ellipse(self, x, y, w, h, fill):
        cx, cy, rx, ry = x + w / 2.0, y + h / 2.0, w / 2.0, h / 2.0
        for yy in range(max(0, y), min(H, y + h)):
            dy = (yy + 0.5 - cy) / ry
            if abs(dy) > 1:
                continue
            dx = rx * (1 - dy * dy) ** 0.5
            self.rect(int(cx - dx), yy, int(2 * dx), 1, fill)

    def text(self, x, y, s, size, fill, bold=False, serif=False, centre=False):
        sc = self._scale(size)
        if centre:
            x = x - self.measure(s, size) // 2
        s = s.upper()
        for ci, ch in enumerate(s):
            glyph = FONT_5X7.get(ch, FONT_5X7[' '])
            gx = x + ci * 6 * sc
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '1':
                        self.rect(gx + col * sc, y + row * sc, sc, sc, fill)
                        if bold:
                            self.rect(gx + col * sc + 1, y + row * sc, sc, sc, fill)

    def save(self, path):
        raw = b"".join(b"\x00" + bytes(self.pix[yy * W * 3:(yy + 1) * W * 3])
                       for yy in range(H))

        def chunk(kind, data):
            c = struct.pack(">I", len(data)) + kind + data
            return c + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

        ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
               + chunk(b"IDAT", zlib.compress(raw, 9))
               + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(png)


# ---------------------------------------------------------------- layout
def draw_block(b, x, y, max_w, lines, size, fill, bold=False, serif=False):
    for i, line in enumerate(lines):
        b.text(x, y + i * (size + 6), line, size, fill, bold=bold, serif=serif)
    return y + len(lines) * (size + 6)


def draw_card(b, x, y, w, h, kicker, headline, body, colour,
              head_sizes=(26, 24, 22), body_sizes=(18, 16, 14)):
    """A story card: tinted panel, colour bar, kicker, headline, body."""
    b.rect(x, y, w, h, LIGHT)
    b.rect(x, y, w, 5, colour)
    b.text(x + 14, y + 14, kicker, 15, colour, bold=True)
    picked = None
    for hs, bs in zip(head_sizes, body_sizes):
        hl = wrap_text(headline, w - 28, lambda t, s=hs: b.measure(t, s, serif=True))
        bl = wrap_text(body, w - 28, lambda t, s=bs: b.measure(t, s))
        picked = (hs, bs, hl, bl)
        tall = 38 + min(len(hl), 3) * (hs + 6) + 2 + min(len(bl), 3) * (bs + 6)
        if len(hl) <= 3 and len(bl) <= 3 and tall <= h - 8:
            break
    hs, bs, hl, bl = picked
    draw_block(b, x + 14, y + 38, w - 28, hl[:3], hs, INK, serif=True)
    by = y + 38 + min(len(hl), 3) * (hs + 6)
    draw_block(b, x + 14, by + 2, w - 28, bl[:3], bs, GREY)


def draw_globe(b, x, y, w, h):
    """Warming planet: blue globe, green land, red rising arrow, 1.5C tag."""
    b.rect(x, y, w, h, SKY)
    cx, cy, r = x + w // 2, y + h // 2 - 6, 62
    b.ellipse(cx - r, cy - r, 2 * r, 2 * r, OCEAN)
    # land blobs, clipped roughly inside the circle by their placement
    b.ellipse(cx - 44, cy - 38, 44, 26, LAND)
    b.ellipse(cx + 6, cy - 26, 40, 30, LAND)
    b.ellipse(cx - 30, cy + 12, 52, 24, LAND)
    b.ellipse(cx + 22, cy + 22, 26, 16, LAND)
    # rising arrow, bottom-left to top-right, as stepped squares
    steps = 18
    x0, y0 = x + 22, y + h - 34
    x1, y1 = x + w - 34, y + 26
    for i in range(steps + 1):
        px = int(x0 + (x1 - x0) * i / steps)
        py = int(y0 + (y1 - y0) * i / steps)
        b.rect(px - 3, py - 3, 7, 7, RED)
    # arrowhead
    b.rect(x1 - 14, y1 - 2, 16, 6, RED)
    b.rect(x1 - 2, y1 - 14, 6, 16, RED)
    b.text(x + 12, y + h - 26, "1.5C", 22, RED, bold=True)


def draw_page(b):
    # outer frame
    b.rect(14, 14, W - 28, 2, INK)
    b.rect(14, H - 16, W - 28, 2, INK)
    b.rect(14, 14, 2, H - 28, INK)
    b.rect(W - 16, 14, 2, H - 28, INK)

    # masthead
    b.text(W // 2, 32, "THE DAILY WORLD", 58, INK, bold=True, serif=True, centre=True)
    b.text(W // 2, 104, "THE WORLD IN ONE PAGE", 16, GREY, bold=True, centre=True)
    b.rect(36, 130, W - 72, 3, RED)
    b.text(W // 2, 142, "FRIDAY  \u2022  20 NOVEMBER 2026", 26, RED, bold=True, centre=True)
    b.rect(36, 180, W - 72, 2, GREY)

    # lead story, full width, globe graphic on the right
    kicker, headline, body, colour = LEAD
    b.rect(36, 196, W - 72, 244, (255, 255, 255))
    b.rect(36, 196, W - 72, 5, colour)
    b.text(56, 212, kicker, 18, colour, bold=True)
    # Shrink until the headline fits in two lines and the body in four.
    # The stdlib bitmap font is wider per character than DejaVu, so it
    # needs the smaller sizes; the PIL path takes the first pair.
    picked = None
    for hs, bs in [(40, 20), (34, 18), (30, 16)]:
        hl = wrap_text(headline, 600, lambda t, s=hs: b.measure(t, s, serif=True))
        bl = wrap_text(body, 600, lambda t, s=bs: b.measure(t, s))
        picked = (hs, bs, hl, bl)
        tall = 48 + len(hl) * (hs + 6) + 12 + len(bl) * (bs + 6)
        if len(hl) <= 2 and len(bl) <= 4 and tall <= 236:
            break
    hs, bs, hl, bl = picked
    draw_block(b, 56, 244, 600, hl, hs, INK, serif=True)
    draw_block(b, 56, 244 + len(hl) * (hs + 6) + 12, 600, bl, bs, GREY)
    draw_globe(b, 700, 212, 268, 212)

    # three stories side by side
    gy, cw, ch, gap = 456, 304, 196, 20
    for i, (kicker, headline, body, colour) in enumerate(COLUMNS):
        draw_card(b, 36 + i * (cw + gap), gy, cw, ch,
                  kicker, headline, body, colour)

    # two stories side by side
    gy2, cw2, ch2 = 660, 466, 156
    for i, (kicker, headline, body, colour) in enumerate(PAIRS):
        draw_card(b, 36 + i * (cw2 + gap), gy2, cw2, ch2,
                  kicker, headline, body, colour,
                  head_sizes=(24, 22, 20), body_sizes=(16, 14, 12))

    # also-today briefs strip
    b.rect(36, 832, W - 72, 96, LIGHT)
    b.rect(36, 832, W - 72, 5, GOLD)
    b.text(56, 846, "ALSO TODAY", 17, RED, bold=True)
    line1 = "  \u2022  ".join(BRIEFS[:2])
    line2 = "  \u2022  ".join(BRIEFS[2:])
    b.text(56, 872, line1, 16, INK, bold=True)
    b.text(56, 900, line2, 16, INK, bold=True)

    # footer
    b.rect(36, 946, W - 72, 2, GREY)
    b.text(W // 2, 960, "FRIDAY 20 NOVEMBER 2026  \u2022  TEN STORIES",
           18, GREY, centre=True)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    use_stdlib = os.environ.get("MAKEFUN_FORCE_STDLIB") == "1"
    backend = None
    if not use_stdlib:
        try:
            backend = PilBackend()
        except Exception:
            backend = None
    if backend is None:
        backend = PixelBackend()
    draw_page(backend)
    backend.save(out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
