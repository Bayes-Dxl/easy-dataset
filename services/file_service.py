"""
# services/file_service.py

## 核心功能
文件管理服务：一致性检查、空标签清理、空标签创建、批量重命名、图片修复。
"""
import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict


_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


class FileService:

    @staticmethod
    def _collect_images(directory: str) -> List[Path]:
        files = []
        for ext in _IMG_EXTS:
            files.extend(Path(directory).glob(f'*{ext}'))
            files.extend(Path(directory).glob(f'*{ext.upper()}'))
        return sorted(set(files))

    @staticmethod
    def check_consistency(image_dir: str, label_dir: str) -> Dict:
        try:
            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}

            images = {p.stem: str(p) for p in FileService._collect_images(image_dir)}
            labels = {p.stem: str(p) for p in Path(label_dir).glob('*.txt')}

            orphan_images = {s: images[s] for s in images if s not in labels}
            orphan_labels = {s: labels[s] for s in labels if s not in images}
            matched = {s for s in images if s in labels}

            return {
                'success': True,
                'total_images': len(images),
                'total_labels': len(labels),
                'matched': len(matched),
                'orphan_images': len(orphan_images),
                'orphan_labels': len(orphan_labels),
                'orphan_image_paths': list(orphan_images.values())[:100],
                'orphan_label_paths': list(orphan_labels.values())[:100],
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def delete_empty_labels(label_dir: str, dry_run: bool = True) -> Dict:
        try:
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}
            empty = [str(p) for p in Path(label_dir).glob('*.txt') if p.stat().st_size == 0]
            if not dry_run:
                for p in empty:
                    os.remove(p)
            return {
                'success': True,
                'dry_run': dry_run,
                'count': len(empty),
                'message': f'{"将删除" if dry_run else "已删除"} {len(empty)} 个空标签文件',
                'paths': empty[:100],
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def create_empty_labels(image_dir: str, label_dir: str) -> Dict:
        try:
            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}
            os.makedirs(label_dir, exist_ok=True)
            images = FileService._collect_images(image_dir)
            created = 0
            for img_path in images:
                label_path = Path(label_dir) / (img_path.stem + '.txt')
                if not label_path.exists():
                    label_path.touch()
                    created += 1
            return {
                'success': True,
                'message': f'已为 {created} 张图片创建空标签文件',
                'created': created,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def batch_rename(image_dir: str, label_dir: str = '',
                     prefix: str = 'img', dry_run: bool = True) -> Dict:
        try:
            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}
            images = sorted(FileService._collect_images(image_dir))
            plan = []
            for idx, img_path in enumerate(images):
                new_stem = f'{prefix}_{idx:06d}'
                new_img = img_path.parent / (new_stem + img_path.suffix)
                plan.append({
                    'old_image': str(img_path),
                    'new_image': str(new_img),
                    'old_stem': img_path.stem,
                    'new_stem': new_stem,
                })

            if not dry_run:
                for item in plan:
                    os.rename(item['old_image'], item['new_image'])
                    if label_dir and os.path.isdir(label_dir):
                        old_lbl = Path(label_dir) / (item['old_stem'] + '.txt')
                        new_lbl = Path(label_dir) / (item['new_stem'] + '.txt')
                        if old_lbl.exists():
                            os.rename(str(old_lbl), str(new_lbl))

            return {
                'success': True,
                'dry_run': dry_run,
                'count': len(plan),
                'message': f'{"预览" if dry_run else "已完成"} {len(plan)} 个文件重命名',
                'preview': plan[:20],
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def repair_images(image_dir: str, quality: int = 95, dry_run: bool = True) -> Dict:
        """重新保存图片以修复截断/损坏的 JPEG 文件"""
        try:
            from PIL import Image, ImageFile
            ImageFile.LOAD_TRUNCATED_IMAGES = True

            if not os.path.isdir(image_dir):
                return {'success': False, 'message': f'图片目录不存在: {image_dir}'}

            images = FileService._collect_images(image_dir)
            repaired, failed = 0, []
            for img_path in images:
                try:
                    with Image.open(str(img_path)) as img:
                        img.load()  # 强制完整加载
                    if not dry_run:
                        with Image.open(str(img_path)) as img:
                            img = img.convert('RGB')
                            img.save(str(img_path), quality=quality)
                    repaired += 1
                except Exception as e:
                    failed.append({'path': str(img_path), 'error': str(e)})

            return {
                'success': True,
                'dry_run': dry_run,
                'repaired': repaired,
                'failed': len(failed),
                'failed_list': failed[:20],
                'message': f'{"检测到" if dry_run else "已修复"} {repaired} 张图片，{len(failed)} 张损坏无法修复',
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
