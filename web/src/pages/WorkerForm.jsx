import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, post } from '../lib/api.js';
import { AppButton, Panel, Screen } from '../components/ui.jsx';
export default function WorkerForm() {
 const { taskId }=useParams(); const [reportText,setReportText]=useState(''); const [riskNote,setRiskNote]=useState(''); const [photo,setPhoto]=useState(null); const [message,setMessage]=useState('');
 if (taskId === 'missing') return <Screen title="오늘 작업"><Panel><p className="font-bold">관리자가 먼저 오늘 작업을 등록해야 합니다</p><p className="mt-2 text-sm text-ink-sub">관리자가 작업을 등록한 뒤 다시 출근해 주세요.</p></Panel></Screen>;
 async function submit(e){e.preventDefault(); try { const form=await post('/worker-forms',{task_id:Number(taskId),report_text:reportText,risk_note:riskNote,ppe_worn:true}); if(photo){const body=new FormData();body.append('photo',photo);await api('/worker-forms/'+form.id+'/photo',{method:'POST',body});} setMessage('마감 보고를 제출했습니다.'); } catch(err){setMessage(err.message)}}
 return <Screen title="작업 마감 보고"><form onSubmit={submit}><Panel><label>오늘 작업 내용<textarea value={reportText} onChange={e=>setReportText(e.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label><label className="mt-4 block">위험하거나 확인이 필요한 점<textarea value={riskNote} onChange={e=>setRiskNote(e.target.value)} className="mt-2 min-h-24 w-full rounded-2xl border border-line p-3" /></label><label className="mt-4 block">사진 첨부 (선택)<input type="file" accept="image/*" onChange={e=>setPhoto(e.target.files?.[0])} className="mt-2 block w-full" /></label></Panel><div className="mx-[22px] mt-5"><AppButton big className="w-full">마감 보고 제출</AppButton></div>{message&&<p className="mx-[22px] mt-3 text-center text-ink-sub">{message}</p>}</form></Screen>;
}
