# 09 · Kết nối trực tiếp Claude Code ↔ Colab qua VS Code

Cách này cho Claude Code **chạy code thẳng trên GPU Colab và đọc kết quả ngay**, không qua git.
Nó ghép hai extension chính thức:

```
VS Code
├── Claude Code (panel) ── tool mcp__ide__executeCode ──┐   chèn cell vào notebook đang mở
│                                                       ▼
└── notebooks/vscode_colab.ipynb ── kernel "Colab" ──► Colab server (GPU T4) ── output trả về cho Claude
     (file nằm ở máy bạn)                               (code chạy ở đây)
```

- **Extension Google Colab** (`google.colab`) biến một Colab server thành kernel cho notebook trong VS Code.
- **Claude Code extension** có một MCP server nội bộ tên `ide`, cung cấp tool `mcp__ide__executeCode`.
  Tool này "chạy code Python trong kernel của notebook Jupyter đang mở". Kernel đó là Colab, nên code chạy trên GPU Colab.
- **Mỗi lần chạy đều hỏi bạn.** Code được chèn thành cell mới ở cuối notebook, VS Code hiện hộp **Execute / Cancel**.
  Không có cách nào để Claude chạy ngầm. Đây là thiết kế an toàn, và cũng làm demo rất trực quan.

## Bước 0. Chuẩn bị (một lần)

| Cần | Kiểm tra / cài |
|---|---|
| VS Code có **Claude Code**, **Jupyter**, **Google Colab** | `code --list-extensions`; thiếu Colab thì `code --install-extension google.colab` |
| Tài khoản Google | Gói free dùng được GPU T4 (tùy quota lúc đó) |
| Claude Code chạy **trong VS Code** | Panel Claude Code của extension. Nếu dùng CLI trong terminal của VS Code, gõ `/ide` để nối với VS Code |

## Bước 1. Nối notebook với Colab server
1. Mở `notebooks/vscode_colab.ipynb`.
2. Góc trên phải: **Select Kernel → Colab → New Colab Server**, chọn loại máy có **GPU (T4)**.
   (Hoặc **Auto Connect** để lấy server mặc định, nhưng có thể không có GPU.)
3. Trình duyệt mở trang đăng nhập Google. Đăng nhập, cấp quyền, rồi quay lại VS Code.
4. Góc trên phải giờ hiển thị kernel Colab. Chạy **cell 1** (tự bấm ▶). Kết quả mong đợi: `Tesla T4 ...` và `cuda: True`.

## Bước 2. Đưa code lên Colab server
Máy bạn và Colab server là **hai máy khác nhau**: file trong repo chưa có trên server.
1. Explorer: chuột phải `src/` → **Upload to Colab**. Làm tương tự với `configs/` và `requirements.txt`.
   Không upload `.venv/`, `checkpoints/`, `data/`.
2. Chạy **cell 2**. Nó chuyển vào `/content` và báo "Code đã sẵn sàng", hoặc liệt kê thứ còn thiếu.
   Có thể xem file trên server ở view **Colab** trên activity bar (mục Contents).

> Repo đã lên GitHub thì có thể thay bước này bằng một cell `!git clone ...`. Với repo private, nhớ rằng
> `userdata.get()` (Secrets của Colab) **chưa được kiểm chứng** là chạy được khi kernel nối qua VS Code.
> Lúc demo, upload là cách chắc chắn nhất.

## Bước 3. Để Claude điều khiển
Bấm vào tab notebook để nó là **editor đang active**, rồi gõ vào panel Claude Code:

| Bạn nói | Claude làm |
|---|---|
| *"Chạy trong notebook đang mở: kiểm tra GPU và phiên bản torch trên Colab"* | Chèn cell `nvidia-smi` + `torch.cuda...`, bạn bấm Execute, Claude đọc và báo lại |
| *"Chạy train demo 2 epoch trên Colab rồi tóm tắt val_acc từng epoch"* | Chèn cell `python -m src.train ... --set train.epochs=2`, đọc log `[epoch 1/2] ...` |
| *"Bắt đầu train đủ 30 epoch chạy nền trên Colab"* | Chèn cell `nohup ... &` (trả về ngay) |
| *"Run nền tới đâu rồi?"* | Chèn cell `tail -n 5 /content/train.log`, đọc tiến độ |

Luồng mỗi lần chạy:
1. Claude gọi `mcp__ide__executeCode`.
2. Lần đầu, Claude Code hỏi quyền dùng tool (tùy permission mode). Chọn *"Yes, and don't ask again"* để bớt hỏi lần sau.
3. Cell mới xuất hiện cuối notebook, VS Code hiện **Execute / Cancel**.
4. Bấm **Execute**. Cell chạy trên Colab, output trả về cho Claude.
5. Bấm **Cancel** (hoặc `Esc`) thì Claude nhận lỗi và không có gì chạy.

## Bước 4. Sửa code rồi chạy lại
Khi cell báo lỗi, bạn có thể nói *"Đọc traceback ở cell vừa rồi và sửa code trong src/"*. Claude sửa file **ở máy bạn**.
Bản trên Colab chưa đổi, nên bạn cần:
- Chuột phải file hoặc thư mục đã sửa → **Upload to Colab** lần nữa, **rồi** bảo Claude chạy lại.
- Module đã được import trong kernel sẽ không tự nạp lại. Lệnh `!python -m src.train` chạy tiến trình mới nên không bị ảnh hưởng.

## Bước 5. Train dài và giữ kết quả
- Checkpoint ở `/content/ckpt` **mất khi server bị xóa** (ngắt kết nối lâu, hết quota, Remove Server).
- Muốn giữ lại: Command Palette → **Colab: Mount Google Drive to Server...**. Lệnh này thêm một cell mount Drive vào notebook.
  Chạy cell đó, rồi dùng `--ckpt-dir /content/drive/MyDrive/ckpt/<run>`.
- Cơ chế resume của `src/train.py` vẫn hoạt động: server mới, chạy lại cùng lệnh với cùng `--ckpt-dir` trên Drive là train tiếp.
- Muốn theo dõi khi đã tắt VS Code, dùng thêm `--log-branch runs` ([08](08-demo-colab-git-log.md)). Cách này cần repo trên GitHub và token có quyền ghi.

## Bước 6. Dọn dẹp
Command Palette → **Colab: Remove Server** để trả GPU (tiết kiệm quota). **Colab: Sign Out** khi dùng máy chung.

## Giới hạn cần biết
- Mỗi lần chạy phải bấm Execute: đây là thiết kế, không tắt được. Quy tắc allow cho `mcp__ide__executeCode`
  chỉ bỏ bớt câu hỏi của Claude Code, không bỏ hộp Execute/Cancel của VS Code.
- Tool chỉ chạy khi có **notebook đang active**, đã cài Jupyter extension, và kernel là Python.
- Kết nối sống khi VS Code còn mở và Colab server còn cấp. Việc train nhiều giờ không cần trông thì cách notebook + branch `runs` ([07](07-colab-kaggle.md), [08](08-demo-colab-git-log.md)) vẫn bền hơn.
- Hai bản code (local và `/content`) không tự đồng bộ.
- Quota GPU của Colab vẫn áp dụng như khi dùng trên trình duyệt.

## Lỗi thường gặp

| Triệu chứng | Xử lý |
|---|---|
| Không thấy **Colab** trong Select Kernel | Extension Google Colab chưa bật, hoặc cần *Developer: Reload Window* |
| Claude nói không có notebook nào đang mở | Bấm vào tab notebook cho nó active rồi yêu cầu lại |
| Claude không có tool chạy notebook | Đang dùng CLI ngoài VS Code. Mở panel Claude Code trong VS Code, hoặc gõ `/ide` trong terminal của VS Code |
| `cuda: False` | Server không có GPU. *Colab: Remove Server*, rồi **New Colab Server** và chọn GPU |
| `ModuleNotFoundError: No module named 'src'` | Chưa upload `src/`, hoặc chưa chạy cell 2 (`%cd /content`) |
| Sửa code rồi mà Colab vẫn chạy bản cũ | Chưa **Upload to Colab** lại file đã sửa |
