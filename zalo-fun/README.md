# Chế độ vui cho nhóm Zalo

Cloudflare Worker nhận webhook riêng, không sửa lịch kiểm tra Portal hoặc Telegram. Không có AI API/LLM. Các câu trả lời được soạn sẵn trong `worker.mjs`.

## Lệnh

- `@Bot Portal Checker Bình` hoặc `@bot Bình`: một câu đùa ngẫu nhiên về deadline/học bài, kèm sticker.
- `@Bot Portal Checker trợ giúp`: hướng dẫn.
- `@Bot Portal Checker dừng Bình`: tắt câu đùa về Bình trong nhóm. Muốn bật lại, chủ bot xóa trường `paused` trong bản ghi Durable Object `state` qua Cloudflare Data Studio; không có lệnh bật lại cho mọi người.
- Các lệnh `/binh`, `/help`, `/stop binh` cũng được hỗ trợ nếu Zalo chuyển sự kiện này đến bot.

Trong Zalo hãy chọn **mention bot thật** từ danh sách gợi ý. Chỉ gõ chữ `@bot` có thể không làm Zalo gửi sự kiện. Bộ phân tích hỗ trợ tên hiển thị `Bot Portal Checker`, tài khoản `bot.iCVlnHsz` và dạng `@bot`. Cần đối chiếu sự kiện thật nếu Zalo thay đổi định dạng mention.

## Giới hạn

Chỉ một nhóm được cấu hình trong `ZALO_CHAT_ID`. Tin nhắn cá nhân/nhóm khác/từ bot khác/không phải lệnh được bỏ qua. Tối thiểu 8 giây giữa phản hồi, 30 giây giữa các câu chọc. Tối đa 100 phản hồi/ngày UTC, mỗi phản hồi dùng 2–3 API calls. Zalo vẫn áp dụng quota riêng; không có cơ chế nâng gói tự động.

Durable Object dùng SQLite được hỗ trợ ở Workers Free. Trạng thái chỉ gồm tối đa 128 ID sự kiện gần nhất, số đếm/thời gian, chỉ số câu đùa và trạng thái tắt; không lưu toàn bộ tin nhắn hay thông tin người gửi. Có lưu reservation trước khi gửi để chống phản hồi lặp. Nếu gửi lỗi, cần nhắn lệnh mới sau thời gian nghỉ; không tự gửi lại cùng sự kiện.

`sendChatAction(typing)` và sticker là best-effort. Lỗi typing vẫn thử gửi chữ; lỗi gửi chữ không gửi sticker. Mã sticker mặc định lấy từ ví dụ chính thức của Zalo; cần xác minh hiển thị thực tế. Đặt `STICKER_ID` rỗng để tắt sticker.

## Triển khai

1. Đăng nhập Cloudflare, giữ Workers Free. Không cần mua tên miền.
2. Cài Wrangler chính thức, vào thư mục này.
3. `npx wrangler login` rồi `npx wrangler deploy`. Wrangler tạo SQLite Durable Object nhờ migration `v1`.
4. Thêm secrets bằng `npx wrangler secret put ZALO_BOT_TOKEN` và `npx wrangler secret put WEBHOOK_SECRET`. Dùng chuỗi ngẫu nhiên dài ít nhất 32 ký tự cho secret webhook, không commit vào repo.
5. Gọi `setWebhook` của Zalo với URL HTTPS `<worker-url>/webhook` và cùng `secret_token`. Kiểm tra `verification.ok`, vì URL vẫn được Zalo lưu kể cả khi xác minh thất bại.
6. Trong nhóm, mention bot và gửi `Bình`. Kiểm tra cả tin chữ/sticker. `typing` chỉ là trạng thái tạm thời, có thể biến mất nhanh.

Việc bật webhook ngăn script local `getUpdates` nhận sự kiện; không ảnh hưởng `sendMessage` của checker chạy trên GitHub Actions. Muốn ngừng tính năng vui: xóa webhook qua `deleteWebhook`; lịch thông báo Portal vẫn tiếp tục.

## Kiểm thử

`node --test worker.test.mjs` — không gửi tin thật.

## Tài liệu

- https://docs.zaloplatforms.com/docs/BOT/webhook
- https://docs.zaloplatforms.com/docs/BOT/apis/setWebhook
- https://docs.zaloplatforms.com/docs/BOT/apis/sendSticker
- https://docs.zaloplatforms.com/docs/BOT/apis/sendChatAction
- https://developers.cloudflare.com/durable-objects/platform/pricing/
