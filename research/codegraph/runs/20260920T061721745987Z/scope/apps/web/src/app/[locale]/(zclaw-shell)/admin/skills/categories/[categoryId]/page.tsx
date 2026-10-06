"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import type { Route } from "next";
import { useParams, useSearchParams } from "next/navigation";
import React from "react";
import { ArrowLeft, Loader2, Plus, RefreshCw, UserMinus } from "lucide-react";
import { toast } from "sonner";
import {
  listAdminGlobalSkillCategorySkillsApi,
  listAdminEnterpriseSkillCategorySkillsApi,
  listEnterpriseAdminSkillCategorySkillsApi,
  type SkillCategoryRecord,
  type SkillCategorySkillRow,
} from "@/api";
import { invalidateZclawSkillMarketCache } from "@/api/moudles/zclaw";
import { useSkillManagementAuth } from "@/hooks/useSkillManagementAuth";
import { isPlatformAdminUser } from "@/hooks/useScopedAdminAccess";
import { emitSkillMarketChanged } from "@/lib/enterprise-context";
import {
  ADMIN_PAGE_SIZE_OPTIONS,
  AdminTablePagination,
} from "../../../_components/AdminTablePagination";
import {
  SkillCategoryAddSkillsDialog,
  SkillCategoryMoveOutDialog,
  SkillCategoryRemoveSkillsDialog,
} from "../../_components/SkillCategoryManageDialogs";
import type { SkillCategoryMigrateScope } from "../../_components/SkillCategoryMigrateDialog";

const addButtonClassName =
  "inline-flex h-8 cursor-pointer items-center justify-center gap-1 rounded border border-[#1677ff] bg-[#1677ff] px-3 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60";

const resetButtonClassName =
  "inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60";

const removeButtonClassName =
  "inline-flex h-8 cursor-pointer items-center justify-center gap-1 rounded border border-[#ff4d4f] bg-white px-3 text-sm font-medium text-[#ff4d4f] transition-colors hover:bg-[#fff1f0] hover:border-[#ff7875] hover:text-[#ff7875] disabled:cursor-not-allowed disabled:opacity-60";

const actionDangerLinkClassName =
  "cursor-pointer text-sm text-[#ff4d4f] hover:text-[#ff7875] disabled:cursor-not-allowed disabled:opacity-50";

function notifySkillMarketChanged() {
  invalidateZclawSkillMarketCache();
  emitSkillMarketChanged();
}

function formatNumber(value: number | string | null | undefined) {
  if (value == null || value === "") return "-";
  const parsed = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(parsed)) return "-";
  return new Intl.NumberFormat("zh-CN").format(parsed);
}

function resolveViewScope(searchParams: URLSearchParams): SkillCategoryMigrateScope {
  const scope = searchParams.get("scope")?.trim();
  return scope === "global" ? "global" : "enterprise";
}

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

function resolveSkillSourceLabel(
  source: string,
  t: ReturnType<typeof useTranslations<"workspace.adminOrg.skillCategories">>,
) {
  if (source === "code") return t("sourceCode");
  if (source === "km") return t("sourceKm");
  if (source === "global") return t("sourceGlobal");
  if (source === "enterprise_override") return t("sourceEnterpriseOverride");
  if (source === "enterprise_custom") return t("sourceEnterpriseCustom");
  return source;
}

function isCategoryEditable(
  category: SkillCategoryRecord | null,
  viewScope: SkillCategoryMigrateScope,
) {
  if (!category) return false;
  if (viewScope === "global") return true;
  return category.scope === "enterprise";
}

export default function SkillCategoryDetailPage() {
  const t = useTranslations("workspace.adminOrg.skillCategories");
  const tc = useTranslations("workspace.adminOrg.common");
  const params = useParams<{ categoryId: string }>();
  const searchParams = useSearchParams();
  const categoryId = params.categoryId?.trim() ?? "";
  const enterpriseId = searchParams.get("enterpriseId")?.trim() ?? "";
  const viewScope = resolveViewScope(searchParams);
  const authState = useSkillManagementAuth();
  const isPlatformAdmin = isPlatformAdminUser();

  const [category, setCategory] = React.useState<SkillCategoryRecord | null>(null);
  const [items, setItems] = React.useState<SkillCategorySkillRow[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState<number>(ADMIN_PAGE_SIZE_OPTIONS[0]);
  const [addSkillsOpen, setAddSkillsOpen] = React.useState(false);
  const [removeSkillsOpen, setRemoveSkillsOpen] = React.useState(false);
  const [moveOutSkill, setMoveOutSkill] = React.useState<SkillCategorySkillRow | null>(null);

  const listHref = (
    `/admin/skills/categories${
      enterpriseId ? `?enterpriseId=${encodeURIComponent(enterpriseId)}` : viewScope === "global" ? "?scope=global" : ""
    }` as Route
  );

  const loadDetail = React.useCallback(async () => {
    if (!categoryId) return;
    if (viewScope === "enterprise" && !enterpriseId) return;

    setLoading(true);
    try {
      const response = await listCategorySkillsApi(
        viewScope,
        isPlatformAdmin,
        enterpriseId,
        categoryId,
      );
      setCategory(response.category);
      setItems(response.items);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("loadCategorySkillsFailed"));
      setCategory(null);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [categoryId, enterpriseId, isPlatformAdmin, t, viewScope]);

  React.useEffect(() => {
    if (authState !== "authorized") return;
    void loadDetail();
  }, [authState, loadDetail]);

  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const paginatedItems = React.useMemo(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * pageSize;
    return items.slice(start, start + pageSize);
  }, [items, page, pageSize, totalPages]);

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const editable = isCategoryEditable(category, viewScope);

  const handleRemoveSkill = (skill: SkillCategorySkillRow) => {
    if (!category || !skill.editable) return;
    setMoveOutSkill(skill);
  };

  const handleSaved = async () => {
    notifySkillMarketChanged();
    await loadDetail();
  };

  if (authState !== "authorized") {
    return (
      <main className="flex min-h-full w-full items-center justify-center bg-white px-5 py-8">
        <div className="text-sm text-[#8c8c8c]">{tc("checkingPermission")}</div>
      </main>
    );
  }

  if (viewScope === "enterprise" && !enterpriseId && !isPlatformAdmin) {
    return (
      <main className="flex min-h-full w-full items-center justify-center bg-white px-5 py-8">
        <div className="text-sm text-[#8c8c8c]">{tc("noManagedOrganizationForSkillCategories")}</div>
      </main>
    );
  }

  return (
    <main className="min-h-full w-full min-w-0 bg-white px-5 py-4">
      <div className="mb-4">
        <Link href={listHref} className="inline-flex items-center gap-1 text-sm text-[#1677ff] hover:text-[#4096ff]">
          <ArrowLeft className="h-4 w-4" />
          {t("backToCategoryList")}
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 py-12 text-sm text-[#8c8c8c]">
          <Loader2 className="h-4 w-4 animate-spin" />
          {tc("loading")}
        </div>
      ) : !category ? (
        <div className="py-12 text-center text-sm text-[#8c8c8c]">{t("categoryNotFound")}</div>
      ) : (
        <>
          <section className="rounded border border-[#f0f0f0] bg-white px-4 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold text-[#1f1f1f]">{category.name}</h1>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-[#595959]">
                  <span>{t("sortOrderLabel", { order: category.sortOrder })}</span>
                  <span className="text-[#e8e8e8]">|</span>
                  <span>
                    {category.source === "system" ? t("sourceSystem") : t("sourceCustom")}
                  </span>
                  <span className="text-[#e8e8e8]">|</span>
                  <span>{t("skillCountUnit", { count: formatNumber(category.skillCount ?? items.length) })}</span>
                </div>
              </div>
              <button
                type="button"
                className={resetButtonClassName}
                disabled={submitting}
                onClick={() => void loadDetail()}
              >
                <RefreshCw className="h-4 w-4" />
                {tc("refresh")}
              </button>
            </div>
          </section>

          <section className="mt-4 overflow-hidden rounded border border-[#f0f0f0] bg-white">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0f0f0] px-4 py-3">
              <h2 className="text-base font-semibold text-[#1f1f1f]">
                {t("categorySkillsTitle", { count: formatNumber(items.length) })}
              </h2>
              {editable ? (
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    className={addButtonClassName}
                    disabled={submitting}
                    onClick={() => setAddSkillsOpen(true)}
                  >
                    <Plus className="h-4 w-4" />
                    {t("addSkills")}
                  </button>
                  <button
                    type="button"
                    className={removeButtonClassName}
                    disabled={submitting}
                    onClick={() => setRemoveSkillsOpen(true)}
                  >
                    <UserMinus className="h-4 w-4" />
                    {t("removeSkills")}
                  </button>
                </div>
              ) : null}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-[#f0f0f0] bg-[#fafafa] text-left text-[#595959]">
                    <th className="px-4 py-3 font-medium">{t("skillTitle")}</th>
                    <th className="px-4 py-3 font-medium">{t("skillKey")}</th>
                    <th className="px-4 py-3 font-medium">{t("source")}</th>
                    <th className="px-4 py-3 font-medium">{t("sortOrder")}</th>
                    <th className="px-4 py-3 font-medium">{t("visible")}</th>
                    <th className="px-4 py-3 font-medium">{t("hot")}</th>
                    {editable ? <th className="px-4 py-3 font-medium">{tc("actions")}</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {paginatedItems.length === 0 ? (
                    <tr>
                      <td colSpan={editable ? 7 : 6} className="px-4 py-12 text-center text-[#8c8c8c]">
                        {t("noSkillsInCategory")}
                      </td>
                    </tr>
                  ) : (
                    paginatedItems.map((skill) => (
                      <tr key={skill.skillKey} className="border-b border-[#f0f0f0] hover:bg-[#fafafa]">
                        <td className="px-4 py-3 text-[#333]">{skill.title}</td>
                        <td className="px-4 py-3 text-[#595959]">{skill.skillKey}</td>
                        <td className="px-4 py-3 text-[#595959]">{resolveSkillSourceLabel(skill.source, t)}</td>
                        <td className="px-4 py-3 text-[#595959]">{skill.sortOrder}</td>
                        <td className="px-4 py-3 text-[#595959]">{skill.isVisible ? tc("enabled") : tc("disabled")}</td>
                        <td className="px-4 py-3 text-[#595959]">{skill.isHot ? tc("enabled") : tc("disabled")}</td>
                        {editable ? (
                          <td className="px-4 py-3">
                            {skill.editable ? (
                              <button
                                type="button"
                                className={actionDangerLinkClassName}
                                disabled={submitting}
                                onClick={() => handleRemoveSkill(skill)}
                              >
                                {t("removeFromCategory")}
                              </button>
                            ) : (
                              <span className="text-[#bfbfbf]">—</span>
                            )}
                          </td>
                        ) : null}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {items.length > 0 ? (
              <AdminTablePagination
                total={items.length}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
              />
            ) : null}
          </section>
        </>
      )}

      <SkillCategoryAddSkillsDialog
        open={addSkillsOpen}
        category={category}
        enterpriseId={enterpriseId}
        viewScope={viewScope}
        isPlatformAdmin={isPlatformAdmin}
        submitting={submitting}
        onClose={() => setAddSkillsOpen(false)}
        onSubmittingChange={setSubmitting}
        onSaved={handleSaved}
      />

      <SkillCategoryRemoveSkillsDialog
        open={removeSkillsOpen}
        category={category}
        enterpriseId={enterpriseId}
        viewScope={viewScope}
        isPlatformAdmin={isPlatformAdmin}
        submitting={submitting}
        onClose={() => setRemoveSkillsOpen(false)}
        onSubmittingChange={setSubmitting}
        onSaved={handleSaved}
      />

      <SkillCategoryMoveOutDialog
        open={Boolean(moveOutSkill)}
        skill={moveOutSkill}
        category={category}
        enterpriseId={enterpriseId}
        viewScope={viewScope}
        isPlatformAdmin={isPlatformAdmin}
        submitting={submitting}
        onClose={() => setMoveOutSkill(null)}
        onSubmittingChange={setSubmitting}
        onSaved={handleSaved}
      />
    </main>
  );
}
