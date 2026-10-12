# Get笔记 Skill

得到大脑（Get笔记）CodeBuddy Skill — 通过 AI 助手管理个人笔记和知识库。

## 结构

```
getnote-skill/
├── SKILL.md                # Skill 核心定义（YAML + 指令）
├── scripts/                # 可执行 SDK
│   ├── src/                # TypeScript 源码
│   ├── dist/               # 编译产物
│   ├── examples/           # 使用示例
│   ├── package.json        # Node.js 依赖
│   └── tsconfig.json       # TypeScript 配置
├── references/             # 参考文档
│   ├── api-reference.md    # API 端点完整列表
│   └── setup-guide.md      # 凭证获取与配置指南
├── assets/                 # 资产文件（模板等）
└── README.md               # 本文件
```

## 快速开始

```bash
# 1. 安装依赖
cd scripts && npm install

# 2. 编译
npx tsc

# 3. 设置环境变量（从浏览器 Cookie 获取）
export GETNOTE_TOKEN="eyJ..."
export GETNOTE_CSRF="abc123..."
export GETNOTE_DEVICE_ID="e152..."

# 4. 运行示例
npx tsx examples/basic.ts
```

## 触发说明

此 Skill 在用户提到以下操作时自动触发：

| 关键词 | 操作 |
|--------|------|
| "记一下"、"存到笔记"、"保存" | 创建笔记 |
| "搜一下"、"找找笔记" | 搜索笔记 |
| "加到知识库"、"加标签" | 管理知识库/标签 |
| "删笔记"、"回收站" | 删除/回收站管理 |
| "配置笔记"、"连接得到大脑" | 设置凭证 |
