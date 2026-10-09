import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { post, api } from '../lib/api.js';
import Recorder from '../components/Recorder.jsx';
import { AppButton, Panel, Screen } from '../components/ui.jsx';
export default function Tbm() {
 const [task, setTask] = useState(useLocation().state?.task); const [text,setText]=useState(''); const [suggestions,setSuggestions]=useState([]); const [result,setResult]=useState(null); const [error,setError]=useState('');
 useEffect(()=>{const id=localStorage.getItem('banjang.taskId'); if(!task&&id) api('/tasks/'+id).then(setTask); if(id) api('/tbm-suggestions?task_id='+id).then((v)=>setSuggestions(v.suggestions));},[task]);
 if(!task) return <Screen title="TBM"><Panel>작업을 먼저 선택해 주세요.</Panel></Screen>;
 async function save(e){e.preventDefault(); try{setResult(await post('/tbm',{task_id:task.id,transcript:text,memo:text}));}catch(err){setError(err.message)}}
 return <Screen title="TBM 기록"><form onSubmit={save}><Panel><b>진행 내용</b><textarea value={text} onChange={e=>setText(e.target.value)} className="mt-3 min-h-32 w-full rounded-2xl border border-line p-3" placeholder="오늘 다룬 안전 수칙을 입력하세요."/><Recorder onTranscript={value=>setText(current=>current ? current+' '+value:value)}/></Panel>{suggestions.length>0&&<Panel className="mt-4"><b>근로자 위험 메모</b>{suggestions.map((v,i)=><button type="button" key={i} onClick={()=>setText(current=>current ? current+' '+v:v)} className="mt-2 block text-left text-sm text-brand-primary">{v}</button>)}</Panel>}{error&&<p className="mx-[22px] mt-3 text-danger">{error}</p>}<div className="mx-[22px] mt-5"><AppButton big className="w-full">TBM 저장·누락 확인</AppButton></div>{result&&<Panel className="mt-4"><b>누락된 필수 수칙</b>{result.missing.length ? result.missing.map(v=><p key={v.code} className="mt-2">{v.title}</p>):<p className="mt-2 text-ok">누락된 필수 수칙이 없습니다.</p>}</Panel>}</form></Screen>;
}
