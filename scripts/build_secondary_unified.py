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
    calc_he_data = json.loads((data_dir / "higher-ed" / "calculus-core-20.json").read_text(encoding="utf-8"))
    linalg_data = json.loads((data_dir / "higher-ed" / "linear-algebra-core-20.json").read_text(encoding="utf-8"))
    sh_seq_geo_data = json.loads((data_dir / "cn-senior-high" / "sequences-geometry-batch3.json").read_text(encoding="utf-8"))
    sh_phys_data = json.loads((data_dir / "cn-senior-high" / "physics-mech-em-batch4.json").read_text(encoding="utf-8"))
    stat_adv_data = json.loads((data_dir / "higher-ed" / "math-stats-advanced-14.json").read_text(encoding="utf-8"))
    prob_ext_data = json.loads((data_dir / "higher-ed" / "prob-stats-distributions-inequalities-24.json").read_text(encoding="utf-8"))

    # 跨学段与跨分支桥梁边：打通初中 ↔ 高中数理 ↔ 大学微积分/线代/概率与统计（全库 237 对象单连通大图）
    higher_ed_bridges = [
        {
            "id": "deriv.bridge.deriv_def_to_diff",
            "from_formula_ids": ["math.calc.derivative_def"],
            "to_formula_id": "calc.diff.differential",
            "relation_type": "generalizes",
            "dependency_site": "definition_level",
            "inference_rules": ["linear_principal_part"],
            "bidirectional": True,
            "levels": {
                "L1_summary": "由高中导数定义 lim(Δy/Δx) = f'(x) 展开余项得 Δy = f'(x)Δx + o(Δx)，提取线性主部即为大学微分 dy = f'(x)dx。",
                "L2_standard": [
                    {"step": 1, "latex": "\\frac{\\Delta y}{\\Delta x} = f'(x) + \\alpha(\\Delta x)\\ (\\alpha \\to 0) \\implies \\Delta y = f'(x)\\Delta x + o(\\Delta x)", "note": "将导数极限写成增量与高阶无穷小之和", "cited_formula_ids": ["math.calc.derivative_def"]},
                    {"step": 2, "latex": "dy = f'(x)\\,dx", "note": "主部 f'(x)dx 即为函数的一阶微分", "cited_formula_ids": []}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "dy = f'(x)\\,dx", "note": "完成从高中导数概念向大学微分与积分微元法的平滑衔接", "cited_formula_ids": ["math.calc.derivative_def"], "pitfall": "一元函数中可导与可微等价，但升维到多元函数后可微严格强于偏导数存在。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.prod_rule_to_parts",
            "from_formula_ids": ["math.calc.deriv_product"],
            "to_formula_id": "calc.int.by_parts",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["product_rule_inverse"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "对高中乘积求导公式 (uv)' = u'v + uv' 两边同时积分并移项，即得大学分部积分法 ∫u dv = uv - ∫v du。",
                "L2_standard": [
                    {"step": 1, "latex": "(uv)' = u'v + uv' \\implies \\int uv'\\,dx = uv - \\int u'v\\,dx", "note": "两边同时取不定积分并移项", "cited_formula_ids": ["math.calc.deriv_product"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\int u\\,dv = uv - \\int v\\,du", "note": "高中乘积求导法则的直接逆运算", "cited_formula_ids": ["math.calc.deriv_product"], "pitfall": "选 u 时优先把求导后更简单的对数、反三角或幂函数放在 u 位置。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.chain_rule_to_sub",
            "from_formula_ids": ["math.calc.chain_rule"],
            "to_formula_id": "calc.int.substitution",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["chain_rule_inverse"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "对高中复合函数链式法则 [F(φ(t))]' = f(φ(t))φ'(t) 两边积分，即得大学换元积分法。",
                "L2_standard": [
                    {"step": 1, "latex": "\\frac{d}{dt} F(\\varphi(t)) = f(\\varphi(t))\\varphi'(t) \\implies \\int f(\\varphi(t))\\varphi'(t)\\,dt = F(\\varphi(t)) + C = \\int f(u)\\,du", "note": "逆用链式法则令 u = φ(t) 化简积分", "cited_formula_ids": ["math.calc.chain_rule"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\int f(\\varphi(t))\\varphi'(t)\\,dt = \\int f(u)\\,du", "note": "链式求导与换元积分是一对互逆核心工具", "cited_formula_ids": ["math.calc.chain_rule"], "pitfall": "定积分换元时务必同步替换上下限。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.improper_to_normal",
            "from_formula_ids": ["calc.int.improper", "calc.int.newton_leibniz"],
            "to_formula_id": "stat.dist.normal_pdf",
            "relation_type": "applies_in",
            "dependency_site": "application_level",
            "inference_rules": ["gaussian_integral_normalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "正态分布密度函数前面的常数 1/(√(2π)σ) 正是由无穷区间广义积分 ∫_{-∞}^{+∞} e^{-t²/2} dt = √(2π) 归一性确定的。",
                "L2_standard": [
                    {"step": 1, "latex": "\\int_{-\\infty}^{+\\infty} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}\\,dx = \\sqrt{2\\pi}\\sigma", "note": "利用高斯广义积分算出曲线下总面积", "cited_formula_ids": ["calc.int.improper"]},
                    {"step": 2, "latex": "\\int_{-\\infty}^{+\\infty} \\frac{1}{\\sqrt{2\\pi}\\sigma} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}\\,dx = 1", "note": "除以 √(2π)σ 满足连续型概率密度总概率为 1 的公理", "cited_formula_ids": ["calc.int.newton_leibniz"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(a \\le X \\le b) = \\int_a^b f(x)\\,dx", "note": "广义积分与定积分是整个连续型概率统计（期望、方差、分布函数）的微积分底座", "cited_formula_ids": ["calc.int.improper", "calc.int.newton_leibniz"], "pitfall": "正态密度函数没有初等原函数，故有限区间概率需标准化后查 Φ(z) 表或数值积分。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.dot_to_gradient",
            "from_formula_ids": ["linalg.vec.dot_product"],
            "to_formula_id": "calc.multi.gradient",
            "relation_type": "applies_in",
            "dependency_site": "application_level",
            "inference_rules": ["directional_derivative_inner_product"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "方向导数 ∂f/∂e = ∇f · e = ‖∇f‖ cos θ 正是向量内积公式在多元微积分中的直接应用，由此立得沿梯度方向上升最快。",
                "L2_standard": [
                    {"step": 1, "latex": "\\frac{\\partial f}{\\partial \\mathbf{e}} = \\nabla f \\cdot \\mathbf{e} = \\|\\nabla f\\| \\cdot 1 \\cdot \\cos\\theta", "note": "套用向量内积几何形式，当 θ = 0 时取最大值 ‖∇f‖", "cited_formula_ids": ["linalg.vec.dot_product"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\nabla f \\cdot \\mathbf{e} = \\|\\nabla f\\|\\cos\\theta", "note": "连接线性代数内积空间与多元微积分梯度下降优化的关键跨分支桥梁", "cited_formula_ids": ["linalg.vec.dot_product"], "pitfall": "方向向量 e 必须是单位向量（‖e‖ = 1），否则算出的不是标准方向导数。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.cs_to_corr",
            "from_formula_ids": ["linalg.vec.cauchy_schwarz"],
            "to_formula_id": "stat.rv.correlation",
            "relation_type": "applies_in",
            "dependency_site": "proof_level",
            "inference_rules": ["random_variable_inner_product"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "将中心化随机变量 X-μX 与 Y-μY 视为内积空间中的向量（内积为协方差），柯西-施瓦茨不等式直接保证 |ρ_XY| ≤ 1。",
                "L2_standard": [
                    {"step": 1, "latex": "|\\text{Cov}(X, Y)| = |E[(X-\\mu_X)(Y-\\mu_Y)]| \\le \\sqrt{D(X)}\\sqrt{D(Y)}", "note": "对中心化随机变量应用柯西-施瓦茨不等式", "cited_formula_ids": ["linalg.vec.cauchy_schwarz"]},
                    {"step": 2, "latex": "|\\rho_{XY}| = \\frac{|\\text{Cov}(X,Y)|}{\\sqrt{D(X)}\\sqrt{D(Y)}} \\le 1", "note": "两端除以标准差乘积即证相关系数有界性", "cited_formula_ids": []}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\rho_{XY} = \\cos\\theta \\in [-1, 1]", "note": "从几何视角看，皮尔逊相关系数正是两个去均值样本向量之间的余弦相似度", "cited_formula_ids": ["linalg.vec.cauchy_schwarz"], "pitfall": "正交（不相关）仅表示夹角 90°（线性无关），不等价于统计独立。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.binom_to_binom_dist",
            "from_formula_ids": ["math.alg.binomial_theorem"],
            "to_formula_id": "stat.dist.binomial",
            "relation_type": "applies_in",
            "dependency_site": "proof_level",
            "inference_rules": ["binomial_normalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在高中二项式定理中令 a = 1 - p、b = p，展开式每一项恰好就是二项分布概率律，且总和 (1-p+p)^n = 1 自动归一。",
                "L2_standard": [
                    {"step": 1, "latex": "1 = [p + (1-p)]^n = \\sum_{k=0}^{n} \\binom{n}{k} p^k (1-p)^{n-k} = \\sum_{k=0}^{n} P(X=k)", "note": "二项式展开通项直接对应二项分布概率律", "cited_formula_ids": ["math.alg.binomial_theorem"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(X = k) = \\binom{n}{k} p^k (1-p)^{n-k}", "note": "这也是概率论中将其命名为“二项分布”的直接由来", "cited_formula_ids": ["math.alg.binomial_theorem"], "pitfall": "二项式定理中 a、b 可为任意实数，而二项分布要求 p ∈ (0, 1) 且两项和为 1。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.vec2d_to_vecnd",
            "from_formula_ids": ["math.geo.vec_dot_2d"],
            "to_formula_id": "linalg.vec.dot_product",
            "relation_type": "generalizes",
            "dependency_site": "definition_level",
            "inference_rules": ["dimensional_generalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "将高中二维平面向量数量积 x1 x2 + y1 y2 自然推广到 n 维欧氏空间，即得大学线性代数内积公式 ∑ u_i v_i。",
                "L2_standard": [
                    {"step": 1, "latex": "x_1 x_2 + y_1 y_2 \\xrightarrow{\\mathbb{R}^2 \\to \\mathbb{R}^n} \\mathbf{u}\\cdot\\mathbf{v} = \\sum_{i=1}^{n} u_i v_i", "note": "从二维坐标点乘推广为 n 维向量内积", "cited_formula_ids": ["math.geo.vec_dot_2d"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\mathbf{u}\\cdot\\mathbf{v} = \\sum_{i=1}^{n} u_i v_i", "note": "进一步抽象公理化后可推广到函数空间内积 ⟨f, g⟩ = ∫ f(x)g(x) dx（傅里叶分析基础）", "cited_formula_ids": ["math.geo.vec_dot_2d"], "pitfall": "高维空间无法直观画图，夹角与正交必须严格依赖代数内积公式判定。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.jh_vel_to_sh_kin",
            "from_formula_ids": ["physics.mech.velocity"],
            "to_formula_id": "physics.kin.vel_time",
            "relation_type": "generalizes",
            "dependency_site": "definition_level",
            "inference_rules": ["constant_acceleration_generalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "初中匀速直线运动 v = s/t 是加速度 a = 0 时的特例；引入恒定加速度 a = Δv/Δt 后推广为高中匀变速公式 v = v0 + at。",
                "L2_standard": [
                    {"step": 1, "latex": "a = \\frac{v - v_0}{t} \\implies v = v_0 + a t", "note": "将匀速推广为匀变速直线运动", "cited_formula_ids": ["physics.mech.velocity"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "v = v_0 + at,\\quad x = v_0 t + \\frac{1}{2}at^2", "note": "当 a = 0 时精确退化回初中匀速公式 x = v0 t", "cited_formula_ids": ["physics.mech.velocity"], "pitfall": "高中运动学中的位移 x 与速度 v 均为矢量，必须带正负号运算。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.jh_ohm_to_closed_ohm",
            "from_formula_ids": ["physics.elec.ohms_law"],
            "to_formula_id": "physics.em.closed_ohm",
            "relation_type": "generalizes",
            "dependency_site": "proof_level",
            "inference_rules": ["internal_resistance_generalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "初中部分电路欧姆定律 I = U/R 忽略了电源内阻；高中把电源内阻 r 串联计入总电阻后推广为闭合电路欧姆定律 I = E/(R+r)。",
                "L2_standard": [
                    {"step": 1, "latex": "E = U_{\\text{外}} + U_{\\text{内}} = I R + I r \\implies I = \\frac{E}{R + r}", "note": "对内外电路分别应用部分电路欧姆定律并相加", "cited_formula_ids": ["physics.elec.ohms_law"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "I = \\frac{E}{R + r}", "note": "当电源为理想电源（内阻 r = 0）时即退化回初中欧姆定律 I = E/R", "cited_formula_ids": ["physics.elec.ohms_law"], "pitfall": "外电路电阻 R 增大时，总电流 I 减小，内电压 Ir 减小，故路端电压 U = E - Ir 反而增大。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.clt_to_ciz",
            "from_formula_ids": ["stat.inf.clt"],
            "to_formula_id": "stat.est.ci_z",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["asymptotic_pivotal_inversion"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "中心极限定理给出 (X̄ - μ)/(σ/√n) 渐近服从 N(0, 1)，取 1-α 双侧分位点反解 μ 即直接得到总体均值 Z 置信区间。",
                "L2_standard": [
                    {"step": 1, "latex": "P\\left(-z_{\\alpha/2} \\le \\frac{\\bar{X} - \\mu}{\\sigma/\\sqrt{n}} \\le z_{\\alpha/2}\\right) \\approx 1 - \\alpha \\implies \\bar{X} \\pm z_{\\alpha/2}\\frac{\\sigma}{\\sqrt{n}}", "note": "以中心极限定理标准化量为枢轴反解 μ", "cited_formula_ids": ["stat.inf.clt"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\bar{X} \\pm z_{\\alpha/2}\\frac{\\sigma}{\\sqrt{n}}", "note": "中心极限定理把大样本下任意分布的均值推断统一归约到标准正态查表", "cited_formula_ids": ["stat.inf.clt"], "pitfall": "小样本且总体严重偏态时，直接套用 CLT 置信区间覆盖率会偏离名义水平 1 - α。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.normal_eq_to_ols1d",
            "from_formula_ids": ["linalg.mat.normal_eq"],
            "to_formula_id": "stat.reg.ols_1d",
            "relation_type": "special_case_of",
            "dependency_site": "proof_level",
            "inference_rules": ["two_by_two_matrix_inversion"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在最小二乘正规方程 (A^T A)β̂ = A^T y 中取设计矩阵 A = [1, x]（两列），求 2×2 矩阵逆即直接得到一元线性回归斜率与截距公式。",
                "L2_standard": [
                    {"step": 1, "latex": "A^\\top A = \\begin{pmatrix} n & \\sum x_i \\\\ \\sum x_i & \\sum x_i^2 \\end{pmatrix},\\quad A^\\top \\mathbf{y} = \\begin{pmatrix} \\sum y_i \\\\ \\sum x_i y_i \\end{pmatrix}", "note": "代入带截距项的二维设计矩阵 A", "cited_formula_ids": ["linalg.mat.normal_eq"]},
                    {"step": 2, "latex": "\\hat{\\beta}_1 = \\frac{\\sum (x_i - \\bar{x})(y_i - \\bar{y})}{\\sum (x_i - \\bar{x})^2},\\quad \\hat{\\beta}_0 = \\bar{y} - \\hat{\\beta}_1 \\bar{x}", "note": "解 2×2 线性方程组即得一元 OLS 公式", "cited_formula_ids": []}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\hat{\\boldsymbol{\\beta}} = (X^\\top X)^{-1} X^\\top \\mathbf{y}", "note": "打通线性代数空间投影与统计学回归分析的核心跨分支桥梁", "cited_formula_ids": ["linalg.mat.normal_eq"], "pitfall": "若多个自变量存在完全多重共线性，X^T X 奇异不可逆。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.bayes_to_bayesconj",
            "from_formula_ids": ["stat.prob.bayes", "stat.dist.normal_pdf"],
            "to_formula_id": "stat.est.bayes_conj",
            "relation_type": "generalizes",
            "dependency_site": "proof_level",
            "inference_rules": ["continuous_bayes_conjugacy"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "将离散贝叶斯公式推广为连续密度形式 p(μ|x) ∝ p(μ)p(x|μ)，代入正态先验与正态似然密度即得精度加权后验均值。",
                "L2_standard": [
                    {"step": 1, "latex": "p(\\mu \\mid x) = \\frac{p(\\mu) p(x \\mid \\mu)}{\\int p(\\mu) p(x \\mid \\mu)\\,d\\mu} \\propto \\exp\\left(-\\frac{(\\mu-\\mu_0)^2}{2\\sigma_0^2} - \\frac{n(\\bar{x}-\\mu)^2}{2\\sigma^2}\\right)", "note": "将正态密度代入连续型贝叶斯公式", "cited_formula_ids": ["stat.prob.bayes", "stat.dist.normal_pdf"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\mu_{\\text{post}} = \\frac{\\mu_0/\\sigma_0^2 + n\\bar{x}/\\sigma^2}{1/\\sigma_0^2 + n/\\sigma^2}", "note": "共轭先验使后验分布与先验属于同一分布族，无需数值积分即可给出闭式解析更新", "cited_formula_ids": ["stat.prob.bayes", "stat.dist.normal_pdf"], "pitfall": "分母是精度之和而非方差之和，方差越小的信息源（越确定）权重越大。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.kolmogorov_to_classical",
            "from_formula_ids": ["stat.prob.kolmogorov_axioms"],
            "to_formula_id": "stat.prob.classical",
            "relation_type": "special_case_of",
            "dependency_site": "definition_level",
            "inference_rules": ["finite_equiprobable_specialization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在柯尔莫哥洛夫公理中取有限样本空间 Ω（|Ω|=n）且各基本事件等可能 P(ω_i)=1/n，即退化为古典概型 P(A)=m/n。",
                "L2_standard": [
                    {"step": 1, "latex": "P(\\Omega) = \\sum_{i=1}^n P(\\omega_i) = n p = 1 \\implies p = \\frac{1}{n},\\quad P(A) = \\frac{m}{n}", "note": "由规范性与有限可加性直接推出古典概型公式", "cited_formula_ids": ["stat.prob.kolmogorov_axioms"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(A) = \\frac{|A|}{|\\Omega|} = \\frac{m}{n}", "note": "公理化概率论同时兼容古典概型、几何概型与一般连续测度空间", "cited_formula_ids": ["stat.prob.kolmogorov_axioms"], "pitfall": "古典概型仅适用于有限且等可能情形，连续区间上的事件必须回归公理化概率测度。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.kolmogorov_to_addition",
            "from_formula_ids": ["stat.prob.kolmogorov_axioms"],
            "to_formula_id": "stat.prob.addition",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["disjoint_union_decomposition"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "把 A∪B 拆为互斥并 A ∪ (B \\ AB)，由柯尔莫哥洛夫可加性公理无需古典概型前提即可严格证得通用加法公式。",
                "L2_standard": [
                    {"step": 1, "latex": "A \\cup B = A \\cup (B \\setminus AB),\\quad B = AB \\cup (B \\setminus AB) \\implies P(A \\cup B) = P(A) + P(B) - P(AB)", "note": "对两处互斥分解分别应用可加性公理并消去 P(B \\ AB)", "cited_formula_ids": ["stat.prob.kolmogorov_axioms"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(A \\cup B) = P(A) + P(B) - P(AB)", "note": "证明全程仅用到有限可加性，适用于任意离散与连续概率空间", "cited_formula_ids": ["stat.prob.kolmogorov_axioms"], "pitfall": "推广到三事件时末尾加回 P(ABC)（奇加偶减容斥原则）。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.bern_to_binom",
            "from_formula_ids": ["stat.dist.bernoulli"],
            "to_formula_id": "stat.dist.binomial",
            "relation_type": "generalizes",
            "dependency_site": "proof_level",
            "inference_rules": ["iid_bernoulli_sum"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "将 n 个独立同分布的伯努利 0-1 变量相加 X = X1 + ... + Xn，即推广得到二项分布 B(n, p)。",
                "L2_standard": [
                    {"step": 1, "latex": "X = \\sum_{i=1}^n X_i,\\quad X_i \\overset{\\text{i.i.d.}}{\\sim} \\text{Bernoulli}(p) \\implies X \\sim B(n, p)", "note": "n 重独立伯努利试验成功总次数即二项分布", "cited_formula_ids": ["stat.dist.bernoulli"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(X = k) = \\binom{n}{k} p^k (1-p)^{n-k}", "note": "当 n = 1 时精确退化为伯努利分布", "cited_formula_ids": ["stat.dist.bernoulli"], "pitfall": "若各次试验成功概率 p_i 不相同，独立和服从泊松二项分布而非二项分布。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.gamma_to_chi",
            "from_formula_ids": ["stat.dist.gamma"],
            "to_formula_id": "stat.dist.chi_square",
            "relation_type": "special_case_of",
            "dependency_site": "definition_level",
            "inference_rules": ["parameter_specialization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在伽马分布 Gamma(α, β) 中令形状参数 α = n/2、速率参数 β = 1/2，即精确特例化为自由度为 n 的卡方分布 χ²(n)。",
                "L2_standard": [
                    {"step": 1, "latex": "\\chi^2(n) \\equiv \\text{Gamma}\\!\\left(\\frac{n}{2}, \\frac{1}{2}\\right) \\implies E(\\chi^2) = \\frac{n/2}{1/2} = n,\\quad D(\\chi^2) = \\frac{n/2}{1/4} = 2n", "note": "代入伽马分布期望与方差通式直接得卡方分布均值 n 与方差 2n", "cited_formula_ids": ["stat.dist.gamma"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "f_{\\chi^2(n)}(x) = \\frac{1}{2^{n/2}\\Gamma(n/2)} x^{n/2 - 1} e^{-x/2}", "note": "同时由伽马分布可加性立即得到独立卡方分布自由度可加：χ²(n1) + χ²(n2) ~ χ²(n1+n2)", "cited_formula_ids": ["stat.dist.gamma"], "pitfall": "当自由度 n = 2 时，χ²(2) = Gamma(1, 1/2) 恰好就是速率 λ = 1/2 的指数分布。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.normal_to_lognormal",
            "from_formula_ids": ["stat.dist.normal_pdf"],
            "to_formula_id": "stat.dist.lognormal",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["exponential_transformation"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "将正态随机变量 Y ~ N(μ, σ²) 代入指数映射 X = e^Y，按雅可比换元乘以 1/x 即得对数正态分布密度。",
                "L2_standard": [
                    {"step": 1, "latex": "Y = \\ln X \\sim N(\\mu, \\sigma^2) \\implies f_X(x) = f_Y(\\ln x)\\cdot \\frac{1}{x} = \\frac{1}{x\\sigma\\sqrt{2\\pi}} e^{-\\frac{(\\ln x - \\mu)^2}{2\\sigma^2}}", "note": "把正态密度代入反函数 y = ln x 并乘以导数 1/x", "cited_formula_ids": ["stat.dist.normal_pdf"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "X = e^Y \\sim \\text{LogNormal}(\\mu, \\sigma^2)", "note": "独立对数正态变量相乘等价于正态变量相加，因此对数正态分布在乘法下封闭", "cited_formula_ids": ["stat.dist.normal_pdf"], "pitfall": "对数正态分布参数 (μ, σ²) 是 ln X 的均值和方差，不是 X 本身的均值和方差。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.normal_t_to_cauchy_ratio",
            "from_formula_ids": ["stat.dist.normal_pdf", "stat.dist.t_dist"],
            "to_formula_id": "stat.dist.cauchy_normal_ratio",
            "relation_type": "equivalent_to",
            "dependency_site": "proof_level",
            "inference_rules": ["normal_ratio_t1_equivalence"],
            "bidirectional": True,
            "levels": {
                "L1_summary": "在学生 t 分布定义 T = Z / √(χ²(n)/n) 中取 n = 1，分母化为 |Z2|，由此打通正态分布、t(1) 与标准柯西分布三者等价。",
                "L2_standard": [
                    {"step": 1, "latex": "T = \\frac{Z_1}{\\sqrt{Z_2^2 / 1}} = \\frac{Z_1}{|Z_2|} \\overset{d}{=} \\frac{Z_1}{Z_2} \\sim \\text{Cauchy}(0, 1) \\equiv t(1)", "note": "取 t 分布自由度 n = 1 即等价于独立标准正态之商", "cited_formula_ids": ["stat.dist.normal_pdf", "stat.dist.t_dist"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "t(1) \\equiv \\text{Cauchy}(0, 1)", "note": "这也解释了为何 t(ν) 仅在 ν > 1 时存在期望、仅在 ν > 2 时存在有限方差", "cited_formula_ids": ["stat.dist.normal_pdf", "stat.dist.t_dist"], "pitfall": "当样本量只有 n = 2（自由度 df = 1）时，t 统计量服从柯西分布，不存在期望与方差。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.cauchy_counter_lln",
            "from_formula_ids": ["stat.dist.cauchy_no_moments"],
            "to_formula_id": "stat.inf.lln",
            "relation_type": "counterexample_to",
            "dependency_site": "application_level",
            "inference_rules": ["missing_first_moment_counterexample"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "柯西分布一阶绝对矩发散（无数学期望），导致其样本均值 X̄_n 恒与单样本同分布，永远不收敛到常数，是弱大数定律前提不可省略的经典反例。",
                "L2_standard": [
                    {"step": 1, "latex": "X_1, \\dots, X_n \\overset{\\text{i.i.d.}}{\\sim} \\text{Cauchy}(x_0, \\gamma) \\implies \\bar{X}_n \\sim \\text{Cauchy}(x_0, \\gamma) \\not\\xrightarrow{P} x_0", "note": "无论样本量 n 多大，样本均值的离散尺度 γ 纹丝不动", "cited_formula_ids": ["stat.dist.cauchy_no_moments"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(|\\bar{X}_n - x_0| > \\gamma) = \\frac{1}{2}\\quad (\\forall n \\ge 1)", "note": "即便采集一百万个柯西样本，均值落在 [x0-γ, x0+γ] 之外的概率依然高达 50%", "cited_formula_ids": ["stat.dist.cauchy_no_moments"], "pitfall": "重尾数据估计中心位置时切勿盲目用样本均值，应改用一致且渐近正态的样本中位数。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.cauchy_counter_clt",
            "from_formula_ids": ["stat.dist.cauchy_no_moments"],
            "to_formula_id": "stat.inf.clt",
            "relation_type": "counterexample_to",
            "dependency_site": "application_level",
            "inference_rules": ["infinite_variance_counterexample"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "柯西分布方差不存在（∞），违反中心极限定理的有限方差条件，其标准化样本均值不趋于正态分布而保持稳定重尾柯西形态。",
                "L2_standard": [
                    {"step": 1, "latex": "\\frac{1}{n}\\sum_{i=1}^n X_i \\overset{d}{=} X_1 \\sim \\text{Cauchy}(0, 1) \\not\\xrightarrow{d} N(0, 1)", "note": "柯西分布属于特征指数 α = 1 的稳定分布，不落入正态吸引域", "cited_formula_ids": ["stat.dist.cauchy_no_moments"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "D(X) = \\text{不存在} \\implies \\text{CLT 失效}", "note": "广义中心极限定理表明，无有限方差的重尾和会收敛到 α-稳定分布而非高斯分布", "cited_formula_ids": ["stat.dist.cauchy_no_moments"], "pitfall": "在金融极端收益或网络重尾流量中直接套用 CLT 正态置信区间会严重低估黑天鹅尾部风险。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.markov_to_chebyshev",
            "from_formula_ids": ["stat.ineq.markov"],
            "to_formula_id": "stat.inf.chebyshev",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["squared_deviation_substitution"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在马尔可夫不等式中代入非负随机变量 Y = (X - μ)² 与阈值 a = ε²，一行即证切比雪夫不等式。",
                "L2_standard": [
                    {"step": 1, "latex": "P(|X - \\mu| \\ge \\varepsilon) = P\\big((X - \\mu)^2 \\ge \\varepsilon^2\\big) \\le \\frac{E[(X - \\mu)^2]}{\\varepsilon^2} = \\frac{\\sigma^2}{\\varepsilon^2}", "note": "令 Y = (X - μ)² ≥ 0 直接套用马尔可夫不等式", "cited_formula_ids": ["stat.ineq.markov"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "P(|X - \\mu| \\ge \\varepsilon) \\le \\frac{\\sigma^2}{\\varepsilon^2}", "note": "由此可见：马尔可夫（一阶矩）→ 切比雪夫（二阶矩）→ 霍夫丁（指数矩）构成了完整的概率集中不等式阶梯", "cited_formula_ids": ["stat.ineq.markov"], "pitfall": "切比雪夫不等式虽普适，但衰减速度仅 O(1/ε²)，远不如有界情形下的霍夫丁指数衰减紧致。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.jensen_to_var",
            "from_formula_ids": ["stat.ineq.jensen"],
            "to_formula_id": "stat.rv.variance_def",
            "relation_type": "applies_in",
            "dependency_site": "proof_level",
            "inference_rules": ["quadratic_convexity"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在琴生不等式中取凸函数 φ(x) = x²，立得 [E(X)]² ≤ E(X²)，直接从凸分析视角证明方差 D(X) = E(X²) - [E(X)]² ≥ 0。",
                "L2_standard": [
                    {"step": 1, "latex": "\\varphi(x) = x^2 \\text{ 为凸函数} \\implies [E(X)]^2 \\le E(X^2) \\implies D(X) = E(X^2) - [E(X)]^2 \\ge 0", "note": "二次凸函数套用琴生不等式立即保证方差非负", "cited_formula_ids": ["stat.ineq.jensen"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "D(X) = 0 \\iff X = E(X)\\ \\text{a.s.}", "note": "因 φ(x)=x² 严格凸，等号成立当且仅当随机变量几乎必然退化为常数", "cited_formula_ids": ["stat.ineq.jensen"], "pitfall": "同理对严格凹函数 √x 应用琴生不等式立得 E(S) ≤ √E(S²) = σ，解释了为何样本标准差 S 是总体标准差 σ 的向下有偏估计。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.char_to_clt",
            "from_formula_ids": ["stat.transform.char_func", "calc.series.taylor"],
            "to_formula_id": "stat.inf.clt",
            "relation_type": "derives_to",
            "dependency_site": "proof_level",
            "inference_rules": ["characteristic_function_taylor_limit"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "对标准化样本均值 Z_n 的特征函数做二阶泰勒展开得 [1 - t²/(2n) + o(1/n)]^n → e^(-t²/2)，由列维连续性定理严格证得中心极限定理。",
                "L2_standard": [
                    {"step": 1, "latex": "\\varphi_{Z_n}(t) = \\left[\\varphi_{(X-\\mu)/\\sigma}\\!\\left(\\frac{t}{\\sqrt{n}}\\right)\\right]^n = \\left[1 - \\frac{t^2}{2n} + o\\!\\left(\\frac{1}{n}\\right)\\right]^n", "note": "利用独立和特征函数连乘及二阶泰勒展开（均值 0、方差 1）", "cited_formula_ids": ["stat.transform.char_func", "calc.series.taylor"]},
                    {"step": 2, "latex": "\\xrightarrow{n \\to \\infty} e^{-t^2/2} = \\varphi_{N(0,1)}(t) \\implies Z_n \\xrightarrow{d} N(0, 1)", "note": "收敛至标准正态特征函数，由列维连续性定理证毕", "cited_formula_ids": []}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\varphi_{Z_n}(t) \\to e^{-t^2/2}", "note": "之所以用特征函数而非 MGF 证明经典 CLT，正是因为 CLT 仅要求有限二阶矩，不要求原分布存在 MGF", "cited_formula_ids": ["stat.transform.char_func", "calc.series.taylor"], "pitfall": "若只用 MGF 证明 CLT，会额外要求分布具有指数轻尾，排除了如自由度为 3 的 t 分布等合法情形。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.total_prob_to_total_exp",
            "from_formula_ids": ["stat.prob.total_probability"],
            "to_formula_id": "stat.law.total_expectation",
            "relation_type": "generalizes",
            "dependency_site": "definition_level",
            "inference_rules": ["indicator_random_variable_generalization"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "在全期望公式 E(X) = E[E(X|Y)] 中令 X = I_B 为事件 B 的示性函数，即精确退化为全概率公式 P(B) = ∑ P(B|A_i)P(A_i)。",
                "L2_standard": [
                    {"step": 1, "latex": "X = \\mathbf{1}_B \\implies P(B) = E(\\mathbf{1}_B) = E[E(\\mathbf{1}_B \\mid Y)] = \\sum_i P(B \\mid A_i) P(A_i)", "note": "全期望公式是全概率公式向一般随机变量的自然推广", "cited_formula_ids": ["stat.prob.total_probability"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "E(X) = E[E(X \\mid Y)]", "note": "示性函数桥梁把事件概率恒等式统一纳入期望算子体系", "cited_formula_ids": ["stat.prob.total_probability"], "pitfall": "全期望公式不仅适用于有限划分，也直接适用于连续条件变量 Y。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.beta_to_bayes_conj",
            "from_formula_ids": ["stat.dist.beta", "stat.dist.binomial"],
            "to_formula_id": "stat.est.bayes_conj",
            "relation_type": "applies_in",
            "dependency_site": "application_level",
            "inference_rules": ["beta_binomial_conjugate_updating"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "Beta(α, β) 先验配二项似然 B(n, p) 得后验 Beta(α+k, β+n-k)，与正态-正态共轭同属指数族共轭贝叶斯解析更新范式。",
                "L2_standard": [
                    {"step": 1, "latex": "p(\\theta \\mid k) \\propto \\theta^{\\alpha-1}(1-\\theta)^{\\beta-1} \\cdot \\theta^k(1-\\theta)^{n-k} = \\theta^{\alpha+k-1}(1-\\theta)^{\\beta+n-k-1}", "note": "后验仍为 Beta 分布，参数直接累加观测成功数 k 与失败数 n-k", "cited_formula_ids": ["stat.dist.beta", "stat.dist.binomial"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "E(\\theta \\mid k) = \\frac{\\alpha + k}{\\alpha + \\beta + n}", "note": "后验均值同样是先验均值 α/(α+β) 与样本频率 k/n 的有效样本量加权平均", "cited_formula_ids": ["stat.dist.beta", "stat.dist.binomial"], "pitfall": "与正态-正态共轭一样，样本量 n 越大先验权重越小，后验均值渐近收敛于 MLE 频率 k/n。"}
                ]
            }
        },
        {
            "id": "deriv.bridge.improper_to_cauchy_no_moments",
            "from_formula_ids": ["calc.int.improper"],
            "to_formula_id": "stat.dist.cauchy_no_moments",
            "relation_type": "applies_in",
            "dependency_site": "proof_level",
            "inference_rules": ["improper_integral_divergence_test"],
            "bidirectional": False,
            "levels": {
                "L1_summary": "双边广义积分收敛要求正负半轴各自独立收敛；柯西一阶矩正半轴 ∫_0^∞ x/(1+x²) dx 呈对数发散，直接判定期望不存在。",
                "L2_standard": [
                    {"step": 1, "latex": "\\int_0^{+\\infty} \\frac{x}{1+x^2}\\,dx = \\lim_{b\\to+\\infty} \\frac{1}{2}\\ln(1+b^2) = +\\infty", "note": "套用无穷区间广义积分定义算出单侧发散", "cited_formula_ids": ["calc.int.improper"]}
                ],
                "L3_detailed": [
                    {"step": 1, "latex": "\\int_{-\\infty}^{+\\infty} x f(x)\\,dx = \\int_{-\\infty}^0 + \\int_0^{+\\infty} = (-\\infty) + (+\\infty)\\text{（不定式发散）}", "note": "严格区分广义积分收敛与柯西主值，是大学微积分与概率论交汇处的经典考题", "cited_formula_ids": ["calc.int.improper"], "pitfall": "双边无穷积分必须拆分在任意有限点 c 两侧分别取独立极限，绝不可同步令上下限趋于 ±∞ 抵消。"}
                ]
            }
        }
    ]

    # 合并全量总图（初中 58 + 高中 83 + 大学及以后 96 = 237 广义知识对象）
    master_formulas = list(all_formulas)
    master_derivations = list(all_derivations)
    master_seen_f = set(seen_f)
    master_seen_d = set(seen_d)
    for extra_pack in (stat_data, calc_he_data, linalg_data, sh_seq_geo_data, sh_phys_data, stat_adv_data, prob_ext_data):
        for f in extra_pack["formulas"]:
            if f["id"] not in master_seen_f:
                master_seen_f.add(f["id"])
                master_formulas.append(f)
        for d in extra_pack["derivations"]:
            if d["id"] not in master_seen_d:
                master_seen_d.add(d["id"])
                master_derivations.append(d)
    for b in higher_ed_bridges:
        assert b["id"] not in master_seen_d, f"Duplicate bridge ID: {b['id']}"
        master_seen_d.add(b["id"])
        master_derivations.append(b)

    master_graph = {
        "schema_version": "1.1.0",
        "metadata": {
            "pack_id": f"formula-graph-master-{len(master_formulas)}",
            "title": f"数理知识图谱全量底座（初中 + 高中 + 大学 · {len(master_formulas)} 对象）",
            "curriculum_ref": "全阶段跨学科统一广义知识对象图谱（支持动态视图生成）",
            "updated_at": "2026-11-24",
        },
        "formulas": master_formulas,
        "derivations": master_derivations,
    }
    master_bundle = bundles_dir / f"master-graph-{len(master_formulas)}.json"
    master_bundle.write_text(json.dumps(master_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    m_errs, m_warns, m_summary = validate.validate_pack(master_bundle, None, None)
    if m_errs:
        print("全量总图校验失败:", m_errs)
        return 1
    print(
        f"[PASS] bundles/{master_bundle.name} | "
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

    # 同步生成可直接部署至 GitHub Pages / Cloudflare Pages 的独立静态网站 + PWA 目录（site/）
    import shutil
    site_dir = repo_root / "site"
    site_dir.mkdir(exist_ok=True)
    (site_dir / "index.html").write_text(rendered, encoding="utf-8")
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    pwa_dir = repo_root / "prototype" / "pwa"
    for asset_name in ("manifest.webmanifest", "sw.js", "icon.svg", "icon-192.png", "icon-512.png"):
        shutil.copy2(pwa_dir / asset_name, site_dir / asset_name)

    print(f"OK: {len(master_formulas)} 公式全部完成多级分类映射，已生成 prototype/index.html 与可部署 PWA 站点 site/。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
