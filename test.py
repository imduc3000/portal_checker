from news_checker import check_for_update, save_new_id

result = check_for_update()
if result:
    print("Kết quả:", result)
    # Giả lập đã xử lý xong thì lưu lại
    save_new_id(result['news_id'])
else:
    print("Bot báo không có tin mới.")