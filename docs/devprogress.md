# Easy Dataset Station — 开发进度记录

> 更新时间：2026-05-26

---

## Phase 1 — 后端 Bug 修复与功能补全

### P1.1 修复 `analyze()` 四处 Bug（`services/dataset_service.py`）

| # | 问题 | 修复方式 |
|---|---|---|
| 1 | `invalid_rows` 未统计 | 新增计数器，对 `len(parts) < 5` 的非空行累加 |
| 2 | 小目标阈值错误（1% → 0.5%） | `a < 0.01` 改为 `a < 0.005` |
| 3 | 大目标阈值错误（25% → 10%） | `a > 0.25` 改为 `a > 0.10` |
| 4 | `image_size_stats` 缺少高度范围 | 补充 `min_height`、`max_height` 字段 |

### P1.2 实现 `list_images()` 服务端过滤（`services/dataset_service.py`）

- 新增参数 `filter: str = 'all'`，支持 `with_label` / `no_label` 两种过滤模式
- 路由 `POST /api/dataset/list-images` 同步透传 `filter` 参数（`routes/main_routes.py`）

### P1.3 添加 `box_count` 字段（`services/dataset_service.py`）

- `list_images()` 每条图片记录新增 `box_count`，通过读取对应 TXT 文件行数统计

### P1.4 添加 `class_distribution` 的 `ratio` 字段（`services/dataset_service.py`）

- 每个类别分布项补充 `ratio = count / total_boxes`，保留 4 位小数

### 前端类型同步（`src/lib/store.ts`、`src/lib/tauri-bridge.ts`）

| 文件 | 变更内容 |
|---|---|
| `store.ts` | `ClassDist` 加 `ratio: number` |
| `store.ts` | `DatasetSummary` 加 `invalid_rows: number` |
| `store.ts` | `DatasetAnalysis.image_size_stats` 加 `min_height`、`max_height` |
| `store.ts` | `ImageItem` 加 `box_count: number` |
| `tauri-bridge.ts` | `api.listImages` 参数签名加 `filter?` 可选参数 |

---

## Phase 2 — 前端 UI 完善

### P2.2 DatasetQuality.tsx — 孤立标签路径列表

- 问题文件折叠面板已包含三个 `FileList` 区块：孤立图片、**孤立标签**、空标签
- 渲染条件：`result.orphan_label_paths.length > 0`，路径以等宽字体滚动列表展示

### P2.3 FileManager.tsx — 一致性检查孤立路径渲染

- 一致性检查结果中，使用 `PathList` 组件渲染 `orphan_image_paths` 和 `orphan_label_paths`
- 标题带数量显示（如"孤立图片路径（共 N 个）"），最大高度 `max-h-36` 可滚动

### P2.4 FileManager.tsx — 批量重命名预览表格

- 执行/预览后，`result.preview`（最多 20 条 `RenameItem`）以两列表格展示
- 每行显示：旧文件名 `→` 新文件名，最大高度 `max-h-48` 可滚动

### P2.5 DatasetViewer.tsx — filter 参数传至后端

- 新增 `filterMap: { all: 'all', yes: 'with_label', no: 'no_label' }`
- `loadImages()` 调用 `api.listImages` 时传入 `filter: filterMap[activeFilter]`
- 过滤在服务端完成，返回结果直接渲染，不再做客户端二次过滤

---

## Phase 3 — v0.2.0 新功能开发

### P3.1 COCO JSON 导出

**后端**：新建 `services/export_service.py`

- `ExportService.yolo2coco(image_dir, label_dir, output_path, class_names?)` 
- YOLO 归一化坐标 → COCO 绝对像素坐标转换：`x_min = (cx - w/2) * W`
- COCO `category_id` 从 1 开始（YOLO `class_id` 从 0 开始）
- 未提供 `class_names` 时自动预扫描所有 TXT，生成 `class_N` 命名
- 返回：`total_images`、`total_annotations`、`skipped`

**路由**：`POST /api/export/coco`（`routes/main_routes.py`）

**前端**：`src/pages/DatasetExport.tsx`（COCO 导出区域）
- 图片目录、标签目录、输出文件（另存为对话框）、类别名称输入
- 导出结果带数量统计

---

### P3.2 数据集合并

**后端**：新建 `services/merge_service.py`

- `MergeService.merge(sources, output_image_dir, output_label_dir, prefix_by_source?)`
- `sources` 列表每项支持：`image_dir`、`label_dir`、`class_offset`（整数偏移）、`class_remap`（字典映射）
- 文件名冲突自动追加来源编号后缀（如 `img001_s2.jpg`）
- 返回：`total_images`、`total_labels`、`conflicts`、`errors`

**路由**：`POST /api/merge/run`（`routes/main_routes.py`）

**前端**：`src/pages/DatasetMerge.tsx`
- 动态来源列表（可增删），每项配置图片目录、标签目录、类别偏移量
- 输出目录配置 + 文件名前缀开关
- 合并结果面板：数量统计 + 可折叠警告列表

---

### P3.3 数据增强预览

**后端**：新建 `services/augment_service.py`

支持 8 种增强类型，**bbox 坐标同步变换**：

| 增强类型 | PIL 操作 | bbox 变换规则 |
|---|---|---|
| `flip_h` 水平翻转 | `FLIP_LEFT_RIGHT` | `cx → 1 - cx` |
| `flip_v` 垂直翻转 | `FLIP_TOP_BOTTOM` | `cy → 1 - cy` |
| `rotate90` 旋转 90° CW | `ROTATE_270` | `(cx,cy,w,h) → (1-cy, cx, h, w)` |
| `rotate180` 旋转 180° | `ROTATE_180` | `(cx,cy) → (1-cx, 1-cy)` |
| `rotate270` 旋转 270° CW | `ROTATE_90` | `(cx,cy,w,h) → (cy, 1-cx, h, w)` |
| `brightness` 提高亮度 | `ImageEnhance.Brightness × 1.6` | bbox 不变 |
| `contrast` 提高对比度 | `ImageEnhance.Contrast × 1.6` | bbox 不变 |
| `grayscale` 灰度化 | `L → RGB` | bbox 不变 |

- `AugmentService.preview()` 返回原图 + 各增强结果的 base64 JPEG 列表
- 预览尺寸限制 480px（避免传输过慢）

**路由**：`POST /api/augment/preview`、`GET /api/augment/list`（`routes/main_routes.py`）

**前端**：`src/pages/AugmentPreview.tsx`
- 增强类型多选标签（全选 / 清空）
- 响应式网格展示增强结果（含 bbox 绘制）

---

### P3.4 BBox 统计图表

**后端**：`DatasetService.bbox_histogram(label_dir)` 新方法（`services/dataset_service.py`）

面积分布分档：

| 区间 | 说明 |
|---|---|
| < 0.1% | 极小目标 |
| 0.1–0.5% | 小目标 |
| 0.5–1% | 较小目标 |
| 1–5% | 中小目标 |
| 5–10% | 中目标 |
| 10–25% | 较大目标 |
| > 25% | 大目标 |

宽高比分布分档：`< 0.25`、`0.25–0.5`、`0.5–1.0`、`1.0–2.0`、`2.0–4.0`、`> 4.0`

**路由**：`POST /api/dataset/bbox-histogram`（`routes/main_routes.py`）

**前端**：`src/pages/DatasetExport.tsx`（统计图表区域）
- 输入标签目录，生成面积分布 + 宽高比分布 CSS 条形图
- 两个图表独立可折叠

---

### 前端集成（`src/pages/MainPage.tsx`、`src/lib/tauri-bridge.ts`、`src/lib/store.ts`）

**导航栏新增 3 项：**

| 页面 ID | 菜单文字 | 图标 |
|---|---|---|
| `export` | 导出 & 图表 | `Download` |
| `merge` | 数据集合并 | `GitMerge` |
| `augment` | 增强预览 | `Wand2` |

**`tauri-bridge.ts` 新增方法：**
- `browseSaveFile()` — 文件另存为对话框
- `api.bboxHistogram()` — BBox 直方图
- `api.exportCoco()` — COCO 导出
- `api.mergeDatasets()` — 数据集合并
- `api.augmentPreview()` — 增强预览

**`store.ts` 类型扩展：**
- `activePage` 联合类型增加 `"export" | "merge" | "augment"`

---

## 文件变更清单

### 新建文件

| 文件 | 用途 |
|---|---|
| `services/export_service.py` | COCO JSON 导出服务 |
| `services/merge_service.py` | 数据集合并服务 |
| `services/augment_service.py` | 数据增强预览服务 |
| `src/pages/DatasetExport.tsx` | 导出 & 统计图表页面 |
| `src/pages/DatasetMerge.tsx` | 数据集合并页面 |
| `src/pages/AugmentPreview.tsx` | 增强预览页面 |

### 修改文件

| 文件 | 变更摘要 |
|---|---|
| `services/dataset_service.py` | 修复 4 个 Bug；`list_images()` 加 filter/box_count；新增 `bbox_histogram()` |
| `routes/main_routes.py` | 导入 3 个新 service；新增 5 条路由；list-images 透传 filter 参数 |
| `src/lib/store.ts` | 类型补全：`ClassDist.ratio`、`DatasetSummary.invalid_rows`、`image_size_stats` height 字段、`ImageItem.box_count`；`activePage` 扩展 3 个新值 |
| `src/lib/tauri-bridge.ts` | 导入 `save`；新增 `browseSaveFile`；`api` 扩展 4 个新方法；`listImages` 加 filter 参数 |
| `src/pages/MainPage.tsx` | 导入 3 个新页面组件；NAV_ITEMS 增加 3 项；pages 映射注册 3 个新页面 |
