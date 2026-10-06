# conv_4af767266aac:learn01：容器技能CLI安装权限排障

会话：conv_4af767266aac

本轮可学习：tar保留包内所有权触发受限chown时改no-same-owner解压，再按脚本剩余安装步骤完成并验证，不重复跑同一失败脚本

原文依据：--no-same-owner

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 用户需求／反馈

来源消息组：u_c31aa3bb2eb58abb52

请根据 https://skillhub.cn/install/skillhub.md，安装 @user_57af6244/wechat-ai-publisher。

## AI处理／结果

来源消息组：a_38ef5d481e8c6742f0

脚本用 `tar -xzf` 解压时保留了包内 uid 501 的所有权，容器里 chown 受限导致失败。我手动下载并用 `--no-same-owner` 解压绕过这个问题。先看下脚本解压后的安装逻辑：

## AI处理／结果

来源消息组：a_abc4d55b53bfb2b9f7

安装完成 ✅

**已完成：**
1. **skillhub CLI** 已安装（v2026.8.5，沙箱 `/workspace/.local/bin/skillhub`）
2. **`@user_57af6244/wechat-ai-publisher` v3.0.3**（公众号自动化助手）已从 SkillHub 下载并部署到 `/workspace/skills/wechat-ai-publisher/`
3. 安装报告已生成：`AI 工作区/成果文件/请根据 https---skillhub-conv_4af767266aac/2026-08-14_wechat-ai-publisher安装报告.md`

**技能内容**：SKILL.md + 发布流水线脚本（run_pipeline / create_draft / upload_material / compress_image / markdown转微信HTML）+ 写作质量规范，共 132K。

⚠️ **一个限制需要你处理**：当前是隔离沙箱，无法直接写入宿主机 OpenClaw 的技能目录（`/home/km-agent/skills/`），所以技能目前只存在于沙箱 workspace。要让本 Agent 真正用上它，请在宿主机执行（二选一）：

```bash
# 复制沙箱里的技能
cp -r "/root/.openclaw/workspace-u_5a7ea6c4-cb72-415d-8298-8b5ced8f3347/skills/wechat-ai-publisher" /home/km-agent/skills/
# 或直接用 skillhub 重装
skillhub install wechat-ai-publisher --namespace user_57af6244 --dir /home/km-agent/skills
```

然后**重启 OpenClaw** 即可生效。使用前还需在技能目录配置 `.env`（`WECHAT_APP_ID` / `WECHAT_APP_SECRET`）并 `pip install -r requirements.txt`，详见报告。

另外问一下：**是否将 SkillHub 设为优先技能安装源？**（以后搜索/安装技能会优先走 skillhub，国内更快更合规，不可用时才回退 clawhub）
