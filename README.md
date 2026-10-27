# Dịch sub Việt + template — skill Claude Code

Gửi cho Claude một link video nước ngoài (YouTube, X…), nhận về video vuông 1254×1254:
video gốc nằm giữa template nền trắng lưới, tiêu đề hook cam/đen phía trên, phụ đề tiếng Việt vàng viền đen chạy theo lời.
Claude tự tải, bóc băng, dịch, gợi ý hook và dựng — không hỏi duyệt giữa chừng.

## 1. Cài đặt — dán prompt này vào Claude Code

```
Cài giúp mình skill dich-sub-viet-template: chạy
git clone https://github.com/Annie-246/dich-sub-viet-template ~/.claude/skills/dich-sub-viet-template
Xong thì chạy "python scripts/dubsub.py doctor" trong thư mục đó để kiểm tra máy mình còn thiếu gì,
cài giúp những gì cài được và hướng dẫn mình phần còn lại.
```

Hoặc tự chạy trong terminal:

```
git clone https://github.com/Annie-246/dich-sub-viet-template ~/.claude/skills/dich-sub-viet-template
```

Cài xong **khởi động lại Claude Code** để skill được nạp.

## 2. Cần có trên máy

| Thứ cần | Cách cài |
|---|---|
| Git | git-scm.com |
| Python 3.10+ | python.org |
| ffmpeg | Windows: `winget install Gyan.FFmpeg` · macOS: `brew install ffmpeg` |
| Thư viện Python | `python -m pip install yt-dlp faster-whisper pillow` |

Không cần API key. Lần đầu bóc băng, faster-whisper tải model khoảng 500 MB.

## 3. Dùng

Trong Claude Code, mở thư mục bạn muốn chứa video rồi gõ:

```
/dich-sub-viet-template https://www.youtube.com/watch?v=...
```

Hoặc nói tự nhiên: "dịch sub Việt video này rồi đặt vào template: <link>".
Video xong nằm ở `runs/<ngày-tên>/final.mp4`, kèm 4–5 hook gợi ý (hook mạnh nhất đã dùng làm tiêu đề).

Mẫu phụ đề và hook đã chạy thật: [examples/elon-musk-job](examples/elon-musk-job).

## 4. Không nhận chỉnh sửa — muốn custom thì tự sửa bản của bạn

**Repo này không nhận chỉnh sửa từ người khác:** không nhận Pull Request, không nhận yêu cầu đổi style.

Bản bạn đã clone về máy là của bạn, cứ sửa thoải mái (đổi template nền, màu, font, cỡ chữ…). Dán prompt này vào Claude Code:

```
Mở skill ~/.claude/skills/dich-sub-viet-template, đọc SKILL.md và scripts/dubsub.py,
rồi sửa giúp mình theo ý: <mô tả thay đổi bạn muốn>.
```

## Bản quyền

- Code: MIT. Font Inter: SIL OFL 1.1.
- Video bạn tải về thuộc bản quyền của chủ kênh gốc. Đăng lại video đã dịch thì tự kiểm tra quyền sử dụng và ghi nguồn.
