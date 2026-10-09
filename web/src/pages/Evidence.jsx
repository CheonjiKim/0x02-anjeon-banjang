import { Camera } from 'lucide-react';
import { EmptyState, Screen } from '../components/ui.jsx';

export default function Evidence() {
  return <Screen title="증빙 사진"><EmptyState icon={Camera} title="준비 중" /></Screen>;
}
