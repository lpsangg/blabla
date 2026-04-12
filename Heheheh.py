import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk


SOURCE_DIR = None
SELECTED_DIR = "images_selected"


class ImagePickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Media Production - Fullscreen Selector")

        # 1. MỞ FULL SCREEN
        self.root.attributes("-fullscreen", True)
        # self.root.state("zoomed")

        self.root.update()
        screen_height = self.root.winfo_height()
        self.image_display_height = int(screen_height * 0.75)


        # Nền tối + gradient dịu mắt
        self.root.config(bg="#181c24")

        # Canvas gradient nền
        self.bg_canvas = tk.Canvas(root, width=1920, height=1080, highlightthickness=0, bd=0)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.draw_gradient()

        # Top bar with status (left) and persistent controls (right)
        top_bar = tk.Frame(root, bg="#232a36")
        top_bar.pack(fill="x")

        left_bar = tk.Frame(top_bar, bg="#232a36")
        left_bar.pack(side="left", fill="x", expand=True)
        right_bar = tk.Frame(top_bar, bg="#232a36")
        right_bar.pack(side="right")

        self.status_label = tk.Label(left_bar, text="Chọn thư mục chứa ảnh để bắt đầu", font=("Arial", 16, "bold"), pady=12, bg="#232a36", fg="white", anchor="w")
        self.status_label.pack(fill="x", padx=12)
        self.action_label = tk.Label(left_bar, text="", font=("Arial", 12), pady=6, bg="#232a36", fg="#f1c40f", anchor="w")
        self.action_label.pack(fill="x", padx=12)

        self.image_container = tk.Frame(root, bg="#181c24")
        self.image_container.pack(expand=True, fill="both")

        # Main action area and persistent controls
        self.button_frame = tk.Frame(root, pady=18, bg="#181c24")
        self.button_frame.pack()

        # Persistent controls (Import Actions) that should persist across scenes - placed in top right
        self.persistent_button_frame = tk.Frame(right_bar, pady=10, bg="#232a36")
        self.persistent_button_frame.pack()

        # Nút chọn folder
        # Styled primary button
        self.select_folder_btn = tk.Button(self.button_frame, text="Chọn thư mục ảnh...", command=self.choose_folder, font=("Arial", 13, "bold"), bg="#27ae60", fg="white", padx=28, pady=10, activebackground="#145a32", bd=0, relief="flat")
        self.select_folder_btn.pack()
    def draw_gradient(self):
        # Gradient dọc từ #232a36 (trên) sang #181c24 (dưới)
        h = self.root.winfo_screenheight()
        w = self.root.winfo_screenwidth()
        steps = 100
        for i in range(steps):
            color = self._blend_color("#232a36", "#181c24", i/steps)
            self.bg_canvas.create_rectangle(0, i*h//steps, w, (i+1)*h//steps, outline="", fill=color)

    def _blend_color(self, c1, c2, t):
        # c1, c2: hex, t: 0..1
        def hex2rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def rgb2hex(rgb):
            return '#%02x%02x%02x' % rgb
        r1,g1,b1 = hex2rgb(c1)
        r2,g2,b2 = hex2rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return rgb2hex((r,g,b))

        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def choose_folder(self):
        global SOURCE_DIR
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if folder:
            SOURCE_DIR = folder
            self.select_folder_btn.destroy()
            self.init_app_after_folder()

    def init_app_after_folder(self):
        # Chuẩn bị dữ liệu
        self.scenes = self.load_and_group_files()
        self.scene_ids = sorted(self.scenes.keys())
        self.current_scene_idx = 0
        self.notes = []
        self._overlay = None
        self.scene_actions = {}

        if not self.scene_ids:
            messagebox.showerror("Lỗi", "Không tìm thấy ảnh!")
            self.root.destroy()
            return

        if not os.path.exists(SELECTED_DIR):
            os.makedirs(SELECTED_DIR)

        # Bind phím tắt
        self.root.bind("<Key>", self.handle_keypress)

        # Nút persistent để dán hoặc load actions (Góc máy & Hành động)
        import_btn = tk.Button(self.persistent_button_frame, text="Dán Góc máy & Hành động", command=self.import_actions_overlay, font=("Arial", 11, "bold"), bg="#8e44ad", fg="white", padx=12, pady=6, bd=0, relief="flat")
        import_btn.pack(side="left", padx=8)

        # Improve appearance of skip button and other primary buttons by centralizing style
        self._primary_btn_style = {"font": ("Arial", 12, "bold"), "bg": "#c0392b", "fg": "white", "bd": 0, "relief": "flat", "padx": 18, "pady": 8}

        self.display_current_scene()

    def load_and_group_files(self):
        global SOURCE_DIR
        if not SOURCE_DIR:
            return {}
        files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        groups = {}
        for f in files:
            try:
                sid = int(f.split('_')[0])
                if sid not in groups:
                    groups[sid] = []
                groups[sid].append(f)
            except:
                continue
        return groups

    def display_current_scene(self):
        # Xóa các widget cũ
        for widget in self.image_container.winfo_children():
            widget.destroy()
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if self.current_scene_idx >= len(self.scene_ids):
            # Khi duyệt xong, hiện tóm tắt các ghi chú (nếu có) trên overlay
            self.show_notes_summary()
            return

        sid = self.scene_ids[self.current_scene_idx]
        options = sorted(self.scenes[sid])
        num = len(options)
        
        self.status_label.config(text=f"SCENE: {sid} | Tiến độ: {self.current_scene_idx + 1}/{len(self.scene_ids)}")
        # Hiển thị hành động tương ứng (nếu có)
        action_text = self.scene_actions.get(sid, "")
        self.action_label.config(text=(action_text if action_text else ""))

        # --- LOGIC TÍNH TOÁN GRID ---
        # 1. Xác định số hàng và cột
        if num == 1:
            rows, cols = 1, 1
        else:
            cols = 2
            rows = (num + 1) // 2

        # 2. Lấy kích thước vùng chứa thực tế (trừ đi lề)
        self.root.update()
        avail_w = self.root.winfo_width() - 60  # Trừ lề trái phải
        avail_h = self.root.winfo_height() - 220 # Trừ tiêu đề và cụm nút dưới

        # Kích thước tối đa cho mỗi "ô" (cell) trong Grid
        cell_w = avail_w // cols
        cell_h = avail_h // rows

        # --- Tạo Grid Wrapper ---
        grid_wrapper = tk.Frame(self.image_container, bg="#181c24")
        grid_wrapper.pack(expand=True, fill="both")
        
        # Cấu hình để các cột luôn giãn đều
        for c in range(cols):
            grid_wrapper.grid_columnconfigure(c, weight=1)
        for r in range(rows):
            grid_wrapper.grid_rowconfigure(r, weight=1)

        self.current_options_paths = []

        for i, fname in enumerate(options):
            path = os.path.join(SOURCE_DIR, fname)
            self.current_options_paths.append(path)
            
            try:
                img_pill = Image.open(path)
                orig_w, orig_h = img_pill.size
                aspect = orig_w / orig_h

                # TÍNH TOÁN KÍCH THƯỚC ẢNH ĐỂ FILL ĐẦY Ô (CELL)
                # Giả định nút bấm và text chiếm khoảng 60px chiều cao trong mỗi ô
                max_img_h = cell_h - 80 
                max_img_w = cell_w - 40

                # Fit ảnh vào kích thước ô mà vẫn giữ tỷ lệ
                if (max_img_w / aspect) <= max_img_h:
                    new_w = max_img_w
                    new_h = int(max_img_w / aspect)
                else:
                    new_h = max_img_h
                    new_w = int(max_img_h * aspect)

                img_pill = img_pill.resize((new_w, new_h), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_pill)

                # Tạo Frame cho mỗi Option
                frame = tk.Frame(grid_wrapper, bg="#232a36", highlightbackground="#232a36", highlightthickness=2)
                
                # Xác định vị trí Grid
                curr_row = i // 2
                curr_col = i % 2
                
                # Nếu là ảnh cuối cùng và tổng số ảnh là số lẻ (3, 5, 7...)
                if i == num - 1 and num % 2 != 0 and num > 1:
                    # Cho phép chiếm 2 cột để nằm giữa
                    frame.grid(row=curr_row, column=0, columnspan=2, sticky="nsew")
                else:
                    frame.grid(row=curr_row, column=curr_col, sticky="nsew")

                # Nội dung bên trong Frame (Ảnh + Nút)
                lbl_img = tk.Label(frame, image=img_tk, bd=2, relief="groove", bg="#232a36")
                lbl_img.image = img_tk
                lbl_img.pack(expand=True)

                btn = tk.Button(frame, text=f"CHỌN {i+1} (Phím {i+1})",
                                command=lambda p=path: self.select_image(p),
                                font=("Arial", 12, "bold"), bg="#2980b9", fg="white",
                                activebackground="#154360", activeforeground="white",
                                width=15, pady=5, bd=0, highlightthickness=0)
                btn.pack(pady=5)

            except Exception as e:
                print(f"Lỗi hiển thị ảnh {fname}: {e}")

        # Nút chức năng dưới cùng
        skip_btn = tk.Button(self.button_frame, text="BỎ QUA (Space)",
                 command=self.next_scene, activebackground="#922b21", activeforeground="white",
                 **self._primary_btn_style)
        skip_btn.pack(side="left", padx=10)
    def select_image(self, path):
        # Determine current scene id safely before advancing index
        sid = None
        if hasattr(self, 'scene_ids') and 0 <= self.current_scene_idx < len(self.scene_ids):
            sid = self.scene_ids[self.current_scene_idx]

        try:
            shutil.copy(path, SELECTED_DIR)
        except Exception as e:
            print(f"Không thể sao chép {path}: {e}")

        if sid is not None:
            print(f"Lưu Scene {sid}")
        else:
            print(f"Lưu file {os.path.basename(path)} (scene unknown)")

        self.next_scene()

    def next_scene(self):
        self.current_scene_idx += 1
        self.display_current_scene()

    def handle_keypress(self, event):
        # Ignore keypresses if we've finished all scenes
        if hasattr(self, 'scene_ids') and self.current_scene_idx >= len(self.scene_ids):
            return
        if event.char in ['1', '2', '3', '4', '5']:
            idx = int(event.char) - 1
            if idx < len(self.current_options_paths):
                self.select_image(self.current_options_paths[idx])
        elif event.keysym == 'space':
            self.next_scene()
        elif event.keysym in ('Return', 'KP_Enter'):
            # Ghi chú cho scene hiện tại (khi không có option phù hợp)
            self.show_input_overlay()

    def show_input_overlay(self):
        # Nếu đã có overlay đang mở thì trả về
        if self._overlay is not None:
            return
        if not hasattr(self, 'scene_ids') or not self.scene_ids:
            return
        if self.current_scene_idx >= len(self.scene_ids):
            return
        sid = self.scene_ids[self.current_scene_idx]

        # Tạo overlay trên chính root (không tạo cửa sổ mới)
        overlay = tk.Frame(self.root, bg="#000000", bd=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        self._overlay = overlay

        # Semi-panel ở giữa để nhập
        panel = tk.Frame(overlay, bg="#2b2f3a", bd=2, relief="raised")
        panel.place(relx=0.5, rely=0.4, anchor="center", relwidth=0.6, relheight=0.18)

        lbl = tk.Label(panel, text=f"Ghi chú cho Scene {sid}", font=("Arial", 14, "bold"), bg="#2b2f3a", fg="white")
        lbl.pack(fill="x", pady=(8, 4))

        entry_var = tk.StringVar()
        entry = tk.Entry(panel, textvariable=entry_var, font=("Arial", 12))
        entry.pack(fill="x", padx=12, pady=(0, 8))
        entry.focus_set()

        btn_frame = tk.Frame(panel, bg="#232a36")
        btn_frame.pack(fill="x", pady=(0, 8))

        def submit_from_entry(event=None):
            text = entry_var.get().strip()
            if text:
                self.notes.append((sid, text))
            self.close_input_overlay()
            self.next_scene()
            # Prevent the Return key event from propagating to root (avoid reopening overlay)
            return "break"

        def cancel_overlay():
            self.close_input_overlay()

        submit_btn = tk.Button(btn_frame, text="Lưu & Tiếp", command=submit_from_entry, bg="#27ae60", fg="white", bd=0, relief="flat", padx=12, pady=6)
        submit_btn.pack(side="left", padx=8)
        cancel_btn = tk.Button(btn_frame, text="Hủy", command=cancel_overlay, bg="#c0392b", fg="white", bd=0, relief="flat", padx=12, pady=6)
        cancel_btn.pack(side="left", padx=8)

        entry.bind('<Return>', submit_from_entry)

    def import_actions_overlay(self):
        # Overlay để dán/nhập danh sách actions (một dòng mỗi scene)
        if self._overlay is not None:
            return
        overlay = tk.Frame(self.root, bg="#000000", bd=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        self._overlay = overlay

        panel = tk.Frame(overlay, bg="#2b2f3a", bd=2, relief="raised")
        panel.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.8, relheight=0.6)

        lbl = tk.Label(panel, text="Dán/Load Góc máy & Hành động (mỗi dòng tương ứng 1 Scene)", font=("Arial", 13, "bold"), bg="#2b2f3a", fg="white")
        lbl.pack(fill="x", pady=(8, 4))

        txt = tk.Text(panel, wrap="word", font=("Arial", 11), bg="#f7f9fa")
        txt.pack(fill="both", expand=True, padx=12, pady=6)

        ctrl_frame = tk.Frame(panel, bg="#2b2f3a")
        ctrl_frame.pack(fill="x", pady=(0, 8))

        def apply_actions():
            content = txt.get("1.0", "end").strip()
            if not content:
                messagebox.showwarning("Không có dữ liệu", "Vui lòng dán hoặc load dữ liệu trước khi áp dụng.")
                return
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            applied = 0
            # Map lines to scenes in order
            for i, sid in enumerate(self.scene_ids):
                if i < len(lines):
                    self.scene_actions[sid] = lines[i]
                    applied += 1
                else:
                    break
            messagebox.showinfo("Hoàn tất", f"Đã áp dụng {applied} dòng cho {len(self.scene_ids)} scene.")
            self.close_input_overlay()
            # refresh current header
            self.display_current_scene()

        def load_file():
            path = filedialog.askopenfilename(title="Chọn file text", filetypes=[("Text files", "*.txt;*.csv;*.tsv"), ("All files", "*")])
            if not path:
                return
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
                txt.delete('1.0', 'end')
                txt.insert('1.0', data)
            except Exception as e:
                messagebox.showerror("Lỗi đọc file", str(e))

        apply_btn = tk.Button(ctrl_frame, text="Áp dụng (map theo thứ tự)", command=apply_actions, bg="#27ae60", fg="white")
        apply_btn.pack(side="left", padx=6)
        load_btn = tk.Button(ctrl_frame, text="Load từ file", command=load_file, bg="#2980b9", fg="white")
        load_btn.pack(side="left", padx=6)
        cancel_btn = tk.Button(ctrl_frame, text="Hủy", command=self.close_input_overlay, bg="#c0392b", fg="white")
        cancel_btn.pack(side="left", padx=6)

    def close_input_overlay(self):
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None

    def show_notes_summary(self):
        if not getattr(self, 'notes', None):
            return
        # Tạo overlay chứa bảng log
        overlay = tk.Frame(self.root, bg="#000000", bd=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        self._overlay = overlay

        panel = tk.Frame(overlay, bg="#ffffff", bd=2, relief="ridge")
        panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)

        header = tk.Frame(panel, bg="#2c3e50")
        header.pack(fill="x")
        h1 = tk.Label(header, text="STT", bg="#2c3e50", fg="white", width=6, font=("Arial", 10, "bold"))
        h1.pack(side="left")
        h2 = tk.Label(header, text="Notes", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        h2.pack(side="left", fill="x", expand=True)

        # Scrollable area
        canvas = tk.Canvas(panel, bg="white")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=inner, anchor='nw')

        summary_lines = []
        for idx, (sid, note) in enumerate(self.notes, start=1):
            row = tk.Frame(inner, bg="white")
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(1, weight=1)
            row.pack(fill="x", padx=4, pady=2)

            # STT column shows the Scene ID (small)
            lbl_idx = tk.Label(row, text=str(sid), bg="white", width=6, anchor="w", font=("Arial", 9))
            lbl_idx.grid(row=0, column=0, sticky="w")
            lbl_note = tk.Label(row, text=f"{note}", bg="white", anchor="w", justify="left", wraplength=800, font=("Arial", 10))
            lbl_note.grid(row=0, column=1, sticky="w")
            # Use tab separator so Excel pastes into two cells (STT and Notes)
            summary_lines.append(f"{sid}\t{note}")

        def _on_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", _on_config)

        # Close only the overlay; keep the app open so user can continue or inspect files
        summary = "\n".join(summary_lines)

        copy_btn = tk.Button(panel, text="Sao chép", command=lambda: self.copy_notes_to_clipboard(summary), bg="#16a085", fg="white")
        copy_btn.pack(side="left", padx=8, pady=8)

        action_frame = tk.Frame(panel, bg="#ffffff")
        action_frame.pack(side="bottom", pady=8)

        restart_btn = tk.Button(action_frame, text="Chọn thư mục khác", command=lambda: self.choose_folder_and_restart(overlay), bg="#2980b9", fg="white")
        restart_btn.pack(side="left", padx=8)

        exit_btn = tk.Button(action_frame, text="Thoát", command=lambda: (overlay.destroy(), self.root.destroy()), bg="#c0392b", fg="white")
        exit_btn.pack(side="left", padx=8)

    def copy_notes_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Sao chép", "Đã sao chép log vào clipboard")
        except Exception as e:
            print(f"Không thể sao chép vào clipboard: {e}")

    def choose_folder_and_restart(self, overlay=None):
        # Allow user to pick a new folder and restart the session
        global SOURCE_DIR
        folder = filedialog.askdirectory(title="Chọn thư mục ảnh để tiếp tục")
        if not folder:
            return
        SOURCE_DIR = folder
        # close overlay if present
        if overlay:
            try:
                overlay.destroy()
            except:
                pass
            self._overlay = None

        # Reinitialize data and UI
        self.scenes = self.load_and_group_files()
        self.scene_ids = sorted(self.scenes.keys())
        self.current_scene_idx = 0
        self.notes = []
        self.scene_actions = {}

        if not self.scene_ids:
            messagebox.showerror("Lỗi", "Không tìm thấy ảnh trong thư mục đã chọn!")
            return

        if not os.path.exists(SELECTED_DIR):
            os.makedirs(SELECTED_DIR)

        # Ensure keybinding is active
        self.root.bind("<Key>", self.handle_keypress)
        self.display_current_scene()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePickerApp(root)
    root.mainloop()