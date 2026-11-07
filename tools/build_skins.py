#!/usr/bin/env python3
"""Builds the Spotifast Pill Windows Media Player skins (.wmz).

A .wmz is a zip holding a .wms definition (XML), the bitmaps it names and an
optional viscolor.txt. Everything here is drawn from scratch with Pillow, so
the skin can be recoloured or re-proportioned by editing this file and running
it again:

    python3 tools/build_skins.py

The art is drawn at 4x and downsampled, which gives the rounded shapes clean
anti-aliased edges at the skin's native size.
"""

from __future__ import annotations

import math
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PREVIEW = ROOT / "preview"

SS = 4  # supersampling factor

# ---------------------------------------------------------------- geometry --

W, H = 480, 96
PILL = (10, 10, 470, 86)  # left, top, right, bottom
RADIUS = 38

ART = 52
ART_X, ART_Y = 26, 22
ART_RADIUS = 14

TEXT_X, TEXT_W = 90, 190
TITLE_Y, TITLE_H = 22, 24
ARTIST_Y, ARTIST_H = 47, 18
SEEK_Y, SEEK_H = 67, 10

VIS = (286, 34, 40, 28)

PREV = (334, 32, 32, 32)
PLAY = (372, 26, 44, 44)
NEXT = (424, 32, 32, 32)

ACCENT = (30, 215, 96)


@dataclass(frozen=True)
class Palette:
    name: str
    title: str
    file: str
    pill_top: tuple[int, int, int, int]
    pill_bottom: tuple[int, int, int, int]
    outline: tuple[int, int, int, int]
    shadow: tuple[int, int, int, int]
    title_color: tuple[int, int, int]
    artist_color: tuple[int, int, int]
    track: tuple[int, int, int, int]
    thumb: tuple[int, int, int, int]
    icon: tuple[int, int, int]
    icon_hover_plate: tuple[int, int, int, int]
    art_plate: tuple[int, int, int, int]
    art_edge: tuple[int, int, int, int]
    play_plate: tuple[int, int, int, int]
    play_glyph: tuple[int, int, int]
    play_hover_plate: tuple[int, int, int, int]
    viscolors: list[tuple[int, int, int]]


DARK = Palette(
    name="dark",
    title="Spotifast Pill",
    file="Spotifast Pill.wmz",
    pill_top=(32, 33, 39, 246),
    pill_bottom=(14, 15, 18, 246),
    outline=(255, 255, 255, 34),
    shadow=(0, 0, 0, 130),
    title_color=(247, 247, 250),
    artist_color=(166, 173, 186),
    track=(255, 255, 255, 46),
    thumb=(255, 255, 255, 255),
    icon=(255, 255, 255),
    icon_hover_plate=(255, 255, 255, 28),
    art_plate=(32, 33, 39, 255),
    art_edge=(255, 255, 255, 30),
    play_plate=(247, 247, 250, 255),
    play_glyph=(12, 13, 16),
    play_hover_plate=(30, 215, 96, 255),
    viscolors=[
        (14, 15, 18),
        (32, 33, 39),
        (118, 247, 166),
        (106, 243, 157),
        (94, 239, 148),
        (83, 234, 139),
        (72, 230, 131),
        (62, 224, 122),
        (53, 218, 114),
        (45, 211, 106),
        (38, 203, 99),
        (32, 194, 92),
        (27, 184, 85),
        (23, 173, 79),
        (19, 161, 73),
        (16, 148, 67),
        (13, 134, 61),
        (11, 119, 55),
        (126, 248, 170),
        (105, 240, 155),
        (84, 231, 140),
        (63, 222, 125),
        (44, 212, 110),
        (246, 247, 250),
    ],
)

LIGHT = Palette(
    name="light",
    title="Spotifast Pill Light",
    file="Spotifast Pill Light.wmz",
    pill_top=(255, 255, 255, 246),
    pill_bottom=(236, 236, 242, 246),
    outline=(0, 0, 0, 20),
    shadow=(0, 0, 0, 90),
    title_color=(20, 21, 26),
    artist_color=(108, 113, 126),
    track=(0, 0, 0, 36),
    thumb=(255, 255, 255, 255),
    icon=(20, 21, 26),
    icon_hover_plate=(0, 0, 0, 18),
    art_plate=(228, 228, 235, 255),
    art_edge=(0, 0, 0, 24),
    play_plate=(20, 21, 26, 255),
    play_glyph=(255, 255, 255),
    play_hover_plate=(30, 215, 96, 255),
    viscolors=[
        (236, 236, 242),
        (255, 255, 255),
        (23, 180, 90),
        (22, 173, 86),
        (21, 166, 82),
        (20, 159, 78),
        (19, 152, 74),
        (18, 145, 70),
        (17, 138, 67),
        (16, 131, 63),
        (15, 124, 59),
        (14, 117, 56),
        (13, 110, 52),
        (12, 103, 49),
        (11, 96, 45),
        (10, 89, 42),
        (9, 82, 38),
        (8, 75, 35),
        (23, 180, 90),
        (20, 166, 82),
        (17, 152, 74),
        (14, 138, 67),
        (11, 124, 59),
        (12, 13, 16),
    ],
)


# ------------------------------------------------------------------ helpers --


def s(value: float) -> int:
    return int(round(value * SS))


def rect(*values: float) -> tuple[int, int, int, int]:
    return tuple(s(v) for v in values)  # type: ignore[return-value]


def canvas(width: int, height: int) -> Image.Image:
    return Image.new("RGBA", (s(width), s(height)), (0, 0, 0, 0))


def rounded(draw: ImageDraw.ImageDraw, box, radius: float, fill) -> None:
    draw.rounded_rectangle(rect(*box), radius=s(radius), fill=fill)


def gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    """A vertical linear gradient, as RGBA."""
    width, height = size
    strip = Image.new("RGBA", (1, s(height)))
    pixels = strip.load()
    for y in range(s(height)):
        share = y / max(1, s(height) - 1)
        pixels[0, y] = tuple(
            int(round(a + (b - a) * share)) for a, b in zip(top, bottom)
        )
    return strip.resize((s(width), s(height)), Image.Resampling.NEAREST)


def rounded_mask(width: int, height: int, radius: float) -> Image.Image:
    mask = Image.new("L", (s(width), s(height)), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, s(width) - 1, s(height) - 1), radius=s(radius), fill=255
    )
    return mask


def finish(image: Image.Image, width: int, height: int) -> Image.Image:
    """Downsample the 4x drawing to the skin's native pixels."""
    return image.resize((width, height), Image.Resampling.LANCZOS)


def save(image: Image.Image, width: int, height: int, path: Path) -> None:
    finish(image, width, height).save(path, "PNG", optimize=True)


# --------------------------------------------------------------------- art --


def background(p: Palette) -> Image.Image:
    image = canvas(W, H)
    left, top, right, bottom = PILL
    width, height = right - left, bottom - top

    # The drop shadow lives in the transparent margin around the pill.
    shadow_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle(
        rect(left, top + 3, right, bottom + 3), radius=s(RADIUS), fill=p.shadow[3]
    )
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(s(7)))
    shadow_layer = Image.new("RGBA", image.size, p.shadow[:3] + (0,))
    shadow_layer.putalpha(shadow_mask)
    image = Image.alpha_composite(image, shadow_layer)

    # The glass.
    fill = gradient((width, height), p.pill_top, p.pill_bottom)
    mask = rounded_mask(width, height, RADIUS)
    pill = Image.new("RGBA", (s(width), s(height)), (0, 0, 0, 0))
    pill.paste(fill, (0, 0), mask)
    image.alpha_composite(pill, (s(left), s(top)))

    draw = ImageDraw.Draw(image)

    # A hairline outline, brighter along the top like a lit edge.
    draw.rounded_rectangle(
        rect(left, top, right - 1, bottom - 1),
        radius=s(RADIUS),
        outline=p.outline,
        width=max(1, s(1)),
    )
    highlight = Image.new("RGBA", image.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.rounded_rectangle(
        rect(left + 1, top + 1, right - 2, bottom - 2),
        radius=s(RADIUS - 1),
        outline=(255, 255, 255, 40 if p.name == "dark" else 150),
        width=max(1, s(1)),
    )
    # Keep only the top half of that second edge, so it reads as a highlight.
    fade = Image.new("L", image.size, 0)
    fd = ImageDraw.Draw(fade)
    fd.rectangle(rect(0, 0, W, top + 26), fill=255)
    fade = fade.filter(ImageFilter.GaussianBlur(s(10)))
    highlight.putalpha(Image.composite(highlight.getchannel("A"), Image.new("L", image.size, 0), fade))
    image = Image.alpha_composite(image, highlight)

    # A soft shading along the bottom inside edge for depth.
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rounded_rectangle(
        rect(left + 1, top + 1, right - 2, bottom - 2),
        radius=s(RADIUS - 1),
        outline=(0, 0, 0, 50),
        width=max(1, s(3)),
    )
    shade = shade.filter(ImageFilter.GaussianBlur(s(2)))
    bottom_only = Image.new("L", image.size, 0)
    ImageDraw.Draw(bottom_only).rectangle(rect(0, bottom - 22, W, H), fill=255)
    bottom_only = bottom_only.filter(ImageFilter.GaussianBlur(s(8)))
    shade.putalpha(Image.composite(shade.getchannel("A"), Image.new("L", image.size, 0), bottom_only))
    image = Image.alpha_composite(image, shade)
    return image


def art_plate(p: Palette) -> Image.Image:
    image = canvas(ART, ART)
    rounded(ImageDraw.Draw(image), (0, 0, ART, ART), ART_RADIUS, p.art_plate)
    return image


def art_edge(p: Palette) -> Image.Image:
    image = canvas(ART, ART)
    ImageDraw.Draw(image).rounded_rectangle(
        rect(0, 0, ART - 1, ART - 1),
        radius=s(ART_RADIUS),
        outline=p.art_edge,
        width=max(1, s(1)),
    )
    return image


def art_round(bg: Image.Image) -> Image.Image:
    """The pill's own pixels, with a rounded-square hole for the album art.

    The live skin draws album art through a rectangular clip, so the square
    corners of a cover are not cut by the plate's shape. This overlay covers
    those corners with the exact background that sits behind the art, which
    makes the cover read as a rounded square without touching the live art.
    """
    crop = bg.crop(
        (s(ART_X), s(ART_Y), s(ART_X + ART), s(ART_Y + ART))
    ).copy()
    mask = rounded_mask(ART, ART, ART_RADIUS)
    crop.putalpha(
        ImageChops.multiply(crop.getchannel("A"), ImageOps.invert(mask))
    )
    return crop


def wave_gif(p: Palette, bg: Image.Image) -> list[Image.Image]:
    """A soft, always-moving ambient wave for the visualiser slot.

    Spotifast's real visualiser needs audio samples from playback on this
    computer. The skin's `wave` element draws that live waveform on top; this
    GIF sits behind it, so the pill still breathes when playback is remote or
    when the audio tap has nothing to give.

    GIF transparency is one bit, so the wave is a tiny three-colour neon line
    rather than an alpha-blended image. Its background stays transparent and
    the pill's own glass shows through.
    """
    vx, vy, vw, vh = VIS
    accent = p.viscolors[2]
    back = p.pill_bottom[:3]

    def mix(colour, share):
        return tuple(
            int(round(a + (b - a) * share)) for a, b in zip(colour, back)
        )

    dim = mix(accent, 0.82)
    middle = mix(accent, 0.55)
    palette = [0, 0, 0, *dim, *middle, *accent]
    palette += [0, 0, 0] * (256 - len(palette) // 3)

    frames: list[Image.Image] = []
    count = 24
    for frame in range(count):
        phase = frame / count * 2.0 * math.pi
        image = Image.new("P", (vw, vh), 0)
        image.putpalette(palette)
        draw = ImageDraw.Draw(image)
        points = []
        for x in range(vw):
            envelope = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(x * 0.22 + phase * 1.3))
            y = vh / 2.0 + math.sin(x * 0.38 + phase * 2.0) * vh * 0.36 * envelope
            points.append((x, y))
        draw.line(points, fill=1, width=5, joint="curve")
        draw.line(points, fill=2, width=3, joint="curve")
        draw.line(points, fill=3, width=1, joint="curve")
        frames.append(image)
    return frames



def track(p: Palette) -> Image.Image:
    image = canvas(TEXT_W, SEEK_H)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        rect(0, SEEK_H / 2 - 1.5, TEXT_W, SEEK_H / 2 + 1.5),
        radius=s(1.5),
        fill=p.track,
    )
    return image


def fill(p: Palette) -> Image.Image:
    image = canvas(TEXT_W, SEEK_H)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        rect(0, SEEK_H / 2 - 1.5, TEXT_W, SEEK_H / 2 + 1.5),
        radius=s(1.5),
        fill=ACCENT + (255,),
    )
    return image


def thumb(p: Palette) -> Image.Image:
    image = canvas(10, 10)
    draw = ImageDraw.Draw(image)
    draw.ellipse(rect(0.5, 0.5, 9.5, 9.5), fill=p.thumb)
    if p.name == "light":
        draw.ellipse(
            rect(0.5, 0.5, 9.5, 9.5),
            outline=(0, 0, 0, 34),
            width=max(1, s(0.75)),
        )
    return image


def glyph_base(size: tuple[int, int], plate: tuple | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = canvas(*size)
    draw = ImageDraw.Draw(image)
    if plate is not None:
        width, height = size
        draw.ellipse(rect(0, 0, width, height), fill=plate)
    return image, draw


def skip_icon(p: Palette, size: int, forward: bool, hover: bool) -> Image.Image:
    plate = p.icon_hover_plate if hover else None
    image, draw = glyph_base((size, size), plate)
    alpha = 235 if hover else 150
    colour = p.icon + (alpha,)
    # Draw a "previous" glyph in 28-unit space, then mirror it for "next".
    k = size / 28.0

    def at(x: float, y: float) -> tuple[int, int]:
        return (s(x * k), s(y * k))

    draw.rounded_rectangle(
        [at(6.0, 7.2), at(8.4, 20.8)],
        radius=s(1.2 * k),
        fill=colour,
    )
    draw.polygon(
        [at(21.0, 6.8), at(9.0, 14.0), at(21.0, 21.2)],
        fill=colour,
    )
    if forward:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return image


def play_icon(p: Palette, hover: bool) -> Image.Image:
    plate = p.play_hover_plate if hover else p.play_plate
    image, draw = glyph_base((44, 44), plate)
    colour = p.play_glyph + (255,)
    # A triangle with its visual mass centred in the circle.
    draw.polygon(
        [
            (s(17.5), s(13.5)),
            (s(17.5), s(30.5)),
            (s(32.0), s(22.0)),
        ],
        fill=colour,
    )
    return image


def pause_icon(p: Palette, hover: bool) -> Image.Image:
    plate = p.play_hover_plate if hover else p.play_plate
    image, draw = glyph_base((44, 44), plate)
    colour = p.play_glyph + (255,)
    for x in (16.0, 24.5):
        draw.rounded_rectangle(
            rect(x, 14.0, x + 4.2, 30.0),
            radius=s(1.4),
            fill=colour,
        )
    return image


# ---------------------------------------------------------------- definition --


VISCOLOR_COMMENTS = [
    "background",
    "grid",
    "band 0", "band 1", "band 2", "band 3", "band 4", "band 5", "band 6",
    "band 7", "band 8", "band 9", "band 10", "band 11", "band 12", "band 13",
    "band 14", "band 15",
    "oscilloscope", "oscilloscope", "oscilloscope", "oscilloscope",
    "oscilloscope", "peaks",
]


def viscolor_text(p: Palette) -> str:
    return "\n".join(
        f"{r},{g},{b} // {comment}"
        for (r, g, b), comment in zip(p.viscolors, VISCOLOR_COMMENTS)
    ) + "\n"


def definition(p: Palette) -> str:
    title = f"#{p.title_color[0]:02x}{p.title_color[1]:02x}{p.title_color[2]:02x}"
    artist = f"#{p.artist_color[0]:02x}{p.artist_color[1]:02x}{p.artist_color[2]:02x}"
    wave = "#%02x%02x%02x" % p.viscolors[2]
    return f"""<!--
  {p.title}. A modern, pill-shaped mini player for Spotifast.

  Drawn by tools/build_skins.py. The pill is one frosted rounded rectangle:
  rounded album art, title and artist, a live visualiser, a seek line and
  Apple-Music-style transport controls.
-->
<THEME title="{p.title}" author="Made for Spotifast" copyright="Free to copy and remix">
<VIEW id="main" width="{W}" height="{H}" titleBar="false" backgroundColor="none"
      resizable="false" scriptFile="pill.js" onLoad="follow();">
  <PLAYER playState_onChange="follow();" currentMedia_onChange="follow();"/>

  <SUBVIEW id="pill" left="0" top="0" width="{W}" height="{H}" backgroundImage="bg.png" passThrough="true">
    <!-- Album art, cut to a rounded square by the plate's own shape. -->
    <SUBVIEW id="artPlate" left="{ART_X}" top="{ART_Y}" width="{ART}" height="{ART}"
             backgroundImage="art_plate.png" clippingColor="#ff00ff" passThrough="true">
      <SUBVIEW id="art" left="0" top="0" width="{ART}" height="{ART}"
               backgroundImage="wmpimage_albumart" passThrough="true"/>
      <SUBVIEW id="artEdge" left="0" top="0" width="{ART}" height="{ART}"
               backgroundImage="art_edge.png" passThrough="true"/>
    </SUBVIEW>
    <!-- Sits outside the plate so the live rectangular album-art clip cannot
         spill a square cover past the plate's rounded shape. -->
    <SUBVIEW id="artCut" left="{ART_X}" top="{ART_Y}" width="{ART}" height="{ART}"
             backgroundImage="art_round.png" passThrough="true"/>

    <TEXT id="title" left="{TEXT_X}" top="{TITLE_Y}" width="{TEXT_W}" height="{TITLE_H}"
          fontSize="14" fontStyle="bold" foregroundColor="{title}"
          scrollingAmount="1" scrollingDelay="35" value="wmpprop:player.currentMedia.name"/>
    <TEXT id="artist" left="{TEXT_X}" top="{ARTIST_Y}" width="{TEXT_W}" height="{ARTIST_H}"
          fontSize="10" foregroundColor="{artist}"
          scrollingAmount="1" scrollingDelay="35" value="wmpprop:player.currentMedia.artist"/>

    <SUBVIEW id="waveBack" left="{VIS[0]}" top="{VIS[1]}" width="{VIS[2]}" height="{VIS[3]}"
             backgroundImage="wave.gif" passThrough="true"/>
    <EFFECTS id="wave" left="{VIS[0]}" top="{VIS[1]}" width="{VIS[2]}" height="{VIS[3]}"
             wave="true" foregroundColor="{wave}" passThrough="true"/>

    <SEEKSLIDER id="seek" left="{TEXT_X}" top="{SEEK_Y}" width="{TEXT_W}" height="{SEEK_H}"
                backgroundImage="track.png" foregroundImage="fill.png"
                thumbImage="thumb.png" thumbHoverImage="thumb.png" thumbDownImage="thumb.png"
                slide="false" cursor="hand" toolTip="Seek"/>

    <PREVBUTTON id="prevButton" left="{PREV[0]}" top="{PREV[1]}" width="{PREV[2]}" height="{PREV[3]}"
                image="prev.png" hoverImage="prev_hover.png" downImage="prev_down.png"
                cursor="hand"/>
    <PLAYBUTTON id="playButton" left="{PLAY[0]}" top="{PLAY[1]}" width="{PLAY[2]}" height="{PLAY[3]}"
                image="play.png" hoverImage="play_hover.png" downImage="play_down.png"
                cursor="hand"/>
    <PAUSEBUTTON id="pauseButton" left="{PLAY[0]}" top="{PLAY[1]}" width="{PLAY[2]}" height="{PLAY[3]}"
                 visible="false" image="pause.png" hoverImage="pause_hover.png"
                 downImage="pause_down.png" cursor="hand"/>
    <NEXTBUTTON id="nextButton" left="{NEXT[0]}" top="{NEXT[1]}" width="{NEXT[2]}" height="{NEXT[3]}"
                image="next.png" hoverImage="next_hover.png" downImage="next_down.png"
                cursor="hand"/>
  </SUBVIEW>
</VIEW>
</THEME>
"""


SCRIPT = """// The Spotifast Pill: marquee only when the words do not fit, and one
// play button or the other, never both.
function fit(text) {
    text.scrolling = text.textWidth > text.width;
}

function follow() {
    var state = player.playState;
    var playing = state == 3 || state == 6 || state == 7 || state == 9;
    playButton.visible = !playing;
    pauseButton.visible = playing;
    wave.visible = playing;
    waveBack.visible = playing;
    fit(title);
    fit(artist);
}
"""


# -------------------------------------------------------------------- build --


def build_skin(p: Palette) -> Path:
    folder = ROOT / "build" / p.name
    folder.mkdir(parents=True, exist_ok=True)

    files: dict[str, bytes] = {}

    def add(name: str, image: Image.Image, width: int, height: int) -> None:
        path = folder / name
        save(image, width, height, path)
        files[name] = path.read_bytes()

    bg = background(p)
    add("bg.png", bg, W, H)
    add("art_round.png", art_round(bg), ART, ART)
    add("art_plate.png", art_plate(p), ART, ART)
    add("art_edge.png", art_edge(p), ART, ART)
    add("track.png", track(p), TEXT_W, SEEK_H)
    add("fill.png", fill(p), TEXT_W, SEEK_H)
    add("thumb.png", thumb(p), 10, 10)

    add("prev.png", skip_icon(p, 32, False, False), 32, 32)
    add("prev_hover.png", skip_icon(p, 32, False, True), 32, 32)
    add("prev_down.png", skip_icon(p, 32, False, True), 32, 32)
    add("next.png", skip_icon(p, 32, True, False), 32, 32)
    add("next_hover.png", skip_icon(p, 32, True, True), 32, 32)
    add("next_down.png", skip_icon(p, 32, True, True), 32, 32)

    add("play.png", play_icon(p, False), 44, 44)
    add("play_hover.png", play_icon(p, True), 44, 44)
    add("play_down.png", play_icon(p, True), 44, 44)
    add("pause.png", pause_icon(p, False), 44, 44)
    add("pause_hover.png", pause_icon(p, True), 44, 44)
    add("pause_down.png", pause_icon(p, True), 44, 44)

    wave_frames = wave_gif(p, bg)
    wave_path = folder / "wave.gif"
    wave_frames[0].save(
        wave_path,
        save_all=True,
        append_images=wave_frames[1:],
        duration=60,
        loop=0,
        transparency=0,
        disposal=2,
        optimize=False,
    )
    files["wave.gif"] = wave_path.read_bytes()

    files["viscolor.txt"] = viscolor_text(p).encode()
    files["pill.js"] = SCRIPT.encode()
    files["pill.wms"] = definition(p).encode()

    (folder / "viscolor.txt").write_bytes(files["viscolor.txt"])
    (folder / "pill.js").write_bytes(files["pill.js"])
    (folder / "pill.wms").write_bytes(files["pill.wms"])

    DIST.mkdir(exist_ok=True)
    target = DIST / p.file
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(f"wrote {target} ({target.stat().st_size / 1024:.1f} KiB)")
    return target


def mock_preview(p: Palette) -> None:
    """A quick composite for looking at the design without running the app."""
    from PIL import ImageFont

    image = finish(background(p), W, H)
    plate = finish(art_plate(p), ART, ART)
    # A stand-in cover: a warm album-art-ish square.
    cover = Image.new("RGBA", (ART, ART), (198, 120, 92, 255))
    cd = ImageDraw.Draw(cover)
    cd.ellipse((10, 10, 46, 46), fill=(244, 214, 190, 255))
    cd.ellipse((22, 22, 34, 34), fill=(58, 42, 36, 255))
    cover.putalpha(plate.getchannel("A"))
    image.alpha_composite(cover, (ART_X, ART_Y))
    image.alpha_composite(finish(art_edge(p), ART, ART), (ART_X, ART_Y))

    image.alpha_composite(finish(track(p), TEXT_W, SEEK_H), (TEXT_X, SEEK_Y))
    fill_img = finish(fill(p), TEXT_W, SEEK_H)
    fill_img = fill_img.crop((0, 0, 84, SEEK_H))
    image.alpha_composite(fill_img, (TEXT_X, SEEK_Y))
    image.alpha_composite(finish(thumb(p), 10, 10), (TEXT_X + 79, SEEK_Y))

    image.alpha_composite(finish(skip_icon(p, 32, False, False), 32, 32), (PREV[0], PREV[1]))
    image.alpha_composite(finish(play_icon(p, False), 44, 44), (PLAY[0], PLAY[1]))
    image.alpha_composite(finish(skip_icon(p, 32, True, False), 32, 32), (NEXT[0], NEXT[1]))

    # Waveform stand-in.
    import random

    random.seed(7)
    points = [math.sin(i / 4.0) * random.uniform(0.2, 1.0) for i in range(40)]
    vx, vy, vw, vh = VIS
    for i, value in enumerate(points):
        height = max(2, int(abs(value) * vh))
        top = vy + (vh - height) // 2
        colour = p.viscolors[2 + int((1 - abs(value)) * 15)]
        ImageDraw.Draw(image).line(
            ((vx + i, top), (vx + i, top + height)), fill=colour + (255,)
        )

    font = None
    bold = None
    for regular, heavy in (
        (
            "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
            "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
        ),
    ):
        if os.path.exists(regular) and os.path.exists(heavy):
            font = ImageFont.truetype(regular, 14)
            bold = ImageFont.truetype(heavy, 18)
            break
    if font and bold:
        draw = ImageDraw.Draw(image)
        draw.text((TEXT_X, 22), "Coffee & Rain", font=bold, fill=p.title_color)
        draw.text((TEXT_X, 47), "Nujabes", font=font, fill=p.artist_color)

    PREVIEW.mkdir(exist_ok=True)
    path = PREVIEW / f"{p.name}.png"
    image.resize((W * 2, H * 2), Image.Resampling.NEAREST).save(path)
    print(f"wrote {path}")


def compose_engine(p: Palette) -> bool:
    """Puts a sample cover and a visualiser into Spotifast's own render.

    The raw render is made by `cargo run --example pill_preview`; the skin
    engine has no album art or audio in a still preview, so the placeholder
    square and flat line are replaced here for the README pictures. Returns
    false when there is no raw render to work from.
    """
    raw = PREVIEW / f"raw-{p.name}.png"
    if not raw.exists():
        return False
    base = Image.open(raw).convert("RGBA")
    folder = ROOT / "build" / p.name
    bg = Image.open(folder / "bg.png").convert("RGBA")

    # Restore the glass where the placeholder art was; the visualiser is
    # already the ambient wave from the engine render.
    base.paste(bg.crop((ART_X, ART_Y, ART_X + ART, ART_Y + ART)), (ART_X, ART_Y))

    # A warm record cover, cut to the same rounded square as real album art.
    cover = Image.new("RGBA", (ART * SS, ART * SS), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cover)
    for y in range(ART * SS):
        share = y / (ART * SS - 1)
        colour = tuple(
            int(round(a + (b - a) * share))
            for a, b in zip((214, 139, 108), (166, 96, 74))
        )
        cd.line(((0, y), (ART * SS, y)), fill=colour + (255,))
    centre = (ART * SS) // 2
    cd.ellipse(
        (
            centre - int(17 * SS),
            centre - int(17 * SS),
            centre + int(17 * SS),
            centre + int(17 * SS),
        ),
        fill=(244, 220, 200, 255),
    )
    cd.ellipse(
        (
            centre - int(5 * SS),
            centre - int(5 * SS),
            centre + int(5 * SS),
            centre + int(5 * SS),
        ),
        fill=(48, 35, 31, 255),
    )
    cover = cover.resize((ART, ART), Image.Resampling.LANCZOS)
    mask = Image.open(folder / "art_plate.png").getchannel("A")
    base.paste(cover, (ART_X, ART_Y), mask)
    base.alpha_composite(Image.open(folder / "art_edge.png").convert("RGBA"), (ART_X, ART_Y))

    base.save(PREVIEW / f"{p.name}.png")
    print(f"wrote {PREVIEW / f'{p.name}.png'} (engine render)")
    return True


def main() -> None:
    for palette in (DARK, LIGHT):
        build_skin(palette)
        if not compose_engine(palette):
            mock_preview(palette)


if __name__ == "__main__":
    main()
