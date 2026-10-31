"""미니 포토샵: 밝기·대비·채도·색조 조절, 크기 변경, 비율 맞춰 가운데 자르기.

사용 예:
    python photo_edit.py 사진.jpg --brightness 1.2 --ratio 4:5
    python photo_edit.py 사진폴더 --width 1080 --contrast 1.1 --out 결과폴더
    python photo_edit.py 사진폴더 --recursive --hue 15 --saturation 1.3

처리 순서: 비율 자르기 → 크기 변경 → 밝기 → 대비 → 채도 → 색온도 → 색조
원본은 절대 덮어쓰지 않는다. 결과는 새 폴더(기본: <입력 위치>/보정결과)에 저장.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
RATIOS = {"1:1": (1, 1), "4:5": (4, 5), "9:16": (9, 16)}
DEFAULT_OUT = "보정결과"


def crop_to_ratio(img, ratio):
    """가운데를 기준으로 목표 비율이 되도록 자른다."""
    rw, rh = RATIOS[ratio]
    w, h = img.size
    if w * rh > h * rw:  # 원본이 더 넓음 → 좌우를 자름
        new_w = round(h * rw / rh)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    new_h = round(w * rh / rw)  # 원본이 더 높음 → 위아래를 자름
    top = (h - new_h) // 2
    return img.crop((0, top, w, top + new_h))


def resize(img, width, height, scale):
    w, h = img.size
    if scale:
        width, height = round(w * scale / 100), round(h * scale / 100)
    elif width and not height:
        height = round(h * width / w)
    elif height and not width:
        width = round(w * height / h)
    if not width:
        return img
    return img.resize((width, height), Image.LANCZOS)


def shift_hue(img, degrees):
    """색상환에서 degrees(-180~180)만큼 색조를 돌린다. 투명도는 유지."""
    alpha = img.getchannel("A") if img.mode == "RGBA" else None
    h, s, v = img.convert("RGB").convert("HSV").split()
    offset = round(degrees / 360 * 256)
    h = h.point(lambda x: (x + offset) % 256)
    out = Image.merge("HSV", (h, s, v)).convert("RGB")
    if alpha:
        out.putalpha(alpha)
    return out


def adjust_warmth(img, amount):
    """색온도 조절. amount -100(차갑게, 파랑)~100(따뜻하게, 주황). 빨강·파랑 채널 비율을 바꾼다."""
    k = amount / 100 * 0.15
    bands = list(img.split())
    bands[0] = bands[0].point(lambda x: min(255, round(x * (1 + k))))
    bands[2] = bands[2].point(lambda x: min(255, round(x * (1 - k))))
    return Image.merge(img.mode, bands)


def edit(img, a):
    img = ImageOps.exif_transpose(img)  # 휴대폰 사진 회전 정보 반영
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    width, height = a.width, a.height
    if a.ratio:
        img = crop_to_ratio(img, a.ratio)
        # 자를 때 생긴 1px 반올림 오차가 크기에 남지 않도록 빠진 변은 비율로 계산
        rw, rh = RATIOS[a.ratio]
        if width and not height:
            height = round(width * rh / rw)
        elif height and not width:
            width = round(height * rw / rh)
    img = resize(img, width, height, a.scale)
    for factor, enhancer in ((a.brightness, ImageEnhance.Brightness),
                             (a.contrast, ImageEnhance.Contrast),
                             (a.saturation, ImageEnhance.Color)):
        if factor != 1.0:
            img = enhancer(img).enhance(factor)
    if a.warmth:
        img = adjust_warmth(img, a.warmth)
    if a.hue:
        img = shift_hue(img, a.hue)
    return img


def save(img, path):
    if path.suffix.lower() in (".jpg", ".jpeg"):
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.getchannel("A"))
            img = bg
        img.save(path, quality=95, subsampling=0)
    else:
        img.save(path)


def collect(src, recursive, out_dir):
    if src.is_file():
        return [src]
    pattern = "**/*" if recursive else "*"
    return sorted(p for p in src.glob(pattern)
                  if p.is_file() and p.suffix.lower() in EXTS
                  and out_dir not in p.parents)  # 이전 결과 폴더는 건너뜀


def main():
    p = argparse.ArgumentParser(description="미니 포토샵 (Pillow)")
    p.add_argument("input", help="사진 파일 또는 폴더")
    p.add_argument("--out", help=f"결과 폴더 (기본: 입력 위치의 '{DEFAULT_OUT}')")
    p.add_argument("--recursive", action="store_true", help="하위 폴더 사진까지 처리")
    p.add_argument("--brightness", type=float, default=1.0, help="밝기 배율 (1.0=그대로, 1.2=20%% 밝게)")
    p.add_argument("--contrast", type=float, default=1.0, help="대비 배율 (1.0=그대로)")
    p.add_argument("--saturation", type=float, default=1.0, help="채도 배율 (0=흑백, 1.0=그대로)")
    p.add_argument("--warmth", type=float, default=0.0, help="색온도 -100(차갑게)~100(따뜻하게)")
    p.add_argument("--hue", type=float, default=0.0, help="색조 회전 각도 -180~180 (모든 색이 함께 돈다)")
    p.add_argument("--ratio", choices=RATIOS, help="가운데 기준으로 비율 자르기")
    size = p.add_mutually_exclusive_group()
    size.add_argument("--scale", type=float, help="크기 퍼센트 (50=절반)")
    size.add_argument("--width", type=int, help="가로 픽셀 (세로만 없으면 비율 유지)")
    p.add_argument("--height", type=int, help="세로 픽셀 (가로만 없으면 비율 유지)")
    a = p.parse_args()

    src = Path(a.input).resolve()
    if not src.exists():
        sys.exit(f"입력을 찾을 수 없음: {src}")
    base = src if src.is_dir() else src.parent
    out_dir = Path(a.out).resolve() if a.out else base / DEFAULT_OUT
    if out_dir == base:
        sys.exit("결과 폴더가 원본 폴더와 같으면 원본을 덮어쓸 수 있어 중단합니다. --out 으로 다른 폴더를 지정하세요.")

    files = collect(src, a.recursive, out_dir)
    if not files:
        sys.exit("처리할 사진이 없습니다.")

    done = 0
    for f in files:
        target = out_dir / (f.relative_to(base) if src.is_dir() else f.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(f) as img:
                result = edit(img, a)
            save(result, target)
            done += 1
            print(f"완료: {f.name} → {target}  ({result.width}x{result.height})")
        except Exception as e:  # 한 장이 실패해도 나머지는 계속
            print(f"실패: {f.name} ({e})")
    print(f"\n{done}/{len(files)}장 처리, 결과 폴더: {out_dir}")


if __name__ == "__main__":
    main()
