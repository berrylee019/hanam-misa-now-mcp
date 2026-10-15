from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse
import os, uvicorn

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 핵심 기능입니다. 하남 미사강변, 스타필드 하남, 미사역 주변의 아이 동반, 반려견 동반, 무료 주차 가능한 카페 식당을 검색합니다."
)
def search_hanam_places(query: str) -> str:
    return "미사호수공원: 카페미스터리(호수뷰, 테라스 애견, 주차 5시간 무료), 디이피커피바(호수 1분, 실내동반)"

@mcp.tool(name="get_parking_info", description="주차 정보")
def get_parking_info(place: str) -> str:
    return f"{place} 주차 2시간 무료"

@mcp.tool(name="get_waiting_summary", description="대기 정보")
def get_waiting_summary(place: str) -> str:
    return f"{place} 주말 12-14시 혼잡"

# SSE 전송용과 HTTP 전송용을 각각 생성
try:
    sse_app = mcp.sse_app(path="/sse")
except TypeError:
    sse_app = mcp.sse_app()

try:
    http_app = mcp.http_app(path="/mcp")
except TypeError:
    http_app = mcp.http_app()

async def health(request):
    return PlainTextResponse("OK - 하남미사 지금갈곳 Online")

# 진짜 라우팅 - /sse는 sse_app으로, /mcp는 http_app으로
app = Starlette(routes=[
    Route("/", endpoint=health),
    Route("/health", endpoint=health),
    Mount("/sse", app=sse_app),
    Mount("/mcp", app=http_app),
    Mount("/", app=http_app),  # 나머지도 http_app이 처리
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
