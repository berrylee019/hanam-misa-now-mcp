from fastmcp import FastMCP
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

# 1. MCP 앱 생성 (기본 경로 /mcp)
mcp_http_app = mcp.http_app(path="/mcp")

# 2. /sse로 들어오면 /mcp로 바꿔주는 래퍼 (이게 핵심!)
async def app_wrapper(scope, receive, send):
    if scope["type"] == "http" or scope["type"] == "websocket":
        path = scope.get("path", "")
        # /sse로 오면 /mcp로 변경
        if path.startswith("/sse"):
            scope["path"] = path.replace("/sse", "/mcp", 1)
            if scope["path"] == "":
                scope["path"] = "/mcp"
    await mcp_http_app(scope, receive, send)

# 3. uvicorn이 실행할 app은 이 래퍼
app = app_wrapper

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
