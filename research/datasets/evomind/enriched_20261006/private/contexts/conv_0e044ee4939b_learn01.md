# 清理 Windows AppData 空间

会话：conv_0e044ee4939b；候选：conv_0e044ee4939b:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：先定位真实占用大目录，再区分应用缓存和本地聊天数据，优先应用内清理；删除前告知本地记录可能不可恢复，不能盲删整个 AppData

边界：历史执行顺序未核准；任务成功及新任务复用收益未独立验证

## 原筛选种子 · 用户

u_d25818a0f8c6c69298

我C盘有个隐藏文件夹AppData，占用了我C盘90%的空间，里面有Local、LocalLow、Roaming、Roaming Tencent，有我能清理的么

## 原筛选种子 · 用户

u_0f31a03d0f3372a85a

你说的这些要么占用空间很小要么就找不到，我现在看到Local文件里面DingTalk和Doubao，能删除么

## 原筛选种子 · AI

a_ddb8c6f79169e79aa7

可以清的**大块头**不少，AppData 占C盘 90% 的话，多半是缓存和日志在呲水。按"最值得清 → 慎重清"排个序：

---

## ✅ 放心清（丢了也不影响使用）

| 位置 | 说明 | 能清多少 |
|------|------|---------|
| `Local\Temp` | 临时文件，很多几千个小文件卡成一团 | **常能清 5–50GB** |
| `Local\Microsoft\Windows\INetCache` | IE/Edge 缓存 | 几百 MB |
| `Local\Microsoft\Windows\WER` | Windows 错误报告（崩溃转储） | 1–10GB |
| `Local\CrashDumps` | 程序崩溃 dmp 文件 | 看运气，有时很大 |
| `Local\Microsoft\OneDrive\cache` | OneDrive 缓存 | 可清 |
| `Local\Packages` 下某些应用的 `AC\INetCache` | 微软商店应用的缓存 | 几百 MB |

## ⚠️ 清也可以，但会丢配置

| 位置 | 会丢什么 |
|------|---------|
| **浏览器缓存** (`Chrome`, `Edge`, `Opera` 等) | 登录状态+浏览记录，要重新登 |
| `Local\Microsoft\Windows\DeliveryOptimization\Cache` | Windows 更新 P2P 缓存，可安全清 |
| `Roaming\Microsoft\Teams\Cache` | Teams 缓存，常占 5–20GB |
| `Local\Discord` 的 Cache | Discord 缓存 |

## 🐘 腾讯系——可能是大头

你的 `Roaming Tencent` 里面：
- **微信** (`WeChat` / `WeChat Files`) — **典型 10–60GB**，全是聊天文件缓存
- **QQ** (`QQ` / `QQ Files`) — 同理

**微信清理路径:** 微信设置 → 通用设置 → 存储空间管理 → 清缓存
**不建议直接删文件夹**，微信可能会重建且丢聊天记录资源。

## 🔧 高效清理操作（建议当面远程帮你）

1. **磁盘清理工具（内置安全方案）**
   - 按 Win+R → 输入 `cleanmgr` → 选 C 盘 → 点"清理系统文件" → 勾上所有 → 确定
   - 这里面 **Windows 更新清理** 一项就能释放 10–30GB

2. **用 WizTree / SpaceSniffer 扫一遍**
   - 可视化成块状图，一眼看出谁在吃空间
   - 你先把大块头告诉我，我帮你看能不能删

3. **手动快速清 temp**
   ```
   Win+R → 输入 %temp% → Ctrl+A → Shift+Del
   ```
   跑不掉的跳过，能删的尽删

---

要不你把 **`Roaming Tencent` 下面**和 **`Local\Temp` 大小**先看看？告诉我具体哪些文件夹大，我帮你逐个判断能不能删。

## 原筛选种子 · AI

a_66e54effb95394cc79

这两个确实是常见的大户，直接说结论：

---

## ✅ DingTalk（钉钉）— **可以清，大胆清**

`Local\DingTalk` 里面存的 90% 是：
- 聊天图片/文件缩略图缓存
- 表情包缓存
- 更新包残留
- 日志文件

**操作：**
```
打开钉钉 → 设置 → 文件管理 → 清空缓存
```
或者**直接进 `Local\DingTalk` 删里面的 `Cache`、`Code Cache`、`GPUCache`、`logs` 这些文件夹**，不会丢聊天记录。

如果你看到 `Local\DingTalk\V2\...` 很大，那是钉钉存的实际聊天文件——删了会丢已下载的文件，但聊天文字记录在服务器上。

---

## ✅ Doubao（豆包）— **可以清**

豆包的本地缓存主要是：
- AI 对话历史缓存
- 模型预加载数据
- 日志

**要权衡的是：** 清了之后，之前的聊天记录本地就没了（云端不一定保留全部历史）。

**操作：** 直接在豆包应用里找清理缓存的选项，或者进 `Local\Doubao` 删 `Cache`、`logs` 子文件夹。

---

## 动手前先看一眼大小

因为这俩的**实际大小差别很大**——有的用户 DingTalk 只有几百 MB，有的能到 20GB+。你先：

```
打开 C:\Users\你的用户名\AppData\Local
→ 右键 DingTalk → 属性 → 看大小
→ 右键 Doubao → 属性 → 看大小
```

告诉我各自多大，我教你怎么精准清。也顺便看看 `Local` 里还有没有别的大家伙。
