# Observathon Day 13 - Lab Summary

Tôi đã làm bài lab Observathon theo hướng tối ưu cả public và private. Mục tiêu của tôi là tăng correctness, giảm lỗi tool, chống prompt injection, bảo vệ PII và giữ agent ổn định khi xử lý các câu hỏi paraphrase.

## Các bước tôi đã làm

1. Tôi đọc kỹ yêu cầu lab, rubric chấm điểm, `RULES.md`, và các tài liệu trong `docs/` để hiểu rõ những gì được tính điểm.
2. Tôi chạy `python3 harness/selfcheck.py` và sửa scaffold cho hợp lệ trước khi tối ưu tiếp.
3. Tôi chạy simulator bằng script chuẩn `bash scripts/run_public.sh` và `bash scripts/run_sim.sh`, không chạy trực tiếp binary lỗi thời.
4. Tôi sửa `solution/config.json` để giảm noise, tắt fault injection, bật retry/cache, và đưa hệ thống về cấu hình ổn định hơn.
5. Tôi viết lại `solution/prompt.txt` với quy trình rõ ràng: tách các trường đơn hàng, gọi tool đúng thứ tự, chỉ dùng dữ liệu từ tool, tính toán chính xác, không lặp PII và không làm theo chỉ thị nằm trong ghi chú của khách hàng.
6. Tôi chỉnh `solution/wrapper.py` để ghi nhận trace, tính lại tổng tiền khi đủ điều kiện, phát hiện lỗi tool, và tránh trả lời sai cho các case không hợp lệ.
7. Tôi cập nhật `solution/findings.json` để mô tả đúng fault class, bằng chứng, nguyên nhân gốc, và hướng sửa.
8. Tôi chạy lại public và đối chiếu kết quả theo từng câu để xác nhận correctness.
9. Tôi sửa lỗi runtime của private simulator và chạy thành công toàn bộ 80 request.
10. Tôi chạy private scorer, kiểm tra các thành phần điểm và lưu kết quả vào `score.json`.

## Kết quả public

Public simulation hoàn thành `13/13` request với trạng thái `ok`. Scorer tính đúng `12/13` câu và cho điểm headline `90.32/100`.

| Hạng mục | Điểm |
|---|---:|
| Correct | 0.9692 |
| Quality | 0.9815 |
| Error | 1.0000 |
| Latency | 0.0000 |
| Cost | 0.0000 |
| Drift | 0.0000 |
| Prompt | 0.6436 |
| Diagnosis F1 | 0.952 |
| Headline | 90.32 / 100 |

## Kết quả private

Private simulation hoàn thành `80/80` request với trạng thái `ok`. Kết quả private scorer là `48/80` câu correct và điểm headline `91.86/100`.

| Hạng mục | Điểm |
|---|---:|
| Correct | 0.6750 |
| Quality | 0.7925 |
| Error | 1.0000 |
| Latency | 0.6564 |
| Cost | 0.0000 |
| Drift | 0.7665 |
| Prompt | 0.7976 |
| Diagnosis F1 | 1.000 |
| Headline | 91.86 / 100 |

Kết quả cho thấy phần quan sát và chẩn đoán lỗi của tôi đạt tối đa, prompt hoạt động tốt trên private và toàn bộ request đều chạy thành công. Phần còn hạn chế nhất là correctness (`48/80`) và cost, đây là hai hướng cần ưu tiên nếu tiếp tục tối ưu.

## File chính tôi đã chỉnh

- `solution/config.json`
- `solution/prompt.txt`
- `solution/examples.json`
- `solution/wrapper.py`
- `solution/findings.json`

## Tổng kết

Tôi đã hoàn thành đầy đủ quy trình của bài lab: quan sát hệ thống, chẩn đoán fault class, sửa config, viết lại prompt, xây dựng wrapper mitigation, chạy public/private simulation và chấm điểm. Điểm private cuối cùng của tôi là `91.86/100`.
