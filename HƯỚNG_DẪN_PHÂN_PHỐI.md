# 📦 Hướng Dẫn Phân Phối App MediaSelector

## ✅ Build đã hoàn tất!

File executable đã được tạo tại: `dist\MediaSelector\`

```
dist/MediaSelector/
├── MediaSelector.exe      (5.5 MB - File chính)
├── _internal/             (Chứa tất cả dependencies)
└── [các file hỗ trợ]
```

---

## 🚀 Cách sử dụng trên máy khác

### **Bước 1: Copy thư mục MediaSelector**
- Copy toàn bộ thư mục `dist\MediaSelector\` sang máy khác
- Không cần cài Python hay môi trường ảo

### **Bước 2: Cài FFmpeg** (Cần thiết)
FFmpeg là external tool, máy khác **bắt buộc phải cài**:

**Windows (dùng winget - khuyến chỉ):**
```powershell
winget install ffmpeg
```

**Windows (dùng Chocolatey):**
```powershell
choco install ffmpeg
```

**Download thủ công:**
- Tải từ: https://ffmpeg.org/download.html
- Giải nén và thêm vào PATH

### **Bước 3: Chạy app**
- Double-click `MediaSelector.exe`
- Hoặc chạy từ PowerShell:
```powershell
.\MediaSelector.exe
```

---

## 📋 Yêu cầu hệ thống

| Yêu cầu | Chi tiết |
|---------|---------|
| OS | Windows 7+ |
| Dung lượng | ~200 MB (app + ffmpeg) |
| Python | ❌ Không cần |
| Dependencies | ✅ Đã gồm trong _internal |
| FFmpeg | ✅ Cần cài riêng |

---

## 🎮 Các phím tắt

| Phím | Chức năng |
|------|----------|
| **1 / 2** | Chọn lựa chọn trái / phải |
| **Space** | Tiếp theo scene |
| **Esc** | Thoát app |
| **Drag progress bar** | Tìm đến thời điểm khác |
| **L 🔊 / R 🔊** | Tắt/bật âm trái / phải |

---

## ⚙️ Cách cập nhật app

1. Chỉnh sửa code trong `hehehe.py`
2. Build lại bằng:
```powershell
pyinstaller --name MediaSelector --onedir --windowed --hidden-import=tkinter --hidden-import=PIL --hidden-import=cv2 --hidden-import=pydub hehehe.py
```
3. Copy thư mục `dist\MediaSelector\` mới sang máy khác

---

## 🐛 Troubleshooting

### ❌ "ffmpeg not found"
**Giải pháp:** Cài ffmpeg và thêm vào PATH:
- Windows: Tải từ ffmpeg.org, thêm vào System Variables
- Hoặc cài qua winget (tự động thêm PATH)

### ❌ App không mở
- Kiểm tra antivirus (có thể chặn executable)
- Chạy PowerShell as Administrator
- Kiểm tra Windows Defender SmartScreen

### ❌ "Cannot find Python"
→ Đây là dấu hiệu build thành công! App không cần Python.

---

## 💡 Tips

- Có thể rename `MediaSelector.exe` thành tên khác
- Thư mục `_internal` không nên xoá hoặc di chuyển
- Để portable hơn, copy cả thư mục vào USB
- Có thể tạo shortcut trên Desktop/Start Menu

---

**Version:** 1.0  
**Ngày build:** 2026-04-12  
**Size:** 5.5 MB + ffmpeg (~50 MB)
