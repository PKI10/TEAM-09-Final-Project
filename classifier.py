
from ultralytics import YOLO

# 1. 사전 학습된 YOLO 이미지 분류 모델 불러오기
model = YOLO("yolo11n-cls.pt")

# 2. 은행나무 이미지 분류 학습
model.train(
    data="dataset",
    epochs=50,
    imgsz=224,
    batch=16,
    device=0,       # NVIDIA GPU 사용
    project="runs",
    name="tree_classifier"
)

# 3. 학습 완료
print("학습 완료!")
