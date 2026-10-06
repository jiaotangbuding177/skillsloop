'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { Check, Loader2, Search, X } from 'lucide-react';
import React from 'react';
import type { SkillEmergenceCandidate } from '@/api';
import { pickEmergenceSubtitle } from '@/lib/skill-market-md';

type BatchAcceptDialogProps = {
  open: boolean;
  items: SkillEmergenceCandidate[];
  submitting: boolean;
  onOpenChange: (open: boolean) => void;
  onAccept: (ids: string[]) => Promise<void>;
};

function itemTitle(item: SkillEmergenceCandidate) {
  return item.skillTitle || item.clusterTitle;
}

export default function BatchAcceptDialog({
  open,
  items,
  submitting,
  onOpenChange,
  onAccept,
}: BatchAcceptDialogProps) {
  const [keyword, setKeyword] = React.useState('');
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(() => new Set());

  React.useEffect(() => {
    if (!open) return;
    setKeyword('');
    setSelectedIds(new Set());
  }, [open]);

  const filtered = React.useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => {
      const title = itemTitle(item).toLowerCase();
      const summary = (item.summary || '').toLowerCase();
      return title.includes(q) || summary.includes(q);
    });
  }, [items, keyword]);

  const allFilteredSelected =
    filtered.length > 0 && filtered.every((item) => selectedIds.has(item.id));
  const someFilteredSelected =
    filtered.some((item) => selectedIds.has(item.id)) && !allFilteredSelected;

  const toggleAll = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allFilteredSelected) {
        for (const item of filtered) next.delete(item.id);
      } else {
        for (const item of filtered) next.add(item.id);
      }
      return next;
    });
  };

  const toggleOne = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedCount = selectedIds.size;

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(next) => {
        if (submitting && !next) return;
        onOpenChange(next);
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[130] bg-slate-950/45 backdrop-blur-[1px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[131] flex max-h-[min(100dvh-24px,640px)] w-[min(560px,calc(100vw-24px))] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl outline-none">
          <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
            <div>
              <Dialog.Title className="text-lg font-semibold text-slate-950">批量纳入</Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-slate-500">
                勾选后纳入个人 Skill
              </Dialog.Description>
            </div>
            <Dialog.Close
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label="关闭"
              disabled={submitting}
            >
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>

          <div className="flex min-h-0 flex-1 flex-col px-6 py-4">
            <div className="relative shrink-0">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索 Skill 名称"
                disabled={submitting}
                className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus-visible:border-blue-600"
              />
            </div>

            <div className="mt-3 flex shrink-0 items-center justify-between">
              <button
                type="button"
                disabled={submitting || filtered.length === 0}
                onClick={toggleAll}
                className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 disabled:opacity-50"
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-md border ${
                    allFilteredSelected
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : 'border-slate-300 bg-white'
                  }`}
                  aria-hidden
                >
                  {allFilteredSelected ? (
                    <Check className="h-3.5 w-3.5" strokeWidth={3} />
                  ) : someFilteredSelected ? (
                    <span className="h-0.5 w-2.5 rounded bg-blue-600" />
                  ) : null}
                </span>
                全选
              </button>
              <span className="text-sm text-slate-500">已选 {selectedCount}</span>
            </div>

            <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
              {items.length === 0 ? (
                <p className="py-12 text-center text-sm text-slate-500">暂无待确认 Skill</p>
              ) : filtered.length === 0 ? (
                <p className="py-12 text-center text-sm text-slate-500">没有匹配的 Skill</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {filtered.map((item) => {
                    const selected = selectedIds.has(item.id);
                    const title = itemTitle(item);
                    const subtitle = pickEmergenceSubtitle(title, item.summary);
                    return (
                      <li key={item.id}>
                        <button
                          type="button"
                          disabled={submitting}
                          onClick={() => toggleOne(item.id)}
                          className="flex w-full items-start gap-3 py-3 text-left hover:bg-slate-50 disabled:opacity-50"
                        >
                          <span
                            className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border ${
                              selected
                                ? 'border-blue-600 bg-blue-600 text-white'
                                : 'border-slate-300 bg-white'
                            }`}
                            aria-hidden
                          >
                            {selected ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : null}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-medium text-slate-900">
                              {title}
                            </span>
                            {subtitle ? (
                              <span className="mt-0.5 line-clamp-1 text-xs text-slate-500">
                                {subtitle}
                              </span>
                            ) : null}
                            <span className="mt-1 block text-xs text-slate-400">
                              {item.evidenceToCount} 对话片段
                            </span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          <div className="flex shrink-0 items-center justify-end gap-3 border-t border-slate-200 px-6 py-4">
            <button
              type="button"
              disabled={submitting}
              onClick={() => onOpenChange(false)}
              className="h-9 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="button"
              disabled={submitting || selectedCount === 0}
              onClick={() => void onAccept([...selectedIds])}
              className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              纳入（{selectedCount}）
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
