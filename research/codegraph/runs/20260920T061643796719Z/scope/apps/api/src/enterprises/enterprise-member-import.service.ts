import {
  BadRequestException,
  ForbiddenException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { Prisma, type PrismaClient } from '@prisma/client';
import { randomUUID } from 'node:crypto';
import { extname } from 'node:path';
import xlsx from 'xlsx';
import { PasswordService } from '../auth/password.service.js';
import { EntitlementService } from '../billing/entitlement.service.js';
import { ZCLAW_QUOTA_MODE_BATCH } from '../zclaw/enterprise-token-batch-quota.service.js';
import { DEFAULT_DYNAMIC_VALIDITY_MONTHS } from '../zclaw/enterprise-token-quota.constants.js';
import { normalizePhone } from '../utils/phone.js';
import { ImportEnterpriseMembersDto } from './dto/import-enterprise-members.dto.js';
import { ImportEnterpriseMembersManualDto } from './dto/import-enterprise-members-manual.dto.js';

const BATCH_STATUS_ACTIVE = 'active';

const ACTIVE_ENTERPRISE_STATUS = 'active';
const ACTIVE_MEMBERSHIP_STATUS = 'active';
const IMPORTABLE_EXTENSIONS = new Set(['.xlsx', '.xls']);
const IMPORT_TEMPLATE_MIME_TYPE =
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
const IMPORT_TEMPLATE_FILENAME = 'enterprise-member-import-template.xlsx';
const IMPORT_MAX_ROWS = 50_000;
const MANUAL_IMPORT_MAX_ROWS = 50;
const IMPORT_WRITE_BATCH_SIZE = 2_000;
const PASSWORD_HASH_CONCURRENCY = 8;
const REQUIRED_HEADERS = ['手机号', '姓名', '部门'] as const;
const IMPORT_MEMBER_ROLE = 'member';
const IMPORT_CONCURRENT_CHANGE_MESSAGE = '导入期间数据状态发生变化，请重新导入';

type ImportJobError = {
  summary: string;
  errors: Array<{ row?: number; field?: string; message: string }>;
};

type ImportRowPlan = {
  rowNumber: number;
  rawPhone: string;
  phone: string;
  realName: string;
  department: string;
};

type ResolvedImportRow = ImportRowPlan & {
  userId: string;
  isNewUser: boolean;
  passwordHash?: string;
};

type ImportProcessInput = {
  enterpriseId: string;
  actorUserId: string;
  initialPassword: string;
  file: Express.Multer.File;
};

type ImportWriteSummary = {
  createdMemberships: number;
  skippedExistingMemberships: number;
  createdMembershipRows?: MembershipWriteRecord[];
};

type MembershipWriteRecord = {
  id: string;
  userId: string;
  realName: string;
  department: string;
};

class ImportValidationError extends Error {
  constructor(readonly details: ImportJobError) {
    super(details.summary);
  }
}

@Injectable()
export class EnterpriseMemberImportService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly passwordService: PasswordService,
    private readonly entitlementService: EntitlementService = {
      ensureB2BMonthlyEntitlementsForMember: async () => ({ skipped: true, batches: [] }),
    } as any,
  ) {}

  async createImportJobForAdmin(
    adminUserId: string,
    dto: ImportEnterpriseMembersDto,
    file?: Express.Multer.File,
  ) {
    const enterpriseId = this.normalizeRequired(dto.enterpriseId, 'enterpriseId');
    const initialPassword = this.validateInitialPassword(dto.initialPassword);
    const importFile = this.validateImportFile(file);
    await this.assertActiveEnterprise(enterpriseId);

    const job = await this.prisma.enterpriseMemberImportJob.create({
      data: {
        enterpriseId,
        createdBy: adminUserId,
        status: 'queued',
        phase: '排队中',
        progress: 0,
      },
      select: { id: true },
    });

    void this.processImportJobUntilUserResolution(job.id, {
      enterpriseId,
      actorUserId: adminUserId,
      initialPassword,
      file: importFile,
    });
    return { jobId: job.id };
  }

  async createImportJobForEnterpriseAdmin(
    callerUserId: string,
    dto: ImportEnterpriseMembersDto,
    file?: Express.Multer.File,
  ) {
    const enterpriseId = this.normalizeRequired(dto.enterpriseId, 'enterpriseId');
    const initialPassword = this.validateInitialPassword(dto.initialPassword);
    const importFile = this.validateImportFile(file);
    await this.assertEnterpriseImportManager(callerUserId, enterpriseId);

    const job = await this.prisma.enterpriseMemberImportJob.create({
      data: {
        enterpriseId,
        createdBy: callerUserId,
        status: 'queued',
        phase: '排队中',
        progress: 0,
      },
      select: { id: true },
    });

    void this.processImportJobUntilUserResolution(job.id, {
      enterpriseId,
      actorUserId: callerUserId,
      initialPassword,
      file: importFile,
    });
    return { jobId: job.id };
  }

  async createManualImportJobForAdmin(
    adminUserId: string,
    dto: ImportEnterpriseMembersManualDto,
  ) {
    const enterpriseId = this.normalizeRequired(dto.enterpriseId, 'enterpriseId');
    const initialPassword = this.validateInitialPassword(dto.initialPassword);
    await this.assertActiveEnterprise(enterpriseId);

    const job = await this.prisma.enterpriseMemberImportJob.create({
      data: {
        enterpriseId,
        createdBy: adminUserId,
        status: 'queued',
        phase: '排队中',
        progress: 0,
      },
      select: { id: true },
    });

    void this.processImportJobFromManual(job.id, {
      enterpriseId,
      actorUserId: adminUserId,
      initialPassword,
      members: dto.members,
    });
    return { jobId: job.id };
  }

  async createManualImportJobForEnterpriseAdmin(
    callerUserId: string,
    dto: ImportEnterpriseMembersManualDto,
  ) {
    const enterpriseId = this.normalizeRequired(dto.enterpriseId, 'enterpriseId');
    const initialPassword = this.validateInitialPassword(dto.initialPassword);
    await this.assertEnterpriseImportManager(callerUserId, enterpriseId);

    const job = await this.prisma.enterpriseMemberImportJob.create({
      data: {
        enterpriseId,
        createdBy: callerUserId,
        status: 'queued',
        phase: '排队中',
        progress: 0,
      },
      select: { id: true },
    });

    void this.processImportJobFromManual(job.id, {
      enterpriseId,
      actorUserId: callerUserId,
      initialPassword,
      members: dto.members,
    });
    return { jobId: job.id };
  }

  async getImportJob(callerUserId: string, jobId: string) {
    const normalizedJobId = this.normalizeRequired(jobId, 'jobId');
    const job = await this.prisma.enterpriseMemberImportJob.findFirst({
      where: { id: normalizedJobId },
    });
    if (!job) {
      throw new NotFoundException('导入任务不存在');
    }

    await this.assertCanReadJob(callerUserId, job.enterpriseId, job.createdBy);

    return {
      job: {
        id: job.id,
        enterpriseId: job.enterpriseId,
        status: job.status,
        phase: job.phase,
        progress: job.progress,
        totalRows: job.totalRows,
        createdUsers: job.createdUsers,
        createdMemberships: job.createdMemberships,
        skippedExistingMemberships: job.skippedExistingMemberships,
        errors: this.normalizeErrorJson(job.errorJson),
        createdAt: job.createdAt,
        updatedAt: job.updatedAt,
        finishedAt: job.finishedAt,
      },
    };
  }

  downloadTemplate() {
    const workbook = xlsx.utils.book_new();
    const worksheet = xlsx.utils.aoa_to_sheet([
      [...REQUIRED_HEADERS],
      ['13800138000', '张三', '研发部'],
    ]);
    xlsx.utils.book_append_sheet(workbook, worksheet, '成员导入模板');
    const buffer = xlsx.write(workbook, { type: 'buffer', bookType: 'xlsx' }) as Buffer;

    return {
      buffer,
      filename: IMPORT_TEMPLATE_FILENAME,
      mimeType: IMPORT_TEMPLATE_MIME_TYPE,
    };
  }

  private async processImportJobUntilUserResolution(jobId: string, input: ImportProcessInput) {
    try {
      await this.prisma.enterpriseMemberImportJob.update({
        where: { id: jobId },
        data: {
          status: 'parsing',
          phase: '解析 Excel 中',
          progress: 35,
        },
      });

      const rows = this.parseImportRows(input.file);
      await this.processImportJobFromRows(jobId, {
        enterpriseId: input.enterpriseId,
        actorUserId: input.actorUserId,
        initialPassword: input.initialPassword,
        rows,
      });
    } catch (error) {
      await this.markJobFailed(jobId, this.toImportJobError(error));
    }
  }

  private async processImportJobFromManual(
    jobId: string,
    input: {
      enterpriseId: string;
      actorUserId: string;
      initialPassword: string;
      members: Array<{ phone: string; realName: string; department: string }>;
    },
  ) {
    try {
      await this.prisma.enterpriseMemberImportJob.update({
        where: { id: jobId },
        data: {
          status: 'parsing',
          phase: '校验录入数据中',
          progress: 35,
        },
      });

      const rows = this.buildImportRowsFromManualMembers(input.members);
      await this.processImportJobFromRows(jobId, {
        enterpriseId: input.enterpriseId,
        actorUserId: input.actorUserId,
        initialPassword: input.initialPassword,
        rows,
      });
    } catch (error) {
      await this.markJobFailed(jobId, this.toImportJobError(error));
    }
  }

  private async processImportJobFromRows(
    jobId: string,
    input: {
      enterpriseId: string;
      actorUserId: string;
      initialPassword: string;
      rows: ImportRowPlan[];
    },
  ) {
    await this.prisma.enterpriseMemberImportJob.update({
      where: { id: jobId },
      data: {
        status: 'validating',
        phase: '校验数据中',
        progress: 55,
        totalRows: input.rows.length,
      },
    });

    await this.ensureDepartments(input.enterpriseId, input.rows);
    const resolvedRows = await this.resolveImportUsers(input.rows, input.initialPassword);
    const createdUsers = resolvedRows.filter((row) => row.isNewUser).length;

    await this.prisma.enterpriseMemberImportJob.update({
      where: { id: jobId },
      data: {
        status: 'writing',
        phase: '写入成员中',
        progress: 75,
        totalRows: input.rows.length,
        createdUsers,
      },
    });

    const summary = await this.writeResolvedImportRows(
      input.enterpriseId,
      input.actorUserId,
      resolvedRows,
    );
    await this.ensureB2BMonthlyEntitlementsForImportedMembers(
      input.enterpriseId,
      input.actorUserId,
      summary.createdMembershipRows ?? [],
    );

    await this.prisma.enterpriseMemberImportJob.update({
      where: { id: jobId },
      data: {
        status: 'succeeded',
        phase: '导入完成',
        progress: 100,
        totalRows: input.rows.length,
        createdUsers,
        createdMemberships: summary.createdMemberships,
        skippedExistingMemberships: summary.skippedExistingMemberships,
        errorJson: Prisma.JsonNull,
        finishedAt: new Date(),
      },
    });
  }

  private buildImportRowsFromManualMembers(
    members: Array<{ phone: string; realName: string; department: string }>,
  ): ImportRowPlan[] {
    if (!members.length) {
      throw this.validationError('手动录入数据为空', [
        { field: 'members', message: '至少录入 1 名成员' },
      ]);
    }
    if (members.length > MANUAL_IMPORT_MAX_ROWS) {
      throw this.validationError('手动录入超出上限', [
        {
          field: 'members',
          message: `单次手动录入最多支持 ${MANUAL_IMPORT_MAX_ROWS} 人`,
        },
      ]);
    }

    const errors: ImportJobError['errors'] = [];
    const rows: ImportRowPlan[] = [];
    const seenPhones = new Map<string, number>();

    members.forEach((member, index) => {
      const rowNumber = index + 2;
      const rawPhone = this.cellToString(member.phone);
      const realName = this.cellToString(member.realName);
      const department = this.cellToString(member.department);

      if (!rawPhone) {
        errors.push({ row: rowNumber, field: '手机号', message: '手机号不能为空' });
      }
      if (!realName) {
        errors.push({ row: rowNumber, field: '姓名', message: '姓名不能为空' });
      }
      if (!department) {
        errors.push({ row: rowNumber, field: '部门', message: '部门不能为空' });
      }
      if (!rawPhone || !realName || !department) {
        return;
      }

      const phone = this.normalizeImportPhone(rawPhone);
      if (!this.isValidImportPhone(rawPhone, phone)) {
        errors.push({ row: rowNumber, field: '手机号', message: '手机号格式不合法' });
        return;
      }

      const duplicateRowNumber = seenPhones.get(phone);
      if (duplicateRowNumber) {
        errors.push({
          row: rowNumber,
          field: '手机号',
          message: `手机号与第 ${duplicateRowNumber} 行重复`,
        });
        return;
      }

      seenPhones.set(phone, rowNumber);
      rows.push({ rowNumber, rawPhone, phone, realName, department });
    });

    if (!rows.length && !errors.length) {
      errors.push({ field: 'members', message: '至少录入 1 名成员' });
    }
    if (errors.length) {
      throw this.validationError('手动录入数据校验失败', errors);
    }

    return rows;
  }

  private parseImportRows(file: Express.Multer.File): ImportRowPlan[] {
    let workbook: xlsx.WorkBook;
    try {
      workbook = xlsx.read(file.buffer, { type: 'buffer', cellDates: false });
    } catch {
      throw this.validationError('Excel 文件解析失败', [
        { field: 'file', message: 'Excel 文件解析失败，请确认文件格式正确' },
      ]);
    }

    const sheetName = workbook.SheetNames[0];
    if (!sheetName) {
      throw this.validationError('Excel 文件没有可读取的工作表', [
        { field: 'file', message: 'Excel 文件没有可读取的工作表' },
      ]);
    }

    const sheet = workbook.Sheets[sheetName];
    const matrix = xlsx.utils.sheet_to_json<unknown[]>(sheet, {
      header: 1,
      defval: '',
      raw: false,
      blankrows: false,
    });
    if (!matrix.length) {
      throw this.validationError('Excel 文件为空', [
        { field: 'file', message: 'Excel 文件为空' },
      ]);
    }

    const header = matrix[0].map((cell) => this.cellToString(cell));
    const headerIndex = new Map(header.map((name, index) => [name, index]));
    const missingHeaders = REQUIRED_HEADERS.filter((name) => !headerIndex.has(name));
    if (missingHeaders.length) {
      throw this.validationError('Excel 表头不完整', [
        {
          row: 1,
          field: '表头',
          message: `缺少表头：${missingHeaders.join('、')}`,
        },
      ]);
    }

    const errors: ImportJobError['errors'] = [];
    const rows: ImportRowPlan[] = [];
    const seenPhones = new Map<string, number>();

    for (let rowIndex = 1; rowIndex < matrix.length; rowIndex += 1) {
      const row = matrix[rowIndex];
      const rowNumber = rowIndex + 1;
      const rawPhone = this.cellToString(row[headerIndex.get('手机号') ?? -1]);
      const realName = this.cellToString(row[headerIndex.get('姓名') ?? -1]);
      const department = this.cellToString(row[headerIndex.get('部门') ?? -1]);

      if (!rawPhone && !realName && !department) {
        continue;
      }

      if (!rawPhone) {
        errors.push({ row: rowNumber, field: '手机号', message: '手机号不能为空' });
      }
      if (!realName) {
        errors.push({ row: rowNumber, field: '姓名', message: '姓名不能为空' });
      }
      if (!department) {
        errors.push({ row: rowNumber, field: '部门', message: '部门不能为空' });
      }
      if (!rawPhone || !realName || !department) {
        continue;
      }

      const phone = this.normalizeImportPhone(rawPhone);
      if (!this.isValidImportPhone(rawPhone, phone)) {
        errors.push({ row: rowNumber, field: '手机号', message: '手机号格式不合法' });
        continue;
      }

      const duplicateRowNumber = seenPhones.get(phone);
      if (duplicateRowNumber) {
        errors.push({
          row: rowNumber,
          field: '手机号',
          message: `手机号与第 ${duplicateRowNumber} 行重复`,
        });
        continue;
      }

      seenPhones.set(phone, rowNumber);
      rows.push({ rowNumber, rawPhone, phone, realName, department });
    }

    if (rows.length > IMPORT_MAX_ROWS) {
      errors.push({
        field: 'file',
        message: `单次导入最多支持 ${IMPORT_MAX_ROWS} 行，请拆分文件后重试`,
      });
    }
    if (!rows.length && !errors.length) {
      errors.push({ field: 'file', message: 'Excel 没有有效数据行' });
    }
    if (errors.length) {
      throw this.validationError('Excel 数据校验失败', errors);
    }

    return rows;
  }

  private async ensureDepartments(enterpriseId: string, rows: ImportRowPlan[]) {
    const existingDepartments = await this.prisma.enterpriseDepartment.findMany({
      where: { enterpriseId, isDeleted: false },
      select: { name: true, sortOrder: true },
    });
    const existingNames = new Set(existingDepartments.map((department) => department.name));
    const uniqueRowNames = [...new Set(rows.map((row) => row.department))];
    const missingNames = uniqueRowNames.filter((name) => !existingNames.has(name));

    if (!missingNames.length) {
      return;
    }

    const maxSortOrder = existingDepartments.reduce(
      (max, department) => Math.max(max, department.sortOrder),
      -1,
    );
    const baseSortOrder = existingDepartments.length ? maxSortOrder + 1 : 0;

    const createData = missingNames.map((name, index) => ({
      enterpriseId,
      name,
      sortOrder: baseSortOrder + index,
      isDeleted: false,
    }));

    await this.prisma.enterpriseDepartment.createMany({
      data: createData,
      skipDuplicates: true,
    });

    console.log(
      `[EnterpriseMemberImport] Auto-created ${missingNames.length} department(s) for enterprise ${enterpriseId}: ${missingNames.join(", ")}`,
    );
  }

  private async resolveImportUsers(
    rows: ImportRowPlan[],
    initialPassword: string,
  ): Promise<ResolvedImportRow[]> {
    const phones = rows.map((row) => row.phone);
    const identities = await this.prisma.userIdentity.findMany({
      where: {
        provider: 'phone',
        providerUserId: { in: phones },
        isDeleted: false,
        user: { isDeleted: false },
      },
      select: { providerUserId: true, userId: true },
    });
    const userIdByPhone = new Map(
      identities.map((identity) => [identity.providerUserId, identity.userId]),
    );
    const passwordHashesByPhone = new Map<string, string>();
    const newRows = rows.filter((row) => !userIdByPhone.has(row.phone));

    await this.mapWithConcurrency(newRows, PASSWORD_HASH_CONCURRENCY, async (row) => {
      passwordHashesByPhone.set(row.phone, await this.passwordService.hashPassword(initialPassword));
    });

    return rows.map((row) => {
      const existingUserId = userIdByPhone.get(row.phone);
      if (existingUserId) {
        return { ...row, userId: existingUserId, isNewUser: false };
      }
      return {
        ...row,
        userId: randomUUID(),
        isNewUser: true,
        passwordHash: passwordHashesByPhone.get(row.phone),
      };
    });
  }

  private async writeResolvedImportRows(
    enterpriseId: string,
    actorUserId: string,
    rows: ResolvedImportRow[],
  ): Promise<ImportWriteSummary> {
    try {
      return await this.prisma.$transaction(async (tx) => {
        const newUserRows = rows.filter((row) => row.isNewUser);
        await this.insertUsers(tx, newUserRows);
        await this.insertUserIdentities(tx, newUserRows);
        await this.insertWallets(tx, newUserRows);

        const existingMemberships = await tx.enterpriseMembership.findMany({
          where: {
            enterpriseId,
            userId: { in: rows.map((row) => row.userId) },
            isDeleted: false,
          },
          select: { id: true, userId: true },
        });
        const existingMembershipByUserId = new Map(
          existingMemberships.map((membership) => [membership.userId, membership]),
        );
        const createMembershipRows: MembershipWriteRecord[] = [];
        let skippedExistingMemberships = 0;

        for (const row of rows) {
          const existingMembership = existingMembershipByUserId.get(row.userId);
          if (!existingMembership) {
            createMembershipRows.push({
              id: randomUUID(),
              userId: row.userId,
              realName: row.realName,
              department: row.department,
            });
            continue;
          }
          skippedExistingMemberships += 1;
        }

        await this.assertB2BImportSeatCapacity(tx, enterpriseId, createMembershipRows.length);
        await this.insertMemberships(tx, enterpriseId, actorUserId, createMembershipRows);
        await this.initializeConversationQuotaForImportedMembers(tx, enterpriseId, createMembershipRows);

        return {
          createdMemberships: createMembershipRows.length,
          skippedExistingMemberships,
          createdMembershipRows: createMembershipRows,
        };
      });
    } catch {
      throw new Error(IMPORT_CONCURRENT_CHANGE_MESSAGE);
    }
  }

  private async insertUsers(tx: Prisma.TransactionClient, rows: ResolvedImportRow[]) {
    for (const batch of this.chunk(rows, IMPORT_WRITE_BATCH_SIZE)) {
      const records = batch.map((row) => ({
        id: row.userId,
        passwordHash: row.passwordHash,
      }));
      if (!records.length) {
        continue;
      }
      await tx.$executeRawUnsafe(
        `
        INSERT INTO "users" (
          "id",
          "role",
          "status",
          "passwordHash",
          "createdAt",
          "updatedAt",
          "isDeleted"
        )
        SELECT
          record."id",
          'user',
          'active',
          record."passwordHash",
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          false
        FROM jsonb_to_recordset($1::jsonb) AS record("id" text, "passwordHash" text)
        `,
        JSON.stringify(records),
      );
    }
  }

  private async insertUserIdentities(tx: Prisma.TransactionClient, rows: ResolvedImportRow[]) {
    for (const batch of this.chunk(rows, IMPORT_WRITE_BATCH_SIZE)) {
      const records = batch.map((row) => ({
        id: randomUUID(),
        userId: row.userId,
        providerUserId: row.phone,
      }));
      if (!records.length) {
        continue;
      }
      await tx.$executeRawUnsafe(
        `
        INSERT INTO "user_identities" (
          "id",
          "userId",
          "provider",
          "providerUserId",
          "createdAt",
          "updatedAt",
          "isDeleted"
        )
        SELECT
          record."id",
          record."userId",
          'phone',
          record."providerUserId",
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          false
        FROM jsonb_to_recordset($1::jsonb)
          AS record("id" text, "userId" text, "providerUserId" text)
        `,
        JSON.stringify(records),
      );
    }
  }

  private async insertWallets(tx: Prisma.TransactionClient, rows: ResolvedImportRow[]) {
    for (const batch of this.chunk(rows, IMPORT_WRITE_BATCH_SIZE)) {
      const records = batch.map((row) => ({ userId: row.userId }));
      if (!records.length) {
        continue;
      }
      await tx.$executeRawUnsafe(
        `
        INSERT INTO "wallets" (
          "userId",
          "balance",
          "version",
          "createdAt",
          "updatedAt",
          "isDeleted"
        )
        SELECT
          record."userId",
          0,
          0,
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          false
        FROM jsonb_to_recordset($1::jsonb) AS record("userId" text)
        ON CONFLICT ("userId") DO NOTHING
        `,
        JSON.stringify(records),
      );
    }
  }

  private async insertMemberships(
    tx: Prisma.TransactionClient,
    enterpriseId: string,
    actorUserId: string,
    rows: MembershipWriteRecord[],
  ) {
    for (const batch of this.chunk(rows, IMPORT_WRITE_BATCH_SIZE)) {
      if (!batch.length) {
        continue;
      }
      await tx.$executeRawUnsafe(
        `
        INSERT INTO "enterprise_memberships" (
          "id",
          "enterpriseId",
          "userId",
          "role",
          "status",
          "realName",
          "department",
          "reviewedBy",
          "reviewedAt",
          "joinedAt",
          "createdAt",
          "updatedAt",
          "isDeleted"
        )
        SELECT
          record."id",
          $2,
          record."userId",
          '${IMPORT_MEMBER_ROLE}',
          'active',
          record."realName",
          record."department",
          $3,
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          (NOW() AT TIME ZONE 'UTC'),
          false
        FROM jsonb_to_recordset($1::jsonb)
          AS record("id" text, "userId" text, "realName" text, "department" text)
        `,
        JSON.stringify(batch),
        enterpriseId,
        actorUserId,
      );
    }
  }

  private async assertB2BImportSeatCapacity(
    tx: Prisma.TransactionClient,
    enterpriseId: string,
    seatsToAdd: number,
  ) {
    if (seatsToAdd <= 0) return;
    if (typeof (tx as any).$executeRaw === 'function') {
      await tx.$executeRaw`
        SELECT "id"
        FROM "enterprise_memberships"
        WHERE "enterpriseId" = ${enterpriseId}
          AND "isDeleted" = false
        FOR UPDATE
      `;
    }
    const activePlan = await this.getActiveB2BMonthlyPlanSeatLimit(tx, enterpriseId);
    if (!activePlan) return;
    const occupiedSeats = await tx.enterpriseMembership.count({
      where: {
        enterpriseId,
        status: { in: ['active', 'disabled'] },
        isDeleted: false,
      },
    });
    if (occupiedSeats + seatsToAdd > activePlan.memberLimit) {
      throw this.validationError('本次导入成员数会超过套餐席位上限', [
        {
          field: 'file',
          message: `本次导入成员数会超过套餐席位上限，当前占席 ${occupiedSeats}，新增 ${seatsToAdd}，上限 ${activePlan.memberLimit}`,
        },
      ]);
    }
  }

  private async getActiveB2BMonthlyPlanSeatLimit(tx: Prisma.TransactionClient, enterpriseId: string) {
    const db = tx as any;
    if (!db.enterprise?.findFirst || !db.entitlementBatch?.findFirst) return null;
    const enterprise = await db.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { enterpriseKind: true },
    });
    if (enterprise?.enterpriseKind !== 'b2b') return null;
    const now = new Date();
    const anchor = await db.entitlementBatch.findFirst({
      where: {
        enterpriseId,
        userId: null,
        subjectType: 'enterprise',
        entitlementType: 'monthly_plan',
        status: { in: ['active', 'scheduled'] },
        validFrom: { lte: now },
        OR: [{ validUntil: null }, { validUntil: { gt: now } }],
        isDeleted: false,
      },
      orderBy: [{ validFrom: 'desc' }, { createdAt: 'desc' }],
      select: { planSnapshot: true, metadata: true },
    });
    if (!anchor) return null;
    const snapshot = this.objectRecord(anchor.planSnapshot);
    const metadata = this.objectRecord(anchor.metadata);
    const seatSnapshot = this.objectRecord(metadata.seatSnapshot);
    const memberLimit = Number(snapshot.memberLimit ?? seatSnapshot.memberLimit);
    return Number.isFinite(memberLimit) && memberLimit > 0 ? { memberLimit } : null;
  }

  private async isDefaultQuotaEffective(tx: Prisma.TransactionClient, enterpriseId: string) {
    const db = tx as any;
    if (!db.enterprise?.findFirst || !db.enterpriseDefaultQuotaPolicy?.findUnique) {
      return true;
    }
    const enterprise = await db.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { enterpriseKind: true },
    });
    if (enterprise?.enterpriseKind !== 'b2b') return false;
    if (await this.getActiveB2BMonthlyPlanSeatLimit(tx, enterpriseId)) return false;
    const policy = await db.enterpriseDefaultQuotaPolicy.findUnique({
      where: { enterpriseId },
      select: { enabled: true },
    });
    return policy?.enabled === true;
  }

  private objectRecord(value: unknown): Record<string, any> {
    return value && typeof value === 'object' && !Array.isArray(value)
      ? (value as Record<string, any>)
      : {};
  }

  private async ensureB2BMonthlyEntitlementsForImportedMembers(
    enterpriseId: string,
    actorUserId: string,
    rows: MembershipWriteRecord[],
  ) {
    for (const row of rows) {
      await this.entitlementService.ensureB2BMonthlyEntitlementsForMember({
        enterpriseId,
        userId: row.userId,
        membershipId: row.id,
        operatorId: actorUserId,
      });
    }
  }

  private async initializeConversationQuotaForImportedMembers(
    tx: Prisma.TransactionClient,
    enterpriseId: string,
    rows: MembershipWriteRecord[],
  ) {
    if (!rows.length) {
      return;
    }
    if (!(await this.isDefaultQuotaEffective(tx, enterpriseId))) {
      return;
    }

    const config = await tx.zclawEnterpriseConversationQuotaConfig.findUnique({
      where: { enterpriseId },
      select: {
        quotaMode: true,
        conversationLimit: true,
        tokenLimit: true,
        periodType: true,
        resetVersion: true,
        batchValidityType: true,
        batchDynamicValidityMonths: true,
      },
    });
    if (!config) {
      return;
    }

    if (config.quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
      const dynamicMonths =
        config.batchValidityType === 'dynamic'
          ? (config.batchDynamicValidityMonths ?? DEFAULT_DYNAMIC_VALIDITY_MONTHS)
          : null;
      await this.initializeBatchQuotaForImportedMembers(tx, enterpriseId, rows, dynamicMonths);
      return;
    }

    if (config.conversationLimit == null && config.tokenLimit == null) {
      return;
    }

    const quotaRows = rows.map((row) => ({ userId: row.userId }));
    for (const batch of this.chunk(quotaRows, IMPORT_WRITE_BATCH_SIZE)) {
      if (!batch.length) {
        continue;
      }
      await tx.$executeRawUnsafe(
        `
        INSERT INTO "zclaw_enterprise_conversation_quota_usages" (
          "id",
          "enterpriseId",
          "userId",
          "remainingConversations",
          "limitSnapshot",
          "overrideMode",
          "tokenOverrideMode",
          "periodType",
          "tokenLimitSnapshot",
          "windowStart",
          "windowEnd",
          "resetVersion",
          "createdAt",
          "updatedAt"
        )
        SELECT
          'zclaw-conv-quota-' || $2 || '-' || record."userId",
          $2,
          record."userId",
          config."conversationLimit",
          config."conversationLimit",
          'inherit',
          'inherit',
          config."periodType",
          config."tokenLimit",
          DATE_TRUNC('month', NOW()),
          DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 microsecond',
          config."resetVersion",
          NOW(),
          NOW()
        FROM jsonb_to_recordset($1::jsonb) AS record("userId" text)
        CROSS JOIN "zclaw_enterprise_conversation_quota_configs" config
        WHERE config."enterpriseId" = $2
          AND (config."conversationLimit" IS NOT NULL OR config."tokenLimit" IS NOT NULL)
        ON CONFLICT ("enterpriseId", "userId") DO UPDATE SET
          "remainingConversations" = CASE
            WHEN "zclaw_enterprise_conversation_quota_usages"."overrideMode" = 'limited'
             AND "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride" IS NOT NULL
            THEN "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride"
            ELSE COALESCE(EXCLUDED."remainingConversations", "zclaw_enterprise_conversation_quota_usages"."remainingConversations")
          END,
          "limitSnapshot" = CASE
            WHEN "zclaw_enterprise_conversation_quota_usages"."overrideMode" = 'limited'
             AND "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride" IS NOT NULL
            THEN "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride"
            ELSE COALESCE(EXCLUDED."limitSnapshot", "zclaw_enterprise_conversation_quota_usages"."limitSnapshot")
          END,
          "periodType" = EXCLUDED."periodType",
          "tokenLimitSnapshot" = CASE
            WHEN "zclaw_enterprise_conversation_quota_usages"."tokenOverrideMode" = 'limited'
             AND "zclaw_enterprise_conversation_quota_usages"."tokenLimitOverride" IS NOT NULL
            THEN "zclaw_enterprise_conversation_quota_usages"."tokenLimitOverride"
            ELSE COALESCE(EXCLUDED."tokenLimitSnapshot", "zclaw_enterprise_conversation_quota_usages"."tokenLimitSnapshot")
          END,
          "resetVersion" = EXCLUDED."resetVersion",
          "updatedAt" = NOW()
        `,
        JSON.stringify(batch),
        enterpriseId,
      );
    }
  }

  private async initializeBatchQuotaForImportedMembers(
    tx: Prisma.TransactionClient,
    enterpriseId: string,
    rows: MembershipWriteRecord[],
    dynamicValidityMonths?: number | null,
  ) {
    const defaultBatch = await tx.zclawEnterpriseTokenQuotaBatch.findFirst({
      where: { enterpriseId, isDefault: true, status: BATCH_STATUS_ACTIVE },
      select: { id: true },
    });
    if (!defaultBatch) {
      return;
    }

    const isDynamic = dynamicValidityMonths != null && dynamicValidityMonths > 0;

    const quotaRows = rows.map((row) => ({
      id: randomUUID(),
      userId: row.userId,
    }));
    for (const batch of this.chunk(quotaRows, IMPORT_WRITE_BATCH_SIZE)) {
      if (!batch.length) {
        continue;
      }
      if (isDynamic) {
        await tx.$executeRawUnsafe(
          `
        INSERT INTO "zclaw_enterprise_token_quota_members" (
          "id",
          "batchId",
          "enterpriseId",
          "userId",
          "validFrom",
          "validTo",
          "assignedAt",
          "createdAt",
          "updatedAt"
        )
        SELECT
          record."id",
          $3,
          $2,
          record."userId",
          NOW(),
          NOW() + ($4 * INTERVAL '1 month'),
          NOW(),
          NOW(),
          NOW()
        FROM jsonb_to_recordset($1::jsonb) AS record("id" text, "userId" text)
        ON CONFLICT ("enterpriseId", "userId") DO NOTHING
        `,
          JSON.stringify(batch),
          enterpriseId,
          defaultBatch.id,
          dynamicValidityMonths,
        );
      } else {
        await tx.$executeRawUnsafe(
          `
        INSERT INTO "zclaw_enterprise_token_quota_members" (
          "id",
          "batchId",
          "enterpriseId",
          "userId",
          "assignedAt",
          "createdAt",
          "updatedAt"
        )
        SELECT
          record."id",
          $3,
          $2,
          record."userId",
          NOW(),
          NOW(),
          NOW()
        FROM jsonb_to_recordset($1::jsonb) AS record("id" text, "userId" text)
        ON CONFLICT ("enterpriseId", "userId") DO NOTHING
        `,
          JSON.stringify(batch),
          enterpriseId,
          defaultBatch.id,
        );
      }
    }
  }

  private async mapWithConcurrency<T>(
    items: T[],
    concurrency: number,
    mapper: (item: T) => Promise<void>,
  ) {
    let nextIndex = 0;
    const workers = Array.from({ length: Math.min(concurrency, items.length) }, async () => {
      while (nextIndex < items.length) {
        const item = items[nextIndex];
        nextIndex += 1;
        await mapper(item);
      }
    });
    await Promise.all(workers);
  }

  private chunk<T>(items: T[], size: number) {
    const chunks: T[][] = [];
    for (let index = 0; index < items.length; index += size) {
      chunks.push(items.slice(index, index + size));
    }
    return chunks;
  }

  private async assertActiveEnterprise(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: {
        id: enterpriseId,
        status: ACTIVE_ENTERPRISE_STATUS,
        isDeleted: false,
      },
      select: { id: true },
    });
    if (!enterprise) {
      throw new NotFoundException('目标组织不存在或不可用');
    }
  }

  private async assertEnterpriseImportManager(userId: string, enterpriseId: string) {
    await this.assertActiveEnterprise(enterpriseId);
    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
      },
      select: { role: true },
    });
    if (!membership || !['owner', 'admin', 'operator'].includes(membership.role)) {
      throw new ForbiddenException('需要组织管理员或运营员权限');
    }
  }

  private async assertCanReadJob(callerUserId: string, enterpriseId: string, createdBy: string) {
    if (callerUserId === createdBy) {
      return;
    }

    const user = await this.prisma.user.findFirst({
      where: { id: callerUserId, status: 'active', isDeleted: false },
      select: { role: true },
    });
    if (user?.role === 'admin') {
      return;
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId: callerUserId,
        enterpriseId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
      },
      select: { role: true },
    });
    if (membership && ['owner', 'admin', 'operator'].includes(membership.role)) {
      return;
    }

    throw new ForbiddenException('无权查看该导入任务');
  }

  private normalizeRequired(value: string | undefined, fieldName: string) {
    const trimmed = value?.trim() ?? '';
    if (!trimmed) {
      throw new BadRequestException(`${fieldName} is required`);
    }
    return trimmed;
  }

  private validateInitialPassword(initialPassword: string | undefined) {
    const password = this.normalizeRequired(initialPassword, 'initialPassword');
    this.passwordService.assertNewPassword(password);
    return password;
  }

  private validateImportFile(file?: Express.Multer.File): Express.Multer.File {
    if (!file) {
      throw new BadRequestException('file is required');
    }
    const extension = extname(file.originalname || '').toLowerCase();
    if (!IMPORTABLE_EXTENSIONS.has(extension)) {
      throw new BadRequestException('仅支持 .xlsx 或 .xls 文件');
    }
    if (!file.buffer?.length) {
      throw new BadRequestException('文件内容为空');
    }
    return file;
  }

  private normalizeErrorJson(value: unknown): ImportJobError | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const candidate = value as Partial<ImportJobError>;
    return {
      summary: typeof candidate.summary === 'string' ? candidate.summary : '',
      errors: Array.isArray(candidate.errors)
        ? candidate.errors.map((item) => ({
            row: typeof item?.row === 'number' ? item.row : undefined,
            field: typeof item?.field === 'string' ? item.field : undefined,
            message: typeof item?.message === 'string' ? item.message : '',
          }))
        : [],
    };
  }

  private normalizeImportPhone(rawPhone: string) {
    const compact = rawPhone.replace(/\s+/g, '');
    if (/^861[3-9]\d{9}$/.test(compact)) {
      return `+86${compact.slice(2)}`;
    }
    return normalizePhone(compact);
  }

  private isValidImportPhone(rawPhone: string, normalizedPhone: string) {
    const compact = rawPhone.replace(/\s+/g, '');
    return (
      /^1[3-9]\d{9}$/.test(compact) ||
      /^861[3-9]\d{9}$/.test(compact) ||
      /^\+861[3-9]\d{9}$/.test(compact) ||
      /^\+\d{6,20}$/.test(normalizedPhone)
    );
  }

  private cellToString(value: unknown) {
    return String(value ?? '').trim();
  }

  private validationError(summary: string, errors: ImportJobError['errors']) {
    return new ImportValidationError({ summary, errors });
  }

  private toImportJobError(error: unknown): ImportJobError {
    if (error instanceof ImportValidationError) {
      return error.details;
    }
    const message = error instanceof Error ? error.message : '导入解析失败';
    return { summary: message, errors: [{ message }] };
  }

  private async markJobFailed(jobId: string, errorJson: ImportJobError) {
    try {
      await this.prisma.enterpriseMemberImportJob.update({
        where: { id: jobId },
        data: {
          status: 'failed',
          phase: '导入失败',
          progress: 0,
          errorJson,
          finishedAt: new Date(),
        },
      });
    } catch {
      // The job query endpoint will expose the last persisted state if failure reporting fails.
    }
  }
}
