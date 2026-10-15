from mcp.server.fastmcp import FastMCP

mcp = FastMCP("하남미사 지금갈곳 - 주차·대기·키즈")

@mcp.tool(
    name="search_hanam_places",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 핵심 기능입니다. 하남 미사, 스타필드, 미사역 주변의 아이 동반 가능, 무료 주차 가능한 식당, 카페, 놀거리를 검색합니다.",
    annotations={
        "title": "하남미사 장소 검색",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
def search_hanam_places(query: str, kids_ok: bool = False, parking_free: bool = False):
    # 기존 로직 그대로 두세요
    return search_logic(query, kids_ok, parking_free)

@mcp.tool(
    name="check_parking_status",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 주차 정보 제공 기능입니다. 특정 가게/장소의 주차 가능 여부, 무료 주차 시간(스타필드 5시간 등), 주차 팁을 제공합니다.",
    annotations={
        "title": "주차 상태 확인",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
def check_parking_status(place_name: str):
    # 기존 로직 그대로 두세요
    return parking_logic(place_name)

@mcp.tool(
    name="get_waiting_and_summary",
    description="하남미사 지금갈곳 - 주차·대기·키즈 서비스의 대기 및 요약 기능입니다. 식당의 현재 대기 팀 수, 영업 상태, 방문 요약 정보를 제공합니다.",
    annotations={
        "title": "대기 현황 및 요약",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
def get_waiting_and_summary(place_name: str):
    # 기존 로직 그대로 두세요
    return waiting_logic(place_name)
