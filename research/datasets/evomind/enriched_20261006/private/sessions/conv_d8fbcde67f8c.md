# conv_d8fbcde67f8c：完整会话证据

原始标题（不作为任务真值）：帮我安装一个技能：nature-skil

筛选：排除提炼；原结论：EXCLUDE。已有科研技能安装及触发说明，没有实际论文任务

本页按角色展示全部正文与内容对应，不宣称原始时序。空回复、重试与重复来源单独保留。

## 内容对应关系


## 用户 · u_b9df2ca651d32b4a73

来源：conv_d8fbcde67f8c:msg_1（原行5432）

学习上下文保留；不代表已认证技能价值

帮我安装一个技能：nature-skills，查找并安装到skills目录下

## 用户 · u_8950cdb78510f437a9

来源：conv_d8fbcde67f8c:msg_28（原行5434）

学习上下文保留；不代表已认证技能价值

这个技能该如何使用？

## AI · a_7c54906ad39184031b

来源：conv_d8fbcde67f8c:msg_27（原行5433）

学习上下文保留；不代表已认证技能价值

搞定了！**nature-skills** 已经安装到 `skills/` 目录下，共安装了 **11 个技能**：

| 技能 | 状态 | 用途 |
|---|---|---|
| ✅ **nature-figure** | Stable | Nature 风格科研绘图（matplotlib/R） |
| ✅ **nature-polishing** | Stable | 学术写作润色（Nature 期刊标准） |
| ✅ **nature-writing** | Draft | 手稿章节撰写（摘要/引言/方法等） |
| ✅ **nature-reviewer** | Draft | 模拟 Nature 审稿人评估 |
| ✅ **nature-citation** | Beta | 文献引用检索与管理（ENW/RIS/Zotero） |
| ✅ **nature-data** | Draft | Data Availability 声明与 FAIR 检查 |
| ✅ **nature-reader** | Beta | 论文双语 Markdown 阅读器 |
| ✅ **nature-response** | Beta | 审稿意见逐条回复信 |
| ✅ **nature-paper2ppt** | Beta | 论文转中文汇报 PPT |
| ✅ **nature-paper-to-patent** | Beta | 论文转中文发明专利草案 |
| ✅ **nature-academic-search** | Beta | 多源学术搜索（PubMed/CrossRef/arXiv） |

来源：[GitHub - Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)

另外 `skills/_shared/` 共享目录也已一同复制，以便有跨技能引用的技能正常工作。需要我详细介绍某个技能怎么用吗？

## AI · a_9bb4ea13672c2b3dcf

来源：conv_d8fbcde67f8c:msg_34（原行5435）

学习上下文保留；不代表已认证技能价值

这些 skills 的使用方式很简单——它们是**自然语言触发**的，直接说你要干什么就行。以下是每个技能的触发方式：

---

### 使用方式一览

直接跟我说类似下面的话就行：

**📝 论文写作与润色**
- **nature-polishing** → `帮我润色这段论文摘要，改成Nature风格` / `帮我改一下这段英文写作`
- **nature-writing** → `帮我写一段引言/讨论部分，核心发现是XXX`
- **nature-reader** → `帮我精读这篇PDF论文，生成中英文对照版`
- **nature-response** → `帮我写审稿意见回复信`

**📊 科研绘图**
- **nature-figure** → `帮我画一个Nature风格的Figure，双栏4个panel` / `用Python画一个科研配图`

**🔍 文献检索**
- **nature-citation** → `帮我查这篇论文的参考文献` / `搜索这篇paper相关的引用`
- **nature-academic-search** → `搜索PubMed/CrossRef上关于XXX的文献`

**🎤 论文汇报**
- **nature-paper2ppt** → `帮我把这篇论文做成组会PPT` / `把这篇paper变成汇报幻灯片`

**📑 审稿与评估**
- **nature-reviewer** → `模拟Nature审稿人，评估这篇论文`
- **nature-data** → `帮写Data Availability声明`

**💡 论文转专利**
- **nature-paper-to-patent** → `帮我把这篇论文转成发明专利草案`

---

### 举个例子

最常用的几个场景：

```
帮我精读一下这个PDF，生成中英文对照版
```
→ 触发 **nature-reader**

```
帮我润色这段文字，改成Nature期刊风格
```
→ 触发 **nature-polishing**

```
用Python画一个四栏科研Figure，柱状图和折线图组合
```
→ 触发 **nature-figure**，会自动问你是用 Python 还是 R

```
帮我把这篇论文做成组会PPT
```
→ 触发 **nature-paper2ppt**，会产出 .pptx 文件

---

本质就是：**说你想要的，技能会自动匹配触发**。不用记具体技能文件名，自然语言交流就行。需要我哪个技能跑个例子看看效果？

## 文件与执行证据

文件引用0条；工具快照2条；skill分级证据0条。文件字节未补造，工具参数及返回请见同名HTML证据折叠区或tools.jsonl。

## 空回复、重试及其他历史事件（不进入学习正文）
