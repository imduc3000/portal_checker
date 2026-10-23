import os
import json
from typing import List, Dict

import requests
from dotenv import load_dotenv

def check_for_update() -> List[Dict] | None: 
    load_dotenv()

    header = os.getenv("HEADERS")
    login_url = os.getenv("LOGIN_URL")
    api_url = os.getenv("API_URL")
    username = os.getenv("PORTAL_USERNAME")
    password = os.getenv("PORTAL_PASSWORD")


    session = requests.Session()
    session.headers.update ({
        "User-Agent": header
    })

    payload = {
        'user': username,
        'pass': password
    }

    try:
        response = session.post(login_url, data=payload, timeout=20)
        response.raise_for_status()

        response_data = response.json() #return result & url as dict. 

        if "url" in response_data:
            print("Login Successfully!")
            session.get(response_data["url"], timeout=20).raise_for_status() # Url contains token to login.
            
        else:
            raise RuntimeError("Portal login failed")
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError("Portal login request failed") from None
       
    try:
        api_response = session.get(api_url, timeout=10)
        api_response.raise_for_status()

        api_data = api_response.json()
        if not isinstance(api_data, list):
            raise RuntimeError('Unexpected Portal response')
        new_notifications = []

        for item in api_data:
            if not isinstance(item, dict) or item.get('id') is None:
                raise RuntimeError('Invalid announcement ID')
            item_id = str(item['id'])

            new_notifications.append({
                'id': item_id,
                'title': item['tieuDe'],
                'summary': item['tomTatNoiDung'],
                'link': item['link'],
                'date': item['ngayDang']
            })

        if new_notifications:
            print(f"Fetched '{len(new_notifications)}' current notifications!")
            return new_notifications
        else:
            print(f"Found 0 new notifications!")
            return None

    except requests.exceptions.RequestException as e:
        raise RuntimeError("Portal API request failed") from None
    except json.JSONDecodeError as e:
        raise RuntimeError("Portal returned invalid JSON") from None



if __name__ == "__main__":
    from delivery import run
    raise SystemExit(run(check_for_update))
