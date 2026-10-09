import { useEffect, useRef } from 'react';

export default function Modal({ title, onClose, children }) {
  const ref = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return <dialog ref={ref} aria-label={title} onCancel={event => { event.preventDefault(); onClose(); }} className="m-auto max-h-[90dvh] w-[calc(100%-24px)] max-w-xl overflow-auto rounded-3xl bg-white p-0 backdrop:bg-black/60">
    <header className="sticky top-0 z-10 flex items-center justify-between bg-white px-5 py-3"><h2 className="text-xl font-bold">{title}</h2><button type="button" onClick={onClose} className="min-h-11 px-3 font-bold">닫기</button></header>
    <div className="pb-5">{children}</div>
  </dialog>;
}
