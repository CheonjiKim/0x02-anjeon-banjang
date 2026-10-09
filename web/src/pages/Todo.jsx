import { ListTodo } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function Todo() {
  return <Screen title="반장 할 일"><EmptyState icon={ListTodo} title="준비 중" /></Screen>;
}
