import {
  BadRequestException,
  Controller,
  ForbiddenException,
  Post,
  Req,
  UseGuards,
} from "@nestjs/common";
import { JwtAuthGuard } from "../auth/jwt-auth.guard.js";
import { SkillEmergenceAccessService } from "../skill-emergence/skill-emergence-access.service.js";
import { SkillEmergencePackagingService } from "../skill-emergence/skill-emergence-packaging.service.js";
import { SkillEmergenceScheduler } from "../skill-emergence/skill-emergence.scheduler.js";
import type { SkillEmergenceProcessSummary } from "./skill-emergence-processor.service.js";
import { SkillEmergenceProcessor } from "./skill-emergence-processor.service.js";

/**
 * 一键把涌现全链路强制跑一轮（归类 → 路径建模 → 门禁评估 → 封装），并回报**每一步的明细**
 * ——不只是计数，还包括每个聚类「为什么没沉淀出技能」和「下一步该做什么」。
 *
 * 存在的理由：正常涌现要等上海零点周期，测试与排障时无从判断卡在哪一步；更糟的是评估
 * 只覆盖已建模的聚类，用户看到「评估 0 个」时无法知道是没采集、没归类还是没建模。
 *
 * **访问控制复用企业涌现开关**（`resolveAccess`），不引入额外的运维开关——
 * 能用涌现的组织就能立刻跑一轮，不能用涌现在本就不能用，语义一致。
 * 这与平台超管后台的「主动触发涌现」（按企业批量）是两条路径，互不影响。
 *
 * **为什么这个控制器住在 skill-analytics 而不是 skill-emergence**：它要同时拿到
 * `SkillEmergenceProcessor`（provider 在 `SkillAnalyticsModule`）与 Scheduler / Packaging
 * （由 `SkillEmergenceModule` export）。依赖方向是单向的 analytics → emergence；把端点
 * 搬进 emergence 模块就得反向 import，制造模块循环。**搬走会破依赖方向，故留在此处。**
 * 路由前缀与目录无关，仍是 `/api/skill-emergence/test/trigger`。
 */
@Controller("skill-emergence")
@UseGuards(JwtAuthGuard)
export class SkillEmergenceTestTriggerController {
  constructor(
    private readonly access: SkillEmergenceAccessService,
    private readonly processor: SkillEmergenceProcessor,
    private readonly scheduler: SkillEmergenceScheduler,
    private readonly packaging: SkillEmergencePackagingService,
  ) {}

  @Post("test/trigger")
  async trigger(@Req() req: any) {
    const userId = req.user?.userId as string | undefined;
    if (!userId) {
      throw new BadRequestException("未登录");
    }
    const enterpriseId = this.access.requireEnterpriseId(req);

    // 与自动涌现同一把开关：未开启时不是「接口不存在」，而是「这个组织还不能涌现」——
    // 如实说明比伪装 404 更有用，因为使用者能看到按钮，需要知道为什么按不动。
    const access = await this.access.resolveAccess(userId, enterpriseId);
    if (!access.allowed) {
      throw new BadRequestException(
        access.source === "user_preference"
          ? "你还没有开启 Skill 自动涌现，请先在个人设置里打开"
          : "当前组织未开启 Skill 自动涌现，请联系企业管理员在基础设置中开启",
      );
    }

    // 作用域与权限必须匹配：归类与封装是**全平台**扫描（不按企业过滤），所以只有
    // 「有权改变涌现行为的人」才能触发它——B 端是管理员/所有者，C 端是用户本人。
    // 只验 `allowed` 不够：普通成员也能满足它，却会让自己的点击触发全平台 LLM 与计费工作。
    if (!access.canToggleEnterprise && !access.canTogglePreference) {
      throw new ForbiddenException(
        "只有企业管理员或所有者可以手动触发涌现评估",
      );
    }

    // 顺序固定：先归类建模（评估只认 path_analyzed 的聚类，反序会得到 evaluated: 0），
    // 再评估，最后封装（评估新建的候选在入队时已直接执行，这里兜的是历史积压任务）。
    const analysis: SkillEmergenceProcessSummary = await this.processor.processPending();
    const evaluation = await this.scheduler.enqueueEvaluateNow(userId, enterpriseId);
    const packaging = await this.packaging.processDueJobs();

    return {
      enabled: true as const,
      analysis,
      evaluation,
      packaging,
      note:
        "归类与封装是全局扫描（不只处理你一个人的数据）；门禁评估按「当前用户 × 企业」执行。" +
        "标记为「已在运行」的阶段说明后台 worker 正巧在跑同一轮，稍后重试即可。",
    };
  }
}
