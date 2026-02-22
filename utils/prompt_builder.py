import json
from datetime import datetime

def build_weekly_prompt(df, patterns):
    """Tạo AI prompt từ data tuần"""
    
    if len(df) == 0:
        return "Chưa có dữ liệu để tạo prompt"
    
    avg_energy = df['energy_level'].mean()
    df['task_count'] = df['tasks'].apply(lambda x: len(json.loads(x)))
    avg_tasks = df['task_count'].mean()
    
    worst_day = df.loc[df['energy_level'].idxmin()]
    best_day = df.loc[df['energy_level'].idxmax()]
    
    prompt = f"""# BỐI CẢNH TUẦN VỪA QUA

Tôi đã theo dõi trạng thái tinh thần và năng lượng trong {len(df)} ngày. Dưới đây là dữ liệu chi tiết:

## DỮ LIỆU TỔNG QUAN
- Năng lượng trung bình: {avg_energy:.1f}/10
- Số công việc trung bình mỗi ngày: {avg_tasks:.1f} việc
- Ngày tốt nhất: {best_day['date']} ({best_day['energy_level']}/10)
- Ngày tệ nhất: {worst_day['date']} ({worst_day['energy_level']}/10)

## CHI TIẾT TỪNG NGÀY
"""
    
    for _, row in df.iterrows():
        tasks = json.loads(row['tasks'])
        prompt += f"""
### {row['date']}
- Trạng thái tinh thần: {row['mental_load']}
- Năng lượng: {row['energy_level']}/10
- Nguồn áp lực: {row['pressure_source']}
- Giấc ngủ: {'⭐' * row['sleep_quality']}
- Số công việc: {len(tasks)} việc
- Cảm giác khi nhìn danh sách: {row['task_feeling']}
"""
    
    prompt += "\n## CÁC XU HƯỚNG PHÁT HIỆN\n"
    for i, pattern in enumerate(patterns, 1):
        clean = pattern.replace('⚠️','').replace('📋','').replace('😴','').replace('🔋','').replace('✅','').strip()
        prompt += f"{i}. {clean}\n"
    
    prompt += """
---

Dựa trên dữ liệu này, hãy:

1. **Xác định nguyên nhân** gây sụt giảm năng lượng hoặc các xu hướng tiêu cực
2. **Đưa ra 3 giải pháp cụ thể** (thay đổi nhỏ, dễ thực hiện) cho tuần sau
3. **Tập trung vào hành động thực tế**, không nói chung chung

Ví dụ giải pháp tốt:
- "Dời công việc A từ Thứ 4 sang Thứ 3 vì Thứ 4 năng lượng thường thấp"
- "Chuẩn bị đồ tối hôm trước để sáng hôm sau không mất thời gian"
- "Chặn 30 phút nghỉ ngơi sau mỗi buổi học dày đặc"

Hãy đưa ra giải pháp dựa trên XU HƯỚNG CỤ THỂ trong dữ liệu của tôi.
"""
    return prompt


def build_daily_framework_prompt_with_schedule(date, data, framework_name):
    """
    Tạo prompt hàng ngày kết hợp lịch cố định và framework khoa học.
    """

    tasks      = data.get('tasks', [])
    tasks_meta = data.get('tasks_meta', [])
    fixed_schedule = data.get('fixed_schedule', [])
    energy     = data.get('energy_level', 5)

    # Tính tổng thời gian công việc — dùng "or 0" để tránh None từ Supabase
    total_minutes = sum((t.get('estimated_time') or 0) for t in tasks_meta)
    total_h = total_minutes // 60
    total_m = total_minutes % 60

    # Tính thời gian bận từ lịch cố định
    busy_minutes = 0
    for s in fixed_schedule:
        try:
            start_key = 'start_time' if 'start_time' in s else 'start'
            end_key   = 'end_time'   if 'end_time'   in s else 'end'
            start = datetime.strptime(s[start_key], "%H:%M")
            end   = datetime.strptime(s[end_key],   "%H:%M")
            busy_minutes += int((end - start).total_seconds() / 60)
        except Exception:
            pass

    # ── Kho framework ──────────────────────────────────────────────
    frameworks = {
        "Thứ 2": {
            "name": "Xem lại tổng thể (GTD)",
            "guide": """
Hôm nay là Thứ Hai — chế độ ĐÁNH GIÁ TOÀN CẢNH.

Nguồn gốc khoa học: David Allen — Getting Things Done (2001)

Thay vì lao vào làm việc ngay, hãy nhìn bức tranh toàn cảnh trước:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Những công việc nào liên quan đến nhau? (nên làm liền nhau)
2. Việc nào BẮT BUỘC hôm nay? Việc nào có thể dời?
3. Điểm tắc nghẽn là gì? (lịch cố định, thời gian hạn chế...)
4. Nếu chỉ làm được 2 việc hôm nay, 2 việc nào ảnh hưởng lớn nhất?

Hãy phân tích theo 4 câu hỏi trên rồi xếp lịch cụ thể.
"""
        },
        "Thứ 3": {
            "name": "Ma trận ưu tiên (Eisenhower)",
            "guide": """
Hôm nay là Thứ Ba — chế độ SẮP XẾP ƯU TIÊN.

Nguồn gốc khoa học: Nguyên tắc Eisenhower — phổ biến bởi Stephen Covey trong "7 Thói quen"

Áp dụng ma trận 4 ô:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Việc nào VỪA GẤP VỪA QUAN TRỌNG? → Làm NGAY sáng nay
2. Việc nào "cảm giác gấp" nhưng thực ra không quan trọng? → Loại bỏ hoặc nhờ người khác
3. Việc nào quan trọng nhưng chưa gấp? → Lên lịch cụ thể, đừng để quên
4. Việc nào không gấp không quan trọng? → Bỏ hẳn

Phân loại từng công việc trong danh sách vào 4 ô này.
"""
        },
        "Thứ 4": {
            "name": "Quản lý chu kỳ năng lượng (Ultradian)",
            "guide": """
Hôm nay là Thứ Tư — chế độ PHÂN BỔ THEO NĂNG LƯỢNG.

Nguồn gốc khoa học: Peretz Lavie & Nathaniel Kleitman — Chu kỳ hoạt động não bộ 90 phút

Não hoạt động theo chu kỳ 90 phút tập trung → 20 phút cần nghỉ. Thứ 4 thường là ngày năng lượng xuống thấp nhất trong tuần:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Việc nào đòi hỏi tập trung cao nhất? → Xếp vào sáng sớm (9-11h)
2. Việc nào có thể làm khi mệt? → Xếp vào chiều hoặc tối
3. Cần nghỉ ở đâu trong ngày? → Mỗi 90 phút nghỉ 10-15 phút
4. Lịch cố định nằm vào lúc nào? → Tránh xếp việc khó ngay sau đó

Sắp xếp lại danh sách theo đúng chu kỳ năng lượng.
"""
        },
        "Thứ 5": {
            "name": "Bớt tải nhận thức (Delegation)",
            "guide": """
Hôm nay là Thứ Năm — chế độ GIẢM TẢI CÔNG VIỆC.

Nguồn gốc khoa học: Lý thuyết tải nhận thức — Sweller (1988)

Não chỉ xử lý hiệu quả 4±1 việc cùng lúc. Không nhất thiết phải tự làm hết:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Việc nào có thể nhờ người khác làm thay? → Nhờ bạn, nhờ thầy cô, nhờ AI
2. Việc nào cần xin trợ giúp thêm? → Đừng cố tự làm nếu mất quá nhiều thời gian
3. Việc nào làm chung sẽ hiệu quả hơn?
4. Việc nào có thể xin gia hạn thêm thời gian?

Mục tiêu: Giảm danh sách xuống còn phần CỐT LÕI thật sự cần bạn làm.
"""
        },
        "Thứ 6": {
            "name": "Nhìn lại để học hỏi (Reflection)",
            "guide": """
Hôm nay là Thứ Sáu — chế độ NHÌN LẠI TUẦN.

Nguồn gốc khoa học: Chu trình học qua trải nghiệm — David Kolb

Học hỏi thật sự xảy ra khi bạn nhìn lại, không chỉ khi trải nghiệm:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Việc gì làm tốt nhất tuần này? → Tiếp tục làm
2. Việc gì gây mệt mỏi hoặc căng thẳng nhất? → Cần dừng hoặc thay đổi
3. Nếu làm lại tuần này, tôi sẽ thay đổi gì?
4. Xu hướng nào lặp lại nhiều lần? → Đây là điều quan trọng cần thay đổi

Rút ra 2-3 bài học cụ thể cho tuần sau.
"""
        },
        "Thứ 7": {
            "name": "Lập kế hoạch dự phòng (If-Then)",
            "guide": f"""
Hôm nay là Thứ Bảy — chế độ LÀM VIỆC THÔNG MINH + CHUẨN BỊ TUẦN SAU.

Nguồn gốc khoa học: Kế hoạch thực thi — Peter Gollwitzer (NYU, 1999)
Nghiên cứu chứng minh: người có quy tắc "nếu... thì..." hoàn thành mục tiêu cao hơn 300%.

Thứ 7 có hai mục tiêu song song:
① Hoàn thành công việc HÔM NAY trong thời gian rảnh thực tế
② Lập quy tắc tự động để tuần sau não không cần "quyết định" nữa

────────────────────────────────────────
BƯỚC 1 — XẾP LỊCH HÔM NAY (ưu tiên trước)
────────────────────────────────────────
Dựa trên lịch cố định và {total_h} giờ {total_m} phút công việc cần làm:

→ Tìm khoảng trống thực tế trước/sau/giữa các lịch cố định
→ "Học sâu" → xếp vào buổi sáng hoặc đầu chiều (khi não còn tỉnh)
→ "Công việc nhẹ" → xếp sau 15 giờ hoặc buổi tối
→ Chèn nghỉ 15 phút sau mỗi 90 phút làm việc liên tục
→ Nếu không đủ thời gian: nói rõ việc nào nên dời sang Chủ nhật

────────────────────────────────────────
BƯỚC 2 — LẬP QUY TẮC DỰ PHÒNG CHO TUẦN SAU
────────────────────────────────────────
Sau khi xếp xong lịch hôm nay, trả lời thêm:

1. Tuần sau có bài nộp hoặc sự kiện quan trọng nào không? → Cần chuẩn bị từ đầu tuần
2. Ngày nào tuần sau có thể bận bất ngờ? → Đặt thời gian dự phòng ngay bây giờ
3. Nhìn vào công việc hôm nay: việc nào nên làm sớm hơn ở tuần sau?
4. Lập 2-3 quy tắc dạng "nếu... thì..." dựa trên ĐÚNG những công việc trong danh sách:
   - "Nếu [tình huống xảy ra] → tôi sẽ [làm gì ngay]"
   - Ví dụ: "Nếu Thứ 3 có thêm lịch học kèm → tôi dời luyện viết sang tối Thứ 2"
   - Ví dụ: "Nếu mệt sau 14 giờ → tôi làm luyện nói thay vì toán"
""",
        },
        "Chủ nhật": {
            "name": "Phục hồi có chủ đích (Active Recovery)",
            "guide": """
Hôm nay là Chủ Nhật — chế độ PHỤC HỒI CÓ CHỦ ĐÍCH.

Nguồn gốc khoa học: Lý thuyết phục hồi — Kellmann (2010)

Nghỉ ngơi thụ động (xem điện thoại, nằm lướt mạng) KHÔNG giúp não phục hồi. Cần nghỉ ngơi chủ động:

CÁC CÂU HỎI CẦN TRẢ LỜI:
1. Hoạt động nào khiến tôi thực sự "nạp lại năng lượng"? → Làm nhiều hơn
2. Hoạt động nào chỉ "giết thời gian" mà không phục hồi? → Làm ít lại
3. Cần tách biệt khỏi gì để não thực sự nghỉ?
4. Hoạt động phục hồi nào phù hợp với năng lượng hiện tại?

Gợi ý phục hồi tốt: đi bộ, đọc sách nhẹ, nấu ăn, gặp bạn bè, vẽ, nghe nhạc.
Tránh: lướt mạng xã hội không có mục đích, xem phim liên tục nhiều tiếng.
"""
        }
    }

    # Xác định ngày trong tuần
    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    weekday_vn = {
        "Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4",
        "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7",
        "Sunday": "Chủ nhật"
    }
    current_weekday = weekday_vn.get(weekday, "Thứ 2")
    framework = frameworks.get(current_weekday, frameworks["Thứ 2"])

    # ── Xây dựng prompt ────────────────────────────────────────────
    prompt = f"""# BỐI CẢNH — HỌC SINH CẦN LẬP LỊCH HÔM NAY

## Ngày: {current_weekday}, {date}
Phương pháp hôm nay: **{framework['name']}**

## 1. TRẠNG THÁI HIỆN TẠI
- Năng lượng: {energy}/10
- Trạng thái tinh thần: {data.get('mental_load', 'Chưa có')}

"""

    # Lịch cố định
    if fixed_schedule:
        prompt += "## 2. LỊCH CỐ ĐỊNH (KHÔNG THỂ THAY ĐỔI)\n"
        for s in fixed_schedule:
            # Hỗ trợ cả key từ SQLite (start/end) và Supabase (start_time/end_time)
            start_key = 'start_time' if 'start_time' in s else 'start'
            end_key   = 'end_time'   if 'end_time'   in s else 'end'
            name_key  = 'schedule_name' if 'schedule_name' in s else 'name'
            prompt += f"- {s[start_key]} - {s[end_key]}: {s[name_key]}\n"
        free_est = max(0, 960 - busy_minutes)
        prompt += f"""
**→ Tổng thời gian bận: khoảng {busy_minutes // 60} giờ {busy_minutes % 60} phút**
**→ Thời gian rảnh ước tính còn lại trong ngày: khoảng {free_est // 60} giờ {free_est % 60} phút**
**→ Hãy tìm KHOẢNG TRỐNG thực tế trước/sau/giữa các lịch cố định để xếp công việc!**

"""
    else:
        prompt += "## 2. LỊCH CỐ ĐỊNH\nKhông có lịch cố định hôm nay.\n\n"

    # Công việc
    prompt += f"## 3. CÔNG VIỆC CẦN LÀM (Tổng: {total_h} giờ {total_m} phút)\n"
    if tasks_meta:
        for i, t in enumerate(tasks_meta, 1):
            phut = t.get('estimated_time') or 0
            tg = f"{phut // 60} giờ {phut % 60} phút" if phut >= 60 else f"{phut} phút"
            prompt += f"{i}. {t.get('task_name', '')} (Thời gian: {tg}, Ưu tiên: {t.get('priority', '')}, Loại: {t.get('task_type', '')})\n"
    else:
        for i, t in enumerate(tasks, 1):
            prompt += f"{i}. {t}\n"

    prompt += f"""
---

# YÊU CẦU — TẠO LỊCH THÔNG MINH

{framework['guide']}

## NHIỆM VỤ CỦA BẠN (AI):

**1. PHÂN TÍCH THỜI GIAN TRỐNG:**
"""
    if fixed_schedule:
        prompt += """   - Xác định các khoảng trống cụ thể (giờ bắt đầu - giờ kết thúc)
   - So sánh tổng thời gian trống với tổng thời gian công việc
   - Nếu không đủ thời gian → nói rõ việc nào nên dời sang ngày khác
"""
    else:
        prompt += """   - Cả ngày đều trống, nhưng đừng xếp quá 6-7 tiếng làm việc liên tục
"""

    prompt += f"""
**2. TẠO LỊCH CỤ THỂ THEO GIỜ:**
   - Xếp công việc vào đúng khoảng trống thực tế
   - "Học sâu" → buổi sáng hoặc đầu chiều (não còn tỉnh táo)
   - "Công việc nhẹ" → chiều muộn hoặc tối (khi năng lượng thấp vẫn làm được)
   - Chèn nghỉ 15 phút sau mỗi 90 phút làm việc liên tục
   - Định dạng bắt buộc: HH:MM - HH:MM | Tên công việc

**3. ÁP DỤNG PHƯƠNG PHÁP {framework['name']}:**
   - Phân tích công việc theo đúng phương pháp này
   - Đưa ra nhận xét cụ thể dựa trên danh sách công việc thực tế hôm nay
   - Không nói chung chung — áp dụng thẳng vào hoàn cảnh hôm nay

**4. KIỂM TRA QUÁ TẢI:**
   - Năng lượng hiện tại: {energy}/10
   - Nếu tổng công việc > thời gian trống → đề xuất cắt/dời cái nào trước
   - Nếu năng lượng ≤ 5 → ưu tiên 1-2 việc quan trọng nhất, bỏ việc ưu tiên thấp

---

# KẾT QUẢ TRẢ VỀ (Dùng đúng định dạng này):

```
📅 LỊCH HÔM NAY — {framework['name'].upper()}

⚡ PHÂN TÍCH NHANH:
[Tổng thời gian trống | Tổng công việc | Có quá tải không?]

⚠️ LƯU Ý (nếu có):
[Quá tải, năng lượng thấp, xung đột lịch...]

🕐 LỊCH THEO GIỜ:
HH:MM - HH:MM | 🔒 [Lịch cố định]
HH:MM - HH:MM | 🔴 [Việc ưu tiên cao - Học sâu]
HH:MM - HH:MM | ☕ Nghỉ 15 phút
HH:MM - HH:MM | 🟡 [Việc ưu tiên trung bình]
HH:MM - HH:MM | 🟢 [Công việc nhẹ]
... (tiếp tục đến cuối ngày)

💡 ÁP DỤNG {framework['name'].upper()}:
[Nhận xét + quy tắc dự phòng cụ thể từ công việc thực tế hôm nay]

🎯 VIỆC ƯU TIÊN TUYỆT ĐỐI:
[1-2 việc không thể bỏ nếu thời gian bị cắt]
```
"""
    return prompt


# Tương thích ngược
def build_daily_framework_prompt(date, data, framework_name):
    return build_daily_framework_prompt_with_schedule(date, data, framework_name)