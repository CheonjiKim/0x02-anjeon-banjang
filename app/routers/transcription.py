from fastapi import APIRouter, File, HTTPException, UploadFile

from app.llm.base import LLMError
from app.llm.transcribe import transcribe_audio
from app.schemas import TranscriptionOut


router = APIRouter(prefix='/api/transcriptions', tags=['transcriptions'])
ALLOWED_SUFFIXES = {'.webm', '.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.ogg', '.flac'}


@router.post('', response_model=TranscriptionOut)
async def transcribe(audio: UploadFile = File(...)):
    name = audio.filename or 'recording.webm'
    suffix = '.' + name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=422, detail='지원하지 않는 음성 파일 형식입니다.')
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=422, detail='비어 있는 음성 파일입니다.')
    try:
        return TranscriptionOut(text=transcribe_audio(name, content, audio.content_type))
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
