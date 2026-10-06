import { ArrayMinSize, IsArray, IsString, IsUUID } from 'class-validator';

export class MigrateSkillCategoryDto {
  @IsUUID()
  targetCategoryId!: string;

  @IsArray()
  @ArrayMinSize(1)
  @IsString({ each: true })
  skillKeys!: string[];
}
