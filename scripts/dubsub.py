"""Pipeline: video link -> Vietnamese subtitles -> square 1254x1254 template video.

Steps (run in order; Claude writes events.json + hook.json between `transcribe` and `build`):
  python dubsub.py doctor
  python dubsub.py fetch "<link>" --out runs/<slug>      # -> source.mp4
  python dubsub.py transcribe runs/<slug> [--lang en]    # -> audio.wav, segs.json, transcript.txt
  python dubsub.py build runs/<slug>                     # events.json + hook.json -> sub.ass, frame.png, final.mp4
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
FONTS = ASSETS / "fonts"
S = 1254                         # canvas size (matches the "anh content" finals)
ORANGE = (220, 117, 79)
BLACK = (24, 24, 30)
HEX_BORDER = "0xDC754F"
TITLE_MAX_W = S - 100
LINE = 38                        # subtitle chars per line before wrapping


def sh(cmd, **kw):
    r = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", **kw)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def probe(path):
    out = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)])
    j = json.loads(out)
    st = j["streams"][0]
    return st["width"], st["height"], st["r_frame_rate"], float(j["format"]["duration"])


def doctor(_):
    for exe in ("ffmpeg", "ffprobe", "yt-dlp"):
        print(exe, "OK" if shutil.which(exe) else "MISSING")
    try:
        import faster_whisper  # noqa: F401
        import PIL  # noqa: F401
        print("faster_whisper + Pillow OK")
    except ImportError as e:
        print("MISSING python lib:", e)


def fetch(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    src = Path(a.link)
    if src.exists():                       # local file instead of a link
        shutil.copy(src, out / "source.mp4")
    else:
        sh(["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
            "--no-playlist", "-o", str(out / "source.%(ext)s"), a.link])
    w, h, fps, dur = probe(out / "source.mp4")
    print(f"source.mp4 {w}x{h} fps={fps} {dur:.1f}s")


def transcribe(a):
    d = Path(a.dir)
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(d / "source.mp4"), "-vn", "-ac", "1", "-ar", "16000", str(d / "audio.wav")])
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en" if a.lang == "en" else "small", compute_type="int8")
    segs, _ = m.transcribe(str(d / "audio.wav"), word_timestamps=True, vad_filter=True, language=a.lang)
    out, lines = [], []
    for s in segs:
        words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in s.words]
        out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(), "words": words})
        lines.append(f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}")
        # word-level view exposes pauses: whisper stretches the last word of a phrase over silence
        lines.append("    " + " ".join(f"{w['w']}@{w['s']}" for w in words))
    (d / "segs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "transcript.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def balance(txt):
    if len(txt) <= LINE:
        return txt
    w = txt.split()
    best = None
    for i in range(1, len(w)):
        x, y = " ".join(w[:i]), " ".join(w[i:])
        d = max(len(x), len(y))
        if best is None or d < best[0]:
            best = (d, x, y)
    return best[1] + r"\N" + best[2]


def layout(w, h):
    """Video box on the canvas, measured from the finals: 16:9 -> full width, y=354."""
    bw, bh = S, round(S * h / w)
    if bh > 760:                              # 4:3 / taller sources: limit height, centre
        bh = min(bh, 880)
        bw = round(bh * w / h)
    y = 354 if bh <= 760 else 290
    return (S - bw) // 2, y, bw, bh


def make_frame(d, hook, box_y):
    from PIL import Image, ImageDraw, ImageFont
    bg = Image.open(ASSETS / "template-nen-sach.png").convert("RGB")
    dr = ImageDraw.Draw(bg)
    col = {"k": BLACK, "o": ORANGE}
    path = str(FONTS / "Inter-Black.ttf")
    size = 67
    f = ImageFont.truetype(path, size)

    def wid(runs):
        return sum(dr.textlength(t, font=f) for t, _ in runs)

    while max(wid(r) for r in hook) > TITLE_MAX_W:
        size -= 1
        f = ImageFont.truetype(path, size)
    pitch = round(size * 1.21)
    # centre the title block in the band above the video (2 lines start ~y=112 for a video at y=354)
    top = max(40, (box_y - 85 + 60) // 2 - len(hook) * pitch // 2 + 29)
    y = top
    for runs in hook:
        x = (S - wid(runs)) / 2
        for t, c in runs:
            dr.text((x, y), t, font=f, fill=col[c])
            x += dr.textlength(t, font=f)
        y += pitch
    bg.save(d / "frame.png")
    return size


def build(a):
    d = Path(a.dir).resolve()
    events = json.loads((d / "events.json").read_text(encoding="utf-8"))   # [{"start","end","text"}]
    hook = json.loads((d / "hook.json").read_text(encoding="utf-8"))       # [[["Elon Musk: ","k"],["5 năm nữa","o"]], ...]
    w, h, fps, dur = probe(d / "source.mp4")
    x, y, bw, bh = layout(w, h)
    size = make_frame(d, hook, y)
    marg = S - (y + bh) + 28
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {S}
PlayResY: {S}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Rim,Inter,44,&H0000D7FF,&H0000D7FF,&H00000000,&HB4000000,1,0,0,0,100,100,0,0,1,4,4,2,60,60,{marg},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    with open(d / "sub.ass", "w", encoding="utf-8") as f:
        f.write(hdr)
        for e in events:
            f.write(f"Dialogue: 0,{ts(e['start'])},{ts(e['end'])},Rim,,0,0,0,,{balance(e['text'])}\n")
    shutil.copytree(FONTS, d / "fonts", dirs_exist_ok=True)   # relative fontsdir avoids Windows drive-colon escaping in libass
    flt = (f"[1:v]scale={bw}:{bh}[v];[0:v][v]overlay={x}:{y}:shortest=1,"
           f"drawbox=x={x}:y={y}:w={bw}:h={bh}:color={HEX_BORDER}:t=3,"
           f"subtitles=sub.ass:fontsdir=fonts,format=yuv420p[o]")
    has_audio = "audio" in sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", "source.mp4"], cwd=d)
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", fps, "-loop", "1", "-i", "frame.png", "-i", "source.mp4",
           "-filter_complex", flt, "-map", "[o]"]
    if has_audio:
        cmd += ["-map", "1:a", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-shortest", "final.mp4"]
    sh(cmd, cwd=d)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", str(min(14, dur / 2)), "-i", "final.mp4", "-frames:v", "1", "check.png"], cwd=d)
    print(f"final.mp4 ok | title font {size}px | video box {bw}x{bh} at ({x},{y}) | fps {fps} | look at check.png")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="c", required=True)
    sp.add_parser("doctor").set_defaults(fn=doctor)
    q = sp.add_parser("fetch")
    q.add_argument("link")
    q.add_argument("--out", required=True)
    q.set_defaults(fn=fetch)
    q = sp.add_parser("transcribe")
    q.add_argument("dir")
    q.add_argument("--lang", default="en")
    q.set_defaults(fn=transcribe)
    q = sp.add_parser("build")
    q.add_argument("dir")
    q.set_defaults(fn=build)
    a = p.parse_args()
    a.fn(a)
