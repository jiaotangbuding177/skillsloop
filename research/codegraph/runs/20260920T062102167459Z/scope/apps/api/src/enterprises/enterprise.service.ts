

































































































































export class EnterpriseService {



























  async listMyEnterprises(
    userId: string,
    options: { includeInactive?: boolean } = {},
  ) {
    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        userId,
        ...(options.includeInactive
          ? {}
          : { status: ACTIVE_MEMBERSHIP_STATUS }),
        isDeleted: false,
        enterprise: {
          ...(options.includeInactive ? {} : { status: "active" }),
          isDeleted: false,
        },
      },
      orderBy: { createdAt: "desc" },
      include: {
        enterprise: true,
      },
    });

    return {
      items: memberships.map((membership) => ({
        id: membership.enterprise.id,
        name: membership.enterprise.name,
        slug: membership.enterprise.slug,
        status: membership.enterprise.status,
        enterpriseKind: membership.enterprise.enterpriseKind,
        logoOssKey: membership.enterprise.logoOssKey,
        avatarOssKey: membership.enterprise.avatarOssKey,
        memoryEnabled: Boolean(membership.enterprise.memoryEnabled),
        membership: {
          id: membership.id,
          role: membership.role,
          status: membership.status,
          realName: membership.realName,
          department: membership.department,
          profileComplete: this.isMembershipProfileComplete(membership),
          joinedAt: membership.joinedAt,
          createdAt: membership.createdAt,
        },
      })),
    };
  }












































































































































































  async joinEnterprise(
    userId: string,
    organizationIdentifier: string,
    dto: JoinEnterpriseDto,
  ) {
    const normalizedIdentifier = organizationIdentifier.trim();
    if (!normalizedIdentifier) {
      throw new BadRequestException("组织名称不能为空");
    }

    const enterprise = await this.prisma.enterprise.findFirst({
      where: {
        isDeleted: false,
        OR: [
          { name: normalizedIdentifier },
          { id: normalizedIdentifier },
          { slug: normalizedIdentifier },
        ],
      },
      orderBy: { createdAt: "asc" },
    });
    if (!enterprise) {
      throw new NotFoundException("组织不存在，请检查组织名称");
    }
    if (enterprise.status !== "active") {
      throw new BadRequestException("组织当前不可加入");
    }

    const realName = this.normalizeRealName(dto.realName);
    const department = await this.assertDepartmentBelongsToEnterprise(
      enterprise.id,
      dto.department,
    );

    const existing = await this.prisma.enterpriseMembership.findFirst({
      where: { enterpriseId: enterprise.id, userId, isDeleted: false },
    });
    if (existing) {
      if (
        [REJECTED_MEMBERSHIP_STATUS, DISABLED_MEMBERSHIP_STATUS].includes(
          existing.status,
        )
      ) {
        const updated = await this.prisma.enterpriseMembership.update({
          where: { id: existing.id },
          data: {
            status: PENDING_MEMBERSHIP_STATUS,
            realName,
            department,
            applicantNote: dto.applicantNote?.trim() || null,
            reviewNote: null,
            reviewedBy: null,
            reviewedAt: null,
          },
        });
        return { membership: this.toMembershipRecord(updated) };
      }
      if (existing.status === ACTIVE_MEMBERSHIP_STATUS) {
        throw new BadRequestException("您已是该组织成员，无需重复申请");
      }
      if (existing.status === PENDING_MEMBERSHIP_STATUS) {
        throw new BadRequestException("您已提交过申请，请等待审核");
      }
      return { membership: this.toMembershipRecord(existing) };
    }

    const membership = await this.prisma.enterpriseMembership.create({
      data: {
        enterpriseId: enterprise.id,
        userId,
        status: PENDING_MEMBERSHIP_STATUS,
        realName,
        department,
        applicantNote: dto.applicantNote?.trim() || undefined,
      },
    });
    return { membership: this.toMembershipRecord(membership) };
  }






































































































  async updateMembershipProfile(
    userId: string,
    membershipId: string,
    dto: UpdateMembershipProfileDto,
  ) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, userId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException("成员记录不存在");
    }
    if (!["active", "pending"].includes(membership.status)) {
      throw new BadRequestException("当前状态不可更新资料");
    }

    const realName = this.normalizeRealName(dto.realName);
    const department = await this.assertDepartmentBelongsToEnterprise(
      membership.enterpriseId,
      dto.department,
    );

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: { realName, department },
    });

    return { membership: this.toMembershipRecord(updated) };
  }

  async updateMembershipProfileForAdmin(
    membershipId: string,
    _adminUserId: string,
    dto: UpdateMembershipProfileDto,
  ) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException('成员记录不存在');
    }
    if (!['active', 'pending'].includes(membership.status)) {
      throw new BadRequestException('当前状态不可更新资料');
    }

    const realName = this.normalizeRealName(dto.realName);
    const department = await this.assertDepartmentBelongsToEnterprise(membership.enterpriseId, dto.department);

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: { realName, department },
    });

    return { membership: this.toMembershipRecord(updated) };
  }

  async updateMembershipProfileForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
    dto: UpdateMembershipProfileDto,
  ) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException('成员记录不存在');
    }
    if (!['active', 'pending'].includes(membership.status)) {
      throw new BadRequestException('当前状态不可更新资料');
    }
    if (membership.role === 'owner') {
      throw new ForbiddenException('不能修改 owner 的基本信息');
    }

    await this.assertEnterpriseAdminOrOwner(callerUserId, membership.enterpriseId);

    const realName = this.normalizeRealName(dto.realName);
    const department = await this.assertDepartmentBelongsToEnterprise(membership.enterpriseId, dto.department);

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: { realName, department },
    });

    return { membership: this.toMembershipRecord(updated) };
  }

  async lookupDepartmentsByIdentifier(organizationIdentifier: string) {
    const normalizedIdentifier = organizationIdentifier.trim();
    if (!normalizedIdentifier) {
      throw new BadRequestException("组织名称不能为空");
    }

    const enterprise = await this.prisma.enterprise.findFirst({
      where: {
        isDeleted: false,
        status: "active",
        OR: [
          { name: normalizedIdentifier },
          { id: normalizedIdentifier },
          { slug: normalizedIdentifier },
        ],
      },
      orderBy: { createdAt: "asc" },
      select: { id: true, name: true },
    });
    if (!enterprise) {
      throw new NotFoundException("组织不存在，请检查组织名称");
    }

    const items = await this.prisma.enterpriseDepartment.findMany({
      where: { enterpriseId: enterprise.id, isDeleted: false },
      orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }],
      select: { id: true, name: true, sortOrder: true },
    });

    return {
      enterprise: {
        id: enterprise.id,
        name: enterprise.name,
      },
      items,
    };
  }


































  async listDepartmentsForEnterprise(userId: string, enterpriseId: string) {
    await this.assertEnterpriseMember(userId, enterpriseId);

    const items = await this.prisma.enterpriseDepartment.findMany({
      where: { enterpriseId, isDeleted: false },
      orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }],
      select: {
        id: true,
        enterpriseId: true,
        name: true,
        sortOrder: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    return { items };
  }

  async listDepartmentsForEnterpriseAdmin(
    userId: string,
    enterpriseId: string,
    tokenUsageRange?: DepartmentTokenUsageRangeInput,
  ) {
    await this.assertEnterpriseDepartmentManager(userId, enterpriseId);
    const callerRole = await this.resolveDepartmentManagerCallerRole(
      userId,
      enterpriseId,
    );
    return this.listDepartmentsWithMemberCounts(
      enterpriseId,
      callerRole,
      tokenUsageRange,
      true,
    );
  }

  async createDepartmentForEnterpriseAdmin(
    userId: string,
    dto: CreateEnterpriseDepartmentDto,
  ) {
    const enterpriseId = dto.enterpriseId.trim();
    if (!enterpriseId) {
      throw new BadRequestException("enterpriseId is required");
    }
    await this.assertEnterpriseDepartmentManager(userId, enterpriseId);

    const name = dto.name.trim();
    if (!name) {
      throw new BadRequestException("部门名称不能为空");
    }

    const duplicate = await this.prisma.enterpriseDepartment.findFirst({
      where: { enterpriseId, name, isDeleted: false },
    });
    if (duplicate) {
      throw new BadRequestException("部门名称已存在");
    }

    const maxSortOrder = await this.prisma.enterpriseDepartment.aggregate({
      where: { enterpriseId, isDeleted: false },
      _max: { sortOrder: true },
    });

    const department = await this.prisma.enterpriseDepartment.create({
      data: {
        enterpriseId,
        name,
        sortOrder: dto.sortOrder ?? (maxSortOrder._max.sortOrder ?? -1) + 1,
      },
    });

    return { department: this.toDepartmentRecord(department, 0) };
  }

  async listDepartmentMembersForEnterpriseAdmin(
    userId: string,
    departmentId: string,
    tokenUsageRange?: DepartmentTokenUsageRangeInput,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const callerRole = await this.resolveDepartmentManagerCallerRole(
      userId,
      department.enterpriseId,
    );
    const resolvedRange =
      this.resolveDepartmentTokenUsageRange(tokenUsageRange);
    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        enterpriseId: department.enterpriseId,
        department: department.name,
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
        ...(callerRole === "operator"
          ? { role: { notIn: [...ENTERPRISE_ADMIN_MEMBERSHIP_ROLES] } }
          : {}),
      },
      orderBy: [{ joinedAt: "desc" }, { createdAt: "desc" }],
      include: {
        user: {
          select: {
            id: true,
            identities: {
              where: { provider: "phone", isDeleted: false },
              orderBy: { createdAt: "desc" },
              take: 1,
              select: { phoneMasked: true, providerUserId: true },
            },
          },
        },
      },
    });
    const tokenUsageByUserId = await this.getTokenUsageByUserId(
      department.enterpriseId,
      memberships.map((membership) => membership.userId),
      resolvedRange,
    );
    const totalTokenUsed = memberships.reduce(
      (sum, membership) =>
        sum + (tokenUsageByUserId.get(membership.userId) ?? 0),
      0,
    );
    const averageTokenUsed =
      memberships.length > 0
        ? Math.round(totalTokenUsed / memberships.length)
        : 0;

    return {
      department: this.toDepartmentRecord(department, memberships.length, {
        totalTokenUsed,
        averageTokenUsed,
      }),
      tokenUsageRange: resolvedRange,
      items: memberships.map((membership) => {
        const identity = membership.user?.identities?.[0];
        const phoneRaw =
          identity?.phoneMasked ?? identity?.providerUserId ?? "";
        return {
          membershipId: membership.id,
          userId: membership.userId,
          realName: membership.realName,
          role: membership.role,
          phoneMasked: phoneRaw || null,
          joinedAt: membership.joinedAt ?? membership.createdAt,
          tokenUsed: tokenUsageByUserId.get(membership.userId) ?? 0,
        };
      }),
    };
  }

  async migrateDepartmentMembersForEnterpriseAdmin(
    userId: string,
    departmentId: string,
    dto: MigrateEnterpriseDepartmentMembersDto,
  ) {
    const sourceDepartment = await this.getDepartmentForAdmin(
      userId,
      departmentId,
    );
    const callerRole = await this.resolveDepartmentManagerCallerRole(
      userId,
      sourceDepartment.enterpriseId,
    );
    const targetDepartmentId = dto.targetDepartmentId.trim();
    if (targetDepartmentId === sourceDepartment.id) {
      throw new BadRequestException("源部门与目标部门不能相同");
    }

    const targetDepartment = await this.prisma.enterpriseDepartment.findFirst({
      where: {
        id: targetDepartmentId,
        enterpriseId: sourceDepartment.enterpriseId,
        isDeleted: false,
      },
    });
    if (!targetDepartment) {
      throw new BadRequestException("目标部门不存在");
    }

    const uniqueUserIds = [
      ...new Set(dto.userIds.map((item) => item.trim()).filter(Boolean)),
    ];
    if (uniqueUserIds.length === 0) {
      throw new BadRequestException("请至少选择一名成员");
    }

    const membersInSource = await this.prisma.enterpriseMembership.findMany({
      where: {
        enterpriseId: sourceDepartment.enterpriseId,
        department: sourceDepartment.name,
        userId: { in: uniqueUserIds },
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
      },
      select: { userId: true, role: true },
    });
    if (membersInSource.length !== uniqueUserIds.length) {
      throw new BadRequestException("部分成员不在源部门中");
    }
    if (
      callerRole === "operator" &&
      membersInSource.some((member) =>
        this.isMembershipHiddenFromEnterpriseOperator(member.role),
      )
    ) {
      throw new NotFoundException("membership not found");
    }

    await this.prisma.enterpriseMembership.updateMany({
      where: {
        enterpriseId: sourceDepartment.enterpriseId,
        department: sourceDepartment.name,
        userId: { in: uniqueUserIds },
        isDeleted: false,
      },
      data: { department: targetDepartment.name },
    });

    await this.enterpriseDepartmentGroupService.removeGroupMembersForUsersInDepartment(
      sourceDepartment.id,
      uniqueUserIds,
    );

    return { movedCount: membersInSource.length };
  }

  async updateDepartmentForEnterpriseAdmin(
    userId: string,
    departmentId: string,
    dto: UpdateEnterpriseDepartmentDto,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const nextName = dto.name?.trim();
    if (nextName !== undefined && !nextName) {
      throw new BadRequestException("部门名称不能为空");
    }

    if (nextName && nextName !== department.name) {
      const duplicate = await this.prisma.enterpriseDepartment.findFirst({
        where: {
          enterpriseId: department.enterpriseId,
          name: nextName,
          isDeleted: false,
          NOT: { id: department.id },
        },
      });
      if (duplicate) {
        throw new BadRequestException("部门名称已存在");
      }
    }

    const updated = await this.prisma.$transaction(async (tx) => {
      const saved = await tx.enterpriseDepartment.update({
        where: { id: department.id },
        data: {
          ...(nextName ? { name: nextName } : {}),
          ...(dto.sortOrder !== undefined ? { sortOrder: dto.sortOrder } : {}),
        },
      });

      if (nextName && nextName !== department.name) {
        await tx.enterpriseMembership.updateMany({
          where: {
            enterpriseId: department.enterpriseId,
            department: department.name,
            isDeleted: false,
          },
          data: { department: nextName },
        });
        await this.rewriteEnterpriseAgentAllowedDepartments(
          department.enterpriseId,
          (stored) => renameAllowedDepartmentName(stored, department.name, nextName),
          tx,
        );
      }

      return saved;
    });

    return { department: this.toDepartmentRecord(updated) };
  }

  async deleteDepartmentForEnterpriseAdmin(
    userId: string,
    departmentId: string,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);

    const memberCount = await this.prisma.enterpriseMembership.count({
      where: {
        enterpriseId: department.enterpriseId,
        department: department.name,
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
      },
    });
    if (memberCount > 0) {
      throw new BadRequestException("该部门仍有成员使用，无法删除");
    }

    const updated = await this.prisma.enterpriseDepartment.update({
      where: { id: department.id },
      data: { isDeleted: true },
    });

    await this.enterpriseDepartmentGroupService.softDeleteGroupsForDepartment(
      department.id,
    );
    await this.rewriteEnterpriseAgentAllowedDepartments(
      department.enterpriseId,
      (stored) => removeAllowedDepartmentName(stored, department.name),
    );

    return { department: this.toDepartmentRecord(updated) };
  }

  async getMemberCountForAdmin(enterpriseId: string) {
    const count = await this.prisma.enterpriseMembership.count({
      where: {
        enterpriseId,
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
      },
    });
    return { count };
  }

  async listMembershipsForAdmin(query: EnterpriseMembershipQueryDto) {
    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        isDeleted: false,
        ...(query.enterpriseId ? { enterpriseId: query.enterpriseId } : {}),
        ...(query.status ? { status: query.status } : {}),
      },
      orderBy: { createdAt: "desc" },
      include: {
        enterprise: true,
        user: {
          select: {
            id: true,
            role: true,
            identities: {
              where: { provider: "phone", isDeleted: false },
              orderBy: { createdAt: "desc" },
              take: 1,
              select: { phoneMasked: true, providerUserId: true },
            },
          },
        },
      },
    });

    return {
      items: memberships.map((membership) =>
        this.toAdminMembershipRecord(membership),
      ),
    };
  }

  async getMembershipDetailForAdmin(membershipId: string) {
    const membership = await this.getMembershipDetailRecord(membershipId);
    return { membership: this.toAdminMembershipRecord(membership) };
  }

  async getMembershipDetailForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipDetailRecord(membershipId);
    const { role: callerRole } = await this.assertEnterpriseOrganizationManager(
      callerUserId,
      membership.enterpriseId,
    );
    this.assertOperatorCanViewMembership(callerRole, membership.role);
    return { membership: this.toAdminMembershipRecord(membership) };
  }





















































































































































































  async approveMembership(membershipId: string, adminUserId: string) {
    const membership = await this.getMembershipForReview(membershipId);
    await this.assertB2BSeatCapacityForMembershipActivation(
      membership.enterpriseId,
      1,
      "当前企业成员数已达到套餐席位上限",
    );
    const updated = await this.activateMembershipWithSeatCapacity(
      membership,
      adminUserId,
      "enterprise member seat limit reached",
    );
    await this.initializeConversationQuotaForApprovedMember(
      updated.enterpriseId,
      updated.userId,
      updated.role,
    );
    await this.ensureB2BMonthlyEntitlementsForApprovedMember(
      updated,
      adminUserId,
    );
    return { membership: this.toMembershipRecord(updated) };
  }

  async rejectMembership(membershipId: string, adminUserId: string) {
    const membership = await this.getMembershipForReview(membershipId);
    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: REJECTED_MEMBERSHIP_STATUS,
        reviewedBy: adminUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async approveMembershipForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipForReview(membershipId);
    const { role: callerRole } = await this.assertEnterpriseOrganizationManager(
      callerUserId,
      membership.enterpriseId,
    );
    this.assertOperatorCanViewMembership(callerRole, membership.role);
    await this.assertB2BSeatCapacityForMembershipActivation(
      membership.enterpriseId,
      1,
      "当前企业成员数已达到套餐席位上限",
    );

    const updated = await this.activateMembershipWithSeatCapacity(
      membership,
      callerUserId,
      "enterprise member seat limit reached",
    );
    await this.initializeConversationQuotaForApprovedMember(
      updated.enterpriseId,
      updated.userId,
      updated.role,
    );
    await this.ensureB2BMonthlyEntitlementsForApprovedMember(
      updated,
      callerUserId,
    );
    return { membership: this.toMembershipRecord(updated) };
  }

  async rejectMembershipForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipForReview(membershipId);
    const { role: callerRole } = await this.assertEnterpriseOrganizationManager(
      callerUserId,
      membership.enterpriseId,
    );
    this.assertOperatorCanViewMembership(callerRole, membership.role);

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: REJECTED_MEMBERSHIP_STATUS,
        reviewedBy: callerUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async updateMembershipRoleForAdmin(
    membershipId: string,
    adminUserId: string,
    role: string,
  ) {
    const normalizedRole = role.trim();
    if (
      !(ENTERPRISE_MEMBERSHIP_ROLES as readonly string[]).includes(
        normalizedRole,
      )
    ) {
      throw new BadRequestException("invalid enterprise membership role");
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException("membership not found");
    }
    if (membership.status !== ACTIVE_MEMBERSHIP_STATUS) {
      throw new BadRequestException("只能修改 active 成员的角色");
    }

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        role: normalizedRole,
        reviewedBy: adminUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async listMembershipsForEnterpriseAdmin(
    callerUserId: string,
    enterpriseId: string,
  ) {
    if (!enterpriseId?.trim()) {
      throw new BadRequestException("enterpriseId 不能为空");
    }
    const { role: callerRole } = await this.assertEnterpriseOrganizationManager(
      callerUserId,
      enterpriseId,
    );

    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        enterpriseId,
        isDeleted: false,
        ...(callerRole === "operator"
          ? { role: { notIn: [...ENTERPRISE_ADMIN_MEMBERSHIP_ROLES] } }
          : {}),
      },
      orderBy: { createdAt: "desc" },
      include: {
        enterprise: true,
        user: {
          select: {
            id: true,
            role: true,
            identities: {
              where: { provider: "phone", isDeleted: false },
              orderBy: { createdAt: "desc" },
              take: 1,
              select: { phoneMasked: true, providerUserId: true },
            },
          },
        },
      },
    });

    return { items: memberships.map((m) => this.toAdminMembershipRecord(m)) };
  }

  async updateMembershipRoleForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
    role: string,
  ) {
    const normalizedRole = role.trim();
    const SETTABLE_ROLES = [
      "viewer",
      "member",
      "editor",
      "operator",
      "admin",
    ] as const;
    if (!(SETTABLE_ROLES as readonly string[]).includes(normalizedRole)) {
      throw new BadRequestException(
        "只能将角色设置为 viewer/member/editor/operator/admin",
      );
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) throw new NotFoundException("membership not found");
    if (membership.status !== ACTIVE_MEMBERSHIP_STATUS) {
      throw new BadRequestException("只能修改 active 成员的角色");
    }
    if (membership.role === "owner") {
      throw new ForbiddenException("不能修改 owner 的角色");
    }
    if (membership.userId === callerUserId) {
      throw new ForbiddenException("不能修改自己的角色");
    }

    await this.assertEnterpriseAdminOrOwner(
      callerUserId,
      membership.enterpriseId,
    );

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        role: normalizedRole,
        reviewedBy: callerUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async disableMembershipForAdmin(membershipId: string, adminUserId: string) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    if (membership.status !== ACTIVE_MEMBERSHIP_STATUS) {
      throw new BadRequestException("only active memberships can be disabled");
    }

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: DISABLED_MEMBERSHIP_STATUS,
        reviewedBy: adminUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async enableMembershipForAdmin(membershipId: string, adminUserId: string) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    if (membership.status !== DISABLED_MEMBERSHIP_STATUS) {
      throw new BadRequestException("only disabled memberships can be enabled");
    }
    await this.assertB2BSeatCapacityForMembershipActivation(
      membership.enterpriseId,
      0,
      "当前企业成员数已超过套餐席位上限，不能启用成员",
    );

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: ACTIVE_MEMBERSHIP_STATUS,
        reviewedBy: adminUserId,
        reviewedAt: new Date(),
        joinedAt: membership.joinedAt ?? new Date(),
      },
    });
    await this.initializeConversationQuotaForApprovedMember(
      updated.enterpriseId,
      updated.userId,
      updated.role,
    );
    await this.ensureB2BMonthlyEntitlementsForApprovedMember(
      updated,
      adminUserId,
    );
    return { membership: this.toMembershipRecord(updated) };
  }

  async disableMembershipForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    await this.assertEnterpriseAdminCanChangeMemberStatus(
      callerUserId,
      membership,
    );
    if (membership.status !== ACTIVE_MEMBERSHIP_STATUS) {
      throw new BadRequestException("only active memberships can be disabled");
    }

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: DISABLED_MEMBERSHIP_STATUS,
        reviewedBy: callerUserId,
        reviewedAt: new Date(),
      },
    });
    return { membership: this.toMembershipRecord(updated) };
  }

  async deleteMembershipForAdmin(membershipId: string, adminUserId: string) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    if (
      !(DELETABLE_MEMBERSHIP_STATUSES as readonly string[]).includes(
        membership.status,
      )
    ) {
      throw new BadRequestException(
        "only disabled or rejected memberships can be deleted",
      );
    }
    if (membership.role === "owner") {
      throw new ForbiddenException("cannot delete owner membership");
    }

    const updated = await this.markMembershipDeleted(membership, adminUserId);
    return { membership: this.toMembershipRecord(updated) };
  }

  async deleteMembershipForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    await this.assertEnterpriseAdminCanChangeMemberStatus(
      callerUserId,
      membership,
    );
    if (
      !(DELETABLE_MEMBERSHIP_STATUSES as readonly string[]).includes(
        membership.status,
      )
    ) {
      throw new BadRequestException(
        "only disabled or rejected memberships can be deleted",
      );
    }

    const updated = await this.markMembershipDeleted(membership, callerUserId);
    return { membership: this.toMembershipRecord(updated) };
  }

  async enableMembershipForEnterpriseAdmin(
    membershipId: string,
    callerUserId: string,
  ) {
    const membership = await this.getMembershipForStatusChange(membershipId);
    await this.assertEnterpriseAdminCanChangeMemberStatus(
      callerUserId,
      membership,
    );
    if (membership.status !== DISABLED_MEMBERSHIP_STATUS) {
      throw new BadRequestException("only disabled memberships can be enabled");
    }
    await this.assertB2BSeatCapacityForMembershipActivation(
      membership.enterpriseId,
      0,
      "当前企业成员数已超过套餐席位上限，不能启用成员",
    );

    const updated = await this.prisma.enterpriseMembership.update({
      where: { id: membership.id },
      data: {
        status: ACTIVE_MEMBERSHIP_STATUS,
        reviewedBy: callerUserId,
        reviewedAt: new Date(),
        joinedAt: membership.joinedAt ?? new Date(),
      },
    });
    await this.initializeConversationQuotaForApprovedMember(
      updated.enterpriseId,
      updated.userId,
      updated.role,
    );
    await this.ensureB2BMonthlyEntitlementsForApprovedMember(
      updated,
      callerUserId,
    );
    return { membership: this.toMembershipRecord(updated) };
  }

  async assertEnterpriseAdminOrOwner(userId: string, enterpriseId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        enterprise: { status: "active", isDeleted: false },
      },
      select: { role: true },
    });
    if (!membership || !["admin", "owner"].includes(membership.role)) {
      throw new ForbiddenException("需要组织管理员权限");
    }
  }

  async assertEnterpriseAdminOrOwnerOrPlatformAdmin(
    userId: string,
    enterpriseId: string,
  ) {
    if (await this.isPlatformAdminUser(userId)) {
      await this.assertActiveEnterprise(enterpriseId);
      return { role: "platform_admin" as const };
    }
    await this.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return { role: "enterprise_admin" as const };
  }

  async assertEnterpriseOwner(userId: string, enterpriseId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        enterprise: { status: "active", isDeleted: false },
      },
      select: { role: true },
    });
    if (!membership || membership.role !== "owner") {
      throw new ForbiddenException("需要组织创建者权限");
    }
  }



































  isMembershipHiddenFromEnterpriseOperator(memberRole: string) {
    return (ENTERPRISE_ADMIN_MEMBERSHIP_ROLES as readonly string[]).includes(
      memberRole,
    );
  }

  private assertOperatorCanViewMembership(
    callerRole: string,
    targetRole: string,
  ) {
    if (
      callerRole === "operator" &&
      this.isMembershipHiddenFromEnterpriseOperator(targetRole)
    ) {
      throw new NotFoundException("membership not found");
    }
  }

  private async assertB2BSeatCapacityForMembershipActivation(
    enterpriseId: string,
    seatsToAdd: number,
    message: string,
  ) {
    const activePlan =
      await this.getActiveB2BMonthlyPlanSeatLimit(enterpriseId);
    if (!activePlan) return;
    const occupiedSeats = await this.prisma.enterpriseMembership.count({
      where: {
        enterpriseId,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, DISABLED_MEMBERSHIP_STATUS] },
        isDeleted: false,
      },
    });
    if (occupiedSeats + seatsToAdd > activePlan.memberLimit) {
      throw new BadRequestException(message);
    }
  }

  private async activateMembershipWithSeatCapacity(
    membership: { id: string; enterpriseId: string; joinedAt?: Date | null },
    reviewerId: string,
    message: string,
  ) {
    return this.prisma.$transaction(async (tx) => {
      await tx.$executeRaw`
        SELECT "id"
        FROM "enterprise_memberships"
        WHERE "enterpriseId" = ${membership.enterpriseId}
          AND "isDeleted" = false
        FOR UPDATE
      `;
      const latest = await tx.enterpriseMembership.findFirst({
        where: { id: membership.id, isDeleted: false },
      });
      if (!latest) throw new NotFoundException("membership not found");
      if (latest.status === ACTIVE_MEMBERSHIP_STATUS) return latest;
      const activePlan = await this.getActiveB2BMonthlyPlanSeatLimitInTx(
        tx,
        membership.enterpriseId,
      );
      if (activePlan) {
        const occupiedSeats = await tx.enterpriseMembership.count({
          where: {
            enterpriseId: membership.enterpriseId,
            status: {
              in: [ACTIVE_MEMBERSHIP_STATUS, DISABLED_MEMBERSHIP_STATUS],
            },
            isDeleted: false,
          },
        });
        if (occupiedSeats + 1 > activePlan.memberLimit) {
          throw new BadRequestException(message);
        }
      }
      return tx.enterpriseMembership.update({
        where: { id: latest.id },
        data: {
          status: ACTIVE_MEMBERSHIP_STATUS,
          reviewedBy: reviewerId,
          reviewedAt: new Date(),
          joinedAt: latest.joinedAt ?? new Date(),
        },
      });
    });
  }





































































  private async ensureB2BMonthlyEntitlementsForApprovedMember(
    membership: {
      id: string;
      enterpriseId: string;
      userId: string;
      status: string;
    },
    operatorId: string,
  ) {
    if (membership.status !== ACTIVE_MEMBERSHIP_STATUS) return;
    await this.entitlementService.ensureB2BMonthlyEntitlementsForMember({
      enterpriseId: membership.enterpriseId,
      userId: membership.userId,
      membershipId: membership.id,
      operatorId,
    });
  }






























































































































  async assertActiveEnterpriseMember(userId: string, enterpriseId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        enterprise: { status: "active", isDeleted: false },
      },
      select: { id: true, role: true, department: true },
    });
    if (!membership) {
      throw new ForbiddenException("你不是该组织的有效成员");
    }
    return membership;
  }






















































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































  private async getMembershipDetailRecord(membershipId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
      include: {
        enterprise: true,
        user: {
          select: {
            id: true,
            role: true,
            identities: {
              where: { provider: "phone", isDeleted: false },
              orderBy: { createdAt: "desc" },
              take: 1,
              select: { phoneMasked: true, providerUserId: true },
            },
          },
        },
      },
    });
    if (!membership) {
      throw new NotFoundException("membership not found");
    }
    return membership;
  }

  private async getMembershipForReview(membershipId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException("membership not found");
    }
    if (membership.status !== PENDING_MEMBERSHIP_STATUS) {
      throw new BadRequestException("该加入申请已处理");
    }
    return membership;
  }

  private async getMembershipForStatusChange(membershipId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: { id: membershipId, isDeleted: false },
    });
    if (!membership) {
      throw new NotFoundException("membership not found");
    }
    return membership;
  }

  private async markMembershipDeleted(
    membership: { id: string; enterpriseId: string; userId: string },
    reviewedBy: string,
  ) {
    try {
      return await this.prisma.$transaction(async (tx) => {
        // (enterpriseId, userId, isDeleted) is unique; purge stale tombstones before soft-deleting.
        await tx.enterpriseMembership.deleteMany({
          where: {
            enterpriseId: membership.enterpriseId,
            userId: membership.userId,
            isDeleted: true,
            id: { not: membership.id },
          },
        });
        await tx.$executeRaw`
          DELETE FROM "zclaw_enterprise_token_quota_members"
          WHERE "enterpriseId" = ${membership.enterpriseId}
            AND "userId" = ${membership.userId}
        `;
        return tx.enterpriseMembership.update({
          where: { id: membership.id },
          data: {
            isDeleted: true,
            reviewedBy,
            reviewedAt: new Date(),
          },
        });
      });
    } catch (error) {
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        error.code === "P2002"
      ) {
        throw new BadRequestException("成员删除失败，请刷新后重试");
      }
      throw error;
    }
  }

  private async assertEnterpriseAdminCanChangeMemberStatus(
    callerUserId: string,
    membership: {
      enterpriseId: string;
      userId: string;
      role: string;
    },
  ) {
    if (membership.role === "owner") {
      throw new ForbiddenException("cannot change owner membership status");
    }
    if (membership.userId === callerUserId) {
      throw new ForbiddenException("cannot change your own membership status");
    }
    const { role: callerRole } = await this.assertEnterpriseOrganizationManager(
      callerUserId,
      membership.enterpriseId,
    );
    this.assertOperatorCanViewMembership(callerRole, membership.role);
  }














  private toMembershipRecord(membership: {
    id: string;
    enterpriseId: string;
    userId: string;
    role: string;
    status: string;
    workspaceQuotaBytes?: bigint | null;
    realName?: string | null;
    department?: string | null;
    applicantNote?: string | null;
    reviewNote?: string | null;
    reviewedAt?: Date | null;
    joinedAt?: Date | null;
    createdAt: Date;
    updatedAt: Date;
  }) {
    return {
      id: membership.id,
      enterpriseId: membership.enterpriseId,
      userId: membership.userId,
      role: membership.role,
      status: membership.status,
      workspaceQuotaBytes:
        membership.workspaceQuotaBytes == null
          ? null
          : membership.workspaceQuotaBytes.toString(),
      realName: membership.realName,
      department: membership.department,
      profileComplete: this.isMembershipProfileComplete(membership),
      applicantNote: membership.applicantNote,
      reviewNote: membership.reviewNote,
      reviewedAt: membership.reviewedAt,
      joinedAt: membership.joinedAt,
      createdAt: membership.createdAt,
      updatedAt: membership.updatedAt,
    };
  }

  private toDepartmentRecord(
    department: {
      id: string;
      enterpriseId: string;
      name: string;
      sortOrder: number;
      createdAt: Date;
      updatedAt: Date;
    },
    memberCount?: number,
    tokenUsage?: {
      totalTokenUsed: number;
      averageTokenUsed: number;
    },
  ) {
    return {
      id: department.id,
      enterpriseId: department.enterpriseId,
      name: department.name,
      sortOrder: department.sortOrder,
      createdAt: department.createdAt,
      updatedAt: department.updatedAt,
      ...(memberCount !== undefined ? { memberCount } : {}),
      ...(tokenUsage ?? {}),
    };
  }

  private isMembershipProfileComplete(membership: {
    realName?: string | null;
    department?: string | null;
  }) {
    return Boolean(
      membership.realName?.trim() && membership.department?.trim(),
    );
  }















  private async assertDepartmentBelongsToEnterprise(
    enterpriseId: string,
    departmentName: string,
  ) {
    const normalized = departmentName.trim();
    if (!normalized) {
      throw new BadRequestException("部门不能为空");
    }

    const department = await this.prisma.enterpriseDepartment.findFirst({
      where: { enterpriseId, name: normalized, isDeleted: false },
    });
    if (!department) {
      throw new BadRequestException("所选部门不在组织部门列表中");
    }
    return department.name;
  }

  private async assertEnterpriseMember(userId: string, enterpriseId: string) {
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        enterprise: { status: "active", isDeleted: false },
      },
      select: { id: true },
    });
    if (!membership) {
      throw new ForbiddenException("需要组织成员权限");
    }
    return membership;
  }

  private async getDepartmentForAdmin(userId: string, departmentId: string) {
    const department = await this.prisma.enterpriseDepartment.findFirst({
      where: { id: departmentId, isDeleted: false },
    });
    if (!department) {
      throw new NotFoundException("部门不存在");
    }
    await this.assertEnterpriseDepartmentManager(
      userId,
      department.enterpriseId,
    );
    return department;
  }

  private async resolveDepartmentManagerCallerRole(
    userId: string,
    enterpriseId: string,
  ) {
    if (await this.isPlatformAdminUser(userId)) {
      return null;
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        enterprise: { status: "active", isDeleted: false },
      },
      select: { role: true },
    });
    return membership?.role ?? null;
  }

  private async listDepartmentsByEnterpriseId(enterpriseId: string) {
    return this.listDepartmentsWithMemberCounts(enterpriseId);
  }

  private async rewriteEnterpriseAgentAllowedDepartments(
    enterpriseId: string,
    rewrite: (stored: string | null) => string | null,
    tx?: Prisma.TransactionClient,
  ) {
    const client = tx ?? this.prisma;
    const agents = await client.enterpriseBuiltinAgentConfig.findMany({
      where: {
        enterpriseId,
        isDeleted: false,
        allowedDepartmentNames: { not: null },
      },
      select: { id: true, allowedDepartmentNames: true },
    });
    for (const agent of agents) {
      const next = rewrite(agent.allowedDepartmentNames);
      if (next === agent.allowedDepartmentNames) continue;
      await client.enterpriseBuiltinAgentConfig.update({
        where: { id: agent.id },
        data: { allowedDepartmentNames: next },
      });
    }
  }

  private async listDepartmentsWithMemberCounts(
    enterpriseId: string,
    callerRole: string | null = null,
    tokenUsageRange?: DepartmentTokenUsageRangeInput,
    includeTokenUsage = false,
  ) {
    const resolvedRange = includeTokenUsage
      ? this.resolveDepartmentTokenUsageRange(tokenUsageRange)
      : null;
    const items = await this.prisma.enterpriseDepartment.findMany({
      where: { enterpriseId, isDeleted: false },
      orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }],
      select: {
        id: true,
        enterpriseId: true,
        name: true,
        sortOrder: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    if (items.length === 0) {
      return {
        items: [],
        ...(resolvedRange ? { tokenUsageRange: resolvedRange } : {}),
      };
    }

    const membershipWhere = {
      enterpriseId,
      isDeleted: false,
      status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
      department: { in: items.map((item) => item.name) },
      ...(callerRole === "operator"
        ? { role: { notIn: [...ENTERPRISE_ADMIN_MEMBERSHIP_ROLES] } }
        : {}),
    };

    const memberCounts = await this.prisma.enterpriseMembership.groupBy({
      by: ["department"],
      where: membershipWhere,
      _count: { _all: true },
    });
    const countByDepartmentName = new Map(
      memberCounts.map((row) => [row.department ?? "", row._count._all]),
    );

    if (!resolvedRange) {
      return {
        items: items.map((department) =>
          this.toDepartmentRecord(
            department,
            countByDepartmentName.get(department.name) ?? 0,
          ),
        ),
      };
    }

    const visibleMemberships = await this.prisma.enterpriseMembership.findMany({
      where: membershipWhere,
      select: { userId: true, department: true },
    });
    const tokenUsageByUserId = await this.getTokenUsageByUserId(
      enterpriseId,
      visibleMemberships.map((membership) => membership.userId),
      resolvedRange,
    );
    const tokenTotalByDepartmentName = new Map<string, number>();
    for (const membership of visibleMemberships) {
      const departmentName = membership.department ?? "";
      tokenTotalByDepartmentName.set(
        departmentName,
        (tokenTotalByDepartmentName.get(departmentName) ?? 0) +
          (tokenUsageByUserId.get(membership.userId) ?? 0),
      );
    }

    return {
      items: items.map((department) => {
        const memberCount = countByDepartmentName.get(department.name) ?? 0;
        const totalTokenUsed =
          tokenTotalByDepartmentName.get(department.name) ?? 0;
        const averageTokenUsed =
          memberCount > 0 ? Math.round(totalTokenUsed / memberCount) : 0;
        return this.toDepartmentRecord(department, memberCount, {
          totalTokenUsed,
          averageTokenUsed,
        });
      }),
      tokenUsageRange: resolvedRange,
    };
  }










































































  private async assertActiveEnterprise(enterpriseId: string) {
    const trimmed = enterpriseId?.trim();
    if (!trimmed) {
      throw new BadRequestException("enterpriseId is required");
    }

    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: trimmed, status: "active", isDeleted: false },
      select: { id: true, name: true, enterpriseKind: true },
    });
    if (!enterprise) {
      throw new NotFoundException("组织不存在或不可用");
    }
    return enterprise;
  }

  private async assertEnterpriseDepartmentManager(
    userId: string,
    enterpriseId: string,
  ) {
    if (await this.isPlatformAdminUser(userId)) {
      await this.assertActiveEnterprise(enterpriseId);
      return;
    }
    await this.assertEnterpriseOrganizationManager(userId, enterpriseId);
  }

  private toAdminMembershipRecord(membership: {
    id: string;
    enterpriseId: string;
    userId: string;
    role: string;
    status: string;
    applicantNote?: string | null;
    reviewNote?: string | null;
    reviewedAt?: Date | null;
    joinedAt?: Date | null;
    createdAt: Date;
    updatedAt: Date;
    enterprise?: {
      id: string;
      name: string;
      slug: string;
      status: string;
      enterpriseKind: string;
    } | null;
    user?: {
      id: string;
      role: string;
      identities?: { phoneMasked: string | null; providerUserId: string }[];
    } | null;
  }) {
    const identity = membership.user?.identities?.[0];
    return {
      ...this.toMembershipRecord(membership),
      enterprise: membership.enterprise
        ? {
            id: membership.enterprise.id,
            name: membership.enterprise.name,
            slug: membership.enterprise.slug,
            status: membership.enterprise.status,
          }
        : null,
      user: membership.user
        ? {
            id: membership.user.id,
            role: membership.user.role,
            phone: identity?.phoneMasked ?? identity?.providerUserId ?? null,
          }
        : null,
    };
  }

































































































