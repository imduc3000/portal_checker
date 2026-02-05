import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from config import LOGIN_PAGE_URL, NEWS_HOMEPAGE_URL, HISTORY_FILE

load_dotenv()
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")

def load_seen_links():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_seen_link(link):
    seen_links = load_seen_links()
    if link not in seen_links:
        seen_links.append(link)
        with open(HISTORY_FILE, "w") as f:
            json.dump(seen_links, f)

def get_notification_detail(page, link):
    page.goto(link)
    page.wait_for_selector("h2.rnews-header")

    title = page.locator("h2.rnews-header").inner_text()
    content = page.locator("#rnew_content").inner_text()

    file_elements = page.locator("a[onclick^='downloadFile']").all()
    attachments = []
    base_url_download = "https://studentnews.tdtu.edu.vn/TinTuc/Download?id={id}&filename={filename}"

    for element in file_elements:
        onclick_attr = element.get_attribute('onclick')
        id_attr = element.get_attribute('id')
        
        if onclick_attr and id_attr:
            try:
                file_name = onclick_attr.split("'")[1]
                file_url = base_url_download.format(id=id_attr, filename=file_name)
                attachments.append(file_url)
            except IndexError:
                continue

    return {
        "title": title,
        "content": content,
        "attachments": attachments
    }
    
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def ai_summarize(title, content, attachment_count):
    # Chúng ta đưa thêm số lượng file vào để AI biết đường mà nhắc
    prompt = f"""
    Bạn là trợ lý thông báo sinh viên. Hãy phân tích thông báo sau:
    TIÊU ĐỀ: {title}
    NỘI DUNG: {content}
    SỐ FILE ĐÍNH KÈM: {attachment_count}

    YÊU CẦU: Trả về kết quả DUY NHẤT ở định dạng JSON với cấu trúc sau:
    {{
        "is_important": true/false (true nếu liên quan học phí, lịch thi, deadline, đăng ký môn),
        "summary": "đoạn tóm tắt súc tích dùng icon",
        "has_action": "hành động cần làm ngay nếu có (ví dụ: Nộp tiền trước 20/01)"
    }}
    """
    
    try:
        # Sử dụng tham số response_mime_type để ép Gemini trả về JSON (chỉ có ở các bản 1.5 hoặc 2.0+)
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Lỗi AI: {e}")
        return None
    
def send_telegram_notification(summary, original_link, attachments):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    # Tạo nội dung tin nhắn
    message = f"{summary}\n\n🔗 Xem chi tiết: {original_link}"
    
    if attachments:
        message += "\n\n📎 File đính kèm:\n" + "\n".join(attachments)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"} # Dùng Markdown để in đậm/nghiêng
    requests.post(url, json=payload)

def run_scraper():
    seen_links = load_seen_links()
    new_notifications = []

    with sync_playwright() as p:
        print("Đang khởi tạo trình duyệt...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Bắt đầu đăng nhập...")
        page.goto(LOGIN_PAGE_URL)

        page.fill("#txtUser", USERNAME)
        page.fill("#txtPass", PASSWORD)
        page.click("#btnLogIn")

        try:
            page.wait_for_load_state("networkidle", timeout=10000) 
            print("Đăng nhập thành công (hoặc đã gửi request login)!")
        except:
            print("Cảnh báo: Mất quá nhiều thời gian để tải trang sau login.")

        print("Đang thu thập link...")
        page.goto(NEWS_HOMEPAGE_URL)
        
        try:
            page.wait_for_selector("a.tb-khan-click", timeout=10000)
        except:
            print("Không tìm thấy thông báo nào hoặc trang chưa load xong.")
            browser.close()
            return

        notification_elements = page.locator("a.tb-khan-click").all()
        
        all_links = []
        base_url_news = "https://studentnews.tdtu.edu.vn"

        for element in notification_elements:
            onclick_attribute = element.get_attribute('onclick')
            
            if onclick_attribute:
                try:
                    relative_path = onclick_attribute.split("'")[1]
                    full_link = base_url_news + relative_path
                    all_links.append(full_link)
                except IndexError:
                    continue

        print(f"Nhiệm vụ hoàn tất. Thu thập được {len(all_links)} links.")
        
        print("\n--- Danh sách link thu thập được ---")
        for i, link in enumerate(all_links):
            print(f"{i+1}: {link}")

        seen_links = load_seen_links() # Đảm bảo có dấu ngoặc () nha!

        for link in all_links:
            if link not in seen_links:
                print(f"Đang xử lý: {link}")
                
                # 1. Lấy dữ liệu thô từ Web (Có chứa link file chuẩn 100%)
                detail = get_notification_detail(page, link)
                
                # 2. Hỏi AI xem tin này có gì hay
                ai_result = ai_summarize(detail['title'], detail['content'], len(detail['attachments']))
                
                if ai_result:
                    # 3. Chuẩn bị nội dung gửi đi
                    header = "🚨 QUAN TRỌNG" if ai_result['is_important'] else "ℹ️ THÔNG TIN"
                    full_summary = f"{header}\n\n{ai_result['summary']}"
                    
                    if ai_result['has_action']:
                        full_summary += f"\n\n👉 Việc cần làm: {ai_result['has_action']}"

                    # 4. Gửi lên Telegram (Truyền detail['attachments'] đã lấy từ lúc scrape)
                    send_telegram_notification(full_summary, link, detail['attachments'])
                    
                    save_seen_link(link)
                    print("Đã gửi thông báo thành công!")


        browser.close()

if __name__ == "__main__":
    run_scraper()