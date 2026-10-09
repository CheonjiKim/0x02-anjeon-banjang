import { useEffect, useState } from 'react';
import { api, post } from '../lib/api.js';
import { AppButton, Panel, Screen } from '../components/ui.jsx';
import { readSession } from '../lib/session.js';
export default function Incidents({ worker = false }) {
 const [note,setNote]=useState(''); const [items,setItems]=useState([]); const [message,setMessage]=useState('');
 const workerId = readSession()?.worker_id || 2;
 const load=()=>api('/incidents'+(worker ? '?worker_id='+workerId : '')).then(setItems); useEffect(()=>{load()},[]);
 async function submit(e){e.preventDefault(); try{const r=await post('/incidents',{note,worker_id:worker ? workerId : 1});setNote('');setMessage('신고가 접수되어 '+r.points+'점을 받았습니다.');load()}catch(err){setMessage(err.message)}}
 async function follow(id){await post('/incidents/'+id+'/follow-up',{});load()}
 return <Screen title="아차사고 신고"><form onSubmit={submit}><Panel><p className="text-sm text-ink-sub">신고는 무사고 기록에 불이익을 주지 않으며 항상 가점이 있습니다.</p><textarea value={note} onChange={e=>setNote(e.target.value)} className="mt-3 min-h-28 w-full rounded-2xl border border-line p-3" placeholder="위험 상황이나 아차사고를 기록하세요."/><AppButton className="mt-3 w-full">신고하기</AppButton></Panel></form>{message&&<p className="mx-[22px] mt-3">{message}</p>}<Panel className="mt-4"><b>신고·후속조치</b>{items.map(item=><div key={item.id} className="mt-3 border-t border-line pt-3">{item.photo_url&&<img src={item.photo_url} alt="신고된 위험 요소" className="mb-3 h-40 w-full rounded-xl object-cover"/>}<p>{item.note||'내용 없음'}</p><small className="text-ink-sub">{item.follow_up_done?'조치 완료':'조치중'}</small>{!worker&&!item.follow_up_done&&<button onClick={()=>follow(item.id)} className="ml-3 text-sm font-bold text-brand-primary">조치 완료</button>}</div>)}</Panel></Screen>;
}
