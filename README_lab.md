# Observathon Day 13 - Lab Summary

Tôi đã làm bài lab Observathon theo hướng tối ưu cả phần chạy public lẫn chuẩn bị cho private. Mục tiêu của tôi là giữ correctness ổn định, giảm lỗi tool, chống injection, và viết lại prompt sao cho agent trả lời đúng hơn với ít chi phí hơn.

## Các bước tôi đã làm

1. Tôi đọc kỹ yêu cầu lab, rubric chấm điểm, `RULES.md`, và các tài liệu trong `docs/` để hiểu rõ những gì được tính điểm.
2. Tôi chạy `python3 harness/selfcheck.py` và sửa scaffold cho hợp lệ trước khi tối ưu tiếp.
3. Tôi chạy simulator bằng script chuẩn `bash scripts/run_public.sh` và `bash scripts/run_sim.sh`, không chạy trực tiếp binary lỗi thời.
4. Tôi sửa `solution/config.json` để giảm noise, tắt fault injection, bật retry/cache, và đưa hệ thống về cấu hình ổn định hơn.
5. Tôi viết lại `solution/prompt.txt` theo hướng ngắn gọn, tool-first, exact arithmetic, không lặp PII, và chống prompt injection.
6. Tôi chỉnh `solution/wrapper.py` để ghi nhận trace, tính lại tổng tiền khi đủ điều kiện, phát hiện lỗi tool, và tránh trả lời sai cho các case không hợp lệ.
7. Tôi cập nhật `solution/findings.json` để mô tả đúng fault class, bằng chứng, nguyên nhân gốc, và hướng sửa.
8. Tôi chạy lại public và đối chiếu kết quả theo từng câu để xác nhận correctness.
9. Tôi kiểm tra thêm các câu paraphrase/injection để chuẩn bị cho private.

## Kết quả public

Tôi đạt `13/13` câu đúng trên public simulation, và điểm public score hiện tại là `90.32/100`.

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

## File chính tôi đã chỉnh

- `solution/config.json`
- `solution/prompt.txt`
- `solution/examples.json`
- `solution/wrapper.py`
- `solution/findings.json`

## Ghi chú cho private

Tôi đã ưu tiên khả năng tổng quát cho private: xử lý paraphrase, voucher/coupon, số lượng bằng chữ, địa chỉ giao đa dạng, PII cleanup, và injection trong ghi chú đơn hàng. Tôi cũng thêm `scripts/run_private.sh` để khi có binary private thì có thể chạy theo đúng luồng chuẩn.

