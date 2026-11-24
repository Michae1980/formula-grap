# Formula Graph（公式知识图谱）

将数学及跨学科公式之间的推导、特例、等价与引用关系构建为结构化有向属性图，支持按 **学段 → 学科 → 分支 → 专题** 自顶向下级联筛选、动态生成专属视图，并在任意两个关联公式之间切换 **L1 摘要 / L2 标准 / L3 详细** 三级推导过程。

## 当前图谱规模（已通过自动校验）

- **初中跨学科底座（58 公式）**：电学与正反比例函数、代数与二次函数、力学与化学溶液定量
- **高中数学核心（45 公式）**：三角恒等变换与解三角形、指对数、基本不等式与导数微积分前置
- **大学及以后专题（18 公式）**：概率与统计学（古典概型、条件概率、贝叶斯公式、期望方差、二项/正态分布与中心极限定理）
- **全量总图**：121 公式 / 107 推导链（含 13 条跨批次/跨学段桥梁边），0 孤立节点，0 校验警告

## 目录结构

```text
formula-graph/
├── .github/workflows/deploy-pages.yml     # GitHub Pages 自动校验、构建与发布工作流
├── schema/
│   ├── formula-graph.v1.schema.json       # 公式图谱 JSON Schema（Draft 2020-12）
│   └── taxonomy.v1.json                   # 学段 → 学科 → 分支 → 专题多级分类树
├── data/
│   ├── cn-junior-high/                    # 初中三批原子数据包（58 公式）
│   ├── cn-senior-high/                    # 高中两批原子数据包（45 公式）
│   └── higher-ed/                         # 大学及以后专题包（概率与统计学 18 公式）
├── bundles/                               # 自动生成的统一总图包（103 / 121 公式）
├── scripts/
│   ├── validate.py                        # 零依赖数据包校验器（Schema / 悬空引用 / 连通性）
│   └── build_secondary_unified.py         # 统一总图打包 + PWA 静态站点构建脚本
├── prototype/                             # 模板、PWA 静态资源与本地离线入口
└── site/                                  # 可直接托管部署的静态网站 + PWA 输出目录
```

## 本地运行与构建

- **直接离线查看**：用任意现代浏览器打开 `prototype/index.html`（或 `site/index.html`）。
- **本地预览网站与 PWA 安装体验**（支持 Service Worker 离线缓存与 URL 分享）：
  ```bash
  python3 -m http.server -d site 8080
  ```
  浏览器打开 `http://localhost:8080`，点击顶部「安装桌面版」即可在 macOS 或 Windows 上安装为独立桌面应用。
- **新增公式后重新校验并构建**（仅需 Python 3.9+，零第三方依赖）：
  ```bash
  python3 scripts/validate.py && python3 scripts/build_secondary_unified.py
  ```

## 一键部署为公开网站（GitHub Pages）

1. 将本仓库推送至 GitHub 的 `main` 分支。
2. 在 GitHub 仓库打开 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
3. 之后每次向 `main` 分支推送代码，`.github/workflows/deploy-pages.yml` 会自动执行全量校验、重新构建 `site/` 并发布上线；访问该网址即可在 Mac、Windows 及移动端安装为离线可用的 PWA 桌面应用。
