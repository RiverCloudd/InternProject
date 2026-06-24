from __future__ import annotations

import os
import re

from .config import Settings


class BaseLLMClient:
    provider_name = "base"

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    provider_name = "mock"

    def generate(self, prompt: str) -> str:
        user_message = self._extract_user_message(prompt)
        agent_id = self._extract_agent_id(prompt)
        return self._generate_deep_english(user_message, agent_id)

    def _extract_user_message(self, prompt: str) -> str:
        matches = re.findall(r"user_message:\s*['\"]?(.*?)['\"]?\s*(?:\n|$)", prompt)
        return matches[-1].strip() if matches else ""

    def _extract_agent_id(self, prompt: str) -> str:
        match = re.search(r"persona_id:\s*([a-z0-9_]+)", prompt)
        return match.group(1) if match else ""

    def _looks_vietnamese(self, text: str) -> bool:
        normalized = text.lower()
        vietnamese_markers = "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
        common_words = [
            "tôi",
            "mình",
            "tao",
            "cần",
            "can",
            "làm",
            "lam",
            "dự án",
            "du an",
            "truyền thông",
            "truyen thong",
            "giáo dục",
            "giao duc",
            "cho",
            "về",
            "ve",
        ]
        return any(char in normalized for char in vietnamese_markers) or any(word in normalized for word in common_words)

    def _generate_vietnamese(self, user_message: str, agent_id: str) -> str:
        if agent_id == "gucci_group_boss":
            return (
                "Mình sẽ chia việc cho team như sau:\n\n"
                "- CEO: xác định mục tiêu chiến lược của dự án giáo dục, nhóm đối tượng chính, và thông điệp cốt lõi.\n"
                "- CHRO: nếu dự án có yếu tố đào tạo/nâng cao năng lực, thiết kế hành trình học, hành vi cần thay đổi, và chỉ số đánh giá.\n"
                "- Regional Comms: xây kế hoạch truyền thông: kênh, lịch đăng, thông điệp theo từng nhóm người học, và cơ chế nhận phản hồi.\n\n"
                "Bước tiếp theo: cho mình biết dự án này nhắm tới học sinh, phụ huynh, giáo viên, hay cộng đồng rộng hơn; mình sẽ giúp bạn dựng brief 1 trang."
            )

        if agent_id == "regional_comms_manager" or any(
            term in user_message.lower() for term in ["truyền thông", "truyen thong", "campaign", "kênh", "kenh"]
        ):
            return (
                "Với dự án truyền thông về giáo dục, bạn nên bắt đầu bằng một brief rất rõ:\n\n"
                "1. Mục tiêu: nâng nhận thức, tuyển người tham gia, thay đổi hành vi, hay kêu gọi tài trợ?\n"
                "2. Đối tượng: học sinh, phụ huynh, giáo viên, nhà trường, hay cộng đồng?\n"
                "3. Thông điệp chính: một câu ngắn nói rõ lợi ích giáo dục mà dự án mang lại.\n"
                "4. Kênh triển khai: Facebook/TikTok cho nhận thức, workshop/webinar cho tương tác, email/Zalo cho nhắc lịch.\n"
                "5. Chỉ số đo: số người đăng ký, tỷ lệ tham gia, tương tác nội dung, phản hồi sau chương trình.\n\n"
                "Nếu bạn muốn, bước kế tiếp hợp lý là viết một campaign brief gồm: mục tiêu, audience, key message, timeline 4 tuần, và KPI."
            )

        if agent_id == "gucci_group_ceo":
            return (
                "Ở góc nhìn chiến lược, dự án giáo dục cần trả lời ba câu hỏi trước:\n\n"
                "1. Vấn đề giáo dục nào đáng giải quyết nhất?\n"
                "2. Vì sao tổ chức của bạn có quyền và năng lực để nói về vấn đề đó?\n"
                "3. Sau chiến dịch, người xem cần nghĩ khác hoặc làm khác điều gì?\n\n"
                "Đừng bắt đầu bằng kênh truyền thông. Hãy bắt đầu bằng một lựa chọn chiến lược rõ: audience nào, insight nào, thay đổi nào."
            )

        return (
            "Nếu dự án giáo dục có phần phát triển năng lực, bạn nên thiết kế nó như một hành trình học chứ không chỉ là truyền thông.\n\n"
            "Khung tối thiểu gồm: năng lực cần cải thiện, hành vi quan sát được, hoạt động học, người hỗ trợ, và cách đo tiến bộ. "
            "Hãy chọn một nhóm người học cụ thể trước, rồi mới viết nội dung truyền thông."
        )

    def _generate_english(self, user_message: str, agent_id: str) -> str:
        if agent_id == "gucci_group_boss":
            return (
                "I would split this across the team: CEO clarifies the strategic objective, CHRO defines the learning or behavior-change goal, "
                "and Regional Comms turns it into an audience-specific communication plan. Start with one target audience and one measurable outcome."
            )
        if agent_id == "regional_comms_manager" or "communication" in user_message.lower():
            return (
                "Build a simple campaign brief: objective, audience, key message, channel mix, timeline, owners, and success metrics. "
                "Then test it with one audience segment before scaling."
            )
        if agent_id == "gucci_group_ceo" or "strategy" in user_message.lower():
            return (
                "Frame the decision around the strategic education problem, the audience that matters most, and the behavior you want to change. "
                "Channels come after that choice."
            )
        return (
            "Start from observable behavior. Define the capability or learning outcome, then design the feedback, coaching, or communication activity around it."
        )

    def _generate_deep_vietnamese(self, user_message: str, agent_id: str) -> str:
        topic = self._infer_topic(user_message)
        if agent_id == "gucci_group_boss":
            return self._deep_boss_vietnamese(topic)
        if agent_id == "gucci_group_ceo":
            return self._deep_ceo_vietnamese(topic)
        if agent_id == "gucci_group_chro":
            return self._deep_chro_vietnamese(topic)
        return self._deep_comms_vietnamese(topic)

    def _generate_deep_english(self, user_message: str, agent_id: str) -> str:
        topic = self._infer_topic(user_message)
        if agent_id == "gucci_group_boss":
            return (
                f"Here is the deeper team brief for {topic}.\n\n"
                "Strategic read: do not start with channels. First decide the behavior or decision you want the audience to change.\n\n"
                "Team assignments:\n"
                "- CEO: define the strategic problem, the audience priority, and the non-negotiable message.\n"
                "- CHRO: translate the education goal into learning outcomes and observable behavior.\n"
                "- Regional Comms: design the campaign journey, channel mix, timeline, and feedback loop.\n\n"
                "Recommended structure: insight -> promise -> proof -> call to action -> measurement. "
                "Your next step is to pick one audience and one measurable outcome."
            )
        if agent_id == "gucci_group_ceo":
            return (
                f"Strategically, {topic} needs a sharper thesis before any campaign plan.\n\n"
                "Define the problem, the audience whose behavior matters most, why your organization has credibility, "
                "and the tradeoff you are willing to make. A good project is not 'education awareness' in general; "
                "it is one focused change for one audience under real constraints."
            )
        if agent_id == "gucci_group_chro":
            return (
                f"If {topic} includes learning, design it as behavior change, not content delivery.\n\n"
                "Specify the learner segment, the capability gap, the observable behavior, the practice moment, "
                "and the reinforcement loop. Then communication becomes the wrapper around a real learning journey."
            )
        return (
            f"For {topic}, build the campaign around an audience journey.\n\n"
            "1. Diagnosis: what does the audience misunderstand, fear, ignore, or lack confidence to do?\n"
            "2. Message: one promise, one proof point, one action.\n"
            "3. Channels: awareness channel, trust-building channel, conversion channel, reminder channel.\n"
            "4. Timeline: tease, launch, deepen, convert, follow up.\n"
            "5. Metrics: reach, engagement quality, sign-ups, attendance, completion, and post-program feedback.\n\n"
            "The strongest next move is to write a one-page brief before making content."
        )

    def _infer_topic(self, user_message: str) -> str:
        normalized = user_message.lower()
        if any(term in normalized for term in ["giáo dục", "giao duc", "education"]):
            return "an education communication project"
        if any(term in normalized for term in ["360", "feedback", "coaching"]):
            return "a feedback and coaching system"
        if any(term in normalized for term in ["competency", "năng lực", "nang luc"]):
            return "a leadership competency framework"
        return "the current project"

    def _deep_boss_vietnamese(self, topic: str) -> str:
        return (
            f"Nhìn sâu hơn, {topic} không nên được xử lý như một việc 'làm vài bài post'. "
            "Nó cần được thiết kế như một hệ thống thay đổi nhận thức và hành vi.\n\n"
            "1. Chẩn đoán chiến lược\n"
            "- Vấn đề thật là gì: thiếu nhận thức, thiếu niềm tin, thiếu kỹ năng, hay thiếu động lực hành động?\n"
            "- Ai là nhóm quyết định thành công: học sinh, phụ huynh, giáo viên, nhà trường, nhà tài trợ, hay cộng đồng?\n"
            "- Sau chiến dịch, họ cần nghĩ khác hoặc làm khác điều gì?\n\n"
            "2. Phân công team\n"
            "- CEO: chốt mục tiêu, audience ưu tiên, thông điệp không được làm loãng, và tiêu chí thành công.\n"
            "- CHRO: nếu có yếu tố học tập, chuyển mục tiêu giáo dục thành năng lực/hành vi quan sát được.\n"
            "- Regional Comms: biến chiến lược thành hành trình truyền thông theo kênh, thời điểm, nội dung, và phản hồi.\n\n"
            "3. Khung triển khai đề xuất\n"
            "- Insight: người học/người ra quyết định đang vướng điều gì?\n"
            "- Promise: dự án giúp họ tốt hơn ở điểm nào?\n"
            "- Proof: bằng chứng, câu chuyện, người thật, số liệu, hoặc demo nào tạo niềm tin?\n"
            "- Action: họ cần đăng ký, tham gia, chia sẻ, thay đổi thói quen, hay cam kết gì?\n\n"
            "4. KPI nên đo theo tầng\n"
            "- Nhận biết: reach, video completion, traffic.\n"
            "- Quan tâm thật: comment chất lượng, inbox, đăng ký, câu hỏi gửi về.\n"
            "- Hành động: số người tham gia, tỷ lệ hoàn thành, referral.\n"
            "- Tác động: thay đổi hiểu biết/hành vi trước và sau chương trình.\n\n"
            "Câu hỏi quan trọng nhất bây giờ: dự án này muốn thay đổi nhận thức, thay đổi hành vi, hay tuyển người tham gia một chương trình giáo dục cụ thể?"
        )

    def _deep_comms_vietnamese(self, topic: str) -> str:
        return (
            f"Với vai trò truyền thông, mình sẽ thiết kế {topic} theo logic campaign brief trước, content sau.\n\n"
            "1. Audience insight\n"
            "Đừng viết cho 'mọi người'. Hãy chọn một nhóm chính. Ví dụ:\n"
            "- Học sinh: cần thấy nội dung gần gũi, dễ bắt đầu, không bị giảng đạo.\n"
            "- Phụ huynh: cần thấy lợi ích, độ tin cậy, an toàn, và kết quả.\n"
            "- Giáo viên/nhà trường: cần thấy tính ứng dụng, giảm tải, và phù hợp chương trình.\n\n"
            "2. Message architecture\n"
            "- Key message: một câu nói rõ dự án giúp ai đạt điều gì.\n"
            "- Supporting messages: 3 ý phụ, mỗi ý trả lời một nỗi lo của audience.\n"
            "- Proof: câu chuyện thật, số liệu, chuyên gia, demo lớp học, hoặc phản hồi người tham gia.\n"
            "- CTA: đăng ký, tham gia buổi giới thiệu, tải tài liệu, hoặc làm bài đánh giá ngắn.\n\n"
            "3. Channel mix\n"
            "- TikTok/Reels: tạo nhận biết bằng tình huống giáo dục đời thường.\n"
            "- Facebook/Zalo group: xây niềm tin với phụ huynh/cộng đồng.\n"
            "- Workshop/webinar: chuyển người quan tâm thành người tham gia.\n"
            "- Email/Zalo OA: nhắc lịch, follow-up, gửi tài liệu.\n\n"
            "4. Timeline 4 tuần\n"
            "- Tuần 1: problem awareness, kể chuyện về vấn đề.\n"
            "- Tuần 2: solution proof, giới thiệu cách dự án giải quyết vấn đề.\n"
            "- Tuần 3: conversion, đẩy đăng ký/tham gia.\n"
            "- Tuần 4: community loop, chia sẻ kết quả sớm và feedback.\n\n"
            "5. Rủi ro cần tránh\n"
            "- Thông điệp quá đạo đức hóa, khiến audience thấy bị phán xét.\n"
            "- Quá nhiều kênh nhưng không có một CTA rõ.\n"
            "- Đo vanity metrics mà không đo hành động thật.\n\n"
            "Bước tiếp theo: viết cho mình 3 thông tin: audience chính, mục tiêu chiến dịch, và dự án giáo dục này giải quyết vấn đề gì."
        )

    def _deep_ceo_vietnamese(self, topic: str) -> str:
        return (
            f"Ở góc nhìn chiến lược, {topic} cần một lựa chọn sắc bén: bạn không thể vừa nói với mọi người, vừa giải quyết mọi vấn đề.\n\n"
            "1. Strategic choice\n"
            "- Chọn một vấn đề giáo dục đáng giải quyết nhất.\n"
            "- Chọn một nhóm audience có khả năng tạo tác động lớn nhất.\n"
            "- Chọn một kết quả kinh doanh/xã hội có thể đo được.\n\n"
            "2. Positioning\n"
            "Dự án cần trả lời: vì sao người ta phải tin bạn? Nếu chưa có uy tín, hãy mượn uy tín từ đối tác, chuyên gia, dữ liệu, hoặc câu chuyện người dùng thật.\n\n"
            "3. Tradeoff\n"
            "Nếu ngân sách/thời gian hạn chế, ưu tiên chiều sâu thay vì phủ rộng: một nhóm audience, một thông điệp, một hành động rõ, một chỉ số tác động.\n\n"
            "CEO decision cần chốt: chiến dịch này ưu tiên awareness, participation, hay measurable learning impact?"
        )

    def _deep_chro_vietnamese(self, topic: str) -> str:
        return (
            f"Nếu {topic} có mục tiêu giáo dục thật, hãy thiết kế nó như một hành trình phát triển năng lực, không chỉ là truyền thông.\n\n"
            "1. Learning outcome\n"
            "Người tham gia sau dự án phải biết gì, tin gì, hoặc làm được gì tốt hơn?\n\n"
            "2. Behavior design\n"
            "Chuyển mục tiêu thành hành vi quan sát được. Ví dụ: không nói 'nâng cao nhận thức', mà nói 'phụ huynh biết chọn 3 tiêu chí đánh giá một chương trình học'.\n\n"
            "3. Reinforcement\n"
            "Truyền thông chỉ kéo người học vào. Tác động đến từ hoạt động sau đó: workshop, tài liệu thực hành, checklist, mentoring, cộng đồng, hoặc feedback.\n\n"
            "4. Measurement\n"
            "Đo trước-sau: mức hiểu biết, mức tự tin, hành vi thử nghiệm, tỷ lệ hoàn thành, và phản hồi định tính.\n\n"
            "Câu hỏi cần trả lời: bạn muốn audience học một kiến thức, thay đổi thái độ, hay hình thành một hành vi mới?"
        )


class GeminiLLMClient(BaseLLMClient):
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError("google-genai is not installed. Run: pip install -r requirements.txt") from error

        os.environ["GEMINI_API_KEY"] = self.api_key
        client = genai.Client(api_key=self.api_key)

        # Current Gemini quickstart recommends the Interactions API. Keep a fallback
        # for SDK versions that still expose generate_content first.
        if hasattr(client, "interactions"):
            interaction = client.interactions.create(model=self.model, input=prompt)
            return getattr(interaction, "output_text", str(interaction))

        response = client.models.generate_content(model=self.model, contents=prompt)
        return getattr(response, "text", str(response))


def create_llm_client(settings: Settings) -> BaseLLMClient:
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key or "PASTE_YOUR" in settings.gemini_api_key:
            return MockLLMClient()
        return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    return MockLLMClient()
