import requests
import os 
from dotenv import load_dotenv

load_dotenv()

s = requests.Session()

s.headers.update ({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
})


login_url = "https://stdportal.tdtu.edu.vn/Login/SignIn?ReturnURL=https://stdportal.tdtu.edu.vn/home/index"

username = os.getenv("PORTAL_USERNAME")
password = os.getenv("PORTAL_PASSWORD")

payload = {
    'user': username,
    'pass': password 
}

response = s.post(login_url, data=payload)

res_data = response.json()

auth_url = res_data.get("url")

s.get(auth_url)

noti_url = 'https://stdportal.tdtu.edu.vn/home/LayThongBaoQuanTrongSinhVien'

noti_res = s.get(noti_url)

data = noti_res.json()

if len(data) > 0:
    latest_item = data[0]

    news_id = latest_item.get('id')

    news_title = latest_item.get('tieuDe')

    news_link = latest_item.get('link')


    print("-" * 30)
    print(f"🆔 ID: {news_id}")
    print(f"📢 Tiêu đề: {news_title}")
    print(f"🔗 Link: {news_link}")
    print("-" * 30)

