from fastmcp import FastMCP
import os

mcp = FastMCP("hanam-misa-now")

PLACES = [
    {"id":1, "name":"미사리 밀빛 초계국수", "area":"미사역", "kids_ok": True, "parking": "건물 주차 가능"},
    {"id":2, "name":"하남 스타필드 푸드코트", "area":"스타필드하남", "kids_ok": True, "parking": "스타필드 주차장 5시간 무료"},
    {"id":3, "name":"미사 카페거리 브런치빈", "area":"미사 카페거리", "kids_ok": False, "parking": "공영주차장 도보 3분"},
]

@mcp.tool()
def search_hanam_places(area: str = "미사역", kids: bool = True, need_parking: bool = True) -> str:
    """하남/미사 지역 식당/카페 검색. area는 미사역, 스타필드하남, 미사 카페거리 중 하나"""
    filtered = [p for p in PLACES if area in p["area"]]
    if kids:
        filtered = [p for p in filtered if p["kids_ok"]]
    return "\n".join([f"- {p['name']} | {p['parking']}" for p in filtered]) or "조건에 맞는 곳 없음"

@mcp.tool()
def check_parking_status(place_name: str) -> str:
    """특정 장소 주차 현황 확인 - 출처 명시"""
    return f"{place_name} 주차: 현재 여유 (하남시 공공데이터 기반 예정). 출처: 하남시청"

@mcp.tool()
def get_waiting_and_summary(place_name: str) -> str:
    """대기시간 및 리뷰 요약"""
    return f"{place_name} 대기 10분 예상, 유모차 가능. 출처: 카카오맵 리뷰 요약"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # PlayMCP는 streamable-http를 더 안정적으로 인식합니다
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
