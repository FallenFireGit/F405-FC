#!/usr/bin/python3.13
"""Render a ~15 s MP4 of the board's design history: one 3D render per committed board revision (git history of
kicad/F405FC.kicad_pcb) with a caption, cross-faded, then a turntable of the final board (top and bottom).

  /usr/bin/python3.13 gen/history_video.py [out.mp4]       (host python + Pillow; renders with kicad-cli through `kc`; ffmpeg)

Default output: docs/F405FC_design_history.mp4. Each revision is rendered from the same camera so the changes line up.
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "F405FC_design_history.mp4")
CH = "/opt/kroot"                      # KiCad chroot; /tmp inside it is CH + /tmp
WORK = "/tmp/histvid"
W, H, FPS = 960, 720, 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CAMERA = "-50,0,25"

# board-revision commits worth showing (oldest first) and their captions; the working-tree board is the final frame
REVS = [
    ("4054877", "First placement draft"),
    ("fc2999f", "Gate 0/1 fixes: crystal loads, LDO caps"),
    ("466f0d4", "Gate 3 rework: pin-anchored placement"),
    ("147f55c", "Clean placement, 4020 inductors"),
    ("8d71549", "Gate 2: bottom-side 100 V input caps"),
    ("c747eaa", "Scripted buck hot loops + VBAT routes"),
    ("cce9f56", "MCU inward fanout, first routing trials"),
    ("f088aee", "Gate 3 fixes: labels, pad grids, VBAT In2 zone"),
    ("ebfe172", "PathFinder router: first full attempt"),
    ("bf89f19", "Routability moves around the MCU"),
    ("0531bb0", "ADC clamps removed for routing space"),
    ("6216e29", "Converged routing, GND pours"),
]


def render(pcb_in_chroot, png_in_chroot, rotate, zoom=0.85):
    subprocess.run(["kc", f'kicad-cli pcb render --width {W} --height {H} --quality basic --perspective '
                          f'--zoom {zoom} --rotate "{rotate}" --background opaque -o {png_in_chroot} {pcb_in_chroot}'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return Image.open(CH + png_in_chroot).convert("RGB").resize((W, H))


def caption(img, title, sub):
    img = img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, H - 92, W, H], fill=(10, 14, 20, 200))
    d.text((24, H - 84), title, font=ImageFont.truetype(FONTB, 30), fill=(255, 255, 255))
    d.text((24, H - 42), sub, font=ImageFont.truetype(FONT, 22), fill=(190, 205, 220))
    return img


def main():
    shutil.rmtree(CH + WORK, ignore_errors=True)
    os.makedirs(CH + WORK + "/f")
    stills = []
    n = len(REVS) + 1
    for k, (sha, text) in enumerate(REVS):
        src = subprocess.run(["git", "-C", ROOT, "show", f"{sha}:kicad/F405FC.kicad_pcb"], capture_output=True, check=True).stdout
        open(f"{CH}{WORK}/r{k}.kicad_pcb", "wb").write(src)
        date = subprocess.run(["git", "-C", ROOT, "show", "-s", "--format=%ad", "--date=short", sha],
                              capture_output=True, text=True).stdout.strip()
        img = render(f"{WORK}/r{k}.kicad_pcb", f"{WORK}/r{k}.png", CAMERA)
        stills.append(caption(img, f"Rev {k + 1}/{n}  {text}", f"{date}  commit {sha}"))
        print("rendered", sha, flush=True)
    shutil.copy(os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"), f"{CH}{WORK}/final.kicad_pcb")
    final = render(f"{WORK}/final.kicad_pcb", f"{WORK}/final.png", CAMERA)
    stills.append(caption(final, f"Rev {n}/{n}  Final design", "36 x 36 mm, 4 layers, STM32F405"))
    frames = []
    hold, fade = 14, 5                      # 0.8 s per revision incl. cross-fade
    for i, s in enumerate(stills):
        frames += [s] * hold
        if i + 1 < len(stills):
            frames += [Image.blend(s, stills[i + 1], (t + 1) / (fade + 1)) for t in range(fade)]
    # turntable of the final board: top side half-turn, then bottom side
    spin = 36
    for t in range(spin):
        z = 25 + 360 * t / spin               # turn about the board normal; tilt -50 deg shows the top, -130 deg the bottom
        rot = f"{-50 if t < spin // 2 else -130},0,{z:.0f}"
        img = render(f"{WORK}/final.kicad_pcb", f"{WORK}/s{t}.png", rot)
        img = caption(img, "Final design", "top and bottom")
        frames += [img, img]                 # 12 fps turntable at 24 fps output
        print("spin", t, flush=True)
    for i, f in enumerate(frames):
        f.save(f"{CH}{WORK}/f/{i:05d}.png")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{CH}{WORK}/f/%05d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", OUT], check=True)
    print(f"history_video: {len(frames)} frames ({len(frames) / FPS:.1f} s) -> {OUT}")


if __name__ == "__main__":
    main()
