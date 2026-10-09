import { ClipboardCheck } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function WorkerForm() {
  return <Screen title="작업자 확인" tabbar={false}><EmptyState icon={ClipboardCheck} title="준비 중" /></Screen>;
}
