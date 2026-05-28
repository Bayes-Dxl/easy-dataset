"""
# services/split_service.py

## 核心功能
数据集划分服务：按比例将图片/标签划分为 train/val/test 三个子集，并可生成 data.yaml。
"""
import os
import random
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Optional


_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


class SplitService:

    @staticmethod
    def _collect_pairs(image_dir: str, label_dir: str):
        """收集图片-标签匹配对，返回 [(img_path, lbl_path_or_None)]"""
        pairs = []
        for f in sorted(Path(image_dir).iterdir()):
            if f.suffix.lower() not in _IMG_EXTS:
                continue
            lbl = Path(label_dir) / (f.stem + '.txt') if label_dir else None
            pairs.append((str(f), str(lbl) if lbl and lbl.exists() else None))
        return pairs

    @staticmethod
    def split(image_dir: str, label_dir: str, output_dir: str,
              train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1,
              seed: int = 42, generate_yaml: bool = True,
              class_names: List[str] = None) -> Dict:
        try:
            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}

            total = train_ratio + val_ratio + test_ratio
            if abs(total - 1.0) > 1e-6:
                return {'success': False, 'message': f'比例之和必须为 1.0，当前为 {total:.2f}'}

            pairs = SplitService._collect_pairs(image_dir, label_dir)
            if not pairs:
                return {'success': False, 'message': '未找到图片文件'}

            random.seed(seed)
            random.shuffle(pairs)

            n = len(pairs)
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)
            # test gets the remainder
            splits = {
                'train': pairs[:n_train],
                'val': pairs[n_train:n_train + n_val],
                'test': pairs[n_train + n_val:],
            }
            if not splits['test'] and test_ratio == 0:
                splits.pop('test')

            os.makedirs(output_dir, exist_ok=True)
            counts = {}
            for split_name, split_pairs in splits.items():
                img_out = os.path.join(output_dir, split_name, 'images')
                lbl_out = os.path.join(output_dir, split_name, 'labels')
                os.makedirs(img_out, exist_ok=True)
                os.makedirs(lbl_out, exist_ok=True)
                for img_path, lbl_path in split_pairs:
                    shutil.copy2(img_path, img_out)
                    if lbl_path:
                        shutil.copy2(lbl_path, lbl_out)
                counts[split_name] = len(split_pairs)

            # 生成 data.yaml
            yaml_path = None
            if generate_yaml:
                import yaml
                cfg = {
                    'path': os.path.abspath(output_dir),
                    'train': 'train/images',
                    'val': 'val/images',
                    'nc': len(class_names) if class_names else 0,
                    'names': class_names or [],
                }
                if 'test' in splits and splits['test']:
                    cfg['test'] = 'test/images'
                yaml_path = os.path.join(output_dir, 'data.yaml')
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)

            msg_parts = [f'{k}: {v}' for k, v in counts.items()]
            return {
                'success': True,
                'message': f'划分完成 — {", ".join(msg_parts)}',
                'counts': counts,
                'output_dir': output_dir,
                'yaml_path': yaml_path,
                'total': n,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
