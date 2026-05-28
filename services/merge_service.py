"""
# services/merge_service.py
数据集合并服务：将多个 YOLO 格式数据集合并为一个，支持类别偏移和类别 ID 重映射。
"""
import os
import glob
import shutil
from pathlib import Path
from typing import Dict, List


class MergeService:

    @staticmethod
    def _collect_images(image_dir: str) -> List[str]:
        exts = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp')
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(image_dir, ext)))
            files.extend(glob.glob(os.path.join(image_dir, ext.upper())))
        return sorted(set(files))

    @staticmethod
    def merge(
        sources: List[Dict],
        output_image_dir: str,
        output_label_dir: str,
        prefix_by_source: bool = False,
    ) -> Dict:
        """合并多个 YOLO 数据集。

        Args:
            sources: 数据集来源列表，每项包含：
                - image_dir (str): 图片目录
                - label_dir (str): 标签目录（可空）
                - class_offset (int, 默认 0): 类别 ID 偏移量，所有 class_id += class_offset
                - class_remap (dict, 可选): 显式类别映射 {old_id: new_id}，优先于 class_offset
            output_image_dir: 合并后图片输出目录
            output_label_dir: 合并后标签输出目录
            prefix_by_source: 是否给文件名添加来源编号前缀（如 src1_xxx.jpg）
        """
        try:
            if not sources:
                return {'success': False, 'message': '请至少提供一个数据集来源'}

            os.makedirs(output_image_dir, exist_ok=True)
            os.makedirs(output_label_dir, exist_ok=True)

            total_images = 0
            total_labels = 0
            conflicts = 0
            src_errors: List[str] = []
            # 跨来源追踪已使用的输出 stem，防止同 stem 不同扩展名（如 foo.jpg / foo.png）
            # 将同名 foo.txt 互相覆盖，导致数据集不一致
            used_stems: set = set()

            for src_idx, src in enumerate(sources):
                image_dir = src.get('image_dir', '')
                label_dir = src.get('label_dir', '')
                class_offset = int(src.get('class_offset', 0))
                # class_remap: {old_id_str: new_id_str} → {int: int}
                raw_remap = src.get('class_remap', {}) or {}
                class_remap: Dict[int, int] = {int(k): int(v) for k, v in raw_remap.items()}
                need_remap = class_offset != 0 or bool(class_remap)

                if not image_dir or not os.path.isdir(image_dir):
                    src_errors.append(f'来源 {src_idx + 1}: 图片目录不存在 "{image_dir}"')
                    continue

                images = MergeService._collect_images(image_dir)
                for img_path in images:
                    stem = Path(img_path).stem
                    ext = Path(img_path).suffix
                    base_name = os.path.basename(img_path)

                    # 目标文件名（可选前缀）
                    dst_name = f'src{src_idx + 1}_{base_name}' if prefix_by_source else base_name
                    dst_img = os.path.join(output_image_dir, dst_name)
                    dst_stem = Path(dst_name).stem

                    # 处理冲突：图片文件已存在 或 标签 stem 已被占用
                    # 后者专门拦截 foo.jpg + foo.png → foo.txt 覆盖场景
                    if os.path.exists(dst_img) or dst_stem in used_stems:
                        conflicts += 1
                        dst_stem = f'{dst_stem}_s{src_idx + 1}'
                        dst_name = f'{dst_stem}{ext}'
                        dst_img = os.path.join(output_image_dir, dst_name)

                    shutil.copy2(img_path, dst_img)
                    used_stems.add(dst_stem)
                    total_images += 1
                    new_stem = dst_stem

                    # 处理标签
                    if label_dir and os.path.isdir(label_dir):
                        src_lbl = os.path.join(label_dir, stem + '.txt')
                        dst_lbl = os.path.join(output_label_dir, new_stem + '.txt')
                        if os.path.isfile(src_lbl):
                            if not need_remap:
                                shutil.copy2(src_lbl, dst_lbl)
                            else:
                                new_lines: List[str] = []
                                with open(src_lbl, 'r') as f:
                                    for line in f:
                                        parts = line.strip().split()
                                        if len(parts) >= 5:
                                            cid = int(parts[0])
                                            # class_remap 优先且完整：显式映射的类别不再叠加 offset
                                            if cid in class_remap:
                                                cid = class_remap[cid]
                                            else:
                                                cid += class_offset
                                            new_lines.append(f'{cid} ' + ' '.join(parts[1:]))
                                        elif parts:
                                            new_lines.append(line.rstrip())
                                with open(dst_lbl, 'w') as f:
                                    f.write('\n'.join(new_lines))
                            total_labels += 1

            msg = f'合并完成：{total_images} 张图片，{total_labels} 个标签文件'
            if conflicts:
                msg += f'，{conflicts} 个文件名冲突（已自动重命名）'
            if src_errors:
                msg += '\n警告：' + '；'.join(src_errors)

            return {
                'success': True,
                'message': msg,
                'total_images': total_images,
                'total_labels': total_labels,
                'conflicts': conflicts,
                'errors': src_errors,
            }

        except Exception as e:
            return {'success': False, 'message': str(e)}
