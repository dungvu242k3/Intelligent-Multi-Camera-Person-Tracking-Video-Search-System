# PLAN: Scheduler Service — Production Data Cleanup
## Giai đoạn: 5.6 Hoàn thiện Dịch vụ Lập lịch dọn dẹp dữ liệu cũ

Kế hoạch thực thi chi tiết tại: [implementation_plan.md](../implementation_plan.md)

---

## 📋 Mô tả mục tiêu
Hoàn thiện logic dọn dẹp (cleanup) dữ liệu rác, ảnh crop hết hạn và vector ReID hết hạn của `apps/scheduler-service`. 
Dịch vụ sẽ tự động quyét và xóa dữ liệu cũ hơn `RETENTION_DAYS` ngày trên cả 3 lớp:
1.  **PostgreSQL**: Xóa `tracking_events`, `fire_events`, `alerts` và `persons` quá hạn.
2.  **Qdrant**: Xóa vector ReID tương ứng trong collection `person_embeddings`.
3.  **MinIO**: Xóa ảnh crop liên kết trong `person-crops` bucket.

---

## ⏱️ Kế hoạch chi tiết

| Task | File | Mô tả công việc |
|---|---|---|
| 1. Config | [settings.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/scheduler-service/src/config/settings.py) | Thêm `DATABASE_URL` và MinIO/Qdrant keys. |
| 2. DB Startup | [main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/scheduler-service/src/main.py) | Thêm `wait_for_db()` để trì hoãn khởi chạy khi Postgres khởi động. |
| 3. Lib Helpers | [minio.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/packages/shared/storage/minio.py) <br>[qdrant.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/packages/shared/vector/qdrant.py) | Thêm hàm `delete_object` và `delete_embeddings`. |
| 4. Cleanup logic | [cleanup_job.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/scheduler-service/src/jobs/cleanup_job.py) | Viết job query Postgres, xóa Qdrant vectors, xóa MinIO crops và xóa bản ghi Postgres. |
| 5. Compose | [docker-compose.yml](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/docker-compose.yml) | Thêm container `mcpt-scheduler-service` vào stack phát triển. |

---

## 🔬 Kế hoạch xác thực (Verification Checklist)
- [ ] Chèn bản ghi cũ (> 30 ngày) vào database.
- [ ] Upload vector mẫu vào Qdrant và ảnh crop mẫu lên MinIO.
- [ ] Chạy `scheduler-service` với `CLEANUP_INTERVAL_HOURS=1` hoặc trigger thủ công.
- [ ] Verify các thực thể liên quan đã bị dọn dẹp sạch sẽ khỏi cả 3 DBs/Storage.
