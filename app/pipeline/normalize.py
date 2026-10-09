"""규칙 평가 전에 조건의 허용 값·원문 근거·지시 문장을 확인한다."""

import re

from app.schemas import UNKNOWN, Conditions

WORKS = {'용접·용단', '절단·원형톱', '도장·방수', '사다리·말비계'}
FLAMMABLES = {'합판', '스티로폼', '단열재', '우레탄', '종이', '박스', '페인트', '시너', '없음'}
PLACES = {'지하 주차장', '지하주차장', '지하실', '지하', '옥상', '외부', '실내', '탱크', '맨홀', '피트', '터널', '계단실', '기계실'}
LOWERING = {'flammable': '없음', 'ventilation': '양호', 'nearby_people': '없음', 'height': '지상'}


def looks_like_instruction(text) -> bool:
    return re.search(
        r'처리\s*해|처리\s*하|으로\s*해\s*줘|로\s*해\s*줘|무시|판정\s*해|체크\s*해|넘어가|안전\s*으로|빼\s*줘|없다고\s*(해|쳐)',
        text,
    ) is not None


def normalize(c: Conditions, evidence: dict[str, str], text: str) -> tuple[Conditions, dict[str, str]]:
    values = {}
    dropped = {}
    instruction = looks_like_instruction(text)
    if re.fullmatch(r'\d+층', c.height):
        # 층수는 작업 층일 뿐 발판에서의 실제 높이가 아니다.
        if c.floor == UNKNOWN and c.height in text:
            c = c.model_copy(update={'floor': c.height, 'height': UNKNOWN})
        else:
            c = c.model_copy(update={'height': UNKNOWN})
        dropped['height'] = '층수만으로 작업 높이를 판단하지 않음'
    for key, original in c.model_dump().items():
        value = original.strip() or UNKNOWN
        allowed = {
            'work': value in WORKS,
            'height': re.fullmatch(r'\d+(?:\.\d+)?m|지상', value) is not None,
            'floor': re.fullmatch(r'\d+층', value) is not None,
            'flammable': value in FLAMMABLES,
            'ventilation': value in {'양호', '불량'},
            'nearby_people': re.fullmatch(r'\d+명|있음|없음', value) is not None,
            'place': value in PLACES,
        }[key]
        if value != UNKNOWN and not allowed:
            dropped[key] = f"허용 목록 밖의 값 '{value}'"
            value = UNKNOWN
        if value == LOWERING.get(key):
            span = evidence.get(key, '').strip()
            if instruction:
                dropped[key] = '작업 문장에 지시가 섞여 있어 안전을 낮추는 값을 받지 않음'
                value = UNKNOWN
            elif not span or span not in text:
                dropped[key] = f"안전을 낮추는 값 '{value}'의 원문 근거가 없음"
                value = UNKNOWN
            else:
                # 원문에 같은 단어가 있어도 다른 조건의 부정 표현이면 근거가 아니다.
                from app.pipeline.extract import extract_with_spans
                extracted, spans = extract_with_spans(text)
                # A longer verbatim quote is valid if it contains the same
                # contextual match. Recheck the quote itself as well as the
                # whole input, so an unrelated "없음" cannot lower this field.
                quoted, quoted_spans = extract_with_spans(span)
                if (getattr(extracted, key) != value or getattr(quoted, key) != value
                        or not spans.get(key) or spans[key] not in span
                        or quoted_spans.get(key) != spans[key]):
                    dropped[key] = f"안전을 낮추는 값 '{value}'의 문맥 근거가 없음"
                    value = UNKNOWN
        values[key] = value
    return Conditions(**values), dropped
