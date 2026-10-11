# Toàn bộ chuỗi hiển thị tiếng Việt của giao diện (tên file/biến tiếng Anh, chuỗi tiếng Việt chỉ nằm ở đây).
# Nguồn chuỗi: các file Stitch trong stitch/html; chỗ nào Stitch ghi sai so với báo cáo thì dùng chuỗi theo báo cáo (xem docs/stitch-mapping.md).
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI

APP_NAME = "EmoVoice"
APP_TAGLINE = "Nhận diện cảm xúc"
APP_DESCRIPTION = "Hệ thống phân tích cảm xúc giọng nói tiếng Việt"

EMOTION_VI = dict(zip(EMOTION_NAMES, EMOTION_NAMES_VI))

# ---- Điều hướng ----
NAV_GROUP_ANALYSIS = "Tác vụ phân tích"
NAV_GROUP_ML = "Học máy & tài nguyên"
NAV_GROUP_ADMIN = "Quản trị hệ thống"
NAV_ANALYZE = "Phân tích cảm xúc"
NAV_HISTORY = "Lịch sử phân tích"
NAV_MODELS = "Mô hình & hiệu năng"
NAV_ADMIN_OVERVIEW = "Tổng quan"
NAV_ADMIN_USERS = "Quản lý người dùng"
NAV_ADMIN_LOGS = "Nhật ký hệ thống"
NAV_ADMIN_MODELS = "Quản lý mô hình AI"
NAV_ADMIN_AUDIO = "Quản lý dữ liệu âm thanh"
LOGOUT = "Đăng xuất"
ROLE_USER_VI = "Người dùng"
ROLE_ADMIN_VI = "Quản trị viên"
BREADCRUMB_HOME = "Trang chủ"
BREADCRUMB_ADMIN = "Quản trị"
SYSTEM_READY = "Hệ thống sẵn sàng"

# ---- Đăng nhập / Đăng ký / Quên mật khẩu ----
LOGIN_NAV_ABOUT = "Giới thiệu"
LOGIN_NAV_GUIDE = "Hướng dẫn"
LOGIN_HERO_TITLE = "Hiểu cảm xúc qua giọng nói"
LOGIN_HERO_SUB = "Tải tệp hoặc thu âm, nhận kết quả cảm xúc kèm giải thích trực quan."
LOGIN_HERO_POINTS = [
    "8 trạng thái cảm xúc theo ngữ điệu",
    "Giải thích bằng biểu đồ chú ý theo thời gian (XAI)",
    "Lưu và đối soát lịch sử phân tích",
]
TAB_LOGIN = "Đăng nhập"
TAB_REGISTER = "Đăng ký"
LOGIN_TITLE = "Chào mừng quay lại"
LOGIN_SUB = "Nhập thông tin xác thực để truy cập bảng điều khiển"
REGISTER_TITLE = "Tạo tài khoản mới"
REGISTER_SUB = "Đăng ký để lưu lịch sử phân tích của bạn"
FORGOT_TITLE = "Quên mật khẩu"
FORGOT_SUB_STEP1 = "Nhập email đã đăng ký, hệ thống sẽ gửi mã đặt lại mật khẩu"
FORGOT_SUB_STEP2 = "Nhập mã đặt lại và mật khẩu mới"
FIELD_USERNAME = "Tên tài khoản"
FIELD_USERNAME_PH = "Nhập tên tài khoản"
FIELD_USERNAME_OR_EMAIL = "Tên tài khoản hoặc email"
FIELD_EMAIL = "Email"
FIELD_EMAIL_PH = "ten@example.com"
FIELD_PASSWORD = "Mật khẩu"
FIELD_PASSWORD_PH = "Nhập mật khẩu"
FIELD_CONFIRM_PASSWORD = "Nhập lại mật khẩu"
FIELD_NEW_PASSWORD = "Mật khẩu mới"
FIELD_RESET_CODE = "Mã đặt lại"
FIELD_RESET_CODE_PH = "Dán mã bạn nhận được"
REMEMBER_ME = "Ghi nhớ đăng nhập"
FORGOT_LINK = "Quên mật khẩu?"
BTN_LOGIN = "Xác nhận đăng nhập"
BTN_REGISTER = "Tạo tài khoản"
BTN_SEND_RESET = "Gửi mã đặt lại"
BTN_RESET = "Đặt lại mật khẩu"
BTN_BACK_TO_LOGIN = "Quay lại đăng nhập"
NO_ACCOUNT = "Chưa có tài khoản?"
BTN_GOTO_REGISTER = "Đăng ký ngay"
BTN_DEV_USER = "Vào thử (Người dùng)"
BTN_DEV_ADMIN = "Vào thử (Quản trị viên)"
DEV_BYPASS_NOTE = "Chế độ dev: DEV_BYPASS_LOGIN=1 — chỉ để xem giao diện, tắt khi triển khai."
MSG_NOT_IMPLEMENTED = "Chức năng này chưa được cài đặt ({detail})."
MSG_FILL_ALL = "Vui lòng nhập đầy đủ thông tin."
MSG_PASSWORD_MISMATCH = "Mật khẩu nhập lại không khớp."
MSG_RESET_SENT = "Nếu email tồn tại, mã đặt lại đã được tạo. Mã có hiệu lực {minutes} phút."
MSG_RESET_DONE = "Đã đặt lại mật khẩu. Bạn có thể đăng nhập."
MSG_LOGIN_ERROR = "Sai tài khoản hoặc mật khẩu"
MSG_DENIED = "Bạn không có quyền thực hiện thao tác này."

# ---- Phân tích mới ----
STEPPER_EYEBROW = "Tiến trình xử lý ngôn ngữ âm thanh"
STEPPER_TITLE = "Phân tích biểu cảm hội thoại"
STEPPER_TITLES = ["Tải âm thanh", "Tiền xử lý", "Phân tích AI", "Kết quả XAI"]
# Phụ đề từng bước theo trạng thái trang: input / processing / result (Stitch ghi 'CRNN/Wav2Vec', 'SHAP' — sai so với báo cáo nên đã thay)
STEPPER_SUBS = {
    "input": ["Đang cấu hình", "Chờ âm thanh", "DistilHuBERT + LoRA", "Biểu đồ chú ý"],
    "processing": ["Hoàn tất", "Đang xử lý", "DistilHuBERT + LoRA", "Biểu đồ chú ý"],
    "result": ["Hoàn tất", "Hoàn tất", "Hoàn tất", "Biểu đồ chú ý"],
}
TAB_UPLOAD = "Tải tệp lên"
TAB_RECORD = "Thu âm trực tiếp"
UPLOAD_TITLE = "Kéo thả hoặc chọn tệp WAV / MP3 từ máy tính"
UPLOAD_HINT = "Thời lượng khuyến nghị 1 – 5 giây, dung lượng tối đa {max_mb} MB."
PREPROC_TITLE = "Tiền xử lý âm thanh áp dụng tự động"
PREPROC_CHIPS = [
    "Tần số lấy mẫu: <strong>16 kHz</strong>, mono",
    "Cắt khoảng lặng (top_db = 25)",
    "Chuẩn hóa biên độ [-1, 1]",
    "Cố định độ dài 3 giây (48.000 mẫu)",
]
BTN_ANALYZE = "Thực hiện phân tích cảm xúc"
TIP_TITLE = "Gợi ý thu nhận âm học tối ưu"
TIP_TEXT = "Mô hình hoạt động chính xác nhất khi mẫu giọng nói rõ, một người nói và môi trường có độ ồn nền thấp."
DIAG_TITLE = "Chẩn đoán & trạng thái lỗi đầu vào"
DIAG_SAMPLE_TAG = "Mô phỏng"
TOAST_FORMAT_TITLE = "Lỗi định dạng âm thanh"
TOAST_FORMAT_TEXT = "Định dạng không được hỗ trợ, vui lòng chọn WAV hoặc MP3."
TOAST_MIC_TITLE = "Cảnh báo thiết bị ghi"
TOAST_MIC_TEXT = "Không tìm thấy micro hoặc chưa cấp quyền truy cập trình duyệt."
TOAST_VAD_TITLE = "Cảnh báo chất lượng âm"
TOAST_VAD_TEXT = "Không phát hiện giọng nói rõ ràng trong đoạn âm thanh."
TOAST_NO_FILE_TITLE = "Chưa có âm thanh"
TOAST_NO_FILE_TEXT = "Vui lòng tải tệp lên hoặc thu âm trước khi phân tích."
PARAMS_TITLE = "Tham số âm phổ ban đầu"
PARAM_SNR = "Tỷ lệ tín hiệu / nhiễu"
PARAM_F0 = "Tần số cơ bản F0"
PARAM_ZCR = "Tốc độ cắt không (ZCR)"
PROCESSING_TITLE = "Đang xử lý âm thanh"
PROCESSING_STEPS = [
    "Nạp tệp, chuyển về 16 kHz mono",
    "Cắt khoảng lặng (top_db = 25)",
    "Chuẩn hóa biên độ, cố định 3 giây",
    "Suy luận DistilHuBERT + LoRA",
    "Tạo biểu đồ chú ý (XAI)",
]
SAMPLE_RESULT_NOTE = "Đang hiển thị kết quả mẫu: mô hình chưa được tích hợp (UC04)."

# ---- Kết quả ----
BTN_ANALYZE_ANOTHER = "Phân tích tệp khác"
BTN_DOWNLOAD_RESULT = "Tải ảnh kết quả"
HERO_EYEBROW = "Cảm xúc dự đoán chính"
HERO_EYEBROW_SUB = "Phân loại giọng đọc đơn"
HERO_LABEL_CHIP = "NHÃN DỰ ĐOÁN"
CONFIDENCE = "Độ tin cậy"
CONFIDENCE_THRESHOLD = "Ngưỡng cảnh báo: < {pct}%"
CONFIDENCE_TOOLTIP = "Độ tin cậy là xác suất của nhãn dự đoán sau softmax qua 8 lớp cảm xúc."
BARS_TITLE = "Phân phối xác suất Softmax"
BARS_SUB = "Tập 8 nhóm cảm xúc"
XAI_TITLE = "Biểu đồ chú ý theo thời gian (Explainable AI - XAI)"
XAI_SUB = "Trọng số Temporal Attention Pooling (149 khung / 3 giây) căn theo dạng sóng"
XAI_LEGEND = "Mức độ chú ý:"
XAI_LEVELS = ["Rất thấp", "Thấp", "Trung bình", "Cao", "Rất cao"]
XAI_LEGEND_RANGE = "(Rất thấp → Rất cao)"
XAI_REAL_END = "Kết thúc giọng nói thực tế ({sec}s)"
XAI_NOTE = "<strong>Giải thích trực quan:</strong> ô đậm hơn là đoạn âm thanh mà mô hình chú ý nhiều nhất khi đưa ra dự đoán. Attention chỉ là công cụ hỗ trợ diễn giải, không phải lời giải thích đầy đủ."
LOW_CONF_TITLE = "Độ tin cậy thấp"
LOW_CONF_TEXT = "Mọi xác suất đều dưới {pct}%, kết quả có thể không chính xác do tiếng ồn môi trường hoặc giọng nói không liên tục."
LOW_CONF_BUTTON = "Xem phân tích nhiễu"
PAGE_RESULT_CRUMB = "Kết quả"
AROUSAL_VI = {
    "neutral": "Mức kích thích thấp",
    "calm": "Mức kích thích thấp",
    "happy": "Mức kích thích cao",
    "sad": "Mức kích thích thấp",
    "angry": "Mức kích thích cao",
    "fearful": "Mức kích thích cao",
    "disgust": "Mức kích thích cao",
    "surprised": "Mức kích thích cao",
}
HERO_DESC = "Mô hình dự đoán «{label}» với độ tin cậy {conf}. Vùng được chú ý nhiều nhất nằm ở khoảng {t0} – {t1} giây."
HERO_FOOT_LEFT = "Dạng sóng đã chuẩn hóa 16 kHz, 3 giây"
HERO_FOOT_RIGHT = "Giọng nói thực tế: {sec}s"

# ---- Lịch sử ----
HISTORY_EYEBROW = "Phân hệ lưu trữ • UC05 - Lịch sử phân tích"
HISTORY_TITLE = "Lịch sử phân tích"
HISTORY_SUB = "Tra cứu, đối soát kết quả suy luận và giải thích chú ý (XAI) cho các bản ghi của bạn."
HISTORY_TOTAL = "Tổng bản ghi"
HISTORY_AVG_CONF = "Độ tin cậy TB"
HISTORY_SEARCH_PH = "Tìm kiếm theo tên tệp âm thanh..."
HISTORY_ALL_EMOTIONS = "Tất cả cảm xúc (8 nhãn)"
HISTORY_TIME_CHOICES = ["7 ngày qua", "30 ngày qua", "Tất cả"]
BTN_EXPORT = "Xuất dữ liệu Excel"
BTN_NEW_ANALYSIS = "Phân tích mới"
TABLE_COL_FILE = "Tệp âm thanh"
TABLE_COL_EMOTION = "Cảm xúc dự đoán"
TABLE_COL_CONFIDENCE = "Độ tin cậy"
TABLE_COL_MODEL = "Mô hình"
TABLE_COL_TIME = "Thời gian"
HISTORY_SELECT_HINT = "Chọn một dòng trong bảng để xem chi tiết XAI."
EMPTY_HISTORY_TITLE = "Chưa có lịch sử phân tích trong khoảng thời gian này?"
EMPTY_HISTORY_TEXT = "Thử điều chỉnh lại bộ lọc cảm xúc, ngày thực hiện hoặc tiến hành nạp bản ghi mới để tính toán."
BTN_START_NOW = "Bắt đầu phân tích ngay"
DRAWER_TITLE = "Chi tiết giải thích XAI"
DRAWER_WAVEFORM = "Dạng sóng âm học (Waveform)"
DRAWER_HEATMAP = "Bản đồ nhiệt chú ý theo thời gian"
DRAWER_HEATMAP_TAG = "5 bậc rời rạc"
DRAWER_PROBS = "Phân bố xác suất 8 cảm xúc"
BTN_CLOSE_DRAWER = "Đóng bảng"
BTN_DOWNLOAD_JSON = "Tải báo cáo JSON"

# ---- Phân trang ----
PAGINATION_INFO = "Hiển thị {start}–{end} trong {total} kết quả"
PAGINATION_PAGE_SIZE = "Số dòng mỗi trang"
PAGINATION_PREV = "Trước"
PAGINATION_NEXT = "Sau"

# ---- Mô hình & hiệu năng ----
MODELS_EYEBROW = "Hệ thống đánh giá & thực nghiệm"
MODELS_TITLE = "Mô hình & hiệu năng"
MODELS_SUB = "Phân tích độ chính xác phân loại, độ trễ suy luận và kích thước mô hình trước/sau cải tiến."
MODELS_ACTIVE_TAG = "Đang phục vụ trực tiếp"
MODELS_HERO_DESC = "Backbone DistilHuBERT đóng băng + LoRA (r=8, alpha=16) gắn q_proj/v_proj + Temporal Attention Pooling + head 768→256→8."
METRIC_ACCURACY = "Độ chính xác (Accuracy)"
METRIC_F1 = "Macro F1-Score"
METRIC_TRAINABLE = "Tham số huấn luyện (LoRA + head)"
METRIC_SIZE_LATENCY = "Dung lượng & độ trễ"
CHART_ACCURACY_TITLE = "Độ chính xác tổng thể"
CHART_ACCURACY_UNIT = "Accuracy (%)"
CHART_LATENCY_TITLE = "Thời gian suy luận"
CHART_LATENCY_UNIT = "Latency (ms/mẫu)"
CHART_SIZE_TITLE = "Dung lượng mô hình"
CHART_SIZE_UNIT = "Checkpoint (MiB)"
CHART_NOT_MEASURED = "Chưa đo"
COMPARISON_TABLE_TITLE = "Bảng so sánh các mô hình thử nghiệm"
COMPARISON_TABLE_SUB = "Kết quả trên tập Test độc lập ({n} mẫu, {dataset})."
COL_MODEL_NAME = "Tên mô hình"
COL_ARCH = "Kiến trúc"
COL_STATUS = "Trạng thái"
STATUS_LABELS = {"active": "Đang dùng", "baseline": "Baseline", "pending": "Chưa đo"}
CM_TITLE = "Ma trận nhầm lẫn 8 cảm xúc (Confusion Matrix)"
CM_SUB = "Chuẩn hóa theo hàng: mỗi ô là tỷ lệ mẫu của nhãn thực tế được dự đoán thành nhãn tương ứng."
CM_SCALE = "Thang tỷ lệ:"
CM_X_AXIS = "Nhãn dự đoán (Predicted) →"
CM_Y_AXIS = "Nhãn thực tế (Ground truth)"
CM_PICK_MODEL = "Chọn mô hình"
CM_NO_DATA = "Chưa có ma trận nhầm lẫn cho mô hình này (cần xuất từ ml/evaluate.py)."
MODELS_INSIGHT_TITLES = ["Tần số lấy mẫu", "Tham số huấn luyện", "Lượng tử hóa / Pruning"]
MODELS_INSIGHT_QUANT = "Chưa thực hiện Pruning hay lượng tử hóa (đề cương tuần 6 - 7, báo cáo ghi nhận chưa làm)."

# ---- Admin ----
ADMIN_OVERVIEW_EYEBROW = "Phân hệ quản trị tập trung (UC06) / Chỉ dành cho Quản trị viên"
ADMIN_OVERVIEW_TITLE = "Quản trị hệ thống & giám sát"
KPI_ANALYSES = "Tổng lượt phân tích"
KPI_ACCOUNTS = "Số tài khoản hoạt động"
KPI_ACTIVE_MODEL = "Mô hình đang kích hoạt"
KPI_SERVICE = "Trạng thái dịch vụ"
KPI_SERVICE_OK = "Hoạt động bình thường"
CHART_DAILY_TITLE = "Lượt phân tích theo ngày"
CHART_DAILY_SUB = "Khối lượng yêu cầu trong 7 ngày gần nhất"
CHART_DIST_TITLE = "Phân bố 8 cảm xúc"
CHART_DIST_SUB = "Tỷ lệ nhãn dự đoán toàn hệ thống"
STATUS_TITLE = "Trạng thái dịch vụ cốt lõi"
STATUS_SUB = "Giám sát ứng dụng, mô hình và cơ sở dữ liệu"
STATUS_NAMES = [
    ("Ứng dụng Gradio", "Giao diện web và xử lý yêu cầu"),
    ("Mô hình AI", "DistilHuBERT + LoRA đã nạp"),
    ("Cơ sở dữ liệu", "SQLite (SQLAlchemy)"),
]
STATUS_OK = "Ổn định"
ADMIN_USERS_EYEBROW = "UC06 / Quản lý người dùng"
ADMIN_USERS_TITLE = "Quản lý người dùng hệ thống"
ADMIN_USERS_SUB = "Danh sách tài khoản, vai trò và trạng thái."
ADMIN_USERS_SEARCH_PH = "Tìm tài khoản hoặc email..."
BTN_ADD_USER = "Thêm"
COL_USERNAME = "Tên tài khoản"
COL_EMAIL = "Email"
COL_ROLE = "Vai trò"
COL_USAGE = "Lượt đã dùng"
COL_ACTIVE = "Trạng thái"
STATE_ACTIVE = "Hoạt động"
STATE_LOCKED = "Đã khóa"
BTN_TOGGLE_USER = "Khóa / mở khóa tài khoản đã chọn"
ADMIN_LOGS_EYEBROW = "UC06 / Nhật ký hệ thống"
ADMIN_LOGS_TITLE = "Nhật ký hệ thống"
ADMIN_LOGS_SUB = "Sự kiện và lỗi của ứng dụng, mô hình và cơ sở dữ liệu."
LOG_LEVELS = ["Tất cả mức", "INFO", "WARNING", "ERROR"]
LOG_SEARCH_PH = "Tìm trong nội dung nhật ký..."
COL_LEVEL = "Mức"
COL_SERVICE = "Dịch vụ"
COL_MESSAGE = "Nội dung"
COL_USER = "Người dùng"
ADMIN_MODELS_EYEBROW = "UC06 / Quản lý mô hình AI (chưa có khung Stitch)"
ADMIN_MODELS_TITLE = "Quản lý mô hình AI"
ADMIN_MODELS_SUB = "Xem chỉ số các mô hình và chọn mô hình đang dùng để suy luận."
BTN_SET_ACTIVE_MODEL = "Đặt làm mô hình đang dùng"
ADMIN_AUDIO_EYEBROW = "UC06 / Quản lý dữ liệu âm thanh (chưa có khung Stitch)"
ADMIN_AUDIO_TITLE = "Quản lý dữ liệu âm thanh"
ADMIN_AUDIO_SUB = "Mẫu âm thanh của mọi người dùng: nghe lại, lọc, tìm kiếm và xóa."
ADMIN_AUDIO_SEARCH_PH = "Tìm theo tên tệp hoặc người dùng..."
BTN_DELETE_AUDIO = "Xóa mẫu đã chọn"
CONFIRM_HINT = "Thao tác này không thể hoàn tác."
SAMPLE_DATA_TAG = "Dữ liệu mẫu"

# ---- Bổ sung: chân biểu đồ, drawer, ghi chú ----
FOOT_DELTA_RF = "Chênh lệch với Random Forest: {delta} điểm %"
FOOT_PENDING_BASELINE = "Chưa có số liệu {names} để so sánh trước/sau cải tiến (cần chạy ml/benchmark.py)."
FOOT_LATENCY_NOTE = "Độ trễ đo chưa đồng nhất giữa các mô hình (báo cáo Bảng 5.4)."
INSIGHT_SAMPLING = "Chuẩn hóa 16.000 Hz đơn kênh (mono), cắt lặng top_db = 25, cố định 48.000 mẫu / 3 giây."
INSIGHT_PARAMS = "Chỉ huấn luyện {trainable} / {total} tham số ({ratio}%): LoRA q_proj, v_proj + Temporal Attention Pooling + head."
DRAWER_META = "Thời lượng: {duration} • 16 kHz mono"
DRAWER_PICK = "Chọn một dòng trong bảng để xem chi tiết."
ADMIN_SELECT_HINT = "Chọn một dòng trong bảng, rồi dùng nút thao tác bên dưới."
MSG_ADMIN_NOT_IMPLEMENTED = "Thao tác này chưa được cài đặt ({detail})."
MSG_NO_SELECTION = "Vui lòng chọn một dòng trong bảng trước."
MSG_DONE = "Đã thực hiện."
SOURCE_METRICS = "Nguồn: assets/metrics/*.json"
