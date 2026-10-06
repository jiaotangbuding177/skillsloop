"use client";


import { translateAutoText } from '@/lib/i18n/translate-auto-text';
import React from "react";
import { ChevronDown, Sparkles } from "lucide-react";
import { resolveSkillIcon, SKILL_ICON_OPTIONS } from "@/lib/skillIconCatalog";
import { SKILL_ICON_STYLE_PRESETS } from "@/lib/skillIconStylePresets";

type SkillIconFieldGroupProps = {
  icon: string;
  colorClassName: string;
  onIconChange: (icon: string) => void;
  onColorClassNameChange: (colorClassName: string) => void;
};

const inputClassName =
  "h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20";

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="mb-1.5 block text-sm text-[#333]">{children}</label>;
}

export function SkillIconFieldGroup({
  icon,
  colorClassName,
  onIconChange,
  onColorClassNameChange,
}: SkillIconFieldGroupProps) {
  const [iconQuery, setIconQuery] = React.useState("");
  const [showCustomStyle, setShowCustomStyle] = React.useState(false);

  const PreviewIconComponent = resolveSkillIcon(icon);
  const previewClassName =
    colorClassName.trim() || "border-gray-200 bg-gray-50 text-gray-600";

  const normalizedQuery = iconQuery.trim().toLowerCase();
  const filteredIcons = SKILL_ICON_OPTIONS.filter((item) => {
    if (!normalizedQuery) return true;
    const haystack = [item.value, item.label, item.keywords ?? ""]
      .join(" ")
      .toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  React.useEffect(() => {
    if (!colorClassName.trim()) {
      setShowCustomStyle(false);
      return;
    }
    const matched = SKILL_ICON_STYLE_PRESETS.some(
      (item) => item.colorClassName === colorClassName,
    );
    setShowCustomStyle(!matched);
  }, [colorClassName]);

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
      <div className="flex items-start gap-4">
        <div
          className={`flex size-14 shrink-0 items-center justify-center rounded-2xl border shadow-sm ${previewClassName}`}
          aria-label={translateAutoText('图标预览')}
        >
          {/* eslint-disable-next-line react-hooks/static-components */}
          <PreviewIconComponent className="size-7" />
        </div>
        <div className="min-w-0 flex-1 space-y-1">
          <div className="text-sm font-medium text-[#333]">{translateAutoText('图标预览')}</div>
          <div className="text-xs text-[#8c8c8c]">
            {icon.trim() ? `图标：${icon}` : translateAutoText('图标：使用内置默认')}
          </div>
          <div className="text-xs text-[#8c8c8c]">
            {colorClassName.trim()
              ? `样式：${colorClassName}`
              : translateAutoText('样式：使用内置默认')}
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <FieldLabel>{translateAutoText('选择图标')}</FieldLabel>
          <input
            value={iconQuery}
            onChange={(event) => setIconQuery(event.target.value)}
            placeholder={translateAutoText('搜索图标名称或关键词')}
            className={`${inputClassName} mt-0`}
          />
          <div className="mt-2 max-h-40 overflow-y-auto rounded-lg border border-slate-200 bg-white p-2">
            <div className="grid grid-cols-6 gap-2 sm:grid-cols-8">
              {filteredIcons.map((item) => {
                const ItemIcon = resolveSkillIcon(item.value);
                const selected = icon === item.value;
                return (
                  <button
                    key={item.value}
                    type="button"
                    title={`${item.label} (${item.value})`}
                    onClick={() => onIconChange(item.value)}
                    className={`flex flex-col items-center gap-1 rounded-lg border px-1 py-2 text-[10px] transition-colors ${
                      selected
                        ? "border-[#1677ff] bg-[#e6f4ff] text-[#1677ff]"
                        : "border-transparent text-[#595959] hover:border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <ItemIcon className="size-5 shrink-0" />
                    <span className="line-clamp-1 w-full text-center">
                      {item.label}
                    </span>
                  </button>
                );
              })}
            </div>
            {filteredIcons.length === 0 ? (
              <div className="px-2 py-6 text-center text-sm text-[#8c8c8c]">
                没有匹配的图标
              </div>
            ) : null}
          </div>
          <button
            type="button"
            className="mt-2 text-sm text-[#1677ff] hover:text-[#4096ff]"
            onClick={() => onIconChange("")}
          >
            使用默认图标
          </button>
        </div>

        <div>
          <FieldLabel>{translateAutoText('选择样式')}</FieldLabel>
          <div className="flex flex-wrap gap-2">
            {SKILL_ICON_STYLE_PRESETS.map((preset) => {
              const selected = colorClassName === preset.colorClassName;
              return (
                <button
                  key={preset.colorClassName}
                  type="button"
                  title={preset.colorClassName}
                  onClick={() => onColorClassNameChange(preset.colorClassName)}
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition-colors ${
                    selected
                      ? "border-[#1677ff] bg-[#e6f4ff] text-[#1677ff]"
                      : "border-slate-200 bg-white text-[#595959] hover:border-[#4096ff]"
                  }`}
                >
                  <span
                    className={`inline-flex size-5 items-center justify-center rounded-full border ${preset.colorClassName}`}
                  >
                    <Sparkles className="size-3" />
                  </span>
                  {preset.label}
                </button>
              );
            })}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="text-sm text-[#1677ff] hover:text-[#4096ff]"
              onClick={() => onColorClassNameChange("")}
            >
              使用默认样式
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1 text-sm text-[#595959] hover:text-[#1677ff]"
              onClick={() => setShowCustomStyle((current) => !current)}
            >
              自定义类名
              <ChevronDown
                className={`size-4 transition-transform ${showCustomStyle ? "rotate-180" : ""}`}
              />
            </button>
          </div>
          {showCustomStyle ? (
            <input
              value={colorClassName}
              onChange={(event) => onColorClassNameChange(event.target.value)}
              placeholder={translateAutoText('如 text-fuchsia-700 bg-fuchsia-50 border-fuchsia-100')}
              className={`${inputClassName} mt-2`}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
