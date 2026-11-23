# 同类项目调研纪要（立项前置留痕）

> 调研日期：2026-11-23  
> 结论：**现有开源社区与市场产品契合度不足，建议自建**，同时吸收四个核心工程与建模思路。

## 1. 同类项目全景对比（元数据取自公开仓库与官网核验）

| 项目名称 | 类型与定位 | 规模 / 星数 | 许可协议 | 核心覆盖与粒度 |
| :--- | :--- | :--- | :--- | :--- |
| [Physics Derivation Graph (PDG)](https://allofphysics.com/) / [ui_v8](https://github.com/allofphysicsgraph/ui_v8_website_flask_neo4j) | 开源公式推导图谱 | 2 stars | CC BY 4.0 | 数学物理表达式 + 推理规则边（Neo4j + SymPy） |
| [cn-k12-math-knowledge-graph](https://github.com/haojing8312/cn-k12-math-knowledge-graph) | 中国 K12 数学先修图谱 | 68 stars | 代码 Apache-2.0；数据 CC BY-NC-SA 4.0 | 中国 1–9 年级 1,327 主题与 1,204 条先修边 |
| [Pkmer-Math](https://github.com/PKM-er/Pkmer-Math) | 中文 Obsidian 数学知识库 | 374 stars | 未声明许可协议 | 高等数学为主的双链笔记网络 |
| [Lean Blueprint](https://github.com/PatrickMassot/leanblueprint) | 形式化证明依赖蓝图 | 403 stars | Apache-2.0 | LaTeX 定理声明与 Lean 4 证明的 DAG |
| [Lean Atlas](https://github.com/NyxFoundation/lean-atlas) | 定理依赖交互浏览器 | 24 stars | MIT | Lean 4 多维筛选图谱与审阅裁剪算法 |
| [MathModDB](https://mardi4nfdi.github.io/MathModDB/) / [GitHub](https://github.com/MaRDI4NFDI/MathModDB) | 跨学科数学模型本体 | 7 stars | CC BY 4.0 | 1,200+ 应用数学模型、公式、物理量与量纲 |
| [Metamath Proof Explorer](https://us.metamath.org/mpeuni/mmset.html) | 形式化证明数据库 | 主库 26,000+ 条证明 | 开源公有领域/自由使用 | 从底层公理出发的完全形式化推导链 |
| [Wolfram MathWorld](https://mathworld.wolfram.com/) / [Mathigon](https://mathigon.org/) / [The Map of Mathematics](https://themapofmathematics.org/) | 商业/科普数学平台 | MathWorld 13,000 词条；Map 含 32 分支 | 闭源/版权保护 | 百科词条、交互课程或学科地图 |

## 2. 市场空白与自建依据

现有项目明显分化为两极：

1. **学术形式化与科研本体工具**（PDG、Lean Blueprint/Atlas、MathModDB、Metamath）强调机器校验与形式化严谨，学习门槛高，缺少面向学习者的“L1/L2/L3 分级详略推导”与中国中学教材体系。
2. **教育图谱与科普百科**（cn-k12-math-knowledge-graph、Pkmer-Math、MathWorld、Mathigon）侧重章节先修或词条阅读，粒度停留在知识点层面，未下沉到具体公式之间的推导步骤。

本项目定位于两者之间的空白区：以中国初高中数学公式切入，提供人类可读、按需切换详略、支持领域筛选且预留跨学科量纲接口的交互式推导图谱。

## 3. 可借鉴实践

1. **前端架构与边分类（借鉴 Lean Atlas）**：采用 `静态 JSON → React Flow + Dagre` 演进路线，区分定义级、推导级与应用级依赖，并提供局部子图聚焦裁剪。
2. **跨学科变量与量纲模型（借鉴 MathModDB）**：将变量拆分为符号、物理量种类（`quantity_kind`）、量纲（`dimension`）与国际单位制单位（`si_unit`）。
3. **推理规则与校验机制（借鉴 PDG 与 cn-k12-math-knowledge-graph）**：为每条推导标注原子推理规则，并建设离线 JSON Schema 校验、悬空引用检查与 SymPy 代数等价性校验脚本。

## 4. 开源合规红线

- **无许可协议仓库仅读思路**：[Pkmer-Math](https://github.com/PKM-er/Pkmer-Math) 未声明开源许可证，禁止复用其代码与文本内容。
- **非商业数据协议隔离**：[cn-k12-math-knowledge-graph](https://github.com/haojing8312/cn-k12-math-knowledge-graph) 的数据部分采用 CC BY-NC-SA 4.0（仅限非商业用途且须同协议共享），本项目所有初高中公式与推导数据均独立整理，不直接导入其数据集。
