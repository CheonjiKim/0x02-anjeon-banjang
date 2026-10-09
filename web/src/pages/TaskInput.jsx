import { HardHat } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function TaskInput() {
  return <Screen title="오늘 작업"><EmptyState icon={HardHat} title="준비 중" /></Screen>;
}
