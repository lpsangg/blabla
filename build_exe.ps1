# Build script để tạo .exe standalone
# Chạy script này trong PowerShell

$app_name = "MediaSelector"
$main_script = "hehehe.py"

# Tạo executable
pyinstaller --name $app_name `
    --onefile `
    --windowed `
    --icon=app.ico `
    --hidden-import=tkinter `
    --hidden-import=PIL `
    --hidden-import=cv2 `
    --hidden-import=pydub `
    --hidden-import=numpy `
    --hidden-import=pygame `
    --hidden-import=audioop `
    --collect-all=pydub `
    --collect-all=PIL `
    --distpath=".\dist" `
    --buildpath=".\build" `
    --specpath="." `
    $main_script

Write-Host "✅ Build hoàn tất! File .exe nằm tại: .\dist\$app_name.exe"
Write-Host "⚠️  Lưu ý: Máy khác phải cài ffmpeg để app chạy được!"
