import { IsBoolean, IsOptional, IsString, MaxLength } from 'class-validator';

export class ApproveSkillSubmissionDto {
  @IsString()
  categoryId!: string;

  @IsString()
  @MaxLength(80)
  categoryName!: string;

  /** 通过后是否进入「推荐技能」（热门）；默认 false，需管理员显式勾选 */
  @IsOptional()
  @IsBoolean()
  isHot?: boolean;
}
