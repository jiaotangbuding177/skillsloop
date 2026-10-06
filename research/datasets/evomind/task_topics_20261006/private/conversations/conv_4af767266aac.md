# conv_4af767266aac

会话主主题：助手配置与技能管理；状态：保留学习候选
其他主题：软件产品、代码与技术排障

说明：下面保留来源正文展示次序；内容对应关系另存，不据此保证真实时间顺序。

## 用户 · u_c31aa3bb2eb58abb52

请根据 https://skillhub.cn/install/skillhub.md，安装 @user_57af6244/wechat-ai-publisher。

## AI · a_b9d447e9420160164d

收到，我先去看一下 skillhub 的安装说明，然后安装 wechat-ai-publisher。

## AI · a_007eea77604c5f58c6

已读取安装说明。现在检查 skillhub CLI 是否已安装：

## AI · a_fc01712310e1a67ed7

skillhub CLI 未安装，先安装 CLI（这是安装技能的前提）：

## AI · a_893609f80127155536

安装脚本在沙箱内因权限问题失败（tar 无法更改文件所有权）。我先看看安装脚本做了什么，再决定怎么处理：

## AI · a_38ef5d481e8c6742f0

脚本用 `tar -xzf` 解压时保留了包内 uid 501 的所有权，容器里 chown 受限导致失败。我手动下载并用 `--no-same-owner` 解压绕过这个问题。先看下脚本解压后的安装逻辑：

## AI · a_521496b4b7e1d93398

明白了安装逻辑。手动下载 kit 并绕过 tar 的 chown 问题：

## AI · a_832137e9a87f5bc140

注意到沙箱 HOME 是 `/workspace`，但当前 Agent 的 skills 目录在 `/home/km-agent/skills/`。确认一下目录情况：

## AI · a_9a722019abcbee05c2

沙箱无法直接访问宿主机 skills 目录。试试 elevated 权限在宿主机上操作（安装说明也提到沙箱受限时需用允许联网的权限执行）：

## AI · a_4fd73b6d465f31e035

elevated 不可用，只能在沙箱内操作。先安装 CLI（装到沙箱 HOME），再搜索目标技能：

## AI · a_c7fb6f4c08d107abee

CLI 安装成功（skillhub 2026.8.5）。现在搜索目标技能：

## AI · a_e0be372397a254852f

找到了 `@user_57af6244/wechat-ai-publisher`（v3.0.3，公众号自动化助手）。查看安装参数后执行安装：

## AI · a_d6563e7a14b3015e68

技能包下载成功。查看安装内容：

## AI · a_1a593754ae6cdd5f47

技能包内容完整（SKILL.md + 发布脚本 + 参考文档）。现在检查 OpenClaw 如何配置技能目录，确定部署位置：

## AI · a_37c48ade1090f96f2f

沙箱里没有 OpenClaw 配置访问权限。我把技能正式部署到 workspace 的稳定位置，并生成部署说明。先看一下 SKILL.md 头部确认技能元数据：

## AI · a_75c6752c4b1eb8df3c

技能内容确认无误。现在把它部署到 workspace 稳定位置，并生成安装报告：

## AI · a_5f140fb6d0bbfabaf8

技能部署完成。生成安装报告到成果目录：

## AI · a_abc4d55b53bfb2b9f7

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
