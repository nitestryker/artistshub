import io
import logging

logger = logging.getLogger(__name__)

MAX_TAGS = 10

CATEGORY_TAGS = {
    'digital': ['digital art', 'digital', 'computer art'],
    'painting': ['painting', 'fine art'],
    'drawing': ['drawing', 'illustration', 'sketch'],
    'photography': ['photography', 'photo'],
    'sculpture': ['sculpture', '3D', 'handmade'],
    'mixed_media': ['mixed media', 'collage'],
    'printmaking': ['printmaking', 'print'],
    'textile': ['textile', 'fiber art', 'handmade'],
    'ceramics': ['ceramics', 'pottery', 'handmade'],
    'street': ['street art', 'graffiti', 'urban'],
    'other': [],
}


def _color_name(r, g, b):
    hue_map = [
        (15, 'red'), (45, 'orange'), (70, 'yellow'),
        (150, 'green'), (195, 'cyan'), (255, 'blue'),
        (285, 'magenta'), (330, 'pink'), (360, 'red'),
    ]
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    if delta < 20:
        if max_c < 60:
            return 'black'
        if max_c > 200:
            return 'white'
        return 'gray'

    if max_c == r:
        hue = 60 * (((g - b) / delta) % 6)
    elif max_c == g:
        hue = 60 * (((b - r) / delta) + 2)
    else:
        hue = 60 * (((r - g) / delta) + 4)

    if hue < 0:
        hue += 360

    for threshold, name in hue_map:
        if hue <= threshold:
            return name
    return 'red'


def _extract_colors(image_bytes):
    try:
        from colorthief import ColorThief
        thief = ColorThief(io.BytesIO(image_bytes))
        palette = thief.get_palette(color_count=5, quality=10)
        seen = set()
        color_tags = []
        for r, g, b in palette:
            name = _color_name(r, g, b)
            if name not in seen:
                seen.add(name)
                color_tags.append(name)
        return color_tags
    except Exception as e:
        logger.warning('Color extraction failed: %s', e)
        return []


def _analyze_image_style(image_bytes):
    try:
        from PIL import Image
        import struct

        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_small = img.resize((100, 100))
        pixels = list(img_small.getdata())

        total = len(pixels)
        r_avg = sum(p[0] for p in pixels) / total
        g_avg = sum(p[1] for p in pixels) / total
        b_avg = sum(p[2] for p in pixels) / total

        brightness = (r_avg + g_avg + b_avg) / 3
        r_var = sum((p[0] - r_avg) ** 2 for p in pixels) / total
        g_var = sum((p[1] - g_avg) ** 2 for p in pixels) / total
        b_var = sum((p[2] - b_avg) ** 2 for p in pixels) / total
        saturation_variance = (r_var + g_var + b_var) / 3

        tags = []
        if brightness < 80:
            tags.append('dark')
        elif brightness > 180:
            tags.append('bright')

        if saturation_variance > 2000:
            tags.append('colorful')
        elif saturation_variance < 300:
            tags.append('monochrome')

        width, height = img.size
        if width > height * 1.4:
            tags.append('landscape')
        elif height > width * 1.4:
            tags.append('portrait')

        return tags
    except Exception as e:
        logger.warning('Image style analysis failed: %s', e)
        return []


def generate_tags(image_path=None, image_bytes=None, category=None):
    if image_bytes is None and image_path is not None:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

    if not image_bytes:
        return []

    tags = []

    if category and category in CATEGORY_TAGS:
        tags.extend(CATEGORY_TAGS[category])

    style_tags = _analyze_image_style(image_bytes)
    for t in style_tags:
        if t not in tags:
            tags.append(t)

    color_tags = _extract_colors(image_bytes)
    for t in color_tags:
        if t not in tags:
            tags.append(t)

    return tags[:MAX_TAGS]
