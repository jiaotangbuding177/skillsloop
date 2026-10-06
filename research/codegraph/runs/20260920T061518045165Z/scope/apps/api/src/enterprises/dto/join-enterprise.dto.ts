import { IsOptional, IsString, MaxLength, MinLength } from 'class-validator';

export class JoinEnterpriseDto {
  @IsString()
  @MinLength(2)
  @MaxLength(32)
  realName!: string;

  @IsString()
  @MinLength(1)
  @MaxLength(64)
  department!: string;

  @IsOptional()
  @IsString()
  @MaxLength(500)
  applicantNote?: string;
}
