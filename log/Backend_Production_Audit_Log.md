# BÁO CÁO ĐÁNH GIÁ SẴN SÀNG SẢN XUẤT — BACKEND (PRODUCTION-READINESS AUDIT LOG)
> **Dự án**: Intelligent Multi-Camera Person Tracking Video Search System (MCPT)  
> **Vai trò**: Principal Backend Architect  
> **Phạm vi**: Python FastAPI · PostgreSQL · Redis · Kafka · JWT  
> **Ngày thực hiện**: 16/07/2026  
> **Ngôn ngữ**: Tiếng Việt

---

## TỔNG QUAN (OVERVIEW)

Báo cáo này kết quả rà soát toàn bộ mã nguồn Backend gồm các dịch vụ:
- `apps/auth-service` — Xác thực, phát token JWT  
- `apps/gateway` — Reverse proxy, WebSocket, Rate Limiting  
- `apps/camera-service` — Quản lý camera RTSP  
- `apps/analytics-service` — Xử lý sự kiện tracking (Kafka consumer, Qdrant)  
- `apps/notification-service` — Chuyển tiếp cảnh báo qua Kafka → Gateway  
- `apps/search-service` — Tìm kiếm vector ReID

### Bảng thống kê lỗi theo mức độ nghiêm trọng

| Mức độ | Số lượng | Ảnh hưởng |
| :--- | :---: | :--- |
| 🔴 **CRITICAL** | **8** | Crash production, mất dữ liệu, leo thang quyền, DoS |
| 🟠 **HIGH** | **11** | Lỗi bảo mật, suy giảm hiệu suất nghiêm trọng |
| 🟡 **MEDIUM** | **6** | Rủi ro vận hành, anti-pattern, khả năng quan sát yếu |
| **TỔNG CỘNG** | **25** | |

---

## CHI TIẾT KẾT QUẢ ĐÁNH GIÁ

---

### CAT 1: XÁC THỰC (AUTHENTICATION)

#### AUTH-01 🔴 CRITICAL: Khóa JWT mặc định yếu được commit vào mã nguồn
- **Severity**: CRITICAL  
- **Root Cause**: Cả hai tệp settings đều khai báo `JWT_SECRET_KEY` với giá trị fallback lặp lại là `"change_this_to_a_secure_256_bit_key_in_production_environment_12345"`.  
- **Impact**: Nếu biến môi trường không được đặt khi deploy (ví dụ: thiếu file `.env` trong Docker), service sẽ hoạt động với khóa công khai, cho phép bất kỳ kẻ tấn công nào tự ký JWT hợp lệ để giả mạo quyền quản trị viên.  
- **Production Risk**: **Nguy cơ chiếm quyền toàn hệ thống** nếu deploy thiếu cấu hình.  
- **File**: [apps/auth-service/src/config/settings.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/auth-service/src/config/settings.py#L10-L13), [apps/gateway/src/config/settings.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/config/settings.py#L12-L15)  
- **Line**: L10-L13 (auth), L12-L15 (gateway)  
- **Evidence**:
```python
JWT_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "change_this_to_a_secure_256_bit_key_in_production_environment_12345"  # ← Hardcoded weak default
)
```

---

#### AUTH-02 🔴 CRITICAL: Không có giới hạn kích thước token JWT đầu vào
- **Severity**: CRITICAL  
- **Root Cause**: Hàm `verify_token()` trong Gateway nhận trực tiếp token từ `Authorization` header mà không kiểm tra độ dài chuỗi trước khi đưa vào `jwt.decode()`.  
- **Impact**: Một client độc hại có thể gửi JWT header có kích thước hàng megabyte, buộc `jwt.decode()` thực hiện xử lý chuỗi khổng lồ, gây tốn CPU và memory — tấn công **ReDoS / Resource Exhaustion**.  
- **Production Risk**: DoS có thể làm tê liệt Gateway.  
- **File**: [apps/gateway/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/main.py#L129-L165)  
- **Line**: L136-L142  
- **Evidence**:
```python
parts = authorization_header.split()   # ← No length check before
token = parts[1]
payload = jwt.decode(token, ...)       # ← No max-length guard on token
```

---

#### AUTH-03 🟠 HIGH: Refresh token được trả về trong Response JSON (Bên cạnh Cookie)
- **Severity**: HIGH  
- **Root Cause**: Endpoint `/login` đặt refresh token vào `HttpOnly` cookie (đúng), **nhưng đồng thời cũng trả về refresh token trong response body** (`TokenResponse` có trường `refresh_token`).  
- **Impact**: Frontend nhận refresh token trong JSON body và có thể lưu vào localStorage (đã xác nhận từ audit frontend). Điều này vô hiệu hóa hoàn toàn cơ chế `HttpOnly` cookie.  
- **Production Risk**: XSS → exfiltrate refresh token → chiếm phiên đăng nhập vĩnh viễn.  
- **File**: [apps/auth-service/src/api/auth_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/auth-service/src/api/auth_routes.py#L60-L108)  
- **Line**: L63, L108  
- **Evidence**:
```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str   # ← Exposed in JSON body — should ONLY be in HttpOnly cookie
    token_type: str = "bearer"

return TokenResponse(access_token=access_token, refresh_token=refresh_token)  # ← Leaks refresh token
```

---

### CAT 2: PHÂN QUYỀN (AUTHORIZATION) & RBAC

#### AUTHZ-01 🔴 CRITICAL: Không có kiểm tra quyền truy cập (Authorization) trong Camera Service và Analytics Service
- **Severity**: CRITICAL  
- **Root Cause**: Tất cả các route trong `camera_routes.py` và `tracking_routes.py` **không có middleware xác thực, không có Depends(), không có header `X-User-Id` check**.  
- **Impact**: Bất kỳ request nào đến trực tiếp các service nội bộ (bypass Gateway) đều được xử lý mà không cần đăng nhập. Nếu các service này bị expose (cấu hình Docker sai, K8s NodePort), bất kỳ ai cũng có thể thêm/xóa camera hoặc đọc toàn bộ dữ liệu tracking.  
- **Production Risk**: Truy cập dữ liệu trái phép trong môi trường lỗi cấu hình network.  
- **File**: [apps/camera-service/src/api/camera_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/api/camera_routes.py#L11-L40)  
- **Line**: L11-L40  
- **Evidence**:
```python
@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db_session)  # ← No auth dependency whatsoever
):
```

---

#### AUTHZ-02 🟠 HIGH: Gateway chỉ truyền `X-User-Role` dưới dạng số nguyên — không có enum, không có validation
- **Severity**: HIGH  
- **Root Cause**: `headers["X-User-Role"] = str(payload.get("role_id", ""))` ghi số (ví dụ `"1"`) vào header. Các downstream service đọc header này nhưng không có file định nghĩa enum vai trò chung. Kẻ tấn công có thể forge header này nếu call thẳng vào service.  
- **Impact**: Nếu network policy không đúng, một request giả mạo `X-User-Role: 1` có thể leo thang quyền.  
- **Production Risk**: Privilege escalation trong môi trường sai cấu hình.  
- **File**: [apps/gateway/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/main.py#L235)  
- **Line**: L235  

---

### CAT 4: KIỂM TRA ĐẦU VÀO (INPUT VALIDATION)

#### INPUT-01 🔴 CRITICAL: Không kiểm tra độ dài hay ký tự đặc biệt của `rtsp_url` trong `CameraCreate` DTO
- **Severity**: CRITICAL  
- **Root Cause**: DTO `CameraCreate` chấp nhận bất kỳ chuỗi nào cho `rtsp_url` mà không có regex validation, không kiểm tra scheme `rtsp://`, không giới hạn độ dài.  
- **Impact**: Kẻ tấn công gửi URL độc hại (ví dụ: file path, javascript protocol, hoặc chuỗi rất dài) có thể gây SSRF, path traversal khi health checker cố kết nối, hoặc buffer exhaustion.  
- **Production Risk**: SSRF/Path Traversal thông qua health checker socket probe.  
- **File**: [apps/camera-service/src/api/camera_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/api/camera_routes.py#L25-L31)  
- **Line**: L25-L31  
- **Evidence**: Không có field validator hay regex kiểm tra `rtsp_url` scheme trong `CameraCreate`.

---

#### INPUT-02 🟠 HIGH: `get_recent_events` cho phép `limit` lên đến 200 — không có cursor pagination
- **Severity**: HIGH  
- **Root Cause**: `limit: int = Query(default=50, ge=1, le=200)` — với 200 tracking events đầy đủ JSON bbox và crop_path mỗi event, response có thể đạt vài MB. Không có cursor/offset pagination.  
- **Impact**: High-frequency clients hoặc một client độc hại gửi `limit=200` liên tục gây tải rất lớn lên PostgreSQL và tăng response time toàn hệ thống.  
- **Production Risk**: Resource exhaustion tại DB layer khi scaling.  
- **File**: [apps/analytics-service/src/presentation/api/v1/tracking_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/analytics-service/src/presentation/api/v1/tracking_routes.py#L13)  
- **Line**: L13  

---

### CAT 6: QUẢN LÝ SECRETS

#### SECRET-01 🔴 CRITICAL: `INTERNAL_SERVICE_KEY` có giá trị mặc định yếu trong settings
- **Severity**: CRITICAL  
- **Root Cause**: `INTERNAL_SERVICE_KEY: str = os.getenv("INTERNAL_SERVICE_KEY", "change_this_internal_key_in_production")` — endpoint `/api/v1/alerts/publish` dùng key này để xác thực service-to-service.  
- **Impact**: Nếu biến môi trường không được đặt, bất kỳ client nào cũng có thể gọi endpoint publish alert với key mặc định, broadcast message giả đến tất cả WebSocket client (tấn công giả mạo cảnh báo cháy, gây hoảng loạn).  
- **Production Risk**: Fake security alerts injection.  
- **File**: [apps/gateway/src/config/settings.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/config/settings.py#L23-L26)  
- **Line**: L23-L26  

---

### CAT 7: XỬ LÝ LỖI (ERROR HANDLING)

#### ERR-01 🟠 HIGH: `authenticate_user` nuốt lỗi và trả về `None` thay vì re-raise lỗi Database
- **Severity**: HIGH  
- **Root Cause**: `except Exception as e: logger.error(...); return None` — khi DB bị timeout hay kết nối bị mất, hàm `authenticate_user` trả về `None`, khiến endpoint `/login` trả về `401 Invalid email or password` — **thay vì 503 Service Unavailable**.  
- **Impact**: Người dùng hợp lệ bị báo sai thông tin đăng nhập. Brute-force lockout counter tăng sai cho IP của người dùng thật do response là 401.  
- **Production Risk**: Sai trạng thái HTTP làm sai logic brute-force protection; người dùng hợp lệ bị khóa oan.  
- **File**: [apps/auth-service/src/services/auth_service.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/auth-service/src/services/auth_service.py#L76-L78)  
- **Line**: L76-L78  
- **Evidence**:
```python
except Exception as e:
    logger.error(f"Database query error...: {e}", exc_info=True)
    return None  # ← Should raise 503, not return None (causes 401 response)
```

---

#### ERR-02 🟠 HIGH: `process_message_callback` trong analytics nuốt lỗi execution mà không có DLQ
- **Severity**: HIGH  
- **Root Cause**: `except Exception as e: logger.error(...); await session.rollback()` — khi xử lý event Kafka thất bại, message bị bỏ qua hoàn toàn (Kafka đã auto-commit offset trước đó).  
- **Impact**: Các event tracking bị mất vĩnh viễn khi gặp lỗi (bad data, Qdrant timeout, DB constraint violation). Không có Dead Letter Queue (DLQ) hay retry mechanism.  
- **Production Risk**: Mất dữ liệu tracking trong môi trường production khi có lỗi tạm thời.  
- **File**: [apps/analytics-service/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/analytics-service/src/main.py#L63-L65)  
- **Line**: L63-L65  

---

### CAT 8: LOGGING

#### LOG-01 🟠 HIGH: Log chứa địa chỉ email người dùng dưới dạng plaintext
- **Severity**: HIGH  
- **Root Cause**: `logger.info(f"New user registered: {new_user.email}...")` và `logger.info(f"User '{email}' authenticated successfully.")` ghi email ra log.  
- **Impact**: Email là PII (Personally Identifiable Information). Ghi PII vào log vi phạm GDPR/PDPA, đặc biệt nếu log được đẩy đến hệ thống log tập trung (ELK/Loki) mà không có mask.  
- **Production Risk**: Vi phạm quy định bảo vệ dữ liệu cá nhân; rò rỉ PII qua log pipeline.  
- **File**: [apps/auth-service/src/api/auth_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/auth-service/src/api/auth_routes.py#L179), [apps/auth-service/src/services/auth_service.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/auth-service/src/services/auth_service.py#L66-L74)  
- **Line**: auth_routes.py L179, auth_service.py L66, L71, L74  
- **Evidence**:
```python
logger.info(f"New user registered: {new_user.email} (ID: {new_user.id})")  # ← PII in log
logger.info(f"User '{email}' authenticated successfully.")                   # ← PII in log
```

---

### CAT 9: GIỚI HẠN TỐC ĐỘ (RATE LIMITING)

#### RATE-01 🟠 HIGH: Rate Limiter In-Memory không thread-safe — race condition khi có multiple workers
- **Severity**: HIGH  
- **Root Cause**: `self.in_memory_db: Dict[str, List[float]] = {}` được đọc và ghi đồng thời từ nhiều asyncio coroutines mà không có lock (`asyncio.Lock`). Dù asyncio là single-threaded, bất kỳ `await` nào cũng có thể nhường quyền cho coroutine khác ghi vào cùng key.  
- **Impact**: Sliding window count có thể bị đọc sai trước khi được cập nhật bởi coroutine khác, cho phép một số request lách qua giới hạn.  
- **Production Risk**: Rate limit bypass khi tải cao với nhiều concurrent requests.  
- **File**: [apps/gateway/src/middleware/rate_limiter.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/middleware/rate_limiter.py#L86-L101)  
- **Line**: L90-L101  
- **Evidence**:
```python
timestamps = self.in_memory_db.get(client_ip, [])     # ← Read
valid_timestamps = [t for t in timestamps if ...]      # ← Process  
# ← Another coroutine can run here at any await
valid_timestamps.append(now)
self.in_memory_db[client_ip] = valid_timestamps        # ← Write (can overwrite another coroutine's append)
```

---

#### RATE-02 🟡 MEDIUM: Rate Limit dùng IP là dễ bị bypass bằng X-Forwarded-For giả mạo
- **Severity**: MEDIUM  
- **Root Cause**: `client_ip = request.client.host` — lấy IP từ TCP connection trực tiếp. Nếu sau này deploy phía sau Load Balancer hay Nginx proxy, `request.client.host` sẽ là IP của LB, không phải client thật. Phải dùng `X-Forwarded-For` nhưng header này dễ bị fake.  
- **Production Risk**: Rate limiting vô hiệu khi deploy sau LB/proxy mà không cấu hình trusted proxies.  
- **File**: [apps/gateway/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/main.py#L178)  
- **Line**: L178  

---

### CAT 10: CACHING

#### CACHE-01 🟡 MEDIUM: Không có cache cho `list_all_cameras()` trong Health Checker
- **Severity**: MEDIUM  
- **Root Cause**: `cameras = await service.list_all_cameras()` được gọi **mỗi chu kỳ health check** (mặc định mỗi 30 giây hoặc ít hơn), gây một query `SELECT * FROM cameras` mỗi lần.  
- **Impact**: Khi số lượng camera lớn hoặc interval ngắn, lượng query tích lũy có thể ảnh hưởng đến connection pool.  
- **Production Risk**: DB connection pool exhaustion khi số lượng camera tăng.  
- **File**: [apps/camera-service/src/services/health_checker.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/services/health_checker.py#L76)  
- **Line**: L76  

---

### CAT 11: TRUY CẬP DATABASE (DATABASE ACCESS)

#### DB-01 🟡 MEDIUM: `list_all_cameras()` không có phân trang — full table scan trong production
- **Severity**: MEDIUM  
- **Root Cause**: `select(Camera)` không có `LIMIT`, `OFFSET`, hay bất kỳ filter nào.  
- **Impact**: Với hàng trăm camera, query trả về toàn bộ records và load vào memory Python. Endpoint `GET /cameras` cũng gọi hàm này, có thể trả về response rất lớn.  
- **Production Risk**: Tăng độ trễ và tải DB khi hệ thống scale.  
- **File**: [apps/camera-service/src/services/camera_service.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/services/camera_service.py#L36-L39)  
- **Line**: L36-L39  

---

### CAT 12: AN TOÀN GIAO DỊCH (TRANSACTION SAFETY)

#### TX-01 🔴 CRITICAL: `CameraService` gọi `await self.db.commit()` trực tiếp — phá vỡ Unit of Work
- **Severity**: CRITICAL  
- **Root Cause**: `CameraService.create_camera()`, `update_camera()`, `update_status()`, `delete_camera()` đều tự gọi `self.db.commit()`. Nếu sau này một use case cần thực hiện nhiều thao tác (ví dụ: tạo camera + ghi audit log) trong một transaction, mỗi bước sẽ commit riêng, phá vỡ tính atomicity.  
- **Impact**: Không thể wrap nhiều thao tác trong một transaction duy nhất. Partial update xảy ra khi một bước thất bại sau commit của bước trước.  
- **Production Risk**: Data inconsistency khi business logic phức tạp hơn.  
- **File**: [apps/camera-service/src/services/camera_service.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/services/camera_service.py#L22-L24)  
- **Line**: L22, L54, L63, L72  
- **Evidence**:
```python
async def create_camera(self, ...):
    self.db.add(camera)
    await self.db.commit()   # ← Commits immediately, no Unit of Work pattern
    await self.db.refresh(camera)
```

---

#### TX-02 🟠 HIGH: Analytics: `vector_store.upsert_embedding()` gọi sau DB nhưng không trong cùng transaction
- **Severity**: HIGH  
- **Root Cause**: Trong `_handle_person_detection`, Qdrant write xảy ra sau DB write nhưng không có cơ chế rollback đồng bộ:  
  1. `await self.person_repo.upsert_person(person)` → ghi SQL
  2. `await self.vector_store.upsert_embedding(...)` → ghi Qdrant  
  Nếu Qdrant write thất bại, person đã được tạo trong PostgreSQL nhưng không có embedding trong Qdrant → ReID sẽ không bao giờ match được với person mới này.  
- **Production Risk**: Inconsistency vĩnh viễn giữa SQL và vector store.  
- **File**: [apps/analytics-service/src/application/use_cases/process_tracking_event.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/analytics-service/src/application/use_cases/process_tracking_event.py#L111-L121)  
- **Line**: L111-L121  

---

### CAT 14: HIỆU NĂNG (PERFORMANCE)

#### PERF-01 🟠 HIGH: Health checker tạo concurrent tasks không giới hạn với `asyncio.gather()`
- **Severity**: HIGH  
- **Root Cause**: `tasks = [self._check_camera(camera, service) for camera in cameras]` + `await asyncio.gather(*tasks)` — với N cameras, tạo N concurrent TCP socket connections **đồng thời**.  
- **Impact**: 100 cameras = 100 concurrent socket connections mỗi chu kỳ. Với timeout 2 giây và interval ngắn, có thể gây socket exhaustion, file descriptor exhaustion trên OS.  
- **Production Risk**: OS socket exhaustion khi deploy với nhiều camera.  
- **File**: [apps/camera-service/src/services/health_checker.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/camera-service/src/services/health_checker.py#L79-L80)  
- **Line**: L79-L80  
- **Evidence**:
```python
tasks = [self._check_camera(camera, service) for camera in cameras]
await asyncio.gather(*tasks)  # ← Unbounded concurrency — no semaphore limit
```

---

#### PERF-02 🟡 MEDIUM: `get_qdrant_store()` tạo instance QdrantVectorStore mới trên mỗi request
- **Severity**: MEDIUM  
- **Root Cause**: `def get_qdrant_store() -> QdrantVectorStore: return QdrantVectorStore()` — FastAPI dependency được gọi cho mỗi request, tạo kết nối Qdrant mới mỗi lần.  
- **Impact**: Overhead kết nối TCP/gRPC đến Qdrant trên mỗi request tìm kiếm.  
- **Production Risk**: Tăng latency và waste connection resources dưới tải cao.  
- **File**: [apps/search-service/src/api/search_routes.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/search-service/src/api/search_routes.py#L9-L10)  
- **Line**: L9-L10  

---

### CAT 15: ĐỒNG THỜI (CONCURRENCY)

#### CONC-01 🔴 CRITICAL: `enable.auto.commit: True` trong Kafka Consumer — risk of message loss
- **Severity**: CRITICAL  
- **Root Cause**: Cả `KafkaEventConsumer` và `consume_alerts` trong notification service đều dùng `'enable.auto.commit': True`. Kafka tự commit offset sau thời gian định kỳ, bất kể message đã được xử lý thành công hay chưa.  
- **Impact**: Nếu service crash hoặc process_callback thất bại **sau khi offset đã được auto-committed**, message sẽ không được xử lý lại sau khi restart. Các tracking event và fire alerts quan trọng sẽ bị mất.  
- **Production Risk**: **Mất dữ liệu tracking và cảnh báo cháy** — không thể phục hồi.  
- **File**: [apps/analytics-service/src/infrastructure/messaging/kafka_consumer.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/analytics-service/src/infrastructure/messaging/kafka_consumer.py#L19), [apps/notification-service/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/notification-service/src/main.py#L37)  
- **Line**: kafka_consumer.py L19, notification main.py L37  
- **Evidence**:
```python
'enable.auto.commit': True  # ← Must be False; commit manually after successful processing
```

---

### CAT 16: BACKGROUND JOBS

#### BG-01 🟡 MEDIUM: `Optional[asyncio.Task]` — biến global `alert_task` được sử dụng mà không được import
- **Severity**: MEDIUM  
- **Root Cause**: `alert_task: Optional[asyncio.Task] = None` ở dòng 25 của `notification-service/src/main.py` dùng type hint `Optional` mà không import `Optional` từ `typing`.  
- **Impact**: Crash ngay khi Python parse module — `NameError: name 'Optional' is not defined` — service không thể start.  
- **Production Risk**: **Service không thể khởi động** — deployment hoàn toàn thất bại.  
- **File**: [apps/notification-service/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/notification-service/src/main.py#L25)  
- **Line**: L25  
- **Evidence**:
```python
# Line 1-14: imports asyncio, json, logging, os, sys... httpx, confluent_kafka
# ← 'Optional' from 'typing' is NOT imported

alert_task: Optional[asyncio.Task] = None  # ← NameError at startup!
```

---

### CAT 18: MONITORING

#### MON-01 🟡 MEDIUM: Endpoint `/metrics` là placeholder rỗng — không có Prometheus metrics thực
- **Severity**: MEDIUM  
- **Root Cause**: Tất cả services trả về `{"message": "Metrics placeholder..."}` từ `/metrics` endpoint.  
- **Impact**: Không có request throughput, error rate, DB connection pool, hay Kafka lag metrics nào được collect bởi Prometheus. Không thể phát hiện degradation trước khi incident.  
- **Production Risk**: Không có observability → incident detection chậm.  
- **File**: auth-service, camera-service, analytics-service `/metrics` endpoints  

---

### CAT 19: HEALTH CHECKS

#### HEALTH-01 🟡 MEDIUM: Health check của gateway không kiểm tra Redis availability
- **Severity**: MEDIUM  
- **Root Cause**: `/health` tại Gateway chỉ trả về static `{"status": "healthy"}` mà không kiểm tra Redis (rate limiter), connections, hay upstream services.  
- **Impact**: K8s readiness probe báo Gateway `healthy` ngay cả khi Redis down (rate limiting disabled) hay downstream services unreachable.  
- **Production Risk**: Load balancer tiếp tục route traffic đến Gateway đang ở trạng thái degraded.  
- **File**: [apps/gateway/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/gateway/src/main.py#L368-L370)  
- **Line**: L368-L370  

---

### CAT 20: SẴN SÀNG SẢN XUẤT (PRODUCTION READINESS)

#### PROD-01 🟠 HIGH: Notification Service không có CORS, không có auth — docs enabled by default
- **Severity**: HIGH  
- **Root Cause**: `app = FastAPI(...)` tại notification service **không có** `docs_url=None if _is_prod else "/docs"` check.  
- **Impact**: Swagger UI luôn luôn enabled kể cả trong production, expose internal API schema.  
- **Production Risk**: Schema leakage của internal alert forwarding API.  
- **File**: [apps/notification-service/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/notification-service/src/main.py#L116-L121)  
- **Line**: L116-L121  
- **Evidence**:
```python
app = FastAPI(
    title="...",
    lifespan=lifespan
    # ← No docs_url=None protection in production
)
```

---

#### PROD-02 🟠 HIGH: Không có Graceful Shutdown timeout — Kafka consumer có thể không close đúng cách
- **Severity**: HIGH  
- **Root Cause**: Khi signal SIGTERM gửi đến (K8s pod termination), lifespan context cancels `consumer_task` ngay lập tức. Consumer đang giữa xử lý message có thể không commit offset hoặc không gọi `consumer.close()`.  
- **Impact**: Incomplete message processing, unclean consumer group state, potential rebalance issues.  
- **Production Risk**: Rebalance storm khi rolling deploy với nhiều instances.  
- **File**: [apps/analytics-service/src/main.py](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/analytics-service/src/main.py#L86-L105)  
- **Line**: L92-L97  

---

## 🔥 BẢNG TÓM TẮT CÁC VẤN ĐỀ THEO MỨC ĐỘ

| ID | Mức độ | Danh mục | Tóm tắt | File chính |
| :--- | :---: | :--- | :--- | :--- |
| AUTH-01 | 🔴 CRITICAL | Authentication | Khóa JWT mặc định yếu trong cấu hình | settings.py |
| AUTH-02 | 🔴 CRITICAL | Authentication | Không giới hạn kích thước JWT token đầu vào | gateway/main.py |
| AUTHZ-01 | 🔴 CRITICAL | Authorization | Không có auth tại camera/analytics services | camera_routes.py |
| INPUT-01 | 🔴 CRITICAL | Input Validation | Không validate `rtsp_url` scheme/length | camera_routes.py |
| SECRET-01 | 🔴 CRITICAL | Secrets | `INTERNAL_SERVICE_KEY` mặc định yếu | gateway/settings.py |
| TX-01 | 🔴 CRITICAL | Transaction | CameraService commit riêng — phá Unit of Work | camera_service.py |
| CONC-01 | 🔴 CRITICAL | Concurrency | Kafka `auto.commit=True` gây mất message | kafka_consumer.py |
| BG-01 | 🔴 CRITICAL | Background Jobs | `Optional` chưa import → service không start | notification/main.py |
| AUTH-03 | 🟠 HIGH | Authentication | Refresh token rò rỉ trong JSON body | auth_routes.py |
| AUTHZ-02 | 🟠 HIGH | Authorization | `X-User-Role` là số nguyên không có enum | gateway/main.py |
| INPUT-02 | 🟠 HIGH | Input Validation | Limit=200 không có pagination | tracking_routes.py |
| ERR-01 | 🟠 HIGH | Error Handling | DB timeout trả 401 thay vì 503 | auth_service.py |
| ERR-02 | 🟠 HIGH | Error Handling | Kafka message fail không có DLQ/retry | analytics/main.py |
| LOG-01 | 🟠 HIGH | Logging | Email plaintext trong production logs | auth_routes.py |
| RATE-01 | 🟠 HIGH | Rate Limiting | In-memory rate limiter không thread-safe | rate_limiter.py |
| TX-02 | 🟠 HIGH | Transaction | Qdrant write không sync với SQL transaction | process_tracking.py |
| PERF-01 | 🟠 HIGH | Performance | asyncio.gather() không bounded cho sockets | health_checker.py |
| PROD-01 | 🟠 HIGH | Production | Swagger luôn bật tại notification service | notification/main.py |
| PROD-02 | 🟠 HIGH | Production | Không có graceful shutdown timeout | analytics/main.py |
| RATE-02 | 🟡 MEDIUM | Rate Limiting | Rate limit IP-based bypass qua LB | gateway/main.py |
| CACHE-01 | 🟡 MEDIUM | Caching | Không cache `list_all_cameras()` | health_checker.py |
| DB-01 | 🟡 MEDIUM | DB Access | Full table scan không paginate | camera_service.py |
| PERF-02 | 🟡 MEDIUM | Performance | Qdrant instance tạo mới mỗi request | search_routes.py |
| MON-01 | 🟡 MEDIUM | Monitoring | `/metrics` placeholder — không có real metrics | All services |
| HEALTH-01 | 🟡 MEDIUM | Health Checks | Gateway health không check Redis/upstreams | gateway/main.py |

---

## 🚀 ĐỀ XUẤT 5 FIX ƯU TIÊN HÀNG ĐẦU

1. **[BG-01] Fix ngay `NameError`** trong notification service: thêm `from typing import Optional` dòng 1 → fix crash deployment.
2. **[CONC-01] Tắt Kafka auto-commit** (`enable.auto.commit: False`) và commit thủ công sau `process_callback` thành công → ngăn mất dữ liệu.
3. **[AUTH-01 + SECRET-01] Bắt buộc secrets từ environment**: thêm validation khi khởi động — nếu biến môi trường không được set, từ chối start service thay vì dùng giá trị mặc định yếu.
4. **[AUTH-03] Xóa `refresh_token` khỏi JSON response** của `/login` — chỉ set qua HttpOnly cookie.
5. **[PERF-01] Giới hạn concurrency health checker** bằng `asyncio.Semaphore(20)` để tránh socket exhaustion khi scale.
