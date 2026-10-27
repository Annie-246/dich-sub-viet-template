---
name: dich-sub-viet-template
description: Từ một link video (YouTube/X/...) tự tải, bóc băng, dịch phụ đề tiếng Việt chạy theo lời gốc (chữ vàng, viền đen, có bóng) rồi đặt video lên template vuông 1254x1254 nền trắng lưới + tiêu đề hook cam/đen Inter Black. Dùng khi người dùng gửi link video nước ngoài và nói "dịch sub Việt", "làm video phụ đề Việt", "đặt vào template dịch và chèn phụ đề". Làm trọn từ link đến file mp4, không hỏi duyệt giữa chừng.
---

# dich-sub-viet-template — link video -> video vuông có phụ đề Việt + hook

Người dùng chỉ gửi link. **Tự làm trọn từ tải về đến mp4**, xong mới báo. Trả lời bằng tiếng Việt.

`SK` = thư mục gốc của skill này (đường dẫn ở dòng "Base directory for this skill" khi skill được nạp).
Mỗi video một folder `runs/<yy.mm.dd-ten>/` **trong thư mục làm việc hiện tại** (không ghi vào thư mục skill):
`source.mp4, segs.json, transcript.txt, events.json, hook.json, sub.ass, frame.png, final.mp4, check.png`.
Mẫu `events.json` / `hook.json` đã chạy thật: `SK/examples/elon-musk-job/`.

## Bước 0 — kiểm tra máy (lần đầu dùng, hoặc khi lệnh lỗi)
```bash
python "$SK/scripts/dubsub.py" doctor
```
Có dòng `MISSING` thì dừng, báo người dùng thiếu gì và cách bổ sung:
- `ffmpeg` / `ffprobe`: Windows `winget install Gyan.FFmpeg` · macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg`. Cài xong mở lại terminal / Claude Code.
- `yt-dlp`, thư viện Python: hỏi người dùng rồi cài giúp `python -m pip install yt-dlp faster-whisper pillow`.
Lần đầu `transcribe`, faster-whisper tải model `small` (~500 MB) — báo trước.

## Quy trình

```bash
python "$SK/scripts/dubsub.py" fetch "<link>" --out runs/<yy.mm.dd-ten>
python "$SK/scripts/dubsub.py" transcribe runs/<yy.mm.dd-ten> --lang en      # in transcript có mốc từng từ
# Claude tự viết runs/<...>/events.json và hook.json (xem dưới)
python "$SK/scripts/dubsub.py" build runs/<yy.mm.dd-ten>                     # -> final.mp4 + check.png
```
Windows: thêm `PYTHONIOENCODING=utf-8` trước `python` nếu in tiếng Việt bị lỗi `cp1252`.

1. **fetch** — yt-dlp tải tối đa 1080p thành `source.mp4`. Nếu người dùng đưa đường dẫn file thay vì link thì truyền đường dẫn đó, script sẽ copy vào. In ra kích thước và fps; giữ nguyên fps nguồn (script tự làm).
2. **transcribe** — faster-whisper `small.en`, in từng câu kèm mốc từng từ (`từ@giây`). Video không phải tiếng Anh thì đổi `--lang`.
3. **Viết `events.json`** — danh sách `{"start","end","text"}` tiếng Việt:
   - Mốc **bắt đầu = từ đầu tiên của cụm**; mốc **kết thúc = từ cuối + ~0,3 s**, KHÔNG lấy `end` của câu. Whisper kéo dài từ cuối qua khoảng im (vd "think" 8,7→10,0 dù chỉ nói ~0,4 s), nên nhìn mốc từng từ để cắt ở chỗ nghỉ > ~0,8 s thành 2 cụm riêng.
   - Bỏ tiếng đệm vô nghĩa ("yeah", "all right, yeah", "you" ở cuối) và đoạn người dẫn chương trình nếu không thuộc ý chính.
   - Dịch văn nói tự nhiên, câu ngắn, không dịch từng chữ kiểu Anh→Việt. Mỗi cụm ≤ ~65 ký tự (script tự ngắt tối đa 2 dòng, mỗi dòng ≤ 38).
   - Kiểm tra số liệu/tên riêng đúng với bản chép lời.
4. **Đọc lại toàn bộ nội dung**, rồi:
   - Gợi ý 4–5 hook gây sốc, xếp từ mạnh nhất. Bám lời người nói; nếu là suy ra (vd "mất việc") thì nói rõ là suy ra.
   - **Hook số 1 dùng luôn làm tiêu đề** trong `hook.json`.
5. **Viết `hook.json`** — mảng dòng, mỗi dòng là mảng `[chữ, màu]`, màu `"k"` đen / `"o"` cam, xen kẽ (tên người: đen; ý chính: cam; từ nhấn: đen). Ví dụ:
   ```json
   [[["Elon Musk: ","k"],["5 năm nữa, AI","o"]], [["thông minh hơn ","o"],["toàn nhân loại","k"]]]
   ```
   - Ưu tiên **2 dòng** (≈ ≤ 31 ký tự/dòng ở cỡ 67); 3 dòng cũng được nếu hook dài, script tự co cỡ chữ cho vừa bề ngang và dịch khối chữ lên. Chia dòng sao cho không bị lẻ 1 từ ("hơn" một mình ở dòng 2 trông xấu).
   - Rút gọn hook cho vừa thì phải báo người dùng đã đổi chữ nào.
6. **build** — dựng, rồi **Read `check.png`** để soi: tiêu đề không chạm video, phụ đề trong khung, viền cam. Sửa `events.json`/`hook.json` rồi build lại nếu lệch. Xem thêm 1–2 khung ở giây khác nếu video có đổi cảnh.
7. Báo người dùng đường dẫn `final.mp4` kèm danh sách hook đã gợi ý.

## Thông số

| Hạng mục | Giá trị |
|---|---|
| Khung | 1254×1254, nền `assets/template-nen-sach.png` |
| Tiêu đề | Inter Black cỡ 67, dòng cách 81 px, căn giữa, cam `(220,117,79)` + đen `(24,24,30)` |
| Video 16:9 | rộng full 1254×705 tại y=354, viền cam 3 px `#DC754F`. Nguồn 4:3 trở lên thì giới hạn cao 880, y=290 |
| Phụ đề | Inter Bold 44, vàng `#FFD700`, viền đen 4, bóng 4, ở đáy khung video (cách đáy ~28 px) |
| fps | giữ fps nguồn (vd 29.97) |

## Bẫy đã vấp

- **Chữ Anh in sẵn trong video gốc** (phụ đề của nguồn) nằm ngay trên phụ đề Việt. Không đè nhau nhưng sát; nếu rối thì báo người dùng, đừng tự che.
- **ffmpeg `subtitles=` trên Windows**: đường dẫn có `D:` bị libass hiểu sai. Script chạy ffmpeg với `cwd` = folder run và dùng `sub.ass` + `fontsdir=fonts` (đã copy fonts vào đó) nên đừng đổi sang đường dẫn tuyệt đối.
- **Mốc từ của whisper bị kéo dài qua khoảng im** — xem bước 3.
- Lưới nền ở vùng tiêu đề hơi đứt (chỗ đã xoá chữ cũ) nhưng chữ mới phủ gần hết.
- Hook người dùng yêu cầu có thể dài hơn 2 dòng: cứ 3 dòng, đừng cắt ý.
- Skill này không có nhạc/SFX.
