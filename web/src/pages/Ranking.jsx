import { Trophy } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function Ranking() {
  return <Screen title="기록"><EmptyState icon={Trophy} title="준비 중" /></Screen>;
}
