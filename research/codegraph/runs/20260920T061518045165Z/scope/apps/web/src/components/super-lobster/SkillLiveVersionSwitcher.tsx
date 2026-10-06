"use client";

import { useLocale, useTranslations } from "next-intl";
import React from "react";
import type { SkillSubmissionVersionRecord } from "@/api";

type SkillLiveVersionSwitcherProps = {
  skillKey: string;
  items: SkillSubmissionVersionRecord[];
  pendingVersion?: number | null;
  pendingSourceVersion?: number | null;
  canRestore: boolean;
  restoringVersion: number | null;
  onRestore: (version: number) => void;
};

type VersionChip = {
  version: number;
  isLive: boolean;
  isPending: boolean;
  sourceVersion: number | null;
  approvedAt: string | null;
  createdAt: string | null;
};

function formatVersionDate(value: string | null, locale: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
  }).format(date);
}

function buildVersionChips(
  items: SkillSubmissionVersionRecord[],
  pendingVersion: number | null,
  pendingSourceVersion: number | null,
): VersionChip[] {
  const chips: VersionChip[] = items.map((item) => ({
    version: item.version,
    isLive: item.isLive,
    isPending: false,
    sourceVersion: item.sourceVersion,
    approvedAt: item.approvedAt,
    createdAt: item.createdAt,
  }));
  if (pendingVersion == null) return chips;

  const existing = chips.find((item) => item.version === pendingVersion);
  if (existing) {
    existing.isPending = true;
    return chips;
  }

  chips.unshift({
    version: pendingVersion,
    isLive: false,
    isPending: true,
    sourceVersion: pendingSourceVersion,
    approvedAt: null,
    createdAt: null,
  });
  return chips;
}

export function SkillLiveVersionSwitcher({
  skillKey,
  items,
  pendingVersion = null,
  pendingSourceVersion = null,
  canRestore,
  restoringVersion,
  onRestore,
}: SkillLiveVersionSwitcherProps) {
  const t = useTranslations("workspace.skillLibrary");
  const locale = useLocale();
  const chips = buildVersionChips(items, pendingVersion, pendingSourceVersion);
  const liveVersion = chips.find((item) => item.isLive)?.version ?? items[0]?.version ?? null;
  const [selectedVersion, setSelectedVersion] = React.useState<number | null>(liveVersion);

  React.useEffect(() => {
    setSelectedVersion(liveVersion);
  }, [skillKey, liveVersion]);

  if (items.length <= 1 && pendingVersion == null) return null;

  const selectedItem = chips.find((item) => item.version === selectedVersion) ?? chips[0];
  const selectedIsLive = Boolean(selectedItem?.isLive);
  const selectedIsPending = Boolean(selectedItem?.isPending);
  const showRestore = Boolean(selectedItem) && !selectedIsLive && !selectedIsPending && canRestore;
  const selectedDate = formatVersionDate(
    selectedItem?.approvedAt ?? selectedItem?.createdAt ?? null,
    locale,
  );
  const isRestoring = selectedItem != null && restoringVersion === selectedItem.version;
  const selectedMeta = selectedDate;

  return (
    <div className="mb-6">
      <div className="mb-2 text-[12px] font-medium text-muted-foreground">{t("liveVersion")}</div>
      <div className="flex items-center gap-2">
        <div
          role="radiogroup"
          aria-label={t("liveVersion")}
          className="no-scrollbar flex min-w-0 flex-1 items-center gap-1 overflow-x-auto"
        >
          {chips.map((item) => {
            const isSelected = item.version === selectedItem?.version;
            const pendingSelected = item.isPending && isSelected;
            return (
              <button
                key={`${item.isPending ? "pending" : "history"}-${item.version}`}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => setSelectedVersion(item.version)}
                className={`inline-flex h-8 shrink-0 items-center gap-1.5 rounded-full px-3 text-[13px] font-medium transition-colors duration-[160ms] motion-reduce:transition-none ${
                  item.isPending
                    ? pendingSelected
                      ? "border border-border bg-secondary text-foreground"
                      : "border border-dashed border-border text-muted-foreground hover:text-foreground"
                    : isSelected
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <span>{t("versionLabel", { version: item.version })}</span>
                {item.isPending ? (
                  <span className="text-[11px] font-normal">{t("versionInReview")}</span>
                ) : item.isLive ? (
                  <span
                    className={`text-[11px] font-normal ${isSelected ? "text-primary-foreground/80" : "text-muted-foreground"}`}
                  >
                    {t("versionInUse")}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
        {selectedMeta ? (
          <span className="shrink-0 text-[12px] text-muted-foreground">{selectedMeta}</span>
        ) : null}
      </div>

      <div
        className="grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none"
        style={{ gridTemplateRows: showRestore || selectedIsPending ? "1fr" : "0fr" }}
      >
        <div className="min-h-0 overflow-hidden">
          {selectedIsPending ? (
            <p className="pt-2 text-[12px] leading-relaxed text-muted-foreground">
              {pendingSourceVersion != null
                ? t("rollbackPendingHint", { version: selectedItem?.version ?? pendingVersion ?? "" })
                : t("pendingVersionHint", { version: selectedItem?.version ?? pendingVersion ?? "" })}
            </p>
          ) : (
            <div className="flex items-center justify-between gap-3 pt-2">
              <p className="min-w-0 text-[12px] leading-relaxed text-muted-foreground">
                {t("restoreThisVersionHint")}
              </p>
              <button
                type="button"
                disabled={isRestoring}
                onClick={() => {
                  if (!selectedItem) return;
                  onRestore(selectedItem.version);
                }}
                className="inline-flex h-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white px-3 text-[12px] font-medium text-foreground transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isRestoring ? t("submitting") : t("restoreThisVersion")}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
