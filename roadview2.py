import os
import csv
import json
import math
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

try:
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SAVE_DIR = "./streetview_dataset"
CSV_PATH = os.path.join(SAVE_DIR, "locations.csv")
os.makedirs(SAVE_DIR, exist_ok=True)

CSV_FIELDS = ["file", "time", "lat", "lng", "pano_id", "yaw", "pitch", "fov", "url"]
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow(CSV_FIELDS)


def mercator_to_latlng(x, y):
    """네이버 지도 URL의 웹 메르카토르(m) 좌표를 위경도로 변환"""
    lng = x / 20037508.34 * 180
    lat = math.degrees(2 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2)
    return lat, lng


def parse_location(url):
    """URL에서 위치/시점 정보를 최대한 뽑아낸다 (없는 값은 빈 문자열)"""
    info = {"lat": "", "lng": "", "pano_id": "", "yaw": "", "pitch": "", "fov": ""}
    q = parse_qs(urlparse(url).query)

    # c= 값: 지도 중심 (x, y, zoom, ...) 형태일 때 좌표 변환
    if "c" in q:
        parts = q["c"][0].split(",")
        try:
            x, y = float(parts[0]), float(parts[1])
            if abs(x) > 1000 and abs(y) > 1000:  # 메르카토르 좌표로 보이는 경우
                info["lat"], info["lng"] = (round(v, 6) for v in mercator_to_latlng(x, y))
        except (ValueError, IndexError):
            pass

    # p= 값: 거리뷰 파노라마 ID, 방향(yaw), 기울기(pitch), 시야각(fov)
    if "p" in q:
        parts = q["p"][0].split(",")
        keys = ["pano_id", "yaw", "pitch", "fov"]
        for k, v in zip(keys, parts):
            info[k] = v
    return info


options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--force-device-scale-factor=1")
options.add_argument("--ignore-gpu-blocklist")
options.add_argument("--enable-webgl")

driver = webdriver.Chrome(options=options)
driver.get("https://map.naver.com/p")

INJECT_JS = """
if (!window.__capHooked) {
    window.__capHooked = true;
    window.__capQueue = 0;
    window.__capQuit = false;
    window.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { window.__capQueue += 1; e.preventDefault(); }
        if (e.key === 'Escape') { window.__capQuit = true; }
    }, true);
}
"""

print("1) 검색창에 '둔산동' 검색 → 2) 거리뷰 버튼 → 3) 파란 길 선택")
print("은행나무가 보이는 장면에서 Enter = 캡처(+위치 저장) / Esc = 종료")

count = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".png")])
taken = 0

try:
    while True:
        try:
            driver.execute_script(INJECT_JS)
            queue = driver.execute_script(
                "var q = window.__capQueue; window.__capQueue = 0; return q;"
            )
            quit_flag = driver.execute_script("return window.__capQuit;")
        except WebDriverException:
            print("\n브라우저가 닫혀 종료합니다.")
            break

        if quit_flag:
            print("\nEsc 입력으로 종료합니다.")
            break

        if queue > 0:
            count += 1
            taken += 1
            filename = f"streetview_{count:04d}.png"
            path = os.path.join(SAVE_DIR, filename)

            url = driver.current_url          # 캡처 순간의 주소
            driver.save_screenshot(path)
            loc = parse_location(url)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1) CSV에 기록
            with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow([
                    filename, now, loc["lat"], loc["lng"], loc["pano_id"],
                    loc["yaw"], loc["pitch"], loc["fov"], url,
                ])

            # 2) PNG 안에도 메타데이터로 삽입 (Pillow가 있을 때)
            if HAS_PIL:
                meta = PngInfo()
                meta.add_text("source_url", url)
                meta.add_text("location", json.dumps(loc, ensure_ascii=False))
                meta.add_text("captured_at", now)
                img = Image.open(path)
                img.save(path, pnginfo=meta)

            where = f"{loc['lat']}, {loc['lng']}" if loc["lat"] else f"pano_id={loc['pano_id'] or '없음'}"
            print(f"저장({taken}장): {filename} | 위치: {where}")

        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n사용자가 중단했습니다.")
finally:
    try:
        driver.quit()
    except Exception:
        pass
    print(f"총 {taken}장 저장 완료 (위치 기록: {CSV_PATH})")