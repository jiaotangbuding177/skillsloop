---
name: remotion-video-generator
description: 完整的 AI 视频生产编排器——根据用户一句话需求，自动完成内容理解、视频策划、分镜设计、AI 素材生成、AI 配音（Edge TTS）、字幕、Remotion 动画、音乐/音效（可选）、预览检查、正式渲染与成片 QA，最终交付 MP4。本技能面向平台化使用，不绑定任何个人账号/邮箱/私有配置，全部凭据走环境变量。触发词：生成视频、做个视频、制作视频、渲染视频、视频生成、宣传视频、教程视频、讲解视频、产品视频、AI 配音、字幕、video。
---

# AI 视频生产编排器（Remotion + AI 素材 + AI 配音）

根据用户描述（"想做什么视频"）自动完成一条正式、可交付的视频。用户不需要理解 Remotion、React 或视频工程。

> 定位：这是**上层视频制作 Skill**。涉及 Remotion 具体技术实现时，参考已安装的官方 Remotion Skills（remotion-best-practices / remotion-create / remotion-markup / remotion-render / remotion-studio / remotion-captions / remotion-multimedia），不要重复实现官方已解决的底层问题。

## 1. 总体原则

成片应该让用户感觉"这是一条经过策划、设计和剪辑的视频"，而不是"AI 把图片和文字渲染了一遍"。

- 完整的视频结构：开场 Hook → 内容主体 → 结尾收束
- 清晰的信息层级、统一的视觉语言、有节奏的镜头变化
- 动画服务于内容，不堆砌廉价特效
- 讲解类视频默认 AI 配音 + 字幕；品牌视觉片默认音乐感优先
- 素材质量、文字可读性、声音设计都要达到可交付标准
- **禁止所有视频都套用"渐变背景 + 大标题 + 图片缩放 + 淡入淡出"模板**

## 2. 标准工作流

```
内容理解 → Creative Direction(简报/母题/分镜) → 素材整理 → AI 素材生成
        → AI 配音(词级时间轴) → Caption Composer(语义分块) → 字幕(句级/关键词/词级)
        → Remotion 动画 → BGM(Preset 合成/许可证过滤+平滑Ducking) → 音效(可选)
        → 预览/关键帧检查 → 正式渲染 → 成片 QA → 交付
```

### 2.0 Creative Director / Storyboard Director（强制前置步骤）

接到"制作视频"任务后，**不得直接"生成图片 → 写 TSX → 渲染"**。必须先完成一次内部 Creative Direction，产出物为创意简报（参考 `<skill目录>/references/creative-brief-template.md`）：

- **Creative Concept**：一句话视觉母题（如"数据在空间中逐层展开""从混乱信息到清晰结果"），整条视频贯穿，不要每个 Scene 独立设计。
- **Visual Motif**：贯穿元素（光线/网格/数据节点/文档卡/光影材质……），统一设计语言。
- **Storyboard**：逐 Scene 明确——为什么存在、观众看哪里、是否配音/字幕、用 AI 图还是真实素材、镜头运动、转场、BGM 情绪。避免机械的"标题→图片→文字→图片→Logo"模板。
- **音乐属于 Creative Direction**：分镜阶段就确定 BGM 情绪曲线（开场建立氛围/核心稳定/结论提升/复杂讲解降低/片尾收束），"安静"也是声音设计。
- 依据创意简报自动输出模块开关（AI Image / Voiceover / Subtitle / BGM / SFX）。

### 2.0.1 Duration Planner（时长规划）

**不要默认把视频压缩到 10~15 秒。** 根据内容复杂度决定时长：

| 内容 | 建议时长 |
|---|---|
| Logo 动画 / 单产品氛围片 / 简单社交素材 | 5~15s |
| 单产品卖点 / 单功能 / 简单品牌宣传 | 20~30s |
| 软件 Demo / AI 系统介绍 / 报告摘要 / 企业介绍 | 30~60s |
| 教程 / 深度讲解 | 60s+（按内容需要） |

**时长由 Voiceover 反推**：先定内容结构与配音稿 → TTS 实测时长 → Scene 时长 = 配音 + 0.5~1.5s 理解留白 + 转场 + 开场/片尾。不要为了渲染时间牺牲内容完整度，不要画面追着旁白跑。

### 2.0.2 Scene Diversity Planner（场景多样性）

禁止连续多个 Scene 同构（如全是"背景图+标题"）。Creative Director 必须为每个 Scene 指定 `scene_type` 并避免连续重复。支持类型（≥16 种）：hero / fullscreen-visual / split-screen / ui-demo / data-card / kpi / quote / timeline / comparison / before-after / process-flow / feature-highlight / product-closeup / ai-broll / diagram / document-zoom / fullscreen-typography / ending。

### 2.0.3 Shot Planner（镜头规划）

一个 Scene 可包含多个 Shot。每个 Shot 明确：duration / focus（观众看哪里）/ camera movement / animation / transition / visual priority。示例（AI 系统研究流程 8s）：A 完整界面 → B 推近输入框 → C 局部放大 Agent 状态 → D 结果高亮 → E 拉远展示报告。

### 2.0.4 镜头运动规则

按内容选用：Slow Push In / Pull Out / Pan（横移/纵移）/ Parallax / Crop Zoom / Focus Shift / Mask Reveal / Camera Follow / Match Move / Layer Depth。**Ken Burns（scale 1→1.05）只是一种方式，不是唯一方式。** 每个 Scene 至少三层：Background（氛围/色彩/空间感）、Midground（图片/UI/图表/产品=主要视觉）、Foreground（标题/标签/高亮/字幕），不同层运动速度不同制造深度。

### 2.0.5 AI 素材不只做背景

按分镜生成：B-roll / 场景建立镜头 / 产品场景 / 概念视觉 / 特写 / 氛围转场 / 抽象隐喻 / 科技空间 / 数据视觉背景。**画面应表达旁白**（如讲"任务拆解"就画卡片分裂），而不是只给旁白配背景。

### 2.0.6 节奏与留白

- **Motion Density**：每 Scene 标 low/medium/high（结论=low、UI 操作=medium、蒙太奇=high），整条视频要有变化。
- **Visual Rhythm**：快→慢→快→收束，禁止所有 Scene 等长（如 4s×N）。
- **Pause / Breathing Space**：重要内容出现后留 0.5~1s 静默，高级感来自"少一点"。


### 2.1 内容理解与策划

先向用户确认（或从描述中提取）：视频目的、内容类型、目标受众、发布平台、横/竖/方比例、目标时长、是否讲解型、是否有用户素材。

生成内部视频方案，明确：主题、目的、观众、时长、比例、视觉方向、内容结构、配音策略、字幕策略、素材策略、音乐策略。**复杂视频必须先策划再动手，不要边写边想。**

### 2.2 分镜设计（Scene 规划）

每个 Scene 明确：目的、开始时间、持续时间、视觉元素、标题/辅助文案、素材、动画、镜头运动、转场、配音内容、字幕内容、音效、音乐状态。

常见节奏参考（不强制）：

| 场景 | 时长 | 作用 |
|---|---|---|
| Hook | 2~4s | 强视觉主体，快速建立主题 |
| Context/Problem | 3~7s | 说明背景或问题 |
| Core | 5~12s | 核心内容/功能/知识点，重点放大 |
| Result | 4~8s | 价值、结果、关键结论 |
| Ending | 2~5s | 总结、品牌、CTA 或核心结论 |

节奏规则：不要所有 Scene 等长；但也不要快到文案/UI/数据来不及看。**时间轴服务于内容和语音**（见 5.4 配音时长联动）。

### 2.3 模块自动判断

每次任务输出模块开关，不要默认全开：

```
AI Image: ON / OFF / 按需
Voiceover: ON / OFF
Subtitle: ON / OFF
Background Music: ON / OFF
Sound Effects: ON / OFF
Charts: ON / OFF
UI Highlight: ON / OFF
```

示例：教程/讲解/系统 Demo/报告解读 → Voiceover ON + Subtitle ON；产品视觉片 → Voiceover 可选 + Subtitle OFF；Logo Animation → 全关。

## 3. 环境检测（先跑，再动手）

```bash
bash <skill目录>/scripts/check_environment.sh
```

输出各组件状态（node/npm/git/python3/chromium/AI 图片密钥/Edge TTS/ffprobe/CJK 字体）。按结果决定启用哪些模块，缺失模块按第 10 节降级。

**平台化环境约定（推荐默认，不假设唯一）：**

- **npm registry**：默认用已配置镜像（如 npmmirror），不要改动。
- **GitHub 访问**：若直连失败，可用环境变量临时注入代理重写（只对单条命令生效，不改全局配置）：
  ```
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=url.<代理前缀>/https://github.com/.insteadOf GIT_CONFIG_VALUE_0=https://github.com/ <命令>
  ```
  代理前缀可用环境变量 `GIT_PROXY_URL` 指定（如 `https://gh-proxy.com`）。
- **Chromium**：优先 `CHROME_PATH` 环境变量；否则自动探测常见路径（/usr/bin/chromium 等）。渲染必须显式 `Config.setBrowserExecutable(<路径>)`，不要让 Remotion 下载 Headless Shell（除非网络允许）。
- **中文字体**：优先系统 CJK 字体（Noto Sans/Serif CJK SC、WenQuanYi 等）；无则先安装字体再渲染，防止文字变方块。
- **AI 图片 Provider**：环境变量 `IMAGE_API_KEY`（或 Provider 专属变量如 `ZZZ4AI_IMAGE_KEY`）+ `IMAGE_API_URL`（默认 `https://llmapi.zzz4ai.com/v1/images/generations`），模型固定 `gpt-image-2`。密钥绝不写入文件/日志/回复。
- **Python**：TTS 环境变量 `TTS_PYTHON` 可指定解释器；默认查找 `.venv-tts`（当前目录与脚本目录向上搜索）→ 系统 python3。

## 4. AI 素材生成（模块：AI Image）

### 4.1 何时用与优先级

用户已有真实素材（Logo/产品图/UI 截图/录屏/照片/视频等）→ **优先使用真实素材**。AI 素材负责补充、衔接、背景、氛围、抽象概念表达、B-roll。不要用 AI 图替换用户明确要求保留的真实内容。

### 4.2 统一视觉规范（生成前先定）

- 主色、辅助色、明暗关系、光线方向、材质、构图、焦段感、景深、时代感、品牌气质、风格（插画/摄影/3D/抽象）
- 同一条视频的 AI 素材必须像来自同一个视觉项目：色调、风格、时代感一致
- **AI 图片中不要生成文字**——文字一律由 Remotion 后期排版（中文清晰、字体统一、可编辑、不乱码）

### 4.3 生成命令

```bash
python3 <skill目录>/scripts/generate_image.py --prompt "<统一风格 + 主体 + 构图 + 无文字>" \
  --size 1536x1024 --quality high --out-dir <项目>/public --stem bg
```

尺寸建议：16:9 背景 `1536x1024` 或 `2048x1152`；方形 `1024x1024`；9:16 `1024x1536`。生成后用 image 工具检查质量与风格一致性，不满意重生成。

### 4.4 失败降级

AI 图片失败 → 用户素材 → SVG/CSS 图形 → 渐变/程序化背景 → 简洁几何视觉。**不允许因单张图失败导致整个视频失败。**

## 5. AI 配音模块（模块：Voiceover）

### 5.1 启用判断

默认启用配音：教程、知识讲解、软件功能介绍、系统 Demo、产品介绍、报告解读、企业介绍、课程、高信息密度视频。
通常不配音：纯视觉品牌片、Logo Animation、极短氛围片、纯音乐视频、用户明确不要配音。

### 5.2 安装与检测

```bash
bash <skill目录>/scripts/install_edge_tts.sh [venv_dir]
```

脚本逻辑：已安装直接退出 → 优先虚拟环境（默认 `.venv-tts`）→ 不破坏系统 Python（externally-managed 时用 venv + get-pip.py 引导）→ 安装后自动跑最小中文测试。**不要为装 TTS 修改防火墙/SSH/系统账户/安全策略/全局代理。**

### 5.3 音色选择（不锁定单一音色）

- 女声：`zh-CN-XiaoxiaoNeural`、`zh-CN-XiaoyiNeural`
- 男声：`zh-CN-YunxiNeural`、`zh-CN-YunjianNeural`、`zh-CN-YunyangNeural`
- 可用 `edge-tts --list-voices`（或 `python -m edge_tts --list-voices`）查询
- 企业/科技/系统介绍 → 稳重专业；教程/讲解 → 清楚自然；产品宣传 → 适度感染力；年轻化短视频 → 轻松稍快
- 用户明确指定音色/性别/语速时优先遵守

### 5.4 配音生成与时长联动

```bash
python3 <skill目录>/scripts/generate_voiceover.py \
  --text "<口语化配音稿>" --voice zh-CN-XiaoxiaoNeural \
  --rate +0% --volume +0% --pitch +0Hz \
  --out-dir <项目>/audio/voiceover --stem vo1
```

脚本使用 **Edge TTS Python API（Communicate, boundary="WordBoundary"）**，输出：
- `<stem>.mp3` — 配音音频
- `<stem>.vtt` — 句级字幕（兼容）
- `<stem>.captions.json` — **词级时间轴**：`{"text", "words": [{"text","start","end","duration"}], "sentences": [...], "boundary": "WordBoundary"}`（offset/duration 为 100ns 单位，已换算为秒）

**词级时间轴降级**：WordBoundary 无事件 → 自动回退 SentenceBoundary → 仍失败则按音频时长比例估算词位置（boundary 字段会如实标注实际使用方式）。

**配音稿处理**：不要把用户长文原样送 TTS。先改写为自然、简洁、口语化、句长适中的旁白；避免连续数字与特殊符号；屏幕标题与旁白互补，不要四个位置重复同一句。

**时长联动（关键）**：用 captions.json 末词 end（或 `get_audio_duration.py`）决定 Scene 时长 = 配音时长 + 0.5~0.8s 留白，再据此排 Sequence/字幕/动画时间轴。**禁止固定 Scene 3 秒然后硬塞 8 秒配音。**

## 6. 字幕模块（模块：Subtitle）

- **开关**：讲解型 + Voiceover ON → 默认 Subtitle ON。品牌视觉片/纯音乐/Logo 动画默认 OFF。用户明确指定时严格遵守。
- **时间轴来源**：优先使用 captions.json 的 **WordBoundary 词级时间轴**（Edge TTS 原生，不引入 Whisper 等外部对齐方案）；词级不可用时回退句级（VTT/SentenceBoundary）。
- **模式自动选择（不要所有视频都做成卡拉 OK 式动态字幕）**：

| 视频类型 | 字幕模式 |
|---|---|
| 企业视频 | sentence（句级整句） |
| 系统 Demo | sentence + keyword（关键词常亮高亮） |
| 知识讲解 | sentence + word（当前词轻高亮，其余弱化） |
| 短视频 | 允许 word（词级动态字幕，可加强对比） |
| 品牌视觉视频 | 默认不启用字幕 |

- **Remotion 组件**：`Captions` 组件支持三种模式（sentence / keyword-highlight / word-highlight），输入 captions.json，词时间按 fps 换算为帧，与 Scene 内配音同步。
- **Caption Composer（语义分组）**：不要把 WordBoundary 词级 token 机械逐词排版。按标点、语义、字符数（阅读速度）、画面宽度把词组合成易读字幕块（如"人工智能正在改变 / 内容生产方式"），keyword 模式支持多 token 关键词短语匹配（如"结构完整"= 结构+完整）。
- **内容**：字幕 = 配音内容，与旁白一致、顺序一致；字幕 = 说的话，Title/Label = 视觉信息，不重复堆叠。
- **设计**：中文清晰、字号足够、高对比度、不遮核心内容、不超安全区、长句断行、半透明底/轻描边。不要整段字幕从头显示到尾。

## 7. 音乐与音效（模块：BGM / SFX，可选）

### 7.1 BGM Provider（可扩展，按优先级）

1. 用户提供的音乐
2. 本地已验证授权音乐库（`audio/music/`，须登记 music_manifest.json）
3. CC0 / Public Domain 源（如 OpenGameArt CC0、Musopen 明确授权录音）
4. CC BY 源（如 Incompetech、FMA 明确 CC BY 且允许衍生/商用）
5. 其他明确允许视频使用的 Provider（如 Pixabay Music 可作 Optional，**不把其文件打包进开源 Skill**）

**不要自动使用授权状态未知的音乐。** 本技能自带兜底：`synthesize_bgm.py` 程序化合成原创音乐（无外部版权依赖、可离线、可商用）。

### 7.2 BGM Preset 系统（程序化合成）

按视频类型自动选择 Preset（每种可调 BPM / Key / 和弦进行 / 层组合 / 密度 / 能量 / 立体声宽度 / 滤波运动 / 混响 / Attack-Release / Master Gain）：

| Preset | 适合 | 特点 |
|---|---|---|
| ambient-tech | AI / 科技 / SaaS / 系统 Demo | Ambient Pad + Soft Pulse + 轻 Arpeggio，少鼓点 |
| corporate-clean | 企业介绍 / 商业汇报 | 明亮 Pluck + 软 Pad，稳定和声，积极克制 |
| documentary | 报告 / 研究 / 知识讲解 | 氛围 Pad + 稀疏 Piano，慢节奏，不抢旁白 |
| minimal-piano | 教程 / 教育 / 情绪化讲解 | 钢琴感 Pluck + 轻 Pad |
| premium-product | 产品宣传 / 品牌视觉 | 温暖质感 + 软 Pluck + 优雅 Pulse |
| cinematic-soft | 故事 / 发布会 / 重要结论 | 宽 Pad + 稀疏点缀 + 长混响 |
| warm-education | 课程 / 教育 | 温暖 Pad + 轻 Pluck |
| future-interface | AI Agent / 软件 / UI Demo | 强节奏 Arp + Pulse + Bass |

**复杂度自动判断**：Voiceover 多 → 少 Layer/少旋律/少鼓/稳定 Pad；纯视觉视频 → 可加 Pulse/Arp/节奏与更明显动态。不要让 BGM 与旁白抢注意力。

### 7.3 程序合成音频工程规范（防杂音/click/clipping）

- **ADSR 包络**：所有程序合成音符必须有 Attack/Sustain/Release，起止严格为 0。短音 Attack 10~30ms / Release 50~150ms；Pad Attack 300~1500ms / Release 500~2500ms。
- **禁止**：0→全幅瞬间出现、全幅→0 瞬间停止、逐采样随机 detune（会产生宽带噪声）、和弦硬切换。
- **Master Fade**：整条 BGM 结束前 2.5~3s Master Fade Out 到真 0（勿仅依赖 Remotion 截断）；开头 1s Fade In。
- **防 Clipping**：多 Layer 各设 gain，合成峰值保留 Headroom（≤ -3dBFS，实际目标 ≈ -4.4dBFS）；float 超范围必须经 Gain staging + 软限幅（tanh）处理，禁止硬裁切。
- **DC Offset**：程序波形围绕 0 对称；合成后做 DC Removal。
- **声道**：立体声宽度通过双声部 detune/pan 实现；采样率统一 44100Hz 16bit。
- 合成后用 `audio_qa.py` 验证：Peak/RMS/DC/Clipping/Click 跳变/首尾归零。

### 7.4 许可证过滤（自动）

| 许可 | 处理 |
|---|---|
| CC0 / Public Domain / CC BY | ✅ 允许；CC BY 必须保存 Attribution 并写入 credits.txt |
| CC BY-SA | ⚠️ 谨慎：默认仅个人使用，商用前需确认 |
| CC BY-NC / CC BY-ND / CC BY-NC-ND / Unknown | ❌ 默认拒绝用于商业视频 |
| License Unknown | ❌ 宁可不加 BGM |

### 7.5 音乐元数据与追溯（逐 Track 记录）

`update_manifest.py` 维护：
- **music_manifest.json**：**每首 Track 单独记录**（禁止整体描述），含 id / title / artist / local file / source / source_url / generator / external_samples / license / commercial_use / derivatives / attribution_required / attribution / mood / genre / energy / instrumental / duration。示例：
  ```json
  {"id": "bgm-001", "title": "Ambient Tech 001", "source": "procedural-generator",
   "generator": "synthesize_bgm.py", "external_samples": false,
   "license": "CC0-1.0", "commercial_use": true, "attribution_required": false}
  ```
  外部音乐必须分别记录 title / artist / source / source_url / license / commercial_use / derivatives / attribution_required / attribution_text；无法确认 License 的音乐不使用。
- **credits.txt**：使用了需署名的第三方音乐时生成（含 Attribution）
- **media-manifest.json**：完整素材追溯（音乐 + 图片 + 配音 + 字体 + 来源 + 许可）

### 7.6 BGM 自动选择

按视频类型自动选 Preset：AI/科技 Demo → ambient-tech / future-interface（BGM Low）；企业介绍 → corporate-clean（Low/Medium）；报告解读 → documentary（Very Low）；教程 → warm-education / minimal-piano（Low）；产品宣传 → premium-product（Medium）；Cinematic → cinematic-soft（Medium/High）。优先 instrumental；**存在 Voiceover 时避免 Vocal、过强鼓点、高频旋律过密**。默认整条视频保持一首 BGM 连续，不每个 Scene 换歌。

### 7.7 自动混音（平滑 Ducking）

Remotion `<Audio volume={fn}>` 逐帧包络实现：
- **优先级：Voiceover(1.0) > 内容 SFX > BGM**
- 存在 Voiceover：BGM 基量 ~0.5，旁白区间自动压低到 ~0.2（duckFactor）
- **平滑包络（禁止硬切）**：Ducking Attack 150~400ms（默认 ~250ms）、Ducking Release 300~800ms（默认 500ms）
- **防 Pumping**：两段旁白间隔 < 0.8s 时合并区间，不完全恢复再立即 Duck
- BGM 开头 Fade In（~1s）、结尾 Fade Out（~1.5s，与 BGM 文件 Master Fade 叠加）
- 无 Voiceover 的视觉视频：BGM 基量可提高到 ~0.85

### 7.8 BGM Director（音乐导演）

Creative Director 在制作前输出 **Music Brief**：mood / energy / tempo / instrumentation / density / beginning / middle / climax / ending。例如 AI 系统 Demo：Mood=专业未来克制；Energy=Low→Medium→Low；Beginning=轻 ambient；Middle=增加 pulse；Key Feature=增加 arpeggio/harmonic lift；Ending=减少 layer 平滑收束。**不要整条视频音乐完全相同。**

### 7.9 Music Sections（音乐段落）

程序化 BGM 支持 Intro / A / B / Highlight / Outro，各段可改变 Layer/Energy/Filter/Chord Voicing/Density，但保持同一音乐主题（同一和声进行与音色）：

```bash
python3 <skill目录>/scripts/synthesize_bgm.py --preset ambient-tech --duration 36 \
  --sections "0-4:intro,4-16:a,16-25:b,25-31:highlight,31-36:outro"
```

**BGM 与 Scene 对齐**：音乐结构对应视频结构（Intro=开场、A/B=主体、Highlight=核心亮点/重要镜头、Outro=片尾）。不要每次切镜都变音乐。

### 7.10 BGM 自动匹配评分

不要只按视频标签选 Preset。使用 `select_bgm.py` 综合评分：Video Type / Voiceover Density / Mood / Energy / Audience / Scene Pace / Brand Tone。

```bash
python3 <skill目录>/scripts/select_bgm.py --video-type report --voiceover-density high
```

（报告+高旁白 → documentary；AI 产品+中等旁白 → ambient-tech/future-interface；企业 → corporate-clean）

## 8. Remotion 动画系统

### 8.1 参考官方技能

涉及 Remotion 实现细节（组件 API、渲染参数、Studio、字幕能力）时，查阅官方 Remotion Skills（remotion-create / remotion-markup / remotion-render / remotion-studio / remotion-captions 等），不要凭空实现。

### 8.2 动画词表（按内容选用）

`useCurrentFrame` / `useVideoConfig` / `interpolate` / `spring` / `Sequence` / `Series` / `AbsoluteFill`，以及：Fade、Slide、Scale、Mask/Blur Reveal、Parallax、Ken Burns、Camera Push/Pull、Pan/Zoom、Spotlight、Highlight、Callout、Underline、Number Count-up、Chart/Progress Animation、Staggered Text、Word Reveal、Split Layout、Before/After、Timeline、Card Stack。

**规则**：每个画面只有一个主要视觉焦点；避免大量元素同时运动；避免每个镜头风格不同；避免频繁无意义转场。

### 8.3 转场/开场/结尾

- 转场：Fade/Blur/Push/Mask/Wipe/Zoom/Match Cut 等，**同一条视频转场体系统一**。
- 开场：Question Hook / Big Number / Hero Image / UI Action / Problem Statement / 快速蒙太奇 / Quote / Data Hook / Before-After 等，前几秒让观众知道"这条视频在讲什么"。避免永远"黑背景 → Logo → 标题淡入"。
- 结尾：关键结论 / 品牌落版 / CTA / 总结句 / Logo / 核心数据，按视频类型选择，不强制 CTA。

### 8.4 文本与数据

- 视觉层级：Primary Title / Secondary / Body / Caption / Metadata / Subtitle，一屏保持 1 个核心标题 + 1 个辅助区 + 少量必要数据。
- 真实数据可用 Count Up / Progress / 图表 / Before-After / KPI 卡等动画；**数据必须来自用户输入或可靠素材，禁止虚构数字**。

### 8.5 工程目录与组件化

每个视频任务独立项目目录：

```text
video-project/
├── assets/user/          # 用户原始素材（只读，不覆盖）
├── generated/images/     # AI 生成素材（归档）
├── audio/voiceover/ music/ sfx/
├── captions/
├── public/               # Remotion 静态资源（图片/音频需在此才能 staticFile 引用）
├── src/components/ scenes/ compositions/
├── previews/
└── output/               # 最终成片
```

- 用户素材与 AI 素材分开保存；不覆盖用户原始文件；临时文件可清理但别误删源素材。
- 复杂视频按 Composition / Scene / Typography / Media / Background / Subtitle / Voiceover / Transition / Chart / UIHighlight 等拆分组件，重复视觉元素抽成组件。

### 8.6 渲染配置

`remotion.config.ts` 至少包含：

```ts
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setBrowserExecutable(process.env.CHROME_PATH || "/usr/bin/chromium");
```

输出尺寸：用户指定则严格遵守；未指定按平台判断——横屏 1920×1080、竖屏 1080×1920、方形 1080×1080、4:5 1080×1350。**不要永远固定 1920×1080。**

## 9. 渲染与 QA

### 9.1 渲染前关键帧检查（Preview QA）

正式渲染前抽查：开场、一个主要内容 Scene、一个复杂动画 Scene、字幕 Scene（如有）、UI/数据 Scene（如有）、结尾。检查：中文字体、图片清晰度/变形、文本溢出、字幕遮挡、元素碰撞、色彩对比、安全区、动画节奏、背景文字可读性。发现问题先修复再渲染。

### 9.2 音频 QA

配音存在时检查：文件存在可播放、时长有效、发音无明显异常、无读出符号、语速合理、音量稳定、与 Scene 时长匹配。字幕存在时检查：无明显提前/延迟、长句已拆分、不遮挡画面。音乐存在时检查：不压旁白、首尾无突然切断。

### 9.3 成片 QA（必须执行）

```bash
python3 <skill目录>/scripts/verify_output.py output/<file>.mp4 \
  --expect-width 1920 --expect-height 1080 --expect-duration <秒>
```

检查项：文件存在、大小正常、可解码、分辨率/FPS/时长正确、无黑屏卡帧、素材无缺失、中文正常、配音/字幕/BGM 正常、结尾完整、无调试元素、无绝对路径泄漏到画面、无占位文字。**只有 QA 通过才能宣布成功。**

**音轨结构检查**：最终交付 MP4 必须为 **1 个 Video Stream + 1 个混音 Audio Stream**（Voiceover/BGM/SFX 混入单轨）。若出现 ≥2 个 Audio Stream，检查是否错误多轨封装。工程阶段可保留独立音轨，交付前混音。

**BGM 音频 QA**（合成/外部音乐均需）：

```bash
python3 <skill目录>/scripts/audio_qa.py audio/music/<file>.wav
```

检查：Peak（不 clipping、有 Headroom）、RMS、DC Offset、相邻采样突变（click/pop，重点开头 100ms 与结尾 500ms）、末尾 200ms 归零、末采样为 0、尾部无跳变。存在 FFmpeg/ffprobe 时可进一步检测 LUFS/True Peak。

辅助脚本（`<skill目录>/scripts/`）：

| 脚本 | 用途 |
|---|---|
| `check_environment.sh` | 环境组件检测（只读） |
| `install_edge_tts.sh` | Edge TTS 安装/复用（venv 优先） |
| `generate_voiceover.py` | 配音生成（WordBoundary 词级时间轴 + captions.json + VTT） |
| `generate_image.py` | AI 素材生成（gpt-image-2，env 读密钥） |
| `synthesize_bgm.py` | 程序化 BGM 合成（8 种 Preset，ADSR/Master Fade/防 clipping） |
| `audio_qa.py` | 音频质量 QA（click/DC/clipping/首尾归零） |
| `update_manifest.py` | music_manifest.json / credits.txt / media-manifest.json 管理与许可证过滤（逐 Track 记录） |
| `get_audio_duration.py` | 音频时长（ffprobe 优先，纯 Python MP3/WAV 解析兜底） |
| `select_bgm.py` | BGM Preset 匹配评分（多维度综合打分） |
| `creative_qa.py` | Creative QA 门禁（Anti-PPT/场景多样性/节奏检查） |
| `verify_output.py` | 成片 QA（分辨率/时长/FPS） |

### 9.4 Creative Quality Gate（创意质量门禁，第二层 QA）

正式交付前除技术 QA 外，执行创意 QA：

```bash
python3 <skill目录>/scripts/creative_qa.py storyboard.json
```

自动检查：连续 3 个 Scene 相同 scene_type/layout（PPT-like risk）、>30% 场景无视觉主体、Scene Type < 3 种、Shot < 8、Motion Density 全程一致、时长过于平均（CV<0.15）、存在 >5s 完全静止画面、缺 Creative Concept/Music Brief、开场非 hero/hook、结尾非收束型。

**Anti-PPT Rule**：若出现"每 Scene 一个标题 + 静态背景 + 只有淡入淡出 + 元素固定居中 + 连续结构一致"，判定 PPT-like risk = HIGH，需重新设计（增加 Shot 变化 / 布局变化 / 深度 / 运动 / 视觉叙事），**不通过不交付**。渲染后还需关键帧目检（开场、每个主要 Scene、复杂动画、字幕、UI/数据、结尾）。

**创意基准要求**：正式 Creative Benchmark 至少一次 30~45s 视频——6~8 Scene、10~15 Shot、≥3 种 Scene Type、≥2 张 AI 素材、至少一个 UI/Diagram/Data Scene、Edge TTS + keyword 字幕、完整 BGM Structure（Intro/Main/Highlight/Outro）+ Ducking、Creative QA + Audio QA + Final QA。短视频仅用于技术 Smoke Test，不作为创意基准。

## 10. 失败降级策略

| 模块失败 | 降级方案 |
|---|---|
| AI 图片 | 用户素材 → SVG/CSS → 渐变/程序化背景 |
| Edge TTS | 其他可用 TTS → 无配音版本（明确告知未生成配音） |
| WordBoundary 获取失败 | 自动回退 SentenceBoundary → 按时长比例估算词位（boundary 字段如实标注） |
| BGM Provider 不可用 | 本地合法音乐 → 程序化合成 BGM → 无 BGM 版本 |
| BGM License 无法确认 | 不使用该音乐（宁缺毋滥） |
| BGM 音频 QA 不通过（click/DC/尾部） | 修复合成参数后重新生成；仍失败则换 Preset 或降级无 BGM |
| 字幕 | 继续生成无字幕版本 |
| BGM | 继续生成无音乐版本 |
| 复杂动画 | 使用更稳定的基础动画 |
| 浏览器/渲染 | 参考官方 remotion-render 技能修复 |

核心目标：**尽可能成功输出完整、可播放的视频。**

## 11. 交付

- 成片保存到当前会话成果目录，命名 `YYYY-MM-DD_描述.mp4`。
- 用户说"发给我/发邮箱给我/发邮件"时：按**当前环境已配置的交付渠道**发送（如 SMTP 邮箱，收件人取环境配置或用户指定；附件需在发信工具允许的目录）。**技能内不写死任何个人邮箱/账号。**
- webchat 直接发文件不可用时，可用临时文件托管给下载链接。

## 12. 平台化与最小修改原则

- **技能内不得包含**：个人邮箱、姓名、手机号、API Key/Token/密码、私人服务器地址、私人下载地址、用户特定记忆规则、固定私有代理、固定私人目录、私有 SMTP 配置。密钥一律来自环境变量/平台 Secret/配置文件。
- **环境适配**：不假设所有平台环境与本机一致（Node/Chromium/Linux/Python/registry/图片 Provider/TTS Provider/ffmpeg 路径均可不同）。本机已验证的配置只作为推荐默认，不是唯一方案。
- **最小修改**：不因视频任务修改 SSH/防火墙/用户权限/系统账户/启动项/无关代理/其他项目依赖；能用项目级依赖或虚拟环境就不用系统级安装。
- 用户私有偏好（如"发给我 = 发到自己邮箱"）只存在于 Agent 的记忆/配置中，不写入本技能。
