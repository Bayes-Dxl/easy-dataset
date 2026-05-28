"""
# services/export_service.py
导出服务：将 YOLO 格式数据集导出为 COCO JSON 格式。
"""
import os
import json
import glob
import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image as PILImage


class ExportService:

    @staticmethod
    def _collect_images(image_dir: str) -> List[str]:
        exts = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp')
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(image_dir, ext)))
            files.extend(glob.glob(os.path.join(image_dir, ext.upper())))
        return sorted(set(files))

    @staticmethod
    def yolo2coco(
        image_dir: str,
        label_dir: str,
        output_path: str,
        class_names: Optional[List[str]] = None,
    ) -> Dict:
        """将 YOLO 格式数据集导出为 COCO JSON 文件。

        YOLO bbox (cx, cy, w, h) 归一化坐标转换为 COCO bbox (x_min, y_min, width, height) 绝对像素坐标。
        COCO category_id 从 1 开始（YOLO class_id 从 0 开始）。
        """
        try:
            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}

            images_paths = ExportService._collect_images(image_dir)
            if not images_paths:
                return {'success': False, 'message': '图片目录中没有找到图片'}

            # 确保输出目录存在
            out_dir = os.path.dirname(os.path.abspath(output_path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            coco: Dict = {
                'info': {
                    'description': 'Exported by Easy Dataset Station',
                    'version': '1.0',
                    'date_created': datetime.date.today().isoformat(),
                },
                'licenses': [],
                'categories': [],
                'images': [],
                'annotations': [],
            }

            # 预扫描所有出现的 class_id（用于未提供 class_names 时自动生成 categories）
            if not class_names:
                seen_ids: set = set()
                for p in images_paths:
                    lbl = os.path.join(label_dir, Path(p).stem + '.txt')
                    if os.path.isfile(lbl):
                        with open(lbl, 'r') as f:
                            for line in f:
                                parts = line.strip().split()
                                if len(parts) >= 5:
                                    seen_ids.add(int(parts[0]))
                coco['categories'] = [
                    {'id': cid + 1, 'name': f'class_{cid}', 'supercategory': ''}
                    for cid in sorted(seen_ids)
                ]
            else:
                coco['categories'] = [
                    {'id': idx + 1, 'name': name, 'supercategory': ''}
                    for idx, name in enumerate(class_names)
                ]

            ann_id = 1
            img_id = 1
            converted = 0
            skipped = 0

            for img_path in images_paths:
                stem = Path(img_path).stem
                filename = os.path.basename(img_path)
                lbl_path = os.path.join(label_dir, stem + '.txt')

                try:
                    with PILImage.open(img_path) as img:
                        W, H = img.size
                except Exception:
                    skipped += 1
                    continue

                coco['images'].append({
                    'id': img_id,
                    'file_name': filename,
                    'width': W,
                    'height': H,
                })

                if os.path.isfile(lbl_path) and os.path.getsize(lbl_path) > 0:
                    with open(lbl_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) < 5:
                                continue
                            cid = int(parts[0])
                            cx = float(parts[1])
                            cy = float(parts[2])
                            rw = float(parts[3])
                            rh = float(parts[4])
                            # YOLO 归一化 → COCO 绝对像素 (top-left x, y, w, h)
                            x_min = (cx - rw / 2) * W
                            y_min = (cy - rh / 2) * H
                            bw = rw * W
                            bh = rh * H
                            coco['annotations'].append({
                                'id': ann_id,
                                'image_id': img_id,
                                'category_id': cid + 1,
                                'bbox': [round(x_min, 2), round(y_min, 2), round(bw, 2), round(bh, 2)],
                                'area': round(bw * bh, 2),
                                'iscrowd': 0,
                                'segmentation': [],
                            })
                            ann_id += 1

                img_id += 1
                converted += 1

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(coco, f, ensure_ascii=False, indent=2)

            return {
                'success': True,
                'message': f'成功导出 {converted} 张图片，{ann_id - 1} 个标注框',
                'output_path': output_path,
                'total_images': converted,
                'total_annotations': ann_id - 1,
                'skipped': skipped,
            }

        except Exception as e:
            return {'success': False, 'message': str(e)}
