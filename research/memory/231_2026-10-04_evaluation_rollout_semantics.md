# 第231轮：公开运行轨迹是评测任务上的执行记录

用户询问“执行、轨迹记录”是不是评测数据的执行结果。本轮核对本地固定官方docs/providers/web.md：当前公开命令读取RecreationBench评测任务，输出metrics.json、trajectory、workspace、evaluation artifacts和tool-use screenshots。来源对应[官方Web指南](https://github.com/QwenLM/RecreationWorld/blob/main/docs/providers/web.md)。

澄清：运行输入是评测任务包，trajectory是agent本次探索/编码/工具交互过程，workspace为交付产物，metrics与evaluation artifacts为后续官方测试/裁判结果。并非公开包自带论文35,000训练轨迹，也不能把轨迹当成评分测试本身。执行框架能力与论文训练任务池公开性分开。

若将某些评测任务执行轨迹用于AutoSkill学习，则这些题属于本实验学习来源，不能随后作为该库的独立held-out泛化评测；可另设预先冻结且无来源重叠的学习/评测子集，但属于派生实验，不再是全部250题held-out。私有测试/gold不得进入学习。未改分集、未执行或重启任务；本轮无新增实验实证发现。官方train获取缺口见229调研。
