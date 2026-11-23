#!/usr/bin/env python3
"""
公式知识图谱数据包自动化校验脚本（validate.py）

功能：
1. Schema 格式与字段枚举校验（零依赖内置校验；若本机安装 jsonschema 则同步执行 Draft 2020-12 校验）
2. 悬空引用校验（from_formula_ids / to_formula_id / cited_formula_ids）
3. 多级推导完整性校验（L1_summary / L2_standard / L3_detailed 及步骤连续性）
4. 图连通性与孤立节点检测（入度、出度、连通分量统计）
5. 跨数据包全局 ID 冲突检测
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

# 允许的枚举值（与 schema/formula-graph.v1.schema.json 保持一致）
VALID_DISCIPLINES = {"mathematics", "physics", "chemistry", "statistics", "computer_science"}
VALID_STAGES = {"junior_high", "senior_high", "undergraduate", "graduate"}
VALID_MATH_TYPES = {"scalar", "angle", "vector", "matrix", "function", "set", "constant"}
VALID_REVIEW_STATUS = {"draft", "ai_reviewed", "human_verified"}
VALID_RELATION_TYPES = {
    "derives_to",
    "special_case_of",
    "generalizes",
    "equivalent_to",
    "simplifies",
    "applies_in",
}
VALID_DEP_SITES = {"definition_level", "proof_level", "application_level"}

RE_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
RE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
RE_FORMULA_ID = re.compile(r"^[a-z]+\.[a-z0-9_]+\.[a-z0-9_]+$")
RE_DERIV_ID = re.compile(r"^deriv\.[a-z0-9_]+\.[a-z0-9_]+$")


def validate_steps(
    steps: Any,
    level_name: str,
    deriv_id: str,
    formula_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    """校验 L2 / L3 推导步骤列表结构、编号连续性与公式引用。"""
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append(f"[{deriv_id}] {level_name} 必须为非空数组")
        return

    has_pitfall = False
    for idx, st in enumerate(steps, start=1):
        if not isinstance(st, dict):
            errors.append(f"[{deriv_id}] {level_name}[{idx}] 必须为对象")
            continue
        if st.get("step") != idx:
            errors.append(f"[{deriv_id}] {level_name}[{idx}] step 编号应为 {idx}，实际为 {st.get('step')}")
        if not isinstance(st.get("latex"), str) or not st["latex"].strip():
            errors.append(f"[{deriv_id}] {level_name}[{idx}] 缺少非空 latex")
        if not isinstance(st.get("note"), str) or not st["note"].strip():
            errors.append(f"[{deriv_id}] {level_name}[{idx}] 缺少非空 note")

        cited = st.get("cited_formula_ids", [])
        if not isinstance(cited, list):
            errors.append(f"[{deriv_id}] {level_name}[{idx}] cited_formula_ids 必须为数组")
        else:
            for cid in cited:
                if cid not in formula_ids:
                    errors.append(f"[{deriv_id}] {level_name}[{idx}] 悬空引用 cited_formula_ids: {cid}")

        if isinstance(st.get("pitfall"), str) and st["pitfall"].strip():
            has_pitfall = True

    if level_name == "L3_detailed" and not has_pitfall:
        warnings.append(f"[{deriv_id}] L3_detailed 建议至少包含 1 条 pitfall 易错提醒")


def validate_pack(
    pack_path: Path,
    schema_obj: dict[str, Any] | None,
    jsonschema_validator: Any | None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    """校验单个 JSON 数据包，返回 (errors, warnings, summary)。"""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(pack_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"JSON 解析失败: {exc}"], warnings, {}

    # 1. 若安装了 jsonschema，执行官方 Draft 2020-12 校验
    if jsonschema_validator is not None and schema_obj is not None:
        for err in jsonschema_validator.iter_errors(data):
            loc = ".".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"[Schema:{loc}] {err.message}")

    # 2. 内置零依赖结构与枚举校验
    required_top = {"schema_version", "metadata", "formulas", "derivations"}
    missing_top = required_top - set(data.keys())
    extra_top = set(data.keys()) - required_top
    if missing_top:
        errors.append(f"缺少顶层必填字段: {sorted(missing_top)}")
    if extra_top:
        errors.append(f"存在未允许的顶层字段: {sorted(extra_top)}")

    if not isinstance(data.get("schema_version"), str) or not RE_SEMVER.match(data["schema_version"]):
        errors.append(f"schema_version 格式无效: {data.get('schema_version')}")

    meta = data.get("metadata", {})
    if not isinstance(meta, dict):
        errors.append("metadata 必须为对象")
    else:
        for k in ("pack_id", "title", "updated_at"):
            if not isinstance(meta.get(k), str) or not meta[k].strip():
                errors.append(f"metadata 缺少非空字段: {k}")
        if isinstance(meta.get("updated_at"), str) and not RE_DATE.match(meta["updated_at"]):
            errors.append(f"metadata.updated_at 日期格式应为 YYYY-MM-DD: {meta.get('updated_at')}")

    formulas = data.get("formulas", [])
    derivations = data.get("derivations", [])
    if not isinstance(formulas, list) or len(formulas) == 0:
        errors.append("formulas 必须为非空数组")
        return errors, warnings, {}
    if not isinstance(derivations, list):
        errors.append("derivations 必须为数组")
        return errors, warnings, {}

    # 3. 公式节点校验
    formula_ids: set[str] = set()
    req_f_keys = {"id", "name", "latex", "taxonomy", "variables", "conditions", "review"}
    allowed_f_keys = req_f_keys | {"aliases", "statement"}

    for idx, f in enumerate(formulas):
        if not isinstance(f, dict):
            errors.append(f"formulas[{idx}] 必须为对象")
            continue
        fid = f.get("id", f"<formulas[{idx}]>")
        missing_f = req_f_keys - set(f.keys())
        extra_f = set(f.keys()) - allowed_f_keys
        if missing_f:
            errors.append(f"[{fid}] 缺少公式必填字段: {sorted(missing_f)}")
        if extra_f:
            errors.append(f"[{fid}] 存在未定义公式字段: {sorted(extra_f)}")
        if not isinstance(fid, str) or not RE_FORMULA_ID.match(fid):
            errors.append(f"[{fid}] 公式 ID 不符合 <discipline>.<subdomain>.<slug> 规范")
        elif fid in formula_ids:
            errors.append(f"[{fid}] 公式 ID 重复")
        else:
            formula_ids.add(fid)

        tax = f.get("taxonomy", {})
        if isinstance(tax, dict):
            discs = tax.get("disciplines", [])
            stages = tax.get("education_stages", [])
            topics = tax.get("topics", [])
            if not discs or not set(discs).issubset(VALID_DISCIPLINES):
                errors.append(f"[{fid}] taxonomy.disciplines 非法: {discs}")
            if not stages or not set(stages).issubset(VALID_STAGES):
                errors.append(f"[{fid}] taxonomy.education_stages 非法: {stages}")
            if not isinstance(topics, list) or not topics:
                errors.append(f"[{fid}] taxonomy.topics 必须为非空数组")

        for v_idx, var in enumerate(f.get("variables", [])):
            if not isinstance(var, dict):
                errors.append(f"[{fid}] variables[{v_idx}] 必须为对象")
                continue
            for vk in ("symbol", "name", "math_type", "domain"):
                if not isinstance(var.get(vk), str) or not var[vk].strip():
                    errors.append(f"[{fid}] variables[{v_idx}] 缺少字段: {vk}")
            if var.get("math_type") not in VALID_MATH_TYPES:
                errors.append(f"[{fid}] variables[{v_idx}] math_type 非法: {var.get('math_type')}")

        rev = f.get("review", {})
        if not isinstance(rev, dict) or rev.get("status") not in VALID_REVIEW_STATUS:
            errors.append(f"[{fid}] review.status 非法: {rev.get('status') if isinstance(rev, dict) else rev}")

    # 4. 推导边校验 + 邻接图构建
    deriv_ids: set[str] = set()
    in_deg: dict[str, int] = {fid: 0 for fid in formula_ids}
    out_deg: dict[str, int] = {fid: 0 for fid in formula_ids}
    undirected_adj: dict[str, set[str]] = defaultdict(set)

    req_d_keys = {
        "id",
        "from_formula_ids",
        "to_formula_id",
        "relation_type",
        "dependency_site",
        "bidirectional",
        "levels",
    }
    allowed_d_keys = req_d_keys | {"inference_rules"}

    for idx, d in enumerate(derivations):
        if not isinstance(d, dict):
            errors.append(f"derivations[{idx}] 必须为对象")
            continue
        did = d.get("id", f"<derivations[{idx}]>")
        missing_d = req_d_keys - set(d.keys())
        extra_d = set(d.keys()) - allowed_d_keys
        if missing_d:
            errors.append(f"[{did}] 缺少推导必填字段: {sorted(missing_d)}")
        if extra_d:
            errors.append(f"[{did}] 存在未定义推导字段: {sorted(extra_d)}")
        if not isinstance(did, str) or not RE_DERIV_ID.match(did):
            errors.append(f"[{did}] 推导 ID 不符合 deriv.<subdomain>.<slug> 规范")
        elif did in deriv_ids:
            errors.append(f"[{did}] 推导 ID 重复")
        else:
            deriv_ids.add(did)

        if d.get("relation_type") not in VALID_RELATION_TYPES:
            errors.append(f"[{did}] relation_type 非法: {d.get('relation_type')}")
        if d.get("dependency_site") not in VALID_DEP_SITES:
            errors.append(f"[{did}] dependency_site 非法: {d.get('dependency_site')}")
        if not isinstance(d.get("bidirectional"), bool):
            errors.append(f"[{did}] bidirectional 必须为布尔值")

        from_ids = d.get("from_formula_ids", [])
        to_id = d.get("to_formula_id")
        if not isinstance(from_ids, list) or len(from_ids) == 0:
            errors.append(f"[{did}] from_formula_ids 必须为非空数组")
        else:
            if to_id not in formula_ids:
                errors.append(f"[{did}] 悬空引用 to_formula_id: {to_id}")
            for fid in from_ids:
                if fid not in formula_ids:
                    errors.append(f"[{did}] 悬空引用 from_formula_id: {fid}")
                elif fid == to_id:
                    errors.append(f"[{did}] 检测到自环推导: {fid} -> {to_id}")
                elif to_id in formula_ids:
                    out_deg[fid] += 1
                    in_deg[to_id] += 1
                    undirected_adj[fid].add(to_id)
                    undirected_adj[to_id].add(fid)

        levels = d.get("levels", {})
        if not isinstance(levels, dict):
            errors.append(f"[{did}] levels 必须为对象")
        else:
            if not isinstance(levels.get("L1_summary"), str) or not levels["L1_summary"].strip():
                errors.append(f"[{did}] levels.L1_summary 必须为非空字符串")
            validate_steps(levels.get("L2_standard"), "L2_standard", did, formula_ids, errors, warnings)
            validate_steps(levels.get("L3_detailed"), "L3_detailed", did, formula_ids, errors, warnings)

    # 5. 孤立节点与连通分量检测
    isolated = sorted(fid for fid in formula_ids if in_deg[fid] == 0 and out_deg[fid] == 0)
    if isolated:
        warnings.append(f"存在 {len(isolated)} 个孤立节点（无任何入边或出边）: {isolated}")

    visited: set[str] = set()
    components = 0
    for fid in formula_ids:
        if fid in visited:
            continue
        components += 1
        queue = deque([fid])
        visited.add(fid)
        while queue:
            cur = queue.popleft()
            for nxt in undirected_adj[cur]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

    summary = {
        "pack_id": meta.get("pack_id", pack_path.stem),
        "formula_count": len(formulas),
        "derivation_count": len(derivations),
        "multi_premise_count": sum(1 for d in derivations if len(d.get("from_formula_ids", [])) > 1),
        "isolated_count": len(isolated),
        "connected_components": components,
        "formula_ids": formula_ids,
        "derivation_ids": deriv_ids,
    }
    return errors, warnings, summary


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"
    schema_path = repo_root / "schema" / "formula-graph.v1.schema.json"

    schema_obj = None
    jsonschema_validator = None
    if schema_path.exists():
        schema_obj = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            import jsonschema  # type: ignore

            jsonschema_validator = jsonschema.Draft202012Validator(schema_obj)
            schema_mode = "内置校验 + jsonschema (Draft 2020-12)"
        except ImportError:
            schema_mode = "内置零依赖校验（未安装 jsonschema）"
    else:
        schema_mode = "内置零依赖校验（未找到 schema 文件）"

    pack_files = sorted(data_dir.rglob("*.json"))
    if not pack_files:
        print("未在 data/ 目录下找到任何 JSON 数据包。")
        return 1

    print(f"=== Formula Graph 数据包校验开始（模式：{schema_mode}）===\n")

    total_errors = 0
    total_warnings = 0
    total_formulas = 0
    total_derivations = 0
    global_formula_owners: dict[str, list[str]] = defaultdict(list)
    global_deriv_owners: dict[str, list[str]] = defaultdict(list)

    for pf in pack_files:
        rel = pf.relative_to(repo_root)
        errs, warns, summary = validate_pack(pf, schema_obj, jsonschema_validator)
        status = "PASS" if not errs else "FAIL"
        print(
            f"[{status}] {rel} | "
            f"公式 {summary.get('formula_count', 0)} 个 · "
            f"推导 {summary.get('derivation_count', 0)} 条（多前提 {summary.get('multi_premise_count', 0)}）· "
            f"连通分量 {summary.get('connected_components', 0)} · "
            f"孤立节点 {summary.get('isolated_count', 0)}"
        )
        for e in errs:
            print(f"  [ERROR] {e}")
        for w in warns:
            print(f"  [WARN]  {w}")

        total_errors += len(errs)
        total_warnings += len(warns)
        total_formulas += summary.get("formula_count", 0)
        total_derivations += summary.get("derivation_count", 0)
        for fid in summary.get("formula_ids", set()):
            global_formula_owners[fid].append(str(rel))
        for did in summary.get("derivation_ids", set()):
            global_deriv_owners[did].append(str(rel))

    # 跨数据包全局 ID 冲突检测
    dup_formulas = {k: v for k, v in global_formula_owners.items() if len(v) > 1}
    dup_derivs = {k: v for k, v in global_deriv_owners.items() if len(v) > 1}
    if dup_formulas or dup_derivs:
        print("\n[跨包 ID 重叠提示]")
        for fid, owners in dup_formulas.items():
            print(f"  [WARN] 公式 ID 跨包复用: {fid} -> {owners}")
            total_warnings += 1
        for did, owners in dup_derivs.items():
            print(f"  [ERROR] 推导 ID 跨包冲突: {did} -> {owners}")
            total_errors += 1

    print(
        f"\n=== 校验汇总：{len(pack_files)} 个数据包 | "
        f"累计 {total_formulas} 公式 / {total_derivations} 推导 | "
        f"{total_errors} 错误 / {total_warnings} 警告 ==="
    )
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
