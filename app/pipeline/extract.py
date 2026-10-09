"""문서에 지정된 키워드와 우선순위로 작업 조건과 근거를 추출한다."""

import re

from app.schemas import UNKNOWN, Conditions

_PATTERNS = {
    'work': [
        (r'용접|용단|가스절단', '용접·용단'),
        (r'원형톱|둥근톱|톱절단|절단', '절단·원형톱'),
        (r'도장|페인트|방수|우레탄', '도장·방수'),
        (r'사다리|말비계', '사다리·말비계'),
    ],
    'height': [
        (r'(?<![\d.\-])(\d+(?:\.\d+)?)\s*(?:m|미터)\s*(?:높이|위|상공|에서)?', 'm'),
        (r'지상|바닥', '지상'),
    ],
    'floor': [(r'(\d+)\s*층', '층')],
    'flammable': [
        (r'톱밥', '톱밥'),
        (r'합판|스티로폼|단열재|우레탄|종이|박스|페인트|시너|목재|각재', None),
        (r'(?:가연물|불에\s*타는\s*(?:물건|것)|인화물)\s*(?:이|은|는)?\s*(?:없\w*|안\s*보\w*)', '없음'),
    ],
    'ventilation': [
        (r'환기(?:\s*상태)?(?:가|는|이)?\s*(?:불량|미흡|안\s*됨|안\s*돼|되지\s*않\w*|안되\w*|없\w*|부족\w*)|환기\s*잘\s*안\s*됨|환풍기(?:가|는|이)?\s*(?:아직\s*)?(?:미설치|없\w*)|창문(?:이|은|는)?\s*없\w*|밀폐|지하|탱크|맨홀|피트', '불량'),
        (r'환기(?:\s*상태)?(?:가|는|이)?\s*(?:양호|잘\s*됨|잘\s*돼|가능|되고\s*있\w*)|개방된\s*공간|야외|옥외', '양호'),
    ],
    'nearby_people': [
        (r'(\d+)\s*명', '명'),
        (r'주변\s*(?:사람|인원|작업자)(?:이|은|는)?\s*(?:없\w*|안\s*보\w*)|잡아\s*줄\s*사람(?:이|은|는)?\s*없\w*|혼자|단독', '없음'),
        (r'옆에\s*작업자|주변(?:에)?\s*(?:사람|인원|작업자)(?:이|은|는)?\s*(?:많\w*|있\w*)|주변\s*작업자|동시\s*작업|아래\s*작업', '있음'),
    ],
    'place': [
        (r'창문(?:이|은|는)?\s*없\w*|밀폐(?:된)?\s*공간', '밀폐 공간'),
        (r'지하\s*주차장|지하실|지하|옥상|외부|실내|탱크|맨홀|피트|터널|계단실|기계실', None),
    ],
}


def extract_with_spans(text: str) -> tuple[Conditions, dict[str, str]]:
    """조건 일곱 개와 실제 매치된 원문 구절을 돌려준다."""
    values = {}
    spans = {}
    for key, patterns in _PATTERNS.items():
        values[key] = UNKNOWN
        for pattern, value in patterns:
            match = re.search(pattern, text)
            if match is None:
                continue
            # A negated low-risk phrase is not evidence for lowering a check.
            if value in {'없음', '양호', '지상'} and re.match(
                r'\s*(?:(?:작업)?(?:이|은|는|가)?\s*(?:아니|아님|아닌)|하지\s*(?:않|못)|하지는\s*않)',
                text[match.end():],
            ):
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
