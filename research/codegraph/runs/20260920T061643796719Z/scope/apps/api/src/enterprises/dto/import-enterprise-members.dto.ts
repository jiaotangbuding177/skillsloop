import { IsString, MaxLength, MinLength } from 'class-validator';

export class ImportEnterpriseMembersDto {
  @IsString()
  @MinLength(1)
  @MaxLength(120)
  enterpriseId!: string;

  @IsString()
  @MinLength(1)
  @MaxLength(120)
  initialPassword!: string;
}
