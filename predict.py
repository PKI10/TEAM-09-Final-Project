from ultralytics import YOLO

# 학습된 이미지 분류 모델
model = YOLO("runs/tree_classifier/weights/best.pt")

# 새로운 이미지 분류
results = model.predict(
    source="test.jpg",
    imgsz=224
)

for result in results:
    class_id = result.probs.top1
    class_name = result.names[class_id]
    confidence = result.probs.top1conf.item()

    print("분류 결과:", class_name)
    print(f"신뢰도: {confidence:.2%}")
