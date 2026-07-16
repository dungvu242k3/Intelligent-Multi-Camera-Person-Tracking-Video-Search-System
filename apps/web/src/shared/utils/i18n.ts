export type Locale = 'en' | 'vi';

export const i18nDict = {
  en: {
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.liveMonitor': 'Live Monitor',
    'nav.personSearch': 'Person Search',
    'nav.cameras': 'Cameras',
    'nav.videoTest': 'Video Test',
    'nav.fireAlarms': 'Fire Alarms',

    // Header
    'header.controlCenter': 'Control Center',
    'header.apiCore': 'API Core: Online',
    'header.realtimeConnected': 'Realtime events: Connected',
    'header.realtimeOffline': 'Realtime events: Offline',

    // Video Test page
    'vtest.title': 'Model Trial Runs',
    'vtest.subtitle': 'Upload local recorded clips or supply surveillance RTSP stream links to test YOLOv8 detection and ReID tracking accuracy.',
    'vtest.tabUpload': 'Upload Video File',
    'vtest.tabUrl': 'Stream Link / URL',
    'vtest.cancel': 'Cancel Run',
    'vtest.reset': 'Reset & Run Another Test',
    'vtest.exportJson': 'Export JSON',
    
    // Video Test uploader
    'vtest.uploader.title': 'Drag and drop video files here',
    'vtest.uploader.sub': 'Supports MP4, AVI, MKV, MOV up to 250MB',
    'vtest.uploader.browse': 'Browse Files',
    'vtest.uploader.errFormat': 'Invalid file format. Supported files: .mp4, .avi, .mkv, .mov',
    'vtest.uploader.errSize': 'File size exceeds 250MB limit.',

    // Video Test Url input
    'vtest.url.placeholder': 'e.g. rtsp://192.168.1.100:554/stream1 or https://example.com/stream.mp4',
    'vtest.url.btn': 'Analyze URL',
    'vtest.url.errEmpty': 'Please specify a stream URL or endpoint path.',
    'vtest.url.errSchema': 'URL must start with rtsp://, http://, or https:// schema.',

    // Video Test Progress
    'vtest.progress.uploading': 'Uploading video payload to API Gateway...',
    'vtest.progress.initDecoder': 'Initializing hardware accelerated GPU decoder (nvv4l2decoder)...',
    'vtest.progress.analyzing': 'Analyzing frames... Processing frame',
    'vtest.progress.aggregating': 'Aggregating DeepStream metadata metrics & saving crops...',
    'vtest.progress.persons': 'Persons Detected',
    'vtest.progress.fires': 'Fire Incidents',
    'vtest.progress.objects': 'Objects Detected',
    'vtest.progress.fps': 'Inference (FPS)',

    // Video Test Results
    'vtest.results.completed': 'Analysis Completed Successfully',
    'vtest.results.processed': 'Processed {frames} frames in {secs}s (Speed: {fps} FPS)',
    'vtest.results.chartTitle': 'Detection Timeline Distribution',
    'vtest.results.galleryTitle': 'Keyframe Detections Gallery',
    'vtest.results.emptyGallery': 'No keyframe object crops captured.',
    'vtest.results.time': 'Time',
    'vtest.results.confidence': 'Confidence',

    // Fire Detection page
    'fire.title': 'Fire Surveillance Center',
    'fire.subtitle': 'Monitor real-time visual alerts and smoke signatures. Red blinking markers represent localized fire incidents.',
    'fire.mapTitle': 'Facility Interactive Floor Map',
    'fire.legendNominal': 'Nominal',
    'fire.legendActive': 'Active Fire',
    
    // Fire Detection simulation panel
    'fire.devControls': 'Developer Simulation Controls',
    'fire.btnTriggerDock': 'Trigger Fire (Loading Dock A)',
    'fire.btnTriggerServer': 'Trigger Fire (Server Room)',
    'fire.btnClear': 'Clear All Alarms',

    // Fire Detection Sidebar
    'fire.sidebarTitle': 'Fire Alerts Incident Log',
    'fire.sidebarCritMsg': 'CRITICAL: Flame/Smoke signature detected on GPU analytics engine!',
    'fire.sidebarResolveMsg': 'Fire safety verification check: RESOLVED.',
    'fire.sidebarBtnResolve': 'Mark as Resolved',
    'fire.sidebarEmptyHeader': 'All Zones Nominal',
    'fire.sidebarEmptyText': 'No active fire signature warnings detected.',

    // Secure Errors mapping (Prevent backend details leak)
    'error.401': 'Session expired. Please log in again.',
    'error.403': 'Access denied. You do not have permission for this action.',
    'error.429': 'Rate limit exceeded. Please wait a few minutes before trying again.',
    'error.500': 'Server connection failure. Please contact administrator.',
    'error.generic': 'An unexpected error occurred. Please try again.',
  },
  vi: {
    // Navigation
    'nav.dashboard': 'Tổng Quan',
    'nav.liveMonitor': 'Giám Sát Trực Tiếp',
    'nav.personSearch': 'Tìm Kiếm Người',
    'nav.cameras': 'Quản Lý Camera',
    'nav.videoTest': 'Thử Nghiệm Video',
    'nav.fireAlarms': 'Cảnh Báo Cháy',

    // Header
    'header.controlCenter': 'Trung Tâm Điều Khiển',
    'header.apiCore': 'Kết nối API: Hoạt động',
    'header.realtimeConnected': 'Sự kiện Realtime: Đang kết nối',
    'header.realtimeOffline': 'Sự kiện Realtime: Mất kết nối',

    // Video Test page
    'vtest.title': 'Chạy Thử Nghiệm Mô Hình',
    'vtest.subtitle': 'Tải lên video clip cục bộ hoặc cung cấp link luồng RTSP để chạy thử nghiệm độ chính xác của YOLOv8 và bộ định danh ReID.',
    'vtest.tabUpload': 'Tải Lên File Video',
    'vtest.tabUrl': 'Link Luồng Video / URL',
    'vtest.cancel': 'Hủy Chạy',
    'vtest.reset': 'Thiết Lập Lại & Chạy Thử Mới',
    'vtest.exportJson': 'Xuất File JSON',
    
    // Video Test uploader
    'vtest.uploader.title': 'Kéo thả file video vào đây',
    'vtest.uploader.sub': 'Hỗ trợ định dạng MP4, AVI, MKV, MOV tối đa 250MB',
    'vtest.uploader.browse': 'Chọn File',
    'vtest.uploader.errFormat': 'Định dạng file không hợp lệ. Các định dạng hỗ trợ: .mp4, .avi, .mkv, .mov',
    'vtest.uploader.errSize': 'Kích thước file vượt quá giới hạn 250MB.',

    // Video Test Url input
    'vtest.url.placeholder': 'Ví dụ: rtsp://192.168.1.100:554/stream1 hoặc https://example.com/stream.mp4',
    'vtest.url.btn': 'Phân Tích URL',
    'vtest.url.errEmpty': 'Vui lòng cung cấp link luồng video hoặc endpoint.',
    'vtest.url.errSchema': 'Đường dẫn URL phải bắt đầu bằng rtsp://, http://, hoặc https://.',

    // Video Test Progress
    'vtest.progress.uploading': 'Đang tải file video lên API Gateway...',
    'vtest.progress.initDecoder': 'Đang khởi tạo bộ giải mã phần cứng GPU (nvv4l2decoder)...',
    'vtest.progress.analyzing': 'Đang phân tích các khung hình... Xử lý frame',
    'vtest.progress.aggregating': 'Đang tổng hợp siêu dữ liệu DeepStream & lưu trữ ảnh crop...',
    'vtest.progress.persons': 'Nhân Số Phát Hiện',
    'vtest.progress.fires': 'Số Điểm Phát Lửa',
    'vtest.progress.objects': 'Vật Thể Phát Hiện',
    'vtest.progress.fps': 'Tốc Độ Xử Lý (FPS)',

    // Video Test Results
    'vtest.results.completed': 'Phân Tích Thành Công',
    'vtest.results.processed': 'Đã xử lý xong {frames} frames trong {secs}s (Tốc độ: {fps} FPS)',
    'vtest.results.chartTitle': 'Dòng Thời Gian Phân Phối Phát Hiện',
    'vtest.results.galleryTitle': 'Thư Viện Ảnh Crop Keyframe Nhận Diện',
    'vtest.results.emptyGallery': 'Không có ảnh crop keyframe nào được chụp lại.',
    'vtest.results.time': 'Thời gian',
    'vtest.results.confidence': 'Độ tin cậy',

    // Fire Detection page
    'fire.title': 'Trung Tâm Giám Sát Phòng Cháy',
    'fire.subtitle': 'Theo dõi các cảnh báo khói lửa thời gian thực. Các điểm tròn nhấp nháy đỏ biểu thị sự cố cháy tại vị trí camera.',
    'fire.mapTitle': 'Sơ Đồ Mặt Bằng Tòa Nhà',
    'fire.legendNominal': 'Bình Thường',
    'fire.legendActive': 'Phát Hiện Cháy',
    
    // Fire Detection simulation panel
    'fire.devControls': 'Bảng Điều Khiển Giả Lập Phát Hỏa',
    'fire.btnTriggerDock': 'Kích Hoạt Cháy (Khu Vực Bốc Dỡ A)',
    'fire.btnTriggerServer': 'Kích Hoạt Cháy (Phòng Máy Chủ)',
    'fire.btnClear': 'Xóa Mọi Báo Động',

    // Fire Detection Sidebar
    'fire.sidebarTitle': 'Nhật Ký Sự Cố Cháy Realtime',
    'fire.sidebarCritMsg': 'NGUY HIỂM: Phát hiện dấu hiệu ngọn lửa/khói từ camera xử lý GPU!',
    'fire.sidebarResolveMsg': 'Đã xác minh kiểm tra an toàn: ĐÃ GIẢI QUYẾT.',
    'fire.sidebarBtnResolve': 'Xác Nhận Giải Quyết',
    'fire.sidebarEmptyHeader': 'Các Khu Vực An Toàn',
    'fire.sidebarEmptyText': 'Không có bất kỳ dấu hiệu cháy nổ nào được ghi nhận.',

    // Secure Errors mapping
    'error.401': 'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.',
    'error.403': 'Từ chối truy cập. Bạn không có quyền thực hiện hành động này.',
    'error.429': 'Tần suất gửi yêu cầu quá nhanh. Vui lòng thử lại sau ít phút.',
    'error.500': 'Hệ thống gặp sự cố kết nối. Vui lòng liên hệ quản trị viên.',
    'error.generic': 'Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.',
  }
};
