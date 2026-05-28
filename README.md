# Easy Dataset Station

YOLO 数据集管理桌面工具 — 与 Easy Infer Station 同架构的系列工具之一。

## 功能

| 模块 | 功能 |
|---|---|
| 数据集质量检测 | 统计图片/标签/标注框数量，发现孤立文件、空标签、类别分布 |
| 数据集可视化 | 带标注框预览，支持过滤"已标注/未标注" |
| 格式转换 | LabelMe → YOLO、VOC → YOLO、YOLO → VOC、类别 ID 重映射 |
| 标签编辑 | 批量替换/删除类别 ID，多 ID 重排序 |
| 文件管理 | 一致性检查、删除空标签、创建空标签、批量重命名、修复损坏图片 |
| 数据集划分 | 按比例 train/val/test 随机划分，自动生成 data.yaml |

## 技术栈

- **桌面壳**：Tauri 2（Rust）
- **前端**：React 19 + TypeScript + Tailwind CSS v4 + Vite 7
- **后端**：Python Flask 3.0（运行在 conda 环境中）
- **端口**：后端 8081，Vite 开发服务器 1421

## 快速开始

### 前提条件

- [Node.js](https://nodejs.org/) 20+
- [Rust](https://rustup.rs/) 1.77+
- [Conda](https://docs.conda.io/) 并有包含 Flask 的 Python 环境

### 安装依赖

```bash
# 前端依赖
npm install

# Python 依赖（在你的 conda 环境中）
pip install -r requirements.txt
```

### 开发模式

```bash
npm run tauri dev
```

### 构建

```bash
npm run tauri build
```

## 目录结构

```
easy_dataset/
├── app.py               # Flask 入口
├── config.py            # 配置（端口、目录）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── routes/              # Flask Blueprint
├── services/            # 业务逻辑
│   ├── dataset_service.py
│   ├── convert_service.py
│   ├── label_service.py
│   ├── file_service.py
│   └── split_service.py
├── src/                 # React 前端
│   ├── pages/
│   │   ├── DatasetQuality.tsx
│   │   ├── DatasetViewer.tsx
│   │   ├── Converter.tsx
│   │   ├── LabelEditor.tsx
│   │   ├── FileManager.tsx
│   │   └── DatasetSplit.tsx
│   ├── components/
│   │   └── ResultBox.tsx
│   └── lib/
│       ├── store.ts        # Zustand 状态管理
│       └── tauri-bridge.ts # Tauri IPC + API 封装
├── src-tauri/           # Tauri Rust 壳
└── docs/
    └── PRD.md           # 产品需求文档
```

## 产品文档

详见 [docs/PRD.md](docs/PRD.md)

## License

MIT
