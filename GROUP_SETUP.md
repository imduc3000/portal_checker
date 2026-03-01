# 👥 Hướng dẫn: Thêm Bot vào Group Telegram

## 🎯 Mục tiêu

Thêm bot vào group để nhiều người cùng nhận thông báo.

---

## 📋 Các bước thực hiện

### Bước 1: Tạo Group

1. Mở Telegram app
2. Menu → **New Group**
3. Đặt tên group: "TDTU Portal Notifications"
4. Thêm bạn bè vào group

### Bước 2: Thêm Bot vào Group

1. Trong group chat, click **Add Members**
2. Search tên bot của bạn (vd: `tdtu_portal_bot`)
3. Add bot vào group
4. Bot sẽ join group

### Bước 3: Cho Bot quyền gửi message

**⚠️ Quan trọng:** Bot cần quyền post messages!

1. Group Settings → **Administrators**
2. **Add Administrator** → Chọn bot
3. Chỉ cần enable: ✅ **Post Messages**
4. Save

*Hoặc để bot là member thường (không phải admin) - bot vẫn post được nhưng chỉ khi group settings cho phép "All Members" post.*

### Bước 4: Lấy Group Chat ID

**4.1 Gửi message test trong group:**
```
/start
Hello bot!
```

**4.2 Call Telegram API để lấy Group Chat ID:**

Mở browser, paste URL (thay `YOUR_BOT_TOKEN`):
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

**4.3 Tìm group chat ID trong JSON response:**

```json
{
  "result": [
    {
      "message": {
        "chat": {
          "id": -1001234567890,  // ← Group Chat ID (số âm!)
          "title": "TDTU Portal Notifications",
          "type": "group"
        }
      }
    }
  ]
}
```

**Đặc điểm Group Chat ID:**
- Là số **âm** (negative number)
- Private chat: số dương
- Group/Supergroup: số âm

### Bước 5: Update `.env` file

```env
# Thay private chat ID bằng group chat ID
TELEGRAM_CHAT_ID=-1001234567890
```

**⚠️ Lưu ý:** Giữ dấu trừ (`-`) ở đầu!

---

## 🧪 Testing

Chạy script để test:
```bash
python news_checker.py
```

Message sẽ được gửi đến **group** thay vì chat riêng!

---

## 💡 Tips

### Tip 1: Bot không gửi được message?

**Nguyên nhân:** Group settings chặn bot

**Giải pháp:**
1. Group Settings → **Permissions**
2. Enable **Send Messages** cho all members
3. Hoặc promote bot thành admin

### Tip 2: Muốn cả 2 (Private + Group)?

Thêm vào `.env`:
```env
TELEGRAM_CHAT_ID=-1001234567890,123456789
```

Update code để gửi nhiều chats:
```python
def send_telegram_notification(notifications):
    chat_ids = os.getenv('TELEGRAM_CHAT_ID').split(',')
    
    for chat_id in chat_ids:
        # Send to each chat
        payload = {'chat_id': chat_id.strip(), 'text': message}
        requests.post(url, json=payload)
```

### Tip 3: Group vs Supergroup

- **Group:** Tối đa 200 members, Chat ID bắt đầu `-100...`
- **Supergroup:** Unlimited members, Chat ID bắt đầu `-1001...`

*Telegram tự động upgrade Group → Supergroup khi cần.*

---

## ❓ Troubleshooting

**Lỗi: "Forbidden: bot was kicked from the group"**
- Bot bị remove khỏi group
- Add lại bot

**Lỗi: "Forbidden: bot is not a member of the group"**
- Bot chưa được add
- Hoặc bot bị ban

**Lỗi: "Bad Request: chat not found"**
- Chat ID sai
- Check lại getUpdates response

---

Done! Bây giờ cả team bạn đều nhận được thông báo! 👥
