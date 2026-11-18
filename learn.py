import os
import random
import time
import pandas as pd
import requests

# 1. 설정 및 API 키 입력
EXCEL_FILE_PATH = "2026 서울시 가로수 위치정보.xlsx"
GOOGLE_API_KEY = "AIzaSyDt8FutkbUEiBg5cnICjPyUpaXTmuplq_s"  # 본인의 Google API 키 입력

# 2. 디렉토리 구조 생성
splits = ["train", "val", "test"]
categories = ["ginkgo", "other"]

for split in splits:
  for category in categories:
    os.makedirs(os.path.join("dataset", split, category), exist_ok=True)

print("디렉토리 구조 생성 완료!")

# 3. 엑셀 파일 로드
try:
  df = pd.read_excel(EXCEL_FILE_PATH, header=2)
except Exception as e:
  print(f"엑셀 파일 읽기 실패: {e}")
  exit()

# 결측치 제거
df = df.dropna(subset=["좌표(위도)", "좌표(경도)", "수종"])

# 4. 은행나무와 기타 나무 분리
ginkgo_df = df[df["수종"].str.contains("은행나무", na=False)].copy()
other_df = df[~df["수종"].str.contains("은행나무", na=False)].copy()

# 5. 원하는 목표 수량 설정 (각 카테고리당 300장씩, 총 600장)
# -> 각 카테고리 안에서 Train 240, Val 30, Test 30으로 배분됨
TARGET_PER_CATEGORY = 300


def sample_and_process(sub_df, category_name):
  # 데이터가 부족할 경우를 대비해 가능한 최대 수량만큼만 샘플링
  sample_size = min(TARGET_PER_CATEGORY, len(sub_df))
  sampled_df = sub_df.sample(
      n=sample_size, random_state=42
  ).copy()  # random_state로 재현성 확보

  data_list = sampled_df.to_dict("records")

  # 비율 배분 (총 300장 기준: Train 240장, Val 30장, Test 30장)
  train_end = int(sample_size * 0.8)  # 240장
  val_end = train_end + int(sample_size * 0.1)  # 30장 (총 270)

  dataset_splits = {
      "train": data_list[:train_end],
      "val": data_list[train_end:val_end],
      "test": data_list[val_end:],
  }

  for split_name, items in dataset_splits.items():
    print(
        f"\n[{category_name.upper()} - {split_name.upper()}] 다운로드 시작 (총"
        f" {len(items)}개)"
    )

    for idx, row in enumerate(items):
      lat = row["좌표(위도)"]
      lng = row["좌표(경도)"]

      filename = os.path.join(
          "dataset",
          split_name,
          category_name,
          f"{category_name}_{idx}_{lat}_{lng}.png",
      )

      if os.path.exists(filename):
        continue

      # 구글 거리뷰 Static API 요청
      url = "https://maps.googleapis.com/maps/api/streetview"
      params = {
          "size": "640x640",
          "scale": 2,  # 고해상도
          "location": f"{lat},{lng}",
          "key": GOOGLE_API_KEY,
      }

      try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
          with open(filename, "wb") as f:
            f.write(response.content)
        else:
          print(f"API 에러 ({response.status_code}): {lat}, {lng}")
      except Exception as e:
        print(f"네트워크 에러: {e}")

      time.sleep(0.2)


# 6. 실행
if __name__ == "__main__":
  print("--- 지정된 수량만큼 데이터셋 샘플링 및 다운로드를 시작합니다 ---")
  sample_and_process(ginkgo_df, "ginkgo")
  sample_and_process(other_df, "other")
  print("\n모든 작업이 완료되었습니다!")
  # learn