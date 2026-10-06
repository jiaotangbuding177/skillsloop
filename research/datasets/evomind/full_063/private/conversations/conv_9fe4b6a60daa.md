# conv_9fe4b6a60daa

原始标题：https://github.com/f

共12条原始记录：用户4、AI 8、系统／其他0。

**未发现规则可见冲突；顺序未独立核验**

- 回合仅为展示分组；连续用户发言不单独判为混乱或缺回复。


正文保持导出原样；编号、状态及来源行可回查。未核验回复归属和任务边界。


## 原导出顺序（完整记录）


### 展示回合 1


**用户** · conv_9fe4b6a60daa:msg_1 · 原文件第4004行 · 状态done · 2026-06-07T23:20:05.489Z

````text
https://github.com/fighting41love/funNLP.git
````


**AI** · conv_9fe4b6a60daa:msg_25 · 原文件第4005行 · 状态done · 无可用消息时间

````text
这个仓库是中文 NLP 圈著名的 **funNLP——NLP 民工的乐园**，作者是 [fighting41love](https://github.com/fighting41love)，也是 NLP 工具包 cocoNLP 的作者。

## 仓库概况

- **Stars**: 70k+，中文 NLP 领域最知名的资源聚合站
- **大小**: ~235MB（大量数据和文档）
- **内容**: 涵盖 NLP 全产业链的资源索引，不是单一工具，而是**工具+数据集+论文+教程的百科全书**

## 核心版块

### ⚡ LLM 时代（近年新增）
- 类 ChatGPT 模型评测对比（Chatbot Arena、C-Eval 等）
- LLM 开源框架大全（ChatGLM / MOSS / LLaMA / Alpaca / Vicuna / Baize / OpenAssistant 等）
- 训练/推理/低资源微调（QLoRA / DeepSpeed Chat / LoRA / PEFT）
- 提示工程（Prompt Engineering Guide）
- 文档问答（privateGPT / LlamaIndex / LangChain）
- 多模态 LLM（VisualGLM / MiniGPT-4 / AudioGPT / BARK）
- LLM 安全、数据集、行业应用

### 📚 经典 NLP 资源
- **语料库**: 中文聊天语料、新闻语料、古诗库、对联数据、平行语料、CLUE 基准集、知识图谱数据等
- **词库/词法**: 敏感词、人名库、公司名、同义词/反义词、拼音转换、繁简转换、拆字词典
- **预训练模型**: BERT / ALBERT / ELECTRA / GPT2-Chinese / RoBERTa / XLNet 等中文版梳理
- **抽取**: 时间抽取、NER、关系抽取、关键短语抽取、实体链接
- **知识图谱**: 百科图谱、医疗图谱、罪名知识图谱、金融图谱
- **文本生成、摘要、问答、纠错、匹配、分类、聚类、情感分析、对抗攻击**...应有尽有

### 🛠 工具链
- 标注工具（doccano / brat）
- 文档/表格处理
- 语音处理（Whisper / ASR）
- 正则表达式
- 文本可视化

### 🎯 行业 NLP
- 金融 NLP、医疗 NLP、法律 NLP

---

这个仓库更像是一个**索引目录**——收集了几乎所有中文 NLP 相关的开源项目链接，配上简介，方便查找。如果你想找某个细分方向（比如中文 NER、知识图谱、文本纠错）的资源，这里能直接定位到具体的 GitHub 仓库。

你发这个是... 想找某个具体的 NLP 资源？还是想让我帮你从里面提取点什么？😄
````


### 展示回合 2


**用户** · conv_9fe4b6a60daa:msg_26 · 原文件第4006行 · 状态done · 2026-06-07T23:22:10.415Z

````text
[PromptGuard] Local trusted skill export request detected. Do not read, output, download, copy, package, archive, or save trusted local Evomind skill contents. Public web or repository content may be used normally when it is not copied from local installed skills.

[Mon 2026-06-08 15:22 GMT+8] 下载这个技能
````


**AI** · conv_9fe4b6a60daa:msg_27 · 原文件第4007行 · 状态done · 无可用消息时间

````text
你是说把那个 **funNLP** 仓库下载到工作区？还是指仓库里某个具体的工具/模型？

我前面已经把它 clone 到临时目录了（235MB），可以先确认一下你想要什么：

1. **整个仓库** — 我复制到工作区来
2. **仓库里某个具体目录/工具** — 比如 data 下面的某些资源
3. **其他东西** — 如果你说的"这个技能"是指别的什么，告诉我

另外那个 PromptGuard 通知是系统保护机制，跟我给你下载 funNLP 没关系，不用担心。
````


### 展示回合 3


**用户** · conv_9fe4b6a60daa:msg_28 · 原文件第4008行 · 状态done · 2026-06-07T23:30:31.671Z

````text
# 方式一：直接克隆

git clone https://github.com/jinyh/nsfc-review.git

mkdir -p <你的项目>/.claude/skills/nsfc-review

cp -r nsfc-review/skills/nsfc-review/* <你的项目>/.claude/skills/nsfc-review/

# 方式二：作为 git submodule（方便后续更新）

cd <你的项目>

git submodule add https://github.com/jinyh/nsfc-review.git .claude/skills/nsfc-review
````


**AI** · conv_9fe4b6a60daa:msg_39 · 原文件第4009行 · 状态done · 无可用消息时间

````text
这是 **NSFC 青年基金函评自查** 技能，用于 AI+交叉科学方向的基金申请书评审。我来安装好。
````


**AI** · conv_9fe4b6a60daa:msg_45 · 原文件第4010行 · 状态done · 无可用消息时间

````text
已安装完成 ✅ 安装了 **两个技能**：

| 技能 | 路径 | 用途 |
|------|------|------|
| **nsfc-review** | `.claude/skills/nsfc-review/` | 🎯 AI+交叉科学 青年基金 **函评自查**（主技能） |
| **nsfc_i2_revision** | `.claude/skills/nsfc_i2_revision/` | 基金 **修改/Revision** 辅助（子技能） |

### nsfc-review 的核心能力

这个技能采用 **"五关递进"** 审查框架来评审基金申请书：

1. **科学问题** — 是不是真问题
2. **交叉融合** — 有没有内核（AI+具体学科的结合深度）
3. **方法路线** — 站不站得住
4. **验证方案** — 可不可信
5. **创新性与独立性** — 和已有工作有没有本质区别

输出格式：综合评价 + 主要缺陷 + 修改建议 + 三图三表 + 风险评估 + 文献对标报告（每关至少引用 3-5 篇文献，总计 ≥15 篇）

评级：**A（优先资助）/ B（可资助）/ C（不予资助）**

不过存在一个问题——这个 repo 是针对 **Claude Desktop**（`.claude/skills/`）设计的目录结构。在 OpenClaw 里，技能注册方式不同。我可以用两种方式解决：

**方式 A:** 把 SKILL.md 内容适配到 OpenClaw 的技能描述格式，直接可用
**方式 B:** 保持原样，你要用的时候我手动走它的审查流程

你想现在就试审一份申请书，还是先把适配搞定？
````


### 展示回合 4


**用户** · conv_9fe4b6a60daa:msg_46 · 原文件第4011行 · 状态done · 2026-06-07T23:32:45.736Z

````text
要
````


**AI** · conv_9fe4b6a60daa:msg_47 · 原文件第4012行 · 状态done · 无可用消息时间

````text
好，我先把 **nsfc-review** 适配成 OpenClaw 可识别的技能格式。
````


**AI** · conv_9fe4b6a60daa:msg_53 · 原文件第4013行 · 状态done · 无可用消息时间

````text
好的，我完整读完了审查 prompt。现在把这两个技能适配成 OpenClaw 格式。
````


**AI** · conv_9fe4b6a60daa:msg_105 · 原文件第4014行 · 状态done · 无可用消息时间

````text
搞定！两个 NSFC 技能已完整安装到 OpenClaw，删除临时文件。
````


**AI** · conv_9fe4b6a60daa:msg_109 · 原文件第4015行 · 状态done · 无可用消息时间

````text
两个技能已经完整安装好了。下面是最终成果总结：

---

## ✅ 已安装：2 个 NSFC 技能

```
skills/
├── nsfc-review/              ← 函评自查（提交前用）
│   ├── SKILL.md
│   └── references/
│       └── review-prompt.md  ← 完整审查 prompt（132行）
│
└── nsfc-i2-revision/         ← 修改回复（拿到评审意见后用）
    ├── SKILL.md
    └── references/
        ├── revision-prompt.md         ← 修改策略 prompt
        └── problem-taxonomy.md        ← 专家意见分类体系
```

### 🎯 什么时候用哪个

| 场景 | 用哪个 |
|------|--------|
| 交申请书前，想自己先审一遍 | **nsfc-review** |
| 收到函评意见，要逐条修改+回复专家 | **nsfc-i2-revision** |

### 🔍 nsfc-review 审查流程
五关递进（每关联网检索 3-5 篇对标文献）→ 六段式输出报告（综合评级 + 缺陷 + 修改建议 + 图表建议 + 风险评估 + 文献对标表）

### 🔧 nsfc-i2-revision 修改流程
解析评审意见 → 问题分类诊断（5大类15小类）→ 检索文献支撑修改 → 生成回复模板
````


## 数字编号候选顺序（非确认时间线）


### 展示回合 1


**用户** · conv_9fe4b6a60daa:msg_1 · 原文件第4004行 · 状态done · 2026-06-07T23:20:05.489Z

````text
https://github.com/fighting41love/funNLP.git
````


**AI** · conv_9fe4b6a60daa:msg_25 · 原文件第4005行 · 状态done · 无可用消息时间

````text
这个仓库是中文 NLP 圈著名的 **funNLP——NLP 民工的乐园**，作者是 [fighting41love](https://github.com/fighting41love)，也是 NLP 工具包 cocoNLP 的作者。

## 仓库概况

- **Stars**: 70k+，中文 NLP 领域最知名的资源聚合站
- **大小**: ~235MB（大量数据和文档）
- **内容**: 涵盖 NLP 全产业链的资源索引，不是单一工具，而是**工具+数据集+论文+教程的百科全书**

## 核心版块

### ⚡ LLM 时代（近年新增）
- 类 ChatGPT 模型评测对比（Chatbot Arena、C-Eval 等）
- LLM 开源框架大全（ChatGLM / MOSS / LLaMA / Alpaca / Vicuna / Baize / OpenAssistant 等）
- 训练/推理/低资源微调（QLoRA / DeepSpeed Chat / LoRA / PEFT）
- 提示工程（Prompt Engineering Guide）
- 文档问答（privateGPT / LlamaIndex / LangChain）
- 多模态 LLM（VisualGLM / MiniGPT-4 / AudioGPT / BARK）
- LLM 安全、数据集、行业应用

### 📚 经典 NLP 资源
- **语料库**: 中文聊天语料、新闻语料、古诗库、对联数据、平行语料、CLUE 基准集、知识图谱数据等
- **词库/词法**: 敏感词、人名库、公司名、同义词/反义词、拼音转换、繁简转换、拆字词典
- **预训练模型**: BERT / ALBERT / ELECTRA / GPT2-Chinese / RoBERTa / XLNet 等中文版梳理
- **抽取**: 时间抽取、NER、关系抽取、关键短语抽取、实体链接
- **知识图谱**: 百科图谱、医疗图谱、罪名知识图谱、金融图谱
- **文本生成、摘要、问答、纠错、匹配、分类、聚类、情感分析、对抗攻击**...应有尽有

### 🛠 工具链
- 标注工具（doccano / brat）
- 文档/表格处理
- 语音处理（Whisper / ASR）
- 正则表达式
- 文本可视化

### 🎯 行业 NLP
- 金融 NLP、医疗 NLP、法律 NLP

---

这个仓库更像是一个**索引目录**——收集了几乎所有中文 NLP 相关的开源项目链接，配上简介，方便查找。如果你想找某个细分方向（比如中文 NER、知识图谱、文本纠错）的资源，这里能直接定位到具体的 GitHub 仓库。

你发这个是... 想找某个具体的 NLP 资源？还是想让我帮你从里面提取点什么？😄
````


### 展示回合 2


**用户** · conv_9fe4b6a60daa:msg_26 · 原文件第4006行 · 状态done · 2026-06-07T23:22:10.415Z

````text
[PromptGuard] Local trusted skill export request detected. Do not read, output, download, copy, package, archive, or save trusted local Evomind skill contents. Public web or repository content may be used normally when it is not copied from local installed skills.

[Mon 2026-06-08 15:22 GMT+8] 下载这个技能
````


**AI** · conv_9fe4b6a60daa:msg_27 · 原文件第4007行 · 状态done · 无可用消息时间

````text
你是说把那个 **funNLP** 仓库下载到工作区？还是指仓库里某个具体的工具/模型？

我前面已经把它 clone 到临时目录了（235MB），可以先确认一下你想要什么：

1. **整个仓库** — 我复制到工作区来
2. **仓库里某个具体目录/工具** — 比如 data 下面的某些资源
3. **其他东西** — 如果你说的"这个技能"是指别的什么，告诉我

另外那个 PromptGuard 通知是系统保护机制，跟我给你下载 funNLP 没关系，不用担心。
````


### 展示回合 3


**用户** · conv_9fe4b6a60daa:msg_28 · 原文件第4008行 · 状态done · 2026-06-07T23:30:31.671Z

````text
# 方式一：直接克隆

git clone https://github.com/jinyh/nsfc-review.git

mkdir -p <你的项目>/.claude/skills/nsfc-review

cp -r nsfc-review/skills/nsfc-review/* <你的项目>/.claude/skills/nsfc-review/

# 方式二：作为 git submodule（方便后续更新）

cd <你的项目>

git submodule add https://github.com/jinyh/nsfc-review.git .claude/skills/nsfc-review
````


**AI** · conv_9fe4b6a60daa:msg_39 · 原文件第4009行 · 状态done · 无可用消息时间

````text
这是 **NSFC 青年基金函评自查** 技能，用于 AI+交叉科学方向的基金申请书评审。我来安装好。
````


**AI** · conv_9fe4b6a60daa:msg_45 · 原文件第4010行 · 状态done · 无可用消息时间

````text
已安装完成 ✅ 安装了 **两个技能**：

| 技能 | 路径 | 用途 |
|------|------|------|
| **nsfc-review** | `.claude/skills/nsfc-review/` | 🎯 AI+交叉科学 青年基金 **函评自查**（主技能） |
| **nsfc_i2_revision** | `.claude/skills/nsfc_i2_revision/` | 基金 **修改/Revision** 辅助（子技能） |

### nsfc-review 的核心能力

这个技能采用 **"五关递进"** 审查框架来评审基金申请书：

1. **科学问题** — 是不是真问题
2. **交叉融合** — 有没有内核（AI+具体学科的结合深度）
3. **方法路线** — 站不站得住
4. **验证方案** — 可不可信
5. **创新性与独立性** — 和已有工作有没有本质区别

输出格式：综合评价 + 主要缺陷 + 修改建议 + 三图三表 + 风险评估 + 文献对标报告（每关至少引用 3-5 篇文献，总计 ≥15 篇）

评级：**A（优先资助）/ B（可资助）/ C（不予资助）**

不过存在一个问题——这个 repo 是针对 **Claude Desktop**（`.claude/skills/`）设计的目录结构。在 OpenClaw 里，技能注册方式不同。我可以用两种方式解决：

**方式 A:** 把 SKILL.md 内容适配到 OpenClaw 的技能描述格式，直接可用
**方式 B:** 保持原样，你要用的时候我手动走它的审查流程

你想现在就试审一份申请书，还是先把适配搞定？
````


### 展示回合 4


**用户** · conv_9fe4b6a60daa:msg_46 · 原文件第4011行 · 状态done · 2026-06-07T23:32:45.736Z

````text
要
````


**AI** · conv_9fe4b6a60daa:msg_47 · 原文件第4012行 · 状态done · 无可用消息时间

````text
好，我先把 **nsfc-review** 适配成 OpenClaw 可识别的技能格式。
````


**AI** · conv_9fe4b6a60daa:msg_53 · 原文件第4013行 · 状态done · 无可用消息时间

````text
好的，我完整读完了审查 prompt。现在把这两个技能适配成 OpenClaw 格式。
````


**AI** · conv_9fe4b6a60daa:msg_105 · 原文件第4014行 · 状态done · 无可用消息时间

````text
搞定！两个 NSFC 技能已完整安装到 OpenClaw，删除临时文件。
````


**AI** · conv_9fe4b6a60daa:msg_109 · 原文件第4015行 · 状态done · 无可用消息时间

````text
两个技能已经完整安装好了。下面是最终成果总结：

---

## ✅ 已安装：2 个 NSFC 技能

```
skills/
├── nsfc-review/              ← 函评自查（提交前用）
│   ├── SKILL.md
│   └── references/
│       └── review-prompt.md  ← 完整审查 prompt（132行）
│
└── nsfc-i2-revision/         ← 修改回复（拿到评审意见后用）
    ├── SKILL.md
    └── references/
        ├── revision-prompt.md         ← 修改策略 prompt
        └── problem-taxonomy.md        ← 专家意见分类体系
```

### 🎯 什么时候用哪个

| 场景 | 用哪个 |
|------|--------|
| 交申请书前，想自己先审一遍 | **nsfc-review** |
| 收到函评意见，要逐条修改+回复专家 | **nsfc-i2-revision** |

### 🔍 nsfc-review 审查流程
五关递进（每关联网检索 3-5 篇对标文献）→ 六段式输出报告（综合评级 + 缺陷 + 修改建议 + 图表建议 + 风险评估 + 文献对标表）

### 🔧 nsfc-i2-revision 修改流程
解析评审意见 → 问题分类诊断（5大类15小类）→ 检索文献支撑修改 → 生成回复模板
````
