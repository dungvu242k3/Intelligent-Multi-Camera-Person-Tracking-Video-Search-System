# BÁO CÁO ĐÁNH GIÁ TOÀN DIỆN FRONTEND (FRONTEND AUDIT LOG)
> **Dự án**: Intelligent Multi-Camera Person Tracking Video Search System (MCPT)  
> **Vai trò**: Principal Frontend Auditor  
> **Ngôn ngữ**: Tiếng Việt (Vietnamese)  
> **Ngày thực hiện**: 16/07/2026

---

## TỔNG QUAN HỆ THỐNG ĐÁNH GIÁ (OVERVIEW)

Báo cáo này ghi nhận kết quả rà soát toàn bộ mã nguồn Frontend thuộc thư mục `apps/web/src`. Quá trình đánh giá được thực hiện qua **8 pha** tiêu chuẩn: Kiến trúc, React Hooks, TypeScript, Hiệu năng, Bảo mật, Tầng API, UI/UX và Kiểm thử (Testing).

### Bảng thống kê lỗi theo mức độ nghiêm trọng

| Mức độ | Số lượng | Mô tả hành vi ảnh hưởng |
| :--- | :---: | :--- |
| 🔴 **CRITICAL (Nghiêm trọng)** | **11** | Gây rò rỉ bộ nhớ, lỗi logic bảo mật nghiêm trọng (XSS), bypass xác thực hoặc crash ứng dụng. |
| 🟠 **HIGH (Cao)** | **14** | Lỗi hiệu năng, thiếu cơ chế xử lý ngoại lệ (Error handling) hoặc cấu hình cứng (Hardcoded) làm mất tính di động. |
| 🟡 **MEDIUM (Trung bình)** | **10** | Trùng lặp code giao diện/kiểu dữ liệu, trải nghiệm người dùng (UX) chưa mượt mà hoặc thiếu responsive. |
| **TỔNG CỘNG** | **35** | |

---

## CHI TIẾT KẾT QUẢ ĐÁNH GIÁ (8 PHASES)

### PHA 1: KIẾN TRÚC (ARCHITECTURE)

#### 1.1. 🔴 CRITICAL: Khởi tạo WebSocket trùng lặp gây rò rỉ bộ nhớ & xung đột trạng thái
* **Tệp ảnh hưởng**:  
  * [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L11-L30) (Dòng 11-30)
  * [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L36-L76) (Dòng 36-76)
* **Chi tiết**: `Header` được render ở mọi route được bảo vệ và tự mở một kết nối WebSocket mới (`new WebSocket(...)`). Khi người dùng truy cập trang `FireDetectionPage`, ứng dụng tiếp tục mở một kết nối WebSocket thứ hai đến cùng một URL.
* **Hậu quả**: Tạo ra nhiều kết nối thừa thãi lên Backend, dễ gây nghẽn Gateway WebSocket pool và gây race-condition khi cập nhật state.

#### 1.2. 🔴 CRITICAL: File khung xương rỗng (Ghost Stub Files)
* **Tệp ảnh hưởng**: 13 tệp trống (0 bytes) nhưng vẫn được import hoặc đăng ký cấu trúc:
  * `shared/stores/alertStore.ts`
  * `shared/stores/cameraStore.ts`
  * `shared/stores/trackingStore.ts`
  * `shared/hooks/useAuth.ts`
  * `shared/hooks/useWebSocket.ts`
  * `shared/utils/api-client.ts`
  * `features/live-monitor/components/CameraGrid.tsx`
  * `features/live-monitor/components/CameraPlayer.tsx`
  * `features/live-monitor/components/TrackingOverlay.tsx`
  * `features/camera-management/components/CameraForm.tsx`
  * `features/camera-management/components/CameraTable.tsx`
  * `features/dashboard/components/ActivityChart.tsx`
  * `features/dashboard/components/StatsCard.tsx`
* **Chi tiết**: Các tính năng Live Monitor, Dashboard và Camera Management hiện tại hoàn toàn là "vỏ rỗng", không có logic hoạt động thực tế.

#### 1.3. 🔴 CRITICAL: Thư viện `@tanstack/react-query` được cài đặt nhưng không sử dụng
* **Tệp ảnh hưởng**: [package.json](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/package.json), [providers.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/app/providers.tsx)
* **Chi tiết**: Đã bọc `QueryClientProvider` ở root nhưng toàn bộ ứng dụng vẫn dùng `useState` + `useEffect` kết hợp với `axios` thủ công, bỏ phí toàn bộ tính năng cache, tự động revalidate, retry và quản lý trạng thái query của React Query.

#### 1.4. 🟠 HIGH: Component quá lớn (God Component) — `VideoTestPage.tsx`
* **Tệp ảnh hưởng**: [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx) (390 dòng)
* **Chi tiết**: Ôm đồm quá nhiều vai trò: quản lý máy trạng thái simulation (`idle/processing/success`), quản lý bộ đếm thời gian `setInterval`, thực hiện cuộc gọi HTTP, render layout UI, xử lý lỗi và xuất báo cáo. Nên tách các phần logic simulation thành hook riêng.

#### 1.5. 🟠 HIGH: Hardcode URL API và WebSocket ở nhiều tệp tin
* **Tệp ảnh hưởng**:
  * [axiosInstance.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/utils/axiosInstance.ts#L5) (Dòng 5)
  * [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L159) (Dòng 159)
  * [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L37) (Dòng 37)
  * [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L13) (Dòng 13)
* **Chi tiết**: Địa chỉ `http://localhost:8000` và `ws://localhost:8000/ws` bị viết cứng trong mã nguồn thay vì lấy từ biến môi trường `import.meta.env.VITE_API_URL`. Sẽ crash ngay lập tức khi deploy lên môi trường Production/Docker.

#### 1.6. 🟠 HIGH: Trùng lặp mã nguồn tiện ích Logger
* **Tệp ảnh hưởng**:
  * [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L317-L320) (Dòng 317-320)
  * [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L188-L191) (Dòng 188-191)
* **Chi tiết**: Đối tượng `logger` giống hệt nhau được khai báo trùng lặp ở cả hai trang. Cần chuyển vào thư mục `shared/utils/logger.ts`.

#### 1.7. 🟡 MEDIUM: Trùng lặp khai báo Interface trong cùng feature
* **Tệp ảnh hưởng**:
  * `CropDetail` và `TimelineEntry` trùng ở [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L13-L26) & [TestResults.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/components/TestResults.tsx#L15-L28).
  * `FireEvent` trùng ở [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L14-L20) & [FireHistorySidebar.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/components/FireHistorySidebar.tsx#L5-L12).
  * `CameraNode` trùng ở [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L7-L12) & [CameraMap.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/components/CameraMap.tsx#L4-L9).

#### 1.8. 🟡 MEDIUM: Trùng lặp hàm `toggleLanguage` chuyển đổi ngôn ngữ
* **Tệp ảnh hưởng**: [LoginPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/LoginPage.tsx#L20), [RegisterPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/RegisterPage.tsx#L23), [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L32).
* **Chi tiết**: Logic chuyển đổi ngôn ngữ viết lặp đi lặp lại 3 lần.

#### 1.9. 🟡 MEDIUM: Cấu hình danh sách Camera bị viết cứng (Hardcoded)
* **Tệp ảnh hưởng**: [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L25-L30) (Dòng 25-30)
* **Chi tiết**: Mảng dữ liệu tọa độ định vị camera hiển thị trên sơ đồ vẽ cứng ngay trong component. Khi backend thêm/sửa camera, sơ đồ sẽ không tự cập nhật.

---

### PHA 2: REACT HOOKS

#### 2.1. 🔴 CRITICAL: Hàm Cleanup của `useEffect` không dọn dẹp setInterval khi unmount
* **Tệp ảnh hưởng**: [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L216-L222) (Dòng 216-222)
* **Chi tiết**: `useEffect` chỉ lắng nghe biến `simInterval`. Tuy nhiên, vì `simInterval` là state chứ không phải ref, việc gọi `setSimInterval(interval)` sẽ kích hoạt render lại và chạy liên tục các vòng lặp dọn dẹp không đúng thời điểm. Khi unmount trang, timer vẫn tiếp tục chạy ngầm, gây rò rỉ bộ nhớ nghiêm trọng và lỗi "cannot update state on unmounted component".

#### 2.2. 🔴 CRITICAL: Nguy cơ lặp vô hạn do dependency array của `initAuth`
* **Tệp ảnh hưởng**: [router.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/app/router.tsx#L19-L21) (Dòng 19-21)
* **Chi tiết**: Truyền hàm `initAuth` từ Zustand store vào danh sách dependencies của `useEffect`. Hiện tại Zustand giữ tham chiếu tĩnh nên chưa lỗi, nhưng nếu sau này `initAuth` phụ thuộc vào state động, router sẽ bị vòng lặp vô hạn.

#### 2.3. 🟠 HIGH: WebSocket ở Header.tsx thiếu cơ chế tự động kết nối lại (Reconnection)
* **Tệp ảnh hưởng**: [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L11-L30)
* **Chi tiết**: Khi kết nối bị gián đoạn (mạng yếu, backend reload), biến `wsConnected` sẽ chuyển sang `false` vĩnh viễn cho đến khi người dùng F5 tải lại trang.

#### 2.4. 🟠 HIGH: Đóng gói bao đóng stale (Stale Closure) đối với mảng `cameras` trong WebSocket
* **Tệp ảnh hưởng**: [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L41-L63)
* **Chi tiết**: Sự kiện `socket.onmessage` được đăng ký một lần khi component mount. Nó lưu trữ tham chiếu đến mảng `cameras` cũ tại thời điểm đó. Nếu danh sách camera thay đổi sau này, hàm callback WebSocket vẫn đọc dữ liệu cũ.

#### 2.5. 🟠 HIGH: `handleResolveEvent` đọc dữ liệu state cũ (Stale State)
* **Tệp ảnh hưởng**: [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L97-L111)
* **Chi tiết**: Truy cập trực tiếp biến `events` để lọc thay vì sử dụng callback update `setEvents(prev => ...)`. Khi click liên tục hoặc giải quyết nhiều cảnh báo nhanh, dữ liệu của lần cập nhật trước có thể bị ghi đè do bất đồng bộ.

#### 2.6. 🟡 MEDIUM: Logic tính toán Clock Drift của Token bị sai hướng
* **Tệp ảnh hưởng**: [authStore.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/stores/authStore.ts#L47-L51) (Dòng 47-51)
* **Chi tiết**: Thay vì trừ đi 10 giây để đảm bảo token còn hạn sử dụng ít nhất 10 giây, code lại cộng thêm 10 giây: `decoded.exp * 1000 < (Date.now() + 10000)`. Điều này khiến token bị phán đoán hết hạn sớm hơn thực tế 10 giây, gây đăng xuất sớm đột ngột.

---

### PHA 3: TYPESCRIPT

#### 3.1. 🔴 CRITICAL: Lạm dụng kiểu dữ liệu `any` trong việc bắt lỗi (catch blocks)
* **Tệp ảnh hưởng**:
  * [LoginPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/LoginPage.tsx#L49) (Dòng 49)
  * [RegisterPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/RegisterPage.tsx#L67) (Dòng 67)
* **Chi tiết**: Sử dụng `catch (err: any)` loại bỏ hoàn toàn tính năng kiểm tra kiểu dữ liệu compile-time của TypeScript. Cần chuyển sang type guard `axios.isAxiosError(err)`.

#### 3.2. 🟠 HIGH: Hàm dịch thuật `t` không được định nghĩa kiểu đầu ra chặt chẽ
* **Tệp ảnh hưởng**: [useTranslation.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/hooks/useTranslation.ts) (Tệp trống)
* **Chi tiết**: Hàm dịch thuật không so sánh đối chiếu tự động xem file ngôn ngữ tiếng Việt (`vi`) có đủ các khóa (keys) giống như file tiếng Anh (`en`) hay không, dễ dẫn đến hiện tượng hiển thị thiếu chữ hoặc hiển thị key thuần trên màn hình.

#### 3.3. 🟠 HIGH: Lạm dụng kiểu `Record<string, React.CSSProperties>` làm mất tính an toàn thuộc tính
* **Tệp ảnh hưởng**: Tất cả tệp khai báo style CSS-in-JS.
* **Chi tiết**: Việc ép kiểu `Record<string, React.CSSProperties>` khiến IDE không báo lỗi nếu truy cập thuộc tính css không tồn tại (ví dụ `styles.noExist`). Nên dùng toán tử `const` hoặc `satisfies React.CSSProperties` của TS 4.9+.

#### 3.4. 🟡 MEDIUM: Sử dụng Magic Number cho vai trò (Role Control)
* **Tệp ảnh hưởng**: [authStore.ts#L70](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/stores/authStore.ts#L70), [Header.tsx#L70](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L70)
* **Chi tiết**: So sánh cứng `user.role_id === 1` thay vì sử dụng Enum. Nếu backend cập nhật lại ID vai trò, frontend sẽ bị lỗi phân quyền ngầm mà không có cảnh báo compile-time.

---

### PHA 4: HIỆU NĂNG (PERFORMANCE)

#### 4.1. 🔴 CRITICAL: Lưu ID bộ đếm thời gian (`setInterval`) vào React State thay vì Ref
* **Tệp ảnh hưởng**: [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L48) (Dòng 48)
* **Chi tiết**: Việc dùng `const [simInterval, setSimInterval] = useState(...)` khiến mỗi lần cập nhật tham chiếu của timer sẽ ép component cha render lại liên tục trong khi tiến trình simulation đang chạy. Nên chuyển sang `useRef`.

#### 4.2. 🟠 HIGH: Tái tạo đối tượng Style inline trên mỗi lượt render (Re-render object recreation)
* **Tệp ảnh hưởng**: Các nút bấm chuyển tab ở `VideoTestPage.tsx` và các thẻ card trong `FireHistorySidebar.tsx`.
* **Chi tiết**: Logic như `style={{ ...styles.tabBtn, borderBottomColor: activeTab === 'upload' ? ... }}` khởi tạo đối tượng mới trên mọi lượt vẽ giao diện, gây áp lực lên GC (Garbage Collector) của trình duyệt.

#### 4.3. 🟠 HIGH: Hàm `isTokenExpired` giải mã JWT liên tục không có cơ chế lưu vết (Memoization)
* **Tệp ảnh hưởng**: [authStore.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/stores/authStore.ts#L90-L120)
* **Chi tiết**: Chuỗi giải mã JWT bao gồm string split, base64 decode, JSON parse. Nếu hàm khởi tạo này bị gọi lặp lại trong các tác vụ kiểm tra phiên, nó sẽ tiêu tốn CPU vô ích.

#### 4.4. 🟡 MEDIUM: Tái tạo mảng tĩnh `links` trên mỗi lượt render
* **Tệp ảnh hưởng**: [Sidebar.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Sidebar.tsx#L16-L23) (Dòng 16-23)
* **Chi tiết**: Mảng liên kết menu `links` nằm trực tiếp trong thân component. Cần đưa ra ngoài hoặc bọc trong `useMemo`.

---

### PHA 5: BẢO MẬT (SECURITY)

#### 5.1. 🔴 CRITICAL: Lưu trữ `refreshToken` trong `localStorage`
* **Tệp ảnh hưởng**: [authStore.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/stores/authStore.ts#L60-L62) (Dòng 60-62)
* **Chi tiết**: Cả `accessToken` và `refreshToken` đều lưu trong `localStorage`. Nếu website dính lỗ hổng XSS, kẻ tấn công dễ dàng đánh cắp cả hai mã khóa này để chiếm quyền điều khiển vĩnh viễn. Token làm mới phải được lưu trữ trong Cookie cấu hình `HttpOnly`.

#### 5.2. 🔴 CRITICAL: Chuyển hướng trang bằng cách gán trực tiếp `window.location.href`
* **Tệp ảnh hưởng**: [axiosInstance.ts](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/utils/axiosInstance.ts#L36) (Dòng 36)
* **Chi tiết**: Khi nhận phản hồi lỗi 401, axios tự động gán cứng href để reload trang. Điều này phá vỡ cơ chế Single Page Application (SPA), làm mất dữ liệu ứng dụng hiện tại và tạo ra nguy cơ bị chuyển hướng độc hại (Open Redirect) nếu backend phản hồi giá trị URL không tin cậy.

#### 5.3. 🔴 CRITICAL: Thiếu hoàn toàn cơ chế tự động làm mới mã đăng nhập (Token Refresh Flow)
* **Tệp ảnh hưởng**: `authStore.ts`, `axiosInstance.ts`
* **Chi tiết**: Dù lưu trữ `refreshToken`, mã nguồn **không hề có** hàm gọi API làm mới token khi token cũ hết hạn. Ứng dụng lập tức đăng xuất và đá người dùng ra trang login khi token cũ hết hạn, tạo ra trải nghiệm sử dụng tồi tệ.

#### 5.4. 🟠 HIGH: Sử dụng thư viện `axios` gốc thay vì `axiosInstance` được cấu hình bảo mật
* **Tệp ảnh hưởng**: [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L2) (Dòng 2)
* **Chi tiết**: Tệp `VideoTestPage` gọi trực tiếp `axios.post` gốc tới `/cameras/test-video` mà không đi qua interceptor của `axiosInstance`. Do đó, yêu cầu này không mang theo token Authorization trong Header, sẽ bị Gateway chặn đứng (lỗi 401).

#### 5.5. 🟠 HIGH: WebSocket kết nối mà không truyền token xác thực
* **Tệp ảnh hưởng**: [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L13), [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L37-L39)
* **Chi tiết**: Mở kết nối WebSocket vô điều kiện không kèm theo bất cứ thông tin xác thực nào. Bất kỳ ai cũng có thể kết nối vào cổng WebSocket Gateway để lắng nghe luồng sự kiện nhạy cảm của hệ thống camera.

#### 5.6. 🟠 HIGH: Cho phép client tự quyết định quyền gửi lên khi Đăng ký (Privilege Escalation)
* **Tệp ảnh hưởng**: [RegisterPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/RegisterPage.tsx#L60) (Dòng 60)
* **Chi tiết**: Gửi cứng trường `role_id: 2` (Operator) từ client lên API đăng ký. Kẻ tấn công có thể dễ dàng sửa gói tin thành `role_id: 1` để tự thăng cấp thành Quản trị viên (Admin) nếu Backend tin tưởng tuyệt đối vào dữ liệu client gửi lên.

#### 5.7. 🟡 MEDIUM: Trình diễn kết quả mô phỏng (Simulation) như thể là kết quả thật
* **Tệp ảnh hưởng**: [VideoTestPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/VideoTestPage.tsx#L62-L146)
* **Chi tiết**: Toàn bộ tiến trình chạy thử video đều sử dụng dữ liệu giả lập ngẫu nhiên ở client (`Math.random()`, `currentPercent += 5`), hoàn toàn bỏ qua kết quả thực từ Backend gửi về. Dữ liệu báo cáo tải về cũng là giả.

#### 5.8. 🟡 MEDIUM: Lỗ hổng tiềm ẩn ghi đè ảnh trong onError (External URL Injection)
* **Tệp ảnh hưởng**: [TestResults.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/video-test/components/TestResults.tsx#L115-L118)
* **Chi tiết**: Khi ảnh crop lỗi, code tự động gán đường dẫn fallback lấy từ địa chỉ API bên ngoài qua biến `crop.id` không được vệ sinh (sanitize).

---

### PHA 6: TẦNG LIÊN KẾT API (API LAYER)

#### 6.1. 🔴 CRITICAL: Thiếu hoàn toàn tầng quản lý API tập trung (Centralized Service Layer)
* **Chi tiết**: Tất cả cuộc gọi API đều viết trực tiếp tại component. Không có thư mục `services` hay `api` nào quản lý tập trung các khai báo endpoint, khiến mã nguồn phân mảnh và cực kỳ khó bảo trì khi cấu trúc API của Backend thay đổi.

#### 6.2. 🟠 HIGH: Thiếu cơ chế hủy yêu cầu HTTP (AbortController)
* **Tệp ảnh hưởng**: `LoginPage.tsx`, `RegisterPage.tsx`, `VideoTestPage.tsx`
* **Chi tiết**: Người dùng bấm login rồi lập tức bấm nút Back hoặc chuyển trang thì request cũ vẫn chạy ngầm. Khi request hoàn thành, ứng dụng cố gắng cập nhật state vào component đã unmount.

#### 6.3. 🟠 HIGH: Thiếu cơ chế tự động thử lại (Retry) đối với các lỗi tạm thời (Transient Errors)
* **Chi tiết**: Gặp sự cố mạng ngắt quãng hoặc server lỗi 503 trong tích tắc, ứng dụng lập tức văng lỗi đỏ thay vì thử lại một vài lần để cải thiện trải nghiệm người dùng.

#### 6.4. 🟠 HIGH: Quản lý mã lỗi HTTP bằng các con số cứng (Magic HTTP Status Codes)
* **Tệp ảnh hưởng**: `LoginPage.tsx`, `RegisterPage.tsx`
* **Chi tiết**: Sử dụng trực tiếp `status === 423` hay `status === 429` rời rạc thay vì ánh xạ thông qua lớp phân tích mã lỗi trung gian.

#### 6.5. 🟡 MEDIUM: Không reset biến `isLoading` khi đăng ký tài khoản thành công
* **Tệp ảnh hưởng**: [RegisterPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/RegisterPage.tsx#L54-L79)
* **Chi tiết**: Sau khi đăng ký thành công và hiển thị popup đợi chuyển hướng, biến `isLoading` vẫn giữ nguyên giá trị `true`. Nếu việc điều hướng router thất bại, nút bấm đăng ký sẽ bị khóa vĩnh viễn cho đến khi tải lại trang.

---

### PHA 7: UI / UX

#### 7.1. 🟠 HIGH: Hiển thị trạng thái tải bằng ký tự dấu ba chấm `'...'`
* **Tệp ảnh hưởng**: [LoginPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/LoginPage.tsx#L149), [RegisterPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/auth/RegisterPage.tsx#L210)
* **Chi tiết**: Thay vì sử dụng Spinner hoặc hiệu ứng mờ nút bấm, giao diện chỉ hiển thị chữ `...` đơn điệu. Điều này không thân thiện với các công cụ đọc màn hình dành cho người khuyết tật (Screen Readers).

#### 7.2. 🟠 HIGH: Thiếu trang thông báo lỗi 404 (Not Found Route)
* **Tệp ảnh hưởng**: [router.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/app/router.tsx)
* **Chi tiết**: Không định nghĩa route catch-all (`path="*"`). Khi người dùng nhập sai URL, ứng dụng render giao diện trống trơn bên trong layout chung.

#### 7.3. 🟠 HIGH: Bảng điều khiển giả lập cảnh báo (Dev Sim Controls) hiển thị ở Prod
* **Tệp ảnh hưởng**: [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L143-L174)
* **Chi tiết**: Phần nút bấm giả lập cháy (Trigger Dock, Trigger Server) không được ẩn đi khi chạy ở môi trường production. Bất kỳ nhân viên vận hành nào cũng có thể nhấn nhầm để tạo cảnh báo giả.

#### 7.4. 🟡 MEDIUM: Chiều rộng Sidebar cố định gây vỡ bố cục trên màn hình nhỏ (Responsive Break)
* **Tệp ảnh hưởng**: [MainLayout.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/MainLayout.tsx#L36), [Header.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/shared/components/layout/Header.tsx#L99)
* **Chi tiết**: Sử dụng lề và kích thước cố định bằng pixel (`left: '240px'`, `marginLeft: '240px'`). Không dùng Grid/Flex responsive hoặc CSS Media Queries, khiến giao diện bị đè vỡ hoàn toàn khi mở trên máy tính bảng hoặc thiết bị di động.

#### 7.5. 🟡 MEDIUM: Xung đột chỉ số hiển thị z-index giữa các lớp giao diện
* **Tệp ảnh hưởng**: [FireHistorySidebar.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/components/FireHistorySidebar.tsx#L115)
* **Chi tiết**: Thanh sidebar cảnh báo cháy đặt `zIndex: 98`, trong khi Header là `99` và Sidebar chính là `100`. Nếu trang có thêm các modal hoặc popup động khác, thanh thông tin cháy này rất dễ bị chìm xuống dưới hoặc hiển thị đè đan xen lỗi mắt.

#### 7.6. 🟡 MEDIUM: Padding bù trừ tĩnh bị sai lệch
* **Tệp ảnh hưởng**: [FireDetectionPage.tsx](file:///c:/Users/dungv/Intelligent-Multi-Camera-Person-Tracking-Video-Search-System/apps/web/src/features/fire-detection/FireDetectionPage.tsx#L198-L200)
* **Chi tiết**: Set cứng `paddingRight: '320px'` để nhường chỗ cho thanh sidebar. Cấu trúc lề tĩnh này sẽ bị lệch ngay khi kích thước màn hình thay đổi.

---

### PHA 8: KIỂM THỬ (TESTING)

#### 8.1. 🔴 CRITICAL: Hoàn toàn không có tệp kiểm thử tự động (Zero Test Files)
* **Chi tiết**: Thư mục `apps/web/tests/` hoàn toàn trống rỗng. Không có Unit Test cho logic Store, không có Integration Test cho Route Guard và không có E2E Test cho luồng đăng nhập/đăng ký.

#### 8.2. 🟠 HIGH: Lỗi tính toán Clock Drift của Token không được phát hiện do thiếu Unit Test
* **Chi tiết**: Lỗi dấu cộng `+ 10000` (Phase 2.6) hoàn toàn có thể được phát hiện ngay lập tức ở môi trường dev nếu có tối thiểu một bộ kiểm thử unit test cho hàm `isTokenExpired`.

#### 8.3. 🟡 MEDIUM: Thiếu kiểm thử luồng nghiệp vụ đầu cuối (E2E Test)
* **Chi tiết**: Không có kịch bản chạy thử tự động (Playwright/Cypress) giả lập hành vi người dùng đăng nhập hệ thống và xem sự kiện.

---

## 🚀 ĐỀ XUẤT 5 FIX ƯU TIÊN HÀNG ĐẦU (TOP 5 REMEDIATION PRIORITIES)

1. **Khắc phục lỗi logic `isTokenExpired`**  
   * *Nơi sửa*: `shared/stores/authStore.ts` dòng 50.  
   * *Cách sửa*: Đổi phép cộng thành phép trừ: `decoded.exp * 1000 - 10000 < Date.now()` để token hết hạn sớm hơn 10s làm đệm kết nối.
2. **Thay thế State bằng Ref cho bộ đếm thời gian `simInterval`**  
   * *Nơi sửa*: `VideoTestPage.tsx` dòng 48.  
   * *Cách sửa*: Chuyển sang `useRef<number | null>(null)` để loại bỏ việc kích hoạt re-render vô tội vạ.
3. **Đổi cuộc gọi API `axios` gốc sang `axiosInstance` bảo mật**  
   * *Nơi sửa*: `VideoTestPage.tsx` dòng 159 và dòng 175.  
   * *Cách sửa*: Import và gọi thông qua `axiosInstance` để tự động đính kèm Token Authorization bảo mật của tài khoản.
4. **Viết Hook chia sẻ kết nối WebSocket chung**  
   * *Nơi sửa*: Viết mã nguồn vào tệp rỗng `shared/hooks/useWebSocket.ts`.  
   * *Cách sửa*: Đưa logic kết nối WebSocket Gateway vào đây, chỉ cho phép khởi tạo 1 kết nối duy nhất (Singleton Pattern) và chia sẻ trạng thái kết nối thông qua Context hoặc Store.
5. **Khai thác TanStack Query thay vì tự gọi Axios**  
   * *Nơi sửa*: Các trang chức năng Camera CRUD, Lịch sử tracking.  
   * *Cách sửa*: Chuyển đổi mã nguồn sang dùng `useQuery` và `useMutation` để tự động hóa xử lý tải dữ liệu, cache và hủy request (AbortController) tự động.
