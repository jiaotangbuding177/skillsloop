import { Module } from '@nestjs/common';
import { AdminGuard } from '../auth/admin.guard.js';
import { DatabaseModule } from '../infra/database.module.js';
import { EnterpriseModule } from '../enterprises/enterprise.module.js';
import { ZclawModule } from '../zclaw/zclaw.module.js';
import {
  SkillAdminController,
  SkillDisplayController,
  SkillEnterpriseAdminController,
  SkillMarketController,
  SkillPersonalConfigController,
  SkillSubmissionController,
} from './skill.controller.js';
import { SkillImportService } from './skill-import.service.js';
import { SkillInitTemplateService } from './skill-init-template.service.js';
import { SkillPersonalConfigService } from './skill-personal-config.service.js';
import { SkillSubmissionService } from './skill-submission.service.js';
import { SkillTemplateAdminController } from './skill-template.controller.js';
import { SkillTemplateService } from './skill-template.service.js';
import { SkillService } from './skill.service.js';

@Module({
  imports: [DatabaseModule, EnterpriseModule, ZclawModule],
  controllers: [
    SkillAdminController,
    SkillTemplateAdminController,
    SkillEnterpriseAdminController,
    SkillDisplayController,
    SkillMarketController,
    SkillSubmissionController,
    SkillPersonalConfigController,
  ],
  providers: [
    AdminGuard,
    SkillService,
    SkillTemplateService,
    SkillInitTemplateService,
    SkillSubmissionService,
    SkillPersonalConfigService,
    SkillImportService,
  ],
  exports: [
    SkillService,
    SkillTemplateService,
    SkillInitTemplateService,
    SkillSubmissionService,
    SkillPersonalConfigService,
    SkillImportService,
  ],
})
export class SkillModule {}
