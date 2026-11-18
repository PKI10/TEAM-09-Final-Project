import os
import time
import pandas as pd
import requests

# 1. 설정 및 API 키 입력
EXCEL_FILE_PATH = "2026 서울시 가로수 위치정보.xlsx"
GOOGLE_API_KEY = "AIzaSyDt8FutkbUEiBg5cnICjPyUpaXTmuplq_s"  # 본인의 구글 API 키 입력
OUTPUT_DIR = "./ginkgo_streetview_images"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
  print("엑셀 파일을 불러오는 중...")
  try:
    df = pd.read_excel(EXCEL_FILE_PATH, header=2)
  except Exception as e:
    print(f"엑셀 파일 읽기 실패: {e}")
    return

  # 은행나무 필터링 (필요시 .head(10)으로 테스트)
  ginkgo_df = df[df["수종"].str.contains("은행나무", na=False)]
  print(f"총 발견된 은행나무 그루 수: {len(ginkgo_df)}")

  for idx, row in ginkgo_df.iterrows():
    lat = row["좌표(위도)"]
    lng = row["좌표(경도)"]

    if pd.isna(lat) or pd.isna(lng):
      continue

    filename = os.path.join(OUTPUT_DIR, f"streetview_{idx}_{lat}_{lng}.png")

    if os.path.exists(filename):
      print(f"[{idx+1}/{len(ginkgo_df)}] 이미 존재함: {filename}")
      continue

    # 구글 Street View Static API 요청 URL
    url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": "640x640",  # 이미지 해상도 크기
        "scale": 2,
        "location": f"{lat},{lng}",  # 위도, 경도 (구글은 위도, 경도 순서입니다!)
        "key": GOOGLE_API_KEY,
    }

    try:
      response = requests.get(url, params=params)

      if response.status_code == 200:
        with open(filename, "wb") as f:
          f.write(response.content)
        print(f"[{idx+1}/{len(ginkgo_df)}] 다운로드 성공: {filename}")
      else:
        print(
            f"[{idx+1}/{len(ginkgo_df)}] API 에러 ({response.status_code}):"
            f" {response.text}"
        )

    except Exception as e:
      print(f"[{idx+1}/{len(ginkgo_df)}] 에러 발생: {e}")

    # 서버 부하 방지 및 쿼리 제한(Rate Limit) 대응을 위한 0.5초 휴식
    time.sleep(0.5)

  print("모든 거리뷰 이미지 수집 작업이 완료되었습니다!")


if __name__ == "__main__":
  main()