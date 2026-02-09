import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Set, Optional

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
# TESTING - Uncomment để test từng function riêng
# ============================================================

if __name__ == "__main__":

    
    # Test 2: Rolling Window
    # print("\nTest 2: Rolling Window")
    # seen = set(['100', '99', '98'])
    # new = ['101', '102']
    # result = maintain_rolling_window(seen, new)
    # print(f"Result: {result}")
    
    # Test 3: Full check
    print("\nTest 3: Full Check")
    result = check_for_update()
    print(f"New notifications: {result}")
    

                
    
