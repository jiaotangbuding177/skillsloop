import { IsBoolean } from 'class-validator';

export class UpdateEnterpriseSkillCategorySettingsDto {
  @IsBoolean()
  inheritGlobalSkillCategories!: boolean;
}
