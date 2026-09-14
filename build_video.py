"""
build_video.py
Turns one script entry (hook + lines + cta) into a finished 1080x1920
vertical video with animated background, kinetic captions, and burned-in
hashtags/branding at the end. No face, no voice required.

Pure PIL + ffmpeg (subprocess) - no moviepy dependency, so it runs
anywhere ffmpeg is installed (incl. GitHub Actions ubuntu-latest out of
the box).

Optional: if assets/music/*.mp3 exists, one is picked at random as a
background bed. If not, a soft silent (or gently faded tone) audio track
is generated so every platform gets a valid audio stream.
"""
from __future__ import annotations
import os
import random
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

W, H = 1080, 1920
FPS = 30


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_gradient_png(path: Path, color_a: str, color_b: str, size=(2160, 3840)) -> None:
    """Diagonal gradient, rendered oversized so ffmpeg can slowly pan/zoom it."""
    w, h = size
    a = _hex_to_rgb(color_a)
    b = _hex_to_rgb(color_b)
    base = Image.new("RGB", (w, h), a)
    top = Image.new("RGB", (w, h), b)
    mask = Image.new("L", (w, h))
    mdata = []
    for y in range(h):
        for x in range(0, 1):  # build one row's ramp, reuse per row below is faster:
            pass
    # Fast diagonal mask using numpy avoids a slow python double loop.
    import numpy as np
    xx, yy = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    grad = (xx + yy) / 2.0
    grad = (grad * 255).astype("uint8")
    mask = Image.fromarray(grad, mode="L")
    out = Image.composite(top, base, mask)

    # subtle vignette + grain so it doesn't look like a flat corporate slide
    grain = (np.random.rand(h, w) * 14).astype("uint8")
    grain_img = Image.fromarray(grain, mode="L").convert("RGB")
    out = Image.blend(out, grain_img, 0.035)
    out.save(path)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _load_font(size: int):
    from PIL import ImageFont
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def render_caption_png(text: str, path: Path, accent=False, accent_color="#D4FF6B", font_size=86):
    """Render one caption card: transparent PNG, big centered bold text,
    word-wrapped, with a soft drop shadow for legibility over any footage."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)
    max_width = int(W * 0.82)
    lines = _wrap_text(draw, text, font, max_width)
    line_height = int(font_size * 1.28)  # ~1.28x leading
    total_h = line_height * len(lines)
    y = (H - total_h) // 2
    fill = _hex_to_rgb(accent_color) + (255,) if accent else (255, 255, 255, 255)
    shadow = (0, 0, 0, 180)
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (W - w) / 2
        for dx, dy in ((0, 6), (3, 3), (-3, 3)):
            draw.text((x + dx, y + dy), line, font=font, fill=shadow)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    img.save(path)


def render_footer_png(handle: str, hashtags: list[str], path: Path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    handle_font = _load_font(52)
    tag_font = _load_font(38)
    max_width = int(W * 0.86)
    tag_lines = _wrap_text(draw, " ".join(hashtags[:4]), tag_font, max_width)

    handle_w = draw.textlength(handle, font=handle_font)
    hx = (W - handle_w) / 2
    hy = H - 230
    draw.text((hx + 2, hy + 2), handle, font=handle_font, fill=(0, 0, 0, 160))
    draw.text((hx, hy), handle, font=handle_font, fill=(255, 255, 255, 235))

    ty = H - 150
    for line in tag_lines:
        w = draw.textlength(line, font=tag_font)
        x = (W - w) / 2
        draw.text((x + 2, ty + 2), line, font=tag_font, fill=(0, 0, 0, 150))
        draw.text((x, ty), line, font=tag_font, fill=(255, 255, 255, 220))
        ty += 52
    img.save(path)


def build_background_clip(tmpdir: Path, duration: float, color_a: str, color_b: str) -> Path:
    grad_path = tmpdir / "gradient.png"
    make_gradient_png(grad_path, color_a, color_b)
    out = tmpdir / "bg.mp4"
    # slow Ken-Burns zoom/pan across the oversized gradient for subtle motion
    frames = int(duration * FPS)
    vf = (
        f"zoompan=z='min(zoom+0.0007,1.25)':d={frames}:s={W}x{H}:fps={FPS}:"
        f"x='if(gte(zoom,1.25),x,x+1)':y='if(gte(zoom,1.25),y,y+1)'"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(grad_path),
        "-vf", vf, "-t", str(duration), "-r", str(FPS),
        "-pix_fmt", "yuv420p", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def build_silent_audio(tmpdir: Path, duration: float) -> Path:
    out = tmpdir / "silence.m4a"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration), "-c:a", "aac", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


# A handful of root notes (Hz) for a simple two-voice pad + soft pulse.
# Picked from a minor-leaning set so it stays calm/ambient rather than
# jingly - fits a finance/education tone without fighting the captions.
_MUSIC_ROOTS = [196.0, 220.0, 246.94, 164.81, 174.61]  # G3, A3, B3, E3, F3


def build_generated_music(tmpdir: Path, duration: float, seed: int = 0) -> Path:
    """Procedurally synthesizes a short ambient pad + soft pulse loop with
    ffmpeg's aevalsrc - no external audio files, no licensing to worry
    about, and every video gets a slightly different (but always calm)
    bed so a daily batch doesn't sound identical. This is the default;
    dropping real .mp3 files into assets/music/ still overrides it."""
    rng = random.Random(seed)
    root = rng.choice(_MUSIC_ROOTS)
    fifth = root * 1.4983  # perfect fifth
    octave = root * 2.0
    pulse_hz = root / 2.0
    pulse_period = rng.choice([0.5, 0.6, 0.75])
    lfo = round(rng.uniform(0.1, 0.22), 3)

    expr = (
        f"0.12*sin(2*PI*{root:.2f}*t)"
        f"+0.08*sin(2*PI*{fifth:.2f}*t)"
        f"+0.045*sin(2*PI*{octave:.2f}*t)*sin(2*PI*{lfo}*t)"
        f"+0.08*sin(2*PI*{pulse_hz:.2f}*t)*exp(-mod(t\\,{pulse_period})*7)"
    )
    out = tmpdir / "generated_music.m4a"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100",
        "-t", str(duration), "-c:a", "aac", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def pick_music(music_dir: Path) -> Path | None:
    if not music_dir.exists():
        return None
    tracks = [p for p in music_dir.glob("*.mp3")]
    return random.choice(tracks) if tracks else None


def build_video(script: dict, colors: tuple[str, str], accent_color: str, handle: str,
                 out_path: Path, music_dir: Path, per_line_seconds: float = 3.2):
    """script: dict with keys hook, lines (list[str]), cta, hashtags (list[str])."""
    beats = [script["hook"], *script["lines"], script["cta"]]
    durations = []
    for i, text in enumerate(beats):
        # reading-speed based duration, floor 2.2s, ceil 4.0s; hook/cta linger
        # slightly longer. Kept snappy on purpose: short-form algorithms
        # weight completion rate heavily, and 15-25s total tends to hold
        # attention better than long lingering beats.
        base = max(2.2, min(4.0, len(text) / 15))
        if i in (0, len(beats) - 1):
            base += 0.4
        durations.append(round(base, 2))
    total_duration = sum(durations) + 1.2  # tail for footer

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        bg = build_background_clip(tmpdir, total_duration, colors[0], colors[1])

        # Render each caption card and its own short clip, then concat.
        clip_paths = []
        for i, (text, dur) in enumerate(zip(beats, durations)):
            png = tmpdir / f"cap_{i:02d}.png"
            is_accent = i == 0 or i == len(beats) - 1
            render_caption_png(text, png, accent=is_accent, accent_color=accent_color)
            clip = tmpdir / f"clip_{i:02d}.mp4"
            fade = min(0.35, dur / 4)
            cmd = [
                "ffmpeg", "-y", "-t", str(dur), "-i", str(bg),
                "-loop", "1", "-t", str(dur), "-i", str(png),
                "-filter_complex",
                (
                    f"[1:v]fade=in:st=0:d={fade}:alpha=1,"
                    f"fade=out:st={max(0, dur - fade):.2f}:d={fade}:alpha=1[cap];"
                    f"[0:v][cap]overlay=0:0:shortest=1"
                ),
                "-t", str(dur), "-r", str(FPS), "-pix_fmt", "yuv420p", str(clip),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            clip_paths.append(clip)

        # footer card (handle + hashtags) held for the final 1.2s over the bg tail
        footer_png = tmpdir / "footer.png"
        render_footer_png(handle, script["hashtags"], footer_png)
        footer_clip = tmpdir / "footer.mp4"
        cmd = [
            "ffmpeg", "-y", "-t", "1.2", "-i", str(bg),
            "-loop", "1", "-t", "1.2", "-i", str(footer_png),
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
            "-t", "1.2", "-r", str(FPS), "-pix_fmt", "yuv420p", str(footer_clip),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        clip_paths.append(footer_clip)

        concat_list = tmpdir / "list.txt"
        concat_list.write_text("".join(f"file '{p}'\n" for p in clip_paths))
        video_only = tmpdir / "video_only.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(video_only)],
            check=True, capture_output=True,
        )

        music = pick_music(music_dir)
        if music:
            audio_cmd = [
                "ffmpeg", "-y", "-i", str(video_only), "-stream_loop", "-1", "-i", str(music),
                "-filter_complex", f"[1:a]afade=in:st=0:d=1,afade=out:st={total_duration-1:.2f}:d=1,volume=0.35,aformat=channel_layouts=stereo[a]",
                "-map", "0:v", "-map", "[a]", "-t", str(total_duration),
                "-c:v", "copy", "-c:a", "aac", str(out_path),
            ]
        else:
            # No hand-picked mp3 available -> procedurally generated ambient
            # bed by default (see build_generated_music). Seeded from the
            # script id so it's reproducible per script but varies across
            # the bank.
            seed = abs(hash(script.get("id", ""))) % (2 ** 31)
            bed = build_generated_music(tmpdir, total_duration, seed=seed)
            audio_cmd = [
                "ffmpeg", "-y", "-i", str(video_only), "-i", str(bed),
                "-filter_complex", f"[1:a]afade=in:st=0:d=1,afade=out:st={total_duration-1:.2f}:d=1,aformat=channel_layouts=stereo[a]",
                "-map", "0:v", "-map", "[a]", "-t", str(total_duration),
                "-c:v", "copy", "-c:a", "aac", str(out_path),
            ]
        subprocess.run(audio_cmd, check=True, capture_output=True)

    return out_path
