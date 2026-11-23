#!/usr/bin/env python3
"""
构建初中全量跨学科总图（58 公式 + 7 条跨批次桥梁边）并同步接入交互原型。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 跨批次桥梁推导边（连接 Batch 1 电学、Batch 2 代数与 Batch 3 力学/化学）
CROSS_BATCH_BRIDGES = [
    {
        "id": "deriv.bridge.prop_to_velocity",
        "from_formula_ids": ["math.func.direct_proportion"],
        "to_formula_id": "physics.mech.velocity",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["constant_rate_model"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "匀速直线运动中路程 s = vt 与时间 t 满足正比例函数关系，图像斜率即速度 v。",
            "L2_standard": [
                {"step": 1, "latex": "s = v t \\implies v = \\frac{s}{t}", "note": "速度 v 恒定时，s-t 图像是过原点的直线，对应正比例函数 y = kx", "cited_formula_ids": ["math.func.direct_proportion"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "s = v t \\quad (v \\text{ 为非零常数})", "note": "将时间 t 视为自变量 x、路程 s 视为因变量 y，斜率 k 即速度 v", "cited_formula_ids": ["math.func.direct_proportion"], "pitfall": "若 s-t 图像不过原点，则对应一次函数 s = s0 + vt，起点存在初始位移 s0。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.prop_to_density",
        "from_formula_ids": ["math.func.direct_proportion", "math.func.inverse_proportion"],
        "to_formula_id": "physics.mech.density",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["control_variable_modeling"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "同种物质质量 m = ρV 与体积成正比（斜率为密度 ρ）；质量一定时不同物质密度与体积成反比。",
            "L2_standard": [
                {"step": 1, "latex": "m = \\rho V \\implies \\rho = \\frac{m}{V}", "note": "同种物质 m-V 图像为过原点正比例直线，斜率即密度 ρ", "cited_formula_ids": ["math.func.direct_proportion"]},
                {"step": 2, "latex": "\\rho = \\frac{m}{V}\\ (m \\text{ 一定})", "note": "质量相同时，密度与体积满足反比例函数关系", "cited_formula_ids": ["math.func.inverse_proportion"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "m = \\rho V", "note": "对比 y = kx，可从 m-V 图像陡峭程度直接比较不同物质密度大小", "cited_formula_ids": ["math.func.direct_proportion"]},
                {"step": 2, "latex": "\\rho = \\frac{m}{V}", "note": "同质量不同物质体积越大密度越小，符合反比例双曲线规律", "cited_formula_ids": ["math.func.inverse_proportion"], "pitfall": "对同一种物质不能说“密度与质量成正比”，密度是物质固有特性。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.prop_to_gravity",
        "from_formula_ids": ["math.func.direct_proportion"],
        "to_formula_id": "physics.mech.gravity",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["proportionality"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "地球表面附近物体所受重力 G 与质量 m 满足正比例函数，比例系数即重力常数 g。",
            "L2_standard": [
                {"step": 1, "latex": "G = g m = m g", "note": "实验测得 G/m = g 为常数，符合正比例函数 y = kx", "cited_formula_ids": ["math.func.direct_proportion"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "G = m g \\quad (g \\approx 9.8\\ \\text{N/kg})", "note": "将质量 m 视作自变量，G-m 图像为过原点直线，斜率为 g", "cited_formula_ids": ["math.func.direct_proportion"], "pitfall": "因果关系是“重力与质量成正比”，不可倒说“质量与重力成正比”。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.prop_to_pressure",
        "from_formula_ids": ["math.func.direct_proportion", "math.func.inverse_proportion"],
        "to_formula_id": "physics.mech.pressure_def",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["control_variable_modeling"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "受力面积一定时压强与压力成正比；压力一定时压强 p = F/S 与受力面积成反比。",
            "L2_standard": [
                {"step": 1, "latex": "p = \\frac{1}{S} F\\ (S \\text{ 一定}),\\quad p = \\frac{F}{S}\\ (F \\text{ 一定})", "note": "分别对应数学正比例与反比例函数模型", "cited_formula_ids": ["math.func.direct_proportion", "math.func.inverse_proportion"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "p = \\frac{F}{S}", "note": "增大受力面积（如履带、书包宽肩带）本质上是利用反比例函数减小压强", "cited_formula_ids": ["math.func.direct_proportion", "math.func.inverse_proportion"], "pitfall": "讨论压强与受力面积反比时，必须先声明“压力 F 保持不变”。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.inv_prop_to_lever",
        "from_formula_ids": ["math.func.inverse_proportion"],
        "to_formula_id": "physics.mech.lever_balance",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["inverse_proportionality"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "阻力与阻力臂乘积 F2l2 一定时，动力 F1 = (F2l2)/l1 与动力臂 l1 满足反比例函数关系。",
            "L2_standard": [
                {"step": 1, "latex": "F_1 l_1 = F_2 l_2 = k \\implies F_1 = \\frac{k}{l_1}", "note": "将阻力矩 F2l2 视作非零常数 k，动力与动力臂成反比", "cited_formula_ids": ["math.func.inverse_proportion"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "F_1 = \\frac{F_2 l_2}{l_1}", "note": "要使所需动力 F1 最小，应寻找最大动力臂 l1（支点到动力作用点连线作力臂）", "cited_formula_ids": ["math.func.inverse_proportion"], "pitfall": "找最小动力题型的核心即反比例单调性：分子阻力矩一定，分母动力臂越大则动力越小。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.quad_ext_to_elec_power",
        "from_formula_ids": ["math.func.quad_extremum", "physics.elec.electric_power_variants", "physics.elec.series_resistance"],
        "to_formula_id": "physics.elec.electric_power_ui",
        "relation_type": "applies_in",
        "dependency_site": "application_level",
        "inference_rules": ["quadratic_optimization"],
        "bidirectional": False,
        "levels": {
            "L1_summary": "串联电路中滑动变阻器电功率可写为关于电流 I 的二次函数 P滑 = UI - I²R0，套用二次函数顶点最值公式即得最大功率条件 R滑 = R0。",
            "L2_standard": [
                {"step": 1, "latex": "P_{\\text{滑}} = U_{\\text{滑}} I = (U - I R_0) I = -R_0 I^2 + U I", "note": "联立串联电压规律与电功率公式，构造关于电流 I 的开口向下二次函数", "cited_formula_ids": ["physics.elec.series_resistance", "physics.elec.electric_power_variants"]},
                {"step": 2, "latex": "I = -\\frac{b}{2a} = \\frac{U}{2 R_0} \\implies P_{\\text{max}} = \\frac{U^2}{4 R_0}", "note": "套用二次函数对称轴与极值公式，此时 R滑 = R0", "cited_formula_ids": ["math.func.quad_extremum"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "P_{\\text{滑}} = -R_0 I^2 + U I \\quad (a = -R_0 < 0,\\ b = U,\\ c = 0)", "note": "把定值电阻 R0 与电源电压 U 视作常数，构成关于电流 I 的二次函数", "cited_formula_ids": ["physics.elec.series_resistance", "physics.elec.electric_power_variants"]},
                {"step": 2, "latex": "I_{\\text{极}} = -\\frac{U}{2(-R_0)} = \\frac{U}{2R_0},\\quad P_{\\text{max}} = \\frac{0 - U^2}{4(-R_0)} = \\frac{U^2}{4R_0}", "note": "代入二次函数顶点极值公式求得最大输出功率，对应 R滑 = R0", "cited_formula_ids": ["math.func.quad_extremum"], "pitfall": "若滑动变阻器最大阻值小于 R0，则对称轴落在取值范围外，需改用二次函数单调性取端点最大值。"}
            ]
        }
    },
    {
        "id": "deriv.bridge.mech_elec_power_analog",
        "from_formula_ids": ["physics.mech.power_def"],
        "to_formula_id": "physics.elec.electric_power_def",
        "relation_type": "equivalent_to",
        "dependency_site": "definition_level",
        "inference_rules": ["cross_domain_unification"],
        "bidirectional": True,
        "levels": {
            "L1_summary": "机械功率与电功率本质上是同一物理定义“单位时间内转化的能量 P = W/t”，量纲均为 M L² T⁻³（单位 W）。",
            "L2_standard": [
                {"step": 1, "latex": "P = \\frac{W}{t}\\quad ([P] = \\text{J}/\\text{s} = \\text{W})", "note": "机械功与电功同属能量量纲，二者功率定义完全统一", "cited_formula_ids": ["physics.mech.power_def"]}
            ],
            "L3_detailed": [
                {"step": 1, "latex": "P = \\frac{W}{t}", "note": "在机电综合题（如电动起重机提重物）中，机械输出功率 P有用 = Gh/t 与电输入总功率 P总 = UI 可直接通过机械效率 η = P有用/P总 衔接", "cited_formula_ids": ["physics.mech.power_def"], "pitfall": "非纯电阻电动机的机械输出功率等于总电功率减去线圈发热功率，即 P机 = UI - I²R。"}
            ]
        }
    }
]

# 8 列分层泳道坐标（58 公式，零重叠）
UNIFIED_COLUMNS = [
    ("1. 乘法与因式分解", [
        "math.alg.distributive", "math.alg.diff_of_squares", "math.alg.perfect_square_sum",
        "math.alg.perfect_square_diff", "math.alg.factor_diff_squares", "math.alg.factor_perfect_square",
        "math.alg.cross_factor", "math.alg.completing_square"
    ]),
    ("2. 方程与韦达定理", [
        "math.eq.quadratic_standard", "math.eq.quadratic_completed", "math.eq.discriminant",
        "math.eq.quadratic_formula", "math.eq.vieta_sum", "math.eq.vieta_product",
        "math.eq.root_diff", "math.eq.root_sq_sum"
    ]),
    ("3. 函数与跨科桥梁", [
        "math.func.quad_general", "math.func.quad_vertex", "math.func.quad_extremum",
        "math.func.quad_intercept", "math.func.direct_proportion", "math.func.inverse_proportion",
        "math.alg.reciprocal_sum", "physics.mech.volume_prism"
    ]),
    ("4. 欧姆与串联电路", [
        "physics.elec.current_def", "physics.elec.ohms_law", "physics.elec.ohms_voltage",
        "physics.elec.ohms_resistance", "physics.elec.series_basic", "physics.elec.series_resistance",
        "physics.elec.series_voltage_divider"
    ]),
    ("5. 并联与电功电热", [
        "physics.elec.parallel_basic", "physics.elec.parallel_resistance", "physics.elec.parallel_two_resistors",
        "physics.elec.electric_work", "physics.elec.electric_power_def", "physics.elec.electric_power_ui",
        "physics.elec.electric_power_variants", "physics.elec.joules_law"
    ]),
    ("6. 密度 · 压强 · 浮力", [
        "physics.mech.velocity", "physics.mech.density", "physics.mech.gravity",
        "physics.mech.pressure_def", "physics.mech.liquid_pressure", "physics.mech.archimedes",
        "physics.mech.floating_balance"
    ]),
    ("7. 简单机械与功功率", [
        "physics.mech.lever_balance", "physics.mech.pulley_force", "physics.mech.pulley_distance",
        "physics.mech.work_def", "physics.mech.useful_work_lift", "physics.mech.power_def",
        "physics.mech.power_fv", "physics.mech.mech_efficiency"
    ]),
    ("8. 化学溶液定量", [
        "chemistry.sol.mass_fraction", "chemistry.sol.solution_mass",
        "chemistry.sol.dilution", "chemistry.sol.solubility_fraction"
    ]),
]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    jh_dir = repo_root / "data" / "cn-junior-high"
    bundles_dir = repo_root / "bundles"
    bundles_dir.mkdir(exist_ok=True)

    batch_files = [
        jh_dir / "electricity-math-batch1.json",
        jh_dir / "algebra-quadratic-batch2.json",
        jh_dir / "mechanics-chemistry-batch3.json",
    ]

    all_formulas = []
    all_derivations = []
    seen_f = set()
    seen_d = set()

    for bf in batch_files:
        pack = json.loads(bf.read_text(encoding="utf-8"))
        for f in pack["formulas"]:
            if f["id"] not in seen_f:
                seen_f.add(f["id"])
                all_formulas.append(f)
        for d in pack["derivations"]:
            if d["id"] not in seen_d:
                seen_d.add(d["id"])
                all_derivations.append(d)

    for b in CROSS_BATCH_BRIDGES:
        assert b["id"] not in seen_d
        seen_d.add(b["id"])
        all_derivations.append(b)

    unified = {
        "schema_version": "1.0.0",
        "metadata": {
            "pack_id": "cn-junior-high-unified-58",
            "title": "初中全量跨学科总图（数学 · 物理 · 化学 · 58 公式）",
            "curriculum_ref": "中国义务教育 7–9 年级数学、物理与化学核心公式（Batch 1–3 融合 + 7 条跨专题桥梁）",
            "updated_at": "2026-11-23",
        },
        "formulas": all_formulas,
        "derivations": all_derivations,
    }

    bundle_path = bundles_dir / "junior-high-unified-58.json"
    bundle_path.write_text(json.dumps(unified, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 校验合并后的统一总图
    sys.path.insert(0, str(repo_root / "scripts"))
    import validate  # type: ignore

    errs, warns, summary = validate.validate_pack(bundle_path, None, None)
    if errs:
        print("统一总图校验失败:", errs)
        return 1

    print(
        f"[PASS] bundles/junior-high-unified-58.json | "
        f"公式 {summary['formula_count']} 个 · "
        f"推导 {summary['derivation_count']} 条（含 7 条跨批次桥梁）· "
        f"连通分量 {summary['connected_components']} · "
        f"孤立节点 {summary['isolated_count']} · 警告 {len(warns)}"
    )

    # 计算 8 列泳道坐标并写入 prototype/index.html
    positions = {}
    lanes = []
    col_x = 24
    for lane_label, ids in UNIFIED_COLUMNS:
        lanes.append({"x": col_x, "label": lane_label})
        for row_idx, fid in enumerate(ids):
            positions[fid] = {"x": col_x, "y": 48 + row_idx * 126}
        col_x += 268

    assert set(positions.keys()) == seen_f, f"坐标与公式集合不一致: diff={set(positions.keys()) ^ seen_f}"

    unified_pack_obj = {
        "data": unified,
        "stageW": 2180,
        "stageH": 1080,
        "defaultZoom": 0.62,
        "defaultFormula": "math.func.direct_proportion",
        "defaultDeriv": "deriv.bridge.quad_ext_to_elec_power",
        "defaultPathStart": "math.alg.distributive",
        "defaultPathEnd": "physics.elec.joules_law",
        "lanes": lanes,
        "topicButtons": [
            {"id": "all", "label": "全部"},
            {"id": "multiplication_formulas", "label": "乘法公式"},
            {"id": "quadratic_equations", "label": "二次方程"},
            {"id": "quadratic_functions", "label": "二次函数"},
            {"id": "proportionality", "label": "比例桥梁"},
            {"id": "electricity", "label": "电学"},
            {"id": "mechanics", "label": "力学"},
            {"id": "chemistry_solutions", "label": "化学溶液"},
        ],
        "positions": positions,
    }

    html_path = repo_root / "prototype" / "index.html"
    html = html_path.read_text(encoding="utf-8")

    # 幂等注入：若已存在 junior_unified 则先清除或直接首次注入
    opt_tag = '<option value="junior_unified">初中全量 · 跨学科总图（58公式）</option>'
    if opt_tag not in html:
        opt_anchor = '<option value="junior_mech_chem">初中 · 力学与化学定量（20公式）</option>'
        assert opt_anchor in html
        html = html.replace(opt_anchor, opt_tag + "\n          " + opt_anchor, 1)

    if "junior_unified:" not in html:
        pack_anchor = "const PACKS = {\n      junior_mech_chem:"
        assert pack_anchor in html
        html = html.replace(
            pack_anchor,
            "const PACKS = {\n      junior_unified: "
            + json.dumps(unified_pack_obj, ensure_ascii=False, indent=2)
            + ",\n      junior_mech_chem:",
            1,
        )

    html = html.replace('loadPack("junior_mech_chem");', 'loadPack("junior_unified");', 1)
    html_path.write_text(html, encoding="utf-8")
    print("OK: 已将初中 58 公式统一跨学科总图接入 prototype/index.html（默认视图）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
