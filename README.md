# Formula Graph（数理知识图谱）

将初中、高中与大学跨学科数理知识对象（公式、公理、定义、定理、定律、分布、不等式）之间的推导、特例、等价、对偶与反例关系构建为结构化有向属性图，支持按 **阶段 → 学科 → 分支 → 专题** 自顶向下级联筛选，并在任意关联对象之间切换 **L1 摘要 / L2 标准 / L3 详细（含易错提醒）** 三级推导过程。

> 站点内容持续扩充，实时收录规模与连通状态请以页面顶栏展示为准。

## 涵盖范围

- **初中跨学科底座**：电学与正反比例函数、代数与二次函数、力学与化学溶液定量
- **高中数理核心**：三角函数与解三角形、指对数不等式与导数前置、数列向量与解析几何、高中物理力学动量与电磁学
- **大学核心**：高等微积分、线性代数、概率论与数理统计（含经典分布、不等式、对偶与反例边界）

## 核心特性

- **代码与数据分离 + 离线 PWA**：前端页面 `index.html` 与静态图谱数据 `data/graph-data.js` 解耦，零跨域报错，支持双击 `file://` 直接打开及 PWA 桌面/移动端离线安装。
- **三视角协同工作台**：支持 **「◎ 聚焦关联」**（左前置依赖 → 中当前聚焦 → 右直接衍生/反例，并将等价与对偶关系置于聚焦卡正下方以双向虚线连接）、**「🌐 全局总览」** 与 **「📋 卡片目录」**（按课程体系序 / 关联热度 / 对象类型排序）无缝切换；右侧详情抽屉支持拖拽调宽与双击还原。
- **智能模糊搜索与简称联想**：支持多词空格 AND 匹配、高频数理化简称扩展（如 `clt`、`lln`、`mgf`、`ols`、`am-gm`、`牛二`、`牛莱`）与字符容错；聚焦模式下输入弹出联想下拉（支持 `↑↓`/`Enter`/`Esc`）直达目标而不打断当前画布。
- **关系过滤与浏览历史**：顶栏支持全局对象类型（`node_kind`）筛选，图谱图例胶囊可点击过滤关系边；右侧抽屉内置返回栈、最近浏览列表与两两推导路径查询。
- **URL 参数直达（Deep Links）**：筛选维度、视图模式与当前焦点实时同步至 URL，可直接分享特定知识视图。

## 目录结构

```text
formula-graph/
├── .github/workflows/deploy-pages.yml     # GitHub Pages 自动构建、校验与发布工作流（Node 24）
├── schema/
│   ├── formula-graph.v1.schema.json       # 广义知识对象图谱 JSON Schema（Draft 2020-12）
│   └── taxonomy.v1.json                   # 阶段 → 学科 → 分支 → 专题多级分类树
├── data/
│   ├── cn-junior-high/                    # 初中原子数据包
│   ├── cn-senior-high/                    # 高中数理数据包
│   └── higher-ed/                         # 大学专题数据包
├── bundles/                               # 自动生成的统一总图包
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
