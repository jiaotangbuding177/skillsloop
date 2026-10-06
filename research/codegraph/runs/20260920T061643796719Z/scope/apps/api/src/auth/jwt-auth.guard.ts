import {
  CanActivate,
  ExecutionContext,
  Inject,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { PrismaClient } from '@prisma/client';
import jwt from 'jsonwebtoken';
import { getCookie, getBearerToken } from './auth.util.js';
import { AccessTokenPayload } from './types.js';

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(
    private readonly configService: ConfigService,
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const req = context.switchToHttp().getRequest();
    const token = getBearerToken(req) ?? getCookie(req, 'access_token');
    if (!token) {
      throw new UnauthorizedException('请先登录');
    }

    let payload: AccessTokenPayload;
    try {
      payload = jwt.verify(
        token,
        this.configService.getOrThrow<string>('JWT_ACCESS_SECRET'),
      ) as AccessTokenPayload;
    } catch (_err) {
      throw new UnauthorizedException('登录已过期，请重新登录');
    }

    const user = await this.prisma.user.findFirst({
      where: { id: payload.sub, isDeleted: false, status: 'active' },
      select: { id: true },
    });
    if (!user) {
      throw new UnauthorizedException('登录已过期或账号不可用，请重新登录');
    }

    req.user = { userId: payload.sub };
    return true;
  }
}

@Injectable()
export class OptionalJwtAuthGuard implements CanActivate {
  constructor(
    private readonly configService: ConfigService,
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const req = context.switchToHttp().getRequest();
    const token = getBearerToken(req) ?? getCookie(req, 'access_token');
    if (!token) {
      return true;
    }

    try {
      const payload = jwt.verify(
        token,
        this.configService.getOrThrow<string>('JWT_ACCESS_SECRET'),
      ) as AccessTokenPayload;

      const user = await this.prisma.user.findFirst({
        where: { id: payload.sub, isDeleted: false, status: 'active' },
        select: { id: true },
      });
      if (user) {
        req.user = { userId: payload.sub };
      }
    } catch {
      // Ignore invalid tokens to allow public access paths to proceed.
    }

    return true;
  }
}
