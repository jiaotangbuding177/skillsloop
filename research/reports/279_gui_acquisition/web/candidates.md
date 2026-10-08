# RecreationWorld 对应训练应用：Web 来源候选

日期：2026-10-04。只获取公开仓库元数据、固定commit文档和少量本地核心源码证据；未运行候选应用、模型、复刻任务、评分或学习。旧267 STOP不恢复。机器化清单见[selected_candidates.json](selected_candidates.json)，去重和规模摘要见[source_identity_audit.json](source_identity_audit.json)。

## 筛选结论

选4个来源候选：3个工具型浏览器应用，加1个更直接对应Web文档站子分布的Vite文档站。三工具具有本地处理机制，文档站具有可构建多路由导航；四者许可证与来源已固定。当前只通过文档/源码侧筛选，**运行准入0、轨迹采集0、技能产物0**。开源、star和可构建文档不能替代实际启动/离线/交互验收。

| 候选 | 固定commit | 许可 | 固定树文件/字节 | 初步定位 |
|---|---|---|---:|---|
| [Squoosh](https://github.com/GoogleChromeLabs/squoosh) | e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3 | Apache-2.0 | 428 / 43,370,978 | 图片导入、异步预览、压缩、导出 |
| [miniPaint](https://github.com/viliusle/miniPaint) | a79733eb803fc97084ef0ee4faa96b031e69e1c0 | MIT | 292 / 6,887,663 | 多菜单、画布工具、图层、undo、文件保存 |
| [StackEdit](https://github.com/benweet/stackedit) | 6dce2a5e36b755a0c244522b48a06c91a2df0f59 | Apache-2.0 | 370 / 3,522,929 | 多文档导航、Markdown预览、本地持久化 |
| [Vite docs](https://github.com/vitejs/vite/tree/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/docs) | fdb2e6f63894d8c458c1778f3df77afe537f2bb2（v8.0.7） | MIT | 2,600 / 16,952,726（monorepo） | 文档导航、目录、锚点、深层路由、浏览器历史 |

前三项表中字节为GitHub固定源码树blobs大小合计，不含git历史/node_modules，不是压缩包大小；tree均truncated=false。根线程实际已获取的四项压缩包分别22,350,386 / 4,252,920 / 1,896,539 / 12,699,216字节，共41,199,061字节，SHA与展开清单见[来源获取manifest](../source_acquisition_manifest.json)。Vite固定release全monorepo归档展开跳过1条symlink，候选GUI范围仅docs/；不把全部源码文件当文档站任务数。GitHub repository size不能冒充本次下载量。

## 1. Squoosh：文件输入—异步状态—产物验证

[固定README](https://github.com/GoogleChromeLabs/squoosh/blob/e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3/README.md)明确图片处理在本地完成；[package.json](https://github.com/GoogleChromeLabs/squoosh/blob/e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3/package.json)给出Rollup构建和静态serve，[move-output.js](https://github.com/GoogleChromeLabs/squoosh/blob/e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3/lib/move-output.js)将静态构建移到build目录，固定.nvmrc为20.16.0。无需使用真实图片或企业资料，以构造PNG文件即可验收。

拟观察的公开流程：导入PNG→改变宽高→选编码/质量→比较预览→下载→重新打开校验尺寸/MIME；另观察左右预览和缩放、替换文件后的状态。精确控件/默认值尚需实测，不把研究人员设想当该commit已验证行为。

预期抽取素材是agent在复刻过程中对输入—控件—预览—输出依赖、异步worker和二进制下载的识别、实现、失败修正与检查，不只是“操作图片工具”的短动作脚本。可泛化候选包括：先建立状态依赖图；校验产物尺寸/格式而非只截图；在移动端与桌面端检查同一控件行为。是否真正抽取出这些技能和是否对测试有效均未知。

风险：WASM/依赖供应链尚未离线验收；官方README披露Analytics，运行时须外网隔离，不能把屏蔽遥测变为替代图片算法。与macOS image-shrinker/PhotoFlare、Windows image-viewer有图像导入/参数/输出的能力交集，但跨平台迁移只是假设。

## 2. miniPaint：菜单—选择工具—图层—撤销

[固定README](https://github.com/viliusle/miniPaint/blob/a79733eb803fc97084ef0ee4faa96b031e69e1c0/README.md)列出层、undo、图片尺寸/变换、文件导出和快捷键。固定[index.html](https://github.com/viliusle/miniPaint/blob/a79733eb803fc97084ef0ee4faa96b031e69e1c0/index.html)直接加载本地dist/bundle.js，仓库含dist；[package.json](https://github.com/viliusle/miniPaint/blob/a79733eb803fc97084ef0ee4faa96b031e69e1c0/package.json)给出webpack生产构建。静态资源存在不是启动成功实证。

[MIT-LICENSE.txt](https://github.com/viliusle/miniPaint/blob/a79733eb803fc97084ef0ee4faa96b031e69e1c0/MIT-LICENSE.txt)的完整MIT文本已获取并核对。GitHub API给NOASSERTION是许可识别不足，不能据此说无许可证；README与package也明确MIT。

拟观察流程：本地导入→resize/crop→undo→PNG导出重开；新建两层→活跃层绘制→切换可见性/顺序→保存JSON层数据→重开。第三流程可观察工具颜色/尺寸、缩放后画布坐标和菜单键盘操作。具体是否支持每条分支以公开UI验收为准。

预期素材是独立复刻时的状态同步、事件坐标换算、可撤销操作、层与最终合成结果的检查；可泛化到多面板GUI而不依赖复制目标DOM。与ubuntu ksnip、macOS PhotoFlare、Windows BMPEditor的相关性是公共GUI能力映射；不是同题、同框架或分数等价证明。

风险：hermite-resize为git依赖，须锁住原lock和发布bundle；webfontloader等可选外部资源需要隔离验证；全应用功能多于首批流程，若只评局部应明确训练任务范围，不能伪称完整应用已复刻。

## 3. StackEdit：导航树—文本编辑—预览—本地状态

[固定README](https://github.com/benweet/stackedit/blob/6dce2a5e36b755a0c244522b48a06c91a2df0f59/README.md)给本地npm启动与生产构建；[固定LICENSE](https://github.com/benweet/stackedit/blob/6dce2a5e36b755a0c244522b48a06c91a2df0f59/LICENSE)为Apache-2.0。源码[localDbSvc.js](https://github.com/benweet/stackedit/blob/6dce2a5e36b755a0c244522b48a06c91a2df0f59/src/services/localDbSvc.js)实际打开IndexedDB并维护localStorage，证明有本地存储路径，不只借用项目宣传。

拟观察流程：新建Markdown→标题/列表/代码→预览→重命名→刷新重开；两文件/目录移动→切换/搜索→核对内容归属；import .md→编辑/undo→export→回读比较。目录、恢复、搜索等精确控件尚未运行核验，unsupported分支须在正式冻结前删除而不伪造行为。

预期素材是agent为复刻建模多pane状态、文档选择与存储的关系、保证预览与文本同步、按结果而非静态外观检查完成。与ubuntu notepadqq、macOS FSNotes、Android EasyNotes、Windows notetask存在编辑/导航/保存能力交集；框架/平台不同，迁移未证。

风险：固定commit为2023-05-27，Vue2/webpack与旧依赖较老，**不能称当前活跃维护或已构建成功**。README Helm示例出现Google/Dropbox key，但那些属于可选网络集成，不能误报本地编辑必需key；反之必须在独立环境实际核验匿名本地路径。

## 4. Vite docs：文档站导航—目录—深层路由—历史

候选是[固定v8.0.7的docs子站](https://github.com/vitejs/vite/tree/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/docs)，不是让agent操作Vite构建CLI。其[根LICENSE](https://github.com/vitejs/vite/blob/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/LICENSE)为MIT且没有整体图片排除条款；第三方主题/图形资产仍要逐项审计。[docs/package.json](https://github.com/vitejs/vite/blob/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/docs/package.json)原生提供vitepress dev/build/serve；[根package](https://github.com/vitejs/vite/blob/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/package.json)要求Node ^20.19.0或>=22.12.0、pnpm 10.33.0，ci-docs先build再docs-build。依赖与实际构建尚未执行，不能称已运行成功。

[固定config](https://github.com/vitejs/vite/blob/fdb2e6f63894d8c458c1778f3df77afe537f2bb2/docs/.vitepress/config.ts)明确Guide/Config/Plugins顶栏、各section sidebar和二三级heading outline。拟观察流程：Guide→Philosophy→锚点→Back→直接刷新深路由；Guide/Config→多级目录→Resources中的本地Blog→窄视口导航；公开UI确认后才加代码复制/主题切换/持久化。验证要检查URL、激活目录、页面内容、锚点位置、历史和移动布局，不能只测首页外观。

预期技能素材是文档复刻的route/content/sidebar关系、深链接与浏览器history一致性、响应式菜单和锚点行为；公开Web样本webpack/keycloak/rust等站点具有更接近的文档与内容站形式。仍只是能力相关性假设，未经训练及配对评测证明迁移。

config包含外部Algolia搜索、analytics/ads、远程字体与外链，**离线核心仅本地路由/目录/锚点/公开可见状态**；外部搜索不列必需行为，也不做伪本地搜索替代。须在独立网络隔离环境验证本地核心不依赖这些外部服务。原MIT并不免除单独资产/商标/主题许可证检查。

## 与RecreationBench的对应及去重限制

同类任务形式应保持：参考应用只允许公开截图、无障碍信息与正常动作观察→agent独立实现→运行/功能/视觉验证→完整真实轨迹进入AutoSkill。获取目标仓库给研究侧搭参考环境，不等于允许actor直接读目标源码。可选公开操作流程是训练验收设计，不读取或提供benchmark私有测试。

本地官方tasks/web.jsonl为50Web；279公共来源catalog的200原生任务有canonical repo，50Web没有repo且大量.example匿名。前三候选在200repo规范化比较无命中；在全250任务身份和266公开文件路径无名称命中。Vite repo也未命中native200；[Web公开首页身份审计](../web_bench_identity_audit.json)中无上述四项目的明确repo/title匹配。**这不是完整去重**：匿名原站、fork、共享模板/代码关系仍须确认，完成之前不当正式训练—测试隔离已验收。没有读取私有测试、换benchmark题或删旧315/945登记。

Web50公开路径多为营销、文档、多路由站点；前三应用偏工具编辑器，第四Vite docs更接近文档站形式。共享菜单、状态、表单、响应式、键盘和文件行为有研究理由，但不能把“都是Web”升为同分布证据。应将工具训练/内容站测试的domain差异、VitePress或主题家族可能重叠作为显式分层与未知项，不盲称应用家族隔离完成。

## 暂不选的候选

| 仓库 | 已核到 | 本轮处理 |
|---|---|---|
| Laverna/laverna | 9e2caf95d69ab77fad24f7128f171621bb340445，MPL-2.0，离线笔记 | 同StackEdit领域且旧依赖，备选，未运行 |
| gchq/CyberChef | 609951ac13967da6d497e0600c922f56bfd0b7af，Apache-2.0，全client-side | 成熟但全功能/构建规模大，首批暂不选，不能只用Base64就宣称复刻全产品 |
| parthlashkari/taskflow | 07c47f325909ef5bb7dfc01539c8a6511dce0b5d，README称MIT/metadata license=null | 未取得独立LICENSE且0stars的新项目，本轮不作为高质量已验明样本 |
| Flowy/TUI Image Editor | 官方库有完整示例界面 | 库/组件示例和完整应用层级不同，暂不凑候选数量 |
| vuejs/docs | 40aa88af0094f7bab4aaf786e55c748a6a251d88，LICENSE为CC-BY-4.0但明确排除全部图片 | 图片授权缺口未解决，作为附加候补而不进入主池；未下载/启动整站 |

本轮结论只到来源筛选。下一步由独立准备协议固定源码、依赖、离线网络、输入fixtures、公开观察流程与训练验证器；无凭据/core断网行为实测通过后才入运行池。同一具体应用最多三轮含首次，失败如实保留，不用换版本重置；素材可以是失败学习经验，不能写成成功SFT数据或承诺多个skills。
