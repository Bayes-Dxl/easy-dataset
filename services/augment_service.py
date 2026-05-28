"""
# services/augment_service.py
数据增强预览服务：对单张图片应用多种增强变换，返回带标注框的 base64 预览图。

支持的增强类型：
  flip_h    水平翻转      flip_v     垂直翻转
  rotate90  旋转 90° CW   rotate180  旋转 180°   rotate270  旋转 270° CW
  brightness 提高亮度     contrast   提高对比度   grayscale  灰度化

bbox 坐标变换规则（YOLO 归一化 cx, cy, w, h）：
  flip_h:    cx → 1-cx
  flip_v:    cy → 1-cy
  rotate90:  (cx,cy,w,h) → (1-cy, cx, h, w)
  rotate180: (cx,cy)     → (1-cx, 1-cy)
  rotate270: (cx,cy,w,h) → (cy, 1-cx, h, w)
  color ops: bbox 不变
"""
import os
import io
import base64
from typing import Dict, List, Optional

from PIL import Image, ImageEnhance, ImageDraw

_COLORS = [
    (255, 56, 56), (255, 157, 151), (255, 112, 31), (255, 178, 29),
    (207, 210, 49), (72, 249, 10), (146, 204, 23), (61, 219, 134),
    (26, 147, 52), (0, 212, 187), (44, 153, 168), (0, 194, 255),
    (52, 69, 147), (100, 115, 255), (0, 24, 236), (132, 56, 255),
    (82, 0, 133), (203, 56, 255), (255, 149, 200), (255, 55, 199),
]

AUGMENT_DEFS: Dict[str, str] = {
    'flip_h': '水平翻转',
    'flip_v': '垂直翻转',
    'rotate90': '旋转 90°',
    'rotate180': '旋转 180°',
    'rotate270': '旋转 270°',
    'brightness': '提高亮度',
    'contrast': '提高对比度',
    'grayscale': '灰度化',
}


def _parse_labels(label_path: str) -> List[List[float]]:
    """解析 YOLO 标签，返回 [[cid, cx, cy, w, h], ...] 列表"""
    rows: List[List[float]] = []
    if label_path and os.path.isfile(label_path) and os.path.getsize(label_path) > 0:
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    rows.append([int(parts[0])] + [float(x) for x in parts[1:5]])
    return rows


def _draw_boxes(img: Image.Image, boxes: List[List[float]], class_names: Optional[List[str]]) -> None:
    W, H = img.size
    draw = ImageDraw.Draw(img)
    for box in boxes:
        cid, cx, cy, w, h = int(box[0]), box[1], box[2], box[3], box[4]
        x1 = int((cx - w / 2) * W)
        y1 = int((cy - h / 2) * H)
        x2 = int((cx + w / 2) * W)
        y2 = int((cy + h / 2) * H)
        color = _COLORS[cid % len(_COLORS)]
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        name = (class_names[cid] if class_names and cid < len(class_names) else str(cid))
        draw.rectangle([x1, y1 - 16, x1 + len(name) * 7 + 4, y1], fill=color)
        draw.text((x1 + 2, y1 - 15), name, fill=(255, 255, 255))


def _img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=82)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def _apply(img: Image.Image, boxes: List[List[float]], aug: str):
    """对图片和 bbox 同步应用一种增强，返回 (new_img, new_boxes)"""
    new_boxes: List[List[float]] = []

    if aug == 'flip_h':
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        for b in boxes:
            new_boxes.append([b[0], 1 - b[1], b[2], b[3], b[4]])

    elif aug == 'flip_v':
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        for b in boxes:
            new_boxes.append([b[0], b[1], 1 - b[2], b[3], b[4]])

    elif aug == 'rotate90':
        # PIL ROTATE_270 = 逆时针 270° = 视觉上顺时针 90°
        img = img.transpose(Image.ROTATE_270)
        for b in boxes:
            cid, cx, cy, w, h = b
            new_boxes.append([cid, 1 - cy, cx, h, w])

    elif aug == 'rotate180':
        img = img.transpose(Image.ROTATE_180)
        for b in boxes:
            cid, cx, cy, w, h = b
            new_boxes.append([cid, 1 - cx, 1 - cy, w, h])

    elif aug == 'rotate270':
        # PIL ROTATE_90 = 逆时针 90° = 视觉上顺时针 270°
        img = img.transpose(Image.ROTATE_90)
        for b in boxes:
            cid, cx, cy, w, h = b
            new_boxes.append([cid, cy, 1 - cx, h, w])

    elif aug == 'brightness':
        img = ImageEnhance.Brightness(img).enhance(1.6)
        new_boxes = [b[:] for b in boxes]

    elif aug == 'contrast':
        img = ImageEnhance.Contrast(img).enhance(1.6)
        new_boxes = [b[:] for b in boxes]

    elif aug == 'grayscale':
        img = img.convert('L').convert('RGB')
        new_boxes = [b[:] for b in boxes]

    else:
        new_boxes = [b[:] for b in boxes]

    return img, new_boxes


class AugmentService:

    @staticmethod
    def preview(
        image_path: str,
        label_path: str = '',
        augments: Optional[List[str]] = None,
        class_names: Optional[List[str]] = None,
    ) -> Dict:
        """对图片应用多种增强并返回 base64 预览图列表（含原图）"""
        try:
            if not os.path.isfile(image_path):
                return {'success': False, 'message': f'图片不存在: {image_path}'}

            if augments is None:
                augments = list(AUGMENT_DEFS.keys())

            base_img = Image.open(image_path).convert('RGB')
            W, H = base_img.size
            max_dim = 480
            if max(W, H) > max_dim:
                ratio = max_dim / max(W, H)
                base_img = base_img.resize((int(W * ratio), int(H * ratio)), Image.LANCZOS)

            boxes = _parse_labels(label_path)

            results = []
            # 原图
            orig = base_img.copy()
            _draw_boxes(orig, boxes, class_names)
            results.append({'aug': 'original', 'label': '原图', 'image_b64': _img_to_b64(orig)})

            for aug in augments:
                if aug not in AUGMENT_DEFS:
                    continue
                aug_img, aug_boxes = _apply(base_img.copy(), [b[:] for b in boxes], aug)
                _draw_boxes(aug_img, aug_boxes, class_names)
                results.append({
                    'aug': aug,
                    'label': AUGMENT_DEFS[aug],
                    'image_b64': _img_to_b64(aug_img),
                })

            return {'success': True, 'results': results}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def list_augments() -> Dict:
        return {
            'success': True,
            'augments': [{'id': k, 'label': v} for k, v in AUGMENT_DEFS.items()],
        }
