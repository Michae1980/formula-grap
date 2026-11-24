#!/usr/bin/env python3
"""
构建中学全量跨学科总图（初中 58 + 高中 45 = 103 公式，合并为一个整体）并同步更新交互原型。
后续统计学、微积分、线性代数等高等专题可作为独立数据包接入同一原型切换器。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_unified as jh_builder  # 复用初中跨批次桥梁定义
import validate  # 复用零依赖校验器

# 初中 ↔ 高中 与 高中跨模块桥梁边（共 6 条）
SECONDARY_BRIDGES = [
    {
        "id": "deriv.bridge.perf_sq_to_am_gm",
        "from_formula_ids": ["math.alg.perfect_square_diff"],
        "to_formula_id": "math.alg.am_gm",
        "relation_type": "derives_to",
        "dependency_site": "proof_level",
        "inference_rules": ["nonnegativity_of_square", "algebraic_rearrangement"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "对两个正实数令 (√a - √b)² ≥ 0，用初中完全平方差公式展开移项即得高中基本不等式 (a+b)/2 ≥ √(ab)。",
            "L2_standard": [
                {"step": 1, "latex": "(\\sqrt{a} - \\sqrt{b})^2 = a - 2\\sqrt{ab} + b \\ge 0", "note": "a, b > 0，套用初中完全平方差公式展开且平方非负", "cited_formula_ids": ["math.alg.perfect_square_diff"]},
                {"step": 2, "latex": "a + b \\ge 2\\sqrt{ab} \\implies \\frac{a + b}{2} \\ge \\sqrt{ab}", "note": "移项并两边同除以 2，当且仅当 √a = √b 即 a = b 时取等", "cited_formula_ids": []}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "(\\sqrt{a} - \\sqrt{b})^2 \\ge 0\\quad (a > 0,\\ b > 0)", "note": "实数的平方恒大于等于 0", "cited_formula_ids": []},
                {"step": 2, "latex": "a - 2\\sqrt{ab} + b \\ge 0 \\implies \\frac{a+b}{2} \\ge \\sqrt{ab}", "note": "用完全平方差公式展开并移项整理，完成从初中代数到高中不等式的自然衔接", "cited_formula_ids": ["math.alg.perfect_square_diff"], "pitfall": "若 a, b 为负数，不能直接开根号，必须先确认“一正”条件。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.quad_ext_to_calc_ext",
        "from_formula_ids": ["math.func.quad_general", "math.calc.deriv_power", "math.calc.extremum_necessary"],
        "to_formula_id": "math.func.quad_extremum",
        "relation_type": "derives_to",
        "dependency_site": "proof_level",
        "inference_rules": ["differentiation", "solve_stationary_point"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "对二次函数一般式 y = ax² + bx + c 求导得 y' = 2ax + b，令导数为 0 立即解出对称轴 x = -b/(2a)。",
            "L2_standard": [
                {"step": 1, "latex": "y' = (ax^2 + bx + c)' = 2ax + b", "note": "用幂函数求导公式逐项求导", "cited_formula_ids": ["math.func.quad_general", "math.calc.deriv_power"]},
                {"step": 2, "latex": "2ax + b = 0 \\implies x = -\\frac{b}{2a},\\quad y_{\\text{极}} = \\frac{4ac - b^2}{4a}", "note": "令导数为 0 求唯一驻点并代回原式", "cited_formula_ids": ["math.calc.extremum_necessary"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "y' = 2ax + b = 0 \\implies x = -\\frac{b}{2a}", "note": "高中导数法比初中配方法更直接地给出极值点，并能无缝推广到三次及更高次多项式", "cited_formula_ids": ["math.func.quad_general", "math.calc.deriv_power", "math.calc.extremum_necessary"], "pitfall": "二阶导数 y'' = 2a 的符号直接对应开口方向与极大/极小值判定。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.ind_neg_to_odd_even",
        "from_formula_ids": ["math.trig.ind_neg"],
        "to_formula_id": "math.func.odd_even",
        "relation_type": "applies_in",
        "dependency_site": "definition_level",
        "inference_rules": ["canonical_example"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "诱导公式三 sin(-α) = -sin α、cos(-α) = cos α 正是奇函数与偶函数定义的典型三角函数实例。",
            "L2_standard": [
                {"step": 1, "latex": "\\sin(-x) = -\\sin x \\text{（奇函数）},\\quad \\cos(-x) = \\cos x \\text{（偶函数）}", "note": "三角函数定义域为 R（关于原点对称），直接满足奇偶性判定式", "cited_formula_ids": ["math.trig.ind_neg"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "\\sin(-x) = -\\sin x,\\quad \\cos(-x) = \\cos x", "note": "结合对称性可知 sin x 图像关于原点中心对称，cos x 图像关于 y 轴轴对称", "cited_formula_ids": ["math.trig.ind_neg"], "pitfall": "若三角函数定义域被截断为不对称区间（如 [0, π]），则不再具有奇偶性。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.sin_sum_to_deriv_trig",
        "from_formula_ids": ["math.trig.sin_sum", "math.calc.derivative_def"],
        "to_formula_id": "math.calc.deriv_trig",
        "relation_type": "derives_to",
        "dependency_site": "proof_level",
        "inference_rules": ["angle_sum_expansion", "important_limit"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "在正弦导数定义中用两角和正弦公式展开 sin(x+Δx)，再代入极限 lim(sin Δx)/Δx = 1 与 lim(cos Δx - 1)/Δx = 0 得 cos x。",
            "L2_standard": [
                {"step": 1, "latex": "\\frac{\\sin(x+\\Delta x)-\\sin x}{\\Delta x} = \\sin x\\frac{\\cos\\Delta x - 1}{\\Delta x} + \\cos x\\frac{\\sin\\Delta x}{\\Delta x}", "note": "用两角和正弦公式展开分子并分组", "cited_formula_ids": ["math.trig.sin_sum", "math.calc.derivative_def"]},
                {"step": 2, "latex": "\\xrightarrow{\\Delta x \\to 0} \\sin x \\cdot 0 + \\cos x \\cdot 1 = \\cos x", "note": "取极限即证 (sin x)' = cos x", "cited_formula_ids": []}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "\\sin(x+\\Delta x) = \\sin x\\cos\\Delta x + \\cos x\\sin\\Delta x", "note": "此步是三角恒等变换向微积分输送的核心桥梁", "cited_formula_ids": ["math.trig.sin_sum", "math.calc.derivative_def"]},
                {"step": 2, "latex": "(\\sin x)' = \\cos x", "note": "同理用两角和余弦公式展开 cos(x+Δx) 可证 (cos x)' = -sin x", "cited_formula_ids": [], "pitfall": "上述两个极限仅在自变量为弧度制时成立，角度制会多出因子 π/180。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.velocity_to_deriv_def",
        "from_formula_ids": ["physics.mech.velocity"],
        "to_formula_id": "math.calc.derivative_def",
        "relation_type": "generalizes",
        "dependency_site": "application_level",
        "inference_rules": ["limit_generalization"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "初中物理平均速度 v = Δs/Δt 在时间间隔 Δt → 0 时的极限，即为高中导数定义的瞬时速度 v(t) = s'(t)。",
            "L2_standard": [
                {"step": 1, "latex": "\\bar{v} = \\frac{\\Delta s}{\\Delta t} \\xrightarrow{\\Delta t \\to 0} v(t_0) = \\lim_{\\Delta t \\to 0}\\frac{s(t_0+\\Delta t) - s(t_0)}{\\Delta t} = s'(t_0)", "note": "由平均变化率取极限推广为瞬时变化率（导数）", "cited_formula_ids": ["physics.mech.velocity"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "v(t) = s'(t),\\quad a(t) = v'(t) = s''(t)", "note": "位移对时间求一阶导得瞬时速度，求二阶导得瞬时加速度，构筑微积分与物理运动学的统一底座", "cited_formula_ids": ["physics.mech.velocity"], "pitfall": "平均速度只依赖初末位置与总时间，瞬时速度则由该时刻切线斜率决定。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.power_red_to_deriv_trig",
        "from_formula_ids": ["math.trig.power_reduction_cos", "math.trig.power_reduction_sin"],
        "to_formula_id": "math.calc.deriv_trig",
        "relation_type": "simplifies",
        "dependency_site": "application_level",
        "inference_rules": ["power_reduction_linearization"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "降幂公式把 sin²x 与 cos²x 化为一次函数 (1 ∓ cos 2x)/2，在微积分求高阶导数与不定积分中大幅简化运算。",
            "L2_standard": [
                {"step": 1, "latex": "\\cos^2 x = \\frac{1 + \\cos 2x}{2},\\quad \\sin^2 x = \\frac{1 - \\cos 2x}{2}", "note": "将二次三角幂线性化为一次余弦，直接对接基本三角求导与积分公式", "cited_formula_ids": ["math.trig.power_reduction_cos", "math.trig.power_reduction_sin"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "(\\sin^2 x)' = \\left(\\frac{1 - \\cos 2x}{2}\\right)' = \\sin 2x", "note": "既验证了链式法则 (sin²x)' = 2sin x cos x = sin 2x，也是大学微积分 ∫sin²x dx 的标准起手式", "cited_formula_ids": ["math.trig.power_reduction_cos", "math.trig.power_reduction_sin"], "pitfall": "降幂同时伴随“角加倍”，求导或积分时别忘处理内层系数 2。"}
            ]
        }
    }
]

# 13 列统一泳道（前 8 列初中 58 公式 + 后 5 列高中 45 公式 = 103 公式）
SECONDARY_COLUMNS = jh_builder.UNIFIED_COLUMNS + [
    ("9. 三角基础与诱导", [
        "math.trig.unit_circle_def", "math.trig.pythagorean", "math.trig.quotient",
        "math.trig.sec_tan_pythagorean", "math.trig.ind_neg", "math.trig.ind_pi_minus",
        "math.trig.ind_half_pi_minus", "math.trig.ind_half_pi_plus"
    ]),
    ("10. 三角和差角", [
        "math.trig.cos_diff", "math.trig.cos_sum", "math.trig.sin_sum",
        "math.trig.sin_diff", "math.trig.tan_sum", "math.trig.tan_diff",
        "math.trig.auxiliary_angle"
    ]),
    ("11. 倍角降幂与解三角", [
        "math.trig.sin_double", "math.trig.cos_double", "math.trig.cos_double_cos",
        "math.trig.cos_double_sin", "math.trig.tan_double", "math.trig.power_reduction_cos",
        "math.trig.power_reduction_sin", "math.trig.law_of_cosines",
        "math.trig.triangle_area", "math.trig.law_of_sines"
    ]),
    ("12. 指对数与不等式", [
        "math.func.exp_rules", "math.func.log_def", "math.func.log_rules",
        "math.func.log_change_base", "math.alg.am_gm", "math.alg.qm_am_gm_hm",
        "math.func.odd_even", "math.func.periodicity"
    ]),
    ("13. 高中导数与微积分前置", [
        "math.calc.derivative_def", "math.calc.deriv_power", "math.calc.deriv_exp_log",
        "math.calc.deriv_trig", "math.calc.deriv_linear", "math.calc.deriv_product",
        "math.calc.deriv_quotient", "math.calc.chain_rule", "math.calc.tangent_line",
        "math.calc.monotonicity", "math.calc.extremum_necessary", "math.calc.deriv_general_exp_log"
    ]),
]

# 高等专题 · 概率与统计学（5 列 18 公式）
STAT_COLUMNS = [
    ("1. 概率公理与条件概率", [
        "stat.prob.classical", "stat.prob.addition",
        "stat.prob.conditional", "stat.prob.multiplication"
    ]),
    ("2. 独立性与贝叶斯推断", [
        "stat.prob.independence", "stat.prob.total_probability",
        "stat.prob.bayes"
    ]),
    ("3. 期望与方差体系", [
        "stat.rv.expectation_discrete", "stat.rv.expectation_linear",
        "stat.rv.variance_def", "stat.rv.variance_props"
    ]),
    ("4. 协方差与二项分布", [
        "stat.rv.covariance", "stat.rv.correlation",
        "stat.dist.binomial", "stat.dist.binomial_moments"
    ]),
    ("5. 正态分布与极限定理", [
        "stat.dist.normal_pdf", "stat.dist.standardization",
        "stat.inf.clt"
    ]),
]


def build_positions_from_cols(columns, row_gap=122):
    positions = {}
    lanes = []
    col_x = 24
    max_rows = 0
    for label, ids in columns:
        lanes.append({"x": col_x, "label": label})
        max_rows = max(max_rows, len(ids))
        for r, fid in enumerate(ids):
            positions[fid] = {"x": col_x, "y": 48 + r * row_gap}
        col_x += 268
    stage_w = col_x + 20
    stage_h = 48 + max_rows * row_gap + 40
    return positions, lanes, stage_w, stage_h


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"
    bundles_dir = repo_root / "bundles"
    bundles_dir.mkdir(exist_ok=True)

    atomic_files = [
        data_dir / "cn-junior-high" / "electricity-math-batch1.json",
        data_dir / "cn-junior-high" / "algebra-quadratic-batch2.json",
        data_dir / "cn-junior-high" / "mechanics-chemistry-batch3.json",
        data_dir / "cn-senior-high" / "trig-seed-25.json",
        data_dir / "cn-senior-high" / "functions-calculus-batch2.json",
    ]

    all_formulas, all_derivations = [], []
    seen_f, seen_d = set(), set()

    for pf in atomic_files:
        pack = json.loads(pf.read_text(encoding="utf-8"))
        for f in pack["formulas"]:
            if f["id"] not in seen_f:
                seen_f.add(f["id"])
                all_formulas.append(f)
        for d in pack["derivations"]:
            if d["id"] not in seen_d:
                seen_d.add(d["id"])
                all_derivations.append(d)

    for b in jh_builder.CROSS_BATCH_BRIDGES + SECONDARY_BRIDGES:
        assert b["id"] not in seen_d, f"Duplicate bridge ID: {b['id']}"
        seen_d.add(b["id"])
        all_derivations.append(b)

    secondary_unified = {
        "schema_version": "1.0.0",
        "metadata": {
            "pack_id": "cn-secondary-unified-103",
            "title": "中学全量跨学科总图（初中 + 高中 · 103 公式）",
            "curriculum_ref": "中国中学阶段（初中 + 高中）数学、物理与化学核心公式统一图谱",
            "updated_at": "2026-11-23",
        },
        "formulas": all_formulas,
        "derivations": all_derivations,
    }

    out_bundle = bundles_dir / "secondary-unified-103.json"
    out_bundle.write_text(json.dumps(secondary_unified, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errs, warns, summary = validate.validate_pack(out_bundle, None, None)
    if errs:
        print("中学总图校验失败:", errs)
        return 1
    print(
        f"[PASS] bundles/secondary-unified-103.json | "
        f"公式 {summary['formula_count']} 个 · "
        f"推导 {summary['derivation_count']} 条（含 13 条跨批次/跨学段桥梁）· "
        f"连通分量 {summary['connected_components']} · "
        f"孤立节点 {summary['isolated_count']} · 警告 {len(warns)}"
    )

    sec_pos, sec_lanes, sec_w, sec_h = build_positions_from_cols(SECONDARY_COLUMNS)
    assert set(sec_pos.keys()) == seen_f, f"坐标缺失或多余: {set(sec_pos.keys()) ^ seen_f}"

    # 准备所有可选数据包（默认中学统一总图，保留单专题包方便聚焦查看，后续可直接追加统计学/微积分包）
    jh_bundle = json.loads((bundles_dir / "junior-high-unified-58.json").read_text(encoding="utf-8"))
    jh_pos, jh_lanes, jh_w, jh_h = build_positions_from_cols(jh_builder.UNIFIED_COLUMNS, row_gap=126)

    stat_data = json.loads((data_dir / "higher-ed" / "probability-statistics-18.json").read_text(encoding="utf-8"))

    # 合并全量总图（中学 103 + 大学及以后 18 = 121 公式），供原型按 学段 → 学科 → 分支 → 专题 动态生成视图
    master_formulas = list(all_formulas)
    master_derivations = list(all_derivations)
    master_seen_f = set(seen_f)
    master_seen_d = set(seen_d)
    for f in stat_data["formulas"]:
        if f["id"] not in master_seen_f:
            master_seen_f.add(f["id"])
            master_formulas.append(f)
    for d in stat_data["derivations"]:
        if d["id"] not in master_seen_d:
            master_seen_d.add(d["id"])
            master_derivations.append(d)

    master_graph = {
        "schema_version": "1.0.0",
        "metadata": {
            "pack_id": "formula-graph-master-121",
            "title": "公式知识图谱全量底座（初中 + 高中 + 大学及以后）",
            "curriculum_ref": "全学段跨学科统一公式知识图谱（支持动态视图生成）",
            "updated_at": "2026-11-23",
        },
        "formulas": master_formulas,
        "derivations": master_derivations,
    }
    master_bundle = bundles_dir / "master-graph-121.json"
    master_bundle.write_text(json.dumps(master_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    m_errs, m_warns, m_summary = validate.validate_pack(master_bundle, None, None)
    if m_errs:
        print("全量总图校验失败:", m_errs)
        return 1
    print(
        f"[PASS] bundles/master-graph-121.json | "
        f"公式 {m_summary['formula_count']} 个 · "
        f"推导 {m_summary['derivation_count']} 条 · "
        f"连通分量 {m_summary['connected_components']} · "
        f"孤立节点 {m_summary['isolated_count']} · 警告 {len(m_warns)}"
    )

    taxonomy_path = repo_root / "schema" / "taxonomy.v1.json"
    taxonomy_obj = json.loads(taxonomy_path.read_text(encoding="utf-8"))

    raw_map = set()
    for disc in taxonomy_obj["disciplines"]:
        for br in disc["branches"]:
            for tp in br["topics"]:
                for rt in tp.get("raw_topics", [tp["id"]]):
                    raw_map.add(rt)
    unmapped = [f["id"] for f in master_formulas if not any(t in raw_map for t in f["taxonomy"]["topics"])]
    assert not unmapped, f"存在未归入分类树的公式: {unmapped}"

    tpl_path = repo_root / "prototype" / "template.html"
    html_path = repo_root / "prototype" / "index.html"
    tpl = tpl_path.read_text(encoding="utf-8")
    assert "/*__TAXONOMY_PAYLOAD__*/" in tpl and "/*__MASTER_GRAPH_PAYLOAD__*/" in tpl
    rendered = tpl.replace("/*__TAXONOMY_PAYLOAD__*/", json.dumps(taxonomy_obj, ensure_ascii=False, indent=2), 1)
    rendered = rendered.replace("/*__MASTER_GRAPH_PAYLOAD__*/", json.dumps(master_graph, ensure_ascii=False, indent=2), 1)
    html_path.write_text(rendered, encoding="utf-8")
    print(f"OK: {len(master_formulas)} 公式全部完成多级分类映射，已生成动态视图原型 prototype/index.html。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
