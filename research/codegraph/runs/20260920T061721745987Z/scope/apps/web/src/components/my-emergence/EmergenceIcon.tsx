import { skillIconMap } from '@/lib/skillIconCatalog';
import Image from 'next/image';

const rules = [
  ['image', /图像|图片|照片|影像|OCR|image/i],
  ['message-square-heart', /对话|讨论|沟通|决策|chat/i],
  ['file-text', /档案|文档|文件|成长|document/i],
  ['bar-chart-3', /市场|报告|经营|market/i],
  ['database', /数据|归因|分析|data/i],
  ['target', /竞争|定位|目标|strategy/i],
] as const;

export function resolveEmergenceIcon(title: string, summary?: string | null, configured?: string | null) {
  if (configured && skillIconMap[configured]) return configured;
  for (const text of [title, summary ?? '']) {
    const match = rules.find(([, pattern]) => pattern.test(text));
    if (match) return match[0];
  }
  return 'sparkles';
}

export function EmergenceIcon({ title, summary, configured, large = false }: {
  title: string;
  summary?: string | null;
  configured?: string | null;
  large?: boolean;
}) {
  const key = resolveEmergenceIcon(title, summary, configured);
  const Icon = skillIconMap[key] ?? skillIconMap.sparkles;
  const illustrated = rules.some(([name]) => name === key);
  return <span aria-hidden className={`emergence-icon emergence-icon--${key} ${large ? 'emergence-icon--large' : ''}`}>
    {illustrated ? <Image src={`/img/skill/emergence-icon-${key}.png`} alt="" width={large ? 88 : 44} height={large ? 88 : 44} sizes={large ? '88px' : '44px'} /> : <Icon />}
  </span>;
}
