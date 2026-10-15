from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import os, uvicorn

# 중요: sse_path를 심사 중인 주소인 /mcp로!
mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈", sse_path="/mcp", streamable_http_path="/mcp")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 핵심 기능입니다. 하남 미사강변, 스타필드 하남, 미사역 5호선 주변의 아이 동반, 반려견 동반, 무료 주차 가능한 카페 식당을 검색합니다."
)
def search_hanam_places(query: str) -> str:
    return "미사호수공원: 카페미스터리(호수뷰, 테라스 애견동반, 주차 5시간 무료), 디이피커피바(호수 1분, 실내동반 멍푸치노, 3.5시간 무료)"

@mcp.tool(
    name="get_parking_info",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 주차 정보 제공 기능입니다. 특정 장소의 주차장 위치와 무료 시간을 알려줍니다."
)
def get_parking_info(place: str) -> str:
    return f"{place} - 미사호수공원 공영주차장 2시간 무료, 스타필드 하남 주차 5시간 무료"

@mcp.tool(
    name="get_waiting_summary",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 대기 요약 기능입니다."
)
def get_waiting_summary(place: str) -> str:
    return f"{place} 주말 12-2시 혼잡, 평일 한적"

sse_app = mcp.sse_app()
app = Starlette(routes=[
    Mount("/", app=sse_app),
    Mount("/mcp", app=sse_app),
    Mount("/sse", app=sse_app),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
