import { IsInt, IsOptional, IsString, MaxLength, Min } from 'class-validator';

export class SaveSkillCategoryDto {
  @IsString()
  @MaxLength(80)
  name!: string;

  @IsOptional()
  @IsInt()
  @Min(0)
  sortOrder?: number;

  @IsOptional()
  @IsString()
  @MaxLength(80)
  icon?: string | null;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  colorClassName?: string | null;
}
