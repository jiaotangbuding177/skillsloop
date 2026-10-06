import { forwardRef, Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { AdminGuard } from "../auth/admin.guard.js";
import { JwtAuthGuard } from "../auth/jwt-auth.guard.js";
import { DatabaseModule } from "../infra/database.module.js";
import { SkillEmergenceAccessService } from "./skill-emergence-access.service.js";
import { SkillEmergenceController } from "./skill-emergence.controller.js";
import { SkillEmergenceEvaluatorService } from "./skill-emergence-evaluator.service.js";
import { SkillEmergencePackagingService } from "./skill-emergence-packaging.service.js";
import { SkillEmergenceReliabilityService } from "./skill-emergence-reliability.service.js";
import { SkillEmergenceScheduler } from "./skill-emergence.scheduler.js";
import { ZclawModule } from "../zclaw/zclaw.module.js";

@Module({
  imports: [ConfigModule, DatabaseModule, forwardRef(() => ZclawModule)],
  controllers: [SkillEmergenceController],
  providers: [
    JwtAuthGuard,
    AdminGuard,
    SkillEmergenceAccessService,
    SkillEmergencePackagingService,
    SkillEmergenceEvaluatorService,
    SkillEmergenceScheduler,
    SkillEmergenceReliabilityService,
  ],
  exports: [
    SkillEmergenceAccessService,
    SkillEmergenceEvaluatorService,
    SkillEmergencePackagingService,
    SkillEmergenceScheduler,
    SkillEmergenceReliabilityService,
  ],
})
export class SkillEmergenceModule {}
