# Toàn bộ chuỗi hiển thị tiếng Việt của giao diện (tên file/biến tiếng Anh, chuỗi tiếng Việt chỉ nằm ở đây).
# Nguồn chuỗi: các file Stitch trong stitch/html; chỗ nào Stitch ghi sai so với báo cáo thì dùng chuỗi theo báo cáo (xem docs/stitch-mapping.md).
from ml.config import EMOTION_NAMES, EMOTION_NAMES_VI

APP_NAME = "EmoVoice"
APP_TAGLINE = "Nhận diện cảm xúc"
APP_DESCRIPTION = "Hệ thống phân tích cảm xúc giọng nói tiếng Việt"
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
FOOTER_NOTE = "© 2026 EmoVoice · Khóa luận tốt nghiệp · Kết quả chỉ mang tính tham khảo"

EMOTION_VI = dict(zip(EMOTION_NAMES, EMOTION_NAMES_VI))

# ---- Điều hướng ----
NAV_GROUP_ANALYSIS = "Tác vụ phân tích"
NAV_GROUP_ACCOUNT = "Cá nhân"
NAV_GROUP_ADMIN = "Quản trị hệ thống"
NAV_ANALYZE = "Phân tích cảm xúc"
NAV_HISTORY = "Lịch sử phân tích"
NAV_ACCOUNT = "Tài khoản của tôi"
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

# ---- Trang công khai: Giới thiệu / Hướng dẫn (chưa có khung Stitch, dựng theo style Stitch) ----
ABOUT_EYEBROW = "Giới thiệu"
ABOUT_TITLE = "EmoVoice nhận diện cảm xúc qua giọng nói"
ABOUT_SUB = (
    "Hệ thống demo của đề tài khóa luận CNTT-KLCN311 (Khoa CNTT, Trường ĐH Công Thương TP.HCM): dùng mô hình Transformer nhẹ "
    "(DistilHuBERT + LoRA) để dự đoán cảm xúc từ giọng nói và giải thích quyết định bằng biểu đồ chú ý."
)
ABOUT_CARDS = [
    ("psychology", "Bài toán", "Nhận diện cảm xúc qua giọng nói (SER) xác định trạng thái cảm xúc của người nói từ âm thanh, có thể ứng dụng trong chăm sóc khách hàng, giáo dục và giải trí."),
    ("memory", "Mô hình", "DistilHuBERT được tinh chỉnh bằng LoRA, kết hợp lớp Temporal Attention Pooling. Mô hình chỉ huấn luyện {ratio} số tham số nhưng vượt rõ các phương pháp truyền thống."),
    ("visibility", "Giải thích (XAI)", "Biểu đồ chú ý theo thời gian cho biết đoạn nào của giọng nói được mô hình quan tâm nhiều hơn khi quyết định, giúp người dùng dễ kiểm chứng kết quả."),
]
ABOUT_EMOTIONS_TITLE = "8 trạng thái cảm xúc nhận diện được"
ABOUT_STATS_TITLE = "Kết quả thực nghiệm"
ABOUT_STATS_SUB = "Đo trên tập kiểm thử độc lập RAVDESS (diễn viên 22–24, 180 mẫu)."
ABOUT_STAT_LABELS = ("Accuracy", "Macro F1", "Tham số huấn luyện", "Độ trễ suy luận")
ABOUT_NOTE = (
    "Lưu ý: mô hình hiện được huấn luyện trên RAVDESS (giọng diễn xuất tiếng Anh). Với giọng nói tự nhiên hoặc tiếng Việt, "
    "kết quả có thể kém chính xác hơn; hỗ trợ tiếng Việt là hướng mở rộng."
)
PUBLIC_CTA = "Đăng nhập để bắt đầu"

GUIDE_EYEBROW = "Hướng dẫn"
GUIDE_TITLE = "Sử dụng EmoVoice trong 3 bước"
GUIDE_SUB = "Chỉ cần một đoạn giọng nói ngắn, hệ thống sẽ tự xử lý và trả về cảm xúc kèm giải thích."
GUIDE_STEPS = [
    ("1", "Tải tệp hoặc thu âm", "Chọn tệp WAV/MP3 hoặc thu âm trực tiếp bằng micro. Thời lượng khuyến nghị 1 – 5 giây, dung lượng tối đa {max_mb} MB."),
    ("2", "Bấm phân tích", "Bấm “Thực hiện phân tích cảm xúc”. Hệ thống tự chuẩn hóa về 16 kHz, cắt khoảng lặng và cố định độ dài 3 giây."),
    ("3", "Xem kết quả", "Nhận cảm xúc dự đoán, độ tin cậy, xác suất của 8 cảm xúc và biểu đồ chú ý. Kết quả được lưu trong lịch sử phân tích của bạn."),
]
GUIDE_TIPS_TITLE = "Mẹo để có kết quả tốt"
GUIDE_TIPS = [
    "Thu âm ở nơi yên tĩnh, hạn chế tiếng ồn nền.",
    "Chỉ một người nói trong đoạn âm thanh.",
    "Nói liền mạch khoảng 1 – 5 giây.",
    "Ưu tiên tệp WAV để giữ chất lượng âm thanh.",
]
GUIDE_FAQ_TITLE = "Câu hỏi thường gặp"
GUIDE_FAQ = [
    ("Độ tin cậy là gì?", "Là xác suất mô hình gán cho cảm xúc được dự đoán (từ 0% đến 100%). Nếu mọi cảm xúc đều dưới 30%, kết quả có thể không chính xác do tín hiệu bị nhiễu."),
    ("Biểu đồ chú ý là gì?", "Biểu đồ cho thấy đoạn nào theo thời gian (0 – 3 giây) được mô hình chú ý nhiều hơn; màu xanh càng đậm thì mô hình chú ý càng nhiều. Đây chỉ là công cụ hỗ trợ tham khảo, không phải lời giải thích đầy đủ."),
    ("Vì sao kết quả có thể sai?", "Mô hình được huấn luyện trên giọng diễn xuất tiếng Anh nên với giọng tự nhiên hoặc tiếng Việt có thể kém hơn. Các cảm xúc gần nhau như Vui vẻ – Ngạc nhiên hoặc Trung tính – Êm đềm – Buồn bã cũng dễ bị nhầm lẫn."),
    ("Dữ liệu của tôi có được lưu không?", "Khi đã đăng nhập, tệp âm thanh và kết quả phân tích được lưu vào lịch sử cá nhân của bạn để xem lại."),
]
LOGIN_HERO_TITLE = "Hiểu cảm xúc qua giọng nói"
LOGIN_HERO_SUB = "Tải tệp hoặc thu âm, nhận kết quả cảm xúc kèm giải thích trực quan."
LOGIN_HERO_POINTS = [
    "8 trạng thái cảm xúc theo ngữ điệu tiếng Việt",
    "Giải thích bằng biểu đồ chú ý thời gian thực (XAI)",
    "Lưu và đối soát lịch sử phân tích âm học",
]
TAB_LOGIN = "Đăng nhập"
TAB_REGISTER = "Đăng ký"
LOGIN_TITLE = "Chào mừng quay lại"
LOGIN_SUB = "Nhập thông tin xác thực để truy cập bảng điều khiển"
REGISTER_TITLE = "Tạo tài khoản mới"
REGISTER_SUB = "Đăng ký để lưu lịch sử phân tích của bạn"
FORGOT_TITLE = "Quên mật khẩu"
FORGOT_SUB_STEP1 = "Nhập email đã đăng ký, hệ thống sẽ gửi mã đặt lại mật khẩu"
FORGOT_SUB_STEP2 = "Nhập mã 6 số vừa được gửi tới email của bạn"
FORGOT_SUB_STEP3 = "Mã đã đúng. Hãy đặt mật khẩu mới cho tài khoản của bạn"
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
FIELD_RESET_CODE_PH = "Nhập mã 6 số trong email"
REMEMBER_ME = "Ghi nhớ đăng nhập"
FORGOT_LINK = "Quên mật khẩu?"
BTN_LOGIN = "Xác nhận đăng nhập"
BTN_REGISTER = "Tạo tài khoản"
BTN_SEND_RESET = "Gửi mã đặt lại"
BTN_RESET = "Đặt lại mật khẩu"
BTN_VERIFY_CODE = "Xác nhận mã"
BTN_BACK_TO_LOGIN = "Quay lại đăng nhập"
NO_ACCOUNT = "Chưa có tài khoản?"
BTN_GOTO_REGISTER = "Đăng ký ngay"
BTN_DEV_USER = "Vào thử (Người dùng)"
BTN_DEV_ADMIN = "Vào thử (Quản trị viên)"
DEV_BYPASS_NOTE = "Chế độ dev: DEV_BYPASS_LOGIN=1 — chỉ để xem giao diện, tắt khi triển khai."
MSG_NOT_IMPLEMENTED = "Chức năng này chưa được cài đặt ({detail})."
MSG_FILL_ALL = "Vui lòng nhập đầy đủ thông tin."
MSG_PASSWORD_MISMATCH = "Mật khẩu nhập lại không khớp."
MSG_RESET_SENT = "Nếu email đã được đăng ký, mã đặt lại đã được gửi vào hộp thư của bạn (kiểm tra cả thư rác). Mã có hiệu lực {minutes} phút."
MSG_RESET_DEMO_CODE = "[Chế độ demo, không an toàn] Mã của bạn: {code}"
MSG_MAIL_NOT_CONFIGURED = "Chức năng gửi email chưa được cấu hình. Vui lòng liên hệ quản trị viên để đặt lại mật khẩu."
MSG_REGISTER_DONE = "Đăng ký thành công. Bạn có thể đăng nhập."
MSG_DB_ERROR = "Không kết nối được cơ sở dữ liệu. Vui lòng thử lại sau."
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
TOAST_DECODE_TITLE = "Không đọc được âm thanh"
TOAST_DECODE_TEXT = "Không giải mã được tệp này. Hãy thử một tệp WAV hoặc MP3 khác."
TOAST_MODEL_TITLE = "Mô hình chưa sẵn sàng"
SAVE_DEMO_TITLE = "Phiên thử nghiệm"
SAVE_DEMO_TEXT = "Kết quả này không được lưu vào lịch sử vì bạn đang dùng tài khoản thử. Hãy đăng nhập tài khoản thật để lưu."
SAVE_FAILED_TITLE = "Chưa lưu được lịch sử"
SAVE_FAILED_TEXT = "Kết quả vẫn hiển thị bình thường nhưng không ghi được vào lịch sử. Hãy kiểm tra kết nối cơ sở dữ liệu."
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
HISTORY_EYEBROW = "Lưu trữ"
TABLE_COL_ACTIONS = "Thao tác"
HISTORY_TABLE_COUNT = "Hiển thị {shown} trên {total} tệp gần nhất"
BTN_VIEW_XAI = "Xem XAI"
HISTORY_TITLE = "Lịch sử phân tích"
HISTORY_SUB = "Tra cứu, đối soát kết quả suy luận và giải thích chú ý (XAI) cho các bản ghi của bạn."
HISTORY_TOTAL = "Tổng bản ghi"
HISTORY_AVG_CONF = "Độ tin cậy TB"
HISTORY_SEARCH_PH = "Tìm kiếm theo tên tệp âm thanh..."
HISTORY_ALL_EMOTIONS = "Tất cả cảm xúc (8 nhãn)"
HISTORY_TIME_CHOICES = ["7 ngày qua", "30 ngày qua", "Tất cả"]
BTN_EXPORT = "Xuất CSV (mở bằng Excel)"
DRAWER_LISTEN_AGAIN = "Nghe lại"
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
MODELS_EYEBROW = "Quản trị • Đánh giá & thực nghiệm"
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
STATUS_LABELS = {"active": "Đang dùng", "ready": "Sẵn sàng", "baseline": "Baseline", "pending": "Chưa đo"}
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
ADMIN_OVERVIEW_EYEBROW = "Quản trị • Chỉ dành cho quản trị viên"
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
    ("Mô hình AI", "{model} đang dùng"),
    ("Cơ sở dữ liệu", "{database} (SQLAlchemy)"),
]
STATUS_OK = "Ổn định"
STATUS_NOT_READY = "Chưa sẵn sàng"
ADMIN_USERS_EYEBROW = "Quản trị • Người dùng"
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
ADMIN_LOGS_EYEBROW = "Quản trị • Nhật ký"
ADMIN_LOGS_TITLE = "Nhật ký hệ thống"
ADMIN_LOGS_SUB = "Sự kiện và lỗi của ứng dụng, mô hình và cơ sở dữ liệu."
LOG_LEVELS = ["Tất cả mức", "INFO", "WARNING", "ERROR"]
LOG_SEARCH_PH = "Tìm trong nội dung nhật ký..."
COL_LEVEL = "Mức"
COL_SERVICE = "Dịch vụ"
COL_MESSAGE = "Nội dung"
COL_USER = "Người dùng"
ADMIN_MODELS_EYEBROW = "Quản trị • Mô hình"
ADMIN_MODELS_TITLE = "Quản lý mô hình AI"
ADMIN_MODELS_SUB = "Xem chỉ số các mô hình và chọn mô hình đang dùng để suy luận."
BTN_SET_ACTIVE_MODEL = "Đặt làm mô hình đang dùng"
ADMIN_AUDIO_EYEBROW = "Quản trị • Dữ liệu"
ADMIN_AUDIO_TITLE = "Quản lý dữ liệu âm thanh"
ADMIN_AUDIO_SUB = "Mẫu âm thanh của mọi người dùng: nghe lại, lọc, tìm kiếm và xóa."
ADMIN_AUDIO_SEARCH_PH = "Tìm theo tên tệp hoặc người dùng..."
BTN_DELETE_AUDIO = "Xóa mẫu đã chọn"
COL_ANALYSES = "Lượt phân tích"
AUDIO_NOT_ANALYZED = "Chưa phân tích"
BTN_CONFIRM_DELETE = "Xác nhận xóa"
BTN_CANCEL_DELETE = "Hủy"
MSG_CONFIRM_DELETE_AUDIO = "Xóa vĩnh viễn mẫu \"{file}\" của {user} cùng {n} lượt phân tích? Tệp âm thanh, ảnh XAI và kết quả sẽ mất hẳn, không hoàn tác được. Bấm \"Xác nhận xóa\" để tiếp tục."
MSG_AUDIO_DELETED = "Đã xóa mẫu \"{file}\" của {user} và {n} lượt phân tích liên quan."
CONFIRM_HINT = "Thao tác này không thể hoàn tác."
SAMPLE_DATA_TAG = "Dữ liệu mẫu"

# ---- Bổ sung: chân biểu đồ, drawer, ghi chú ----
FOOT_DELTA_OTHER = "Chênh lệch với {name}: {delta} điểm %"
FOOT_LATENCY_NOTE = "Độ trễ chỉ so sánh được khi các mô hình đo cùng thiết bị (CPU hoặc GPU)."
MODELS_EMPTY_TITLE = "Chưa có mô hình nào được đăng ký"
MODELS_EMPTY_TEXT = "Chạy python -m ml.register_model --checkpoint <tệp .pt> --activate để nạp mô hình, đánh giá trên tập kiểm thử và ghi số đo vào CSDL."
MODELS_UNAVAILABLE_TITLE = "Chưa đọc được danh mục mô hình"
MSG_MODEL_ACTIVATED = "Đã đặt \"{name}\" làm mô hình đang dùng."
INSIGHT_SAMPLING = "Chuẩn hóa 16.000 Hz đơn kênh (mono), cắt lặng top_db = 25, cố định 48.000 mẫu / 3 giây."
INSIGHT_PARAMS = "Chỉ huấn luyện {trainable} / {total} tham số ({ratio}%): LoRA q_proj, v_proj + Temporal Attention Pooling + head."
DRAWER_META = "Thời lượng: {duration} • 16 kHz mono"
DRAWER_PICK = "Chọn một dòng trong bảng để xem chi tiết."
ADMIN_SELECT_HINT = "Chọn một dòng trong bảng, rồi dùng nút thao tác bên dưới."
MSG_ADMIN_NOT_IMPLEMENTED = "Thao tác này chưa được cài đặt ({detail})."
MSG_NO_SELECTION = "Vui lòng chọn một dòng trong bảng trước."
MSG_DONE = "Đã thực hiện."
BTN_RESET_USER_PASSWORD = "Cấp mật khẩu tạm"
LABEL_ROLE_SELECT = "Vai trò của tài khoản đã chọn"
MSG_ROLE_SAME = "Tài khoản này đã có vai trò đó."
MSG_ROLE_GRANTED = "Đã cấp quyền quản trị cho {name}. Quyền có hiệu lực ngay, người đó có thể cần tải lại trang."
MSG_ROLE_REVOKED = "Đã thu hồi quyền quản trị của {name}, tài khoản trở lại vai trò người dùng."
MSG_USER_LOCKED = "Đã khóa tài khoản {name}."
MSG_USER_UNLOCKED = "Đã mở khóa tài khoản {name}."
MSG_TEMP_PASSWORD = "Mật khẩu tạm của {name}: {password}. Hãy chuyển cho người dùng và nhắc họ đổi ở trang Tài khoản của tôi. Mật khẩu này chỉ hiện một lần."
LOG_DATE_PH = "Ngày (năm-tháng-ngày)"
KPI_VS_LAST_WEEK = "so với 7 ngày trước"
KPI_WEEK_COUNT = "{n} lượt trong 7 ngày qua"
KPI_ACCOUNTS_SUB = "Tổng {total} tài khoản, {locked} bị khóa"
ADMIN_NO_ANALYSES_TITLE = "Chưa có lượt phân tích nào"
ADMIN_NO_ANALYSES_TEXT = "Biểu đồ phân bố sẽ xuất hiện khi người dùng bắt đầu phân tích giọng nói."
SOURCE_METRICS = "Nguồn: bảng models trong CSDL"

# ---- Tài khoản của tôi ----
ACCOUNT_EYEBROW = "Cá nhân"
ACCOUNT_TITLE = "Tài khoản của tôi"
ACCOUNT_SUB = "Cập nhật thông tin cá nhân và mật khẩu đăng nhập của bạn."
ACCOUNT_PROFILE_TITLE = "Thông tin cá nhân"
ACCOUNT_PROFILE_SUB = "Họ tên hiển thị ở góc phải đầu trang. Tên đăng nhập và vai trò không đổi được."
ACCOUNT_PASSWORD_TITLE = "Đổi mật khẩu"
ACCOUNT_PASSWORD_SUB = "Nhập mật khẩu hiện tại, sau đó đặt mật khẩu mới (ít nhất 8 ký tự)."
ACCOUNT_SUMMARY_TITLE = "Hồ sơ"
ACCOUNT_FULL_NAME = "Họ và tên"
ACCOUNT_FULL_NAME_PH = "Nguyễn Văn A"
ACCOUNT_CURRENT_PASSWORD = "Mật khẩu hiện tại"
ACCOUNT_JOINED = "Tham gia"
ACCOUNT_JOINED_DEMO = "Tài khoản thử nghiệm"
ACCOUNT_DEMO_NOTE = "Đây là tài khoản thử nghiệm: thay đổi chỉ áp dụng trong phiên đăng nhập này."
BTN_SAVE_PROFILE = "Lưu thay đổi"
BTN_CHANGE_PASSWORD = "Cập nhật mật khẩu"
MSG_PROFILE_SAVED = "Đã lưu thông tin cá nhân."
MSG_PASSWORD_CHANGED = "Đã đổi mật khẩu."
