import { IsBoolean, IsIn, IsInt, IsOptional, IsString, MaxLength, Min } from 'class-validator';
import { SkillDetailFieldsDto } from './skill-detail-fields.dto.js';

export class SaveEnterpriseSkillDto extends SkillDetailFieldsDto {
  @IsString()
  enterpriseId!: string;

  @IsString()
  @MaxLength(120)
  skillKey!: string;

  @IsIn(['override', 'custom'])
  type!: 'override' | 'custom';

  @IsString()
  @MaxLength(120)
  title!: string;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;

  @IsOptional()
  @IsString()
  @MaxLength(80)
  categoryName?: string;

  @IsOptional()
  @IsString()
  categoryId?: string;

  @IsOptional()
  @IsInt()
  @Min(0)
  sortOrder?: number;

  @IsOptional()
  @IsBoolean()
  isVisible?: boolean;

  @IsOptional()
  @IsBoolean()
  isHot?: boolean;
}
