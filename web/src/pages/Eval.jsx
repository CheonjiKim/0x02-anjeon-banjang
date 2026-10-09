import { useEffect, useState } from 'react';
import { ChartColumn, RefreshCw } from 'lucide-react';
import { api } from '../lib/api.js';
import { AppButton, EmptyState, Panel, Screen } from '../components/ui.jsx';

function Metric({ label, value, suffix = '' }) {
  return <div className="rounded-xl bg-brand-soft p-3"><p className="text-sm font-bold text-brand-dark">{label}</p><p className="mt-1 text-2xl font-extrabold text-brand-primary tnum">{value ?? '-'}{suffix}</p></div>;
}

export default function Eval() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true); setError('');
    try { setReport(await api('/eval/latest')); }
    catch (requestError) { setError(requestError.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  if (loading) return <Screen title="평가"><EmptyState icon={ChartColumn} title="평가 결과를 불러오는 중" /></Screen>;
  if (error) return <Screen title="평가"><EmptyState icon={ChartColumn} title="아직 평가 결과가 없어요" hint="개발자가 평가 실행 후 결과를 확인하는 화면입니다." action="다시 불러오기" onAction={load} /></Screen>;

  return <Screen title="AI 평가">
    <Panel><p className="text-sm text-ink-sub">최근 평가 파일</p><p className="mt-1 font-bold break-all">{report.file}</p><p className="mt-2 text-sm text-ink-sub">평가 수치는 개발 검증용이며 현장 안전 판단을 대신하지 않습니다.</p></Panel>
    {Object.entries(report.results || {}).map(([key, result]) => <Panel key={key} className="mt-4">
      <h2 className="font-bold">{result.variant_label || key}</h2>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <Metric label="오승인" value={result.false_approvals?.total} suffix="건" />
        <Metric label="작업·조건 정확도" value={result.extraction?.overall_accuracy_pct} suffix="%" />
        <Metric label="사진 판정 정확도" value={result.photo?.accuracy_pct} suffix="%" />
        <Metric label="TBM 누락 탐지" value={result.tbm?.recall_pct} suffix="%" />
      </div>
    </Panel>)}
    <div className="mx-[22px] mt-5"><AppButton outline className="w-full" onClick={load}><RefreshCw className="mr-2 inline" size={18} />새로고침</AppButton></div>
  </Screen>;
}
