import { ListTodo } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function Checklist() {
  return <Screen title="체크리스트"><EmptyState icon={ListTodo} title="준비 중" /></Screen>;
}
