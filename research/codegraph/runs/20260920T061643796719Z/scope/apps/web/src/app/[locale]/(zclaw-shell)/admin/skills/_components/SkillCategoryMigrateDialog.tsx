"use client";

import { useLocale, useTranslations } from "next-intl";
import React from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  listAdminEnterpriseSkillCategoriesApi,
  listAdminGlobalSkillCategoriesApi,
  listAdminGlobalSkillCategorySkillsApi,
  listAdminEnterpriseSkillCategorySkillsApi,
  listEnterpriseAdminSkillCategoriesApi,
  listEnterpriseAdminSkillCategorySkillsApi,
  migrateAdminGlobalSkillCategoryApi,
  migrateAdminEnterpriseSkillCategoryApi,
  migrateEnterpriseAdminSkillCategoryApi,
  type SkillCategoryRecord,
  type SkillCategorySkillRow,
} from "@/api";
import { filterMigrateTargetCategories } from "./skill-category-migrate.util";

const inputClassName =
  "h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20 disabled:cursor-not-allowed disabled:bg-[#fafafa] disabled:text-[#8c8c8c]";

const queryButtonClassName =
  "inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60";

const resetButtonClassName =
  "inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60";

const selectAllButtonClassName =
  "inline-flex h-7 cursor-pointer items-center rounded border border-[#d9d9d9] bg-white px-2.5 text-xs font-medium text-[#595959] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60";

function formatNumber(value: number | string | null | undefined, locale: string) {
  if (value == null || value === "") return "-";
  const parsed = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(parsed)) return "-";
  return new Intl.NumberFormat(locale).format(parsed);
}

type ConfirmRequest = (options: {
  title: string;
  description: string;
  confirmText: string;
  onConfirm: () => Promise<void>;
}) => void;

export type SkillCategoryMigrateScope = "global" | "enterprise";

type SkillCategoryMigrateDialogProps = {
  open: boolean;
  sourceCategory: SkillCategoryRecord | null;
  enterpriseId: string;
  viewScope: SkillCategoryMigrateScope;
  isPlatformAdmin: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmittingChange: (submitting: boolean) => void;
  onMigrated: () => Promise<void>;
  requestConfirm: ConfirmRequest;
};

function listCategorySkillsApi(
  viewScope: SkillCategoryMigrateScope,
  isPlatformAdmin: boolean,
  enterpriseId: string,
  categoryId: string,
) {
  if (viewScope === "global") {
    return listAdminGlobalSkillCategorySkillsApi(categoryId);
  }
  return isPlatformAdmin
    ? listAdminEnterpriseSkillCategorySkillsApi(enterpriseId, categoryId)
    : listEnterpriseAdminSkillCategorySkillsApi(enterpriseId, categoryId);
}

function listCategoriesApi(
  viewScope: SkillCategoryMigrateScope,
  isPlatformAdmin: boolean,
  enterpriseId: string,
) {
  if (viewScope === "global") {
    return listAdminGlobalSkillCategoriesApi().then((response) => response.items ?? []);
  }
  return (isPlatformAdmin
    ? listAdminEnterpriseSkillCategoriesApi(enterpriseId)
    : listEnterpriseAdminSkillCategoriesApi(enterpriseId)
  ).then((response) => [...(response.globalItems ?? []), ...(response.enterpriseItems ?? [])]);
}

function migrateCategoryApi(
  viewScope: SkillCategoryMigrateScope,
  isPlatformAdmin: boolean,
  enterpriseId: string,
  categoryId: string,
  data: { targetCategoryId: string; skillKeys: string[] },
) {
  if (viewScope === "global") {
    return migrateAdminGlobalSkillCategoryApi(categoryId, data);
  }
  return isPlatformAdmin
    ? migrateAdminEnterpriseSkillCategoryApi(enterpriseId, categoryId, data)
    : migrateEnterpriseAdminSkillCategoryApi(enterpriseId, categoryId, data);
}

export function SkillCategoryMigrateDialog({
  open,
  sourceCategory,
  enterpriseId,
  viewScope,
  isPlatformAdmin,
  submitting,
  onClose,
  onSubmittingChange,
  onMigrated,
  requestConfirm,
}: SkillCategoryMigrateDialogProps) {
  const locale = useLocale();
  const t = useTranslations("workspace.adminOrg.skillCategories");
  const tc = useTranslations("workspace.adminOrg.common");
  const [loading, setLoading] = React.useState(false);
  const [targetCategories, setTargetCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [sourceSkills, setSourceSkills] = React.useState<SkillCategorySkillRow[]>([]);
  const [selectedTargetCategoryId, setSelectedTargetCategoryId] = React.useState("");
  const [selectedSkillKeys, setSelectedSkillKeys] = React.useState<string[]>([]);

  React.useEffect(() => {
    if (!open || !sourceCategory) return;
    if (viewScope === "enterprise" && !enterpriseId) return;

    setLoading(true);
    setSelectedSkillKeys([]);

    void Promise.all([
      listCategoriesApi(viewScope, isPlatformAdmin, enterpriseId),
      listCategorySkillsApi(viewScope, isPlatformAdmin, enterpriseId, sourceCategory.id),
    ])
      .then(([categories, skillsResponse]) => {
        const candidates = filterMigrateTargetCategories(categories, sourceCategory.id);
        setTargetCategories(candidates);
        setSelectedTargetCategoryId(candidates[0]?.id ?? "");
        setSourceSkills(skillsResponse.items.filter((item) => item.editable));
      })
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : t("loadMigrateFailed"));
        setTargetCategories([]);
        setSourceSkills([]);
        setSelectedTargetCategoryId("");
      })
      .finally(() => setLoading(false));
  }, [open, sourceCategory, enterpriseId, viewScope, isPlatformAdmin, t]);

  if (!open || !sourceCategory) return null;

  const selectedTarget =
    targetCategories.find((category) => category.id === selectedTargetCategoryId) ?? null;
  const allSelected =
    sourceSkills.length > 0 && selectedSkillKeys.length === sourceSkills.length;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedSkillKeys([]);
      return;
    }
    setSelectedSkillKeys(sourceSkills.map((skill) => skill.skillKey));
  };

  const handleMigrate = () => {
    if (selectedSkillKeys.length === 0) {
      toast.error(t("selectSkillAtLeastOne"));
      return;
    }
    if (!selectedTargetCategoryId || !selectedTarget) {
      toast.error(t("selectTargetCategory"));
      return;
    }

    requestConfirm({
      title: t("migrateSkills"),
      description: t("migrateSkillsDescription", {
        source: sourceCategory.name,
        count: formatNumber(selectedSkillKeys.length, locale),
        target: selectedTarget.name,
      }),
      confirmText: tc("migrateAction"),
      onConfirm: async () => {
        onSubmittingChange(true);
        try {
          const result = await migrateCategoryApi(
            viewScope,
            isPlatformAdmin,
            enterpriseId,
            sourceCategory.id,
            {
              targetCategoryId: selectedTargetCategoryId,
              skillKeys: selectedSkillKeys,
            },
          );
          toast.success(t("migratedSkillCount", { count: formatNumber(result.movedCount, locale) }));
          onClose();
          await onMigrated();
        } catch (error) {
          toast.error(error instanceof Error ? error.message : t("migrateFailed"));
        } finally {
          onSubmittingChange(false);
        }
      },
    });
  };

  const selectedSkillsSummary = `${formatNumber(selectedSkillKeys.length, locale)} / ${t("skillCountUnit", { count: sourceSkills.length })}`;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 px-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-[#f0f0f0] bg-white shadow-xl">
        <div className="border-b border-[#f0f0f0] px-4 py-3 text-base font-semibold text-[#1f1f1f]">
          {t("migrateSkills")}
        </div>
        <div className="space-y-4 px-4 py-4">
          <div className="rounded border border-[#f0f0f0] bg-[#fafafa] px-3 py-2 text-sm text-[#595959]">
            <div>
              {t("sourceCategoryLabel")}
              <span className="font-medium text-[#333]">{sourceCategory.name}</span>
            </div>
            <div className="mt-1">
              {t("selectedSkillsLabel")}
              <span className="font-medium text-[#333]">{selectedSkillsSummary}</span>
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <label className="text-sm text-[#595959]">{t("selectSkills")}</label>
              <button
                type="button"
                className={selectAllButtonClassName}
                disabled={submitting || loading || sourceSkills.length === 0}
                onClick={handleSelectAll}
              >
                {allSelected ? tc("deselectAll") : tc("selectAllQuick")}
              </button>
            </div>
            <div className="max-h-56 overflow-y-auto rounded border border-[#f0f0f0]">
              {loading ? (
                <div className="flex items-center justify-center gap-2 px-3 py-10 text-sm text-[#8c8c8c]">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {tc("loading")}
                </div>
              ) : sourceSkills.length === 0 ? (
                <div className="px-3 py-10 text-center text-sm text-[#8c8c8c]">{t("noMigratableSkills")}</div>
              ) : (
                sourceSkills.map((skill) => {
                  const checked = selectedSkillKeys.includes(skill.skillKey);
                  return (
                    <label
                      key={skill.skillKey}
                      className="flex cursor-pointer items-start gap-2 border-b border-[#f0f0f0] px-3 py-2 last:border-b-0 hover:bg-[#fafafa]"
                    >
                      <input
                        type="checkbox"
                        className="mt-1 accent-[#1677ff]"
                        checked={checked}
                        disabled={submitting}
                        onChange={() => {
                          setSelectedSkillKeys((current) =>
                            checked
                              ? current.filter((key) => key !== skill.skillKey)
                              : [...current, skill.skillKey],
                          );
                        }}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm text-[#333]">{skill.title}</span>
                        <span className="mt-0.5 block text-xs text-[#8c8c8c]">{skill.skillKey}</span>
                      </span>
                    </label>
                  );
                })
              )}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm text-[#595959]">{t("selectTargetCategory")}</label>
            {loading ? (
              <div className="flex items-center gap-2 py-2 text-sm text-[#8c8c8c]">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t("loadingCategories")}
              </div>
            ) : targetCategories.length === 0 ? (
              <div className="rounded border border-[#f0f0f0] px-3 py-4 text-center text-sm text-[#8c8c8c]">
                {t("noTargetCategories")}
              </div>
            ) : (
              <select
                className={inputClassName}
                value={selectedTargetCategoryId}
                disabled={submitting}
                onChange={(event) => setSelectedTargetCategoryId(event.target.value)}
              >
                {targetCategories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {t("categoryOptionLabel", {
                      name: category.name,
                      count: formatNumber(category.skillCount ?? 0, locale),
                    })}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-[#f0f0f0] px-4 py-3">
          <button type="button" className={resetButtonClassName} disabled={submitting} onClick={onClose}>
            {tc("cancel")}
          </button>
          <button
            type="button"
            className={queryButtonClassName}
            disabled={
              submitting ||
              loading ||
              targetCategories.length === 0 ||
              sourceSkills.length === 0 ||
              selectedSkillKeys.length === 0
            }
            onClick={handleMigrate}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {tc("migrateAction")}
          </button>
        </div>
      </div>
    </div>
  );
}
