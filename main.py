try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

# 하남 호수뷰 + 반려견 동반 카페 10곳 DB
HANAM_CAFES = [
    {
        "name": "카페미스터리",
        "address": "하남시 미사강변동로 40번길 15",
        "view": "미사호수공원 뷰",
        "pet": "테라스 애견동반 가능 (소형견)",
        "parking": "지하주차장 최대 5시간 무료",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 조용하고 채광 좋은 미사호수공원 산책 후 쉬어가기 좋은 곳"
    },
    {
        "name": "디이피커피바 (DEP COFFEE&BAR)",
        "address": "미사호수공원 인근, 센트럴파크2 상가",
        "view": "미사호수공원 도보 1분",
        "pet": "실내 애견동반 가능, 강아지 의자 있음, 멍푸치노 3,000원",
        "parking": "센트럴파크2 주차장 3시간30분 무료",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 반려견과 함께 브런치 즐기기 좋은 곳"
    },
    {
        "name": "드로게리아",
        "address": "하남시 미사동로 102-17",
        "view": "한강뷰 + 통창뷰",
        "pet": "반려동물 동반 가능",
        "parking": "주차 가능",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 이탈리아 감성 브런치카페"
    },
    {
        "name": "흠커피 HCR",
        "address": "하남시 춘궁동 춘궁저수지 인근",
        "view": "춘궁저수지(호수) 뷰 + 정원 + 루프탑",
        "pet": "반려견 동반 가능, 대형 야외 테라스",
        "parking": "대형 주차장 50대 이상",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 빵 맛집으로 유명한 호수뷰 카페"
    },
    {
        "name": "라이드온애스터로이드",
        "address": "미사호수공원 인근",
        "view": "미사호수공원 뷰, 늦게까지 영업",
        "pet": "테라스 애견동반 가능",
        "parking": "미사호수공원 공영주차장 이용 (최초 2시간 무료)",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 조용하고 고즈넉한 분위기"
    },
    {
        "name": "슬로우선데이커피샵",
        "address": "미사호수공원 바로 앞",
        "view": "호수뷰",
        "pet": "테라스 애견동반 가능",
        "parking": "공영주차장 도보 2분",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 말차 아이스크림 라떼 시그니처"
    },
    {
        "name": "누커스",
        "address": "미사강변북로30번안길 31",
        "view": "미사호수공원 뷰 (2층)",
        "pet": "소형견 동반 가능 문의",
        "parking": "건물 주차",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 채광 좋은 작은 감성 카페"
    },
    {
        "name": "카페 그랑그랑",
        "address": "하남시 미사동",
        "view": "호수공원 인근",
        "pet": "애견동반 가능",
        "parking": "미사호수공원 공영주차장 2시간 무료",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 넓은 테라스 보유"
    },
    {
        "name": "담금 젤라또",
        "address": "미사강변한강로 290-3",
        "view": "미사호수공원 도보권",
        "pet": "야외 애견동반 가능",
        "parking": "C3단지 상가 주차",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 수제 젤라또 맛집"
    },
    {
        "name": "테이블드파스타",
        "address": "하남시 미사강변동로",
        "view": "미사호수공원 근처",
        "pet": "실내 애견동반 가능 (리드줄, 개모차)",
        "parking": "매장 앞 주차 가능",
        "desc": "하남미사 지금갈곳 - 주차·대기·키즈 서비스 추천. 실내 애견동반 식당 겸 카페"
    }
]

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
def search_hanam_places(query: str):
    results = []
    for cafe in HANAM_CAFES:
        if "반려견" in query or "애견" in query or "강아지" in query:
            if "가능" in cafe["pet"]:
                results.append(cafe)
        elif "호수" in query:
            results.append(cafe)
        else:
            results.append(cafe)
    
    # 최대 3곳만 반환 (AI가 요약하기 좋게)
    return results[:3]

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
