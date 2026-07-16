# 🗺️ Kế Hoạch Triển Khai Chi Tiết — Hệ Thống Phân Tích Video Đa Camera Thông Minh

> **Phạm vi mở rộng:** Không chỉ theo dõi người, mà còn **phát hiện lửa/cháy, phát hiện đồ vật**, có quy trình **huấn luyện mô hình YOLO tùy chỉnh**, và **thử nghiệm bằng video tải lên/đường dẫn**.
>
> **Phương pháp:** Xây dựng từ dưới lên theo từng giai đoạn. Mỗi giai đoạn hoàn thành, kiểm tra xong mới chuyển sang giai đoạn tiếp.
>
> **Quy tắc:** Chỉ lên kế hoạch, KHÔNG thực hiện.

---

## Phạm vi dự án

**Bao gồm:**
- Phát hiện đa đối tượng: **người, lửa/cháy, đồ vật tùy chỉnh** (xe máy, ba lô, dao,...)
- Huấn luyện mô hình YOLO tùy chỉnh (.pt) từ bộ dữ liệu tự gán nhãn
- Theo dõi người xuyên camera (ReID + MTMC)
- Tìm kiếm người bằng hình ảnh (vector search)
- Thử nghiệm bằng **tải video lên** hoặc **dán đường dẫn video/RTSP**
- 8 dịch vụ vi mô + giao diện React + giám sát + CI/CD
- Cảnh báo thời gian thực (lửa, xâm nhập, đồ vật nguy hiểm)

**Không bao gồm:**
- Ứng dụng di động
- Triển khai biên (edge computing)
- Cụm Kafka đa nút (dùng đơn nút cho phát triển)
- Tích hợp SSO (chỉ giữ chỗ)

---

## Tổng quan luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NGUỒN VIDEO ĐẦU VÀO                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐            │
│  │ Camera   │  │ Video tải    │  │ Đường dẫn video   │            │
│  │ RTSP     │  │ lên (MP4/AVI)│  │ (URL/YouTube)     │            │
│  └────┬─────┘  └──────┬───────┘  └─────────┬─────────┘            │
│       │               │                    │                       │
│       └───────────────┼────────────────────┘                       │
│                       ▼                                            │
│            ┌──────────────────────┐                                │
│            │   Bộ quản lý luồng  │                                │
│            │   (Stream Manager)  │                                │
│            └──────────┬──────────┘                                │
└───────────────────────┼────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    ĐƯỜNG ỐNG AI (DeepStream)                      │
│                                                                    │
│  nvstreammux → nvinfer (YOLO) → nvtracker → nvinfer (ReID)       │
│                   │                                                │
│          ┌────────┼────────┐                                      │
│          ▼        ▼        ▼                                      │
│       Người    Lửa/Cháy  Đồ vật                                  │
│          │        │        │                                      │
│          └────────┼────────┘                                      │
│                   ▼                                                │
│          Kafka "detection-events"                                  │
└───────────────────────────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                   BACKEND (Xử lý sự kiện)                         │
│                                                                    │
│  analytics-service ──┬── Lưu PostgreSQL + Qdrant + MinIO         │
│                      ├── Cảnh báo lửa → notification-service      │
│                      └── Cập nhật danh tính → search-service      │
│                                                                    │
│  gateway (WebSocket) ← Cảnh báo thời gian thực → React Dashboard │
└───────────────────────────────────────────────────────────────────┘
```

---

## Giai đoạn 0: Sửa Nền Tảng & Mở Rộng Cấu Trúc (0.5 ngày)

> Cấu trúc hiện tại chỉ hỗ trợ phát hiện người. Cần mở rộng cho đa đối tượng và video thử nghiệm.

- [ ] Cập nhật `docker-compose.yml` — sửa đường dẫn từ cấu trúc cũ sang `apps/`, thêm Triton Inference Server
- [ ] Cập nhật `docker-compose.prod.yml` — thêm tất cả dịch vụ mới
- [ ] Cập nhật `.env.example` — thêm biến cho: loại phát hiện, ngưỡng tin cậy, đường dẫn mô hình
- [ ] Cập nhật `Makefile` — thêm lệnh cho: huấn luyện, xuất mô hình, chạy thử nghiệm video
- [ ] Cập nhật `.gitignore` — thêm: `*.pt`, `*.onnx`, `*.engine`, `datasets/raw/`, `datasets/processed/`
- [ ] Tạo thêm thư mục:
  - `apps/ai-service/src/detectors/` — bộ phát hiện cho từng loại đối tượng
  - `apps/web/src/features/video-test/` — tính năng thử nghiệm video
  - `apps/web/src/features/fire-detection/` — tính năng phát hiện lửa
  - `models/fire/` — mô hình phát hiện lửa
  - `models/objects/` — mô hình phát hiện đồ vật
  - `datasets/fire/`, `datasets/objects/` — bộ dữ liệu cho từng loại
- [ ] Kiểm tra: `docker compose config` không lỗi

---

## Giai đoạn 1: Chuẩn Bị Bộ Dữ Liệu & Gán Nhãn (2 ngày)

> **Đây là bước quan trọng nhất.** Chất lượng mô hình phụ thuộc hoàn toàn vào chất lượng dữ liệu.

### 1.1 Thu thập dữ liệu

- [ ] Thu thập ảnh/video cho **phát hiện người** — tối thiểu 5.000 ảnh từ:
  - Bộ dữ liệu mở: COCO (lớp person), CrowdHuman, MOT17
  - Video tự quay trong môi trường thực tế (văn phòng, hành lang, bãi xe)
- [ ] Thu thập ảnh/video cho **phát hiện lửa/cháy** — tối thiểu 3.000 ảnh từ:
  - Bộ dữ liệu mở: FireNet, FLAME, Kaggle Fire Detection Dataset
  - Tự quay: đốt giấy, khói thuốc, bếp gas (trong điều kiện an toàn)
  - Ảnh tiêu cực: ánh đèn đỏ, ánh hoàng hôn, đèn LED đỏ (để tránh dương tính giả)
- [ ] Thu thập ảnh/video cho **phát hiện đồ vật** (tùy chọn) — tối thiểu 2.000 ảnh/lớp:
  - Dao, súng, ba lô đáng ngờ, xe máy, v.v.
- [ ] Lưu dữ liệu thô vào `datasets/raw/person/`, `datasets/raw/fire/`, `datasets/raw/objects/`

### 1.2 Gán nhãn dữ liệu

- [ ] Cài đặt công cụ gán nhãn: **LabelImg** hoặc **CVAT** hoặc **Roboflow**
- [ ] Viết `scripts/dataset/setup-labeling.sh` — kịch bản cài đặt công cụ gán nhãn
- [ ] Định nghĩa danh sách lớp cho từng mô hình:
  - Mô hình người: `person`
  - Mô hình lửa: `fire`, `smoke`
  - Mô hình đồ vật: `knife`, `gun`, `backpack`, `motorcycle` (tùy chỉnh)
- [ ] Gán nhãn tất cả ảnh theo định dạng **YOLO** (file `.txt` cùng tên ảnh):
  ```
  <class_id> <x_center> <y_center> <width> <height>
  ```
- [ ] Viết `scripts/dataset/validate-labels.py` — kiểm tra:
  - Mỗi ảnh có file nhãn tương ứng
  - Tọa độ nằm trong phạm vi [0, 1]
  - Không có nhãn trống hoặc lỗi
- [ ] Lưu nhãn vào `datasets/annotations/person/`, `datasets/annotations/fire/`, `datasets/annotations/objects/`

### 1.3 Chia bộ dữ liệu & Tạo cấu hình

- [ ] Viết `scripts/dataset/split-dataset.py` — chia dữ liệu theo tỷ lệ:
  - 70% huấn luyện → `datasets/training/{loại}/images/` + `labels/`
  - 20% xác thực → `datasets/validation/{loại}/images/` + `labels/`
  - 10% kiểm tra → `datasets/processed/{loại}/test/images/` + `labels/`
- [ ] Tạo file cấu hình YOLO cho từng bộ dữ liệu:
  - `datasets/person.yaml`:
    ```yaml
    train: datasets/training/person/images
    val: datasets/validation/person/images
    nc: 1
    names: ['person']
    ```
  - `datasets/fire.yaml`:
    ```yaml
    train: datasets/training/fire/images
    val: datasets/validation/fire/images
    nc: 2
    names: ['fire', 'smoke']
    ```
  - `datasets/objects.yaml` — tương tự cho đồ vật
- [ ] Viết `scripts/dataset/augment-data.py` — tăng cường dữ liệu:
  - Lật ngang, xoay ±15°, thay đổi độ sáng, thêm nhiễu
  - Đặc biệt cho lửa: thay đổi tông màu, mờ gaussian
- [ ] Kiểm tra: xác nhận số lượng ảnh/nhãn khớp, phân bố lớp cân bằng

---

## Giai đoạn 2: Huấn Luyện Mô Hình YOLO (3 ngày)

> **Giới hạn phần cứng:** GTX 1650 Max-Q (4GB VRAM) → dùng YOLOv8n (nano) hoặc YOLOv8s (small).
> Nếu VRAM không đủ, giảm batch_size xuống 8 hoặc dùng Google Colab.

### 2.1 Thiết lập môi trường huấn luyện

- [ ] Viết `scripts/setup/setup-training-env.sh` — cài đặt:
  ```bash
  pip install ultralytics torch torchvision
  pip install albumentations wandb tensorboard
  ```
- [ ] Viết `models/configs/training/person_train.yaml` — siêu tham số huấn luyện:
  ```yaml
  model: yolov8n.pt          # Mô hình gốc (pretrained)
  data: datasets/person.yaml
  epochs: 100
  batch: 16                   # Giảm xuống 8 nếu hết VRAM
  imgsz: 640
  device: 0                   # GPU đầu tiên
  patience: 20                # Dừng sớm nếu 20 epoch không cải thiện
  optimizer: AdamW
  lr0: 0.001
  lrf: 0.01
  augment: true
  mosaic: 1.0
  mixup: 0.1
  project: models/checkpoints/person
  name: yolov8n_person
  ```
- [ ] Viết tương tự cho lửa: `models/configs/training/fire_train.yaml`
- [ ] Viết tương tự cho đồ vật: `models/configs/training/objects_train.yaml`

### 2.2 Kịch bản huấn luyện

- [ ] Viết `models/scripts/train_person.py` — huấn luyện mô hình phát hiện người:
  ```python
  from ultralytics import YOLO
  
  model = YOLO('yolov8n.pt')  # Tải mô hình pretrained
  results = model.train(
      data='datasets/person.yaml',
      epochs=100,
      batch=16,
      imgsz=640,
      device=0,
      project='models/checkpoints/person',
      name='yolov8n_person_v1'
  )
  ```
- [ ] Viết `models/scripts/train_fire.py` — huấn luyện mô hình phát hiện lửa/khói
- [ ] Viết `models/scripts/train_objects.py` — huấn luyện mô hình phát hiện đồ vật
- [ ] Viết `models/scripts/train_all.py` — kịch bản tổng hợp: huấn luyện tuần tự tất cả mô hình
- [ ] Viết `models/scripts/resume_training.py` — tiếp tục huấn luyện từ checkpoint nếu bị gián đoạn:
  ```python
  model = YOLO('models/checkpoints/person/yolov8n_person_v1/weights/last.pt')
  model.train(resume=True)
  ```

### 2.3 Đánh giá & Tinh chỉnh mô hình

- [ ] Viết `models/scripts/evaluate_model.py` — đánh giá mô hình trên tập kiểm tra:
  ```python
  model = YOLO('models/checkpoints/person/yolov8n_person_v1/weights/best.pt')
  metrics = model.val(data='datasets/person.yaml')
  # In: mAP50, mAP50-95, Precision, Recall
  ```
- [ ] Viết `models/scripts/compare_models.py` — so sánh hiệu suất giữa các phiên bản:
  - Bảng so sánh: mAP50, FPS, kích thước mô hình, VRAM sử dụng
- [ ] Viết `models/scripts/confusion_matrix.py` — vẽ ma trận nhầm lẫn cho từng mô hình
- [ ] Viết `models/scripts/visualize_predictions.py` — lưu ảnh kết quả phát hiện để kiểm tra bằng mắt
- [ ] Mục tiêu hiệu suất tối thiểu:
  - Phát hiện người: mAP50 ≥ 0.85, FPS ≥ 25
  - Phát hiện lửa: mAP50 ≥ 0.80, FPS ≥ 25
  - Phát hiện đồ vật: mAP50 ≥ 0.75, FPS ≥ 25

### 2.4 Xuất mô hình cho triển khai

- [ ] Viết `models/scripts/export_yolov8.py` — xuất mô hình tốt nhất:
  ```python
  model = YOLO('models/checkpoints/person/best.pt')
  # Xuất ONNX
  model.export(format='onnx', dynamic=True, simplify=True)
  # Xuất TensorRT (cho DeepStream)
  model.export(format='engine', device=0, half=True)  # FP16 cho GTX 1650
  ```
- [ ] Viết `models/scripts/export_fire.py` — tương tự cho mô hình lửa
- [ ] Viết `models/scripts/export_objects.py` — tương tự cho mô hình đồ vật
- [ ] Viết `models/scripts/benchmark_models.py` — đo hiệu năng trên GTX 1650:
  - FPS, độ trễ, VRAM cho từng mô hình (FP32 vs FP16)
  - Kiểm tra tổng VRAM khi chạy tất cả mô hình đồng thời
- [ ] Lưu kết quả vào:
  - `models/yolo/person_best.pt`, `models/yolo/person_best.onnx`
  - `models/fire/fire_best.pt`, `models/fire/fire_best.onnx`
  - `models/objects/objects_best.pt`, `models/objects/objects_best.onnx`
  - `models/tensorrt/person_fp16.engine`, `models/tensorrt/fire_fp16.engine`
- [ ] Kiểm tra: tất cả engine TensorRT chạy được trên GTX 1650

---

## Giai đoạn 3: Các Gói Dùng Chung (2 ngày)

> Xây nền tảng thư viện dùng chung trước khi viết code cho bất kỳ dịch vụ nào.

### 3.1 `packages/domain/` — Thực thể miền & Đối tượng giá trị

- [ ] Viết `entities/camera.py` — Camera: mã, tên, URL RTSP, vị trí, trạng thái, FPS
- [ ] Viết `entities/person.py` — Người: mã toàn cục, tên hiển thị, lần đầu xuất hiện, tổng lần xuất hiện
- [ ] Viết `entities/detection_event.py` — Sự kiện phát hiện: loại đối tượng (người/lửa/đồ vật), mã camera, khung bao, độ tin cậy, mốc thời gian
- [ ] Viết `entities/fire_event.py` — Sự kiện lửa: mức độ nghiêm trọng, diện tích lửa, tốc độ lan, camera_id
- [ ] Viết `entities/alert.py` — Cảnh báo: loại (lửa/xâm nhập/đồ vật nguy hiểm), mức độ, tiêu đề, camera
- [ ] Viết `value_objects/bounding_box.py` — Khung bao: x, y, rộng, cao + diện tích(), IoU(), tâm()
- [ ] Viết `value_objects/embedding.py` — Vector đặc trưng: mảng, số chiều, chuẩn hóa(), khoảng cách cosine()
- [ ] Viết `value_objects/detection_class.py` — Lớp phát hiện: tên, mã, ngưỡng tin cậy, màu hiển thị
- [ ] Viết `enums/detection_type.py` — Loại phát hiện: NGƯỜI, LỬA, KHÓI, ĐỒ_VẬT
- [ ] Viết `enums/camera_status.py` — Trạng thái camera: ĐÃ KẾT NỐI, MẤT KẾT NỐI, LỖI, BẢO TRÌ
- [ ] Viết `enums/alert_severity.py` — Mức độ: THÔNG TIN, CẢNH BÁO, NGHIÊM TRỌNG, KHẨN CẤP
- [ ] Thiết lập `pyproject.toml` — phụ thuộc, phiên bản
- [ ] Kiểm tra: kiểm thử đơn vị cho tất cả thực thể và đối tượng giá trị

### 3.2 `packages/contracts/` — Hợp đồng dữ liệu

- [ ] Viết `dto/camera.py` — Pydantic v2: TạoCamera, CậpNhậtCamera, PhảnHồiCamera
- [ ] Viết `dto/detection.py` — PhảnHồiPhátHiện, DanhSáchPhátHiện (chung cho tất cả loại)
- [ ] Viết `dto/person.py` — PhảnHồiNgười, TómTắtNgười
- [ ] Viết `dto/fire.py` — PhảnHồiSựKiệnLửa, ThốngKêLửa
- [ ] Viết `dto/alert.py` — TạoCảnhBáo, PhảnHồiCảnhBáo
- [ ] Viết `dto/search.py` — YêuCầuTìmTheoẢnh, KếtQuảTìm
- [ ] Viết `dto/video_test.py` — YêuCầuThửNghiệmVideo, KếtQuảThửNghiệm, TrạngTháiThửNghiệm
- [ ] Viết `events/detection_event.py` — Sự kiện Kafka: SựKiệnPhátHiệnĐượcTạo (đa loại)
- [ ] Viết `events/alert_event.py` — CảnhBáoĐượcTạo
- [ ] Viết `events/camera_event.py` — ThayĐổiTrạngTháiCamera
- [ ] Viết lược đồ Avro + Protobuf tương ứng
- [ ] Kiểm tra: xác nhận tất cả DTO serialize/deserialize đúng

### 3.3 `packages/shared/` — Tiện ích dùng chung

- [ ] Viết `config/base_settings.py` — Cấu hình Pydantic cơ bản
- [ ] Viết `constants/kafka_topics.py` — Chủ đề: DETECTION_EVENTS, ALERT_EVENTS, VIDEO_TEST_EVENTS
- [ ] Viết `constants/detection_classes.py` — Ánh xạ lớp phát hiện: {0: 'person', 1: 'fire', 2: 'smoke', ...}
- [ ] Viết `exceptions/`, `logger/`, `middleware/`, `decorators/`, `helpers/`, `utils/`
  - (Giống plan cũ — ngoại lệ, ghi nhật ký, trung gian, thử lại, phân trang, xác thực)
- [ ] Kiểm tra: kiểm thử đơn vị

### 3.4 `packages/testing/` — Hạ tầng kiểm thử

- [ ] Viết fixtures, factories, mocks (giống plan cũ)
- [ ] Thêm `factories/detection_factory.py` — tạo dữ liệu phát hiện giả lập cho tất cả loại
- [ ] Kiểm tra: factories tạo dữ liệu hợp lệ

---

## Giai đoạn 4: Tầng Cơ Sở Dữ Liệu (1.5 ngày)

### 4.1 Lược đồ & Di trú

- [ ] Viết `database/postgres/schema.sql` — DDL đầy đủ:
  - Bảng `cameras` — mã, tên, URL RTSP, vị trí, trạng thái
  - Bảng `detection_events` — mã, loại (person/fire/smoke/object), camera_id, khung bao, độ tin cậy, mốc thời gian
  - Bảng `persons` — mã toàn cục, tên, lần đầu xuất hiện, vector đặc trưng
  - Bảng `fire_events` — mã, camera_id, mức độ, diện tích, mốc bắt đầu, mốc kết thúc
  - Bảng `alerts` — mã, loại, mức độ, tiêu đề, camera_id, trạng thái
  - Bảng `users`, `roles` — xác thực
  - Bảng `video_tests` — mã, tên file, URL, trạng thái (đang xử lý/hoàn thành/lỗi), kết quả JSON
- [ ] Thiết lập Alembic trong `database/postgres/migrations/`
- [ ] Tạo di trú ban đầu
- [ ] Viết dữ liệu mẫu (seed) cho camera, người dùng
- [ ] Viết cấu hình Kafka topics, MinIO buckets, Redis
- [ ] Kiểm tra: khởi động PostgreSQL → áp dụng di trú → nạp dữ liệu → truy vấn thành công

### 4.2 Thiết lập Qdrant

- [ ] Tạo bộ sưu tập `person_embeddings` (512 chiều, cosine, HNSW)
- [ ] Kiểm tra: chèn và truy vấn vector thử nghiệm thành công

---

## Giai đoạn 5: Các Dịch Vụ Backend (8 ngày)

> Thứ tự: xác thực → camera → tìm kiếm → phân tích → thông báo → lập lịch → cổng API

### 5.1 `apps/auth-service/` — Xác thực (1 ngày)

- [ ] Viết mô hình Người dùng, Vai trò (SQLAlchemy)
- [ ] Viết dịch vụ xác thực: đăng ký, đăng nhập, tạo/xác thực JWT, làm mới token
- [ ] Viết API: POST /đăng-nhập, POST /đăng-ký, POST /làm-mới, GET /thông-tin
- [ ] Viết Dockerfile, pyproject.toml
- [ ] Kiểm tra: kiểm thử đơn vị + kiểm thử API luồng đăng nhập

### 5.2 `apps/camera-service/` — Quản lý camera (1 ngày)

- [ ] Viết mô hình Camera, Nhóm camera (SQLAlchemy)
- [ ] Viết dịch vụ: CRUD + kiểm tra sức khỏe RTSP + phân nhóm theo khu vực
- [ ] **MỞ RỘNG:** Thêm API nhận video thử nghiệm:
  - POST /cameras/test-video — tải video lên (multipart/form-data)
  - POST /cameras/test-url — gửi đường dẫn video (URL hoặc RTSP)
  - GET /cameras/test/{test_id}/status — kiểm tra trạng thái xử lý
  - GET /cameras/test/{test_id}/results — lấy kết quả phát hiện
- [ ] Viết Dockerfile, pyproject.toml
- [ ] Kiểm tra: kiểm thử CRUD camera + kiểm thử tải video

### 5.3 `apps/search-service/` — Tìm kiếm (1.5 ngày)

- [ ] Viết kho vector Qdrant: chèn, tìm kiếm, xóa vector đặc trưng
- [ ] Viết logic tương đồng cosine + xếp hạng lại
- [ ] Viết lập chỉ mục vector từ sự kiện Kafka
- [ ] Viết API: POST /tìm-kiếm/theo-ảnh, GET /tìm-kiếm/theo-văn-bản, GET /tìm-kiếm/theo-mã-người
- [ ] Kiểm tra: kiểm thử tìm kiếm vector (giả lập Qdrant)

### 5.4 `apps/analytics-service/` — Phân tích - Kiến trúc sạch (2 ngày)

#### Tầng miền
- [ ] Viết thực thể: SựKiệnPhátHiện, DanhTínhNgười, SựKiệnLửa, KhuVực
- [ ] Viết đối tượng giá trị: KhungBao, VectorĐặcTrưng, VịTríCamera
- [ ] Viết giao diện kho: TrackingRepository, PersonRepository, FireEventRepository
- [ ] Viết dịch vụ miền: theo dõi, bản đồ nhiệt, phân tích lửa

#### Tầng ứng dụng
- [ ] Viết ca sử dụng: XửLýSựKiệnPhátHiện (xử lý chung cho tất cả loại đối tượng)
- [ ] Viết ca sử dụng: XửLýCảnhBáoLửa (phát hiện lửa → tạo cảnh báo KHẨN CẤP ngay lập tức)
- [ ] Viết ca sử dụng: TạoPhânTích (thống kê bảng điều khiển)
- [ ] Viết ca sử dụng: LấyLộTrìnhNgười (lộ trình qua các camera)
- [ ] Viết DTO chuyển đổi

#### Tầng hạ tầng
- [ ] Viết hiện thực cụ thể các kho (SQLAlchemy)
- [ ] Viết Kafka consumer: tiêu thụ chủ đề detection-events
- [ ] Viết Kafka producer: phát hành sự kiện cảnh báo
- [ ] Viết kết nối Qdrant + MinIO

#### Tầng trình bày
- [ ] Viết API: GET /phát-hiện/sự-kiện, GET /phát-hiện/lửa, GET /phân-tích/bảng-điều-khiển, GET /theo-dõi/lộ-trình/{mã_người}
- [ ] Viết Kafka consumer entry point
- [ ] Kiểm tra: kiểm thử miền, kiểm thử ca sử dụng, kiểm thử API

### 5.5 `apps/notification-service/` — Thông báo (1 ngày)

- [ ] Viết các kênh: WebSocket, email, webhook
- [ ] **MỞ RỘNG:** Viết quy tắc cảnh báo tùy chỉnh:
  - Lửa phát hiện → cảnh báo KHẨN CẤP (ngay lập tức, tất cả kênh)
  - Đồ vật nguy hiểm → cảnh báo NGHIÊM TRỌNG
  - Người xâm nhập khu vực cấm → cảnh báo CẢNH BÁO
- [ ] Viết Kafka consumer, API cảnh báo, mẫu email
- [ ] Kiểm tra: kiểm thử các kênh + kiểm thử quy tắc cảnh báo

### 5.6 `apps/scheduler-service/` — Lập lịch (0.5 ngày)

- [ ] Viết công việc: dọn dẹp dữ liệu cũ, kiểm tra sức khỏe camera, tạo báo cáo, đồng bộ vector
- [ ] Kiểm tra: kiểm thử thực thi công việc

### 5.7 `apps/gateway/` — Cổng API (1 ngày)

- [ ] Viết xác thực JWT, phân quyền RBAC, giới hạn tốc độ
- [ ] Viết quản lý WebSocket: kết nối, phát sóng cảnh báo thời gian thực
- [ ] **MỞ RỘNG:** Viết tuyến proxy cho API thử nghiệm video:
  - POST /api/v1/test/upload-video → chuyển tiếp đến camera-service
  - POST /api/v1/test/video-url → chuyển tiếp đến camera-service
  - GET /api/v1/test/{id}/status → trạng thái xử lý
  - GET /api/v1/test/{id}/results → kết quả phát hiện
- [ ] Viết tuyến proxy cho tất cả dịch vụ phía dưới
- [ ] Kiểm tra: kiểm thử chuyển tiếp + WebSocket

---

## Giai đoạn 6: Đường Ống AI — DeepStream (5 ngày)

### 6.1 Cấu hình đa mô hình (1 ngày)

- [ ] Viết `configs/deepstream_app.yml` — cấu hình đường ống:
  - Nguồn: RTSP + file video (cho thử nghiệm)
  - Bộ ghép: nvstreammux (đa luồng)
  - Phát hiện chính (PGIE): YOLO người
  - Phát hiện phụ 1 (SGIE-1): YOLO lửa/khói
  - Phát hiện phụ 2 (SGIE-2): YOLO đồ vật (tùy chọn)
  - Bộ theo dõi: NvDCF
  - Suy luận phụ (SGIE-3): ReID (chỉ cho người)
- [ ] Viết `configs/pgie_person.txt` — cấu hình nvinfer cho phát hiện người:
  ```
  [property]
  gpu-id=0
  net-scale-factor=0.00392157
  model-engine-file=models/tensorrt/person_fp16.engine
  labelfile-path=labels/person.txt
  batch-size=4
  network-mode=2  # FP16
  num-detected-classes=1
  interval=0      # Suy luận mỗi khung hình
  gie-unique-id=1
  ```
- [ ] Viết `configs/sgie_fire.txt` — cấu hình cho phát hiện lửa
- [ ] Viết `configs/sgie_objects.txt` — cấu hình cho phát hiện đồ vật
- [ ] Viết `configs/sgie_reid.txt` — cấu hình ReID (chỉ áp dụng cho lớp "person")
- [ ] Viết `configs/tracker_config.yml` — tham số bộ theo dõi NvDCF

### 6.2 Lõi đường ống & Đa bộ phát hiện (2 ngày)

- [ ] Viết `src/detectors/__init__.py` — bộ quản lý các mô hình phát hiện
- [ ] Viết `src/detectors/person_detector.py` — bộ phát hiện người (PGIE)
- [ ] Viết `src/detectors/fire_detector.py` — bộ phát hiện lửa/khói (SGIE)
- [ ] Viết `src/detectors/object_detector.py` — bộ phát hiện đồ vật (SGIE)
- [ ] Viết `src/pipelines/pipeline_builder.py` — API xây dựng đường ống:
  ```python
  pipeline = PipelineBuilder() \
      .add_source(rtsp_url_or_file_path) \
      .add_detector('person', 'configs/pgie_person.txt') \
      .add_detector('fire', 'configs/sgie_fire.txt') \
      .add_tracker('configs/tracker_config.yml') \
      .add_reid('configs/sgie_reid.txt', for_class='person') \
      .build()
  ```
- [ ] Viết `src/pipelines/deepstream_pipeline.py` — đường ống GStreamer hoàn chỉnh
- [ ] Viết `src/stream/rtsp_source.py` — kết nối RTSP với tự kết nối lại
- [ ] Viết `src/stream/file_source.py` — **MỚI:** đọc video file (MP4, AVI) cho thử nghiệm
- [ ] Viết `src/stream/stream_manager.py` — quản lý vòng đời đa luồng (RTSP + file)
- [ ] Viết `src/inference/detector.py` — phân tích khung bao YOLO
- [ ] Viết `src/inference/batch_processor.py` — xử lý theo lô
- [ ] Viết `src/plugins/probe_callbacks.py` — hàm thăm dò GStreamer: trích xuất siêu dữ liệu tất cả loại phát hiện
- [ ] Viết `src/plugins/custom_parser.py` — phân tích đầu ra YOLO tùy chỉnh
- [ ] Kiểm tra: đường ống khởi động, xử lý 1 file video, phát hiện người + lửa

### 6.3 ReID & Theo dõi xuyên camera (1 ngày)

- [ ] Viết `src/reid/feature_extractor.py` — trích xuất vector 512 chiều từ ảnh cắt người
- [ ] Viết `src/reid/gallery_manager.py` — thư viện nhận dạng: thêm, cập nhật, tìm gần nhất
- [ ] Viết `src/reid/spatial_constraints.py` — topo camera: ràng buộc chuyển tiếp
- [ ] Viết `src/reid/mtmc_association.py` — khớp đa mục tiêu đa camera
- [ ] Viết `src/utils/` — khung bao, NMS, vector đặc trưng, giám sát GPU
- [ ] Kiểm tra: kiểm thử khớp ReID trên video đã ghi

### 6.4 Phát hành sự kiện & Cơ chế thử nghiệm video (1 ngày)

- [ ] Viết `src/events/kafka_producer.py` — phát hành sự kiện phát hiện đa loại
- [ ] Viết `src/events/event_schemas.py` — lược đồ sự kiện (nhập từ packages/contracts)
- [ ] Viết `src/storage/crop_saver.py` — lưu ảnh cắt người/lửa vào MinIO
- [ ] **MỚI:** Viết `src/test_runner/__init__.py` — bộ chạy thử nghiệm video
- [ ] **MỚI:** Viết `src/test_runner/video_processor.py` — xử lý video thử nghiệm:
  ```python
  class VideoTestProcessor:
      """Nhận file video hoặc URL → chạy qua đường ống → trả kết quả."""
      
      async def process_video(self, source: str, test_id: str):
          # 1. Tải video (nếu URL) hoặc đọc file
          # 2. Tạo đường ống DeepStream với file_source
          # 3. Chạy suy luận frame-by-frame
          # 4. Thu thập kết quả: danh sách phát hiện, số đếm, ảnh cắt
          # 5. Lưu kết quả vào DB + MinIO
          # 6. Cập nhật trạng thái: hoàn thành
          pass
  ```
- [ ] **MỚI:** Viết `src/test_runner/result_aggregator.py` — tổng hợp kết quả:
  - Tổng số phát hiện theo loại (người, lửa, đồ vật)
  - Khung hình có phát hiện / tổng khung hình
  - Thời gian xử lý, FPS trung bình
  - Ảnh cắt tiêu biểu cho mỗi phát hiện
  - Dòng thời gian phát hiện (phát hiện nào tại giây nào)
- [ ] Viết `src/main.py` — điểm vào: hỗ trợ 2 chế độ:
  - Chế độ sản xuất: xử lý RTSP liên tục
  - Chế độ thử nghiệm: xử lý 1 video → trả kết quả → thoát
- [ ] Viết `Dockerfile` — dựa trên nvcr.io/nvidia/deepstream:7.x
- [ ] Kiểm tra: chạy thử nghiệm video file → sự kiện Kafka → kết quả lưu DB

---

## Giai đoạn 7: Giao Diện Dashboard (6 ngày)

### 7.1 Thiết lập nền tảng (0.5 ngày)

- [ ] Thiết lập Vite + React + TypeScript
- [ ] Cài đặt phụ thuộc: react-router, zustand, @tanstack/react-query, axios, socket.io-client, leaflet, recharts, thư viện UI
- [ ] Viết biến thiết kế CSS, kiểu toàn cục, chế độ tối
- [ ] Viết api-client (Axios + JWT), kiểu TypeScript, nhà cung cấp, bộ định tuyến, App gốc

### 7.2 Bố cục & Thành phần chung (1 ngày)

- [ ] Viết Sidebar, Header, MainLayout
- [ ] Viết thành phần chung: Button, Modal, Table, Badge, Spinner
- [ ] Viết hook chung: useWebSocket, useAuth
- [ ] Kiểm tra: hiển thị trực quan

### 7.3 Tính năng: Bảng điều khiển (0.5 ngày)

- [ ] **MỞ RỘNG:** Thẻ thống kê cho ĐA LOẠI phát hiện:
  - Tổng người phát hiện hôm nay
  - Tổng cảnh báo lửa hôm nay
  - Tổng đồ vật phát hiện
  - Số camera đang hoạt động
- [ ] Biểu đồ hoạt động: phân biệt màu cho người (xanh), lửa (đỏ), đồ vật (vàng)
- [ ] Danh sách cảnh báo gần đây (ưu tiên lửa)
- [ ] Kiểm tra: hiển thị với dữ liệu giả lập

### 7.4 Tính năng: Giám sát trực tiếp (1 ngày)

- [ ] Viết trình phát video (HLS.js/WebRTC) với điều khiển
- [ ] Viết lưới camera đáp ứng: 1x1, 2x2, 3x3, 4x4
- [ ] **MỞ RỘNG:** Lớp phủ đa loại phát hiện:
  - Khung bao XANH cho người + mã theo dõi
  - Khung bao ĐỎ NHẤP NHÁY cho lửa + biểu tượng cảnh báo
  - Khung bao VÀNG cho đồ vật + tên lớp
- [ ] WebSocket thời gian thực: nhận phát hiện → vẽ lên canvas
- [ ] Kiểm tra: video phát, lớp phủ hiển thị đúng loại

### 7.5 Tính năng: Thử nghiệm video ⭐ MỚI (1 ngày)

> **Đây là tính năng quan trọng cho giai đoạn phát triển — thử nghiệm mô hình mà không cần camera thật.**

- [ ] Viết `features/video-test/VideoTestPage.tsx` — trang thử nghiệm video:
  - **Tab 1: Tải video lên** — kéo thả file MP4/AVI/MKV (tối đa 500MB)
  - **Tab 2: Dán đường dẫn** — nhập URL video (YouTube, đường dẫn trực tiếp, RTSP)
  - Nút "Bắt đầu phân tích"
- [ ] Viết `features/video-test/components/VideoUploader.tsx`:
  - Kéo thả + nhấp chọn file
  - Thanh tiến trình tải lên
  - Xem trước video sau khi tải
- [ ] Viết `features/video-test/components/UrlInput.tsx`:
  - Ô nhập URL + xác thực định dạng
  - Hỗ trợ: URL trực tiếp (.mp4), RTSP (rtsp://...), YouTube (tùy chọn)
- [ ] Viết `features/video-test/components/AnalysisProgress.tsx`:
  - Thanh tiến trình: % khung hình đã xử lý
  - Hiển thị thời gian thực: FPS, số phát hiện đang tăng
  - WebSocket cập nhật trạng thái liên tục
- [ ] Viết `features/video-test/components/TestResults.tsx`:
  - **Tóm tắt:** tổng phát hiện (người, lửa, đồ vật), FPS trung bình, thời gian xử lý
  - **Dòng thời gian:** biểu đồ phát hiện theo thời gian (giây nào phát hiện gì)
  - **Khung hình tiêu biểu:** ảnh có khung bao đã vẽ
  - **Bảng chi tiết:** danh sách mỗi phát hiện (loại, tin cậy, khung hình, khung bao)
  - Nút "Tải kết quả JSON" + "Tải video đã chú thích"
- [ ] Viết `features/video-test/components/AnnotatedVideoPlayer.tsx`:
  - Phát lại video gốc VỚI khung bao phát hiện được vẽ chồng lên
  - Thanh trượt thời gian: nhảy đến các điểm có phát hiện
- [ ] Kiểm tra: tải video → xử lý → hiển thị kết quả

### 7.6 Tính năng: Phát hiện lửa ⭐ MỚI (0.5 ngày)

- [ ] Viết `features/fire-detection/FireDetectionPage.tsx`:
  - Bản đồ camera + đánh dấu camera có phát hiện lửa (BIỂU TƯỢNG LỬA ĐỎ)
  - Lịch sử sự kiện lửa: thời gian, camera, mức độ, ảnh chụp
  - Thống kê: tổng sự kiện lửa, thời gian phản hồi trung bình
- [ ] Kiểm tra: hiển thị sự kiện lửa giả lập

### 7.7 Tính năng còn lại (1.5 ngày)

- [ ] Tìm kiếm người: tải ảnh → tìm kiếm → kết quả + xem lộ trình
- [ ] Lịch sử theo dõi: bản đồ lộ trình + dòng thời gian
- [ ] Quản lý camera: bảng CRUD + kiểm tra sức khỏe
- [ ] Trung tâm cảnh báo: lọc theo loại (lửa/người/đồ vật) + đánh dấu đã đọc
- [ ] Cài đặt: tùy chọn cảnh báo, kênh thông báo, ngưỡng tin cậy
- [ ] Viết Dockerfile
- [ ] Kiểm tra: tất cả trang hiển thị, điều hướng, đáp ứng

---

## Giai đoạn 8: Tích Hợp & Kiểm Thử (3 ngày)

### 8.1 Tích hợp dịch vụ (1.5 ngày)

- [ ] Thử nghiệm: đường ống AI → Kafka → dịch vụ phân tích (đầu-cuối với video thử nghiệm)
- [ ] Thử nghiệm: phát hiện lửa → cảnh báo KHẨN CẤP → WebSocket → giao diện (< 3 giây)
- [ ] Thử nghiệm: phát hiện người → vector Qdrant → tìm kiếm bằng ảnh
- [ ] Thử nghiệm: tải video thử nghiệm → kết quả hiển thị trên giao diện
- [ ] Thử nghiệm: cổng API chuyển tiếp → tất cả dịch vụ
- [ ] Viết `tests/integration/test_ai_to_kafka.py`
- [ ] Viết `tests/integration/test_fire_alert_pipeline.py`
- [ ] Viết `tests/integration/test_video_test_flow.py`

### 8.2 Kiểm thử đầu-cuối (1 ngày)

- [ ] Viết `tests/e2e/test_full_detection_flow.py` — Video → AI → Kafka → DB → API → Giao diện
- [ ] Viết `tests/e2e/test_fire_detection.py` — Video có lửa → phát hiện → cảnh báo → thông báo
- [ ] Viết `tests/e2e/test_video_upload.py` — Tải video → xử lý → kết quả
- [ ] Viết `tests/e2e/test_person_search.py` — Tải ảnh → tìm kiếm → kết quả
- [ ] Thiết lập Playwright cho kiểm thử giao diện
- [ ] Kiểm tra: toàn bộ chạy trên docker compose

### 8.3 Kiểm thử tải & sức chịu (0.5 ngày)

- [ ] Viết kiểm thử Locust: API + tải video đồng thời
- [ ] Viết kiểm thử GPU: 2-4 luồng đồng thời + 3 mô hình YOLO trên GTX 1650
- [ ] Ghi lại kết quả vào `docs/benchmark/`

---

## Giai đoạn 9: Giám Sát & Quan Sát (2 ngày)

- [ ] Viết cấu hình Prometheus: thu thập chỉ số từ tất cả dịch vụ
- [ ] Viết quy tắc cảnh báo: dịch vụ ngừng, GPU > 90%, Kafka trễ > 1000, phát hiện lửa (tích hợp với alertmanager)
- [ ] Viết bảng điều khiển Grafana:
  - Tổng quan hệ thống: sức khỏe, tốc độ yêu cầu, tỷ lệ lỗi
  - Đường ống AI: GPU, FPS, số phát hiện theo loại, VRAM
  - **Bảng điều khiển lửa:** biểu đồ sự kiện lửa, thời gian phản hồi, dương tính giả
- [ ] Viết cấu hình Loki (nhật ký), Tempo (theo dõi phân tán), Alertmanager
- [ ] Kiểm tra: bảng điều khiển Grafana hoạt động

---

## Giai đoạn 10: CI/CD & Vận Hành (2 ngày)

- [ ] Viết `.github/workflows/ci.yml` — kiểm tra mã + kiểm thử đơn vị + xây Docker
- [ ] Viết `.github/workflows/cd-staging.yml` — triển khai dàn dựng
- [ ] Viết `.github/workflows/cd-production.yml` — triển khai sản xuất
- [ ] Viết `.github/workflows/ai-model-test.yml` — kiểm thử mô hình AI trên GPU
- [ ] Viết tệp kê khai Kubernetes cơ bản + lớp phủ dàn dựng/sản xuất
- [ ] Viết cấu hình Nginx proxy ngược
- [ ] Kiểm tra: chạy thử trên K8s

---

## Giai đoạn 11: Tài Liệu & Hoàn Thiện (1.5 ngày)

- [ ] Viết tài liệu kiến trúc hệ thống (sơ đồ Mermaid)
- [ ] Viết tài liệu API (gateway, camera, tìm kiếm, phân tích)
- [ ] Viết hướng dẫn triển khai (Docker, K8s, GPU)
- [ ] Viết tài liệu ERD + sơ đồ tuần tự
- [ ] **MỚI:** Viết hướng dẫn huấn luyện mô hình:
  - Cách thu thập và gán nhãn dữ liệu
  - Cách huấn luyện YOLO tùy chỉnh
  - Cách đánh giá và xuất mô hình
  - Cách cập nhật mô hình trong đường ống đang chạy
- [ ] **MỚI:** Viết hướng dẫn thử nghiệm video:
  - Cách sử dụng giao diện thử nghiệm
  - Định dạng video hỗ trợ
  - Cách đọc kết quả
- [ ] Viết bản ghi quyết định kiến trúc (ADR)
- [ ] Cập nhật README.md hoàn chỉnh

---

## Tổng kết thời gian

| Giai đoạn | Nội dung | Ước lượng |
|:----------|:---------|:----------|
| **GĐ 0** | Sửa nền tảng & mở rộng cấu trúc | 0.5 ngày |
| **GĐ 1** | Chuẩn bị bộ dữ liệu & gán nhãn | 2 ngày |
| **GĐ 2** | Huấn luyện mô hình YOLO (người, lửa, đồ vật) | 3 ngày |
| **GĐ 3** | Các gói dùng chung | 2 ngày |
| **GĐ 4** | Tầng cơ sở dữ liệu | 1.5 ngày |
| **GĐ 5** | Các dịch vụ Backend (8 dịch vụ) | 8 ngày |
| **GĐ 6** | Đường ống AI DeepStream (đa mô hình) | 5 ngày |
| **GĐ 7** | Giao diện Dashboard (9 tính năng) | 6 ngày |
| **GĐ 8** | Tích hợp & kiểm thử | 3 ngày |
| **GĐ 9** | Giám sát & quan sát | 2 ngày |
| **GĐ 10** | CI/CD & vận hành | 2 ngày |
| **GĐ 11** | Tài liệu & hoàn thiện | 1.5 ngày |
| | **TỔNG CỘNG** | **~36.5 ngày** |

---

## Quy trình huấn luyện YOLO — Tham khảo nhanh

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. Thu thập  │───▶│ 2. Gán nhãn  │───▶│ 3. Huấn luyện│───▶│ 4. Đánh giá  │
│    dữ liệu   │    │  (LabelImg/  │    │  (ultralytics│    │  (mAP, FPS,  │
│    (ảnh/video)│    │   CVAT)      │    │   YOLO)      │    │   ma trận)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                          ĐẠT?    │   KHÔNG ĐẠT?
                                                          ┌────────▼────────┐
                                                          │                 │
                                                     ┌────▼───┐      ┌─────▼─────┐
                                                     │5. Xuất │      │ Quay lại   │
                                                     │ ONNX → │      │ bước 1-3:  │
                                                     │ TensorRT│     │ thêm dữ liệu│
                                                     └────┬───┘      │ tinh chỉnh  │
                                                          │          │ siêu tham số │
                                                     ┌────▼───┐     └─────────────┘
                                                     │6. Triển│
                                                     │  khai  │
                                                     │DeepStream│
                                                     └────────┘
```

### Lệnh huấn luyện nhanh (tham khảo)

```bash
# Huấn luyện mô hình phát hiện người
python models/scripts/train_person.py

# Hoặc dùng CLI ultralytics trực tiếp
yolo detect train \
  model=yolov8n.pt \
  data=datasets/person.yaml \
  epochs=100 \
  batch=16 \
  imgsz=640 \
  device=0 \
  project=models/checkpoints/person \
  name=v1

# Đánh giá
yolo detect val \
  model=models/checkpoints/person/v1/weights/best.pt \
  data=datasets/person.yaml

# Xuất TensorRT
yolo export \
  model=models/checkpoints/person/v1/weights/best.pt \
  format=engine \
  device=0 \
  half=True

# Thử nghiệm trên 1 video
yolo detect predict \
  model=models/checkpoints/person/v1/weights/best.pt \
  source=test_video.mp4 \
  save=True \
  conf=0.5
```

---

## Câu hỏi mở

1. **Đồ vật cụ thể** — Bạn muốn phát hiện những đồ vật nào ngoài người và lửa? (dao, súng, ba lô, xe máy,...)
2. **Dữ liệu huấn luyện** — Bạn đã có dữ liệu riêng chưa, hay dùng hoàn toàn bộ dữ liệu mở?
3. **Thư viện giao diện** — Ant Design (nhiều component sẵn) hay Shadcn/ui (hiện đại, tùy biến)?
4. **Hỗ trợ YouTube** — Có cần tải video từ YouTube để thử nghiệm không? (cần thêm yt-dlp)

---

> **Cập nhật:** 2026-07-16 · **Phiên bản:** 2.0 (Mở rộng: đa phát hiện + huấn luyện + thử nghiệm video)
