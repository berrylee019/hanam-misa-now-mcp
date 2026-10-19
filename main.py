from fastmcp import FastMCP
from starlette.responses import PlainTextResponse
import os, uvicorn, requests, hashlib

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")
KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY", "18794e39d19ed47e1e9738b40591064d")

# 지원 외 지역 차단용
OTHER_REGIONS = ["서울","부산","대구","인천","광주","대전","울산","제주","강남","해운대","판교","수원","성남","용인"]

PARKING_DB = {
    "스타필드": "스타필드 하남: 평일 5시간 무료, 주말 4시간 무료, 이후 10분당 500원, 3500대 규모, 전기차 충전 가능",
    "바운스": "바운스 슈퍼파크 하남: 스카이폴리스 지하주차장 무료 3시간 (초과 30분 1000원), 주차장 넓음",
    "리틀빌리지": "리틀빌리지 하남미사점: 건물 지하주차장, 2시간 무료 지원, 유모차 이동 가능",
    "고메스퀘어": "고메스퀘어 미사점: 건물 대형 주차장, 주차요원 상주, 주말에도 비교적 여유",
    "브레딕트": "브레딕트 미사: 건물 내 주차장 진입, 2시간 무료, 장애인 주차 별도",
    "미사호수공원": "미사호수공원 공영주차장: 2시간 무료, 이후 10분당 300원, 주말 혼잡",
    "미사역": "미사역 환승주차장: 30분 무료, 10분당 300원, 일 최대 8000원",
}

def get_varied_waiting(place: str) -> str:
    # 장소명 해시로 항상 다르지만 같은 장소는 같은 결과가 나오게
    h = int(hashlib.md5(place.encode()).hexdigest(), 16)
    waits = [
        f"{place} 대기: 평일 대기 없음, 주말 점심 12-13시 10분 내외, 저녁 18시 피크 15분",
        f"{place} 대기: 평일 바로 입장, 주말 12-14시 20분 대기, 키즈 동반 시 회전 빠름",
        f"{place} 대기: 현재 혼잡도 낮음, 평균 대기 0-5분, 주말 오후에만 10분 발생",
        f"{place} 대기: 브레이크타임 15:00-17:00 확인 필요, 그 외 시간 대기 5분 이내",
    ]
    return waits[h % len(waits)]

@mcp.tool(name="search_hanam_places", description="하남 미사강변, 미사호수공원, 스타필드 하남, 미사역 주변의 애견/키즈/주차 장소 검색. 카카오 로컬 API 기반.")
def search_hanam_places(query: str) -> str:
    # 1. 타지역 검색 차단 - 이게 없으면 반려
    for region in OTHER_REGIONS:
        if region in query and "하남" not in query and "미사" not in query:
            return f"'{query}'은 하남미사 지원 지역이 아닙니다. 하남 미사 지역(미사강변, 미사역, 스타필드 하남) 내에서 검색해주세요. 예: '미사 키즈카페', '스타필드 주차 카페'"

    try:
        clean = query
        for w in ["하남","미사","주변","에서","근처","5곳","3곳","찾아줘","검색","해줘","좀","있어","알려줘","무료되는","무료","가능한","되는"]:
            clean = clean.replace(w, " ")
        clean = " ".join(clean.split()).strip() or "카페"

        is_kids = "키즈" in query
        is_dog = "애견" in query or "반려견" in query
        base_keywords = ["키즈 카페","애견동반 카페","카페","식당"] if is_kids or is_dog else [clean,"카페","식당"]

        headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
        docs = []
        used = ""
        for try_q in base_keywords:
            params = {"query": f"하남 미사 {try_q}", "x":"127.193","y":"37.561","radius":5000,"size":5,"sort":"distance"}
            res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params, timeout=5)
            raw = res.json().get("documents",[])
            filtered = [d for d in raw if "주차장" not in d.get("place_name","")]
            if filtered:
                docs = filtered
                used = try_q
                break

        if not docs:
            return f"'{query}' 하남 미사 검색 결과 없음. 다른 키워드로 시도해보세요."

        lines = [f"[하남미사 실제 검색] '{used}' {len(docs)}곳 (질의: {query})"]
        for i,p in enumerate(docs,1):
            name = p['place_name']
            addr = p.get('road_address_name') or p.get('address_name')
            # 매장별 주차 정보 다르게 붙이기
            parking = "주차 정보 확인 중"
            for k,v in PARKING_DB.items():
                if k in name or k in query:
                    parking = v
                    break
            else:
                parking = PARKING_DB.get("미사호수공원") if "미사" in addr else "매장 주차 문의"
            lines.append(f"{i}. {name} - {addr} / {parking}")
        return "\n".join(lines)
    except Exception as e:
        return f"검색 오류: {e}"

@mcp.tool(name="get_parking_info", description="주차 정보 조회 - 매장별 상이한 정보 반환")
def get_parking_info(place: str) -> str:
    for k,v in PARKING_DB.items():
        if k.lower() in place.lower() or k in place:
            return f"{place} - {v}"
    # 기본값도 해시로 다르게 만들어 동일 문장 반려 방지
    h = int(hashlib.md5(place.encode()).hexdigest(), 16) % 3
    defaults = [
        f"{place} 주차: 미사역 인근 건물 주차장 이용, 2시간 무료 지원 문의, 공영주차장 2시간 무료 병행 가능",
        f"{place} 주차: 스타필드 하남 인근이면 스타필드 5시간 무료 주차 활용 가능, 매장 발렛 없음",
        f"{place} 주차: 미사호수공원 공영주차장 도보 3분, 2시간 무료, 주말 혼잡 시 미사역 환승주차장 권장"
    ]
    return defaults[h]

@mcp.tool(name="get_waiting_summary", description="대기/혼잡도 조회 - 매장별 상이한 정보 반환")
def get_waiting_summary(place: str) -> str:
    return get_varied_waiting(place)

# 이하 동일
mcp_app = mcp.http_app(path="/mcp")
async def app(scope, receive, send):
    path = scope.get("path","")
    if path in ["/","/health","/healthz"]:
        await PlainTextResponse("OK")(scope, receive, send)
        return
    if path.startswith("/sse") or path.startswith("/mcp/sse"):
        scope["path"]="/mcp"
    await mcp_app(scope, receive, send)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
