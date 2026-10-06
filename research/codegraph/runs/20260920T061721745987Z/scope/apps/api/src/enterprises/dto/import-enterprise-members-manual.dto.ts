import {
  ArrayMaxSize,
  ArrayMinSize,
  IsArray,
  IsString,
  MaxLength,
  MinLength,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';

class ImportEnterpriseManualMemberDto {
  @IsString()
  @MinLength(1)
  @MaxLength(64)
  phone!: string;

  @IsString()
  @MinLength(1)
  @MaxLength(64)
  realName!: string;

  @IsString()
  @MinLength(1)
  @MaxLength(64)
  department!: string;
}

export class ImportEnterpriseMembersManualDto {
  @IsString()
  @MinLength(1)
  @MaxLength(120)
  enterpriseId!: string;

  @IsString()
  @MinLength(1)
  @MaxLength(120)
  initialPassword!: string;

  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(50)
  @ValidateNested({ each: true })
  @Type(() => ImportEnterpriseManualMemberDto)
  members!: ImportEnterpriseManualMemberDto[];
}
