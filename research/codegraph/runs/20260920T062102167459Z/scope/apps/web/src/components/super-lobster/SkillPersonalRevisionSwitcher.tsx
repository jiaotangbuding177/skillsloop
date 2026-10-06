"use client";

import { useLocale, useTranslations } from "next-intl";
import React from "react";
import type { PersonalSkillRevisionSummary } from "@/api";

type SkillPersonalRevisionSwitcherProps = {
  skillKey: string;
  items: PersonalSkillRevisionSummary[];
  restoringRevision: number | null;
  onRestore: (revision: number) => void;
  onSelect?: (revision: PersonalSkillRevisionSummary) => void;
};

function formatRevisionDate(value: string | null, locale: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function SkillPersonalRevisionSwitcher({
  skillKey,
  items,
  restoringRevision,
  onRestore,
  onSelect,
}: SkillPersonalRevisionSwitcherProps) {
  const t = useTranslations("workspace.skillLibrary");
  const locale = useLocale();
  const sorted = React.useMemo(
    () => [...items].sort((a, b) => b.revision - a.revision),
    [items],
  );
  const liveRevision = sorted.find((item) => item.isLive)?.revision ?? null;
  const [selectedRevision, setSelectedRevision] = React.useState<number | null>(
    liveRevision ?? sorted[0]?.revision ?? null,
  );

  React.useEffect(() => {
    setSelectedRevision(liveRevision ?? sorted[0]?.revision ?? null);
  }, [skillKey, liveRevision, sorted]);

  if (sorted.length === 0) return null;

  const selectedItem =
    sorted.find((item) => item.revision === selectedRevision) ?? sorted[0] ?? null;
  const selectedIsLive = Boolean(selectedItem?.isLive);
  const showRestore = Boolean(selectedItem) && !selectedIsLive;
  const selectedDate = formatRevisionDate(selectedItem?.createdAt ?? null, locale);
  const isRestoring =
    selectedItem != null && restoringRevision === selectedItem.revision;

  return (
    <div className="mb-6">
      <div className="mb-2 text-[12px] font-medium text-muted-foreground">
        {t("personalRevision")}
      </div>
      <div className="flex items-center gap-2">
        <div
          role="radiogroup"
          aria-label={t("personalRevision")}
          className="no-scrollbar flex min-w-0 flex-1 items-center gap-1 overflow-x-auto"
        >
          {sorted.map((item) => {
            const isSelected = item.revision === selectedItem?.revision;
            return (
              <button
                key={item.revision}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => {
                  setSelectedRevision(item.revision);
                  onSelect?.(item);
                }}
                className={`inline-flex h-8 shrink-0 items-center gap-1.5 rounded-full px-3 text-[13px] font-medium transition-colors duration-[160ms] motion-reduce:transition-none ${
                  isSelected
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <span>{t("revisionLabel", { revision: item.revision })}</span>
                {item.isLive ? (
                  <span
                    className={`text-[11px] font-normal ${
                      isSelected ? "text-primary-foreground/80" : "text-muted-foreground"
                    }`}
                  >
                    {t("revisionInUse")}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
        {selectedDate ? (
          <span className="shrink-0 text-[12px] text-muted-foreground">{selectedDate}</span>
        ) : null}
      </div>

      {selectedItem && !selectedIsLive ? (
        <div className="mt-2 rounded-lg border border-border/70 bg-secondary/40 px-3 py-2">
          <p className="text-[13px] font-medium text-foreground">{selectedItem.title}</p>
          {selectedItem.description ? (
            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
              {selectedItem.description}
            </p>
          ) : null}
        </div>
      ) : null}

      <div
        className="grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none"
        style={{ gridTemplateRows: showRestore ? "1fr" : "0fr" }}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="flex items-center justify-between gap-3 pt-2">
            <p className="min-w-0 text-[12px] leading-relaxed text-muted-foreground">
              {t("usePersonalRevisionHint")}
            </p>
            <button
              type="button"
              disabled={isRestoring}
              onClick={() => {
                if (!selectedItem) return;
                onRestore(selectedItem.revision);
              }}
              className="inline-flex h-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white px-3 text-[12px] font-medium text-foreground transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRestoring ? t("submitting") : t("usePersonalRevision")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
