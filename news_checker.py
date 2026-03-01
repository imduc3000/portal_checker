import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup

WINDOW_SIZE = 50  
SEEN_FILE = 'seen_notifications.json'  

def load_seen_data() -> Dict:
    default_data = {
        'last_check_time': None,
        'seen_ids': set(),
        'metadata': {
            'window_size': WINDOW_SIZE,
            'total_checked': 0
        }
    }

    try:
        with open (SEEN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data['seen_ids'] = set(data.get('seen_ids', []))
            return data

    except FileNotFoundError:
        print(f"File '{SEEN_FILE}' not found - first run, using defaults")
        return default_data
    
    except json.JSONDecodeError as e:
        print(f"File '{SEEN_FILE}' contains invalid JSON: {e}")
        print(f"Tip: Delete the file and run again to create a fresh one")
        return default_data
    
    except Exception as e:
        print(f"Load data Error: {e}")
        return default_data

def save_seen_data(data: Dict) -> None:
    save_data = {
        'last_check_time': datetime.now().isoformat(timespec='seconds'),
        'seen_ids': list(data['seen_ids']),
        'metadata': {
            'window_size': data['metadata'].get('window_size', WINDOW_SIZE),
            'total_checked': data['metadata'].get('total_checked', 0)
        }
    }

    try:
        with open (SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
    
    except IOError as e:
        print(f"IO Error when writing in to JSON file: {e}")

    except Exception as e:
        print(f"Error when save new data to Json file: {e}")


def maintain_rolling_window(seen_ids: Set[str], new_ids: List[str]) -> Set[str]:
    """
    Duy trì rolling window: thêm IDs mới, xóa IDs cũ nếu quá limit
    
    Args:
        seen_ids: Set of IDs đã thấy
        new_ids: List of IDs mới cần thêm
        
    Returns:
        Set of IDs sau khi maintain (không modify input)
    """

    update_ids = seen_ids.copy()
    update_ids.update(new_ids)
    
    if len(update_ids) > WINDOW_SIZE:
        sorted_ids = sorted(update_ids, key=lambda x : int(x), reverse=True)
        sorted_ids = sorted_ids[:WINDOW_SIZE]
        return set(sorted_ids)

    return update_ids
    

def check_for_update() -> List[Dict] | None: 
    load_dotenv()

    header = os.getenv("HEADERS")
    login_url = os.getenv("LOGIN_URL")
    api_url = os.getenv("API_URL")
    username = os.getenv("PORTAL_USERNAME")
    password = os.getenv("PORTAL_PASSWORD")

    data = load_seen_data()
    seen_ids = data['seen_ids']

    session = requests.Session()
    session.headers.update ({
        "User-Agent": header
    })

    payload = {
        'user': username,
        'pass': password
    }

    try:
        response = session.post(login_url, data=payload)
        response.raise_for_status()

        response_data = response.json() #return result & url as dict. 

        if "url" in response_data:
            print("Login Successfully!")
            session.get(response_data["url"]) # Url contains token to login.
            
        else:
            print("Login Failed!")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"Login Error: {e}")
        return None
       
    try:
        api_response = session.get(api_url, timeout=10)
        api_response.raise_for_status()

        api_data = api_response.json()
        new_notifications = []
        all_current_ids = []

        for item in api_data:
            item_id = str(item.get('id'))
            all_current_ids.append(item_id)

            if item_id not in seen_ids:
                new_notifications.append({
                    'id': item_id,
                    'title': item['tieuDe'],
                    'summary': item['tomTatNoiDung'],
                    'link': item['link'],
                    'date': item['ngayDang']
                })

        seen_ids = maintain_rolling_window(seen_ids=seen_ids, new_ids=all_current_ids)
        data['metadata']['total_checked'] += 1
        data['seen_ids'] = seen_ids

        save_seen_data(data)

        if new_notifications:
            print(f"Found '{len(new_notifications)}' new notifications!")
            new_notifications.sort(key=lambda k : int(k['id']) , reverse=True)
            return new_notifications
        else:
            print(f"Found 0 new notifications!")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Data not in JSON format: {e}")
        return None


# ============================================================
# PHASE 2: EXTRACTION
# ============================================================
# PHASE 2: TELEGRAM NOTIFICATION
# ============================================================

def send_telegram_notification(notifications: List[Dict]) -> bool:
    """
    Gửi thông báo qua Telegram Bot.
    
    Args:
        notifications: List of notification dicts từ check_for_update()
            [{'id': '...', 'title': '...', 'summary': '...', 'link': '...', 'date': '...'}]
        
    Returns:
        True nếu gửi thành công, False nếu có lỗi
    
    Xem hướng dẫn chi tiết: TELEGRAM_IMPLEMENTATION.md
    """
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    message = f"🔔 Có {len(notifications)} thông báo mới!\n\n"
    for notification in notifications:
        title = notification['title']
        summary = notification['summary']
        link = notification['link']
        date = notification['date']

        message += f"📌 Tít Le: {title}\n\n"
        message += f"📄 Tóm tắt: {summary}\n\n"
        message += f"🔗 Link: {link}\n\n"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()  
    
        print("Telegram notification sent!")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Telegram API Error: {e}")
        return False



# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 TDTU Portal Notification Checker")
    print("=" * 50)
    
    # Check for new notifications
    notifications = check_for_update()
    
    if notifications:
        print(f"\n📋 Found {len(notifications)} new notification(s)!")
        print("-" * 50)
        
        # Print notifications
        for notif in notifications:
            print(f"\n🆔 ID: {notif['id']}")
            print(f"📌 Title: {notif['title']}")
            print(f"📄 Summary: {notif['summary'][:100]}...")
            print(f"📅 Date: {notif['date']}")
            print(f"🔗 Link: {notif['link']}")
        
        # Send to Telegram
        print("\n" + "=" * 50)
        print("📱 Sending to Telegram...")
        print("=" * 50)
        
        success = send_telegram_notification(notifications)
        
        if success:
            print("\n✅ Telegram notification sent!")
        else:
            print("\n❌ Failed to send Telegram notification")
    else:
        print("\n✅ All caught up! No new notifications.")
    
    print("\n" + "=" * 50)
