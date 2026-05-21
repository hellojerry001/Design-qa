#!/usr/bin/env python3
import argparse
import json
import re
from typing import Any, Dict, List

STYLE_KEYS = {
    "color", "background", "backgroundColor", "fontFamily", "fontSize", "fontWeight",
    "lineHeight", "letterSpacing", "borderRadius", "boxShadow", "margin", "marginTop",
    "marginRight", "marginBottom", "marginLeft", "padding", "paddingTop", "paddingRight",
    "paddingBottom", "paddingLeft", "gap", "width", "height", "position", "top", "left",
    "right", "bottom", "display", "flex", "flexGrow", "flexShrink", "flexDirection",
    "justifyContent", "alignItems", "border", "borderWidth", "borderStyle", "borderColor",
    "overflow", "opacity"
}
IGNORE_KEYS = {"text", "content", "label", "title", "children", "items"}
ADAPTIVE_LAYOUT_KEYS = {"width", "height", "top", "left", "right", "bottom"}


def normalize(v: Any) -> Any:
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v.strip())
    return v


def extract_style(node: Dict[str, Any]) -> Dict[str, Any]:
    style = {}
    inline = node.get("style")
    if isinstance(inline, dict):
        for k, v in inline.items():
            if k in STYLE_KEYS:
                style[k] = normalize(v)
    for k, v in node.items():
        if k in IGNORE_KEYS:
            continue
        if k in STYLE_KEYS:
            style[k] = normalize(v)
    if "class" in node and isinstance(node["class"], str):
        style["class"] = normalize(node["class"])
    return style


def node_children(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    children = node.get("children", [])
    return [c for c in children if isinstance(c, dict)]


def node_name(node: Dict[str, Any], idx: int) -> str:
    nid = node.get("id")
    cls = node.get("class")
    typ = node.get("type", "node")
    if nid:
        return f"{typ}#{nid}"
    if cls:
        short_cls = " ".join(str(cls).split()[:3])
        return f"{typ}.{short_cls}"
    return f"{typ}[{idx}]"


def looks_like_shell(node: Dict[str, Any]) -> bool:
    cls = str(node.get("class", ""))
    shell_hints = {
        "sidebar", "header", "footer", "layout", "shell", "framework",
        "app-shell", "navigation", "nav", "container-fluid"
    }
    class_tokens = {t.strip().lower() for t in cls.split()}
    return bool(shell_hints & class_tokens)


def is_adaptive_value(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    vv = v.strip().lower()
    adaptive_tokens = {
        "auto", "fit-content", "max-content", "min-content", "inherit", "initial",
        "unset", "normal"
    }
    return (
        vv in adaptive_tokens
        or "%" in vv
        or "vw" in vv
        or "vh" in vv
        or "calc(" in vv
        or "var(" in vv
    )


def should_ignore_diff(
    key: str,
    dv: Any,
    iv: Any,
    design_node: Dict[str, Any],
    impl_node: Dict[str, Any],
    ignore_adaptive: bool,
    ignore_shell: bool,
) -> bool:
    if ignore_shell and (looks_like_shell(design_node) or looks_like_shell(impl_node)):
        return True
    if key == "class":
        return True
    if ignore_adaptive and key in ADAPTIVE_LAYOUT_KEYS and (is_adaptive_value(dv) or is_adaptive_value(iv)):
        return True
    return False


def severity_for_key(key: str) -> str:
    high = {"width", "height", "position", "top", "left", "right", "bottom", "color", "background", "backgroundColor", "fontSize", "fontWeight"}
    medium = {"padding", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "margin", "marginTop", "marginRight", "marginBottom", "marginLeft", "gap", "lineHeight", "letterSpacing", "borderRadius", "borderColor", "borderWidth"}
    if key in high:
        return "高"
    if key in medium:
        return "中"
    return "低"


def advice_for_key(key: str, design_val: Any) -> str:
    return f"将 `{key}` 调整为设计稿值 `{design_val}`，并与设计 token 保持一致。"


def compare_nodes(
    design: Dict[str, Any],
    impl: Dict[str, Any],
    path: str,
    rows: List[Dict[str, str]],
    ignore_adaptive: bool,
    ignore_shell: bool,
) -> None:
    d_style = extract_style(design)
    i_style = extract_style(impl)

    all_keys = sorted(set(d_style.keys()) | set(i_style.keys()))
    for k in all_keys:
        dv = d_style.get(k)
        iv = i_style.get(k)
        if dv != iv and not should_ignore_diff(k, dv, iv, design, impl, ignore_adaptive, ignore_shell):
            rows.append({
                "问题位置": path,
                "问题描述": f"样式 `{k}` 不一致：设计稿=`{dv}`，开发实现=`{iv}`",
                "修改建议": advice_for_key(k, dv),
                "优先级": severity_for_key(k),
                "备注": "仅样式差异，已忽略文案内容"
            })

    d_children = node_children(design)
    i_children = node_children(impl)
    max_len = max(len(d_children), len(i_children))

    for idx in range(max_len):
        if idx >= len(d_children):
            if not ignore_shell:
                rows.append({
                    "问题位置": f"{path} > child[{idx}]",
                    "问题描述": "开发实现存在设计稿未包含的额外节点（可能引入额外样式影响）",
                    "修改建议": "确认是否为预期扩展；非预期则移除或隐藏该节点。",
                    "优先级": "中",
                    "备注": "结构差异可能导致样式偏差"
                })
            continue
        if idx >= len(i_children):
            if not ignore_shell:
                rows.append({
                    "问题位置": f"{path} > child[{idx}]",
                    "问题描述": "设计稿节点在开发实现中缺失",
                    "修改建议": "补齐对应节点并应用设计稿样式。",
                    "优先级": "高",
                    "备注": "结构缺失"
                })
            continue

        d_child = d_children[idx]
        i_child = i_children[idx]
        child_path = f"{path} > {node_name(d_child, idx)}"
        compare_nodes(d_child, i_child, child_path, rows, ignore_adaptive, ignore_shell)


def render_markdown(rows: List[Dict[str, str]]) -> str:
    header = "| 问题位置 | 问题描述 | 修改建议 | 优先级 | 备注 |\n|---|---|---|---|---|"
    lines = [header]
    for r in rows:
        lines.append(
            f"| {r['问题位置']} | {r['问题描述']} | {r['修改建议']} | {r['优先级']} | {r['备注']} |"
        )
    if not rows:
        lines.append("| - | 未发现样式差异 | - | - | 可判定为样式通过 |")
    return "\n".join(lines)


def render_summary(rows: List[Dict[str, str]]) -> str:
    total = len(rows)
    high = sum(1 for r in rows if r["优先级"] == "高")
    medium = sum(1 for r in rows if r["优先级"] == "中")
    low = sum(1 for r in rows if r["优先级"] == "低")
    return f"差异总数：{total}（高：{high}，中：{medium}，低：{low}）"


def main() -> None:
    p = argparse.ArgumentParser(description="Compare style differences between design and implementation JSON")
    p.add_argument("--design", required=True, help="Path to design JSON")
    p.add_argument("--impl", required=True, help="Path to implementation JSON")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--no-ignore-adaptive", action="store_true", help="Do not ignore adaptive layout diffs")
    p.add_argument("--no-ignore-shell", action="store_true", help="Do not ignore framework shell/container diffs")
    args = p.parse_args()

    with open(args.design, "r", encoding="utf-8") as f:
        design = json.load(f)
    with open(args.impl, "r", encoding="utf-8") as f:
        impl = json.load(f)

    rows: List[Dict[str, str]] = []
    compare_nodes(
        design,
        impl,
        "root",
        rows,
        ignore_adaptive=not args.no_ignore_adaptive,
        ignore_shell=not args.no_ignore_shell,
    )

    if args.format == "json":
        print(json.dumps({"summary": render_summary(rows), "rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(render_summary(rows))
        print()
        print(render_markdown(rows))


if __name__ == "__main__":
    main()
