import os
import sys

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
# Suppress noisy INFO logs from external libraries
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("AFC").setLevel(logging.ERROR)
logging.getLogger("AFC").propagate = False
from pathlib import Path
from datetime import datetime
from speech_synth_engine.schemas.provider import ProviderConfig, CredentialsConfig, VoiceConfig, AudioConfig
from speech_synth_engine.schemas.generation import GenerateSpeechConfig
from speech_synth_engine.dataset.dataset_generator import DatasetGenerator

from rich import print

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Test text in Vietnamese
test_text = "Xin chào, đây là test với Gemini TTS provider"
test_texts = [
    ('0108245608_2', 'số sáu mươi sáu, đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội'),
    ('0108235818', 'số ba trăm chín mươi tám đường quảng oai, thị trấn tây đằng, huyện ba vì, thành phố hà nội')
]

# test_texts = [
#     # ('0109720214', 'xóm hai, xã phú phương, huyện ba vì, thành phố hà nội'),
#     # ('0109675882', 'xóm mười, thôn phương khê, xã phú phương, huyện ba vì, thành phố hà nội'),
#     # ('0109543565', 'xóm mười, xã phú phương, huyện ba vì, thành phố hà nội'),
#     # ('0108521223', 'xóm mười, thôn phương khê, xã phú phương, huyện ba vì, thành phố hà nội'),
#     # ('0108165818', 'xóm hai, thôn phương châu, xã phú phương, huyện ba vì, thành phố hà nội'),
#     # ('0107155895', 'phương châu, xã phú phương, huyện ba vì, hà nội'),
#     # ('0106918456', 'phương khê, xã phú phương, huyện ba vì, hà nội'),
#     # ('0106702665', 'thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     # ('0106688805', 'xóm bảy, thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     # ('0106540809', 'thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     ('0106323882', 'xóm sáu, xã phú phương, huyện ba vì, hà nội'),
#     # ('0105972877', 'xóm mười hai, thôn phương khê, xã phú phương, huyện ba vì, hà nội'),
#     # ('0105915251', 'xóm hai, thôn phương châu, xã phú phương, huyện ba vì, hà nội'),
#     # ('0105810587', 'phú phương xã phú phương, huyện ba vì, hà nội'),
#     # ('0105760135', 'xóm tám, xã phú phương, huyện ba vì, hà nội'),
#     # ('0104016244', 'phú phương ba vì xã phú phương, huyện ba vì, hà nội')
# ]


test_texts = [
    # ('tts_001', 'Bản tin sáng ngày 12 tháng 3 năm 2026 cho biết nhiệt độ tại Hà Nội dao động từ 22 đến 28 độ C, độ ẩm khoảng 75 phần trăm và có khả năng mưa nhẹ vào buổi chiều.'),
    # ('tts_002', 'Theo báo cáo công bố ngày 10 tháng 3 năm 2026, GDP quý một ước tính tăng khoảng 6,2 phần trăm so với cùng kỳ năm 2025.'),
    # ('tts_003', 'Giá vàng SJC sáng nay ở mức khoảng 81 triệu đồng một lượng, tăng gần 500 nghìn đồng so với phiên giao dịch ngày hôm qua.'),
    ('tts_004', 'Tính đến ngày 1 tháng 3 năm 2026, Việt Nam đã đón hơn 3,5 triệu lượt khách du lịch quốc tế.'),
    ('tts_005', 'Một tuyến cao tốc dài 120 km với tổng vốn đầu tư hơn 25 nghìn tỷ đồng dự kiến sẽ hoàn thành vào năm 2027.'),
    ('tts_006', 'Theo Bộ Y tế, trong tuần từ ngày 5 đến ngày 11 tháng 3 năm 2026 ghi nhận khoảng 2.300 ca mắc cúm mùa trên toàn quốc.'),
    ('tts_007', 'Giá xăng RON95 trong kỳ điều hành ngày 14 tháng 3 năm 2026 được điều chỉnh tăng thêm 350 đồng mỗi lít.'),
    ('tts_008', 'Một công ty công nghệ vừa công bố mẫu pin mới có dung lượng 5.000 mAh và thời gian sạc đầy chỉ khoảng 30 phút.'),
    # ('tts_009', 'Tại thành phố Hồ Chí Minh, lượng xe lưu thông giờ cao điểm có thể đạt hơn 900 nghìn lượt mỗi ngày.'),
    # ('tts_010', 'Theo dự báo, tốc độ gió trong cơn bão có thể đạt 90 km một giờ khi tiến vào khu vực ven biển miền Trung.'),
    # ('tts_011', 'Trong năm 2025, tổng kim ngạch xuất khẩu của Việt Nam đạt hơn 355 tỷ đô la Mỹ.'),
    # ('tts_012', 'Một nghiên cứu mới cho thấy trung bình mỗi người trưởng thành nên đi bộ khoảng 7.000 đến 10.000 bước mỗi ngày.'),
    # ('tts_013', 'Ngày 20 tháng 3 năm 2026 sẽ diễn ra hội nghị công nghệ với sự tham gia của hơn 1.200 đại biểu.'),
    # ('tts_014', 'Một dự án điện gió công suất 300 MW đang được xây dựng tại khu vực duyên hải miền Trung.'),
    # ('tts_015', 'Theo thống kê mới nhất, tỷ lệ thanh toán không tiền mặt tại Việt Nam đã đạt khoảng 45 phần trăm tổng số giao dịch bán lẻ.'),
    # ('tts_016', 'Trong tháng 2 năm 2026, doanh số bán ô tô trong nước đạt hơn 28.000 chiếc.'),
    # ('tts_017', 'Một chuyến bay từ Hà Nội đến Đà Nẵng thường kéo dài khoảng 1 giờ 20 phút với quãng đường gần 770 km.'),
    # ('tts_018', 'Các nhà khoa học cho biết nhiệt độ trung bình toàn cầu đã tăng khoảng 1,1 độ C so với thời kỳ tiền công nghiệp.'),
    # ('tts_019', 'Một giải chạy marathon dài 42 km sẽ được tổ chức vào ngày 5 tháng 4 năm 2026 với khoảng 8.000 vận động viên tham gia.'),
    # ('tts_020', 'Theo kế hoạch, tuyến metro số 1 dài gần 20 km sẽ phục vụ khoảng 160.000 lượt hành khách mỗi ngày sau khi đi vào hoạt động.'),
    # ('tts_021', 'Giá điện sinh hoạt dự kiến điều chỉnh thêm khoảng 3 phần trăm từ ngày 1 tháng 5 năm 2026.'),
    # ('tts_022', 'Một báo cáo môi trường cho thấy nồng độ bụi mịn PM2.5 tại một số khu vực đô thị có lúc vượt ngưỡng 50 microgam trên mét khối.'),
    # ('tts_023', 'Trong chiến dịch trồng cây năm nay, mục tiêu là trồng mới khoảng 10 triệu cây xanh trên toàn quốc.'),
    # ('tts_024', 'Theo dữ liệu từ ngành du lịch, thời gian lưu trú trung bình của du khách quốc tế tại Việt Nam là khoảng 7,2 ngày.'),
    # ('tts_025', 'Một trung tâm dữ liệu mới có công suất tiêu thụ điện khoảng 30 MW đang được xây dựng tại khu công nghệ cao.'),
    # ('tts_026', 'Ngày 15 tháng 6 năm 2026 dự kiến sẽ diễn ra kỳ thi với hơn 1 triệu thí sinh đăng ký tham gia.'),
    # ('tts_027', 'Theo thống kê, mỗi năm Việt Nam sản xuất khoảng 43 triệu tấn lúa.'),
    # ('tts_028', 'Một chương trình đào tạo kỹ năng số kéo dài 6 tháng sẽ hỗ trợ khoảng 5.000 học viên trên cả nước.'),
    # ('tts_029', 'Tốc độ internet trung bình tại các đô thị lớn hiện đạt khoảng 95 Mbps theo báo cáo công bố tháng 2 năm 2026.'),
    # ('tts_030', 'Dự báo đến năm 2030, tỷ lệ năng lượng tái tạo trong hệ thống điện quốc gia có thể đạt khoảng 30 phần trăm.')


]


# Build GenerationConfig


credentials_cfg = CredentialsConfig(
    api_keys=[
        "AIzaSyBS012-hXDQb_WwNtavE19W6t3LcE5VRVQ", 
        # "AIzaSyA1l0Y1y4Rv6UqsrmOYeH4Dnlo-4LX02xU"
    ],
    # api_keys = ["AIzaSyA1l0Y1y4Rv6UqsrmOYeH4Dnlo-4LX02xU"]
    
)


provider_config = ProviderConfig(
    name="gemini",
    models=["gemini-2.5-flash-preview-tts"],
    default_model="gemini-2.5-flash-preview-tts",
    credentials=credentials_cfg,
)

voice_config = VoiceConfig(voice_id="Zephyr")
audio_config = AudioConfig(channel=1, sample_rate=24000)


generation_config = GenerateSpeechConfig(
    model="gemini-2.5-flash-preview-tts",
    voice_config=voice_config,
    audio_config=audio_config
)

import time
current_time = time.strftime("%Y%m%d_%H%M%S")

# Use DatasetGenerator main flow
output_dir = f"/home/nampv1/projects/tts/speech-synth-engine/try/try_output/data_generator/test_generator_gemini/{current_time}"

generator = DatasetGenerator(
    output_dir=output_dir,
)

# text_items already contains (id, text)
summary = generator.generate_from_configs(
    text_items=test_texts,
    provider_config=provider_config,
    generation_config=generation_config,
    batch_size=5,
    delay_between_requests=1.0,
    continue_on_error=True,
    tts_type="synthesize",
    enable_concurrency=True,
)

# print(summary)

# print("\nBatch Summary:")
# print(f"Total: {summary.total_texts}")
# print(f"Successful: {summary.successful_generations}")
# print(f"Failed: {summary.failed_generations}")
