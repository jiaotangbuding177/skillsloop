"use client";

import { useTranslations } from "next-intl";
import React from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";
import {
  listAdminAvailableSkillsApi,
  listAdminEnterpriseSkillCategoriesApi,
  listAdminGlobalSkillCategoriesApi,
  listAdminGlobalSkillsApi,
  listAdminGlobalSkillCategorySkillsApi,
  listAdminEnterpriseSkillCategorySkillsApi,
  listEnterpriseAdminSkillCategoriesApi,
  listEnterpriseAdminSkillCategorySkillsApi,
  moveAdminGlobalSkillCategorySkillsApi,
  moveAdminEnterpriseSkillCategorySkillsApi,
  moveEnterpriseAdminSkillCategorySkillsApi,
  type SkillCategoryRecord,
  type SkillCategorySkillRow,
} from "@/api";
import {
  buildKmInstalledPoolItems,
  loadEnterpriseAdminSkillRows,
} from "@/lib/enterprise-skill-picker";
import { mergeGlobalAdminSkillRows } from "@/lib/skill-admin-merge";
import type { SkillCategoryMigrateScope } from "./SkillCategoryMigrateDialog";
import {
  ADD_SKILL_ALL_CATEGORIES_FILTER,
  ADD_SKILL_UNCATEGORIZED_FILTER,
  buildAddSkillCategoryFilterOptions,
  filterAddSkillCandidates,
  filterAddSkillCandidatesByToolbar,
  type AddSkillCandidateRow,
} from "./skill-category-add-candidates.util";
import { filterMigrateTargetCategories } from "./skill-category-migrate.util";

const inputClassName =
  "h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20 disabled:cursor-not-allowed disabled:bg-[#fafafa] disabled:text-[#8c8c8c]";

const queryButtonClassName =
  "inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60";

const resetButtonClassName =
  "inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60";

const selectAllButtonClassName =
  "inline-flex h-7 shrink-0 cursor-pointer items-center rounded border border-[#d9d9d9] bg-white px-2.5 text-xs font-medium text-[#595959] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60";

type SkillCandidate = AddSkillCandidateRow;

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

function moveSkillsApi(
  viewScope: SkillCategoryMigrateScope,
  isPlatformAdmin: boolean,
  enterpriseId: string,
  categoryId: string,
  data: { skillKeys: string[]; targetCategoryId?: string | null },
) {
  if (viewScope === "global") {
    return moveAdminGlobalSkillCategorySkillsApi(categoryId, data);
  }
  return isPlatformAdmin
    ? moveAdminEnterpriseSkillCategorySkillsApi(enterpriseId, categoryId, data)
    : moveEnterpriseAdminSkillCategorySkillsApi(enterpriseId, categoryId, data);
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

async function loadAddSkillCandidates(input: {
  viewScope: SkillCategoryMigrateScope;
  isPlatformAdmin: boolean;
  enterpriseId: string;
  category: SkillCategoryRecord;
}): Promise<SkillCandidate[]> {
  const { viewScope, isPlatformAdmin, enterpriseId, category } = input;

  if (viewScope === "global") {
    const [availableResponse, skillsResponse, categoriesResponse] = await Promise.all([
      listAdminAvailableSkillsApi({ purpose: "global", includeConfigured: true }),
      listAdminGlobalSkillsApi(),
      listAdminGlobalSkillCategoriesApi(),
    ]);
    const rows = mergeGlobalAdminSkillRows(
      skillsResponse.items ?? [],
      categoriesResponse.items ?? [],
      buildKmInstalledPoolItems(availableResponse.items ?? []),
    );
    return filterAddSkillCandidates(
      rows
        .filter((item) => item.isVisible)
        .map((item) => ({
          skillKey: item.skillKey,
          title: item.title,
          categoryId: item.categoryId,
          categoryName: item.categoryName || "-",
          editable: true,
        })),
      category,
    );
  }

  const rows = await loadEnterpriseAdminSkillRows(enterpriseId, isPlatformAdmin);
  return filterAddSkillCandidates(
    rows
      .filter((item) => item.isVisible)
      .map((item) => ({
        skillKey: item.skillKey,
        title: item.title,
        categoryId: item.categoryId,
        categoryName: item.categoryName || "-",
        editable: true,
      })),
    category,
  );
}

export function SkillCategoryAddSkillsDialog({
  open,
  category,
  enterpriseId,
  viewScope,
  isPlatformAdmin,
  submitting,
  onClose,
  onSubmittingChange,
  onSaved,
}: {
  open: boolean;
  category: SkillCategoryRecord | null;
  enterpriseId: string;
  viewScope: SkillCategoryMigrateScope;
  isPlatformAdmin: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmittingChange: (submitting: boolean) => void;
  onSaved: () => Promise<void>;
}) {
  const t = useTranslations("workspace.adminOrg.skillCategories");
  const tc = useTranslations("workspace.adminOrg.common");
  const [loading, setLoading] = React.useState(false);
  const [keyword, setKeyword] = React.useState("");
  const [categoryFilter, setCategoryFilter] = React.useState(ADD_SKILL_ALL_CATEGORIES_FILTER);
  const [candidates, setCandidates] = React.useState<SkillCandidate[]>([]);
  const [selectedSkillKeys, setSelectedSkillKeys] = React.useState<string[]>([]);

  React.useEffect(() => {
    if (!open || !category) return;
    if (viewScope === "enterprise" && !enterpriseId) return;

    setKeyword("");
    setCategoryFilter(ADD_SKILL_ALL_CATEGORIES_FILTER);
    setSelectedSkillKeys([]);
    setLoading(true);
    void loadAddSkillCandidates({ viewScope, isPlatformAdmin, enterpriseId, category })
      .then(setCandidates)
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : t("loadAddCandidatesFailed"));
        setCandidates([]);
      })
      .finally(() => setLoading(false));
  }, [open, category, enterpriseId, viewScope, isPlatformAdmin, t]);

  if (!open || !category) return null;

  const categoryFilterOptions = buildAddSkillCategoryFilterOptions(candidates);
  const filteredCandidates = filterAddSkillCandidatesByToolbar(candidates, {
    categoryFilter,
    keyword,
  });
  const selectableKeys = filteredCandidates
    .filter((skill) => skill.editable)
    .map((skill) => skill.skillKey);
  const allSelected =
    selectableKeys.length > 0 && selectableKeys.every((key) => selectedSkillKeys.includes(key));

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedSkillKeys((current) => current.filter((key) => !selectableKeys.includes(key)));
      return;
    }
    setSelectedSkillKeys((current) => Array.from(new Set([...current, ...selectableKeys])));
  };

  const handleSave = async () => {
    if (selectedSkillKeys.length === 0) {
      toast.error(t("selectSkillAtLeastOne"));
      return;
    }
    onSubmittingChange(true);
    try {
      await moveSkillsApi(viewScope, isPlatformAdmin, enterpriseId, category.id, {
        skillKeys: selectedSkillKeys,
      });
      await onSaved();
      toast.success(t("addedSkillsCount", { count: selectedSkillKeys.length }));
      onClose();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("addSkillsFailed"));
    } finally {
      onSubmittingChange(false);
    }
  };

  const displayCategoryName = (name: string) =>
    name === "-" || !name.trim() ? t("uncategorized") : name;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 px-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-[#f0f0f0] bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-[#f0f0f0] px-4 py-3">
          <h3 className="text-base font-semibold text-[#1f1f1f]">{t("addSkillsTitle", { name: category.name })}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-[#8c8c8c] hover:bg-[#f5f5f5] hover:text-[#333]"
            aria-label={tc("close")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 px-4 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex min-w-0 flex-1 items-center gap-2 text-sm text-[#595959]">
              <span className="shrink-0">{t("filterByCategory")}</span>
              <select
                className={`${inputClassName} max-w-full flex-1`}
                value={categoryFilter}
                disabled={submitting || loading}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value={ADD_SKILL_ALL_CATEGORIES_FILTER}>{t("allCategories")}</option>
                {categoryFilterOptions.categoryNames.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
                {categoryFilterOptions.hasUncategorized ? (
                  <option value={ADD_SKILL_UNCATEGORIZED_FILTER}>{t("uncategorized")}</option>
                ) : null}
              </select>
            </label>
            <button
              type="button"
              className={selectAllButtonClassName}
              disabled={submitting || loading || selectableKeys.length === 0}
              onClick={handleSelectAll}
            >
              {allSelected ? tc("deselectAll") : tc("selectAllQuick")}
            </button>
          </div>
          <input
            className={inputClassName}
            value={keyword}
            disabled={submitting}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder={t("searchSkillKeyword")}
          />
          <div className="max-h-72 overflow-y-auto rounded border border-[#f0f0f0]">
            {loading ? (
              <div className="flex items-center justify-center gap-2 px-3 py-10 text-sm text-[#8c8c8c]">
                <Loader2 className="h-4 w-4 animate-spin" />
                {tc("loading")}
              </div>
            ) : filteredCandidates.length === 0 ? (
              <div className="px-3 py-10 text-center text-sm text-[#8c8c8c]">{t("noSkillsToAdd")}</div>
            ) : (
              filteredCandidates.map((skill) => {
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
                      disabled={submitting || !skill.editable}
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
                      <span className="mt-0.5 block text-xs text-[#8c8c8c]">
                        {skill.skillKey} ·{" "}
                        {t("currentCategoryLabel", { name: displayCategoryName(skill.categoryName) })}
                      </span>
                    </span>
                  </label>
                );
              })
            )}
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-[#f0f0f0] px-4 py-3">
          <button type="button" className={resetButtonClassName} disabled={submitting} onClick={onClose}>
            {tc("cancel")}
          </button>
          <button type="button" className={queryButtonClassName} disabled={submitting} onClick={() => void handleSave()}>
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {tc("confirm")}
          </button>
        </div>
      </div>
    </div>
  );
}

export function SkillCategoryRemoveSkillsDialog({
  open,
  category,
  enterpriseId,
  viewScope,
  isPlatformAdmin,
  submitting,
  onClose,
  onSubmittingChange,
  onSaved,
}: {
  open: boolean;
  category: SkillCategoryRecord | null;
  enterpriseId: string;
  viewScope: SkillCategoryMigrateScope;
  isPlatformAdmin: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmittingChange: (submitting: boolean) => void;
  onSaved: () => Promise<void>;
}) {
  const t = useTranslations("workspace.adminOrg.skillCategories");
  const tc = useTranslations("workspace.adminOrg.common");
  const [loading, setLoading] = React.useState(false);
  const [keyword, setKeyword] = React.useState("");
  const [skills, setSkills] = React.useState<SkillCategorySkillRow[]>([]);
  const [targetCategories, setTargetCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [selectedTargetCategoryId, setSelectedTargetCategoryId] = React.useState("");
  const [selectedSkillKeys, setSelectedSkillKeys] = React.useState<string[]>([]);

  React.useEffect(() => {
    if (!open || !category) return;
    if (viewScope === "enterprise" && !enterpriseId) return;

    setKeyword("");
    setSelectedSkillKeys([]);
    setSelectedTargetCategoryId("");
    setLoading(true);
    void Promise.all([
      listCategorySkillsApi(viewScope, isPlatformAdmin, enterpriseId, category.id),
      listCategoriesApi(viewScope, isPlatformAdmin, enterpriseId),
    ])
      .then(([skillsResponse, categories]) => {
        setSkills(skillsResponse.items.filter((item) => item.editable));
        const targets = filterMigrateTargetCategories(categories, category.id);
        setTargetCategories(targets);
        setSelectedTargetCategoryId(targets[0]?.id ?? "");
      })
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : t("loadCategorySkillsFailed"));
        setSkills([]);
        setTargetCategories([]);
        setSelectedTargetCategoryId("");
      })
      .finally(() => setLoading(false));
  }, [open, category, enterpriseId, viewScope, isPlatformAdmin, t]);

  if (!open || !category) return null;

  const filteredSkills = skills.filter((skill) => {
    const keywordText = keyword.trim().toLowerCase();
    if (!keywordText) return true;
    const haystack = [skill.title, skill.skillKey].join(" ").toLowerCase();
    return haystack.includes(keywordText);
  });

  const selectedTarget =
    targetCategories.find((item) => item.id === selectedTargetCategoryId) ?? null;

  const handleSave = async () => {
    if (selectedSkillKeys.length === 0) {
      toast.error(t("selectSkillAtLeastOne"));
      return;
    }
    if (!selectedTargetCategoryId || !selectedTarget) {
      toast.error(t("selectTargetCategory"));
      return;
    }
    onSubmittingChange(true);
    try {
      await moveSkillsApi(viewScope, isPlatformAdmin, enterpriseId, category.id, {
        skillKeys: selectedSkillKeys,
        targetCategoryId: selectedTargetCategoryId,
      });
      await onSaved();
      toast.success(
        t("batchMovedToCategory", {
          count: selectedSkillKeys.length,
          target: selectedTarget.name,
        }),
      );
      onClose();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("removeSkillsFailed"));
    } finally {
      onSubmittingChange(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 px-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-[#f0f0f0] bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-[#f0f0f0] px-4 py-3">
          <h3 className="text-base font-semibold text-[#1f1f1f]">
            {t("removeSkillsTitle", { name: category.name })}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-[#8c8c8c] hover:bg-[#f5f5f5] hover:text-[#333]"
            aria-label={tc("close")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 px-4 py-4">
          <input
            className={inputClassName}
            value={keyword}
            disabled={submitting}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder={t("searchSkillKeyword")}
          />
          <div className="max-h-72 overflow-y-auto rounded border border-[#f0f0f0]">
            {loading ? (
              <div className="flex items-center justify-center gap-2 px-3 py-10 text-sm text-[#8c8c8c]">
                <Loader2 className="h-4 w-4 animate-spin" />
                {tc("loading")}
              </div>
            ) : filteredSkills.length === 0 ? (
              <div className="px-3 py-10 text-center text-sm text-[#8c8c8c]">{t("noSkillsToRemove")}</div>
            ) : (
              filteredSkills.map((skill) => {
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
                {targetCategories.map((item) => (
                  <option key={item.id} value={item.id}>
                    {t("categoryOptionLabel", {
                      name: item.name,
                      count: item.skillCount ?? 0,
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
              selectedSkillKeys.length === 0 ||
              !selectedTargetCategoryId
            }
            onClick={() => void handleSave()}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {t("confirmRemoveFromCategory")}
          </button>
        </div>
      </div>
    </div>
  );
}

export function SkillCategoryMoveOutDialog({
  open,
  skill,
  category,
  enterpriseId,
  viewScope,
  isPlatformAdmin,
  submitting,
  onClose,
  onSubmittingChange,
  onSaved,
}: {
  open: boolean;
  skill: SkillCategorySkillRow | null;
  category: SkillCategoryRecord | null;
  enterpriseId: string;
  viewScope: SkillCategoryMigrateScope;
  isPlatformAdmin: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmittingChange: (submitting: boolean) => void;
  onSaved: () => Promise<void>;
}) {
  const t = useTranslations("workspace.adminOrg.skillCategories");
  const tc = useTranslations("workspace.adminOrg.common");
  const [loading, setLoading] = React.useState(false);
  const [targetCategories, setTargetCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [selectedTargetCategoryId, setSelectedTargetCategoryId] = React.useState("");

  React.useEffect(() => {
    if (!open || !category || !skill) return;
    if (viewScope === "enterprise" && !enterpriseId) return;

    setSelectedTargetCategoryId("");
    setLoading(true);
    void listCategoriesApi(viewScope, isPlatformAdmin, enterpriseId)
      .then((categories) => {
        const targets = filterMigrateTargetCategories(categories, category.id);
        setTargetCategories(targets);
        setSelectedTargetCategoryId(targets[0]?.id ?? "");
      })
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : t("loadMigrateFailed"));
        setTargetCategories([]);
        setSelectedTargetCategoryId("");
      })
      .finally(() => setLoading(false));
  }, [open, category, skill, enterpriseId, viewScope, isPlatformAdmin, t]);

  if (!open || !category || !skill) return null;

  const selectedTarget =
    targetCategories.find((item) => item.id === selectedTargetCategoryId) ?? null;

  const handleSave = async () => {
    if (!selectedTargetCategoryId || !selectedTarget) {
      toast.error(t("selectTargetCategory"));
      return;
    }
    onSubmittingChange(true);
    try {
      await moveSkillsApi(viewScope, isPlatformAdmin, enterpriseId, category.id, {
        skillKeys: [skill.skillKey],
        targetCategoryId: selectedTargetCategoryId,
      });
      await onSaved();
      toast.success(t("movedToCategory", { target: selectedTarget.name }));
      onClose();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("removeSkillsFailed"));
    } finally {
      onSubmittingChange(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/35 px-4">
      <div className="w-full max-w-md overflow-y-auto rounded-lg border border-[#f0f0f0] bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-[#f0f0f0] px-4 py-3">
          <h3 className="text-base font-semibold text-[#1f1f1f]">{t("moveOutToCategory")}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-[#8c8c8c] hover:bg-[#f5f5f5] hover:text-[#333]"
            aria-label={tc("close")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 px-4 py-4">
          <div className="rounded border border-[#f0f0f0] bg-[#fafafa] px-3 py-2 text-sm text-[#595959]">
            <div className="font-medium text-[#333]">{skill.title}</div>
            <div className="mt-0.5 text-xs text-[#8c8c8c]">{skill.skillKey}</div>
            <div className="mt-1 text-xs">
              {t("sourceCategoryLabel")}
              <span className="font-medium text-[#333]">{category.name}</span>
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
                {targetCategories.map((item) => (
                  <option key={item.id} value={item.id}>
                    {t("categoryOptionLabel", {
                      name: item.name,
                      count: item.skillCount ?? 0,
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
              submitting || loading || targetCategories.length === 0 || !selectedTargetCategoryId
            }
            onClick={() => void handleSave()}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {t("confirmRemoveFromCategory")}
          </button>
        </div>
      </div>
    </div>
  );
}
