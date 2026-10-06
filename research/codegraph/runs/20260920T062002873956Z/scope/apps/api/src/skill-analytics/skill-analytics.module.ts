import { Module, forwardRef } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { AgentModule } from "../agent/agent.module.js";
import { DatabaseModule } from "../infra/database.module.js";
import { SkillEmergenceModule } from "../skill-emergence/skill-emergence.module.js";
import { SkillAnalyticsRecorder } from "./skill-analytics-recorder.service.js";
import { SkillEmergenceProcessor } from "./skill-emergence-processor.service.js";
import { SkillEmergenceRecorder } from "./skill-emergence-recorder.service.js";
import { SkillEmergenceTestTriggerController } from "./skill-emergence-test-trigger.controller.js";

@Module({
  imports: [
    ConfigModule,
    DatabaseModule,
    AgentModule,
    forwardRef(() => SkillEmergenceModule),
  ],
  controllers: [SkillEmergenceTestTriggerController],
  providers: [SkillAnalyticsRecorder, SkillEmergenceRecorder, SkillEmergenceProcessor],
  exports: [SkillAnalyticsRecorder, SkillEmergenceRecorder],
})
export class SkillAnalyticsModule {}
