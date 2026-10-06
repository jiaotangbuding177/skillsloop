# conv_a53e75e3ce15:learn01：Unity第一人称角色控制器

会话：conv_a53e75e3ce15

本轮可学习：复用状态实例避免状态转换分配，对大量子弹用对象池；满屏子弹不挂TrailRenderer，效果改用Mesh拖尾并独立验证帧率

原文依据：别给子弹挂 TrailRenderer

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：原始时序未独立核验；附件与产物字节未提供；方法适用性及任务结果未独立验收

## 用户需求／反馈

来源消息组：u_6aa33c17f4e74fa2e2

用 game-developer 技能，帮我用 Unity 写一个 FPS 的角色控制器，要求：第一人称移动+跳跃+冲刺，带状态机，敌人子弹多要对象池，性能要稳 60 帧

## AI处理／结果

来源消息组：a_e757d62baef85a904e

搞定老板 ✅ 完整方案已交付，共 16 个 C# 脚本 + README，位于：

📁 `AI 工作区/成果文件/用 game-developer 技能，-conv_a53e75e3ce15/2026-09-05_UnityFPS角色控制器/`

## 架构一览

**状态机**（字典注册 + Exit/Enter 转移，状态实例永久复用零分配）：
- `LocomotionState` — 待机/行走/冲刺（Shift 长按）
- `AirborneState` — 跳跃/下落，带**土狼时间**、**跳跃缓冲**、**跳砍**（可变跳高）
- `DashState` — 冲刺技（Ctrl/C），方向跟随输入、空中可用、撞墙提前结束、冷却 0.9s
- 状态只改"速度意图"，位移统一由 `FirstPersonPlayer.Integrate()` 执行，杜绝状态间位移打架

**子弹对象池**：通用 `ObjectPool<T>`（预热 96 + 上限 512 防刷爆）→ 场景单例 `ProjectilePool` 给所有 `EnemyShooter` 共用。子弹每帧用共享缓冲的 `SphereCastNonAlloc` 探测碰撞——**没有 Rigidbody、没有触发器回调**，高速不穿透，命中/超时自动回池。

**60 FPS 保障**（代码侧已做满）：
- Update 内零 GetComponent / Find / Instantiate / Destroy / LINQ
- 玩家用 CharacterController（比 Rigidbody 省物理开销），重力手写
- 敌人错峰开火防帧尖峰；`FpsStabilizer` 启动锁 60 + 防死亡螺旋
- `PerformanceMonitor`（F3）盯着 Alloc 列——运行时每帧分配应 ≈ 0 B

## 上手三步

1. 工程设置切 `Input Manager (Old)`，建 `Player`/`Enemy` 两个 Layer
2. 按 README 层级搭 Player（CC + 三脚本 + CameraRig 眼睛高度 1.6m）和 Enemy
3. 做 Bullet 预制体（初始 inactive，挂 EnemyBullet），拖进 ProjectilePool → 开跑

操作：WASD 移动 / Space 跳 / Shift 冲刺 / Ctrl 滑步 / 左键射击。手感参数全部集中在 `PlayerSettings` 资产里调。README 里有完整场景搭建表 + 引擎侧优化清单（遮挡剔除、GPU Instancing 等）。

一个提醒：README 里标了**别给子弹挂 TrailRenderer**——满屏拖尾是帧率杀手，想加特效建议用 Mesh 拖尾。需要我再补脚步声、动画联动或弹药系统就说一声 🎮
