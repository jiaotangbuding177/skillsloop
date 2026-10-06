# conv_97579cceae5e:learn01：书转视频课插件状态机修订

会话：conv_97579cceae5e

本轮可学习：对照实际插件规范注册工具与门控；发现门控先complete再重置pending导致流程绕时修状态转移，补完整流水线测试，真实视频适配仍留未接通边界

原文依据：先 completeStage 再重置 pending

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 用户需求／反馈

来源消息组：u_063c0b47fbd4574b20

我要做一个Deepseek 的插件,  https://deepseek-code.com/plugins  流水线设计：书 → 视频课 → 出题

## 用户需求／反馈

来源消息组：u_ef38c53b70214c797b

这个是我们evomind 本身的技能 Evomind视频生成器【自研】

## 用户需求／反馈

来源消息组：u_fc9b74da0921f0db83

搭插件骨架

## AI处理／结果

来源消息组：a_a2d8c40e04feff33d5

测试全部通过 ✅ 不过我发现 tools.ts 里门控通过后的状态流转写得绕（先 completeStage 再重置 pending），优化一下让状态机更干净。

## AI处理／结果

来源消息组：a_320f48fea76254cab2

补一个完整流水线流程测试，然后整体验证。

## AI处理／结果

来源消息组：a_fb3fc85f61dd25b1b2

✅ 骨架搭建完成并已提交。交付总结：

## 📦 dsh-book2course 插件骨架

**位置**：`AI 工作区/成果文件/帮我把下面的这段话翻译一下：我们登录进来-conv_97579cceae5e/dsh-book2course/`

### 结构（完全对齐 DSH 插件规范）

```
dsh-book2course/
├── package.json              # dsh 元数据 + cordis.patch.yml bundle 配置
├── cordis.patch.yml          # 挂载宿主半区（storage/tools/shell）
├── SKILL.md                  # agent 操作手册（流水线+门控+降级规范）
├── README.md / LICENSE / .gitignore
├── book2course.config.example.json  # 音色/主题/难度分布/门控开关
├── assets/plugin-icon.svg
├── src/
│   ├── index.ts              # 插件入口（name/inject/apply，无 default 导出）
│   ├── types.ts              # Job/蓝图/课程产物/题目 领域类型
│   ├── domain.ts             # 状态机 + 门控校验（非法迁移拦截）
│   ├── service.ts            # Job 持久化服务
│   ├── tools.ts              # 11 个 book2course_* 工具
│   ├── pipeline/             # 解析(OCR三级探测)/蓝图prompt/出题prompt/导出
│   └── evomind/adapter.ts    # ★ Evomind 视频生成器适配层
└── tests/domain.test.ts      # 状态机测试（4/4 通过）
```

### 关键设计点

- **11 个工具**：start → parse → blueprint → 🔒门控1 → lesson → 🔒门控2 → quiz → 🔒门控3 → export + status/cancel，门控工具返回 waiting 状态、不伪造进度（book2skill 同款原则）
- **状态机**：非法迁移直接拦截（如 pending 直接 exported 会报错），终态不可逆
- **Evomind 对接点**（`adapter.ts`）：探测技能目录（环境变量 > 常见路径）→ 蓝图 lesson 作创意简报 → 回收 `script.md/storyboard.json/slides/配音/字幕/成片`，生成器自带三重 QA 不可跳过
- **验证**：node strip-types 跑通 4/4 测试，9 个 TS 文件语法全过

### 待实现的 TODO（骨架标注清楚）

1. 真实解析器（epub/pdf/md + OCR 三级探测）
2. Evomind 适配层真实调用（`produceLesson()`）
3. 导出转换器（问卷星/Kahoot CSV）
4. storage-domain 持久化（跨会话恢复）

下一步建议：**先做 Evomind 适配层的真实对接**（这是流水线的核心引擎），需要一台装了 remotion-video-generator 技能的环境来联调。要现在继续吗？
