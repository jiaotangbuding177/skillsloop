'use client';


import { translateAutoText } from '@/lib/i18n/translate-auto-text';
import React from 'react';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

export const SKILL_ADMIN_PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

type SkillAdminTablePaginationProps = {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
};

function PageSizeSelect({
  value,
  onChange,
}: {
  value: number;
  onChange: (size: number) => void;
}) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className="group inline-flex h-8 min-w-[108px] cursor-pointer items-center justify-between gap-1.5 rounded border border-[#d9d9d9] bg-white px-2.5 text-sm text-[#595959] outline-none transition-colors hover:border-[#4096ff] focus:border-[#1677ff] data-[state=open]:border-[#1677ff]"
        >
          <span>{value} 条/页</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-[#bfbfbf] transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={4}
          className="z-[120] min-w-[108px] overflow-hidden rounded border border-[#f0f0f0] bg-white p-1 shadow-lg"
        >
          {SKILL_ADMIN_PAGE_SIZE_OPTIONS.map((size) => (
            <DropdownMenu.Item
              key={size}
              onSelect={() => onChange(size)}
              className={`cursor-pointer rounded px-3 py-1.5 text-sm outline-none ${size === value
                  ? 'bg-[#e6f4ff] font-medium text-[#1677ff]'
                  : 'text-[#333] hover:bg-[#f5f5f5]'
                }`}
            >
              {size} 条/页
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

function NavButton({
  disabled,
  onClick,
  children,
}: {
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded border border-[#d9d9d9] bg-white text-[#595959] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:border-[#f0f0f0] disabled:bg-[#fafafa] disabled:text-[#d9d9d9]"
    >
      {children}
    </button>
  );
}

function PageButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex h-8 min-w-8 cursor-pointer items-center justify-center rounded border px-2 text-sm transition-colors ${active
          ? 'border-[#1677ff] bg-[#1677ff] font-medium text-white'
          : 'border-[#d9d9d9] bg-white text-[#595959] hover:border-[#4096ff] hover:text-[#1677ff]'
        }`}
    >
      {children}
    </button>
  );
}

export function SkillAdminTablePagination({
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: SkillAdminTablePaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const [jumpPage, setJumpPage] = React.useState(String(page));
  const showPageNav = totalPages > 1;

  React.useEffect(() => {
    setJumpPage(String(page));
  }, [page]);

  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1).filter((pageNumber) => {
    if (totalPages <= 7) return true;
    if (pageNumber === 1 || pageNumber === totalPages) return true;
    return Math.abs(pageNumber - page) <= 1;
  });

  const handleJump = () => {
    const next = Number.parseInt(jumpPage, 10);
    if (!Number.isFinite(next)) return;
    onPageChange(Math.min(totalPages, Math.max(1, next)));
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-[#f0f0f0] bg-[#fafafa] px-4 py-2.5">
      <span className="text-sm text-[#8c8c8c]">
        共 <span className="font-medium text-[#333]">{total}</span> 条
      </span>

      <div className="flex flex-wrap items-center gap-2">
        <PageSizeSelect
          value={pageSize}
          onChange={(size) => {
            onPageSizeChange(size);
            onPageChange(1);
          }}
        />

        {showPageNav ? (
          <>
            <span className="mx-0.5 hidden h-4 w-px bg-[#e8e8e8] sm:inline-block" aria-hidden />
            <NavButton disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </NavButton>

            {pageNumbers.map((pageNumber, index) => {
              const prev = pageNumbers[index - 1];
              const showEllipsis = prev !== undefined && pageNumber - prev > 1;
              return (
                <React.Fragment key={pageNumber}>
                  {showEllipsis ? (
                    <span className="inline-flex h-8 w-6 items-center justify-center text-[#bfbfbf]">…</span>
                  ) : null}
                  <PageButton active={page === pageNumber} onClick={() => onPageChange(pageNumber)}>
                    {pageNumber}
                  </PageButton>
                </React.Fragment>
              );
            })}

            <NavButton disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              <ChevronRight className="h-4 w-4" />
            </NavButton>

            <span className="mx-0.5 hidden h-4 w-px bg-[#e8e8e8] sm:inline-block" aria-hidden />

            <div className="flex items-center gap-1.5 text-sm text-[#8c8c8c]">
              <span className="whitespace-nowrap">{translateAutoText('前往')}</span>
              <input
                value={jumpPage}
                onChange={(event) => setJumpPage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') handleJump();
                }}
                className="h-8 w-12 rounded border border-[#d9d9d9] bg-white px-1 text-center text-sm text-[#333] outline-none transition-colors hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20"
              />
              <span className="whitespace-nowrap">{translateAutoText('页')}</span>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
