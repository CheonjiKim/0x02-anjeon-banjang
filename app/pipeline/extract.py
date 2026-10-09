"""문서에 지정된 키워드와 우선순위로 작업 조건과 근거를 추출한다."""

import re

from app.schemas import UNKNOWN, Conditions

_PATTERNS = {
    'work': [
        (r'그라인더|절단|연마', '그라인더·절단'),
        (r'용접|용단|가스절단', '용접·용단'),
    ],
    'height': [
        (r'(\d+)\s*층', '층'),
        (r'(\d+)\s*m|(\d+)\s*미터', 'm'),
        (r'지상|바닥', '지상'),
    ],
    'flammable': [
        (r'합판|스티로폼|단열재|우레탄|종이|박스|페인트|시너', None),
        (r'가연물\s*없\w*|주변\s*없\w*|아무것도\s*없\w*', '없음'),
        (r'\S*없\S*', '없음'),
    ],
    'ventilation': [
        (r'환기\s*(양호|잘|됨|가능)|개방|야외|옥외', '양호'),
        (r'밀폐|지하|탱크|맨홀|피트', '불량'),
        (r'환기', '양호'),
    ],
    'nearby_people': [
        (r'(\d+)\s*명', '명'),
        (r'혼자|단독', '없음'),
        (r'옆에\s*작업자|주변\s*작업자|동시\s*작업|아래\s*작업', '있음'),
    ],
    'place': [
        (r'지하\s*주차장|지하실|지하|옥상|외부|실내|탱크|맨홀|피트|터널|계단실|기계실', None),
    ],
}


def extract_with_spans(text: str) -> tuple[Conditions, dict[str, str]]:
    """조건 여섯 개와 실제 매치된 원문 구절을 돌려준다."""
    values = {}
    spans = {}
    for key, patterns in _PATTERNS.items():
        values[key] = UNKNOWN
        for pattern, value in patterns:
            match = re.search(pattern, text)
            if match is None:
                continue
            if value in ('층', 'm', '명'):
                number = next(group for group in match.groups() if group is not None)
                values[key] = number + value
            else:
                values[key] = value if value is not None else match.group(0)
            spans[key] = match.group(0)
            break
    return Conditions(**values), spans


def extract_conditions(text: str) -> Conditions:
    """키워드로 추출한 조건만 돌려준다."""
    return extract_with_spans(text)[0]


def evidence_spans(text: str, c: Conditions) -> dict[str, str]:
    """키워드 추출 결과와 전달된 조건 값이 같은 근거만 돌려준다."""
    extracted, spans = extract_with_spans(text)
    return {key: span for key, span in spans.items() if getattr(extracted, key) == getattr(c, key)}
