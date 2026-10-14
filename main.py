from fastmcp import FastMCP
import datetime

mcp = FastMCP("hanam-misa-now")

# 1. 더미 DB - 나중에 구글시트/DB로 교체
PLACES = [
    {"id":1, "name":"미사리 밀빛 초계국수", "area":"미사역", "kids_ok": True, "stroller": True, "parking": "건물 주차 가능", "lat":37.563, "lng":127.195},
    {"id":2, "name":"하남 스타필드 푸드코트", "area":"스타필드하남", "kids_ok": True, "stroller": True, "parking": "스타필드 주차장 5시간 무료", "lat":37.545, "lng":127.203},
    {"id":3, "name":"미사 카페거리 브런치빈", "area":"미사 카페거리", "kids_ok": False, "stroller": False, "parking": "공영주차장 도보 3분", "lat":37.566, "lng":127.185},
]

@mcp.tool()
def search_hanam_places(area: str = "미사역", kids: bool = True, need_parking: bool = True) -> str:
    """하남/미사 지역 식당/카페 검색. area: 미사역, 스타필드하남, 미사 카페거리 등 / kids: 아이 동반 여부 / need_parking: 주차 필요 여부"""
    filtered = [p for p in PLACES if (area in p["area"]) and (not kids or p["kids_ok"]) and (not need_parking or p["parking"])]
    if not filtered:
        return "조건에 맞는 곳이 더미 DB에 없어요. 필터를 완화해보세요."
    return "\n".join([f"- {p['name']} ({p['area']}) | {p['parking']} | 키즈:{p['kids_ok']}" for p in filtered])

@mcp.tool()
def check_parking_status(place_name: str) -> str:
    """특정 장소 주차 현황 확인 (현재는 더미, 추후 하남시 공영주차 API 연동)"""
    # TODO: 하남시 공공데이터 API 연동 - https://data.hanam.go.kr
    # 예: GET https://api.hanam.go.kr/parking/status
    return f"{place_name} - 주차: 현재 여유 있음 (18:00 기준, 더미데이터). 실제 연동 시 하남시 공영주차장 실시간 API로 교체 예정. 출처: 하남시 공공데이터"

@mcp.tool()
def get_waiting_and_summary(place_name: str) -> str:
    """최근 리뷰/블로그에서 대기시간 요약"""
    # TODO: 네이버 플레이스 크롤링 or 블로그 검색 API
    return f"{place_name} - 최근 리뷰 요약: '주말 12시 기준 대기 10분', '유모차 입장 가능, 테이블 간격 넓음' (요약 출처 표시 예정 - 모두의 AI 핵심 요구사항)"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # Render가 주는 PORT 사용
    mcp.run(transport="sse", host="0.0.0.0", port=port)
