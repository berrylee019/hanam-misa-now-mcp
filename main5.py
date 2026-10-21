"""하남미사 지금갈곳 - 주차·대기·키즈 MCP 서버

데이터 출처
- 장소 검색/주변 주차장: 카카오 로컬 API (keyword / category PK6)
- 대기 요약: 카카오 검색 API(블로그) 최근 글에서 '웨이팅/대기' 언급을 추출 (실시간 아님)
- 운영사 주차 정책: PARKING_POLICY (운영사 공지 기준, 방문 전 확인 필요)

환경변수: KAKAO_REST_API_KEY (필수, 코드에 키를 넣지 마세요)
"""
import os
import re
import statistics
import time
from datetime import datetime, timedelta, timezone

import requests
import uvicorn
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

mcp = FastMCP(
    "하남미사 지금갈곳 - 주차·대기·키즈",
    instructions=(
        "하남시 미사역·미사강변·미사호수공원·스타필드 하남 일대 전용 도구입니다. "
        "이 지역의 식당/카페/키즈카페 검색, 주변 주차장 조회, 최근 후기 기반 웨이팅 요약을 제공합니다. "
        "실시간 대기·만차 정보는 제공하지 않으며, 응답에 없는 정보는 추측하지 말고 매장 확인을 안내하세요."
    ),
)

KAKAO_BASE = "https://dapi.kakao.com/v2"
KST = timezone(timedelta(hours=9))

# 기준점: 카카오로 좌표를 조회하고, 실패 시 아래 대략 좌표를 사용
ANCHORS = {
    "미사역": (127.1928, 37.5612),
    "스타필드": (127.2236, 37.5453),
    "미사호수공원": (127.1960, 37.5580),
    "미사강변": (127.1893, 37.5640),
    "미사 카페거리": (127.1893, 37.5640),
}
DEFAULT_ANCHOR = "미사역"

# 하남·미사 외 지역을 단독으로 물으면 안내
OTHER_REGIONS = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "제주",
                 "강남", "해운대", "판교", "수원", "성남", "용인"]
LOCAL_WORDS = ["하남", "미사", "스타필드"]

# 운영사가 공지한 주차 정책 (방문 전 공식 채널로 재확인 필요)
# 값 변경 시 checked 날짜도 갱신하세요.
# 공식 페이지에서 직접 확인한 값만 넣으세요. 공지(notices)는 기간이 끝나면 자동으로 숨겨집니다.
# from/until: "YYYY-MM-DD" (None이면 기간 제한 없음). 공지가 바뀌면 이 표만 수정하세요.
PARKING_POLICY: dict = {
    "스타필드": {
        "match": ["스타필드", "미사대로 750"],   # 장소명 또는 주소에 포함되면 적용
        "summary": "주차요금 무료 (스타필드 하남 공식 주차 안내 기준)",
        "source": "https://www.starfield.co.kr/hanam/about/parkingInfo.do",
        "checked": "2026-10-21",
        "notices": [
            {"text": "지상 주차장 및 전기차 충전소(4F) 이용 불가", "from": "2026-10-12", "until": "2026-10-22"},
            {"text": "메가박스 조조·심야 영화 관람 시 야외주차장 이용", "from": "2026-10-12", "until": "2027-01-22"},
            {"text": "10시 이전, 23시 이후 실내 주차장 이용 불가 (주차장 공사)", "from": "2026-10-12", "until": "2027-01-22"},
            {"text": "트레이더스 홀세일 클럽 이용 고객은 지하주차장 이용", "from": None, "until": None},
        ],
    },
}


def policy_lines(place_name: str, query: str, address: str) -> list:
    today = datetime.now(KST).strftime("%Y-%m-%d")
    out = []
    for v in PARKING_POLICY.values():
        hay = f"{place_name} {query} {address}"
        if not any(m in hay for m in v["match"]):
            continue
        out.append(f"- 운영사 안내: {v['summary']} (출처: {v['source']}, 확인일: {v['checked']})")
        active = [n for n in v["notices"]
                  if (not n.get("from") or n["from"] <= today) and (not n.get("until") or today <= n["until"])]
        for n in active:
            period = f" ({n['from']} ~ {n['until']})" if n.get("from") and n.get("until") else ""
            out.append(f"- 이용 공지: {n['text']}{period}")
        break
    return out

# ---------------------------------------------------------------- 공통 유틸
_cache: dict = {}
CACHE_TTL = 300


def _key() -> str:
    k = os.environ.get("KAKAO_REST_API_KEY")
    if not k:
        raise RuntimeError("서버에 KAKAO_REST_API_KEY 환경변수가 설정되지 않았습니다.")
    return k


def kakao_get(path: str, params: dict) -> dict:
    cache_key = (path, tuple(sorted(params.items())))
    hit = _cache.get(cache_key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    res = requests.get(
        f"{KAKAO_BASE}{path}",
        headers={"Authorization": f"KakaoAK {_key()}"},
        params=params,
        timeout=5,
    )
    res.raise_for_status()
    data = res.json()
    _cache[cache_key] = (time.time(), data)
    return data


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").replace("&quot;", '"').replace("&amp;", "&").strip()


def resolve_anchor(name: str):
    """기준점 좌표 (x, y)"""
    try:
        docs = kakao_get("/local/search/keyword.json",
                         {"query": f"하남 {name}", "size": 1}).get("documents", [])
        if docs:
            return float(docs[0]["x"]), float(docs[0]["y"])
    except Exception:
        pass
    return ANCHORS.get(name, ANCHORS[DEFAULT_ANCHOR])


def detect_anchor(text: str) -> str:
    for name in ANCHORS:
        if name in text:
            return name
    if "스타필드" in text:
        return "스타필드"
    return DEFAULT_ANCHOR


def nearby_parking(x: float, y: float, radius: int = 300, size: int = 3):
    docs = kakao_get("/local/search/category.json", {
        "category_group_code": "PK6", "x": x, "y": y,
        "radius": radius, "sort": "distance", "size": size,
    }).get("documents", [])
    return [{
        "name": d["place_name"],
        "distance_m": int(d.get("distance") or 0),
        "address": d.get("road_address_name") or d.get("address_name"),
        "url": d.get("place_url"),
    } for d in docs]


def fmt_parking(lots) -> str:
    if not lots:
        return "반경 내 등록된 주차장 정보 없음(매장 문의 필요)"
    return "; ".join(f"{l['name']}({l['distance_m']}m)" for l in lots)


# ---------------------------------------------------------------- 질의 해석
KIDS_WORDS = ["키즈", "아이", "아기", "유모차", "어린이", "아이랑", "아이와"]
PET_WORDS = ["애견", "반려견", "강아지", "반려동물", "펫"]
PARK_WORDS = ["주차"]
NOISE_WORDS = ["하남", "미사역", "미사강변", "미사호수공원", "미사", "스타필드", "카페거리",
               "주변", "근처", "에서", "찾아줘", "검색", "해줘", "좀", "있어", "알려줘",
               "추천", "가능한", "되는", "무료", "곳", "지금", "동반", "갈 수", "갈수",
               "들어갈", "대기", "없는", "있는", "랑", "와", "이랑"]


def parse_query(query: str):
    kids = any(w in query for w in KIDS_WORDS)
    pet = any(w in query for w in PET_WORDS)
    parking = any(w in query for w in PARK_WORDS)
    core = re.sub(r"\d+\s*곳", " ", query)
    for w in KIDS_WORDS + PET_WORDS + PARK_WORDS + NOISE_WORDS:
        core = core.replace(w, " ")
    core = " ".join(core.split())
    return core, kids, pet, parking


# ---------------------------------------------------------------- Tool 1
@mcp.tool(
    name="search_hanam_places",
    description=(
        "하남 미사(미사역·미사강변·미사호수공원·스타필드 하남) 지역 전용 검색 도구입니다. 이 일대의 "
        "식당/카페/키즈카페/애견동반 장소를 카카오 로컬 API로 검색합니다. 검색어의 메뉴·업종(예: 파스타, 브런치, 카페)과 "
        "아이동반(키즈)·애견동반·주차 조건을 반영하며, 기준점에서 가까운 순으로 정렬합니다. "
        "주차 조건이 있으면 매장 반경 300m 내 주차장도 함께 알려줍니다. "
        "아이/반려견 동반 여부는 검색 키워드·업종 기반이라 방문 전 매장 확인이 필요합니다."
    ),
)
def search_hanam_places(
    query: str,
    kids_friendly: bool = False,
    pet_friendly: bool = False,
    parking_needed: bool = False,
    limit: int = 5,
) -> str:
    """query: 자연어 검색어 (예: '미사역 근처 파스타 식당', '스타필드 키즈카페')
    kids_friendly: 아이 동반 가능한 곳 우선
    pet_friendly: 반려견 동반 가능한 곳 우선
    parking_needed: 주변 주차장 정보 포함
    limit: 결과 수 (1~10)
    """
    query = (query or "").strip()
    if not query:
        return "검색어를 입력해주세요. 예: '미사역 근처 아이랑 갈 수 있는 식당'"

    if any(r in query for r in OTHER_REGIONS) and not any(l in query for l in LOCAL_WORDS):
        return ("이 서비스는 하남 미사 지역(미사역, 미사강변, 미사호수공원, 스타필드 하남)만 지원합니다. "
                "예: '미사 키즈카페', '스타필드 근처 브런치'")

    limit = max(1, min(int(limit), 10))
    core, kids, pet, parking = parse_query(query)
    kids, pet, parking = kids or kids_friendly, pet or pet_friendly, parking or parking_needed
    anchor = detect_anchor(query)

    try:
        x, y = resolve_anchor(anchor)
        base = core or ("카페" if ("카페" in query) else "맛집")
        queries = []  # (검색어, 가산점)
        if kids and "키즈" not in base:
            queries.append((f"하남 {anchor} {base} 키즈", 2))
            queries.append((f"하남 {anchor} 키즈카페" if not core else f"하남 {anchor} {base} 아이동반", 1))
        if pet and "애견" not in base:
            queries.append((f"하남 {anchor} {base} 애견동반", 2))
        queries.append((f"하남 {anchor} {base}", 0))

        found: dict = {}
        for q, bonus in queries:
            docs = kakao_get("/local/search/keyword.json", {
                "query": q, "x": x, "y": y, "radius": 3000, "size": 15, "sort": "accuracy",
            }).get("documents", [])
            for d in docs:
                addr = d.get("road_address_name") or d.get("address_name") or ""
                if "하남" not in addr:
                    continue
                if d.get("category_group_code") == "PK6" and not ("주차" in query):
                    continue
                score = bonus
                text = d["place_name"] + d.get("category_name", "")
                if kids and "키즈" in text:
                    score += 2
                if pet and ("애견" in text or "반려" in text):
                    score += 2
                prev = found.get(d["id"])
                if prev is None or score > prev[0]:
                    found[d["id"]] = (score, d)

        if not found:
            return (f"'{query}' 조건에 맞는 하남 미사 장소를 찾지 못했습니다. "
                    "업종이나 키워드를 바꿔 다시 시도해주세요. (예: 카페, 식당, 키즈카페)")

        pool = sorted(found.values(),
                      key=lambda t: (-t[0], int(t[1].get("distance") or 10**9)))
        evidence: dict = {}
        if kids:
            from concurrent.futures import ThreadPoolExecutor
            cand = pool[:10]
            with ThreadPoolExecutor(max_workers=5) as ex:
                counts = list(ex.map(lambda t: kids_evidence(t[1]["place_name"]), cand))
            evidence = {t[1]["id"]: c for t, c in zip(cand, counts)}
            pool = sorted(pool, key=lambda t: (-t[0], -evidence.get(t[1]["id"], 0),
                                               int(t[1].get("distance") or 10**9)))
        ranked = pool[:limit]

        notes = []
        if kids:
            notes.append("아이동반")
        if pet:
            notes.append("애견동반")
        if parking:
            notes.append("주차")
        cond = f" / 조건: {', '.join(notes)}" if notes else ""
        lines = [f"[하남미사 검색] 기준점: {anchor} / 키워드: '{base}'{cond} / {len(ranked)}곳"]

        for i, (score, d) in enumerate(ranked, 1):
            addr = d.get("road_address_name") or d.get("address_name")
            dist = f"{d['distance']}m" if d.get("distance") else "-"
            cat = d.get("category_name", "").split(">")[-1].strip()
            line = f"{i}. {d['place_name']} ({cat}) | {addr} | 기준점에서 {dist}"
            if d.get("phone"):
                line += f" | ☎ {d['phone']}"
            line += f" | {d.get('place_url', '')}"
            if kids:
                if "키즈" in d["place_name"] + d.get("category_name", ""):
                    line += " | 아이동반: 키즈 업종/키워드 일치"
                n = evidence.get(d["id"])
                if n is not None:
                    line += (f" | 아이동반 후기 언급 {n}건(최근 6개월 블로그)" if n
                             else " | 아이동반 후기 언급 확인되지 않음(매장 확인 필요)")
            if pet and score >= 2 and any(w in d["place_name"] + d.get("category_name", "") for w in ["애견", "반려"]):
                line += " | 애견동반: 애견 업종/키워드 일치"
            if parking:
                lots = nearby_parking(float(d["x"]), float(d["y"]))
                line += f" | 주변 주차장(300m): {fmt_parking(lots)}"
            lines.append(line)

        lines.append("출처: 카카오 로컬 API, 카카오 검색 API(블로그). 위에 표시된 항목 외의 정보"
                     "(주차 가능 여부·아이 메뉴·유아의자 보유 등)는 확인되지 않았으므로 추측하지 말고 "
                     "방문 전 매장에 확인하도록 안내하세요.")
        return "\n".join(lines)
    except Exception as e:
        return f"검색 중 오류가 발생했습니다: {e}"


# ---------------------------------------------------------------- Tool 2
GENERIC_WORDS = ["식당", "카페", "맛집", "음식점", "레스토랑", "가게"]


def _candidates(place: str, size: int = 5):
    anchor = detect_anchor(place)
    x, y = resolve_anchor(anchor)
    docs = kakao_get("/local/search/keyword.json", {
        "query": f"하남 {place}", "x": x, "y": y, "radius": 10000, "size": 15,
    }).get("documents", [])
    out = []
    for d in docs:
        addr = d.get("road_address_name") or d.get("address_name") or ""
        if "하남" in addr and d.get("category_group_code") != "PK6":
            out.append(d)
    return out[:size]


def _is_generic(place: str) -> bool:
    """'스타필드 하남 식당'처럼 특정 상호가 없는 입력인지"""
    if not any(g in place for g in GENERIC_WORDS):
        return False
    rest = place
    for w in LOCAL_WORDS + ["미사역", "미사강변", "미사호수공원", "근처", "주변"] + GENERIC_WORDS:
        rest = rest.replace(w, " ")
    return not rest.strip()


def _find_place(place: str):
    """이름으로 하남 미사 일대 장소 1곳 조회 (주차장 제외 첫 결과)"""
    cands = _candidates(place, size=1)
    return cands[0] if cands else None


def _ask_specific(place: str) -> str:
    cands = _candidates(place, size=5)
    names = ", ".join(c["place_name"] for c in cands) or "(후보 없음)"
    return (f"'{place}'는 특정 매장이 아니라 종류만 지정된 입력입니다. 정확한 상호명으로 다시 요청해주세요. "
            f"후보: {names}. (search_hanam_places로 먼저 매장을 검색할 수 있습니다.)")


def kids_evidence(name: str) -> int:
    """최근 6개월 블로그 후기 중 아이 동반 관련 언급 건수"""
    try:
        since = datetime.now(KST) - timedelta(days=183)
        docs = kakao_get("/search/blog", {
            "query": f"{name} 아이랑 유아의자", "sort": "recency", "size": 30,
        }).get("documents", [])
        n = 0
        for doc in docs:
            try:
                if datetime.fromisoformat(doc["datetime"]) < since:
                    continue
            except Exception:
                continue
            text = strip_tags(doc.get("title", "") + " " + doc.get("contents", ""))
            if name.split()[0] in text and any(w in text for w in
                    ["유아의자", "아기의자", "유아식기", "아이랑", "아이와", "유모차", "키즈", "아기랑"]):
                n += 1
        return n
    except Exception:
        return 0


@mcp.tool(
    name="get_parking_info",
    description=(
        "하남 미사 지역 전용. 장소(매장/시설) 이름으로 해당 위치와 반경 500m 내 주차장(이름·거리·주소)을 카카오 로컬 API로 조회합니다. "
        "스타필드 등 운영사 공지 정책이 있으면 함께 안내합니다. 실시간 주차 가능 대수는 제공하지 않습니다."
    ),
)
def get_parking_info(place: str) -> str:
    """place: 장소명 (예: '스타필드 하남', '미사호수공원', '○○카페')"""
    place = (place or "").strip()
    if not place:
        return "장소명을 입력해주세요."
    try:
        if _is_generic(place):
            return _ask_specific(place)
        d = _find_place(place)
        if not d:
            return f"'{place}'을(를) 하남 미사 일대에서 찾지 못했습니다. 정확한 상호명으로 다시 입력해주세요."

        lots = nearby_parking(float(d["x"]), float(d["y"]), radius=500, size=5)
        lines = [f"[주차 정보] {d['place_name']} ({d.get('road_address_name') or d.get('address_name')})"]

        lines += policy_lines(d["place_name"], place,
                              d.get("road_address_name") or d.get("address_name") or "")

        if lots:
            lines.append("- 반경 500m 내 주차장 (가까운 순):")
            for l in lots:
                lines.append(f"  · {l['name']} {l['distance_m']}m | {l['address']} | {l['url']}")
        else:
            lines.append("- 반경 500m 내 등록된 주차장이 없습니다. 매장에 직접 문의해주세요.")
        lines.append("출처: 카카오 로컬 API. 요금·무료시간·만차 여부는 이 서버가 제공하지 않으므로 "
                     "추측하지 말고 현장/운영사 확인을 안내하세요.")
        return "\n".join(lines)
    except Exception as e:
        return f"주차 정보 조회 중 오류가 발생했습니다: {e}"


# ---------------------------------------------------------------- Tool 3
WAIT_WORDS = ["웨이팅", "대기", "줄", "기다", "캐치테이블", "테이블링"]
MIN_PATTERN = re.compile(r"(\d{1,3})\s*분")


@mcp.tool(
    name="get_waiting_summary",
    description=(
        "하남 미사 지역 전용. 장소 이름으로 최근 6개월 블로그 후기에서 웨이팅/대기 언급을 모아 요약합니다 "
        "(언급 건수, 후기에 적힌 대기시간 범위, 원문 링크). "
        "실시간 대기 현황이 아니라 최근 후기 기반 참고 정보입니다."
    ),
)
def get_waiting_summary(place: str) -> str:
    """place: 장소명 (예: '스타필드 하남 ○○식당')"""
    place = (place or "").strip()
    if not place:
        return "장소명을 입력해주세요."
    try:
        if _is_generic(place):
            return _ask_specific(place)
        d = _find_place(place)
        name = d["place_name"] if d else place
        since = datetime.now(KST) - timedelta(days=183)

        docs = kakao_get("/search/blog", {
            "query": f"{name} 웨이팅", "sort": "recency", "size": 30,
        }).get("documents", [])

        mentions, minutes = [], []
        for doc in docs:
            try:
                dt = datetime.fromisoformat(doc["datetime"])
            except Exception:
                continue
            if dt < since:
                continue
            text = strip_tags(doc.get("title", "") + " " + doc.get("contents", ""))
            if not any(w in text for w in WAIT_WORDS):
                continue
            sentences = re.split(r"(?<=[.!?…])\s+|\n", text)
            snippet = next((s for s in sentences if any(w in s for w in WAIT_WORDS)), text[:80])
            for s in sentences:
                if any(w in s for w in WAIT_WORDS):
                    minutes += [int(m) for m in MIN_PATTERN.findall(s) if 0 < int(m) <= 180]
            mentions.append((dt, snippet[:90], doc.get("url", "")))

        header = f"[대기 요약] {name} (최근 6개월 블로그 후기 기준, 실시간 아님)"
        if not mentions:
            return (f"{header}\n대기 관련 언급을 찾지 못했습니다. 대기가 없다는 뜻은 아니므로 "
                    "캐치테이블/테이블링 또는 매장 전화로 확인하세요.\n출처: 카카오 검색 API(블로그)")

        lines = [header, f"- 대기 언급 후기: {len(mentions)}건 (조회 {len(docs)}건 중)"]
        if minutes:
            lines.append(f"- 후기에 적힌 대기시간: {min(minutes)}~{max(minutes)}분 "
                         f"(중앙값 {int(statistics.median(minutes))}분, 언급 {len(minutes)}건)")
        else:
            lines.append("- 후기에 구체적인 대기시간(분) 언급은 없었습니다.")
        lines.append("- 최근 후기 발췌:")
        for dt, snip, url in sorted(mentions, reverse=True)[:3]:
            lines.append(f"  · {dt.strftime('%Y-%m-%d')} \"{snip}\" {url}")
        lines.append("출처: 카카오 검색 API(블로그). 요일·시간대에 따라 크게 달라질 수 있습니다.")
        return "\n".join(lines)
    except Exception as e:
        return f"대기 정보 조회 중 오류가 발생했습니다: {e}"


# ---------------------------------------------------------------- 서버
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


@mcp.custom_route("/", methods=["GET"])
async def root(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


app = mcp.http_app(path="/mcp")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
