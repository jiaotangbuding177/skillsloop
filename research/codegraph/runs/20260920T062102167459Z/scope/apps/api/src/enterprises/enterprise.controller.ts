































@Controller('enterprises')
@UseGuards(JwtAuthGuard)
export class EnterpriseController {
  constructor(
    private readonly enterpriseService: EnterpriseService,
    private readonly enterpriseMemberImportService: EnterpriseMemberImportService,
    private readonly enterpriseDepartmentGroupService: EnterpriseDepartmentGroupService,
  ) {}

  @Get('me')
  async listMyEnterprises(@Req() req: any, @Query('includeInactive') includeInactive?: string) {
    return this.enterpriseService.listMyEnterprises(req.user.userId, {
      includeInactive: includeInactive === 'true',
    });
  }

  @Get('departments/lookup')
  async lookupDepartments(@Query('organizationIdentifier') organizationIdentifier: string) {
    return this.enterpriseService.lookupDepartmentsByIdentifier(organizationIdentifier);
  }

  @Get('lookup')
  async searchEnterprisesForJoin(@Query() query: SearchEnterprisesForJoinQueryDto) {
    return this.enterpriseService.searchEnterprisesForJoin(query.keyword);
  }

  @Get('consumer/membership')
  async getConsumerMembership(@Req() req: any) {
    return this.enterpriseService.getConsumerMembership(req.user.userId);
  }

  @Post('consumer/join')
  async joinConsumerEnterprise(@Req() req: any, @Body() dto: JoinConsumerEnterpriseDto) {
    return this.enterpriseService.joinConsumerEnterprise(req.user.userId, dto);
  }

  @Get('admin/memberships')
  @UseGuards(AdminGuard)
  async listMemberships(@Query() query: EnterpriseMembershipQueryDto) {
    return this.enterpriseService.listMembershipsForAdmin(query);
  }







  @Get('admin/:enterpriseId/member-count')
  @UseGuards(AdminGuard)
  async getMemberCountForAdmin(@Param('enterpriseId') enterpriseId: string) {
    return this.enterpriseService.getMemberCountForAdmin(enterpriseId);
  }
















  @Get('admin/memberships/:membershipId')
  @UseGuards(AdminGuard)
  async getMembershipForAdmin(@Param('membershipId') membershipId: string) {
    return this.enterpriseService.getMembershipDetailForAdmin(membershipId);
  }

























  @Post('admin/memberships/import')
  @UseGuards(AdminGuard)
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      limits: { fileSize: ENTERPRISE_MEMBER_IMPORT_MAX_FILE_SIZE, files: 1 },
    }),
  )
  async importMembershipsForAdmin(
    @Req() req: any,
    @Body() dto: ImportEnterpriseMembersDto,
    @UploadedFile() file?: Express.Multer.File,
  ) {
    return this.enterpriseMemberImportService.createImportJobForAdmin(req.user.userId, dto, file);
  }

  @Post('admin/memberships/import-manual')
  @UseGuards(AdminGuard)
  async importManualMembershipsForAdmin(
    @Req() req: any,
    @Body() dto: ImportEnterpriseMembersManualDto,
  ) {
    return this.enterpriseMemberImportService.createManualImportJobForAdmin(req.user.userId, dto);
  }

  @Post('admin/memberships/:membershipId/approve')
  @UseGuards(AdminGuard)
  async approveMembership(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.approveMembership(membershipId, req.user.userId);
  }

  @Post('admin/memberships/:membershipId/reject')
  @UseGuards(AdminGuard)
  async rejectMembership(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.rejectMembership(membershipId, req.user.userId);
  }

  @Post('admin/memberships/:membershipId/disable')
  @UseGuards(AdminGuard)
  async disableMembership(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.disableMembershipForAdmin(membershipId, req.user.userId);
  }

  @Post('admin/memberships/:membershipId/enable')
  @UseGuards(AdminGuard)
  async enableMembership(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.enableMembershipForAdmin(membershipId, req.user.userId);
  }

  @Delete('admin/memberships/:membershipId')
  @UseGuards(AdminGuard)
  async deleteMembership(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.deleteMembershipForAdmin(membershipId, req.user.userId);
  }

  @Patch('admin/memberships/:membershipId/role')
  @UseGuards(AdminGuard)
  async updateMembershipRole(
    @Req() req: any,
    @Param('membershipId') membershipId: string,
    @Body() dto: UpdateEnterpriseMembershipRoleDto,
  ) {
    return this.enterpriseService.updateMembershipRoleForAdmin(membershipId, req.user.userId, dto.role);
  }










  @Patch('admin/memberships/:membershipId/profile')
  @UseGuards(AdminGuard)
  async updateMembershipProfileForAdmin(
    @Req() req: any,
    @Param('membershipId') membershipId: string,
    @Body() dto: UpdateMembershipProfileDto,
  ) {
    return this.enterpriseService.updateMembershipProfileForAdmin(membershipId, req.user.userId, dto);
  }

  @Get('enterprise-admin/memberships')
  async listMembershipsForEnterpriseAdmin(@Req() req: any, @Query('enterpriseId') enterpriseId: string) {
    return this.enterpriseService.listMembershipsForEnterpriseAdmin(req.user.userId, enterpriseId);
  }

  @Get('enterprise-admin/memberships/:membershipId')
  async getMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.getMembershipDetailForEnterpriseAdmin(membershipId, req.user.userId);
  }














  @Post('enterprise-admin/memberships/import')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      limits: { fileSize: ENTERPRISE_MEMBER_IMPORT_MAX_FILE_SIZE, files: 1 },
    }),
  )
  async importMembershipsForEnterpriseAdmin(
    @Req() req: any,
    @Body() dto: ImportEnterpriseMembersDto,
    @UploadedFile() file?: Express.Multer.File,
  ) {
    return this.enterpriseMemberImportService.createImportJobForEnterpriseAdmin(req.user.userId, dto, file);
  }

  @Post('enterprise-admin/memberships/import-manual')
  async importManualMembershipsForEnterpriseAdmin(
    @Req() req: any,
    @Body() dto: ImportEnterpriseMembersManualDto,
  ) {
    return this.enterpriseMemberImportService.createManualImportJobForEnterpriseAdmin(
      req.user.userId,
      dto,
    );
  }

  @Post('enterprise-admin/memberships/:membershipId/approve')
  async approveMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.approveMembershipForEnterpriseAdmin(membershipId, req.user.userId);
  }

  @Post('enterprise-admin/memberships/:membershipId/reject')
  async rejectMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.rejectMembershipForEnterpriseAdmin(membershipId, req.user.userId);
  }

  @Post('enterprise-admin/memberships/:membershipId/disable')
  async disableMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.disableMembershipForEnterpriseAdmin(membershipId, req.user.userId);
  }

  @Post('enterprise-admin/memberships/:membershipId/enable')
  async enableMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.enableMembershipForEnterpriseAdmin(membershipId, req.user.userId);
  }

  @Delete('enterprise-admin/memberships/:membershipId')
  async deleteMembershipForEnterpriseAdmin(@Req() req: any, @Param('membershipId') membershipId: string) {
    return this.enterpriseService.deleteMembershipForEnterpriseAdmin(membershipId, req.user.userId);
  }

  @Patch('enterprise-admin/memberships/:membershipId/role')
  async updateMembershipRoleForEnterpriseAdmin(
    @Req() req: any,
    @Param('membershipId') membershipId: string,
    @Body() dto: UpdateEnterpriseMembershipRoleDto,
  ) {
    return this.enterpriseService.updateMembershipRoleForEnterpriseAdmin(membershipId, req.user.userId, dto.role);
  }










  @Patch('enterprise-admin/memberships/:membershipId/profile')
  async updateMembershipProfileForEnterpriseAdmin(
    @Req() req: any,
    @Param('membershipId') membershipId: string,
    @Body() dto: UpdateMembershipProfileDto,
  ) {
    return this.enterpriseService.updateMembershipProfileForEnterpriseAdmin(
      membershipId,
      req.user.userId,
      dto,
    );
  }


















  @Get('enterprise-admin/departments')
  async listDepartmentsForEnterpriseAdmin(
    @Req() req: any,
    @Query('enterpriseId') enterpriseId: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    return this.enterpriseService.listDepartmentsForEnterpriseAdmin(req.user.userId, enterpriseId, {
      startDate,
      endDate,
    });
  }

  @Post('enterprise-admin/departments')
  async createDepartmentForEnterpriseAdmin(@Req() req: any, @Body() dto: CreateEnterpriseDepartmentDto) {
    return this.enterpriseService.createDepartmentForEnterpriseAdmin(req.user.userId, dto);
  }

  @Patch('enterprise-admin/departments/:departmentId')
  async updateDepartmentForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Body() dto: UpdateEnterpriseDepartmentDto,
  ) {
    return this.enterpriseService.updateDepartmentForEnterpriseAdmin(req.user.userId, departmentId, dto);
  }

  @Delete('enterprise-admin/departments/:departmentId')
  async deleteDepartmentForEnterpriseAdmin(@Req() req: any, @Param('departmentId') departmentId: string) {
    return this.enterpriseService.deleteDepartmentForEnterpriseAdmin(req.user.userId, departmentId);
  }

  @Get('enterprise-admin/departments/:departmentId/members')
  async listDepartmentMembersForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    return this.enterpriseService.listDepartmentMembersForEnterpriseAdmin(req.user.userId, departmentId, {
      startDate,
      endDate,
    });
  }

  @Post('enterprise-admin/departments/:departmentId/migrate')
  async migrateDepartmentMembersForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Body() dto: MigrateEnterpriseDepartmentMembersDto,
  ) {
    return this.enterpriseService.migrateDepartmentMembersForEnterpriseAdmin(
      req.user.userId,
      departmentId,
      dto,
    );
  }

  @Get('enterprise-admin/departments/:departmentId/groups')
  async listDepartmentGroupsForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
  ) {
    return this.enterpriseDepartmentGroupService.listGroupsForDepartmentAdmin(
      req.user.userId,
      departmentId,
    );
  }

  @Post('enterprise-admin/departments/:departmentId/groups')
  async createDepartmentGroupForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Body() dto: CreateEnterpriseDepartmentGroupDto,
  ) {
    return this.enterpriseDepartmentGroupService.createGroupForDepartmentAdmin(
      req.user.userId,
      departmentId,
      dto,
    );
  }

  @Patch('enterprise-admin/departments/:departmentId/groups/:groupId')
  async updateDepartmentGroupForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Param('groupId') groupId: string,
    @Body() dto: UpdateEnterpriseDepartmentGroupDto,
  ) {
    return this.enterpriseDepartmentGroupService.updateGroupForDepartmentAdmin(
      req.user.userId,
      departmentId,
      groupId,
      dto,
    );
  }

  @Delete('enterprise-admin/departments/:departmentId/groups/:groupId')
  async deleteDepartmentGroupForEnterpriseAdmin(
    @Req() req: any,
    @Param('departmentId') departmentId: string,
    @Param('groupId') groupId: string,
  ) {
    return this.enterpriseDepartmentGroupService.deleteGroupForDepartmentAdmin(
      req.user.userId,
      departmentId,
      groupId,
    );
  }















  @Patch('memberships/:membershipId/profile')
  async updateMembershipProfile(
    @Req() req: any,
    @Param('membershipId') membershipId: string,
    @Body() dto: UpdateMembershipProfileDto,
  ) {
    return this.enterpriseService.updateMembershipProfile(req.user.userId, membershipId, dto);
  }

  @Get('memberships/import-jobs/:jobId')
  async getMembershipImportJob(@Req() req: any, @Param('jobId') jobId: string) {
    return this.enterpriseMemberImportService.getImportJob(req.user.userId, jobId);
  }

  @Get('memberships/import-template')
  async downloadMembershipImportTemplate(@Res() res: ExpressResponse) {
    const template = this.enterpriseMemberImportService.downloadTemplate();
    const nodeRes = res as unknown as ServerResponse;
    nodeRes.setHeader('Content-Type', template.mimeType);
    nodeRes.setHeader(
      'Content-Disposition',
      `attachment; filename="${template.filename}"`,
    );
    nodeRes.setHeader('Cache-Control', 'no-store');
    nodeRes.setHeader('Content-Length', String(template.buffer.length));
    nodeRes.setHeader('X-Content-Type-Options', 'nosniff');
    nodeRes.end(template.buffer);
  }

  @Post()
  @UseGuards(AdminGuard)
  async createEnterprise(@Req() req: any, @Body() dto: CreateEnterpriseDto) {
    return this.enterpriseService.createEnterprise(req.user.userId, dto);
  }

  @Post(':organizationIdentifier/join')
  async joinEnterprise(
    @Req() req: any,
    @Param('organizationIdentifier') organizationIdentifier: string,
    @Body() dto: JoinEnterpriseDto,
  ) {
    return this.enterpriseService.joinEnterprise(req.user.userId, organizationIdentifier, dto);
  }

  @Get(':enterpriseId/departments')
  async listDepartments(@Req() req: any, @Param('enterpriseId') enterpriseId: string) {
    return this.enterpriseService.listDepartmentsForEnterprise(req.user.userId, enterpriseId);
  }
}
