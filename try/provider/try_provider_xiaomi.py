import sys
import os

sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from rich import print

from pathlib import Path
from speech_synth_engine.providers.xiaomi_provider import XiaomiTTSProvider
from speech_synth_engine.schemas.provider import ReplicatedVoiceConfig
from speech_synth_engine.schemas.generation import VoiceCloningConfig
from datetime import datetime

# Initialize provider
provider = XiaomiTTSProvider(name="xiaomi")

# Voice cloning with auto-transcribed reference_text
voice_cfg = ReplicatedVoiceConfig(
    reference_audio="/media/nampv1/hdd/data/VoiceGarden/vbee/refined1/hue_female_huonggiang_news_48k_cs-thg.mp3",
    # reference_audio = "/media/nampv1/hdd/data/VoiceGarden/vbee/original/sg_female_tuongvy_call_44k-fhg.mp3",
    reference_text="Chào mừng đến với website của chúng tôi. Đây là trang web cung cấp một giải pháp chuyển văn bản thành giọng nói. Trên cơ sở đó, nó hỗ trợ các doanh nghiệp xây dựng hệ thống trung tâm cuộc gọi tự động, hệ thống thông báo công khai, trợ lý ảo, tin tức âm thanh, podcast, sách âm thanh và tường thuật phim.",  # Will be auto-transcribed
    language="vi"
)

cloning_cfg = VoiceCloningConfig(
    model="OmniVoice",
    voice_config=voice_cfg
)

text = "Chia sẻ tại hội thảo, Tiến sĩ Trần Việt Hùng đã mang đến góc nhìn toàn diện và thực tiễn về sự phát triển vượt bậc của AI trong thời gian gần đây. Ông nhấn mạnh rằng AI không còn là công cụ hỗ trợ đơn thuần mà đang dần trở thành một đồng nghiệp số, có khả năng đảm nhận nhiều công việc trí tuệ với tốc độ và quy mô vượt trội. Từ kinh nghiệm thực tiễn, việc ứng dụng AI vào toàn bộ quy trình làm việc đã giúp rút ngắn đáng kể thời gian xử lý, nâng cao năng suất và hiệu quả vận hành."

# text = "Tiến sĩ Trần Việt Hùng là chuyên gia công nghệ người Việt đang làm việc tại Thung lũng Silicon, đồng thời là nhà sáng lập AI for Vietnam Foundation – tổ chức phi lợi nhuận hoạt động theo luật Hoa Kỳ, quy tụ các chuyên gia AI hàng đầu thế giới nhằm thúc đẩy ứng dụng trí tuệ nhân tạo tại Việt Nam. Việc kết nối và mời được các chuyên gia tầm cỡ quốc tế tham gia chia sẻ đã góp phần lan tỏa mạnh mẽ tri thức công nghệ, mang đến những góc nhìn thực tiễn và hiện đại cho quá trình chuyển đổi của Bưu điện Việt Nam."
# text = "Cuộc thi chạy đường dài không chỉ là thử thách về tốc độ mà còn là hành trình bứt phá giới hạn bản thân. Mỗi bước chạy là một nỗ lực, mỗi nhịp thở là một quyết tâm. Trên chặng đường âý, người tham gia học cách kiên trì, giữ vững tinh thần và tiến lên. Họ hướng tới vạch đích với khát khao chiến thắng và niềm hứng khởi khi vượt qua chính mình."

text = "Ông nhấn mạnh mục tiêu dài hạn là sớm đưa mô hình vào vận hành thương mại, từ đó nhân rộng trên toàn địa bàn Hà Nội và các tỉnh, thành phố khác. Theo đánh giá của Bưu điện Việt Nam, lĩnh vực y tế là một trong những lĩnh vực có hiệu quả ứng dụng UAV cao nhất, do yêu cầu khắt khe về thời gian và chất lượng vận chuyển. Từ thực tiễn nghiên cứu và triển khai, ông Nguyễn Trường Giang cũng cho rằng logistics tầm thấp không chỉ phục vụ y tế mà còn có tiềm năng lớn trong nông nghiệp, đặc biệt tại các khu vực miền núi, nơi UAV có thể giúp gia tăng đáng kể năng lực vận chuyển và sản xuất."

text = "Tôi có 25 quyển sách. Kết quả là 3.14. Đây là lần thứ 2 tôi đến đây. Nhiệt độ từ 20-30 độ. Số tài khoản là 123456789. Sự kiện diễn ra năm 2024. Sinh nhật tôi là 01-05-2000. Hẹn gặp lúc 7h45. Tôi nghỉ vào chủ nhật. Doanh thu quý II tăng mạnh. Quãng đường dài 10km. Tốc độ đạt 60 km/h. Nhiệt độ là 30°C."

# text = "Tôi có hai mươi lăm quyển sách. Kết quả là ba phẩy mười bốn. Đây là lần thứ hai tôi đến đây. Nhiệt độ từ hai mươi đến ba mươi độ. Số tài khoản là một hai ba bốn năm sáu bảy tám chín. Sự kiện diễn ra năm hai nghìn không trăm hai mươi bốn. Sinh nhật tôi là ngày một tháng năm năm hai nghìn. Hẹn gặp lúc bảy giờ bốn mươi lăm. Tôi nghỉ vào chủ nhật. Doanh thu quý hai tăng mạnh. Quãng đường dài mười ki lô mét. Tốc độ đạt sáu mươi ki lô mét trên giờ. Nhiệt độ là ba mươi độ C."

# text = "Tôi có hai mươi lăm quyển sách. Kết quả là ba phẩy mười bốn. Đây là lần thứ hai tôi đến đây. Nhiệt độ từ hai mươi đến ba mươi độ."

# text = "Kết quả là ba phẩy mười bốn"

# text = "phẩy"

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
text_in_filename = "_".join(text[:50].split())

result = provider.clone_with_metadata(
    text=text,
    output_file=f"/home/nampv1/projects/tts/speech-synth-engine/try/output/wavs/try_xiaomi_{text_in_filename}_{current_time}.wav",
    voice_cloning_config=cloning_cfg
)
print("Result:")
print(result)
