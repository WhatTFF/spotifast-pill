# Spotifast Pill

Two floating pill skins for [Spotifast](https://spotifast.rocks)'s Winamp mini player — a smoked-glass
dark and a soft-white light. Each is a 480 × 96 WMP skin with rounded album art, a bold title and
quieter artist line, marquee overflow, a slim seek line, three transport buttons, hover states and a
baked glass shadow. Spotifast's real waveform draws in the visualiser slot when the local audio tap
has samples; a soft ambient wave keeps the pill moving when playback is remote.

![Spotifast Pill, dark](preview/dark.png)

<img src="preview/light.png" alt="Spotifast Pill, light" width="55%">

The starting idea was [Dynamic Music Pill](https://github.com/Andbal23/dynamic-music-pill): a floating
media controller that samples the cover for an adaptive colour, blurs the desktop behind it and expands
into a popover. That needs live CSS and compositor access, which a Winamp/WMP skin does not have. A
classic `.wsz` is a fixed 275 × 116 sprite sheet with no transparency or album-art area; a `.wmz` adds a
transparent window, album art and live text, but still cannot read the cover's pixels, blur the backdrop
or resize on demand. This is the closest compact approximation the format allows.

## Install

Drop either file from `dist/` onto the mini player (**Ctrl+M**, or **Cmd+Shift+M** on macOS), or open
**Settings → Winamp mini player → Choose a skin**.

MIT licensed. No code or artwork from Dynamic Music Pill is used.
