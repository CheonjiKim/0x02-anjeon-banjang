import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { AppButton, Panel, Screen } from '../components/ui.jsx';
export default function Review() {
 const [forms,setForms]=useState([]); const [items,setItems]=useState([]); const [message,setMessage]=useState(''); const taskId=localStorage.getItem('banjang.taskId');
 const load=()=>{if(taskId){api('/worker-forms?task_id='+taskId).then(setForms);api('/tasks/'+taskId).then(task=>setItems(task.checklist));}}; useEffect(load,[]);
 async function judge(formId,code){const body=new FormData();body.append('item_code',code);try{const r=await api('/worker-forms/'+formId+'/evidence',{method:'POST',body});setMessage(r.result==='confirmed'?'확인되어 '+r.points+'점이 반영되었습니다.':'사진 판정: '+r.result);load();}catch(e){setMessage(e.message)}}
 return <Screen title="마감 보고 확인"><Panel><p className="text-sm text-ink-sub">사진은 기록으로 보관하거나, 아래에서 수칙 증빙 판정을 요청할 수 있습니다.</p></Panel>{forms.map(form=><Panel key={form.id} className="mt-4"><p>{form.report_text||'텍스트 보고 없음'}</p><p className="mt-2 text-sm text-warn">{form.risk_note}</p>{form.photo_url&&<><img className="mt-3 w-full rounded-xl" src={form.photo_url}/><select className="mt-3 w-full rounded-xl border border-line p-3" onChange={e=>e.target.value&&judge(form.id,e.target.value)} defaultValue=""><option value="">기록용으로 유지</option>{items.map(item=><option key={item.code} value={item.code}>{item.title} 증빙 판정 요청</option>)}</select></>}</Panel>)}{message&&<p className="mx-[22px] mt-3">{message}</p>}</Screen>;
}
