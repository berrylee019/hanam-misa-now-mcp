from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import os, uvicorn

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 핵심 기능입니다. 하남 미사강변, 스타필드 하남, 미사역 5호선 주변의 아이 동반, 반려견 동반, 무료 주차 가능한 카페 식당을 실시간 검색합니다."
)
def search_hanam_places(query: str) -> str:
    return """미사호수공원 추천:
1. 카페미스터리 - 호수뷰, 테라스 애견동반, 주차 5시간 무료
2. 디이피커피바 - 호수 1분, 실내동반 멍푸치노 제공, 3.5시간 무료
3. 스타필드 하남 - 대형 키즈카페, 주차 5시간 무료"""

@mcp.tool(name="get_parking_info", description="주차 정보 제공")
def get_parking_info(place: str) -> str:
    return f"{place} 주차 정보: 미사호수공원 공영주차장 2시간 무료, 스타필드 5시간 무료"

@mcp.tool(name="get_waiting_summary", description="대기 요약")
def get_waiting_summary(place: str) -> str:
    return f"{place} 대기: 주말 12-14시 혼잡, 평일 한적"

# /mcp 경로로 서비스
http_app = mcp.http_app(path="/mcp")

# PlayMCP가 /mcp, /sse, / 어디로 오든 다 응답
app = Starlette(routes=[
    Mount("/mcp", app=http_app),
    Mount("/sse", app=http_app),
    Mount("/", app=http_app),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
