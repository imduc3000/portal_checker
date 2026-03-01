# ⚙️ GitHub Actions Setup Guide

## 🎯 Mục tiêu

Setup GitHub Actions để tự động:
- Chạy script mỗi 30 phút
- Check thông báo mới
- Gửi Telegram
- **Persist state** (seen_notifications.json)

---

## 📋 Bước 1: Push code lên GitHub

### 1.1 Tạo repository mới

1. Vào https://github.com/new
2. Repository name: `tdtu-portal-checker`
3. **Private** (để bảo mật credentials)
4. **Không** tick "Add README" (đã có local)
5. Create repository

### 1.2 Tạo .gitignore

```bash
# Tạo file .gitignore
cat > .gitignore << EOF
.env
.venv/
__pycache__/
*.pyc
news_checker_backup.py
EOF
```

**⚠️ Quan trọng:** File `.env` KHÔNG được commit (chứa passwords)!

### 1.3 Init Git và push

```bash
# Init git
git init
git add .
git commit -m "Initial commit: Portal notification checker"

# Connect to GitHub
git remote add origin https://github.com/YOUR_USERNAME/tdtu-portal-checker.git
git branch -M main
git push -u origin main
```

---

## 📋 Bước 2: Setup GitHub Secrets

GitHub Secrets = Nơi lưu credentials an toàn (không public).

### 2.1 Vào Settings

1. Vào repo trên GitHub
2. **Settings** tab
3. **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2.2 Thêm các secrets

**Add từng secret sau (copy từ file `.env`):**

| Secret Name | Value | Example |
|------------|-------|---------|
| `PORTAL_USERNAME` | Username portal | `123456789` |
| `PORTAL_PASSWORD` | Password portal | `YourPassword123` |
| `TELEGRAM_BOT_TOKEN` | Bot token | `123456:ABCdef...` |
| `TELEGRAM_CHAT_ID` | Chat/Group ID | `-1001234567890` |
| `HEADERS` | User-Agent | `Mozilla/5.0...` |
| `LOGIN_URL` | Login endpoint | `https://stdportal...` |
| `API_URL` | API endpoint | `https://stdportal...` |

**Cách thêm:**
1. Secret name: `PORTAL_USERNAME`
2. Secret value: Copy từ `.env` file
3. Click **Add secret**
4. Repeat cho tất cả secrets

---

## 📋 Bước 3: Verify Workflow File

File `.github/workflows/checker.yml` đã được tạo!

**Kiểm tra:**
```bash
cat .github/workflows/checker.yml
```

**Should see:**
- `schedule: cron: '*/30 * * * *'` → Chạy mỗi 30 phút
- Environment variables từ secrets
- Auto-commit step

---

## 📋 Bước 4: Push Workflow lên GitHub

```bash
git add .github/workflows/checker.yml
git commit -m "Add GitHub Actions workflow"
git push origin main
```

---

## 📋 Bước 5: Enable Workflow

### 5.1 Vào Actions tab

1. Repo trên GitHub → **Actions** tab
2. Nếu thấy warning "Workflows aren't being run..."
3. Click **I understand, enable them**

### 5.2 Verify workflow đã enable

- Vào **Actions** tab
- Thấy workflow "TDTU Portal Checker"
- Status: Enabled ✅

---

## 📋 Bước 6: Grant Write Permission cho GitHub Actions

**⚠️ Cực kỳ quan trọng!** Để workflow commit được `seen_notifications.json`.

### 6.1 Settings → Actions → General

1. Repo **Settings**
2. **Actions** → **General** (sidebar)
3. Scroll down → **Workflow permissions**

### 6.2 Enable Write Permission

- Select: ✅ **Read and write permissions**
- Click **Save**

*Mặc định là "Read-only" - workflow sẽ fail nếu không đổi!*

---

## 🧪 Bước 7: Test Manual Run

### 7.1 Trigger manual run

1. **Actions** tab
2. Click workflow "TDTU Portal Checker"
3. **Run workflow** dropdown
4. Click **Run workflow** button

### 7.2 Watch workflow run

- Workflow sẽ chạy (~30 giây)
- Click vào run để xem logs
- Check từng step: ✅ or ❌

### 7.3 Verify kết quả

**Check 1: Telegram**
- Mở Telegram group
- Có message mới? (nếu có notification)

**Check 2: Git commit**
- Vào repo trên GitHub
- Check commit history
- Thấy commit mới: "🤖 Update seen notifications"

**Check 3: seen_notifications.json**
- Click file `seen_notifications.json` trên GitHub
- Check `last_check_time` đã update

---

## 📅 Bước 8: Schedule đã active!

Workflow giờ sẽ tự động chạy **mỗi 30 phút**.

**Next runs:**
- 00:00, 00:30, 01:00, 01:30, ...
- 24/7 non-stop!

**Xem lịch chạy:**
- Actions tab → Workflow runs
- Lọc "Schedule" để xem automated runs

---

## 🔧 Customize Schedule

Muốn đổi tần suất? Edit `.github/workflows/checker.yml`:

```yaml
schedule:
  - cron: '*/15 * * * *'  # Mỗi 15 phút
  - cron: '0 * * * *'     # Mỗi giờ đúng
  - cron: '0 8,12,18 * * *'  # 8am, 12pm, 6pm mỗi ngày
```

**Cron syntax:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └── Day of week (0-6, Sunday=0)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

**Tools:** https://crontab.guru

---

## 📊 Monitoring

### Check workflow status

**Actions tab → All workflows:**
- Green ✅ = Success
- Red ❌ = Failed

**Click vào run để xem:**
- Logs của từng step
- Error messages nếu fail

### Common errors

**Error: "Permission denied"**
- Chưa enable "Write permissions"
- Xem lại Bước 6

**Error: "Bad credentials"**
- Secrets sai
- Check lại Settings → Secrets

**Error: Import error (beautifulsoup4, etc)**
- Thiếu dependency
- Check workflow file có `pip install ...`

---

## 💡 Tips

### Tip 1: Disable khi không dùng

Nếu đi du lịch không muốn nhận spam:
1. Actions tab
2. Workflow → **...** menu → **Disable workflow**

### Tip 2: Manual trigger

Test bất cứ lúc nào:
- Actions → Run workflow

### Tip 3: View logs

Debug khi có vấn đề:
- Click vào workflow run
- Expand từng step để xem output

### Tip 4: Notifications

Nhận email khi workflow fail:
- Settings → Notifications
- Enable "Actions" notifications

---

## 🚀 Congratulations!

Tool của bạn giờ chạy **tự động 24/7** trên GitHub! 🎉

**Flow hoạt động:**
```
GitHub Actions (mỗi 30 phút)
    ↓
Login Portal → Check API
    ↓
New notifications? 
    ↓ Yes
Send Telegram → Update JSON → Git commit
    ↓ No
Skip
```

**State persistence:**
- `seen_notifications.json` được commit sau mỗi lần chạy
- Lần chạy sau load file đã update
- Không bao giờ gửi duplicate notifications!

---

## 🎓 Next Level (Optional)

### 1. Error handling & retry
```yaml
- name: Check notifications (retry on fail)
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    command: python news_checker.py
```

### 2. Notifications on failure
Add vào workflow:
```yaml
- name: Notify on failure
  if: failure()
  run: |
    curl -X POST https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage \
      -d chat_id=${{ secrets.TELEGRAM_CHAT_ID }} \
      -d text="❌ Portal Checker failed!"
```

### 3. Multiple environments
Tạo secrets cho:
- `PORTAL_USERNAME_FRIEND`
- Run 2 workflows parallel cho nhiều accounts

---

Done! Enjoy your automated notification system! 🚀
