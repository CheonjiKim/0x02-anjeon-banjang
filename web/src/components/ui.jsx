import { Button, Page } from 'konsta/react';
import {
  ChevronLeft, CircleCheck, CircleHelp, EyeOff, Info,
  MessageCircleQuestion, ScanEye, Shield, ShieldAlert,
} from 'lucide-react';

export const STROKE = 2.25;
export const STATUS = {
  required: { label: '필수', Icon: ShieldAlert, cls: 'bg-danger-soft text-danger' },
  recommended: { label: '권장', Icon: Shield, cls: 'bg-warn-soft text-warn' },
  confirmed: { label: '확인됨', Icon: CircleCheck, cls: 'bg-ok-soft text-ok' },
  not_visible: { label: '안 보임', Icon: EyeOff, cls: 'bg-danger-soft text-danger' },
  uncertain: { label: '판단불가', Icon: CircleHelp, cls: 'bg-review-soft text-review' },
  todo_uncertain: { label: '판단불가', Icon: ScanEye, cls: 'bg-review-soft text-review' },
  condition: { label: '조건 미상', Icon: MessageCircleQuestion, cls: 'bg-gray-100 text-ink-sub' },
};

export function StatusBadge({ kind, label }) {
  const { label: defaultLabel, Icon, cls } = STATUS[kind];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold ${cls}`}>
      <Icon size={16} strokeWidth={STROKE} aria-hidden="true" />
      {label ?? defaultLabel}
    </span>
  );
}

export function LegalNote() {
  return (
    <p className="mx-[22px] mt-8 flex items-center justify-center gap-1.5 text-[13px] text-ink-sub">
      <Info size={16} strokeWidth={STROKE} aria-hidden="true" />
      AI 기반 서비스이며 참고용 안내입니다. 법률 자문이나 작업 승인이 아닙니다.
    </p>
  );
}

export function AppButton({ big = false, outline = false, className = '', ...props }) {
  return (
    <Button
      large outline={outline}
      className={`!rounded-[20px] !font-bold transition-transform active:scale-[0.98] ${big ? '!h-16 !text-lg' : '!h-14 !text-[17px]'} ${!outline && !props.disabled ? 'shadow-cta' : ''} ${className}`}
      {...props}
    />
  );
}

export function Chip({ active = false, className = '', children, ...props }) {
  return (
    <button type="button" aria-pressed={active}
      className={`min-h-11 rounded-full px-4 py-2 font-bold ${active ? 'bg-brand-primary text-white' : 'bg-brand-soft text-brand-dark'} ${className}`}
      {...props}>
      {children}
    </button>
  );
}

export function Segment({ value, onChange, options, label }) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-2">
      {options.map(([key, text]) => (
        <Chip key={key} active={value === key} onClick={() => onChange(key)}>{text}</Chip>
      ))}
    </div>
  );
}

export function BackButton({ onClick }) {
  return (
    <button type="button" onClick={onClick} aria-label="뒤로" className="flex h-11 w-11 items-center justify-center rounded-full bg-white shadow-card">
      <ChevronLeft size={24} strokeWidth={STROKE} aria-hidden="true" />
    </button>
  );
}

export function Screen({ title, left, right, tabbar = true, children }) {
  return (
    <Page className={`app-bg ${tabbar ? 'pb-safe-24' : 'pb-safe-8'}`}>
      <header className="relative flex h-16 items-center justify-center px-[22px]">
        {left && <div className="absolute left-[22px]">{left}</div>}
        <h1 className="text-xl font-extrabold text-ink">{title}</h1>
        {right && <div className="absolute right-[22px]">{right}</div>}
      </header>
      {children}
      <LegalNote />
    </Page>
  );
}

export function Panel({ className = '', children }) {
  return <section className={`mx-[22px] rounded-[20px] border border-line/60 bg-white p-5 shadow-card ${className}`}>{children}</section>;
}

export function SectionTitle({ children, aside }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="text-xl font-bold">{children}</h2>
      {aside && <span className="text-[15px] text-ink-sub">{aside}</span>}
    </div>
  );
}

export function PhotoStrip({ src, at, parts = [], className = '' }) {
  const date = new Date(at);
  const pad = (v) => String(v).padStart(2, '0');
  const time = `${date.getFullYear()}.${pad(date.getMonth() + 1)}.${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
  return (
    <figure className={`overflow-hidden rounded-[20px] ${className}`}>
      <img src={src} alt="제출한 증빙 사진" className="w-full object-cover" />
      <figcaption className="bg-black px-4 py-2 text-[13px] text-white">{[time, ...parts].join(' · ')}</figcaption>
    </figure>
  );
}

export function EmptyState({ icon: Icon, title, hint, action, onAction }) {
  return (
    <div className="mx-[22px] flex flex-col items-center py-14 text-center">
      {Icon && <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brand-soft text-brand-primary"><Icon size={36} strokeWidth={STROKE} aria-hidden="true" /></div>}
      <h2 className="text-xl font-bold">{title}</h2>
      {hint && <p className="mt-3 text-ink-sub">{hint}</p>}
      {action && <AppButton className="mt-6 w-full" onClick={onAction}>{action}</AppButton>}
    </div>
  );
}

export function Skeleton({ className = '' }) {
  return <div aria-hidden="true" className={`animate-pulse rounded-[20px] bg-gray-200 ${className}`} />;
}
