import { IsOptional, IsString, MaxLength } from 'class-validator';

export class SkillDetailFieldsDto {
  @IsOptional()
  @IsString()
  @MaxLength(500)
  targetUsers?: string;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  reason?: string;

  @IsOptional()
  @IsString()
  @MaxLength(4000)
  exampleInput?: string;

  @IsOptional()
  @IsString()
  @MaxLength(4000)
  prefillTemplate?: string;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  expectedOutput?: string;

  @IsOptional()
  @IsString()
  @MaxLength(80)
  icon?: string | null;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  colorClassName?: string | null;
}
