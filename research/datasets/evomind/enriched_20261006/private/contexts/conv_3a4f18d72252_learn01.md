# 从 docx 制作演讲 PPT

会话：conv_3a4f18d72252；候选：conv_3a4f18d72252:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：先转成可核对的文本，再生成大纲与演讲意图，选择下游渲染器进行逐页渲染，最后检查输出；安装声明不算学习结果

边界：历史执行顺序未核准；任务成功及新任务复用收益未独立验证

## 原筛选种子 · 用户

u_363497c2213ba08adb

帮我使用这个skill 根据我的这个markdown 文件做一个PPT

## 原筛选种子 · 用户

u_30e79e5d9fd18ac36f

用这个docx就可以了

## 原筛选种子 · 用户

u_3660f7244b7416c92f

帮我根据这个docx 绘制PPT的图片，然后一页一页画出来

## 原筛选种子 · AI

a_0e4518f14fb81893e2

先做个全貌规划，再一步步来。

**步骤：**
1. ✅ 将 docx 转成 markdown（确认内容）
2. ✅ 安装下游渲染 skill（`guizang-ppt-skill`）
3. ✅ 运行 Humanize PPT — 出 AST 大纲、演讲意图、pproduction brief
4. ✅ 用 guizang-ppt-skill 渲染出 HTML PPT
5. ✅ 输出最终产物到成果文件夹

动手：内容已转成 markdown——这是一份非常完整的 **AI + 病理数据创业调研报告**（中文）。现在装下游渲染 skill，然后跑 Humanize PPT 全流程。Humanize PPT 已经成功跑完了 Brief 模式，生成了完整的 outline。让我看看产出的关键文件。All 15 slides are properly built. The extra `<section>` in the grep was from a comment — harmless. Let me now write the slide plan and verify the HTML is well-formed, then deliver the final summary.全部完成！让整理产出物清单：

---

**全流程跑通 ✓**

### 🏗 安装的 skills
| Skill | 作用 |
|-------|------|
| `humanize-ppt` ✅ | AST 大纲导演 + 演讲体检 |
| `guizang-ppt-skill` ✅ | 中文 deck 原生渲染（瑞士国际主义风） |

### 📦 产出物（在成果文件夹）

**Humanize PPT 契约层：**
- `humanize-output-v2/ast_outline.md` — 观众状态转移大纲（Hook→Context→Tension→Method→Proof）
- `humanize-output-v2/slide_plan.json` — 逐页媒体决策（配图/SVG/视频）
- `humanize-output-v2/speaker_intent.md` — 每页演讲稿语义
- `humanize-output-v2/guizang-production-prompt.md` — 下游渲染生产指令
- `humanize-output-v2/deck_brief.md` — 观众画像 + 目标 + 核心张力

**瑞士风 Deck 渲染层（直接浏览器打开）：**
- `ppt/index.html` — **15 页单文件 HTML PPT**

### 🎨 设计风格
- **瑞士国际主义风（Style B）** — 克莱因蓝 IKB
- 封面/封底：IKB 满屏 + ASCII 点阵呼吸场
- 15 页覆盖：市场机遇 → TAM/SAM/SOM → 竞品矩阵 → 四象限空白区 → 商业模式 → SWOT → 产品创意 → 三年路线图 → 行动策略
- 快捷键：`← →` 翻页 · `B` 切换低功耗 · `ESC` 索引视图

用浏览器打开就能看。要不要我做一些后续操作，比如：

1. **跑演讲体检** — 用 `--qa-from` 检查渲染结果
2. **加配图** — 装 `baoyu-image-gen` 给封面/S01 配实景图
3. **部署到 GitHub Pages** 方便分享
