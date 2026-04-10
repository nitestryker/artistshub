import io
import logging

logger = logging.getLogger(__name__)

ART_STYLE_LABELS = [
    'realism', 'abstract', 'impressionism', 'expressionism', 'surrealism',
    'minimalism', 'pop art', 'cubism', 'digital art', 'anime', 'manga',
    'concept art', 'illustration', 'sketch', 'watercolor', 'oil painting',
    'pixel art', '3D render', 'street art', 'graffiti',
]

CONFIDENCE_THRESHOLD = 0.2
MAX_TAGS = 10

_clip_model = None
_clip_preprocess = None
_clip_device = None


def _load_clip():
    global _clip_model, _clip_preprocess, _clip_device
    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _clip_device
    import torch
    import clip as openai_clip
    _clip_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    _clip_model, _clip_preprocess = openai_clip.load('ViT-B/32', device=_clip_device)
    return _clip_model, _clip_preprocess, _clip_device


def _detect_styles(image_bytes):
    try:
        import torch
        import clip as openai_clip
        from PIL import Image

        model, preprocess, device = _load_clip()

        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_input = preprocess(image).unsqueeze(0).to(device)

        text_inputs = openai_clip.tokenize(
            [f'a {label} artwork' for label in ART_STYLE_LABELS]
        ).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_inputs)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (image_features @ text_features.T).squeeze(0)
            probs = similarity.softmax(dim=-1).cpu().numpy()

        return [
            ART_STYLE_LABELS[i]
            for i, score in enumerate(probs)
            if score >= CONFIDENCE_THRESHOLD
        ]
    except Exception as e:
        logger.warning('CLIP style detection failed: %s', e)
        return []


def _color_name(r, g, b):
    hue_map = [
        (15, 'red'), (45, 'orange'), (70, 'yellow'),
        (150, 'green'), (195, 'cyan'), (255, 'blue'),
        (285, 'purple'), (330, 'pink'), (360, 'red'),
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
        palette = thief.get_palette(color_count=5, quality=5)
        seen = set()
        color_tags = []
        for r, g, b in palette:
            name = _color_name(r, g, b)
            if name not in seen:
                seen.add(name)
                color_tags.append(name)
        return color_tags
    except Exception as e:
        logger.warning('ColorThief color extraction failed: %s', e)
        return []


def generate_tags(image_path=None, image_bytes=None):
    if image_bytes is None and image_path is not None:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

    if not image_bytes:
        return []

    style_tags = _detect_styles(image_bytes)
    color_tags = _extract_colors(image_bytes)

    combined = style_tags + [c for c in color_tags if c not in style_tags]
    return combined[:MAX_TAGS]
