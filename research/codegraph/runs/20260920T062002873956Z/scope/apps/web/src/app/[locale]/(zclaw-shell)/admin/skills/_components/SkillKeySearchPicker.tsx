'use client';


import { translateAutoText } from '@/lib/i18n/translate-auto-text';
import React from 'react';
import { Loader2 } from 'lucide-react';
import type { AvailableSkillItem } from '@/api';

const inputClassName =
  'h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20';

export function SkillKeySearchPicker({
  value,
  selectedKey,
  options,
  loading,
  disabled,
  placeholder = translateAutoText('输入关键词搜索并选择 Skill'),
  maxVisible = 50,
  dropdownMaxClassName = 'max-h-72',
  onQueryChange,
  onSelect,
}: {
  value: string;
  selectedKey: string;
  options: AvailableSkillItem[];
  loading: boolean;
  disabled?: boolean;
  placeholder?: string;
  maxVisible?: number;
  dropdownMaxClassName?: string;
  onQueryChange: (next: string) => void;
  onSelect: (item: AvailableSkillItem) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const normalized = value.trim().toLowerCase();
  const filtered = options.filter((item) => {
    if (!normalized) return true;
    return item.aliases.some((alias) => alias.toLowerCase().includes(normalized));
  });

  return (
    <div className="relative">
      <input
        value={value}
        disabled={disabled}
        onChange={(event) => {
          onQueryChange(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 150);
        }}
        placeholder={placeholder}
        className={inputClassName}
      />
      {open && !disabled ? (
        <div
          className={`absolute z-[230] mt-1 w-full overflow-auto rounded border border-[#f0f0f0] bg-white shadow-lg ${dropdownMaxClassName}`}
        >
          {loading ? (
            <div className="flex items-center justify-center gap-2 px-3 py-4 text-sm text-[#8c8c8c]">
              <Loader2 className="h-4 w-4 animate-spin" />
              加载可选 Skill...
            </div>
          ) : filtered.length === 0 ? (
            <div className="px-3 py-4 text-sm text-[#8c8c8c]">{translateAutoText('没有匹配的 Skill，请调整关键词')}</div>
          ) : (
            filtered.slice(0, maxVisible).map((item) => (
              <button
                key={item.skillKey}
                type="button"
                className={`flex w-full flex-col gap-0.5 border-b border-[#f5f5f5] px-3 py-2 text-left last:border-b-0 hover:bg-[#f5f5f5] ${
                  selectedKey === item.skillKey ? 'bg-[#e6f4ff]' : ''
                }`}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  onSelect(item);
                  setOpen(false);
                }}
              >
                <span className="text-sm font-medium text-[#333]">{item.title}</span>
                <span className="font-mono text-xs text-[#8c8c8c]">{item.skillKey}</span>
                <span className="text-xs text-[#bfbfbf]">
                  {item.source === 'builtin' ? translateAutoText('内置') : 'Evomind'}
                  {item.kmInstalled ? '' : translateAutoText(' · 未安装')}
                </span>
              </button>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
