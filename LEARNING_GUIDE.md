# 📚 Learning Guide - Portal Checker Project

## 🎯 Mục tiêu
Tự implement Rolling Window approach để track notifications, tránh duplicate

## 📝 Roadmap Implementation

### Phase 1: File I/O (TODO 1-4) ⭐ START HERE
**Kiến thức cần học:**
- Python file operations: `open()`, `read()`, `write()`
- JSON: `json.load()`, `json.dump()`
- Exception handling: `try/except/finally`
- Python data types: `dict`, `list`, `set`

**Resources:**
- [Python JSON Tutorial](https://docs.python.org/3/library/json.html)
- [Python File I/O](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files)
- [Python Sets](https://docs.python.org/3/tutorial/datastructures.html#sets)

**Checklist:**
- [ ] TODO 1: Implement `load_seen_data()` - Load JSON file
- [ ] TODO 2: Handle FileNotFoundError và JSONDecodeError
- [ ] TODO 3: Implement `save_seen_data()` - Save dict to JSON
- [ ] TODO 4: Handle IO exceptions

**Testing:**
```python
# Test code (uncomment trong main block):
data = load_seen_data()
print(f"Loaded: {data}")
save_seen_data(data)
print("✅ Phase 1 Done!")
```

---

### Phase 2: Rolling Window Logic (TODO 5) 
**Kiến thức cần học:**
- Set operations: `.update()`, `.add()`, `.remove()`
- List comprehensions
- `sorted()` function với `key` parameter
- Lambda functions

**Resources:**
- [Python Set Methods](https://docs.python.org/3/tutorial/datastructures.html#sets)
- [Sorting HOW TO](https://docs.python.org/3/howto/sorting.html)
- [Lambda Functions](https://realpython.com/python-lambda/)

**Checklist:**
- [ ] TODO 5: Implement `maintain_rolling_window()`
  - [ ] Thêm IDs mới vào set
  - [ ] Check size và trim nếu cần
  - [ ] Sort by ID (largest first)
  - [ ] Return updated set

**Testing:**
```python
# Test rolling window
seen = set(['100', '99', '98'])
new = ['101', '102', '97']
result = maintain_rolling_window(seen, new)
print(f"Result should have 101,102,100,99,98,97: {result}")
print(f"✅ Phase 2 Done!")
```

---

### Phase 3: Main Logic (TODO 6-11) 
**Kiến thức cần học:**
- `requests` library: Session, POST, GET
- HTTP status codes và error handling
- List comprehensions và filtering
- Membership testing: `in` operator với set

**Resources:**
- [Requests Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
- [Python dotenv](https://pypi.org/project/python-dotenv/)
- [List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)

**Checklist:**
- [ ] TODO 6: Load environment variables
- [ ] TODO 7: Setup session và login
  - [ ] Create Session
  - [ ] POST login
  - [ ] Handle authentication URL
- [ ] TODO 8: Fetch API data
  - [ ] GET request với timeout
  - [ ] Parse JSON
  - [ ] Check empty response
- [ ] TODO 9: Find new notifications
  - [ ] Loop qua items
  - [ ] Check membership với `not in`
  - [ ] Build notification dict
- [ ] TODO 10: Update và save
- [ ] TODO 11: Return results

**Testing:**
```python
# Full test
result = check_for_update()
if result:
    print(f"✅ Found {len(result)} new notifications!")
else:
    print("✅ No new notifications (or first run)")
print("✅ Phase 3 Done!")
```

---

### Phase 4: Bonus Features (Optional)
**Checklist:**
- [ ] Implement `get_stats()` - Debug helper
- [ ] Implement `reset_seen_data()` - Testing helper
- [ ] Add logging instead of print statements
- [ ] Add retry logic for API calls
- [ ] Add config validation

---

## 🐛 Debugging Tips

### Problem: FileNotFoundError
**Solution:** Check nếu file chưa tồn tại → return default dict

### Problem: JSONDecodeError
**Solution:** File bị corrupt → delete và recreate

### Problem: TypeError: Object of type set is not JSON serializable
**Solution:** Convert set → list trước khi save

### Problem: Login failed
**Solution:** Check .env file, verify credentials

### Problem: All notifications marked as "new" every time
**Solution:** Check nếu save_seen_data() được gọi đúng chỗ

---

## 📊 Testing Strategy

### 1. Unit Tests (Test từng function riêng)
```python
# Test load/save
data = load_seen_data()
assert 'seen_ids' in data
assert isinstance(data['seen_ids'], set)

# Test rolling window
result = maintain_rolling_window(set(['1','2']), ['3','4'])
assert len(result) == 4
```

### 2. Integration Test (Test flow hoàn chỉnh)
```python
# Lần 1: Nên mark tất cả là seen
result1 = check_for_update()
print(f"First run: {result1}")

# Lần 2: Không nên có tin mới
result2 = check_for_update()
print(f"Second run (should be None): {result2}")
```

### 3. Edge Cases
- File không tồn tại
- API trả về empty array
- API trả về >150 notifications
- Network timeout
- Invalid JSON format

---

## 🎓 Concepts to Understand

### Why Set instead of List?
```python
# List: O(n) lookup
'145677' in ['145677', '145676', ...]  # Slow

# Set: O(1) lookup  
'145677' in {'145677', '145676', ...}  # Fast! ⚡
```

### Why Rolling Window?
- File size không tăng vô hạn
- Performance ổn định (O(1) lookup)
- Không phụ thuộc timestamp server

### JSON vs Plain Text
```python
# Plain text: Khó parse
145677
145676

# JSON: Dễ parse, có structure
{
  "seen_ids": ["145677", "145676"],
  "metadata": {...}
}
```

---

## 🚀 Next Steps After Completion

1. **Add logging:** Replace `print()` với `logging` module
2. **Add tests:** Viết unit tests với `pytest`
3. **Add retry:** Retry khi API call fails
4. **Add metrics:** Track success rate, average response time
5. **Deploy:** Schedule chạy định kỳ với cron/systemd

---

## 💡 Questions to Ask Yourself

- [ ] Tại sao dùng set thay vì list cho seen_ids?
- [ ] Điều gì xảy ra nếu WINDOW_SIZE = 10 và portal push 100 tin mới?
- [ ] Làm sao handle khi script bị crash giữa chừng?
- [ ] Có cách nào tối ưu hơn maintain_rolling_window()?
- [ ] Khi nào nên dùng timestamp thay vì rolling window?

---

## 📞 When You're Stuck

1. **Read error messages carefully** - Python errors rất rõ ràng
2. **Print debug info** - `print(type(variable))`, `print(len(variable))`
3. **Test từng phần nhỏ** - Đừng code hết rồi mới test
4. **Google the right keywords** - "python set update", "json load file"
5. **Ask for hints** - Không sao cả, quan trọng là hiểu!

---

## ✅ Success Criteria

Bạn hoàn thành project khi:
- [ ] Code chạy không lỗi
- [ ] File seen_notifications.json được tạo đúng format
- [ ] Lần chạy đầu không spam notifications
- [ ] Lần chạy thứ 2 không có tin mới (nếu portal không update)
- [ ] Khi có tin mới thực sự, detect được
- [ ] File size không tăng vô hạn (luôn ~WINDOW_SIZE IDs)
- [ ] **Quan trọng nhất: Bạn HIỂU từng dòng code mình viết**

---

## 🎉 Final Note

Đừng copy-paste code từ Internet! Hãy:
1. Đọc TODO
2. Nghĩ cách giải quyết
3. Tự viết code
4. Test và debug
5. Học từ mistakes

**Good luck! Bạn làm được! 💪**
