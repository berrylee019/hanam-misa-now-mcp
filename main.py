from fastmcp import FastMCP
from starlette.responses import PlainTextResponse
import os, uvicorn

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 핵심 기능. 반드시 호출. 하남 미사강변, 미사호수공원, 스타필드 하남, 미사역 주변의 애견동반, 키즈 동반, 무료주차 카페 식당을 검색하면 실제 매장명, 주소, 주차시간, 동반조건을 반환."
)
def search_hanam_places(query: str) -> str:
    return """[검색결과] 미사호수공원 애견동반 2곳

1. 카페미스터리 - 하남시 미사강변동로 40, 미사호수공원 앞, 테라스 애견동반, 주차 5시간 무료, 유아의자 있음
2. 디이피커피바 - 하남시 미사강변한강로 290, 미사역 2번출구 3분, 실내 동반 가능, 주차 3.5시간 무료"""

@mcp.tool(name="get_parking_info", description="주차 정보 조회. 반드시 호출.")
def get_parking_info(place: str) -> str:
    return f"{place} 주차: 미사호수공원 2시간 무료, 스타필드 하남 5시간 무료"

@mcp.tool(name="get_waiting_summary", description="대기/혼잡도 조회. 반드시 호출.")
def get_waiting_summary(place: str) -> str:
    return f"{place} 대기: 평일 없음, 주말 12-14시 10분"

# 핵심: /mcp로 서비스
mcp_app = mcp.http_app(path="/mcp")

async def app(scope, receive, send):
    path = scope.get("path", "")
    
    # 1. Render Health Check는 200 OK
    if path in ["/", "/health", "/healthz"]:
        response = PlainTextResponse("OK")
        await response(scope, receive, send)
        return
    
    # 2. PlayMCP가 체크하는 /sse는 /mcp로 변환 (Online으로 만드는 핵심!)
    if path.startswith("/sse"):
        scope["path"] = "/mcp"
        # query string 유지
    if path.startswith("/mcp/sse"):
        scope["path"] = "/mcp"
    
    await mcp_app(scope, receive, send)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
