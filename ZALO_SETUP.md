# Thêm Zalo, giữ Telegram làm kênh song song

Telegram luôn tiếp tục được gửi như trước. Khi cấu hình Zalo, mỗi thông báo mới được gửi tới cả hai kênh. Mỗi kênh có danh sách ID gửi thành công riêng: Zalo lỗi/quota không ngăn Telegram gửi. Thiếu cả hai secret Zalo thì chỉ chạy Telegram. Cấu hình Zalo chỉ có một secret sẽ báo lỗi cấu hình, nhưng vẫn chạy Telegram.

## Cấu hình trên GitHub

Giữ nguyên toàn bộ secrets hiện có. Trong repository → Settings → Secrets and variables → Actions, thêm:

- `ZALO_BOT_TOKEN`: token bot của bạn, không gửi vào chat hoặc commit.
- `ZALO_CHAT_ID`: ID nhóm đã thử thành công: `zgr-90394514db7b32256b6a`.

Sau khi áp dụng code, vào Actions → TDTU Portal Checker → Run workflow. Bot chỉ gửi thông báo chưa có trong trạng thái, nên nếu không có tin mới thì không có tin để thử. Không xóa state để ép gửi thử.

Không cần cài dự án trên máy bạn để chạy bằng GitHub Actions. Không cần server hoặc API AI trả phí. Giới hạn/quyền của Zalo BASIC do Zalo áp dụng; thay đổi code không mua gói hay nâng quota.

## Chuyển trạng thái và thử lại

- Lần đầu chuyển đổi lấy `seen_ids` cũ làm mốc cho cả hai kênh, tránh gửi hàng loạt thông báo cũ. Code cũ lưu ID trước khi gửi nên không thể biết chắc những tin lịch sử đã thật sự đến Telegram.
- Mỗi tin dài chia thành các đoạn, Zalo tối đa 2.000 đơn vị UTF-16; Telegram tối đa 4.000. Lưu tiến độ sau mỗi đoạn thành công.
- Khi gửi lỗi, dừng batch của kênh đó và thử lại ở lần chạy sau, miễn thông báo vẫn được Portal API trả về. Không lưu nội dung thông báo vào repository công khai; vì vậy không thể phục hồi tin đã biến mất khỏi API.
- Workflow commit trạng thái kể cả khi một kênh lỗi, sau đó vẫn báo workflow thất bại để bạn biết. Workflow chạy tuần tự để hạn chế xung đột trạng thái.
- Nếu mạng ngắt sau khi dịch vụ đã nhận tin nhưng trước khi nhận phản hồi, hoặc lưu/push trạng thái thất bại, lần chạy sau vẫn có thể gửi trùng. Không cam kết gửi đúng một lần tuyệt đối.
- Đổi bot/nhóm mới không tự phát lại lịch sử. `deliveries` lưu ID/hàm băm/tiến độ, không lưu token hoặc nội dung; ID vẫn là metadata công khai nếu repo public.
- Chỉ dùng cho thông báo chung phù hợp với các thành viên nhóm.

Muốn tạm tắt Zalo: xóa cả hai secrets Zalo; Telegram tiếp tục chạy.

## Kiểm thử local

```sh
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Chạy local đọc biến môi trường hoặc `.env` (không commit). Workflow lấy cấu hình từ GitHub Secrets. Kiểm thử giả lập không gửi tin thật.
