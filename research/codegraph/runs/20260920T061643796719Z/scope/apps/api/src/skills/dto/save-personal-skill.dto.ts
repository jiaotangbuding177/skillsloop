import { IsOptional, IsString, MaxLength } from 'class-validator';
import { SkillDetailFieldsDto } from './skill-detail-fields.dto.js';

export class SavePersonalSkillDto extends SkillDetailFieldsDto {
  @IsString()
  @MaxLength(120)
  title!: string;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  description?: string;
}
