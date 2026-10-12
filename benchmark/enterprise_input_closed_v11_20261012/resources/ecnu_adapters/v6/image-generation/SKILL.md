---
name: image-generation
description: 按用户指定的ECNU实验接口生成图片，并记录真实接口、尺寸及转换。
---

# ECNU实验图片适配

本轮用户明确要求图片采用ECNU。原EvoMind图片包作为出处保留，本入口按相同任务能力调用配置好的ECNU账号，无需ZZZ4密钥，不声明历史供应方同版复现。

实际执行：

```bash
python /opt/eval-adapter/ecnu_tools.py image --text "完整图片描述" --size 1280x720 --output /workspace/outputs/图片.png
```

命令读取运行容器的私有模型凭据；不向用户索要、输出或粘贴密钥。每次先读取当前输入图片/要求并采用新输出路径。提示词最多1024字符；超过时依据全部用户约束写完整简洁指令，不能静默截断。生成后打开或渲染实际文件核查任务约束，交付图片路径和所用适配。

生成支持 --size WIDTHxHEIGHT；非接口原生尺寸先生成匹配比例原生图，再保持比例缩放与补边。receipt保留真实原生尺寸、请求尺寸和转换方式。不要将补边称为原生高分辨率生成。

多参考编辑使用 --image-paths "主图" "参考图2" ...，输入会制成明确编号参考图拼版，并单图上传；指令说明每张用途，输出只保留成品。receipt保留所有参考图SHA及拼版适配，不能声明ECNU原生多文件上传或保证任何编辑与旧历史图完全一致。无法遵循细节时基于本次实际图片继续编辑，不能用文本描述冒充图片。

接口文档：https://developer.ecnu.edu.cn/vitepress/llm/api/imagegenerate.html 与 https://developer.ecnu.edu.cn/vitepress/llm/api/imageedit.html。
