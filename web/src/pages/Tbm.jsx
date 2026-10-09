import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { post, api } from '../lib/api.js';
import Recorder from '../components/Recorder.jsx';
import { AppButton, Panel, Screen } from '../components/ui.jsx';
export default function Tbm() {
 const navigate = useNavigate();
 const submitting = useRef(false); const [pending,setPending]=useState(false); const [savedPayload,setSavedPayload]=useState(null);
 const [task, setTask] = useState(useLocation().state?.task); const [text,setText]=useState(''); const [memo,setMemo]=useState(''); const [attendees,setAttendees]=useState(''); const [suggestions,setSuggestions]=useState([]); const [result,setResult]=useState(null); const [error,setError]=useState('');
 useEffect(()=>{const id=localStorage.getItem('banjang.taskId'); if(!task&&id) api('/tasks/'+id).then(setTask).catch(err=>setError(err.message)); if(id) api('/tbm-suggestions?task_id='+id).then((v)=>setSuggestions(v.suggestions)).catch(err=>setError(err.message));},[task]);
 if(!task) return <Screen title="TBM"><Panel><p>작업을 먼저 선택해 주세요.</p><AppButton className="mt-4 w-full" onClick={()=>navigate('/')}>작업 화면으로 이동</AppButton></Panel></Screen>;
 const payloadKey = JSON.stringify({task_id:task.id,transcript:text,memo,attendees});
 const unchanged = savedPayload === payloadKey;
 async function save(e){
   e.preventDefault();
   if(submitting.current || unchanged) return;
   if(!text.trim()) return setError('TBM 내용을 입력해 주세요.');
   submitting.current=true; setPending(true); setError(''); setResult(null);
   try { setResult(await post('/tbm',JSON.parse(payloadKey))); setSavedPayload(payloadKey); }
   catch(err){setError(err.message)}
   finally{submitting.current=false;setPending(false)}
 }

 return <Screen title="TBM 기록"><form onSubmit={save}><fieldset disabled={pending}><Panel><b>진행 내용</b><p className="mt-1 text-sm text-ink-sub">음성 전사 결과는 저장 전 직접 수정할 수 있습니다.</p><textarea value={text} onChange={e=>setText(e.target.value)} className="mt-3 min-h-32 w-full rounded-2xl border border-line p-3" placeholder="오늘 다룬 안전 수칙을 입력하세요."/><Recorder onTranscript={value=>setText(current=>current ? current+' '+value:value)}/><label className="mt-4 block text-sm font-bold">참석자<input value={attendees} onChange={e=>setAttendees(e.target.value)} className="mt-2 w-full rounded-xl border border-line p-3" placeholder="예: 김작업, 이근로" /></label><label className="mt-4 block text-sm font-bold">관리자 메모<textarea value={memo} onChange={e=>setMemo(e.target.value)} className="mt-2 min-h-20 w-full rounded-xl border border-line p-3" placeholder="추가 전달 사항 (선택)" /></label></Panel>{suggestions.length>0&&<Panel className="mt-4"><b>다음 TBM에 반영할 근로자 위험 메모</b>{suggestions.map((v,i)=><button type="button" key={i} onClick={()=>setText(current=>current ? current+' '+v:v)} className="mt-2 block text-left text-sm text-brand-primary">{v}</button>)}</Panel>}{error&&<p className="mx-[22px] mt-3 text-danger">{error}</p>}<div className="mx-[22px] mt-5"><AppButton big className="w-full" disabled={pending || unchanged}>{pending ? '저장 중…' : unchanged ? 'TBM 저장 완료' : 'TBM 저장·누락 확인'}</AppButton></div>{result&&unchanged&&<Panel className="mt-4"><p role="status" className="mb-3 font-bold text-ok">TBM 기록을 저장했습니다.</p><b>누락된 필수 수칙</b>{result.missing.length ? result.missing.map(v=><p key={v.code} className="mt-2">{v.title}</p>):<p className="mt-2 text-ok">누락된 필수 수칙이 없습니다.</p>}</Panel>}{result&&unchanged&&<div className="mx-[22px] mt-4 grid gap-2"><AppButton type="button" className="w-full" onClick={()=>navigate('/checklist')}>체크리스트 다시 보기</AppButton><AppButton type="button" outline className="w-full" onClick={()=>navigate('/evidence')}>사진 증빙으로 이동</AppButton></div>}</fieldset></form></Screen>;
}
