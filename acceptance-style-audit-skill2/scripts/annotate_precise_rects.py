#!/usr/bin/env python3
import argparse
import json
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int):
    for p in [
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/System/Library/Fonts/Supplemental/PingFang.ttc',
    ]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def scale_rect(rect, sx, sy):
    return (
        round(rect['x'] * sx),
        round(rect['y'] * sy),
        round(rect['width'] * sx),
        round(rect['height'] * sy),
    )


def draw_label_box(draw, rect, label, color, font):
    x, y, w, h = rect
    draw.rectangle((x, y, x + w, y + h), outline=color, width=4)
    tag_h = 30
    tag_w = max(180, min(520, len(label) * 16))
    ty = max(0, y - tag_h)
    draw.rectangle((x, ty, x + tag_w, y), fill=color)
    draw.text((x + 8, ty + 4), label, fill='white', font=font)


def main():
    parser = argparse.ArgumentParser(description='Annotate screenshot with precise rects from same-frame DOM metrics.')
    parser.add_argument('--image', required=True, help='Screenshot path (same frame as rect capture)')
    parser.add_argument('--metrics', required=True, help='JSON file with viewport and rects')
    parser.add_argument('--output', required=True, help='Output image path')
    parser.add_argument('--show-root', action='store_true', help='Draw root rect helper in blue')
    args = parser.parse_args()

    with open(args.metrics, 'r', encoding='utf-8') as f:
        data = json.load(f)

    image = Image.open(args.image).convert('RGB')
    draw = ImageDraw.Draw(image)

    vw = data['viewport']['w']
    vh = data['viewport']['h']
    sx = image.width / vw
    sy = image.height / vh

    font = load_font(24)

    if args.show_root and data.get('root'):
        root_rect = scale_rect(data['root'], sx, sy)
        draw_label_box(draw, root_rect, '目标容器 root div', (0, 122, 255), font)

    if data.get('title'):
        rect = scale_rect(data['title'], sx, sy)
        draw_label_box(draw, rect, 'A: 标题差异', (220, 0, 0), font)

    if data.get('chip'):
        rect = scale_rect(data['chip'], sx, sy)
        draw_label_box(draw, rect, 'B: 首卡差异', (220, 0, 0), font)

    image.save(args.output)
    print(args.output)


if __name__ == '__main__':
    main()
