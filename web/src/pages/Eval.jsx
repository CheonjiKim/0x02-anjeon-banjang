import { ChartColumn } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function Eval() {
  return <Screen title="평가"><EmptyState icon={ChartColumn} title="준비 중" /></Screen>;
}
