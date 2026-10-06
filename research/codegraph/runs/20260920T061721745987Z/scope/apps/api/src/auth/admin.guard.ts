import { Inject, CanActivate, ExecutionContext, Injectable } from '@nestjs/common';
import type { PrismaClient } from '@prisma/client';

@Injectable()
export class AdminGuard implements CanActivate {
  constructor(@Inject('PrismaClient') private readonly prisma: PrismaClient) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const req = context.switchToHttp().getRequest();
    const userId = req?.user?.userId as string | undefined;
    if (!userId) return false;

    const user = await this.prisma.user.findFirst({
      where: { id: userId, isDeleted: false, status: 'active' },
      select: { role: true },
    });

    return user?.role === 'admin';
  }
}
