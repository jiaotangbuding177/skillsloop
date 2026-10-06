'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Loader2, Upload, X } from 'lucide-react';
import { toast } from 'sonner';
import { errorToast } from '@/lib/error-handler';
import {
  importAdminSkillZipsApi,
  importEnterpriseAdminSkillZipsApi,
  type ImportSkillZipsResult,
} from '@/api';

/** Keep in sync with apps/api SKILL_ZIP_MAX_BYTES / SKILL_ZIP_MAX_MB */
const MAX_SKILL_ZIP_MB = 50;
const MAX_SKILL_ZIP_BYTES = MAX_SKILL_ZIP_MB * 1024 * 1024;

const inputClassName =
  'h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20';

const modalPrimaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const modalSecondaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60';

type CategoryOption = { id: string; name: string };

type SkillZipUploadDialogProps = {
  open: boolean;
  enterpriseId: string;
  isPlatformAdmin: boolean;
  categories: CategoryOption[];
  onClose: () => void;
  onImported: () => void | Promise<void>;
};

export function SkillZipUploadDialog({
  open,
  enterpriseId,
  isPlatformAdmin,
  categories,
  onClose,
  onImported,
}: SkillZipUploadDialogProps) {
  const t = useTranslations('workspace.pages.skillList');
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [files, setFiles] = React.useState<File[]>([]);
  const [categoryId, setCategoryId] = React.useState('');
  const [isVisible, setIsVisible] = React.useState(true);
  const [isHot, setIsHot] = React.useState(false);
  const [sortOrder, setSortOrder] = React.useState('0');
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    setFiles([]);
    setCategoryId(categories[0]?.id ?? '');
    setIsVisible(true);
    setIsHot(false);
    setSortOrder('0');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [open, categories]);

  if (!open) return null;

  const selectedCategory = categories.find((item) => item.id === categoryId);

  const runImport = async (overwriteSkillKeys: string[] = []) => {
    if (!enterpriseId) {
      toast.error(t('selectEnterpriseFirst'));
      return null;
    }
    if (files.length === 0) {
      toast.error(t('zipRequired'));
      return null;
    }
    const oversized = files.find((file) => file.size > MAX_SKILL_ZIP_BYTES);
    if (oversized) {
      toast.error(t('zipTooLarge', { name: oversized.name, limit: MAX_SKILL_ZIP_MB }));
      return null;
    }
    if (!selectedCategory) {
      toast.error(t('categoryRequired'));
      return null;
    }

    setSubmitting(true);
    try {
      const payload = {
        files,
        categoryId: selectedCategory.id,
        categoryName: selectedCategory.name,
        isVisible,
        isHot,
        sortOrder: Number(sortOrder) || 0,
        overwriteSkillKeys,
      };
      const result = isPlatformAdmin
        ? await importAdminSkillZipsApi(enterpriseId, payload)
        : await importEnterpriseAdminSkillZipsApi(enterpriseId, payload);
      return result;
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('uploadFailed'));
      return null;
    } finally {
      setSubmitting(false);
    }
  };

  const summarizeResult = (result: ImportSkillZipsResult) => {
    if (result.imported.length > 0) {
      toast.success(t('uploadSuccess', { count: result.imported.length }));
    }
    if (result.errors.length > 0) {
      const first = result.errors[0]!;
      toast.error(
        t('uploadPartialErrors', {
          count: result.errors.length,
          detail: first.skillKey
            ? `${first.skillKey}: ${first.message}`
            : `${first.sourceFile}: ${first.message}`,
        }),
      );
    }
  };

  const handleSubmit = async () => {
    const result = await runImport();
    if (!result) return;

    if (result.conflicts.length > 0) {
      const names = result.conflicts.map((item) => item.skillKey).join(', ');
      const confirmed = window.confirm(t('overwriteConfirm', { keys: names }));
      if (!confirmed) {
        summarizeResult(result);
        if (result.imported.length > 0) {
          await onImported();
        }
        return;
      }
      const retry = await runImport(result.conflicts.map((item) => item.skillKey));
      if (!retry) return;
      summarizeResult({
        imported: [...result.imported, ...retry.imported],
        conflicts: retry.conflicts,
        errors: [...result.errors, ...retry.errors],
      });
      if (retry.imported.length > 0 || result.imported.length > 0) {
        await onImported();
        onClose();
      }
      return;
    }

    summarizeResult(result);
    if (result.imported.length > 0) {
      await onImported();
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="flex w-full max-w-lg flex-col overflow-hidden rounded-lg border border-border bg-white shadow-lg">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h3 className="text-base font-semibold text-foreground">{t('uploadTitle')}</h3>
          <button
            type="button"
            className="rounded p-1 text-muted-foreground hover:text-foreground"
            onClick={onClose}
            disabled={submitting}
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="space-y-4 px-5 py-4">
          <p className="text-sm text-muted-foreground">{t('uploadHint')}</p>

          <div>
            <label className="mb-1.5 block text-sm text-[#333]">{t('zipFiles')}</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,application/zip"
              multiple
              className="block w-full text-sm text-[#333] file:mr-3 file:rounded file:border-0 file:bg-[#f5f5f5] file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-[#333]"
              onChange={(event) => {
                const next = Array.from(event.target.files ?? []);
                const accepted: File[] = [];
                for (const file of next) {
                  if (file.size > MAX_SKILL_ZIP_BYTES) {
                    toast.error(t('zipTooLarge', { name: file.name, limit: MAX_SKILL_ZIP_MB }));
                    continue;
                  }
                  accepted.push(file);
                }
                setFiles(accepted);
                if (accepted.length === 0 && fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
            />
            {files.length > 0 ? (
              <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                {files.map((file) => (
                  <li key={`${file.name}-${file.size}`}>{file.name}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-[#333]">{t('category')}</label>
            <select
              className={inputClassName}
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
            >
              <option value="">{t('categoryPlaceholder')}</option>
              {categories.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 text-sm text-[#333]">
              <input
                type="checkbox"
                checked={isVisible}
                onChange={(event) => setIsVisible(event.target.checked)}
              />
              {t('isVisible')}
            </label>
            <label className="flex items-center gap-2 text-sm text-[#333]">
              <input
                type="checkbox"
                checked={isHot}
                onChange={(event) => setIsHot(event.target.checked)}
              />
              {t('isHot')}
            </label>
          </div>

          <div>
            <label className="mb-1.5 block text-sm text-[#333]">{t('sortOrder')}</label>
            <input
              className={inputClassName}
              value={sortOrder}
              onChange={(event) => setSortOrder(event.target.value)}
              inputMode="numeric"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-border px-5 py-4">
          <button
            type="button"
            className={modalSecondaryButtonClassName}
            onClick={onClose}
            disabled={submitting}
          >
            {t('cancel')}
          </button>
          <button
            type="button"
            className={modalPrimaryButtonClassName}
            onClick={() => void handleSubmit()}
            disabled={submitting}
          >
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                {t('uploading')}
              </>
            ) : (
              <>
                <Upload className="size-4" />
                {t('uploadSubmit')}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
