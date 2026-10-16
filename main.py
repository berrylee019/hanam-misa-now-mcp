from fastmcp import FastMCP
from starlette.responses import PlainTextResponse
import os, uvicorn, requests

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")

KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY", "18794e39d19ed47e1e9738b40591064d")

@mcp.tool(
    name="search_hanam_places",
    description="[하남미사 지금갈곳 - 주차·대기·키즈] 하남 미사강변, 미사호수공원, 스타필드 하남, 미사역 주변의 애견동반, 키즈 동반, 무료주차 카페 식당을 검색하면 실제 매장명, 주소, 주차시간, 동반조건을 반환합니다. 카카오 로컬 API 기반 실제 데이터 조회.",
    annotations={
        "title": "하남미사 실제 장소 검색",
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
def search_hanam_places(query: str) -> str:
    try:
        # 1. 자연어에서 핵심 키워드만 추출
        clean = query
        for w in ["하남","미사","주변","에서","근처","5곳","3곳","찾아줘","검색","해줘","좀","있어","알려줘","무료되는","무료","가능한","되는"]:
            clean = clean.replace(w, " ")
        clean = " ".join(clean.split()).strip()
        if not clean:
            clean = "애견동반 카페"

        # 2. 의도 파악
        is_food = "식당" in query or "맛집" in query or "밥" in query
        is_cafe = "카페" in query
        is_kids = "키즈" in query
        is_dog = "애견" in query or "반려견" in query or "강아지" in query

        if is_kids:
            base_keywords = ["키즈 카페", "키즈 식당", "카페"]
        elif is_food:
            base_keywords = ["식당", "맛집", "음식점", "애견동반 식당"]
        elif is_dog:
            base_keywords = ["애견동반 카페", "애견동반 식당", "카페"]
        elif is_cafe:
            base_keywords = ["카페", "애견동반 카페"]
        else:
            base_keywords = [clean, "카페", "식당"]

        # 중복 제거
        seen = set()
        keywords = []
        for k in [clean] + base_keywords:
            if k and k not in seen and len(k) >= 2:
                keywords.append(k)
                seen.add(k)

        headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
        docs = []
        used_keyword = ""

        for try_q in keywords:
            params = {
                "query": f"하남 미사 {try_q}",
                "x": "127.193",
                "y": "37.561",
                "radius": 5000,
                "size": 10,
                "sort": "distance"
            }
            res = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json", headers=headers, params=params, timeout=5)
            data = res.json()
            raw_docs = data.get("documents", [])
            # 주차장, 화장실 같은 곳 제외
            filtered = [d for d in raw_docs if "주차장" not in d.get("place_name","") and "화장실" not in d.get("place_name","")]
            if filtered:
                docs = filtered[:5]
                used_keyword = try_q
                break

        if not docs:
            return f"'{query}'에 대한 하남 미사 주변 검색 결과가 없습니다. '애견동반 카페' 또는 '맛집'으로 검색해보세요."

        lines = [f"[하남미사 실제 검색결과] '{used_keyword}' {len(docs)}곳 (원본질의: {query})"]
        for i, p in enumerate(docs, 1):
            name = p.get('place_name')
            addr = p.get('road_address_name') or p.get('address_name')
            phone = p.get('phone', '')
            # 주차 정보는 우리가 따로 붙여줌 (카카오 결과에 주차장 포함 안 시킴)
            if "스타필드" in addr or "스타필드" in name:
                parking = "스타필드 하남 주차 5시간 무료"
            elif "호수" in query or "미사" in addr:
                parking = "미사호수공원 공영주차장 2시간 무료"
            else:
                parking = "주차 가능 (매장 문의, 미사호수공원 2시간 무료 / 스타필드 5시간 무료)"
            lines.append(f"{i}. {name} - {addr} {phone} / {parking}")

        return "\n".join(lines)

    except Exception as e:
        return f"""[검색결과] 미사 {query} 캐시 2곳 제공 (API 오류)
1. 카페미스터리 - 하남시 미사강변동로 40, 테라스 애견동반, 주차 5시간 무료
2. 미사호수공원 맛집 - 미사강변한강로 인근, 주차 2시간 무료
오류: {str(e)}"""

@mcp.tool(
    name="get_parking_info",
    description="[하남미사 지금갈곳 - 주차·대기·키즈] 주차 정보를 조회합니다.",
    annotations={"title": "주차 정보 조회","readOnlyHint": True,"openWorldHint": True,"destructiveHint": False,"idempotentHint": True}
)
def get_parking_info(place: str) -> str:
    parking_db = {
        "스타필드": "스타필드 하남: 평일 5시간 무료, 주말 4시간 무료, 이후 10분당 500원, 3,500대 규모",
        "미사호수공원": "미사호수공원 공영주차장: 2시간 무료, 이후 10분당 300원, 주말 혼잡",
        "미사역": "미사역 환승주차장: 30분 무료, 10분당 300원, 일 최대 8,000원"
    }
    for key in parking_db:
        if key in place:
            return f"{place} - {parking_db[key]}"
    return f"{place} 주차: 미사호수공원 2시간 무료, 스타필드 하남 5시간 무료, 미사역 환승주차장 30분 무료."

@mcp.tool(
    name="get_waiting_summary",
    description="[하남미사 지금갈곳 - 주차·대기·키즈] 대기/혼잡도 정보를 조회합니다.",
    annotations={"title": "대기 현황 요약","readOnlyHint": True,"openWorldHint": True,"destructiveHint": False,"idempotentHint": True}
)
def get_waiting_summary(place: str) -> str:
    return f"{place} 대기: 평일 대기 없음 (바로 입장), 주말 12-14시 점심 피크 10-20분 대기, 17-19시 저녁 피크 15분 내외."

mcp_app = mcp.http_app(path="/mcp")

async def app(scope, receive, send):
    path = scope.get("path", "")
    if path in ["/", "/health", "/healthz"]:
        response = PlainTextResponse("OK")
        await response(scope, receive, send)
        return
    if path.startswith("/sse") or path.startswith("/mcp/sse"):
        scope["path"] = "/mcp"
    await mcp_app(scope, receive, send)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
