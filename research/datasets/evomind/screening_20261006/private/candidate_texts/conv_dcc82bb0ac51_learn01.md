# conv_dcc82bb0ac51:learn01：图片PPT生成环境权限回退

会话：conv_dcc82bb0ac51

本轮可学习：缺requests及python-pptx先查实际Python和安装权限；系统环境受限时改用户安装而不是反复运行失败命令，确认依赖后逐页生成合成

原文依据：改用 `--user` 模式安装

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 用户需求／反馈

来源消息组：u_002e9e0630f3565196

请根据会话内容，生成【相关主题】的图片型PPT，不超过3页

## 用户需求／反馈

来源消息组：u_ab3a6cc739b6810dac

直接生成

## 用户需求／反馈

来源消息组：u_a51dc0e03c6b21b380

Python 缺两个依赖包，缺哪两个依赖包

## AI处理／结果

来源消息组：a_e1ff4ca59a8b88675f

权限问题，改用 `--user` 模式安装：

## AI处理／结果

来源消息组：a_7d867a07addbce1cd8

依赖就绪。现在写逐页生成脚本（先验证文件系统路径一致性）：

## AI处理／结果

来源消息组：a_f4928ace0bcdef072b

缺的是这两个：

1. **`requests`** —— 用于调用图片生成 API（`https://llmapi.zzz4ai.com/v1/images/generations` 和 `/edits`），发 HTTP 请求、接收 base64 图片数据
2. **`python-pptx`** —— 用于把三张页面图片全幅嵌入、汇总生成 `.pptx` 文件（构建 PPT 演示文稿）

当时系统 Python 是"externally managed"环境（PEP 668 保护），普通 `pip install` 被拒，最后用 `python3 -m pip install --user --break-system-packages requests python-pptx` 装到了用户目录（`/workspace/.local`）才成功。装完后 `import requests, pptx` 验证通过，后续生成全部正常 ✅
