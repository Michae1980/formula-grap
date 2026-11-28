# Formula Graph（数理知识图谱）

将初中、高中与大学跨学科数理知识对象（公式、公理、定义、定理、定律、分布、不等式）之间的推导、特例、等价、对偶与反例关系构建为结构化有向属性图，支持按 **阶段 → 学科 → 分支 → 专题** 自顶向下级联筛选，并在任意关联对象之间切换 **L1 摘要 / L2 标准 / L3 详细（含易错提醒）** 三级推导过程。

## 当前图谱规模（已通过自动校验）

- **初中跨学科底座（58 对象）**：电学与正反比例函数（18）、代数与二次函数（20）、力学与化学溶液定量（20）
- **高中数理核心（83 对象）**：三角函数与解三角形（25）、指对数不等式与导数前置（20）、数列向量与解析几何（18）、高中物理力学动量与电磁学（20）
- **大学核心（96 对象）**：高等微积分（20）、线性代数（20）、概率与统计学基础（18）、数理统计进阶（14）、概率与统计学经典分布与不等式扩展包（24）
- **全量总图**：**237 个广义知识对象 / 238 条推导链**，12 个原子数据包全部 0 错误 / 0 警告，**1 个全阶段单连通大图**，0 孤立节点

## 核心特性

- **代码与数据分离 + 离线 PWA**：前端页面 `index.html`（约 143.6 KB）与静态图谱数据 `data/graph-data.js`（约 507.7 KB）解耦，零跨域报错，支持双击 `file://` 直接打开及 PWA（`formula-graph-pwa-v2`）桌面/移动端离线安装。
- **三视角协同工作台**：支持 **「◎ 聚焦关联」**（默认 3 栏顶部对齐聚焦视图）、**「🌐 全局总览」** 与 **「📋 卡片目录」**（按课程体系序 / 关联热度 / 对象类型排序）无缝切换；右侧详情抽屉支持拖拽调宽与双击还原。
- **智能模糊搜索与简称联想**：支持多词空格 AND 匹配、40+ 数理化高频简称扩展（如 `clt`、`lln`、`mgf`、`ols`、`am-gm`、`牛二`、`牛莱`）与字符容错；聚焦模式下输入弹出 Top 8 联想下拉（支持 `↑↓`/`Enter`/`Esc`）直达目标而不打断当前画布。
- **关系过滤与浏览历史**：顶栏支持全局对象类型（`node_kind`）筛选，图谱图例胶囊可点击过滤关系边；右侧抽屉内置 `← 返回`（40 步栈）、`🕒 最近浏览`（15 项）与 `⇄ 查与上项路径`。
- **URL 参数直达（Deep Links）**：筛选维度、视图模式与当前焦点实时同步至 URL，可直接分享特定知识视图。

## 目录结构

```text
formula-graph/
├── .github/workflows/deploy-pages.yml     # GitHub Pages 自动构建、校验与发布工作流（Node 24）
├── schema/
│   ├── formula-graph.v1.schema.json       # 广义知识对象图谱 JSON Schema（Draft 2020-12）
│   └── taxonomy.v1.json                   # 阶段 → 学科 → 分支 → 专题多级分类树（v1.3.0）
├── data/
│   ├── cn-junior-high/                    # 初中三批原子数据包（58 对象）
│   ├── cn-senior-high/                    # 高中四批数理数据包（83 对象）
│   └── higher-ed/                         # 大学五批专题包（96 对象）
├── bundles/                               # 自动生成的统一总图包（master-graph-237.json）
├── scripts/
│   ├── validate.py                        # 零依赖数据包、连通性、产物与隐私全量校验器
│   └── build_secondary_unified.py         # 统一总图打包 + 数据剥离 + PWA 静态站点构建脚本
├── prototype/                             # 唯一前端模板 template.html、PWA 源码与本地离线入口
└── site/                                  # 可直接托管部署的纯静态网站 + PWA 输出目录
```

## 本地运行与构建

- **直接离线查看**：用任意现代浏览器打开 `site/index.html`（或 `prototype/index.html`）。
- **本地静态服务预览（体验 PWA 离线缓存与分享链接）**：
  ```bash
  python3 -m http.server -d ~/Documents/Workspace/Projects/formula-graph/site 8080
  ```
  浏览器打开 `http://localhost:8080`，点击顶部「安装桌面版」即可安装为独立应用。
- **修改模板或数据包后重建并校验**（仅需 Python 3.9+，零第三方依赖）：
  ```bash
  python3 scripts/build_secondary_unified.py && python3 scripts/validate.py
  ```

## 一键部署为公开网站（GitHub Pages）

1. 将本仓库推送至 GitHub 的 `main` 分支。
2. 在 GitHub 仓库打开 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
3. 每次向 `main` 分支推送代码，`.github/workflows/deploy-pages.yml` 会自动执行构建、全量校验并发布上线。
