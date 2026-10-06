import { ArrayMinSize, IsArray, IsOptional, IsString, IsUUID, ValidateIf } from 'class-validator';

export class MoveSkillCategorySkillsDto {
  @IsArray()
  @ArrayMinSize(1)
  @IsString({ each: true })
  skillKeys!: string[];

  @ValidateIf((_obj, value) => value !== null && value !== undefined)
  @IsOptional()
  @IsUUID()
  targetCategoryId?: string | null;
}
