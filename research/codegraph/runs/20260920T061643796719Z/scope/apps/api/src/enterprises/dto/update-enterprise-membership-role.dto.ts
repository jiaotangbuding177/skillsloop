import { IsIn } from 'class-validator';

export class UpdateEnterpriseMembershipRoleDto {
  @IsIn(['viewer', 'member', 'editor', 'operator', 'admin', 'owner'])
  role!: string;
}
