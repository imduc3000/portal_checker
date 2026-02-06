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


# ============================================================
# PART 2: ROLLING WINDOW LOGIC - Maintain danh sách seen IDs
# ============================================================

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
    


# ============================================================
# PART 3: MAIN LOGIC - Check for updates
# ============================================================

def check_for_update() -> List[Dict] | None:
    """
    Main function: Login portal, fetch notifications, check for new ones
    
    TODO 6: Load environment và seen data
    1. Gọi load_dotenv()
    2. Load các env variables (header, login_url, api_url, username, password)
    3. Gọi load_seen_data() để lấy seen_ids
    
    TODO 7: Setup session và login
    1. Tạo requests.Session()
    2. Update session.headers với User-Agent
    3. POST login với payload {'user': ..., 'pass': ...}
    4. Check response và handle authentication URL nếu có
    5. Dùng try/except để catch login errors
    
    TODO 8: Fetch notifications từ API
    1. GET request đến api_url với timeout=10
    2. Parse JSON response
    3. Check nếu api_data empty → return None
    
    TODO 9: Check for new notifications
    1. Tạo list rỗng: new_notifications = []
    2. Tạo list rỗng: all_current_ids = []
    3. Loop qua từng item trong api_data:
       a. Lấy item_id = str(item.get('id'))
       b. Thêm item_id vào all_current_ids
       c. Check: if item_id not in seen_ids:
          - Đây là tin MỚI!
          - Append vào new_notifications dict với keys:
            'id', 'title', 'summary', 'link', 'date'
    
    TODO 10: Update rolling window và save
    1. Gọi maintain_rolling_window(seen_ids, all_current_ids)
    2. Update metadata: total_checked += 1
    3. Gọi save_seen_data() để lưu
    
    TODO 11: Return results
    1. Nếu có new_notifications:
       - Print số lượng tin mới
       - Sort notifications theo ID (mới nhất trước)
       - Return list
    2. Nếu không có tin mới:
       - Print message
       - Return None
    
    Tips:
    - Dùng multiple try/except blocks cho từng phần
    - Login error và API error nên handle riêng
    - response.raise_for_status() để check HTTP errors
    """
    # TODO: Implement ở đây
    pass


# ============================================================
# PART 4: BONUS - Helper functions (Optional)
# ============================================================

def get_stats() -> Dict:
    """
    BONUS TODO: Lấy thống kê về seen data (để debug)
    
    1. Load seen_data
    2. Return dict với:
       - total_seen_ids: len(seen_ids)
       - window_size: từ metadata
       - last_check: từ last_check_time
       - total_checks: từ metadata
    
    Dùng để debug: print(get_stats())
    """
    # TODO: Implement nếu muốn có debug info
    pass


def reset_seen_data() -> None:
    """
    BONUS TODO: Reset file seen_notifications.json
    
    Dùng khi muốn test lại từ đầu
    Xóa file hoặc ghi đè với empty data
    """
    # TODO: Implement nếu cần reset
    pass


# ============================================================
# TESTING - Uncomment để test từng function riêng
# ============================================================

if __name__ == "__main__":
    # Case 1: Ít hơn WINDOW_SIZE (5)
    seen = set(['100', '99', '98'])  # 3 IDs
    new = ['101']                     # Thêm 1
    result = maintain_rolling_window(seen, new)
    print(result)  # ❌ None! (Expected: set(['100','99','98','101']))

    # Case 2: Vượt WINDOW_SIZE
    seen = set(['100', '99', '98', '97', '96'])  # 5 IDs
    new = ['101']                                 # Thêm 1 → total 6
    result = maintain_rolling_window(seen, new)
    print(result)  # ✅ OK: set(['101','100','99','98','97'])
    
    # Test 2: Rolling Window
    # print("\nTest 2: Rolling Window")
    # seen = set(['100', '99', '98'])
    # new = ['101', '102']
    # result = maintain_rolling_window(seen, new)
    # print(f"Result: {result}")
    
    # Test 3: Full check
    # print("\nTest 3: Full Check")
    # result = check_for_update()
    # print(f"New notifications: {result}")
    

                
    
