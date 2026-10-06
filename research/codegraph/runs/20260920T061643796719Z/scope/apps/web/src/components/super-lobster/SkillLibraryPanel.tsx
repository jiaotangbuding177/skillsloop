"use client";


import { useTranslations } from "next-intl";
import React from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowLeft,
  Briefcase,
  Calculator,
  Flame,
  LayoutGrid,
  Plus,
  Radar,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  User,
  UserPlus,
  UserRound,
  X,
  type LucideIcon,
} from "lucide-react";
import type { Route } from "next";
import { Link } from "@/i18n/navigation";
import { toast } from "sonner"
import { emitError, errorToast } from '@/lib/error-handler';
import { resolveSkillIcon } from "@/lib/skillIconCatalog";
import {
  getSkillSubmissionChangesApi,
  listMySkillSubmissionsApi,
  listPersonalSkillRevisionsApi,
  listSkillVersionsApi,
  listZclawSkillMarketApi,
  resubmitSkillVersionApi,
  restorePersonalSkillRevisionApi,
  savePersonalSkillConfigApi,
  submitSkillForReviewApi,
  type PersonalSkillRevisionSummary,
  type SkillSubmissionRecord,
  type SkillSubmissionVersionRecord,
  type ZclawSkillMarketCategory,
  type ZclawSkillMarketItem,
} from "@/api";
import {
  buildMarketRecommendedSkillViews,
  findMatchingMarketItem,
  getMarketSkillDisplayItem,
  resolveConversationSkillKey,
  resolveRecommendedSkillPrefillText,
  resolveMarketSkillContent,
  type SkillCategoryKey,
} from "./skillDisplay";
import {
  ACTIVE_ENTERPRISE_CHANGED_EVENT,
  SKILL_MARKET_CHANGED_EVENT,
  getActiveEnterpriseId,
} from "@/lib/enterprise-context";
import {
  canSubmitSkillSubmission,
  isRollbackPending,
  isVersionUpdatePending,
  resolvePendingReviewDisplayVersion,
  resolvePublishedVersion,
} from "./skill-submission-display";
import { SkillLiveVersionSwitcher } from "./SkillLiveVersionSwitcher";
import { SkillPersonalRevisionSwitcher } from "./SkillPersonalRevisionSwitcher";
import {
  type WorkbenchRoleCategory,
} from "@/lib/workbenchRoleCategories";
import { SkillIconFieldGroup } from "@/app/[locale]/(zclaw-shell)/admin/skills/_components/SkillIconFieldGroup";

type PersonalEditFormState = {
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string;
  colorClassName: string;
};

interface SkillLibraryPanelProps {
  onClose: () => void;
  onInsert: (skill: {
    id: string;
    name: string;
    displayName: string;
    prompt: string;
    prefillText?: string;
    scope?: ZclawSkillMarketItem["scope"];
    source?: ZclawSkillMarketItem["source"];
  }) => void;
  onCreateSkillInstall: () => void;
}

type MarketCategoryKey = "personal" | "recommended" | SkillCategoryKey;

type MarketSkill = {
  id: string;
  slug: string;
  skillKey: string;
  title: string;
  description: string;
  categoryKey: MarketCategoryKey;
  categoryTitle: string;
  icon: string;
  colorClassName: string;
  sortOrder: number;
  isRecommended?: boolean;
  hot?: boolean;
  entryCopy: string;
  targetUsers: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  reason: string;
  prompt: string;
  scope: ZclawSkillMarketItem["scope"];
  source: ZclawSkillMarketItem["source"];
  reliabilityReport?: ZclawSkillMarketItem["reliabilityReport"];
};

function compareMarketSkillsByOrder(left: MarketSkill, right: MarketSkill) {
  return (
    left.sortOrder - right.sortOrder ||
    left.title.localeCompare(right.title, "zh-CN") ||
    left.slug.localeCompare(right.slug, "zh-CN")
  );
}

function resolveSkillPrefillText(skill: Pick<MarketSkill, "prefillTemplate" | "exampleInput">) {
  return resolveRecommendedSkillPrefillText(skill);
}

type MarketCategory = {
  key: MarketCategoryKey;
  title: string;
  icon?: string | null;
  colorClassName?: string | null;
};

const roleCategoryIconComponents: Record<WorkbenchRoleCategory, LucideIcon> = {
  运营: Briefcase,
  人力资源: UserPlus,
  财务: Calculator,
  法务: ShieldAlert,
  销售: TrendingUp,
  市场: Radar,
  通用: Sparkles,
};

const categoryIconMap: Record<string, LucideIcon> = {
  personal: UserRound,
  recommended: Flame,
  ...roleCategoryIconComponents,
};

function renderCategoryNavIcon(category: MarketCategory, isActive: boolean) {
  if (category.icon?.trim()) {
    const CustomIcon = resolveSkillIcon(category.icon);
    const styleClassName =
      category.colorClassName?.trim() ||
      (isActive ? "text-blue-500" : "text-gray-400");
    return (
      <span
        className={`inline-flex size-[22px] items-center justify-center rounded-md border border-transparent ${styleClassName}`}
      >
        <CustomIcon className="size-[15px]" />
      </span>
    );
  }

  const FallbackIcon = categoryIconMap[category.key] || LayoutGrid;
  return <FallbackIcon className={isActive ? "size-[15px] text-primary" : "size-[15px]"} />;
}

function toApiMarketSkill(
  skill: ZclawSkillMarketItem,
  index: number,
  t: ReturnType<typeof useTranslations<'workspace.skillLibrary'>>,
  tWorkbench: ReturnType<typeof useTranslations<'workspace.workbench'>>,
): MarketSkill {
  const item = getMarketSkillDisplayItem(skill, index);
  const content = resolveMarketSkillContent(skill);

  return {
    id: skill.id,
    slug: skill.name || skill.id,
    skillKey: skill.skillKey || skill.id,
    title: content.title,
    description: content.description || tWorkbench('noDescription'),
    categoryKey: skill.scope === "personal" ? "personal" : (content.categoryName as MarketCategoryKey),
    categoryTitle: skill.scope === "personal" ? t('mySkills') : content.categoryName,
    icon: content.icon,
    colorClassName: content.colorClassName,
    sortOrder: skill.sortOrder,
    isRecommended: skill.scope !== "personal" && content.isHot,
    hot: skill.scope !== "personal" && content.isHot,
    entryCopy: content.description || t('useSkillAssist', { title: content.title }),
    targetUsers: content.targetUsers,
    exampleInput: content.exampleInput,
    prefillTemplate: content.prefillTemplate,
    expectedOutput: content.expectedOutput,
    reason: content.reason,
    prompt: t('useSkillPrompt', { name: content.title }),
    scope: skill.scope,
    source: skill.source,
    reliabilityReport: skill.reliabilityReport ?? null,
  };
}

function filterMarketSkills(skills: MarketSkill[], activeCategory: MarketCategoryKey, keyword: string) {
  const normalizedKeyword = keyword.trim().toLowerCase();
  return skills
    .filter((skill) => {
    const matchesCategory =
      activeCategory === "personal"
        ? skill.scope === "personal"
        : activeCategory === "recommended"
          ? skill.scope !== "personal" && skill.isRecommended
          : skill.scope !== "personal" && skill.categoryKey === activeCategory;
    if (!matchesCategory) return false;
    if (!normalizedKeyword) return true;
    return [
      skill.slug,
      skill.title,
      skill.description,
      skill.categoryTitle,
      skill.entryCopy,
      skill.targetUsers,
      skill.exampleInput,
      skill.prefillTemplate,
      skill.expectedOutput,
      skill.reason,
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalizedKeyword);
  })
    .sort(compareMarketSkillsByOrder);
}

function NavButton({
  icon,
  label,
  isActive,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`iw-skill-library-nav-btn flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left text-[13px] font-medium transition-all ${isActive
        ? "border-gray-200/60 bg-white text-blue-600 shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)]"
        : "border-transparent text-gray-600 hover:bg-gray-100/80 hover:text-gray-900"
        }`}
    >
      <span className={isActive ? "text-blue-500" : "text-gray-400"}>{icon}</span>
      <span className="truncate">{label}</span>
    </button>
  );
}

export default function SkillLibraryPanel({ onClose, onInsert, onCreateSkillInstall }: SkillLibraryPanelProps) {
  const t = useTranslations('workspace.skillLibrary');
  const tWorkbench = useTranslations('workspace.workbench');
  const tChat = useTranslations('workspace.chat');
  const [keyword, setKeyword] = React.useState("");
  const [activeEnterpriseId, setActiveEnterpriseId] = React.useState(() =>
    getActiveEnterpriseId(),
  );
  const [apiSkills, setApiSkills] = React.useState<ZclawSkillMarketItem[]>([]);
  const [apiCategories, setApiCategories] = React.useState<ZclawSkillMarketCategory[]>([]);
  const [submissionsBySkillKey, setSubmissionsBySkillKey] = React.useState<
    Record<string, SkillSubmissionRecord>
  >({});
  const [submittingSkillKey, setSubmittingSkillKey] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(true);
  const [activeCategory, setActiveCategory] = React.useState<MarketCategoryKey>("recommended");
  const [previewSkillId, setPreviewSkillId] = React.useState("");
  const [isDetailCollapsed, setIsDetailCollapsed] = React.useState(false);
  const [isReturningToGrid, setIsReturningToGrid] = React.useState(false);
  const [isEditingPersonal, setIsEditingPersonal] = React.useState(false);
  const [savingPersonal, setSavingPersonal] = React.useState(false);
  const [editForm, setEditForm] = React.useState<PersonalEditFormState | null>(null);
  const [versionHistoryBySkillKey, setVersionHistoryBySkillKey] = React.useState<
    Record<string, SkillSubmissionVersionRecord[]>
  >({});
  const [resubmittingVersion, setResubmittingVersion] = React.useState<number | null>(null);
  const versionHistoryFetchedRef = React.useRef<Set<string>>(new Set());
  const [personalRevisionsBySkillKey, setPersonalRevisionsBySkillKey] = React.useState<
    Record<string, PersonalSkillRevisionSummary[]>
  >({});
  const [restoringPersonalRevision, setRestoringPersonalRevision] = React.useState<number | null>(
    null,
  );
  const personalRevisionsFetchedRef = React.useRef<Set<string>>(new Set());
  const [changesBySkillKey, setChangesBySkillKey] = React.useState<
    Record<string, "changed" | "unchanged" | "error">
  >({});
  const [changesLoadingKey, setChangesLoadingKey] = React.useState("");
  const changesFetchedRef = React.useRef<Set<string>>(new Set());

  const resolveSubmissionStatusLabel = React.useCallback(
    (submission: SkillSubmissionRecord | undefined) => {
      if (!submission) return null;
      if (submission.status === "pending") return t("statusPending");
      if (submission.status === "approved") return t("statusApproved");
      if (submission.status === "rejected") return t("statusRejected");
      if (submission.status === "removed") return t("statusRemoved");
      return null;
    },
    [t],
  );

  const loadVersionHistory = React.useCallback(
    async (skillKey: string, options?: { force?: boolean }) => {
      const normalizedKey = skillKey.trim();
      if (!normalizedKey) return;

      const hasCache = versionHistoryFetchedRef.current.has(normalizedKey);
      if (!options?.force && hasCache) {
        return;
      }

      try {
        const response = await listSkillVersionsApi(normalizedKey);
        setVersionHistoryBySkillKey((prev) => ({
          ...prev,
          [normalizedKey]: response.items ?? [],
        }));
        versionHistoryFetchedRef.current.add(normalizedKey);
      } catch (error) {
        if (!hasCache) {
          errorToast(error instanceof Error ? error.message : t("versionHistoryLoadFailed"));
          setVersionHistoryBySkillKey((prev) => ({
            ...prev,
            [normalizedKey]: [],
          }));
        }
      }
    },
    [t],
  );

  const invalidateVersionHistory = React.useCallback((skillKey: string) => {
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) return;
    versionHistoryFetchedRef.current.delete(normalizedKey);
  }, []);

  const loadPersonalRevisions = React.useCallback(
    async (skillKey: string, options?: { force?: boolean }) => {
      const normalizedKey = skillKey.trim();
      if (!normalizedKey) return;
      const hasCache = personalRevisionsFetchedRef.current.has(normalizedKey);
      if (!options?.force && hasCache) return;
      try {
        const response = await listPersonalSkillRevisionsApi(normalizedKey);
        setPersonalRevisionsBySkillKey((prev) => ({
          ...prev,
          [normalizedKey]: response.items ?? [],
        }));
        personalRevisionsFetchedRef.current.add(normalizedKey);
      } catch (error) {
        if (!hasCache) {
          errorToast(
            error instanceof Error ? error.message : t("personalRevisionLoadFailed"),
          );
          setPersonalRevisionsBySkillKey((prev) => ({
            ...prev,
            [normalizedKey]: [],
          }));
        }
      }
    },
    [t],
  );

  const invalidatePersonalRevisions = React.useCallback((skillKey: string) => {
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) return;
    personalRevisionsFetchedRef.current.delete(normalizedKey);
  }, []);

  const loadSubmissionChanges = React.useCallback(
    async (skillKey: string, options?: { force?: boolean }) => {
      const normalizedKey = skillKey.trim();
      if (!normalizedKey) return;
      const hasCache = changesFetchedRef.current.has(normalizedKey);
      if (!options?.force && hasCache) return;

      if (!hasCache) {
        setChangesLoadingKey(normalizedKey);
      }
      try {
        const response = await getSkillSubmissionChangesApi(normalizedKey);
        setChangesBySkillKey((prev) => ({
          ...prev,
          [normalizedKey]: response.hasChanges ? "changed" : "unchanged",
        }));
        changesFetchedRef.current.add(normalizedKey);
      } catch {
        setChangesBySkillKey((prev) => ({
          ...prev,
          [normalizedKey]: "error",
        }));
        changesFetchedRef.current.add(normalizedKey);
      } finally {
        setChangesLoadingKey((current) => (current === normalizedKey ? "" : current));
      }
    },
    [],
  );

  const invalidateSubmissionChanges = React.useCallback((skillKey: string) => {
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) return;
    changesFetchedRef.current.delete(normalizedKey);
  }, []);

  const reloadSubmissions = React.useCallback(async () => {
    try {
      const response = await listMySkillSubmissionsApi();
      const next: Record<string, SkillSubmissionRecord> = {};
      for (const item of response.items ?? []) {
        next[item.skillKey] = item;
      }
      setSubmissionsBySkillKey(next);
    } catch {
      // 无组织上下文时静默跳过
    }
  }, []);

  const reloadMarket = React.useCallback(async () => {
    const response = await listZclawSkillMarketApi({ force: true });
    setApiSkills(response.items.filter((skill) => skill.selectable !== false));
    setApiCategories(response.categories ?? []);
  }, []);

  React.useEffect(() => {
    const syncEnterpriseId = () => {
      setActiveEnterpriseId(getActiveEnterpriseId());
    };
    syncEnterpriseId();
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
    return () => window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, syncEnterpriseId);
  }, []);

  React.useEffect(() => {
    const handleSkillMarketChanged = () => {
      void reloadMarket();
    };
    window.addEventListener(SKILL_MARKET_CHANGED_EVENT, handleSkillMarketChanged);
    return () => window.removeEventListener(SKILL_MARKET_CHANGED_EVENT, handleSkillMarketChanged);
  }, [reloadMarket]);

  React.useEffect(() => {
    let active = true;
    setIsLoading(true);
    void (async () => {
      try {
        const response = await listZclawSkillMarketApi({ force: true });
        if (!active) return;
        setApiSkills(response.items.filter((skill) => skill.selectable !== false));
        setApiCategories(response.categories ?? []);
        await reloadSubmissions();
      } catch (error) {
        emitError(error, { path: '/api/zclaw/skill-market', page: window.location.pathname });
      } finally {
        if (active) setIsLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [activeEnterpriseId, reloadSubmissions]);

  const openPersonalEdit = React.useCallback(
    (skill: MarketSkill) => {
      const raw = findMatchingMarketItem(apiSkills, skill);
      setEditForm({
        title: raw?.title?.trim() || skill.title,
        description: raw?.displayDescription ?? raw?.description ?? skill.description,
        targetUsers: raw?.targetUsers ?? "",
        reason: raw?.reason ?? "",
        exampleInput: raw?.exampleInput ?? "",
        prefillTemplate: raw?.prefillTemplate ?? "",
        expectedOutput: raw?.expectedOutput ?? "",
        icon: raw?.icon ?? "",
        colorClassName: raw?.colorClassName ?? "",
      });
      setIsEditingPersonal(true);
    },
    [apiSkills],
  );

  const handleSavePersonalEdit = React.useCallback(
    async (skill: MarketSkill) => {
      if (!editForm || savingPersonal) return;
      const title = editForm.title.trim();
      if (!title) {
        toast.error(t("titleRequired"));
        return;
      }
      setSavingPersonal(true);
      try {
        await savePersonalSkillConfigApi(skill.skillKey, {
          title,
          description: editForm.description.trim(),
          targetUsers: editForm.targetUsers.trim(),
          reason: editForm.reason.trim(),
          exampleInput: editForm.exampleInput.trim(),
          prefillTemplate: editForm.prefillTemplate.trim(),
          expectedOutput: editForm.expectedOutput.trim(),
          icon: editForm.icon.trim() || null,
          colorClassName: editForm.colorClassName.trim() || null,
        });
        await reloadMarket();
        setIsEditingPersonal(false);
        setEditForm(null);
        toast.success(t("saveSuccess"));
        invalidateSubmissionChanges(skill.skillKey);
        void loadSubmissionChanges(skill.skillKey, { force: true });
      } catch (error) {
        errorToast(error instanceof Error ? error.message : t("saveFailed"));
      } finally {
        setSavingPersonal(false);
      }
    },
    [editForm, invalidateSubmissionChanges, loadSubmissionChanges, reloadMarket, savingPersonal, t],
  );

  const handleSubmitForReview = React.useCallback(
    async (skill: MarketSkill) => {
      if (!skill.skillKey || submittingSkillKey) return;
      setSubmittingSkillKey(skill.skillKey);
      try {
        const response = await submitSkillForReviewApi(skill.skillKey);
        setSubmissionsBySkillKey((prev) => ({
          ...prev,
          [skill.skillKey]: response.submission,
        }));
        toast.success(t("submitSuccess"));
        invalidateVersionHistory(skill.skillKey);
        invalidateSubmissionChanges(skill.skillKey);
        await Promise.all([
          loadVersionHistory(skill.skillKey, { force: true }),
          loadSubmissionChanges(skill.skillKey, { force: true }),
        ]);
      } catch (error) {
        errorToast(error instanceof Error ? error.message : t("submitFailed"));
      } finally {
        setSubmittingSkillKey("");
      }
    },
    [
      invalidateSubmissionChanges,
      invalidateVersionHistory,
      loadSubmissionChanges,
      loadVersionHistory,
      submittingSkillKey,
      t,
    ],
  );

  const handleResubmitVersion = React.useCallback(
    async (skill: MarketSkill, version: number) => {
      if (!skill.skillKey || resubmittingVersion != null) return;
      setResubmittingVersion(version);
      try {
        const response = await resubmitSkillVersionApi(skill.skillKey, version);
        setSubmissionsBySkillKey((prev) => ({
          ...prev,
          [skill.skillKey]: response.submission,
        }));
        toast.success(t("resubmitVersionSuccess", { version }));
        invalidateVersionHistory(skill.skillKey);
        invalidateSubmissionChanges(skill.skillKey);
        await Promise.all([
          loadVersionHistory(skill.skillKey, { force: true }),
          loadSubmissionChanges(skill.skillKey, { force: true }),
        ]);
      } catch (error) {
        errorToast(error instanceof Error ? error.message : t("resubmitVersionFailed"));
      } finally {
        setResubmittingVersion(null);
      }
    },
    [
      invalidateSubmissionChanges,
      invalidateVersionHistory,
      loadSubmissionChanges,
      loadVersionHistory,
      resubmittingVersion,
      t,
    ],
  );

  const handleRestorePersonalRevision = React.useCallback(
    async (skill: MarketSkill, revision: number) => {
      if (!skill.skillKey || restoringPersonalRevision != null) return;
      setRestoringPersonalRevision(revision);
      try {
        await restorePersonalSkillRevisionApi(skill.skillKey, revision);
        toast.success(t("personalRevisionRestoreSuccess", { revision }));
        invalidatePersonalRevisions(skill.skillKey);
        invalidateSubmissionChanges(skill.skillKey);
        await Promise.all([
          reloadMarket(),
          loadPersonalRevisions(skill.skillKey, { force: true }),
          loadSubmissionChanges(skill.skillKey, { force: true }),
        ]);
      } catch (error) {
        errorToast(
          error instanceof Error ? error.message : t("personalRevisionRestoreFailed"),
        );
      } finally {
        setRestoringPersonalRevision(null);
      }
    },
    [
      invalidatePersonalRevisions,
      invalidateSubmissionChanges,
      loadPersonalRevisions,
      loadSubmissionChanges,
      reloadMarket,
      restoringPersonalRevision,
      t,
    ],
  );

  React.useEffect(() => {
    setIsEditingPersonal(false);
    setEditForm(null);
  }, [previewSkillId]);

  const marketSkills = React.useMemo<MarketSkill[]>(
    () => apiSkills.map((skill, index) => toApiMarketSkill(skill, index, t, tWorkbench)),
    [apiSkills, t, tWorkbench],
  );

  const categories = React.useMemo<MarketCategory[]>(() => {
    const discoverCategories = [
      { key: "personal", title: t('mySkills') },
      { key: "recommended", title: tWorkbench('recommendedSkills') },
    ] satisfies MarketCategory[];

    const roleCategories = apiCategories.map((category) => ({
      key: category.name as MarketCategoryKey,
      title: category.name,
      icon: category.icon ?? null,
      colorClassName: category.colorClassName ?? null,
    }));

    return [...discoverCategories, ...roleCategories];
  }, [apiCategories, t, tWorkbench]);

  React.useEffect(() => {
    if (categories.some((category) => category.key === activeCategory)) return;
    setActiveCategory("recommended");
    setPreviewSkillId("");
    setIsDetailCollapsed(false);
    setIsReturningToGrid(false);
  }, [activeCategory, categories]);

  const filteredSkills = React.useMemo(() => {
    if (activeCategory === "recommended") {
      const normalizedKeyword = keyword.trim().toLowerCase();
      const views = buildMarketRecommendedSkillViews(apiSkills);
      const filteredViews = views.filter((view) => {
        if (!normalizedKeyword) return true;
        return [
          view.skill.name,
          view.title,
          view.description,
          view.targetUsers,
          view.reason,
          view.expectedOutput,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedKeyword);
      });

      return filteredViews.flatMap((view) => {
        const base = marketSkills.find((skill) => skill.id === view.skill.id);
        if (!base) return [];
        return [
          {
            ...base,
            title: view.title,
            description: view.description,
            icon: view.icon,
            colorClassName: view.colorClassName,
            isRecommended: true,
            hot: true,
          },
        ];
      });
    }

    return filterMarketSkills(marketSkills, activeCategory, keyword);
  }, [activeCategory, apiSkills, keyword, marketSkills]);

  React.useEffect(() => {
    if (filteredSkills.length === 0) {
      setPreviewSkillId("");
      setIsDetailCollapsed(false);
      setIsReturningToGrid(false);
      return;
    }
    if (!filteredSkills.some((skill) => skill.id === previewSkillId)) {
      setPreviewSkillId("");
      setIsDetailCollapsed(false);
      setIsReturningToGrid(false);
    }
  }, [filteredSkills, previewSkillId]);

  const previewSkill = React.useMemo(
    () => (isDetailCollapsed ? null : filteredSkills.find((skill) => skill.id === previewSkillId) || null),
    [filteredSkills, isDetailCollapsed, previewSkillId],
  );

  React.useEffect(() => {
    // 选中个人技能时预取组织版本历史 + AI 个人修订
    if (!previewSkill?.skillKey || previewSkill.scope !== "personal") {
      return;
    }
    void loadVersionHistory(previewSkill.skillKey);
    void loadPersonalRevisions(previewSkill.skillKey);
    const submission = submissionsBySkillKey[previewSkill.skillKey];
    if (submission?.status === "approved") {
      void loadSubmissionChanges(previewSkill.skillKey);
    }
  }, [
    loadPersonalRevisions,
    loadSubmissionChanges,
    loadVersionHistory,
    previewSkill?.scope,
    previewSkill?.skillKey,
    submissionsBySkillKey,
  ]);
  const previewPersonalRaw = React.useMemo(
    () =>
      previewSkill?.scope === "personal"
        ? findMatchingMarketItem(apiSkills, previewSkill) ?? null
        : null,
    [apiSkills, previewSkill],
  );
  const isActiveCategoryLoading = isLoading;

  const handleCategoryChange = (categoryKey: MarketCategoryKey) => {
    setActiveCategory(categoryKey);
    setKeyword("");
    setPreviewSkillId("");
    setIsDetailCollapsed(false);
    setIsReturningToGrid(false);
  };

  const handleReturnToList = () => {
    setIsReturningToGrid(true);
    setIsDetailCollapsed(true);
  };

  const insertSkill = React.useCallback(
    (skill: MarketSkill, options?: { prefillText?: string }) => {
      const conversationSkillKey = resolveConversationSkillKey({
        id: skill.id,
        name: skill.slug,
        scope: skill.scope,
        skillKey: skill.skillKey,
      });
      onInsert({
        id: conversationSkillKey,
        name: conversationSkillKey,
        displayName: skill.title,
        prompt: skill.prompt,
        prefillText: options?.prefillText,
        scope: skill.scope,
        source: skill.source,
      });
    },
    [onInsert],
  );

  const handleApplySkillTemplate = (skill: MarketSkill) => {
    insertSkill(skill, { prefillText: resolveSkillPrefillText(skill) });
    toast.success(
      skill.scope === "personal" ? t('skillAdded', { title: skill.title }) : t('scenarioApplied', { title: skill.title }),
    );
    onClose();
  };

  const handleUseSkillDirect = (skill: MarketSkill) => {
    insertSkill(skill);
    toast.success(t('skillEnabled', { title: skill.title }));
    onClose();
  };

  const isListCompact = Boolean(previewSkill || isReturningToGrid);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98, y: 15 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98, y: 15 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="iw-skill-library-root relative z-10 flex h-full min-h-0 overflow-hidden rounded-3xl border border-gray-200/50 bg-white text-gray-900 shadow-2xl"
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute right-4 top-4 z-50 flex size-8 items-center justify-center rounded-full bg-black/5 text-gray-500 transition-colors hover:bg-black/10 hover:text-gray-700"
        title={t('close')}
      >
        <X className="size-4" />
      </button>

      <aside className="iw-skill-library-sidebar flex w-[220px] shrink-0 flex-col border-r border-gray-100 bg-gray-50/50 pb-6">
        <div className="p-5 pb-2">
          <div className="mb-6 flex items-center gap-2">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Sparkles className="size-3.5" />
            </div>
            <h2 className="truncate text-lg font-bold tracking-tight text-gray-900">{tChat('skillLibrary')}</h2>
          </div>
        </div>

        <div className="iw-skill-library-nav-scroll no-scrollbar min-h-0 flex-1 space-y-1 overflow-y-auto px-3">
          <div>
            <div className="mb-2 mt-2 px-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">{t('discover')}</div>
            <NavButton
              icon={<UserRound className={activeCategory === "personal" ? "size-[15px] text-primary" : "size-[15px]"} />}
              label={t('mySkills')}
              isActive={activeCategory === "personal"}
              onClick={() => handleCategoryChange("personal")}
            />
            <NavButton
              icon={<Flame className={activeCategory === "recommended" ? "size-[15px] text-primary" : "size-[15px]"} />}
              label={tWorkbench('recommendedSkills')}
              isActive={activeCategory === "recommended"}
              onClick={() => handleCategoryChange("recommended")}
            />
          </div>

          <div>
            <div className="mb-2 mt-6 px-3 text-[11px] font-bold uppercase tracking-wider text-gray-400">{t('categories')}</div>
            {categories
              .filter((category) => category.key !== "personal" && category.key !== "recommended")
              .map((category) => (
                <NavButton
                  key={category.key}
                  icon={renderCategoryNavIcon(category, activeCategory === category.key)}
                  label={category.title}
                  isActive={activeCategory === category.key}
                  onClick={() => handleCategoryChange(category.key)}
                />
              ))}
          </div>
        </div>
      </aside>

      <motion.section
        layout
        initial={false}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={`iw-skill-library-list flex min-h-0 shrink-0 flex-col border-r border-gray-100 bg-white ${previewSkill ? "w-[340px]" : "flex-1"
          }`}
      >
        <motion.div layout className="shrink-0 border-b border-gray-100 p-4 pr-14">
          <div className="flex items-center gap-3">
            <div className="group relative min-w-0 flex-1 max-w-md">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-[15px] -translate-y-1/2 text-gray-400 transition-colors group-focus-within:text-blue-500" />
              <input
                type="text"
                value={keyword}
                onChange={(event) => {
                  setKeyword(event.target.value);
                  setPreviewSkillId("");
                  setIsDetailCollapsed(false);
                  setIsReturningToGrid(false);
                }}
                placeholder={t('searchPlaceholder')}
                className="w-full rounded-xl border border-gray-200/80 bg-gray-50/50 py-2 pl-9 pr-4 text-[13px] text-gray-800 outline-none transition-all placeholder:text-gray-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <button
              type="button"
              onClick={onCreateSkillInstall}
              className="iw-skill-library-create-btn inline-flex h-9 shrink-0 items-center gap-1.5 rounded-xl bg-primary px-4 text-[13px] font-semibold text-primary-foreground shadow-sm ring-1 ring-primary/20 transition-all hover:opacity-90 hover:shadow-md active:scale-[0.98]"
            >
              <Plus className="size-4 stroke-[2.5]" />
              <span className="iw-skill-library-create-label">{t('createSkill')}</span>
            </button>
          </div>
        </motion.div>

        <div className="no-scrollbar min-h-0 flex-1 overflow-y-auto bg-[#FAFAFA] p-4">
          {isActiveCategoryLoading ? (
            <div className="flex h-full min-h-[260px] items-center justify-center text-center">
              <div>
                <Sparkles className="mx-auto mb-3 size-6 animate-pulse text-blue-500" />
                <div className="text-sm font-semibold text-gray-900">{t('loading')}</div>
              </div>
            </div>
          ) : filteredSkills.length === 0 ? (
            <div className="flex h-full min-h-[260px] flex-col items-center justify-center text-center text-gray-400">
              {activeCategory === "personal" ? (
                <>
                  <UserRound className="mb-3 size-8 text-gray-300" />
                  <p className="text-sm font-semibold text-gray-500">{t('noMySkills')}</p>
                  <p className="mt-1 text-xs font-medium text-gray-400">{t('noMySkillsHint')}</p>
                </>
              ) : (
                <>
                  <Search className="mb-3 size-8 text-gray-300" />
                  <p className="text-sm font-medium">{t('noResults')}</p>
                </>
              )}
            </div>
          ) : (
            <>
            <motion.div
              layout="position"
              transition={{ type: "spring", stiffness: 260, damping: 32 }}
              className={`iw-skill-library-grid ${isListCompact ? "flex flex-col gap-3" : "grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4"}`}
            >
              {filteredSkills.map((skill) => {
                const SkillIcon = resolveSkillIcon(skill.icon);
                const isActive = previewSkillId === skill.id && (Boolean(previewSkill) || isReturningToGrid);
                const submission = skill.scope === "personal" ? submissionsBySkillKey[skill.skillKey] : undefined;
                const statusLabel = resolveSubmissionStatusLabel(submission);
                return (
                  <motion.button
                    layout="position"
                    transition={{ type: "spring", stiffness: 260, damping: 32 }}
                    key={skill.id}
                    type="button"
                    onClick={() => {
                      setIsReturningToGrid(false);
                      setPreviewSkillId(skill.id);
                      setIsDetailCollapsed(false);
                    }}
                    className={`group flex w-full items-start gap-4 rounded-xl border p-4 text-left transition-all duration-200 ${isActive
                      ? "border-blue-200 bg-blue-50/80 shadow-[0_2px_12px_-4px_rgba(59,130,246,0.2)]"
                      : "border-gray-200/60 bg-white hover:border-blue-200/60 hover:bg-white hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]"
                      }`}
                  >
                    <div
                      className={`flex size-10 shrink-0 items-center justify-center rounded-[10px] border transition-all ${isActive ? "border-blue-600 bg-blue-500 text-white" : `${skill.colorClassName} group-hover:scale-105`
                        }`}
                    >
                      <SkillIcon className="size-[18px]" />
                    </div>
                    <div className="min-w-0 flex-1 pt-0.5">
                      <div className="mb-1.5 flex items-center gap-2">
                        <h3 className={`truncate text-[14px] font-bold ${isActive ? "text-blue-900" : "text-gray-900 group-hover:text-blue-600"}`}>
                          {skill.title}
                        </h3>
                        {statusLabel ? (
                          <span className="shrink-0 rounded border border-border bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                            {statusLabel}
                          </span>
                        ) : null}
                        {skill.hot ? <Flame className="size-3 shrink-0 text-primary" /> : null}
                      </div>
                      <p
                        className={`text-[12px] leading-relaxed ${isListCompact ? "line-clamp-1" : "line-clamp-2"
                          } ${isActive ? "text-blue-700/80" : "text-gray-500 group-hover:text-gray-600"}`}
                      >
                        {skill.description}
                      </p>
                    </div>
                  </motion.button>
                );
              })}
            </motion.div>

            </>
          )}
        </div>
      </motion.section>

      <AnimatePresence
        initial={false}
        onExitComplete={() => {
          if (!isReturningToGrid) return;
          setPreviewSkillId("");
          setIsDetailCollapsed(false);
          setIsReturningToGrid(false);
        }}
      >
        {previewSkill ? (
          <motion.section
            layout
            key="detail-panel"
            initial={{ opacity: 0, width: 0, flex: 0 }}
            animate={{ opacity: 1, width: "auto", flex: 1 }}
            exit={{ opacity: 0, width: 0, flex: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="iw-skill-library-detail relative flex min-w-0 shrink-0 flex-col overflow-hidden border-l border-gray-100/50 bg-white"
          >
            <div className="iw-skill-library-detail-inner relative flex h-full w-full min-w-[400px] flex-col">
              <div className="iw-skill-library-detail-back absolute right-16 top-4 z-20">
                <button
                  type="button"
                  onClick={handleReturnToList}
                  className="inline-flex h-8 items-center gap-1.5 rounded-full bg-gray-50 px-3 text-[12px] font-semibold text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800"
                  title={t('backToList')}
                >
                  <ArrowLeft className="size-3.5" />
                  {t('backToList')}
                </button>
              </div>

              <div className="no-scrollbar relative z-0 flex min-h-0 flex-1 flex-col overflow-y-auto pb-24">
                {isEditingPersonal && editForm && previewSkill.scope === "personal" ? (
                  <div className="space-y-4 bg-white p-8 pb-8">
                    <h2 className="text-[18px] font-semibold text-foreground">{t("editTitle")}</h2>
                    {submissionsBySkillKey[previewSkill.skillKey]?.status === "pending" ? (
                      <p className="text-[12px] text-muted-foreground">{t("pendingEditHint")}</p>
                    ) : null}
                    <div className="space-y-3">
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("titleLabel")}</label>
                        <input
                          className="h-9 w-full rounded border border-border bg-card px-3 text-sm outline-none focus:border-primary"
                          value={editForm.title}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, title: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("descriptionLabel")}</label>
                        <textarea
                          className="min-h-[88px] w-full rounded border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
                          value={editForm.description}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, description: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("targetUsersLabel")}</label>
                        <input
                          className="h-9 w-full rounded border border-border bg-card px-3 text-sm outline-none focus:border-primary"
                          value={editForm.targetUsers}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, targetUsers: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("reasonLabel")}</label>
                        <textarea
                          className="min-h-[72px] w-full rounded border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
                          value={editForm.reason}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, reason: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("exampleInputLabel")}</label>
                        <textarea
                          className="min-h-[72px] w-full rounded border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
                          value={editForm.exampleInput}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, exampleInput: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("prefillTemplateLabel")}</label>
                        <textarea
                          className="min-h-[72px] w-full rounded border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
                          value={editForm.prefillTemplate}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, prefillTemplate: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-sm text-foreground">{t("expectedOutputLabel")}</label>
                        <textarea
                          className="min-h-[72px] w-full rounded border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary"
                          value={editForm.expectedOutput}
                          onChange={(event) =>
                            setEditForm((current) =>
                              current ? { ...current, expectedOutput: event.target.value } : current,
                            )
                          }
                        />
                      </div>
                      <SkillIconFieldGroup
                        icon={editForm.icon}
                        colorClassName={editForm.colorClassName}
                        onIconChange={(icon) =>
                          setEditForm((current) => (current ? { ...current, icon } : current))
                        }
                        onColorClassNameChange={(colorClassName) =>
                          setEditForm((current) =>
                            current ? { ...current, colorClassName } : current,
                          )
                        }
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="shrink-0 bg-white p-8 pb-8">
                      <div className="mb-6 flex items-start gap-5 pr-20">
                        <div className={`flex size-16 shrink-0 items-center justify-center rounded-2xl border shadow-sm ${previewSkill.colorClassName}`}>
                          {React.createElement(resolveSkillIcon(previewSkill.icon), { className: "size-7" })}
                        </div>
                        <div className="min-w-0 pt-1">
                          <h2 className="mb-2 text-[22px] font-extrabold leading-tight tracking-tight text-gray-900">{previewSkill.title}</h2>
                          <p className="text-[14px] font-medium leading-relaxed text-gray-500">{previewSkill.description}</p>
                        </div>
                      </div>

                      {previewSkill.scope === "personal" ? (
                        <>
                          <SkillPersonalRevisionSwitcher
                            skillKey={previewSkill.skillKey}
                            items={personalRevisionsBySkillKey[previewSkill.skillKey] ?? []}
                            restoringRevision={restoringPersonalRevision}
                            onRestore={(revision) =>
                              void handleRestorePersonalRevision(previewSkill, revision)
                            }
                          />
                          {(() => {
                            const submission = submissionsBySkillKey[previewSkill.skillKey];
                            const versionPending = submission
                              ? isVersionUpdatePending(submission)
                              : false;
                            return (
                              <SkillLiveVersionSwitcher
                                skillKey={previewSkill.skillKey}
                                items={versionHistoryBySkillKey[previewSkill.skillKey] ?? []}
                                pendingVersion={
                                  versionPending && submission
                                    ? resolvePendingReviewDisplayVersion(submission)
                                    : null
                                }
                                pendingSourceVersion={submission?.sourceVersion ?? null}
                                canRestore={canSubmitSkillSubmission(submission)}
                                restoringVersion={resubmittingVersion}
                                onRestore={(version) =>
                                  void handleResubmitVersion(previewSkill, version)
                                }
                              />
                            );
                          })()}
                        </>
                      ) : null}

                      {previewSkill.scope === "personal" && previewSkill.reliabilityReport ? (
                        <div className="mb-4">
                          <Link
                            href={`/skills/${encodeURIComponent(previewSkill.skillKey)}/security-report?from=library` as Route}
                            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                          >
                            <ShieldCheck className="h-4 w-4" />
                            查看安全评估报告
                          </Link>
                        </div>
                      ) : null}

                      {(Boolean(previewPersonalRaw?.targetUsers?.trim()) ||
                        Boolean(previewPersonalRaw?.reason?.trim()) ||
                        Boolean(previewSkill.targetUsers?.trim()) ||
                        Boolean(previewSkill.reason?.trim())) ? (
                        <>
                          {(Boolean(previewPersonalRaw?.targetUsers?.trim()) ||
                            Boolean(previewSkill.targetUsers?.trim())) ? (
                            <div className="mb-6 flex items-center gap-3">
                              <span className="shrink-0 text-[12px] font-bold uppercase tracking-wider text-gray-400">{t('targetUsers')}</span>
                              <div className="flex flex-wrap gap-2">
                                {(() => {
                                  const targetUsersText =
                                    previewSkill.scope === "personal"
                                      ? previewPersonalRaw?.targetUsers || previewSkill.targetUsers || ""
                                      : previewSkill.targetUsers;
                                  const roles = targetUsersText
                                    .split(/[、,，]/)
                                    .map((role) => role.trim())
                                    .filter(Boolean);
                                  return roles.map((role) => (
                                    <span key={role} className="rounded-md border border-gray-200/50 bg-gray-100 px-2.5 py-1 text-[12px] font-medium text-gray-600">
                                      {role}
                                    </span>
                                  ));
                                })()}
                              </div>
                            </div>
                          ) : null}

                          {(Boolean(previewPersonalRaw?.reason?.trim()) ||
                            Boolean(previewSkill.reason?.trim())) ? (
                            <div className="relative overflow-hidden rounded-xl border border-border p-4 text-[13px] leading-relaxed text-gray-700">
                              <div className="mb-1.5 flex items-center gap-1.5 text-[12px] font-bold uppercase tracking-wider text-muted-foreground">
                                <Sparkles className="size-[13px]" />
                                {t('highlights')}
                              </div>
                              <p className="pl-1 text-gray-600">
                                {previewSkill.scope === "personal"
                                  ? previewPersonalRaw?.reason || previewSkill.reason
                                  : previewSkill.reason}
                              </p>
                            </div>
                          ) : null}
                        </>
                      ) : null}
                    </div>

                    {(Boolean(previewPersonalRaw?.exampleInput?.trim()) ||
                      Boolean(previewPersonalRaw?.expectedOutput?.trim()) ||
                      Boolean(previewSkill.exampleInput?.trim()) ||
                      Boolean(previewSkill.expectedOutput?.trim())) ? (
                      <div className="relative flex flex-1 flex-col border-t border-gray-100/60 bg-[#FAFAFA] px-8 pb-10 pt-6 shadow-[inset_0_4px_10px_rgba(0,0,0,0.02)]">
                        <div className="flex items-center gap-3 pb-8">
                          <div className="h-px flex-1 bg-gray-200/80" />
                          <span className="px-2 text-[11px] font-bold uppercase tracking-widest text-gray-400">{t('interactionPreview')}</span>
                          <div className="h-px flex-1 bg-gray-200/80" />
                        </div>

                        <div className="space-y-6">
                          {(Boolean(previewPersonalRaw?.exampleInput?.trim()) ||
                            Boolean(previewSkill.exampleInput?.trim())) ? (
                            <div className="flex flex-col items-end gap-1.5">
                              <div className="mb-1 flex items-center gap-1.5 pr-1 text-[11px] font-semibold tracking-wide text-gray-400">
                                {t('typicalInput')}
                                <User className="size-3" />
                              </div>
                              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary p-4 text-[14px] font-medium leading-relaxed text-primary-foreground shadow-md">
                                {previewSkill.scope === "personal"
                                  ? previewPersonalRaw?.exampleInput || previewSkill.exampleInput
                                  : previewSkill.exampleInput}
                              </div>
                            </div>
                          ) : null}

                          {(Boolean(previewPersonalRaw?.expectedOutput?.trim()) ||
                            Boolean(previewSkill.expectedOutput?.trim())) ? (
                            <div className="flex flex-col items-start gap-1.5">
                              <div className="mb-1 flex items-center gap-1.5 pl-1 text-[11px] font-bold tracking-wide text-muted-foreground">
                                <Sparkles className="size-3" />
                                {t('expectedOutput')}
                              </div>
                              <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-gray-200/80 bg-white p-4 text-[14px] font-medium leading-relaxed text-gray-800 shadow-sm">
                                {previewSkill.scope === "personal"
                                  ? previewPersonalRaw?.expectedOutput || previewSkill.expectedOutput
                                  : previewSkill.expectedOutput}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                  </>
                )}
              </div>

              <div className="iw-skill-library-detail-actions absolute bottom-0 left-0 right-0 z-20 border-t border-gray-100/80 bg-white/80 p-4 px-5 backdrop-blur-md">
                {previewSkill.scope !== "personal" ? (
                  <div className="flex items-stretch gap-2.5">
                    <button
                      type="button"
                      onClick={() => handleUseSkillDirect(previewSkill)}
                      className="flex min-w-[108px] flex-[1] basis-0 items-center justify-center rounded-xl border border-border bg-white px-3 py-3 text-[14px] font-medium text-muted-foreground transition-colors hover:border-gray-300 hover:bg-gray-50 hover:text-foreground"
                    >
                      {t('useDirectly')}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplySkillTemplate(previewSkill)}
                      className="group flex min-w-0 flex-[2] basis-0 items-center justify-center gap-1.5 rounded-xl border border-gray-800 bg-gray-900 px-3 py-3 text-[14px] font-bold text-white shadow-[0_8px_20px_-6px_rgba(0,0,0,0.3)] transition-all hover:-translate-y-0.5 hover:bg-gray-800 hover:shadow-[0_12px_25px_-6px_rgba(0,0,0,0.4)]"
                    >
                      <Sparkles className="size-4 shrink-0 text-[#FFD700] transition-transform group-hover:scale-110" />
                      <span className="truncate">{t('applyScenario')}</span>
                    </button>
                  </div>
                ) : isEditingPersonal ? (
                  <div className="flex items-center justify-end gap-4">
                    <button
                      type="button"
                      className="text-sm text-muted-foreground hover:text-foreground"
                      onClick={() => {
                        setIsEditingPersonal(false);
                        setEditForm(null);
                      }}
                      disabled={savingPersonal}
                    >
                      {t("cancelEdit")}
                    </button>
                    <button
                      type="button"
                      className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
                      disabled={savingPersonal}
                      onClick={() => void handleSavePersonalEdit(previewSkill)}
                    >
                      {savingPersonal ? t("saving") : t("save")}
                    </button>
                  </div>
                ) : (
                  (() => {
                    const submission = submissionsBySkillKey[previewSkill.skillKey];
                    const canSubmit = canSubmitSkillSubmission(submission);
                    const isSubmitting = submittingSkillKey === previewSkill.skillKey;
                    const isPending = submission?.status === "pending";
                    const isVersionPending = submission ? isVersionUpdatePending(submission) : false;
                    const liveVersion = submission ? resolvePublishedVersion(submission) : null;
                    const changeStatus = changesBySkillKey[previewSkill.skillKey];
                    const isCheckingChanges =
                      submission?.status === "approved" &&
                      (changesLoadingKey === previewSkill.skillKey || !changeStatus);
                    const hasNoPersonalChanges =
                      submission?.status === "approved" && changeStatus === "unchanged";
                    const blockNewVersionSubmit = isCheckingChanges || hasNoPersonalChanges;
                    const submitLabel = isSubmitting
                      ? t("submitting")
                      : isCheckingChanges
                        ? t("checkingChanges")
                        : submission?.status === "approved"
                          ? t("submitNewVersion")
                          : submission?.status === "rejected" || submission?.status === "removed"
                            ? t("resubmitForReview")
                            : t("submitForReview");

                    return (
                      <div className="space-y-3">
                        {submission?.status === "rejected" && submission.rejectReason ? (
                          <p className="text-[12px] leading-relaxed text-muted-foreground">
                            {t("rejectReasonLabel")}: {submission.rejectReason}
                          </p>
                        ) : null}
                        {isVersionPending && submission ? (
                          <p className="text-[12px] text-muted-foreground">
                            {t(
                              isRollbackPending(submission)
                                ? "rollbackPendingReviewHint"
                                : "versionPendingReviewHint",
                              {
                                published:
                                  submission.approvedVersionAtSubmit ?? liveVersion ?? "?",
                                pending:
                                  resolvePendingReviewDisplayVersion(submission) ??
                                  submission.version,
                              },
                            )}
                          </p>
                        ) : isPending ? (
                          <p className="text-[12px] text-muted-foreground">{t("awaitingReview")}</p>
                        ) : null}
                        {submission?.status === "approved" && !isVersionPending && hasNoPersonalChanges ? (
                          <p className="text-[12px] text-muted-foreground">
                            {t("noChangesHint", {
                              version: liveVersion ?? submission.version,
                            })}
                          </p>
                        ) : submission?.status === "approved" && !isVersionPending ? (
                          <p className="text-[12px] text-muted-foreground">
                            {t("publishedHintWithVersion", {
                              version: liveVersion ?? submission.version,
                            })}
                          </p>
                        ) : null}
                        {submission?.status === "removed" ? (
                          <p className="text-[12px] text-muted-foreground">{t("removedHint")}</p>
                        ) : null}

                        <div className="flex items-stretch gap-2.5">
                          <button
                            type="button"
                            onClick={() => openPersonalEdit(previewSkill)}
                            disabled={isPending}
                            className="flex min-w-[88px] items-center justify-center rounded-xl border border-border bg-white px-3 py-3 text-[14px] font-medium text-muted-foreground transition-colors hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {t("edit")}
                          </button>
                          {canSubmit ? (
                            <button
                              type="button"
                              disabled={isSubmitting || blockNewVersionSubmit}
                              title={
                                hasNoPersonalChanges ? t("noChangesSubmitBlocked") : undefined
                              }
                              onClick={() => void handleSubmitForReview(previewSkill)}
                              className="flex min-w-[108px] flex-1 items-center justify-center rounded-xl bg-primary px-3 py-3 text-[14px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              {submitLabel}
                            </button>
                          ) : null}
                          <button
                            type="button"
                            onClick={() => handleApplySkillTemplate(previewSkill)}
                            className="flex min-w-[108px] flex-1 items-center justify-center gap-2 rounded-xl border border-border bg-white py-3.5 text-[14px] font-medium text-muted-foreground transition-colors hover:border-gray-300 hover:text-foreground"
                          >
                            {t("useThisSkill")}
                          </button>
                        </div>
                      </div>
                    );
                  })()
                )}
              </div>
            </div>
          </motion.section>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
}
