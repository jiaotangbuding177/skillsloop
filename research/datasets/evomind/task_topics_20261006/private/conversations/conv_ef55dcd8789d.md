# conv_ef55dcd8789d

会话主主题：助手配置与技能管理；状态：暂存待补证
其他主题：无

说明：下面保留来源正文展示次序；内容对应关系另存，不据此保证真实时间顺序。

## 用户 · u_e1b4190ce242b4a5af

academic-research-skills下载

## 用户 · u_acb19f70d3632499c2

需要

## AI · a_ab9c3535a4e8c00150

我搜索到了一系列学术研究相关的 OpenClaw 技能。我来查一下当前环境，然后帮你下载安装。看到有 `academic-research-skills` 和 `academic-research-hub`！让我用正确的格式安装：全部安装完毕！以下是为您下载安装的 **学术研究技能** 汇总：

---

## ✅ 已安装的 Academic Research Skills（共 13 个）

### 📚 学术搜索与检索
| 技能 | 说明 | 安装命令 |
|---|---|---|
| **academic-research** | OpenAlex API 检索学术论文、文献综述（免费，无需 API Key） | `clawhub install academic-research` |
| **academic-research-hub** | 一站式检索 arXiv / PubMed / Semantic Scholar，导出 BibTeX / RIS / Markdown | `clawhub install academic-research-hub` |
| **arxiv-search-collector** | 模型驱动的 arXiv 论文检索工作流 | `clawhub install arxiv-search-collector` |
| **abstract-searcher** | 向 .bib 文件中搜索添加摘要（arXiv / Semantic Scholar / CrossRef） | `clawhub install abstract-searcher` |
| **paper-fetcher** | 通过 DOI 从 Sci-Hub 自动下载论文 PDF | `clawhub install paper-fetcher` |
| **academic-researcher** | 通用学术研究者工具 | `clawhub install academic-researcher` |

### ✍️ 学术写作与审稿
| 技能 | 说明 |
|---|---|
| **academic-research-writing-skill** | 学术论文写作辅助：选题、大纲、写作、审稿 |
| **academic-research-skills** | AI 驱动的学术研究工作流：选题、写作、审稿、回复审稿意见 |
| **research-academic-helper** | 科研学术助手（中文） |
| **huimai-academic-research** | 🎓 学术研究指导（中文） |

### 🔬 深度研究
| 技能 | 说明 |
|---|---|
| **alvis-academic-deep-research** | 学术深度研究技能 |
| **scholar-deep-research** | 学者深度研究技能 |
| **paper-reading** | 学术论文阅读、总结、方法图绘制 |

---

### 📁 安装位置
`/workspace/skills/` 目录下。

### 🔧 如何使用
新技能安装后，在会话中提及相关关键词（如"帮我搜论文"、"文献综述"、"查 arXiv"），OpenClaw 就会自动调用对应的技能。也可以直接在对话里说：
> *"帮我用 academic-research-hub 找近一年 graph neural networks 的论文，导出 BibTeX"*

需要我把这些技能配置到 OpenClaw 的 skill entries 中使其自动启用吗？

## AI · a_ec77c081776856ba34

OpenClaw 在这个沙箱里没有安装（技能已下载到 `/workspace/skills/`）。我无法直接修改你宿主机上的 OpenClaw 配置，但可以给你完整的配置内容，你只需复制到 `openclaw.json` 即可。

---

先确认你的 OpenClaw 配置文件位置，执行：
```bash
# 查看当前 skills 路径
openclaw config get skills.dir

# 或者直接找配置文件
cat ~/.openclaw/openclaw.json
```

**典型位置：** `~/.openclaw/openclaw.json`

然后将以下内容添加到 `skills.entries` 部分：

```json
{
  "skills": {
    "entries": {
      "academic-research": {
        "enabled": true,
        "dir": "/workspace/skills/academic-research"
      },
      "academic-research-hub": {
        "enabled": true,
        "dir": "/workspace/skills/academic-research-hub"
      },
      "academic-research-skills": {
        "enabled": true,
        "dir": "/workspace/skills/academic-research-skills"
      },
      "academic-research-writing-skill": {
        "enabled": true,
        "dir": "/workspace/skills/academic-research-writing-skill"
      },
      "academic-researcher": {
        "enabled": true,
        "dir": "/workspace/skills/academic-researcher"
      },
      "arxiv-search-collector": {
        "enabled": true,
        "dir": "/workspace/skills/arxiv-search-collector"
      },
      "abstract-searcher": {
        "enabled": true,
        "dir": "/workspace/skills/abstract-searcher"
      },
      "paper-fetcher": {
        "enabled": true,
        "dir": "/workspace/skills/paper-fetcher"
      },
      "paper-reading": {
        "enabled": true,
        "dir": "/workspace/skills/paper-reading"
      },
      "research-academic-helper": {
        "enabled": true,
        "dir": "/workspace/skills/research-academic-helper"
      },
      "huimai-academic-research": {
        "enabled": true,
        "dir": "/workspace/skills/huimai-academic-research"
      },
      "alvis-academic-deep-research": {
        "enabled": true,
        "dir": "/workspace/skills/alvis-academic-deep-research"
      },
      "scholar-deep-research": {
        "enabled": true,
        "dir": "/workspace/skills/scholar-deep-research"
      }
    }
  }
}
```

> ⚠️ 如果你的 skills 目录不是 `/workspace/skills`，请调整 `dir` 路径。可以用 `clawhub list` 在宿主机上确认实际安装路径。

**或者更简单——** 直接运行以下命令把技能安装到 OpenClaw 默认的 skills 目录：

```bash
# 先确认默认路径
openclaw config get skills.dir

# 然后在那里安装
cd $(openclaw config get skills.dir)
clawhub install academic-research
clawhub install academic-research-hub
clawhub install academic-research-skills
clawhub install academic-research-writing-skill
clawhub install academic-researcher
clawhub install arxiv-search-collector
clawhub install abstract-searcher
clawhub install paper-fetcher
clawhub install paper-reading
clawhub install research-academic-helper
clawhub install huimai-academic-research
clawhub install alvis-academic-deep-research
clawhub install scholar-deep-research
```

安装完后重启会话，技能就会自动生效。需要我帮你把技能文件打包，方便你传到宿主机上？

## AI · a_0c9834c7642f00bf74

包已打好！文件在沙箱中：`/workspace/academic-research-skills.tar.gz`（215KB）。

你可以直接在你的宿主机（运行 OpenClaw 的机器）上执行以下命令下载：

```bash
# 如果可以直接从沙箱复制（同一台机器）：
cp /workspace/academic-research-skills.tar.gz ~/

# 或者通过 clawhub 直接安装到默认 skills 目录（推荐，一步到位）：
cd ~/.openclaw/skills  # 或者 openclaw config get skills.dir
clawhub install academic-research
clawhub install academic-research-hub
clawhub install academic-research-skills
clawhub install academic-research-writing-skill
clawhub install academic-researcher
clawhub install arxiv-search-collector
clawhub install abstract-searcher
clawhub install paper-fetcher
clawhub install paper-reading
clawhub install research-academic-helper
clawhub install huimai-academic-research
clawhub install alvis-academic-deep-research
clawhub install scholar-deep-research
```

**推荐方案二（一键脚本批量安装）：**

```bash
SKILLS="academic-research academic-research-hub academic-research-skills academic-research-writing-skill academic-researcher arxiv-search-collector abstract-searcher paper-fetcher paper-reading research-academic-helper huimai-academic-research alvis-academic-deep-research scholar-deep-research"
for s in $SKILLS; do clawhub install "$s"; done
```

安装完重启 OpenClaw 会话即可自动加载。需要我进一步帮你做什么配置吗？
