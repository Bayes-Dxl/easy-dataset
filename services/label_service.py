"""
# services/label_service.py

## 核心功能
标签文件编辑服务：类别 ID 替换、删除、重排序。
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class LabelService:

    @staticmethod
    def _read_label(path: str) -> List[str]:
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()

    @staticmethod
    def _write_label(path: str, lines: List[str]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    @staticmethod
    def change_class(label_dir: str, old_id: int, new_id: int,
                     in_place: bool = False, output_dir: str = '') -> Dict:
        try:
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}
            out_dir = label_dir if in_place else output_dir
            if not in_place:
                if not out_dir:
                    return {'success': False, 'message': '未指定输出目录'}
                os.makedirs(out_dir, exist_ok=True)

            txt_files = list(Path(label_dir).glob('*.txt'))
            changed_files, changed_boxes = 0, 0
            for tf in txt_files:
                lines = LabelService._read_label(str(tf))
                new_lines, file_changed = [], False
                for line in lines:
                    parts = line.strip().split()
                    if parts and int(parts[0]) == old_id:
                        parts[0] = str(new_id)
                        file_changed = True
                        changed_boxes += 1
                    new_lines.append(' '.join(parts) + '\n' if parts else line)
                out_path = str(tf) if in_place else os.path.join(out_dir, tf.name)
                LabelService._write_label(out_path, new_lines)
                if file_changed:
                    changed_files += 1

            return {
                'success': True,
                'message': f'完成：修改了 {changed_files} 个文件，{changed_boxes} 个标注框',
                'changed_files': changed_files, 'changed_boxes': changed_boxes,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def delete_class(label_dir: str, class_id: int,
                     in_place: bool = False, output_dir: str = '') -> Dict:
        try:
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}
            out_dir = label_dir if in_place else output_dir
            if not in_place:
                if not out_dir:
                    return {'success': False, 'message': '未指定输出目录'}
                os.makedirs(out_dir, exist_ok=True)

            txt_files = list(Path(label_dir).glob('*.txt'))
            changed_files, deleted_boxes = 0, 0
            for tf in txt_files:
                lines = LabelService._read_label(str(tf))
                new_lines, file_changed = [], False
                for line in lines:
                    parts = line.strip().split()
                    if parts and int(parts[0]) == class_id:
                        file_changed = True
                        deleted_boxes += 1
                        continue
                    new_lines.append(line)
                out_path = str(tf) if in_place else os.path.join(out_dir, tf.name)
                LabelService._write_label(out_path, new_lines)
                if file_changed:
                    changed_files += 1

            return {
                'success': True,
                'message': f'完成：修改了 {changed_files} 个文件，删除了 {deleted_boxes} 个标注框',
                'changed_files': changed_files, 'deleted_boxes': deleted_boxes,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def reorder_classes(label_dir: str, order_map: Dict,
                        in_place: bool = False, output_dir: str = '') -> Dict:
        """order_map: {"0": 2, "1": 0, "2": 1, ...} 原ID→新ID"""
        try:
            if not os.path.isdir(label_dir):
                return {'success': False, 'message': f'标签目录不存在: {label_dir}'}
            mapping = {int(k): int(v) for k, v in order_map.items()}
            out_dir = label_dir if in_place else output_dir
            if not in_place:
                if not out_dir:
                    return {'success': False, 'message': '未指定输出目录'}
                os.makedirs(out_dir, exist_ok=True)

            txt_files = list(Path(label_dir).glob('*.txt'))
            processed = 0
            for tf in txt_files:
                lines = LabelService._read_label(str(tf))
                new_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        cid = int(parts[0])
                        parts[0] = str(mapping.get(cid, cid))
                    new_lines.append(' '.join(parts) + '\n' if parts else line)
                out_path = str(tf) if in_place else os.path.join(out_dir, tf.name)
                LabelService._write_label(out_path, new_lines)
                processed += 1

            return {
                'success': True,
                'message': f'完成：处理了 {processed} 个文件',
                'processed': processed,
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
