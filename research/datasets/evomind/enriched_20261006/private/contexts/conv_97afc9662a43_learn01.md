# 抢票技能安装候选功能核查

会话：conv_97afc9662a43；候选：conv_97afc9662a43:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：同名候选可能仅查询，读源码功能而非名称确认购票能力；SPA难抓包时用官方v1搜索拿准确slug下载，检查包完整性和环境依赖，不能声称已能真实抢票

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 原筛选种子 · 用户

u_214b62d2ad48e6e04a

请安装 skill「火车票自动抢」到个人工作区 skills 目录（workspace/skills）：优先平台技能库与市场，没有再从 ClawdHub 或者 GitHub 下载安装

## 原筛选种子 · AI

a_dbff86f03730bba4f5

ClawHub API 路由需要确认，GitHub 上的 `12306-Skill` 是查询类技能（不是自动抢票）。我继续深挖：先找 ClawHub 正确的搜索方式，再用 GitHub 搜索「火车票自动抢」相关的 AgentSkill。

## 原筛选种子 · AI

a_dd867063637ff098f2

找到下载 API 了：`GET /api/v1/download?slug=...`。下载前先检查该技能的安全审查状态（verify 端点），再决定是否安装。

## 原筛选种子 · AI

a_6d50e12034b5bd28f9

技能包完整（SKILL.md + adb_helper.py + skill-card.md + _meta.json），许可证 MIT-0，ClawHub 安全扫描无恶意标记。现在安装到工作区 `skills/` 目录。

## 对应关系扩入上下文 · AI

a_eb8b1471327cae104b

✅ 技能「火车票自动抢」已安装完成！

## 安装结果

**安装路径：** `workspace/skills/12306-android-adb/`（即「我的技能」目录）

```
skills/12306-android-adb/
├── SKILL.md          ← 核心技能说明（自动抢票流程）
├── adb_helper.py     ← ADB 自动化辅助脚本（288 行，语法已验证）
├── skill-card.md     ← 发布者信息与安全提示（MIT-0 许可）
└── _meta.json        ← ClawHub 版本元数据（v1.0.1）
```

## 查找过程（按您要求的优先级）

1. **平台技能库**：100+ 内置技能中无火车票相关 → 跳过
2. **ClawHub 市场**：搜索「12306 / 抢票 / 火车票 / train / ticket」共 30+ 个候选，逐一筛选：
   - ✅ **选中 `openlittlebear/12306-android-adb`**（⬇711 下载，安全扫描无恶意标记）——唯一真正「自动抢票」类技能
   - ❌ 排除 `alinklab/12306-ticket-purchase-search`（安全审查警告：明文存储 API key）
   - ❌ 其余多为「余票查询」类（如 kirorab/12306），不含抢票能力
3. **GitHub 备选**：`ArtLjn/12306-Skill` 等均为查询类，不如 ClawHub 候选匹配，未采用

## 技能能做什么

通过 **ADB / uiautomator2** 控制安卓手机上的官方 12306 App，自动完成：搜索车票 → 定位目标车次的「预订」按钮（含 UC WebView 虚拟列表的坑位处理）→ 处理静音车厢弹窗 → 选择乘车人 → 提交订单。**支付环节保留人工确认**（跳转支付宝/微信）。

## ⚠️ 使用前提（需要您知晓）

- 需要一台**已开启 USB 调试的安卓手机**，装有 12306 App
- 安装 `uiautomator2`：`pip install uiautomator2`
- 技能描述中提到可选的 `appium-android-adb` 桥接技能（未安装，主流程用 uiautomator2 即可，不需要它）
- 每次下单前请人工确认步骤，避免误操作真实购票

如需要，我也可以帮您把这个技能改名为更直观的中文描述，或补充一个「启动前环境检查」脚本。
