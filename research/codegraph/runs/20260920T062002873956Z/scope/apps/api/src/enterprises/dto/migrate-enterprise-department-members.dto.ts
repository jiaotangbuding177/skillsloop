import { ArrayMinSize, IsArray, IsString, IsUUID } from 'class-validator';

export class MigrateEnterpriseDepartmentMembersDto {
  @IsString()
  @IsUUID()
  targetDepartmentId!: string;

  @IsArray()
  @ArrayMinSize(1)
  @IsString({ each: true })
  userIds!: string[];
}
