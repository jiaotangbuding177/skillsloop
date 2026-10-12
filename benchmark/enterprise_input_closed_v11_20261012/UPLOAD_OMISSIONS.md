# v11 上传遗漏清单（GitHub）

本目录（`benchmark/enterprise_input_closed_v11_20261012/`）已上传至 GitHub 仓库 `jiaotangbuding177/skillsloop` 的分支 `codex/enterprise-benchmark-v11-20261012`（2026-10-12）。除下表列出的 6 个文件外，本 benchmark 全部文件随 git 提交上传，包括 `evaluation/validator_suite/`（226 个逐任务校验入口、合同、检查点与评分实现）。

## 未上传文件（6 个）

| 路径 | 字节 | SHA-256 | 原因 |
|---|---|---|---|
| environment/skill_images/openclaw-gitee-skills.tar | 3,751,969,280 | cc429309f99cfb9d63552793297b88405cece71beea9470f1659ccc688120329 | 第三方工具镜像导出，超出 GitHub 单文件 100MB 与推送包上限；可由公开组件重建 |
| resources/objects/b7a334884c588b7cbfe49956f2747e34084909536487e17732b5b5cf53e2c7e4/原始视频Xin.mp4 | 173,156,613 | b7a334884c588b7cbfe49956f2747e34084909536487e17732b5b5cf53e2c7e4 | 单文件 >100MB，GitHub 拒绝 |
| resources/environment_closure/v7/9b2ec4e3f645c47482b9ac9f991ea8a5517dc7351f33bf7b4ace4dfad78e15c8/runtime.tar.gz | 138,563,126 | 9b2ec4e3f645c47482b9ac9f991ea8a5517dc7351f33bf7b4ace4dfad78e15c8 | 单文件 >100MB 且为不透明运行时归档 |
| resources/objects/3d5bbd99106062138379eda5b12bc3f7a7781c94f983a6af7e699476ce898723/天辰-易知_科技产业匹配_Agent制作包.zip | 126,148,365 | 3d5bbd99106062138379eda5b12bc3f7a7781c94f983a6af7e699476ce898723 | 单文件 >100MB，GitHub 拒绝 |
| resources/objects/83b031e33392432481c2cadfc634124a8a92a9427eaec5a0184567c429cd5d64/credentials.md | 752 | 83b031e33392432481c2cadfc634124a8a92a9427eaec5a0184567c429cd5d64 | 仓库敏感文件规则（`**/credentials.*`）排除；内容为凭据目录说明且自身声明机密不外传 |
| resources/objects/ad60404d211f581f699c17cfe577651f262146a49fc79b82177a472f756874cb/credentials.md | 831 | ad60404d211f581f699c17cfe577651f262146a49fc79b82177a472f756874cb | 同上 |

`**/__pycache__/` 按仓库忽略规则未提交（构建缓存）。

## 字节保真

本目录含 `* -text` 属性的 `.gitattributes`，禁用 Git 行尾转换：提交与检出都保持与本地一致的原始字节（本机文件多为 CRLF）。已抽查 JSON、JSONL 与大文件，`git cat-file blob` 的 SHA-256 与本地文件一致，可与 [文件哈希清单.json](文件哈希清单.json)、[release_freeze_v11.json](release_freeze_v11.json) 逐字节核对。

## 复核方式

- 本地工作区保留上述全部文件；`sha256` 与本表一致即未被改动。
- 整包口径见 [release_freeze_v11.json](release_freeze_v11.json)（file_count=11301、bytes=5,597,163,937，含本表省略项）。远端克隆的字节数因此小于冻结口径。
- 省略项不改变任何会话、合同、检查点或校验脚本；除上表 4 个大文件所属资源对象外，226 任务全部数据完整上传。
- 上传时对全树做过凭据扫描（私钥、GitHub/AWS token、Bearer、password/secret 赋值等），除公开文档中的占位示例外无真实凭据。
