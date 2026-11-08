# Spotifast Pill

A compact, floating music-pill mini player skin for
[Spotifast](https://spotifast.rocks)'s Winamp mini player. The starting idea was
[Dynamic Music Pill](https://github.com/Andbal23/dynamic-music-pill).

![Spotifast Pill, dark](preview/dark.png)

<img src="preview/light.png" alt="Spotifast Pill, light" width="100%">

## What is in the box

| File | Description |
| --- | --- |
| `dist/Spotifast Pill.wmz` | Smoked-glass dark pill |
| `dist/Spotifast Pill Light.wmz` | Soft-white light pill |
| `tools/build_skins.py` | Draws every bitmap, writes the `.wms` and packs both `.wmz` files |
| `build/dark`, `build/light` | The unpacked skins the script generates, for editing or inspecting |
| `preview/*.png` | Rendered by Spotifast's own skin engine, with a sample cover and the ambient wave |
| `preview/raw-*.png` | The untouched engine render (placeholder art; the dotted line is the live-wave fallback) |

Both skins are 480 × 96 skin pixels and use the same layout:

- rounded 52 px album art, cut to a rounded square
- bold title and quieter artist line, both with a marquee when they overflow
- live visualiser: Spotifast's real waveform when the local audio tap has samples, over a soft ambient wave that keeps moving during playback
- a slim seek line with a draggable thumb
- previous / play-pause / next transport controls
- hover states: the transport icons brighten, the play button turns Spotify green
- a transparent margin with a baked drop shadow, so the window floats

## Install

1. Open Spotifast's mini player: **Ctrl+M** (Windows/Linux) or **Cmd+Shift+M**
   (macOS), or use the shrink button in the player bar.
2. Open **Settings → Winamp mini player → Choose a skin**.
3. Pick `dist/Spotifast Pill.wmz`, or drag the file straight onto the mini
   player window. (Copying either file into `~/.config/spotifast/skins/` also
   makes it appear in the list after a moment.)
4. Use the right-click menu → **Size** to try 1× or 2×. The skin is drawn at
   native pixels and scaled by whole numbers, so 1× is the sharpest.

Switch between the dark and light files the same way.

## Controls

| Action | Result |
| --- | --- |
| Drag the glass | Move the window |
| Click the album art / title / empty glass | Drag the window (no accidental pause) |
| Buttons | Previous, play/pause, next |
| Seek line | Click or drag to seek |
| Right-click | Spotifast's menu: size, always on top, Big window, quit |
| Ctrl+M / Cmd+Shift+M | Back to the full player |

## Origin: the music-pill idea

The starting point was Dynamic Music Pill: a floating, rounded media controller
with album art, a title and artist, and a live waveform. That widget is a GNOME
Shell extension with live CSS and compositor access. It can sample the current
cover for an adaptive colour, blur the desktop behind the pill, and expand into
a popover with lyrics and seek controls.

A Spotifast mini player cannot do that. It is a Winamp/WMP skin: a fixed bitmap
layout inside a fixed window. A classic `.wsz` skin is a 275 × 116 sprite sheet
with no transparency and no album-art area at all. A `.wmz` skin adds a
transparent window, album art and live text, but it still cannot read the
cover's pixels, blur what is behind the window, recolour itself per track, or
expand and shrink on demand. The classic equalizer and playlist windows are not
part of a WMP skin either.

So this is the closest compact approximation the format allows: the pill
silhouette, rounded art, title and artist, a seek line, three transport buttons
and a waveform, all in a fixed 480 × 96 window. The glass and its shadow are
baked into the background bitmap, and the waveform's ambient layer is animated
in the skin because the format cannot read remote audio.

## Visualiser and album art

Spotifast draws the real waveform from the local audio tap. If playback is
remote (Spotify Connect on a phone or another speaker, or a route where the tap
has no samples), that waveform collapses to a flat dotted line. The skin keeps a
soft ambient wave behind it, so the pill still breathes while music is playing;
the live waveform draws over it when samples are available.

Album art is drawn by the live app through a rectangular clip. The skin adds a
rounded corner overlay in the pill's exact glass colour, so a square cover still
ends in a clean rounded square without spilling over the plate.

## Rebuild or recolour

Requires Python 3 and Pillow (`pip install -r requirements.txt`).

```bash
python3 tools/build_skins.py
```

Edit the `DARK` and `LIGHT` palettes (and the geometry constants near the top)
in `tools/build_skins.py`. The script redraws the PNGs at 4× and downsamples
them for clean rounded edges, then rewrites both `.wmz` files and the previews.

## Credits

The starting idea is [Dynamic Music Pill](https://github.com/Andbal23/dynamic-music-pill)
by Andbal23 (GPL-3.0). This is not a port: the adaptive colour, blur and popover
of that GNOME extension cannot be reproduced by a Winamp/WMP skin. No code or
artwork from the original project is used here; every bitmap is generated by
`tools/build_skins.py`.

## License

MIT. See [LICENSE](LICENSE).
