# conv_dca388ba673f

原始标题：我想用NEGA。。。但不知道该如何使用和

共2条原始记录：用户1、AI 1、系统／其他0。

**未发现规则可见冲突；顺序未独立核验**

- 回合仅为展示分组；连续用户发言不单独判为混乱或缺回复。


正文保持导出原样；编号、状态及来源行可回查。未核验回复归属和任务边界。


## 原导出顺序（完整记录）


### 展示回合 1


**用户** · d5d395d1-e47b-466b-8ed6-a29e914a1a5f · 原文件第38184行 · 状态done · 无可用消息时间

````text
我想用NEGA。。。但不知道该如何使用和安装
````


**AI** · 5d503e78-79e9-42a7-b21f-f4c0d58726ab · 原文件第38185行 · 状态done · 无可用消息时间

````text
搜到几个叫 NEGA 的项目,先确认下你说的是哪个——最可能的是这个 GitHub 上的 AI 英语口语教练项目,我拉一下它的完整文档:这个 NEGA 应该是 GitHub 上的开源项目 **diyanqi/NEGA**——一个 AI 英语口语教练/语法助手(自称"西海岸口语教练",Next.js 写的)。如果你说的不是这个,把链接或截图发我,我再查。

先按这个给你完整攻略:

## 它是什么
AI 驱动的英语助手,功能:实时语法纠错、发音指导(西海岸口音)、AI 口语对话、中英双语界面。技术栈:Next.js 16 + OpenAI API + NVIDIA Riva 语音服务(ASR 语音转文字 / TTS 文字转语音)。

## 安装前提
- **Node.js 18+**(建议 20 LTS)
- **包管理器**:pnpm(推荐,`npm install -g pnpm` 可装)
- **OpenAI API Key**(对话功能必需,付费)
- 语音功能还需要 **NVIDIA Riva 服务**(`grpc://localhost:50051`),这玩意儿要 NVIDIA GPU + NGC 容器,比较重——**如果只想用文字对话/语法纠错,可以先不配 Riva**

## 安装步骤(本地跑)
```bash
# 1. 克隆项目
git clone https://github.com/diyanqi/NEGA.git
cd NEGA

# 2. 装依赖
pnpm install

# 3. 配置环境变量(项目里有 .env.example 就复制,没有就手动建)
cp .env.example .env.local   # 如果存在的话

# 4. 编辑 .env.local,填入你的 key
#    OPENAI_API_KEY=sk-xxxx
#    RIVA_ASR_SERVICE=grpc://localhost:50051   ← 没有 Riva 可先留空
#    RIVA_TTS_SERVICE=grpc://localhost:50051   ← 没有 Riva 可先留空

# 5. 启动开发模式
pnpm dev
```
浏览器打开 `http://localhost:3000` 就能用了。

## 生产部署
```bash
pnpm build
pnpm start
```
想部署到公网可以用 Vercel(Next.js 亲儿子,`vercel` 一条命令),把环境变量在 Vercel 后台配好即可。

## 几个提醒
1. **这是个个人开源项目**,README 里的安装命令写得比较糙(有省略),上面是我按标准 Next.js 流程补全的,如果 clone 下来发现有 `.env.example`,以它为准
2. **发音指导功能强依赖 Riva**,没有 NVIDIA GPU 的话这功能基本用不了——纯文字纠错和对话没问题
3. 如果你只是想要"AI 练口语"这个效果,不想折腾本地环境,直接用现成的(比如 ChatGPT 语音模式)可能更省事;想体验/学习这个项目本身才值得装

要不要我帮你确认下这个仓库最近有没有更新、作者有没有部署线上 demo?或者你说下是从哪看到 NEGA 的,我帮你确认是不是同一个东西。
````
