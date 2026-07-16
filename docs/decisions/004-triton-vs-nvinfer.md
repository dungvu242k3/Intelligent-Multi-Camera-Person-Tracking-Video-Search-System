# Quyết định kiến trúc: Lựa chọn giữa Triton Inference Server vs Native TensorRT (nvinfer)

## Ngữ cảnh (Context)
Hệ thống cần chạy 3 nhiệm vụ phân tích: phát hiện người, phát hiện lửa/khói, và trích xuất vector đặc trưng (ReID). Phần cứng mục tiêu là GPU GTX 1650 Max-Q (4GB VRAM). Chúng ta cần chọn phương án tối ưu để triển khai mô hình (Model Serving).

Có hai lựa chọn chính trong hệ sinh thái NVIDIA DeepStream:
1. **nvinfer (Native TensorRT):** Nhúng trực tiếp thư viện TensorRT runtime vào trong tiến trình GStreamer.
2. **nvinferserver (Triton Inference Server):** Gửi frame sang Triton Server (chạy trong tiến trình khác hoặc cùng tiến trình qua C-API) để suy luận.

---

## Phân tích Triton Inference Server (Ưu & Nhược điểm)

### 1. Cơ chế tối ưu của Triton
* **Dynamic Batching (Gom lô động):** Khi có nhiều camera gửi frame về ở các mili-giây khác nhau, Triton sẽ giữ chúng lại trong một cửa sổ nhỏ (ví dụ 5ms) để gom thành 1 batch lớn và đẩy vào GPU. Điều này giúp tận dụng tối đa số lượng nhân CUDA của GPU.
* **Concurrent Model Execution (Chạy mô hình song song):** Triton cho phép nạp nhiều bản sao (instances) của cùng một mô hình hoặc nhiều mô hình khác nhau lên GPU và tự động lập lịch chạy song song để giảm thời gian chờ.
* **Model Control API (Nạp mô hình theo yêu cầu):** Triton cung cấp HTTP/gRPC API để:
  * Nạp (load) hoặc giải phóng (unload) mô hình khỏi VRAM mà không cần khởi động lại luồng video.
  * *Ví dụ:* Bình thường chỉ nạp mô hình Người (nhẹ). Khi phát hiện có chuyển động lạ hoặc theo chu kỳ 10 giây/lần, mới gọi API nạp mô hình Lửa/Đồ vật để quét, sau đó giải phóng VRAM.
* **Tách biệt hạ tầng (Decoupling):** Tách biệt tầng giải mã video (DeepStream) và tầng suy luận AI (Triton). Nếu mô hình AI bị sập, luồng video vẫn chạy bình thường.

### 2. Nhược điểm đối với GPU 4GB VRAM
* **Overhead bộ nhớ:** Bản thân tiến trình Triton Server khi chạy riêng biệt (out-of-process) tiêu tốn khoảng 400MB - 600MB VRAM tĩnh chỉ để khởi động.
* **Độ trễ truyền dữ liệu:** Việc chuyển dữ liệu ảnh từ tiến trình DeepStream sang Triton qua IPC (gRPC/Shared Memory) gây ra độ trễ nhỏ (tuy nhiên có thể tối ưu bằng Shared Memory).

---

## So sánh lựa chọn

| Tiêu chí | nvinfer (Native TensorRT) | nvinferserver (Triton Server) |
| :--- | :--- | :--- |
| **Tiêu thụ VRAM** | **Cực thấp (Tối ưu nhất cho 4GB VRAM)** | Trung bình (Tốn bộ nhớ nền cho server) |
| **Độ trễ (Latency)** | **Thấp nhất** (Chạy trực tiếp trong luồng dữ liệu GPU) | Thấp (Có thêm độ trễ truyền thông điệp) |
| **Gom lô (Batching)** | Tĩnh (Cấu hình cứng batch-size) | **Động (Dynamic Batching tự động)** |
| **Nạp/Giải phóng mô hình** | Phải khởi động lại cả pipeline | **Linh hoạt qua API (Load/Unload on-demand)** |
| **Hỗ trợ Framework** | Chỉ TensorRT (`.engine`) | Đa dạng (ONNX, PyTorch, TensorRT, TF) |

---

## Quyết định đề xuất (Proposed Decision)

Để phù hợp với **GTX 1650 Max-Q (4GB VRAM)**, chúng tôi đề xuất:

1. **Giai đoạn thử nghiệm / Dev cục bộ:** Dùng **nvinfer (Native TensorRT)**.
   * *Lý do:* Tiết kiệm từng MB VRAM để có thể chạy đồng thời YOLOv8n + ReID trên 1 GPU duy nhất mà không bị lỗi OOM (Out Of Memory).
2. **Giai đoạn Production (khi lên GPU lớn hơn, ví dụ RTX 3060/4060):** Chuyển sang **Triton Inference Server**.
   * *Lý do:* Lúc này VRAM dồi dào, cần dùng Triton để phục vụ nhiều camera gửi yêu cầu về cùng lúc (Dynamic Batching) và quản lý nạp/giải phóng mô hình tự động.

### Cách hiện thực "Gọi mô hình khi cần" (On-demand) không cần Triton (cho GPU 4GB)
Nếu không dùng Triton, chúng ta vẫn có thể tối ưu luồng "khi nào cần mới chạy" bằng cách cấu hình **GStreamer Pipeline**:
* **Chạy tuần tự (Cascaded Inference):** Mô hình chính (PGIE - YOLO Người) chạy liên tục ở 100% số khung hình.
* Mô hình phụ (SGIE - Đồ vật hoặc ReID) chỉ được kích hoạt suy luận khi PGIE phát hiện ra đối tượng mục tiêu. Nếu PGIE không thấy ai, SGIE sẽ ở trạng thái nghỉ, không tiêu tốn chu kỳ tính toán của GPU.
* Cấu hình bằng cách đặt tham số `input-tensor-meta=1` và liên kết ID lớp cha trong file cấu hình mô hình phụ.
