import { useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { AppButton } from './ui.jsx';
import { transcribe } from '../lib/api.js';

export default function Recorder({ onTranscript }) {
  const recorder = useRef(null);
  const chunks = useRef([]);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function start() {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const media = new MediaRecorder(stream);
      chunks.current = [];
      media.ondataavailable = (event) => chunks.current.push(event.data);
      media.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop()); setBusy(true);
        try { const result = await transcribe(new Blob(chunks.current, { type: media.mimeType || 'audio/webm' })); onTranscript(result.text); }
        catch (err) { setError(err.message); } finally { setBusy(false); }
      };
      recorder.current = media; media.start(); setRecording(true);
    } catch (_) { setError('마이크 권한을 허용한 뒤 다시 시도해 주세요.'); }
  }
  function stop() { recorder.current?.stop(); setRecording(false); }
  return <div className="mt-3"><AppButton outline disabled={busy} onClick={recording ? stop : start} className="w-full">{recording ? <><Square className="mr-2 inline" size={18} />녹음 중지</> : <><Mic className="mr-2 inline" size={18} />{busy ? '음성을 글로 바꾸는 중…' : '음성으로 입력'}</>}</AppButton>{error && <p role="alert" className="mt-2 text-sm text-danger">{error}</p>}</div>;
}
