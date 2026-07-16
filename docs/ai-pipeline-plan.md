# 🗺️ Kế Hoạch Triển Khai: Luồng Xử Lý AI (AI Pipeline)

> **Công nghệ sử dụng:** **NVIDIA DeepStream 7.x** + **TensorRT 10.x** + **Python (PyDS)**.
> **Lý do:** DeepStream chạy toàn bộ đường ống trên bộ nhớ GPU (NVMM), giảm thiểu overhead sao chép dữ liệu giữa CPU-GPU. Điều này là **bắt buộc** để đạt hiệu năng cao trên GPU GTX 1650 Max-Q (4GB VRAM).
> **Giải pháp tối ưu VRAM:** Gộp tất cả phát hiện (Người, Lửa, Khói, Đồ vật) vào **một mô hình YOLOv8n đa lớp (Multi-class PGIE)**. Sau đó dùng bộ theo dõi **NvDCF** và chạy mô hình phụ **ReID (SGIE)** chỉ cho lớp Người (`person`).

---

## Kiến trúc đường ống AI (DeepStream Pipeline)

```
[Nguồn vào: RTSP/File] ──▶ nvurisourcesrc
                               │ (Giải mã phần cứng NVDEC)
                               ▼
[Batching] ──────────────▶ nvstreammux (Ghép luồng)
                               ▼
[Phát hiện (PGIE)] ──────▶ nvinfer (YOLOv8n Đa lớp: Người, Lửa, Khói, Đồ vật)
                               ▼
[Theo dõi] ──────────────▶ nvtracker (NvDCF Tracker)
                               ▼
[Đặc trưng (SGIE)] ──────▶ nvinfer (ReID OSNet - Chỉ chạy trên nhãn 'person')
                               ▼
[Gấp Probe Callback] ────▶ PyDS Metadata Interceptor
                               │
                               ├──▶ Trích xuất: BBoxes, Tracking IDs, Embeddings
                               ├──▶ Trích xuất: Ảnh cắt đối tượng (Crops)
                               ▼
[Xuất dữ liệu] ──────────▶ Async Executor
                               ├──▶ Đẩy Metadata JSON → Kafka
                               └──▶ Lưu Ảnh cắt (.jpg) → MinIO
```

---

## Phạm vi (Scope)

**Bao gồm:**
- Cấu hình và khởi dựng đường ống DeepStream bằng GStreamer Python bindings (`pyds`).
- Chạy suy luận đa mô hình (YOLOv8n engine + ReID engine).
- Trích xuất metadata (Tọa độ khung bao, mã định danh theo dõi, vector đặc trưng 512 chiều).
- Trích xuất ảnh cắt (crop) đối tượng trực tiếp từ bộ nhớ GPU.
- Hỗ trợ nguồn vào: RTSP và File video (.mp4) để thử nghiệm.
- Đẩy sự kiện bất đồng bộ sang Kafka và MinIO.

**Không bao gồm:**
- Web UI hiển thị (Dashboard).
- Lưu trữ cơ sở dữ liệu PostgreSQL / Qdrant (analytics-service sẽ xử lý).

---

## Các giai đoạn triển khai (Phased Action Items)

### Phase 1: Chuẩn bị mô hình & Biên dịch TensorRT Engine
*Mục tiêu: Đưa các file `.pt` (YOLOv8n và ReID) về định dạng `.engine` tối ưu cho GTX 1650 (FP16).*

- [ ] **Step 1:** Viết script `models/scripts/export_yolov8.py` để xuất YOLOv8n đa lớp sang định dạng ONNX có hỗ trợ Dynamic Batching.
- [ ] **Step 2:** Sử dụng công cụ `trtexec` biên dịch file ONNX sang TensorRT Engine (`.engine`) với chế độ tối ưu hóa độ chính xác nửa (FP16) để tiết kiệm VRAM.
- [ ] **Step 3:** Viết script `models/scripts/export_reid.py` xuất mô hình ReID (OSNet-x0.25) sang ONNX và biên dịch thành TensorRT Engine FP16.
- [ ] **Step 4:** Kiểm tra kích thước và benchmark hiệu năng suy luận (FPS, VRAM) của 2 engine trên máy phát triển.

### Phase 2: Docker & Cài đặt môi trường DeepStream
*Mục tiêu: Thiết lập container chạy DeepStream hỗ trợ đầy đủ GPU CUDA.*

- [ ] **Step 5:** Cập nhật `apps/ai-service/Dockerfile` dựa trên ảnh nền chính thức `nvcr.io/nvidia/deepstream:7.0-triton-multiarch`.
- [ ] **Step 6:** Cài đặt các thư viện Python cần thiết và đặc biệt là bộ bindings **PyDS (Python DeepStream)**.
- [ ] **Step 7:** Cập nhật `docker-compose.yml` để mount GPU (NVIDIA runtime) và cấu hình phân phối tài nguyên cho container `ai-pipeline`.

### Phase 3: Viết Cấu hình Đường ống DeepStream (Configuration Files)
*Mục tiêu: Định nghĩa tham số hoạt động của bộ giải mã, bộ phát hiện và bộ theo dõi.*

- [ ] **Step 8:** Viết `apps/ai-service/configs/pgie_yolov8.txt` cấu hình cho nvinfer chính (YOLOv8n) — khai báo kích thước ảnh (640x640), ngưỡng nhận diện (0.25) và đường dẫn file engine.
- [ ] **Step 9:** Viết `apps/ai-service/configs/sgie_reid.txt` cấu hình cho nvinfer phụ (ReID) — cấu hình chạy phụ thuộc (`operate-on-class-ids=0` chỉ chạy trên ID của người).
- [ ] **Step 10:** Tinh chỉnh `apps/ai-service/configs/tracker_config.yml` cấu hình NvDCF tracker (độ dài vết theo dõi, ngưỡng biến mất).

### Phase 4: Xây dựng Đường ống bằng Python (GStreamer & PyDS)
*Mục tiêu: Viết mã Python thiết lập các element GStreamer và kết nối chúng.*

- [ ] **Step 11:** Viết `apps/ai-service/src/stream/stream_manager.py` quản lý luồng đầu vào, hỗ trợ tự động kết nối lại khi luồng RTSP bị ngắt.
- [ ] **Step 12:** Viết `apps/ai-service/src/pipelines/deepstream_pipeline.py` khởi tạo các element (`nvstreammux`, `nvinfer`, `nvtracker`, `nvvideoconvert`) và liên kết chúng thành một chuỗi.
- [ ] **Step 13:** Viết hàm **Pad Probe Callback** trên cổng ra của ReID để đánh chặn metadata: duyệt qua danh sách các đối tượng được phát hiện, đọc tọa độ BBox, Tracking ID và vector ReID.
- [ ] **Step 14:** Tích hợp bộ cắt ảnh trực tiếp từ GPU (dùng `nvbufsurface` thông qua PyDS API) để cắt ảnh đối tượng người/lửa/đồ vật mà không cần chuyển frame về CPU RAM.

### Phase 5: Xuất Sự kiện & Thử nghiệm Video
*Mục tiêu: Đẩy kết quả xử lý sang Kafka/MinIO và tạo cơ chế chạy thử nghiệm video.*

- [ ] **Step 15:** Viết `apps/ai-service/src/events/kafka_producer.py` đẩy dữ liệu JSON chứa metadata (camera_id, object_type, bbox, tracking_id, embedding_vector) lên Kafka topic `detection-events`.
- [ ] **Step 16:** Viết `apps/ai-service/src/storage/crop_saver.py` để đẩy các ảnh cắt đối tượng lên MinIO bucket `detection-crops`.
- [ ] **Step 17:** Viết kịch bản chạy thử nghiệm đầu vào là file video cục bộ, kết thúc pipeline khi file video chạy hết và lưu báo cáo kết quả ra định dạng JSON.

---

## Kế hoạch kiểm thử (Validation Plan)

### Kiểm thử cục bộ (Không có hệ thống bên ngoài)
1. **Kiểm tra biên dịch:** Chạy thử biên dịch engine YOLO và ReID:
   ```bash
   yolo export model=yolov8n.pt format=engine device=0 half=True
   ```
2. **Kiểm tra đường ống:** Chạy thử đường ống với 1 file video đầu vào và in log metadata ra màn hình terminal:
   ```bash
   python apps/ai-service/src/main.py --source data/test_video.mp4 --debug
   ```

### Kiểm thử tích hợp (Có Kafka & MinIO)
1. Khởi động Kafka và MinIO thông qua Docker Compose:
   ```bash
   docker compose up -d kafka minio
   ```
2. Khởi chạy luồng AI và giám sát thông điệp đến trên Kafka:
   ```bash
   kafka-console-consumer --bootstrap-server localhost:29092 --topic detection-events --from-beginning
   ```
