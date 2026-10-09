"""사진 판정 인터페이스를 제공하는 mock 판정기다."""

from app.schemas import Judgement


def judge_evidence(item_title: str, photo: bytes, forced: str | None = None) -> Judgement:
    """시연용 판정을 반환하며 사진 분석이나 점수 계산은 수행하지 않는다."""
    result = forced or 'confirmed'
    if result == 'confirmed':
        return Judgement(result=result, observed=f'{item_title}이(가) 사진에서 확인돼요')
    if result == 'not_visible':
        return Judgement(
            result=result,
            observed=f'{item_title} 관련 장면이 보이지 않아요',
            retake_hint='작업 위치와 해당 설비가 함께 보이게 다시 찍어 주세요',
        )
    return Judgement(
        result='uncertain',
        observed='사진만으로는 판단하기 어려워요',
        retake_hint='반장님이 직접 확인해 주세요',
    )
