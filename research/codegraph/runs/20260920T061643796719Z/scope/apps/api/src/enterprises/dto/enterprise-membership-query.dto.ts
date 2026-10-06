import { IsIn, IsOptional, IsString } from 'class-validator';

export class EnterpriseMembershipQueryDto {
  @IsOptional()
  @IsString()
  enterpriseId?: string;

  @IsOptional()
  @IsIn(['pending', 'active', 'rejected', 'disabled'])
  status?: string;
}
