# 📱 Telegram Bot Setup Guide

## 🎯 Mục tiêu

Implement `send_telegram_notification()` để gửi thông báo qua Telegram Bot.

---

## 📋 Bước 1: Tạo Telegram Bot (5 phút)

### 1.1 Tìm @BotFather trên Telegram

1. Mở Telegram app
2. Search: `@BotFather`
3. Click `/start`

### 1.2 Tạo bot mới

```
/newbot
```

BotFather sẽ hỏi:
1. **Bot name:** TDTU Portal Checker (tên hiển thị)
2. **Bot username:** tdtu_portal_bot (phải unique, kết thúc bằng `_bot`)

### 1.3 Lưu Bot Token

BotFather sẽ trả về:
```
Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Copy token này!**

---

## 📋 Bước 2: Lấy Chat ID (3 phút)

### 2.1 Start chat với bot

1. Click link bot từ BotFather message
2. Click `/start` trong bot chat

### 2.2 Lấy Chat ID

Mở browser, paste URL này (thay YOUR_BOT_TOKEN):
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Sẽ thấy JSON response:
```json
{
  "result": [{
    "message": {
      "chat": {
        "id": 123456789  // ← Đây là CHAT_ID của bạn
      }
    }
  }]
}
```

**Copy chat ID này!**

---

## 📋 Bước 3: Thêm vào .env

Mở file `.env`, thêm 2 dòng:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

---

## 📋 Bước 4: Implement Function

### TODO: Code function `send_telegram_notification()`

**Cần làm:**

1. **Load credentials từ .env**
   ```python
   bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
   chat_id = os.getenv('TELEGRAM_CHAT_ID')
   ```

2. **Format message cho TỪNG notification**
   - Loop qua list notifications
   - Format mỗi notification thành string đẹp
   - Example format:
     ```
     🔔 Thông báo mới!
     
     📌 [Tiêu đề]
     📄 [Summary]
     📅 [Date]
     🔗 [Link]
     ```

3. **Send POST request đến Telegram API**
   - URL: `https://api.telegram.org/bot{token}/sendMessage`
   - Method: POST
   - Body (JSON):
     ```json
     {
       "chat_id": "...",
       "text": "message đã format"
     }
     ```

4. **Handle response**
   - Check `response.status_code == 200`
   - Return `True` nếu thành công
   - Return `False` và print error nếu thất bại

---

## 🧪 Testing

Sau khi code xong:

### Test 1: Run script
```bash
python news_checker.py
```

### Test 2: Check Telegram
- Mở Telegram app
- Vào chat với bot
- Phải thấy message mới!

---

## 💡 Tips

**Keywords để research:**
- `requests.post()` - Gửi POST request
- `json={}` parameter - Gửi JSON body
- `f-string` - Format message đẹp với \n (newline)
- Try-except để handle network errors

**Telegram API Docs:**
- https://core.telegram.org/bots/api#sendmessage

**Message formatting (optional):**
- Dùng Markdown: `parse_mode: "Markdown"`
- Bold: `**text**`
- Link: `[text](url)`

---

## ❓ Troubleshooting

**Lỗi: "Unauthorized"**
- Bot token sai, check lại .env

**Lỗi: "Chat not found"**
- Chat ID sai hoặc chưa `/start` bot

**Không thấy message:**
- Check mở đúng bot chat
- Check response từ API (print ra)

---

## 🚀 Next: GitHub Actions

Sau khi Telegram works thì setup GitHub Actions để chạy tự động!
# 📱 Hướng dẫn Chi tiết - Telegram Notification Function

## 🎯 Mục tiêu

Viết function `send_telegram_notification(notifications)` để gửi thông báo qua Telegram Bot.

---

## 📋 Input/Output

**Input:**
```python
notifications = [
    {
        'id': '145738',
        'title': '[Tiếng Anh] - Lịch thi cuối kỳ...',
        'summary': 'Khoa Ngoại ngữ thông báo lịch thi...',
        'link': 'https://studentnews.tdtu.edu.vn/ThongBao/Detail/145738',
        'date': '06/02/2026'
    },
    # ... có thể có nhiều notifications
]
```

**Output:**
- `True` nếu gửi thành công
- `False` nếu có lỗi

**Telegram message format:**
```
🔔 Có 2 thông báo mới!

━━━━━━━━━━━━━━━━━━━━━━

📌 [Tiếng Anh] - Lịch thi cuối kỳ HK2

📄 Khoa Ngoại ngữ thông báo lịch thi cuối kỳ HK2 2024-2025...

📅 06/02/2026
🔗 Link: https://studentnews.tdtu.edu.vn/ThongBao/Detail/145738

━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 Implementation Guide

### Bước 1: Load credentials từ .env

```python
def send_telegram_notification(notifications: List[Dict]) -> bool:
    # Load credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Validate credentials exist
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials in .env")
        return False
```

**Giải thích:**
- `os.getenv()` đọc từ file `.env` (đã có `load_dotenv()` ở đầu script)
- Check credentials tồn tại trước khi gửi
- Return `False` nếu thiếu credentials

---

### Bước 2: Format message

**2.1 Tạo header (số lượng thông báo):**
```python
    # Build message header
    count = len(notifications)
    message = f"🔔 Có {count} thông báo mới!\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
```

**Giải thích:**
- `f"..."` là f-string để insert biến vào string
- `\n` là newline (xuống dòng)
- `\n\n` là 2 dòng trống
- `+=` append vào string

**2.2 Loop qua từng notification:**
```python
    # Add each notification
    for notif in notifications:
        # Extract fields
        title = notif['title']
        summary = notif['summary']
        link = notif['link']
        date = notif['date']
        
        # Format notification block
        message += f"📌 {title}\n\n"
        message += f"📄 {summary}\n\n"
        message += f"📅 {date}\n"
        message += f"🔗 Link: {link}\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
```

**Giải thích:**
- Loop qua list `notifications`
- Extract từng field từ dict
- Format thành text đẹp với emoji
- Separator line giữa các notifications

**💡 Tip - Truncate summary nếu quá dài:**
```python
        # Limit summary to 200 chars
        summary = notif['summary'][:200]
        if len(notif['summary']) > 200:
            summary += '...'
```

---

### Bước 3: Send POST request đến Telegram API

**3.1 Construct API URL:**
```python
    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
```

**Giải thích:**
- Template: `https://api.telegram.org/bot{YOUR_BOT_TOKEN}/sendMessage`
- F-string để insert `bot_token` vào URL

**3.2 Prepare request body:**
```python
    # Prepare payload
    payload = {
        'chat_id': chat_id,
        'text': message
    }
```

**Giải thích:**
- `payload` là dict chứa data gửi lên API
- `chat_id`: ID của chat nhận message
- `text`: Message content (string đã format ở bước 2)

**3.3 Send POST request:**
```python
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()  # Raise exception nếu status code != 2xx
        
        print("✅ Telegram notification sent!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram API Error: {e}")
        return False
```

**Giải thích:**
- `requests.post()` gửi POST request
- `json=payload` tự động convert dict → JSON và set `Content-Type: application/json`
- `timeout=10` timeout sau 10 giây
- `raise_for_status()` throw exception nếu response code 4xx/5xx
- Try-except để catch network errors
- Return `True` nếu OK, `False` nếu lỗi

---

## 📝 Complete Code Structure

```python
def send_telegram_notification(notifications: List[Dict]) -> bool:
    # Step 1: Load credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials in .env")
        return False
    
    # Step 2: Format message
    count = len(notifications)
    message = f"🔔 Có {count} thông báo mới!\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for notif in notifications:
        # Extract and format each notification
        # ... (code ở trên)
        pass
    
    # Step 3: Send to Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram notification sent!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram API Error: {e}")
        return False
```

---

## 🧪 Testing Strategy

### Test 1: Fake notification test
```python
# Ở cuối file, thêm test code:
if __name__ == "__main__":
    # Test với fake data
    fake_notifications = [
        {
            'id': '12345',
            'title': 'Test Notification',
            'summary': 'This is a test summary',
            'link': 'https://example.com',
            'date': '28/02/2026'
        }
    ]
    
    success = send_telegram_notification(fake_notifications)
    print(f"Result: {success}")
```

### Test 2: Real notification test
Chạy script bình thường, nếu có notification mới sẽ tự động gửi.

---

## 🎨 Optional Enhancements (Sau khi basic works)

### 1. Markdown formatting (đẹp hơn)
```python
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'  # Enable Markdown
    }
    
    # Trong message format:
    message += f"*{title}*\n\n"  # Bold title
    message += f"[Xem chi tiết]({link})\n\n"  # Clickable link
```

### 2. Disable link preview
```python
    payload = {
        'chat_id': chat_id,
        'text': message,
        'disable_web_page_preview': True  # No preview thumbnail
    }
```

### 3. Send multiple messages (nếu quá dài)
```python
    # Telegram limit: 4096 chars per message
    if len(message) > 4000:
        # Send each notification separately
        for notif in notifications:
            # Format one notification
            single_message = f"..."
            # Send single_message
```

---

## ❓ Troubleshooting

**Lỗi: `"Missing Telegram credentials"`**
- Check file `.env` có 2 dòng: `TELEGRAM_BOT_TOKEN=...` và `TELEGRAM_CHAT_ID=...`
- Check không có khoảng trắng: `CHAT_ID=123` (đúng), `CHAT_ID = 123` (sai)

**Lỗi: `"Bad Request: chat not found"`**
- Chat ID sai
- Hoặc chưa `/start` bot

**Lỗi: `"Unauthorized"`**
- Bot token sai

**Message không hiện đúng format:**
- Check `\n` cho newline
- Check emoji có hiển thị không (copy từ guide này)

---

## 💡 Debug Tips

**Print message trước khi gửi:**
```python
    print("=" * 50)
    print("DEBUG - Message to send:")
    print(message)
    print("=" * 50)
```

**Print response từ Telegram:**
```python
    response = requests.post(url, json=payload, timeout=10)
    print(f"Telegram response: {response.json()}")
```

---

Bạn có thể bắt đầu code theo structure này! Nếu bí bước nào thì hỏi tôi nhé! 😊
