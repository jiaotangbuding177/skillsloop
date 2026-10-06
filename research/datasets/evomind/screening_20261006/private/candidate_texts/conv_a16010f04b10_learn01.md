# conv_a16010f04b10:learn01：科研系统可移植打包

会话：conv_a16010f04b10

本轮可学习：可交付包排除venv、git、缓存和依赖目录，删当前研究产物后重打包，不把运行时混为技能源码

原文依据：`.venv/` `.git/` `__pycache__/`

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 用户需求／反馈

来源消息组：u_8eee200e7b9b56201b

帮我把这个技能包打包到workspace下变成一个zip包

## 用户需求／反馈

来源消息组：u_e4e2f32d177ff8443c

昂我把 下面的内容删除掉：✅ 已完成的研究项目（EvoSkillCompiler）

✅ 实验代码 + 论文 Word 文档

✅ 文档说明

## 用户需求／反馈

来源消息组：u_062c468fa91987f6a4

帮我把 evomind-auto-research打包成zip包放到workspace 下面

## 用户需求／反馈

来源消息组：u_ad07195a08bf6d2b5e

重新打个包

## AI处理／结果

来源消息组：a_cf646c6df7c94ca588

打包完成 ✅

| 项目 | 值 |
|------|-----|
| 文件名 | `/workspace/evomind-auto-research.zip` |
| 大小 | **5.4 MB**（含 346 个文件） |
| 排除项 | `.venv/` `.git/` `__pycache__/` `node_modules/` `outputs/` |

包含全部内容：
- ✅ 50 个 Agent Prompt 模板
- ✅ 24 个编排模块
- ✅ SKILL.md + 适配器
- ✅ 已完成的研究项目（EvoSkillCompiler）
- ✅ 实验代码 + 论文 Word 文档
- ✅ 文档说明

解压到任何机器上，`python3 -m venv .venv && .venv/bin/pip install -e .` 即可恢复环境。
