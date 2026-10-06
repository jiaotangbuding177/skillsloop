import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
  Put,
  Query,
  Req,
  UploadedFiles,
  UseGuards,
  UseInterceptors,
} from '@nestjs/common';
import { FilesInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { AdminGuard } from '../auth/admin.guard.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { SaveEnterpriseSkillDto } from './dto/save-enterprise-skill.dto.js';
import { SaveGlobalSkillDto } from './dto/save-global-skill.dto.js';
import { SaveSkillCategoryDto } from './dto/save-skill-category.dto.js';
import { UpdateEnterpriseSkillCategorySettingsDto } from './dto/update-enterprise-skill-category-settings.dto.js';
import { ApplySkillInitTemplatesDto } from './dto/apply-skill-init-templates.dto.js';
import { PullSkillInitTemplatesDto } from './dto/pull-skill-init-templates.dto.js';
import { SaveSkillInitTemplateDto } from './dto/save-skill-init-template.dto.js';
import { UpdateSkillDto } from './dto/update-skill.dto.js';
import { MigrateSkillCategoryDto } from './dto/migrate-skill-category.dto.js';
import { MoveSkillCategorySkillsDto } from './dto/move-skill-category-skills.dto.js';
import { ApproveSkillSubmissionDto } from './dto/approve-skill-submission.dto.js';
import { RejectSkillSubmissionDto } from './dto/reject-skill-submission.dto.js';
import { ResubmitSkillVersionDto } from './dto/resubmit-skill-version.dto.js';
import { SubmitSkillDto } from './dto/submit-skill.dto.js';
import { SkillImportService } from './skill-import.service.js';
import { SkillInitTemplateService } from './skill-init-template.service.js';
import { SavePersonalSkillDto } from './dto/save-personal-skill.dto.js';
import { SkillPersonalConfigService } from './skill-personal-config.service.js';
import { SkillSubmissionService } from './skill-submission.service.js';
import { SkillService } from './skill.service.js';
import type { SkillPoolPurpose } from './skill-pool.js';
import { SKILL_ZIP_BATCH_LIMIT, SKILL_ZIP_MAX_BYTES } from './skill-zip.util.js';

function parseOverwriteSkillKeys(raw: unknown): string[] {
  if (typeof raw !== 'string' || !raw.trim()) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === 'string');
  } catch {
    return raw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }
}

function parseBooleanFormField(raw: unknown, fallback: boolean) {
  if (typeof raw !== 'string') return fallback;
  const value = raw.trim().toLowerCase();
  if (value === 'true' || value === '1') return true;
  if (value === 'false' || value === '0') return false;
  return fallback;
}

function parseSortOrderFormField(raw: unknown) {
  if (typeof raw !== 'string' || !raw.trim()) return 0;
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

@Controller('enterprises/admin/skills')
@UseGuards(JwtAuthGuard, AdminGuard)
export class SkillAdminController {
  constructor(
    private readonly skillService: SkillService,
    private readonly skillInitTemplateService: SkillInitTemplateService,
    private readonly skillSubmissionService: SkillSubmissionService,
    private readonly skillImportService: SkillImportService,
  ) {}

  @Get('submissions')
  async listSubmissionsForAdmin(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Query('status') status?: string,
  ) {
    return this.skillSubmissionService.listForAdmin(req.user.userId, enterpriseId, {
      status,
      bypassMembership: true,
    });
  }

  @Get('submissions/:submissionId')
  async getSubmissionForAdmin(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.getForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      { bypassMembership: true },
    );
  }

  @Post('submissions/:submissionId/approve')
  async approveSubmissionForAdmin(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: ApproveSkillSubmissionDto,
  ) {
    return this.skillSubmissionService.approveForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      dto,
      { bypassMembership: true },
    );
  }

  @Post('submissions/:submissionId/reject')
  async rejectSubmissionForAdmin(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: RejectSkillSubmissionDto,
  ) {
    return this.skillSubmissionService.rejectForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      dto,
      { bypassMembership: true },
    );
  }

  @Post('submissions/:submissionId/remove-from-org')
  async removeSubmissionFromOrgForAdmin(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.removeFromOrgForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      { bypassMembership: true },
    );
  }

  @Delete('submissions/:submissionId')
  async deleteSubmissionForAdmin(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.deleteForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      { bypassMembership: true },
    );
  }

  @Post('import-zips')
  @UseInterceptors(
    FilesInterceptor('files', SKILL_ZIP_BATCH_LIMIT, {
      storage: memoryStorage(),
      limits: { fileSize: SKILL_ZIP_MAX_BYTES, files: SKILL_ZIP_BATCH_LIMIT },
    }),
  )
  async importSkillZipsForAdmin(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Body() body: Record<string, unknown>,
    @UploadedFiles() files?: Express.Multer.File[],
  ) {
    return this.skillImportService.importZipsForAdmin(
      req.user.userId,
      enterpriseId,
      files ?? [],
      {
        categoryId: typeof body.categoryId === 'string' ? body.categoryId : '',
        categoryName: typeof body.categoryName === 'string' ? body.categoryName : '',
        title: typeof body.title === 'string' ? body.title : undefined,
        description: typeof body.description === 'string' ? body.description : undefined,
        isVisible: parseBooleanFormField(body.isVisible, true),
        isHot: parseBooleanFormField(body.isHot, false),
        sortOrder: parseSortOrderFormField(body.sortOrder),
        overwriteSkillKeys: parseOverwriteSkillKeys(body.overwriteSkillKeys),
      },
      { bypassMembership: true },
    );
  }

  @Get('categories')
  async listGlobalCategories(@Req() req: any) {
    return this.skillService.listGlobalCategories(req.user.userId);
  }

  @Get('categories/:categoryId/skills')
  async listGlobalCategorySkills(@Req() req: any, @Param('categoryId') categoryId: string) {
    return this.skillService.listGlobalCategorySkills(req.user.userId, categoryId);
  }

  @Post('categories/:categoryId/migrate')
  async migrateGlobalCategorySkills(
    @Req() req: any,
    @Param('categoryId') categoryId: string,
    @Body() dto: MigrateSkillCategoryDto,
  ) {
    return this.skillService.migrateGlobalCategorySkills(req.user.userId, categoryId, dto);
  }

  @Post('categories/:categoryId/skills/move')
  async moveGlobalCategorySkills(
    @Req() req: any,
    @Param('categoryId') categoryId: string,
    @Body() dto: MoveSkillCategorySkillsDto,
  ) {
    return this.skillService.moveGlobalCategorySkills(req.user.userId, categoryId, dto);
  }

  @Post('categories')
  async createGlobalCategory(@Body() dto: SaveSkillCategoryDto) {
    return this.skillService.createGlobalCategory(dto);
  }

  @Patch('categories/:categoryId')
  async updateGlobalCategory(
    @Param('categoryId') categoryId: string,
    @Body() dto: SaveSkillCategoryDto,
  ) {
    return this.skillService.updateGlobalCategory(categoryId, dto);
  }

  @Delete('categories/:categoryId')
  async deleteGlobalCategory(@Param('categoryId') categoryId: string) {
    return this.skillService.deleteGlobalCategory(categoryId);
  }

  @Get('available')
  async listAvailableSkillsForAdmin(
    @Req() req: any,
    @Query('keyword') keyword?: string,
    @Query('purpose') purpose?: SkillPoolPurpose,
    @Query('enterpriseId') enterpriseId?: string,
    @Query('includeConfigured') includeConfigured?: string,
  ) {
    return this.skillService.listAvailableSkillsForAdmin(req.user.userId, {
      keyword,
      purpose,
      enterpriseId,
      includeConfigured: includeConfigured === 'true',
      bypassEnterpriseMembership: true,
    });
  }

  @Get('union')
  async listUnionSkills(@Req() req: any) {
    return this.skillService.listUnionSkills(req.user.userId);
  }

  @Get('init-templates')
  async listInitTemplates(@Req() req: any) {
    return this.skillInitTemplateService.listCatalog(req.user.userId);
  }

  @Post('init-templates')
  async upsertInitTemplate(@Body() dto: SaveSkillInitTemplateDto) {
    return this.skillInitTemplateService.upsert(dto);
  }

  @Get('init-templates/org-preview')
  async previewOrgInitTemplates(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId?: string,
  ) {
    return this.skillInitTemplateService.previewOrg(req.user.userId, enterpriseId ?? '');
  }

  @Post('init-templates/apply')
  async applyInitTemplates(@Req() req: any, @Body() dto: ApplySkillInitTemplatesDto) {
    return this.skillInitTemplateService.apply(req.user.userId, dto);
  }

  @Post('init-templates/pull')
  async pullInitTemplates(@Req() req: any, @Body() dto: PullSkillInitTemplatesDto) {
    return this.skillInitTemplateService.pull(req.user.userId, dto);
  }

  @Patch('init-templates/:templateId')
  async updateInitTemplate(
    @Param('templateId') templateId: string,
    @Body() dto: SaveSkillInitTemplateDto,
  ) {
    return this.skillInitTemplateService.update(templateId, dto);
  }

  @Delete('init-templates/:templateId')
  async deleteInitTemplate(@Param('templateId') templateId: string) {
    return this.skillInitTemplateService.remove(templateId);
  }

  @Delete('init-templates/by-skill-key/:skillKey')
  async deleteInitTemplateBySkillKey(@Param('skillKey') skillKey: string) {
    return this.skillInitTemplateService.removeBySkillKey(skillKey);
  }

  @Get()
  async listGlobalSkills(@Req() req: any) {
    return this.skillService.listGlobalSkills(req.user.userId);
  }

  @Get('enterprises/:enterpriseId')
  async listEnterpriseSkillsForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
  ) {
    return this.skillService.listEnterpriseSkillsForAdmin(req.user.userId, enterpriseId);
  }

  @Get('enterprises/:enterpriseId/categories')
  async listEnterpriseCategoriesForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
  ) {
    return this.skillService.listEnterpriseCategoriesForAdmin(req.user.userId, enterpriseId);
  }

  @Get('enterprises/:enterpriseId/categories/:categoryId/skills')
  async listEnterpriseCategorySkillsForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
  ) {
    return this.skillService.listEnterpriseCategorySkillsForAdmin(
      req.user.userId,
      enterpriseId,
      categoryId,
    );
  }

  @Post('enterprises/:enterpriseId/categories/:categoryId/migrate')
  async migrateEnterpriseCategorySkillsForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: MigrateSkillCategoryDto,
  ) {
    return this.skillService.migrateEnterpriseCategorySkillsForAdmin(
      req.user.userId,
      enterpriseId,
      categoryId,
      dto,
    );
  }

  @Post('enterprises/:enterpriseId/categories/:categoryId/skills/move')
  async moveEnterpriseCategorySkillsForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: MoveSkillCategorySkillsDto,
  ) {
    return this.skillService.moveEnterpriseCategorySkillsForAdmin(
      req.user.userId,
      enterpriseId,
      categoryId,
      dto,
    );
  }

  @Post('enterprises/:enterpriseId/categories')
  async createEnterpriseCategoryForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Body() dto: SaveSkillCategoryDto,
  ) {
    return this.skillService.createEnterpriseCategoryForAdmin(enterpriseId, dto);
  }

  @Patch('enterprises/:enterpriseId/categories/:categoryId')
  async updateEnterpriseCategoryForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: SaveSkillCategoryDto,
  ) {
    return this.skillService.updateEnterpriseCategoryForAdmin(enterpriseId, categoryId, dto);
  }

  @Delete('enterprises/:enterpriseId/categories/:categoryId')
  async deleteEnterpriseCategoryForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
  ) {
    return this.skillService.deleteEnterpriseCategoryForAdmin(enterpriseId, categoryId);
  }

  @Patch('enterprises/:enterpriseId/category-settings')
  async updateEnterpriseSkillCategorySettingsForAdmin(
    @Req() req: any,
    @Param('enterpriseId') enterpriseId: string,
    @Body() dto: UpdateEnterpriseSkillCategorySettingsDto,
  ) {
    return this.skillService.updateEnterpriseSkillCategorySettingsForAdmin(
      req.user.userId,
      enterpriseId,
      dto,
    );
  }

  @Post('enterprises')
  async saveEnterpriseSkillForAdmin(@Req() req: any, @Body() dto: SaveEnterpriseSkillDto) {
    return this.skillService.saveEnterpriseSkillForAdmin(req.user.userId, dto);
  }

  @Patch('enterprises/:enterpriseId/:skillId')
  async updateEnterpriseSkillForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
    @Body() dto: UpdateSkillDto,
  ) {
    return this.skillService.updateEnterpriseSkillForAdmin(enterpriseId, skillId, dto);
  }

  @Delete('enterprises/:enterpriseId/:skillId')
  async deleteEnterpriseSkillForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
  ) {
    return this.skillService.deleteEnterpriseSkillForAdmin(enterpriseId, skillId);
  }

  @Post('enterprises/:enterpriseId/:skillId/reset')
  async resetEnterpriseSkillForAdmin(
    @Param('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
  ) {
    return this.skillService.resetEnterpriseSkillForAdmin(enterpriseId, skillId);
  }

  @Post()
  async saveGlobalSkill(@Req() req: any, @Body() dto: SaveGlobalSkillDto) {
    return this.skillService.saveGlobalSkill(req.user.userId, dto);
  }

  @Patch(':skillId')
  async updateGlobalSkill(@Param('skillId') skillId: string, @Body() dto: UpdateSkillDto) {
    return this.skillService.updateGlobalSkill(skillId, dto);
  }

  @Delete(':skillId')
  async deleteGlobalSkill(@Param('skillId') skillId: string) {
    return this.skillService.deleteGlobalSkill(skillId);
  }
}

@Controller('enterprises/enterprise-admin/skills')
@UseGuards(JwtAuthGuard)
export class SkillEnterpriseAdminController {
  constructor(
    private readonly skillService: SkillService,
    private readonly skillSubmissionService: SkillSubmissionService,
    private readonly skillImportService: SkillImportService,
  ) {}

  @Post('import-zips')
  @UseInterceptors(
    FilesInterceptor('files', SKILL_ZIP_BATCH_LIMIT, {
      storage: memoryStorage(),
      limits: { fileSize: SKILL_ZIP_MAX_BYTES, files: SKILL_ZIP_BATCH_LIMIT },
    }),
  )
  async importSkillZips(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Body() body: Record<string, unknown>,
    @UploadedFiles() files?: Express.Multer.File[],
  ) {
    return this.skillImportService.importZipsForAdmin(
      req.user.userId,
      enterpriseId,
      files ?? [],
      {
        categoryId: typeof body.categoryId === 'string' ? body.categoryId : '',
        categoryName: typeof body.categoryName === 'string' ? body.categoryName : '',
        title: typeof body.title === 'string' ? body.title : undefined,
        description: typeof body.description === 'string' ? body.description : undefined,
        isVisible: parseBooleanFormField(body.isVisible, true),
        isHot: parseBooleanFormField(body.isHot, false),
        sortOrder: parseSortOrderFormField(body.sortOrder),
        overwriteSkillKeys: parseOverwriteSkillKeys(body.overwriteSkillKeys),
      },
    );
  }

  @Get('submissions')
  async listSubmissions(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Query('status') status?: string,
  ) {
    return this.skillSubmissionService.listForAdmin(req.user.userId, enterpriseId, { status });
  }

  @Get('submissions/:submissionId')
  async getSubmission(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.getForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
    );
  }

  @Post('submissions/:submissionId/approve')
  async approveSubmission(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: ApproveSkillSubmissionDto,
  ) {
    return this.skillSubmissionService.approveForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      dto,
    );
  }

  @Post('submissions/:submissionId/reject')
  async rejectSubmission(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: RejectSkillSubmissionDto,
  ) {
    return this.skillSubmissionService.rejectForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
      dto,
    );
  }

  @Post('submissions/:submissionId/remove-from-org')
  async removeSubmissionFromOrg(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.removeFromOrgForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
    );
  }

  @Delete('submissions/:submissionId')
  async deleteSubmission(
    @Req() req: any,
    @Param('submissionId') submissionId: string,
    @Query('enterpriseId') enterpriseId: string,
  ) {
    return this.skillSubmissionService.deleteForAdmin(
      req.user.userId,
      submissionId,
      enterpriseId,
    );
  }

  @Get('categories')
  async listEnterpriseCategories(@Req() req: any, @Query('enterpriseId') enterpriseId: string) {
    return this.skillService.listEnterpriseCategories(req.user.userId, enterpriseId);
  }

  @Get('categories/:categoryId/skills')
  async listEnterpriseCategorySkills(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
  ) {
    return this.skillService.listEnterpriseCategorySkills(
      req.user.userId,
      enterpriseId,
      categoryId,
    );
  }

  @Post('categories/:categoryId/migrate')
  async migrateEnterpriseCategorySkills(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: MigrateSkillCategoryDto,
  ) {
    return this.skillService.migrateEnterpriseCategorySkills(
      req.user.userId,
      enterpriseId,
      categoryId,
      dto,
    );
  }

  @Post('categories/:categoryId/skills/move')
  async moveEnterpriseCategorySkills(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: MoveSkillCategorySkillsDto,
  ) {
    return this.skillService.moveEnterpriseCategorySkills(
      req.user.userId,
      enterpriseId,
      categoryId,
      dto,
    );
  }

  @Post('categories')
  async createEnterpriseCategory(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: SaveSkillCategoryDto,
  ) {
    return this.skillService.createEnterpriseCategory(req.user.userId, enterpriseId, dto);
  }

  @Patch('categories/:categoryId')
  async updateEnterpriseCategory(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
    @Body() dto: SaveSkillCategoryDto,
  ) {
    return this.skillService.updateEnterpriseCategory(
      req.user.userId,
      enterpriseId,
      categoryId,
      dto,
    );
  }

  @Delete('categories/:categoryId')
  async deleteEnterpriseCategory(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('categoryId') categoryId: string,
  ) {
    return this.skillService.deleteEnterpriseCategory(req.user.userId, enterpriseId, categoryId);
  }

  @Patch('category-settings')
  async updateEnterpriseSkillCategorySettings(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Body() dto: UpdateEnterpriseSkillCategorySettingsDto,
  ) {
    return this.skillService.updateEnterpriseSkillCategorySettings(
      req.user.userId,
      enterpriseId,
      dto,
    );
  }

  @Get('available')
  async listAvailableSkillsForEnterpriseAdmin(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Query('keyword') keyword?: string,
    @Query('purpose') purpose?: SkillPoolPurpose,
    @Query('includeConfigured') includeConfigured?: string,
  ) {
    return this.skillService.listAvailableSkillsForAdmin(req.user.userId, {
      keyword,
      purpose,
      enterpriseId,
      includeConfigured: includeConfigured === 'true',
    });
  }

  @Get()
  async listEnterpriseSkills(@Req() req: any, @Query('enterpriseId') enterpriseId: string) {
    return this.skillService.listEnterpriseSkills(req.user.userId, enterpriseId);
  }

  @Post()
  async saveEnterpriseSkill(@Req() req: any, @Body() dto: SaveEnterpriseSkillDto) {
    return this.skillService.saveEnterpriseSkill(req.user.userId, dto);
  }

  @Patch(':skillId')
  async updateEnterpriseSkill(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
    @Body() dto: UpdateSkillDto,
  ) {
    return this.skillService.updateEnterpriseSkill(req.user.userId, enterpriseId, skillId, dto);
  }

  @Delete(':skillId')
  async deleteEnterpriseSkill(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
  ) {
    return this.skillService.deleteEnterpriseSkill(req.user.userId, enterpriseId, skillId);
  }

  @Post(':skillId/reset')
  async resetEnterpriseSkill(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Param('skillId') skillId: string,
  ) {
    return this.skillService.resetEnterpriseSkill(req.user.userId, enterpriseId, skillId);
  }
}

@Controller('enterprises')
@UseGuards(JwtAuthGuard)
export class SkillDisplayController {
  constructor(private readonly skillService: SkillService) {}

  @Get('global/skill-display')
  async getGlobalSkillDisplayConfig() {
    return this.skillService.getGlobalSkillDisplayConfig();
  }

  @Get(':enterpriseId/skill-display')
  async getSkillDisplayConfig(@Req() req: any, @Param('enterpriseId') enterpriseId: string) {
    return this.skillService.getSkillDisplayConfig(req.user.userId, enterpriseId);
  }
}

@Controller('zclaw/skill-market')
@UseGuards(JwtAuthGuard)
export class SkillMarketController {
  constructor(private readonly skillService: SkillService) {}

  @Get()
  async getSkillMarket(@Req() req: any) {
    return this.skillService.getSkillMarket(req.user.userId, req);
  }
}

@Controller('zclaw/skill-submissions')
@UseGuards(JwtAuthGuard)
export class SkillSubmissionController {
  constructor(private readonly skillSubmissionService: SkillSubmissionService) {}

  @Get()
  async listMine(@Req() req: any) {
    return this.skillSubmissionService.listMine(req.user.userId, req);
  }

  @Post()
  async submit(@Req() req: any, @Body() dto: SubmitSkillDto) {
    return this.skillSubmissionService.submit(req.user.userId, dto, req);
  }

  @Get('skill/:skillKey/versions')
  async listVersions(@Req() req: any, @Param('skillKey') skillKey: string) {
    return this.skillSubmissionService.listVersions(req.user.userId, skillKey, req);
  }

  @Get('skill/:skillKey/changes')
  async getChanges(@Req() req: any, @Param('skillKey') skillKey: string) {
    return this.skillSubmissionService.getChanges(req.user.userId, skillKey, req);
  }

  @Post('skill/:skillKey/resubmit-version')
  async resubmitVersion(
    @Req() req: any,
    @Param('skillKey') skillKey: string,
    @Body() dto: ResubmitSkillVersionDto,
  ) {
    return this.skillSubmissionService.resubmitVersion(req.user.userId, skillKey, dto, req);
  }

  @Get(':submissionId')
  async getMine(@Req() req: any, @Param('submissionId') submissionId: string) {
    return this.skillSubmissionService.getMine(req.user.userId, submissionId, req);
  }
}

@Controller('zclaw/personal-skills')
@UseGuards(JwtAuthGuard)
export class SkillPersonalConfigController {
  constructor(private readonly skillPersonalConfigService: SkillPersonalConfigService) {}

  @Get(':skillKey/revisions')
  async listRevisions(@Req() req: any, @Param('skillKey') skillKey: string) {
    return this.skillPersonalConfigService.listRevisions(req.user.userId, skillKey, req);
  }

  @Get(':skillKey/revisions/:revision')
  async getRevision(
    @Req() req: any,
    @Param('skillKey') skillKey: string,
    @Param('revision') revisionRaw: string,
  ) {
    return this.skillPersonalConfigService.getRevision(
      req.user.userId,
      skillKey,
      Number(revisionRaw),
      req,
    );
  }

  @Post(':skillKey/revisions/:revision/restore')
  async restoreRevision(
    @Req() req: any,
    @Param('skillKey') skillKey: string,
    @Param('revision') revisionRaw: string,
  ) {
    return this.skillPersonalConfigService.restoreRevision(
      req.user.userId,
      skillKey,
      Number(revisionRaw),
      req,
    );
  }

  @Get(':skillKey')
  async getMine(@Req() req: any, @Param('skillKey') skillKey: string) {
    return this.skillPersonalConfigService.getMine(req.user.userId, skillKey, req);
  }

  @Put(':skillKey')
  async saveMine(
    @Req() req: any,
    @Param('skillKey') skillKey: string,
    @Body() dto: SavePersonalSkillDto,
  ) {
    return this.skillPersonalConfigService.saveMine(req.user.userId, skillKey, dto, req);
  }
}
