---
name: acceptance-style-audit
description: 对比开发实现 JSON 与设计稿 HTML/JSON（自动将 HTML 转 JSON），仅聚焦颜色、字体、圆角、投影、间距等样式差异，忽略文案差异，输出结构化验收报告表格（问题位置、问题描述、修改建议、优先级、备注）。当用户提到样式验收、还原度对比、设计走查、UI QA、生成验收表时使用。
---

# Acceptance Style Audit

用于 UI 样式验收的专用 skill：输入「开发实现 JSON」与「设计稿 HTML 或 JSON」，自动产出仅包含样式差异的验收报告。

## 适用场景

- 用户上传两份 JSON，要求验收还原度
- 用户要求只看样式差异，不看文案差异
- 用户要表格化报告（可贴 Jira/飞书）

## 输出要求

报告必须使用以下表头：

- 问题位置
- 问题描述
- 修改建议
- 优先级
- 备注

## 忽略项（默认）

- 所有文案字段：`text`、`content`、`label`、`title`（仅文本含义）
- 动态业务数据值（如数字内容本身）
- 框架壳层差异（外部导航、侧栏、页面容器等非目标元素）
- 自适应宽高导致的差异（`%`/`vw`/`vh`/`calc()`/`var()`/`auto` 等）

## 对比维度

必须对比以下样式维度（存在则比）：

1. 颜色：文本色、背景色、边框色、透明度
2. 字体：font-family、font-size、font-weight、line-height、letter-spacing
3. 圆角：border-radius
4. 投影：box-shadow
5. 间距：margin、padding、gap
6. 尺寸与布局：width、height、position、top/left/right/bottom、display、flex 相关
7. 边框：border-width/style/color

## 优先级判定规则

- 高：影响布局结构或明显视觉层级（尺寸、定位、主色、关键字体）
- 中：局部视觉偏差（间距、次要字体参数、圆角轻微不一致）
- 低：状态样式或非关键细节（hover 态、可容忍细节差异）

## 工作流程

1. 要求用户提供：
- 开发实现 JSON
- 设计稿 HTML 或 JSON/样式规则

2. 若设计稿是 HTML，先转 JSON：
`python3 scripts/html_to_json.py --input design.html --output design.json`

3. 运行对比脚本：
`python3 scripts/compare_style_json.py --design design.json --impl impl.json --format markdown`

4. 若用户提供的是片段而非完整 JSON：
- 先抽取同层级节点
- 使用 `path` 或 `class/id` 做节点定位
- 无法一一映射时在“备注”中标注“映射不确定”

5. 输出验收表格，并附：
- 差异总数
- 高/中/低数量统计
- 是否可发布建议（可选）
- 不输出一致项，只输出差异项

6. 需要“差异点截图”时，使用精准标注流程（强制）：
- 必须在**同一时刻**获取 DOM `getBoundingClientRect()` 与截图
- 不能用“另一时刻”的截图去标注“当前坐标”
- 使用 viewport 尺寸和截图尺寸做坐标换算：`sx = imageWidth / innerWidth`，`sy = imageHeight / innerHeight`
- 若截图分辨率受 DPR 影响（如 2x），通过上面的 `sx/sy` 自动吸收，不要手工猜偏移
- 优先标注目标业务容器内元素，避免把框架壳层（侧栏/顶栏）误当偏移

## 命令示例

```bash
python3 scripts/run_acceptance.py \
  --impl-json /path/to/impl.json \
  --design-html /path/to/design.html \
  --format markdown

# 或分步执行
python3 scripts/html_to_json.py \
  --input /path/to/design.html \
  --output /tmp/design.json

python3 scripts/compare_style_json.py \
  --design /tmp/design.json \
  --impl /path/to/impl.json \
  --format markdown

# 如需强制对比自适应尺寸或框架壳层，可关闭默认忽略策略
python3 scripts/compare_style_json.py \
  --design examples/design.json \
  --impl examples/impl.json \
  --format markdown \
  --no-ignore-adaptive \
  --no-ignore-shell

# 精准差异标注图（同帧坐标 + 同帧截图）
python3 scripts/annotate_precise_rects.py \
  --image /path/to/web-viewport.png \
  --metrics /path/to/web-metrics.json \
  --output /path/to/web-annotated.png \
  --show-root
```

## 资源

- 对比脚本：`scripts/compare_style_json.py`
- HTML 转 JSON：`scripts/html_to_json.py`
- 一键验收：`scripts/run_acceptance.py`
- 精准标注脚本：`scripts/annotate_precise_rects.py`
- 报告模板：`references/report-template.md`
- 示例输入：`examples/design.json`、`examples/impl.json`
