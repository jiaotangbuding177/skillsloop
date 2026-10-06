# 扫描合同公司名与倒置附录核验

会话：conv_aad48418bf73；候选：conv_aad48418bf73:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：扫描中文公司名出现歧义时对照英文拼音和登记信息，不能凭OCR猜实体；附录倒置先旋转再OCR，翻译对象与未可读部分分别记录

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 原筛选种子 · 用户

u_501aa3ea38ae00694a

帮我翻译一下这份文件
[附加文件: Springbok_Onshore Holdco Joint Venture Agreement_Signed【签署版】.pdf (/workspace/对话附件/Springbok_Onshore Holdco Joint Venture Agreement_Signed【签署版】.pdf)]

## 原筛选种子 · 用户

u_3d6c251aa1869664e9

翻译好了吗

## 原筛选种子 · AI

a_d8ce7bbac64d650846

让我用第二个 OCR 引擎（easyocr）交叉验证这两个公司名的汉字，确保准确：

## 原筛选种子 · AI

a_e403029a5f46bbb15d

换最后一种客观校验——直接放大第4页的英文名，确认到底是 Lianguang 还是 Liangguang：

## 原筛选种子 · AI

a_4b3bf50fcf73583495

这两个公司名通过谐音交叉验证基本锁定（与英文拼音完全吻合）。最后用工商登记信息快速核实一下：

## 原筛选种子 · AI

a_5abfc2a6ad2abf2f19

附件6（初始业务计划）在原件中倒置，我旋转后重新识别；同时继续读取附件9定义部分：
