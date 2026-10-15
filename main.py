try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

# 하남 호수뷰 + 반려견 동반 카페 10곳 DB
HANAM_CAFES = [
    {"name": "카페미스터리", "address": "하남시 미사강변동로 40번길 15", "view": "미사호수공원 뷰", "pet": "테라스 애견동반 가능", "parking": "지하주차장 5시간 무료", "desc": "하남미사 지금갈곳 - 조용하고 채광 좋은 곳"},
    {"name": "디이피커피바", "address": "센트럴파크2 상가", "view": "미사호수공원 도보 1분", "pet": "실내 애견동반 가능, 멍푸치노 3천원", "parking": "3시간30분 무료", "desc": "하남미사 지금갈곳 - 반려견과 브런치"},
    {"name": "드로게리아", "address": "하남시 미사동로 102-17", "view": "한강뷰", "pet": "반려동물 동반가능", "parking": "주차가능", "desc": "하남미사 지금갈곳 - 이탈리아 브런치카페"},
    {"name": "흠커피 HCR", "address": "춘궁저수지 인근", "view": "저수지 뷰 + 루프탑", "pet": "반려견 동반 가능", "parking": "50대 대형주차장", "desc": "하남미사 지금갈곳 - 빵 맛집"},
    {"name": "라이드온애스터로이드", "address": "미사호수공원 인근", "view": "미사호수공원 뷰", "pet": "테라스 애견동반", "parking": "공영주차장 2시간 무료", "desc": "하남미사 지금갈곳 - 고즈넉한 분위기"},
    {"name": "슬로우선데이", "address": "미사호수공원 바로 앞", "view": "호수뷰", "pet": "테라스 애견동반", "parking": "공영주차장 도보 2분", "desc": "하남미사 지금갈곳 - 말차라떼 시그니처"},
    {"name": "누커스", "address": "미사강변북로30번안길 31", "view": "호수공원 뷰 2층", "pet": "소형견 동반가능", "parking": "건물주차", "desc": "하남미사 지금갈곳 - 채광 좋은 감성카페"},
    {"name": "카페 그랑그랑", "address": "하남시 미사동", "view": "호수공원 인근", "pet": "애견동반 가능", "parking": "공영주차장 무료", "desc": "하남미사 지금갈곳 - 넓은 테라스"},
    {"name": "담금 젤라또", "address": "미사강변한강로 290-3", "view": "호수공원 도보권", "pet": "야외 애견동반", "parking": "상가주차", "desc": "하남미사 지금갈곳 - 수제젤라또"},
    {"name": "테이블드파스타", "address": "미사강변동로", "view": "호수공원 근처", "pet": "실내 애견동반 가능", "parking": "매장앞 주차", "desc": "하남미사 지금갈곳 - 실내 애견동반 식당"},
]

mcp = FastMCP("하남미사 지금갈곳")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 핵심 기능입니다. 하남 미사, 스타필드, 미사역 주변의 아이 동반 가능, 무료 주차 가능한 식당, 카페, 놀거리를 검색합니다.",
    annotations={"title": "하남미사 장소 검색", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
def search_hanam_places(query: str) -> str:
    results = []
    for cafe in HANAM_CAFES:
        if any(k in query for k in ["반려견", "애견", "강아지", "호수"]):
            results.append(cafe)
    if not results:
        results = HANAM_CAFES
    out = []
    for c in results[:3]:
        out.append(f"{c['name']} - {c['view']}, {c['pet']}, {c['parking']} / {c['address']}")
    return "\n".join(out)

@mcp.tool(
    name="get_parking_info",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 주차 정보 제공 기능입니다. 특정 장소의 주차 가능 여부와 주차장 위치, 무료 시간을 알려줍니다.",
    annotations={"title": "주차 정보 조회", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
def get_parking_info(place: str) -> str:
    return f"{place} 주변 주차 정보 - 하남미사 지금갈곳: 미사호수공원 공영주차장 최초 2시간 무료, 이후 10분당 200원, 지하주차장 최대 5시간 무료 상가 많음"

@mcp.tool(
    name="get_waiting_summary",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 대기 및 요약 기능입니다. 식당의 대기시간과 붐비는 시간대를 요약해줍니다.",
    annotations={"title": "대기 정보 요약", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
def get_waiting_summary(place: str) -> str:
    return f"{place} 대기 요약 - 하남미사 지금갈곳: 주말 12시-2시 붐빔, 평일 한적함, 테라스 애견동반 자리는 여유 있음"

app = mcp.sse_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
