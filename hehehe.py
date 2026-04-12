import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import subprocess
import tempfile
from pydub import AudioSegment
import threading
import time
import logging
from pathlib import Path


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output folder will be created inside the selected source folder

# ===== UTILITY FUNCTIONS =====
def find_ffmpeg():
    """Find ffmpeg executable in system PATH or common locations"""
    # Check common Windows locations
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Users\Sang\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"Found ffmpeg at: {path}")
            return path
    
    # Try to find in system PATH
    try:
        result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.strip().split('\n')[0]
            logger.info(f"Found ffmpeg in PATH: {ffmpeg_path}")
            return ffmpeg_path
    except:
        pass
    
    logger.warning("FFmpeg not found!")
    return None

def find_ffplay():
    """Find ffplay executable"""
    common_paths = [
        r"C:\ffmpeg\bin\ffplay.exe",
        r"C:\Users\Sang\AppData\Local\Microsoft\WinGet\Links\ffplay.exe",
        r"C:\Program Files\ffmpeg\bin\ffplay.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffplay.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"Found ffplay at: {path}")
            return path
    
    try:
        result = subprocess.run(["where", "ffplay"], capture_output=True, text=True)
        if result.returncode == 0:
            ffplay_path = result.stdout.strip().split('\n')[0]
            logger.info(f"Found ffplay in PATH: {ffplay_path}")
            return ffplay_path
    except:
        pass
    
    logger.warning("FFplay not found!")
    return None

def validate_ffmpeg_on_startup():
    """Check if FFmpeg/FFplay are available and show warning if missing"""
    ffmpeg_path = find_ffmpeg()
    ffplay_path = find_ffplay()
    
    if not ffmpeg_path or not ffplay_path:
        logger.warning(f"Missing tools - FFmpeg: {bool(ffmpeg_path)}, FFplay: {bool(ffplay_path)}")
        
        missing = []
        if not ffmpeg_path:
            missing.append("FFmpeg")
        if not ffplay_path:
            missing.append("FFplay")
        
        message = f"⚠️ MISSING: {', '.join(missing)}\n\n"
        message += "These tools are needed for AUDIO extraction and playback.\n"
        message += "You can still SELECT videos, but AUDIO will NOT work.\n\n"
        message += "To install FFmpeg:\n"
        message += "1. Download: https://ffmpeg.org/download.html\n"
        message += "2. Extract to: C:\\ffmpeg\\\n"
        message += "3. Add to PATH or restart app\n\n"
        message += "Or use WinGet: winget install FFmpeg\n\n"
        message += "Continue anyway?"
        
        logger.warning(f"Missing FFmpeg components: {missing}")
        
        # Show warning dialog
        root_temp = tk.Tk()
        root_temp.withdraw()
        result = messagebox.askyesno(
            "⚠️ FFmpeg Not Found",
            message
        )
        root_temp.destroy()
        
        return result  # True if user clicks Yes, False if No
    
    logger.info("✅ FFmpeg and FFplay both found - audio will work")
    return True

# ===== COLORS =====
PRIMARY_BG = "#0f1419"
SECONDARY_BG = "#1a1f2e"
ACCENT_COLOR = "#00d4ff"
SUCCESS_COLOR = "#00ff88"
DANGER_COLOR = "#ff006e"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0aec0"


# ===== AUDIO MANAGER =====
class AudioExtractor:
    """Extract audio from video files"""
    
    ffmpeg_path = find_ffmpeg()
    
    @staticmethod
    def extract_audio_to_wav(video_path, output_path=None):
        """Extract audio from video to WAV file using ffmpeg"""
        if AudioExtractor.ffmpeg_path is None:
            logger.error("FFmpeg not found - cannot extract audio")
            messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg.")
            return None
            
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"audio_{int(time.time() * 1000)}.wav")
        
        try:
            cmd = [
                AudioExtractor.ffmpeg_path, "-i", video_path,
                "-q:a", "5",
                "-n",
                "-vn", output_path
            ]
            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=30, startupinfo=startupinfo)
            
            if os.path.exists(output_path):
                logger.info(f"Extracted audio to: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Audio extract error: {e}")
        
        return None
    
    @staticmethod
    def create_stereo_mix(left_audio_path, right_audio_path, output_path=None):
        """Combine 2 mono audio files into stereo (L/R channels)"""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"stereo_{int(time.time() * 1000)}.wav")
        
        try:
            # Load audio files
            left_audio = AudioSegment.from_wav(left_audio_path)
            right_audio = AudioSegment.from_wav(right_audio_path)
            
            # Ensure same length by using a silent segment to pad
            max_len = max(len(left_audio), len(right_audio))
            silence = AudioSegment.silent(duration=1)  # 1ms silence
            
            if len(left_audio) < max_len:
                # Pad left audio with silence
                diff = max_len - len(left_audio)
                padding = AudioSegment.silent(duration=diff)
                left_audio = left_audio + padding
            
            if len(right_audio) < max_len:
                # Pad right audio with silence
                diff = max_len - len(right_audio)
                padding = AudioSegment.silent(duration=diff)
                right_audio = right_audio + padding
            
            # Create stereo by panning left and right, then overlaying
            left_stereo = left_audio.set_channels(1).pan(-1.0)  # Hard left
            right_stereo = right_audio.set_channels(1).pan(1.0)  # Hard right
            
            # Overlay (mix) the two channels
            stereo_mix = left_stereo.overlay(right_stereo)
            stereo_mix.export(output_path, format="wav")
            
            return output_path
        except Exception as e:
            print(f"Stereo mix error: {e}")
            return None


class AudioPlayer:
    """Play stereo audio with ffplay"""
    
    ffplay_path = find_ffplay()
    temp_files = []  # Track temp files for cleanup
    
    def __init__(self):
        self.process = None
        self.is_playing = False
        self.current_audio_path = None
    
    def play(self, audio_path):
        """Play audio file using ffplay"""
        try:
            if not self.ffplay_path:
                logger.error("FFplay not found")
                return
                
            if self.process:
                self.stop()
            
            logger.info(f"Playing audio: {audio_path}")
            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            self.process = subprocess.Popen(
                [self.ffplay_path, "-nodisp", "-autoexit", audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )
            self.is_playing = True
            self.current_audio_path = audio_path
        except Exception as e:
            logger.error(f"Audio play error: {e}")
    
    def stop(self):
        """Stop audio playback"""
        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.is_playing = False
                self.process = None
                logger.info("Audio stopped")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop()
    
    @staticmethod
    def cleanup_temp_files():
        """Clean up temporary audio files"""
        for temp_file in AudioPlayer.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.error(f"Error cleaning temp file {temp_file}: {e}")
        AudioPlayer.temp_files.clear()

class ImagePickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Media Production - Professional Selector")

        # FULLSCREEN
        self.root.attributes("-fullscreen", True)

        # DATA
        self.source_dir = None
        self.image_cache = {}
        self.active_videos = {}
        self.move_history = []  # Track moved files for undo
        self.temp_audio_files = set()  # Track temp audio files
        
        # Statistics tracking
        self.scenes_completed = 0  # Scenes where user made selection
        self.scenes_skipped = 0    # Scenes user skipped
        self.start_time = None     # When processing started
        self.total_scenes = 0      # Total scenes to process
        
        # Two separate audio players for left/right channels
        self.audio_player_left = AudioPlayer()
        self.audio_player_right = AudioPlayer()
        self.current_audio_left = None
        self.current_audio_right = None

        # UI
        self.root.config(bg=PRIMARY_BG)

        # ===== HEADER =====
        self.create_header()

        # ===== MAIN CONTENT =====
        self.image_container = tk.Frame(root, bg=PRIMARY_BG)
        self.image_container.pack(expand=True, fill="both", padx=40, pady=40)

        # Cleanup on exit
        self.output_dir = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # KEY BINDINGS
        self.root.bind("<Key>", self.handle_keypress)
        
        # CRITICAL: Check FFmpeg/FFplay on startup
        self.root.after(100, self.check_ffmpeg_on_startup)
    
    def check_ffmpeg_on_startup(self):
        """Validate FFmpeg/FFplay at startup"""
        if not validate_ffmpeg_on_startup():
            logger.error("User cancelled app due to missing FFmpeg")
            messagebox.showinfo("Exit", "App will close. Please install FFmpeg to use audio features.")
            self.root.quit()
            return
        
        # Continue with normal flow
        self.choose_folder()
    
    def on_closing(self):
        """Clean up resources before closing"""
        logger.info("Closing application...")
        try:
            self.audio_player_left.cleanup()
            self.audio_player_right.cleanup()
            AudioPlayer.cleanup_temp_files()
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        self.root.destroy()

    # =========================
    # HEADER
    # =========================
    def create_header(self):
        header = tk.Frame(self.root, bg=SECONDARY_BG, height=100)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Left content
        left_content = tk.Frame(header, bg=SECONDARY_BG)
        left_content.pack(side="left", fill="both", expand=True, padx=30, pady=20)

        # Title
        title = tk.Label(
            left_content, text="Chời ơi cứu tuiiii",
            font=("Segoe UI", 28, "bold"), bg=SECONDARY_BG, fg=ACCENT_COLOR
        )
        title.pack(anchor="w")

        # Status
        self.status_label = tk.Label(
            left_content, text="Chọn thư mục để bắt đầu",
            font=("Segoe UI", 12), bg=SECONDARY_BG, fg=TEXT_SECONDARY
        )
        self.status_label.pack(anchor="w", pady=(5, 0))

        # Right buttons
        right_content = tk.Frame(header, bg=SECONDARY_BG)
        right_content.pack(side="right", padx=30, pady=20)

        # Undo button
        self.btn_undo = self.create_button(
            right_content, "↶ Undo", self.undo_last_move,
            bg="#ff9500", fg="#000000"
        )
        self.btn_undo.pack(side="left", padx=10)
        self.btn_undo.config(state="disabled")

        self.btn_select = self.create_button(
            right_content, "📁 Chọn Thư Mục", self.choose_folder,
            bg="#00d4ff", fg="#000000"
        )
        self.btn_select.pack(side="left", padx=10)

    # =========================
    # HELPER: CREATE BUTTON
    # =========================
    def create_button(self, parent, text, command, bg=None, fg=None):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg or ACCENT_COLOR, fg=fg or "#000000",
            font=("Segoe UI", 11, "bold"),
            padx=20, pady=12, relief="flat", bd=0,
            cursor="hand2",
            activebackground="#00a8cc" if bg == ACCENT_COLOR else bg,
            activeforeground=fg or "#000000"
        )
        return btn

    # =========================
    # FOLDER SELECTION
    # =========================
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục ảnh/video")
        if not folder:
            logger.info("No folder selected")
            return

        self.source_dir = folder
        logger.info(f"Selected source folder: {folder}")
        
        # Create output folders inside the selected folder
        self.images_output_dir = os.path.join(folder, "images_selected")
        self.videos_output_dir = os.path.join(folder, "video_selected")

        # RESET OUTPUT folders
        for output_dir in [self.images_output_dir, self.videos_output_dir]:
            if os.path.exists(output_dir):
                try:
                    shutil.rmtree(output_dir)
                    logger.info(f"Removed existing output folder: {output_dir}")
                except Exception as e:
                    logger.error(f"Error removing folder {output_dir}: {e}")
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output folder: {output_dir}")
            except Exception as e:
                logger.error(f"Error creating folder {output_dir}: {e}")
                messagebox.showerror("Error", f"Cannot create output folder: {e}")
                return

        self.current_scene_idx = 0
        self.image_cache = {}
        self.move_history = []
        self.btn_undo.config(state="disabled")
        
        # Reset statistics
        self.scenes_completed = 0
        self.scenes_skipped = 0
        self.start_time = time.time()  # Start tracking time

        self.init_data()

    def init_data(self):
        try:
            self.scenes = self.load_and_group_files()
            self.scene_ids = sorted(self.scenes.keys())
            self.total_scenes = len(self.scene_ids)
            
            logger.info(f"Loaded {self.total_scenes} scenes")

            if not self.scene_ids:
                logger.error("No files found in selected folder")
                messagebox.showerror("Lỗi", "Không tìm thấy file!")
                return

            self.display_current_scene()
        except Exception as e:
            logger.error(f"Error initializing data: {e}")
            messagebox.showerror("Error", f"Error loading files: {e}")

    # =========================
    # LOAD FILE
    # =========================
    def load_and_group_files(self):
        files = [f for f in os.listdir(self.source_dir)
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov', '.avi'))]

        groups = {}
        for f in files:
            try:
                sid = int(f.split('_')[0])
                groups.setdefault(sid, []).append(f)
            except:
                continue
        return groups

    def is_video(self, path):
        return path.lower().endswith(('.mp4', '.mov', '.avi'))

    # =========================
    # PLAY VIDEO IN LABEL
    # =========================
    def play_video_in_label(self, path, video_container):
        """Phát video lặp lại với progress bar modern & time display"""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            lbl = tk.Label(video_container, text="❌ Video Error", fg=DANGER_COLOR, bg="black",
                          font=("Segoe UI", 14, "bold"))
            lbl.pack(expand=True, fill="both")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration_sec = total_frames / fps if fps > 0 else 0

        # Video display
        lbl = tk.Label(video_container, bg="black")
        lbl.pack(expand=True, fill="both")

        # ===== CONTROL BAR =====
        ctrl_frame = tk.Frame(video_container, bg=SECONDARY_BG, height=60)
        ctrl_frame.pack(fill="x", padx=0, pady=0)
        ctrl_frame.pack_propagate(False)

        # Left: Time display
        time_var = tk.StringVar(value="00:00 / 00:00")
        time_label = tk.Label(
            ctrl_frame, textvariable=time_var,
            font=("Segoe UI", 10, "bold"), fg=TEXT_SECONDARY, bg=SECONDARY_BG,
            width=12
        )
        time_label.pack(side="left", padx=12, pady=12)

        # Middle: Modern progress bar
        progress_var = tk.DoubleVar()
        
        progress = tk.Scale(
            ctrl_frame, from_=0, to=total_frames or 100,
            orient="horizontal", variable=progress_var,
            bg=SECONDARY_BG, fg=ACCENT_COLOR, 
            troughcolor=PRIMARY_BG,
            relief="flat", bd=0, highlightthickness=0,
            activebackground=ACCENT_COLOR, 
            cursor="hand2",
            takefocus=True
        )
        progress.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        # Bind click event to progress bar for seeking
        def on_progress_click(event):
            # Get click position and convert to frame number
            width = progress.winfo_width()
            click_x = event.x
            ratio = max(0, min(1, click_x / width))
            frame_num = int(ratio * (total_frames or 100))
            progress_var.set(frame_num)
            self.seek_video(cap, frame_num)
        
        progress.bind("<Button-1>", on_progress_click)
        progress.bind("<B1-Motion>", on_progress_click)

        # Right: Mute buttons for Left and Right audio
        mute_state_left = {"muted": False}
        mute_state_right = {"muted": False}

        def toggle_mute_left():
            mute_state_left["muted"] = not mute_state_left["muted"]
            icon = "🔇" if mute_state_left["muted"] else "🔊"
            mute_btn_left.config(text=f"L {icon}")
            
            if mute_state_left["muted"]:
                self.audio_player_left.stop()
            else:
                if self.current_audio_left and os.path.exists(self.current_audio_left):
                    def play_audio():
                        self.audio_player_left.play(self.current_audio_left)
                    audio_thread = threading.Thread(target=play_audio, daemon=True)
                    audio_thread.start()

        def toggle_mute_right():
            mute_state_right["muted"] = not mute_state_right["muted"]
            icon = "🔇" if mute_state_right["muted"] else "🔊"
            mute_btn_right.config(text=f"R {icon}")
            
            if mute_state_right["muted"]:
                self.audio_player_right.stop()
            else:
                if self.current_audio_right and os.path.exists(self.current_audio_right):
                    def play_audio():
                        self.audio_player_right.play(self.current_audio_right)
                    audio_thread = threading.Thread(target=play_audio, daemon=True)
                    audio_thread.start()

        mute_btn_left = tk.Button(
            ctrl_frame, text="L 🔊", command=toggle_mute_left,
            font=("Segoe UI", 11),
            bg=ACCENT_COLOR, fg="#000000",
            relief="flat", bd=0, highlightthickness=0,
            activebackground="#00a8cc", activeforeground="#000000",
            padx=10, pady=8, cursor="hand2"
        )
        mute_btn_left.pack(side="right", padx=6, pady=12)

        mute_btn_right = tk.Button(
            ctrl_frame, text="R 🔊", command=toggle_mute_right,
            font=("Segoe UI", 11),
            bg=ACCENT_COLOR, fg="#000000",
            relief="flat", bd=0, highlightthickness=0,
            activebackground="#00a8cc", activeforeground="#000000",
            padx=10, pady=8, cursor="hand2"
        )
        mute_btn_right.pack(side="right", padx=6, pady=12)

        # Store data
        self.active_videos[lbl] = {
            "cap": cap,
            "muted_left": mute_state_left,
            "muted_right": mute_state_right,
            "progress": progress_var,
            "total_frames": total_frames,
            "fps": fps,
            "time_label": time_label,
            "duration_sec": duration_sec,
            "is_dragging": False
        }

        def format_time(seconds):
            """Convert seconds to MM:SS format"""
            mins = int(seconds) // 60
            secs = int(seconds) % 60
            return f"{mins:02d}:{secs:02d}"
        
        # Bind drag events
        def on_drag_start(event):
            self.active_videos[lbl]["is_dragging"] = True
            # Stop audio khi bắt đầu drag
            if not mute_state_left["muted"]:
                self.audio_player_left.stop()
            if not mute_state_right["muted"]:
                self.audio_player_right.stop()
        
        def on_drag_motion(event):
            self.active_videos[lbl]["is_dragging"] = True
            width = progress.winfo_width()
            click_x = event.x
            ratio = max(0, min(1, click_x / width))
            frame_num = int(ratio * (total_frames or 100))
            progress_var.set(frame_num)
            self.seek_video(cap, frame_num)
            # Update frame immediately while dragging
            immediate_update_frame()
        
        def on_drag_release(event):
            self.active_videos[lbl]["is_dragging"] = False
            # Restart audio khi release, sync với vị trí video hiện tại
            current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            offset_sec = current_frame / fps if fps > 0 else 0
            
            # Restart left audio if not muted
            if not mute_state_left["muted"] and self.current_audio_left:
                try:
                    from pydub import AudioSegment as AS
                    audio = AS.from_wav(self.current_audio_left)
                    trimmed_audio = audio[int(offset_sec * 1000):]
                    
                    # Export trimmed audio tạm thời
                    temp_audio = os.path.join(tempfile.gettempdir(), f"trim_L_{int(time.time() * 1000)}.wav")
                    trimmed_audio.export(temp_audio, format="wav")
                    
                    # Play từ offset
                    def play_offset_left():
                        self.audio_player_left.play(temp_audio)
                    audio_thread = threading.Thread(target=play_offset_left, daemon=True)
                    audio_thread.start()
                except:
                    pass  # Nếu trim failed, bỏ qua
            
            # Restart right audio if not muted
            if not mute_state_right["muted"] and self.current_audio_right:
                try:
                    from pydub import AudioSegment as AS
                    audio = AS.from_wav(self.current_audio_right)
                    trimmed_audio = audio[int(offset_sec * 1000):]
                    
                    # Export trimmed audio tạm thời
                    temp_audio = os.path.join(tempfile.gettempdir(), f"trim_R_{int(time.time() * 1000)}.wav")
                    trimmed_audio.export(temp_audio, format="wav")
                    
                    # Play từ offset
                    def play_offset_right():
                        self.audio_player_right.play(temp_audio)
                    audio_thread = threading.Thread(target=play_offset_right, daemon=True)
                    audio_thread.start()
                except:
                    pass  # Nếu trim failed, bỏ qua
        
        def immediate_update_frame():
            """Update frame immediately without waiting for loop"""
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            if ret:
                frame = cv2.resize(frame, (800, 480))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(img)
                
                lbl.config(image=imgtk)
                lbl.image = imgtk
                
                current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
                progress_var.set(current_frame)
                
                current_sec = current_frame / fps if fps > 0 else 0
                time_text = f"{format_time(current_sec)} / {format_time(duration_sec)}"
                time_var.set(time_text)
        
        progress.bind("<Button-1>", on_drag_start)
        progress.bind("<B1-Motion>", on_drag_motion)
        progress.bind("<ButtonRelease-1>", on_drag_release)

        def update_frame():
            if lbl not in self.active_videos:
                cap.release()
                return

            # Skip frame advance if user is dragging
            if not self.active_videos[lbl]["is_dragging"]:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    return self.root.after(30, update_frame)

                frame = cv2.resize(frame, (800, 480))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(img)

                lbl.config(image=imgtk)
                lbl.image = imgtk

            current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            progress_var.set(current_frame)
            
            # Update time display
            current_sec = current_frame / fps if fps > 0 else 0
            time_text = f"{format_time(current_sec)} / {format_time(duration_sec)}"
            time_var.set(time_text)

            self.root.after(30, update_frame)

        update_frame()

    def seek_video(self, cap, frame_num):
        """Seek video to frame"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

    # =========================
    # AUDIO SETUP
    # =========================
    def setup_stereo_audio(self, left_video_path, right_video_path):
        """Setup and play stereo audio from 2 videos (L/R channels) - INDEPENDENTLY"""
        try:
            logger.info(f"Setting up stereo audio: L={left_video_path}, R={right_video_path}")
            
            # Extract audio files
            left_audio = AudioExtractor.extract_audio_to_wav(left_video_path)
            right_audio = AudioExtractor.extract_audio_to_wav(right_video_path)
            
            if not left_audio or not right_audio:
                error_msg = "Could not extract audio from videos. "
                if not AudioExtractor.ffmpeg_path:
                    error_msg += "FFmpeg not found - please install it."
                else:
                    error_msg += "Check if video files are valid."
                logger.warning(error_msg)
                print(f"⚠️  {error_msg}")
                messagebox.showwarning("Audio Error", error_msg)
                return
            
            # Track temp files
            self.temp_audio_files.add(left_audio)
            self.temp_audio_files.add(right_audio)
            
            # Store paths for independent playback
            self.current_audio_left = left_audio
            self.current_audio_right = right_audio
            
            # Play both independently in background threads
            def play_left():
                self.audio_player_left.play(left_audio)
            
            def play_right():
                self.audio_player_right.play(right_audio)
            
            thread_left = threading.Thread(target=play_left, daemon=True)
            thread_right = threading.Thread(target=play_right, daemon=True)
            thread_left.start()
            thread_right.start()
            logger.info(f"🎧 Audio playing independently")
            print(f"🎧 Audio playing independently")
        
        except Exception as e:
            logger.error(f"Audio setup error: {e}")
            print(f"Audio setup error: {e}")

    # =========================
    # DISPLAY
    # =========================
    def display_current_scene(self):
        # Stop all active videos
        for lbl, data in list(self.active_videos.items()):
            try:
                data["cap"].release()
            except Exception as e:
                logger.error(f"Error releasing video: {e}")
        self.active_videos.clear()

        for w in self.image_container.winfo_children():
            w.destroy()

        if self.current_scene_idx >= len(self.scene_ids):
            stats = self._get_stats_text()
            self.status_label.config(text=stats)
            logger.info("All scenes completed!")
            return

        sid = self.scene_ids[self.current_scene_idx]
        options = sorted(self.scenes[sid])

        # Calculate progress stats
        stats_text = self._get_stats_text()
        self.status_label.config(text=stats_text)

        self.current_options_paths = []

        # Create scrollable frame for >2 items
        if len([f for f in options if os.path.exists(os.path.join(self.source_dir, f))]) > 2:
            # Scrollable UI for >2 files
            parent_frame = tk.Frame(self.image_container, bg=PRIMARY_BG)
            parent_frame.pack(expand=True, fill="both")
            
            canvas = tk.Canvas(parent_frame, bg=PRIMARY_BG, highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
            scrollbar.pack(side="right", fill="y")
            
            canvas.config(yscrollcommand=scrollbar.set)
            
            frame = tk.Frame(canvas, bg=PRIMARY_BG)
            canvas.create_window(0, 0, window=frame, anchor="nw")
            
            # Grid for scrollable items
            for i, fname in enumerate(options):
                path = os.path.join(self.source_dir, fname)
                
                if not os.path.exists(path):
                    continue
                    
                self.current_options_paths.append(path)

                card = tk.Frame(frame, bg=SECONDARY_BG, width=850, height=520)
                card.pack(pady=20, padx=25, fill="both", expand=True)

                if self.is_video(path):
                    try:
                        video_container = tk.Frame(card, bg="black", height=520, width=850)
                        video_container.pack(expand=True, fill="both", padx=0, pady=0)
                        self.play_video_in_label(path, video_container)
                    except Exception as e:
                        logger.error(f"Error playing video {fname}: {e}")
                else:
                    try:
                        if path not in self.image_cache:
                            img = Image.open(path)
                            img = img.resize((800, 480), Image.Resampling.LANCZOS)
                            self.image_cache[path] = ImageTk.PhotoImage(img)
                        
                        img_tk = self.image_cache[path]
                        lbl = tk.Label(card, image=img_tk, bg=SECONDARY_BG)
                        lbl.image = img_tk
                        lbl.pack(expand=True, fill="both", padx=0, pady=0)
                    except Exception as e:
                        logger.error(f"Error loading image {fname}: {e}")
            
            frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))
        else:
            # Normal grid for 2 files
            frame = tk.Frame(self.image_container, bg=PRIMARY_BG)
            frame.pack(expand=True, fill="both")

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=0)
            frame.grid_columnconfigure(2, weight=0)
            frame.grid_columnconfigure(3, weight=1)
            frame.grid_rowconfigure(0, weight=1)

            for i, fname in enumerate(options):
                path = os.path.join(self.source_dir, fname)
                
                if not os.path.exists(path):
                    continue
                    
                self.current_options_paths.append(path)

                card = tk.Frame(frame, bg=SECONDARY_BG)
                card.grid(row=0, column=i+1, padx=25, pady=25, sticky="nsew")

                if self.is_video(path):
                    try:
                        video_container = tk.Frame(card, bg="black", height=520, width=850)
                        video_container.pack(expand=True, fill="both", padx=0, pady=0)
                        self.play_video_in_label(path, video_container)
                    except Exception as e:
                        logger.error(f"Error playing video {fname}: {e}")
                else:
                    try:
                        if path not in self.image_cache:
                            img = Image.open(path)
                            img = img.resize((800, 480), Image.Resampling.LANCZOS)
                            self.image_cache[path] = ImageTk.PhotoImage(img)

                        img_tk = self.image_cache[path]
                        lbl = tk.Label(card, image=img_tk, bg=SECONDARY_BG)
                        lbl.image = img_tk
                        lbl.pack(expand=True, fill="both", padx=0, pady=0)
                    except Exception as e:
                        logger.error(f"Error loading image {fname}: {e}")
        
        # Setup stereo audio if both are videos (in background to avoid lag)
        if len(self.current_options_paths) == 2:
            left_path, right_path = self.current_options_paths
            if self.is_video(left_path) and self.is_video(right_path):
                self.audio_player_left.stop()
                self.audio_player_right.stop()
                self.status_label.config(text=f"Scene {sid} • ⏳ Đang tải audio...")
                
                def load_audio_bg():
                    try:
                        self.setup_stereo_audio(left_path, right_path)
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"Scene {sid} • {self.current_scene_idx+1}/{len(self.scene_ids)}"
                        ))
                    except Exception as e:
                        logger.error(f"Background audio load error: {e}")
                
                audio_thread = threading.Thread(target=load_audio_bg, daemon=True)
                audio_thread.start()

    # =========================
    # UNDO FEATURE
    # =========================
    def undo_last_move(self):
        """Undo last moved file"""
        if not self.move_history:
            messagebox.showinfo("Info", "Nothing to undo")
            return
        
        try:
            src_path, dst_path = self.move_history.pop()
            if os.path.exists(dst_path):
                shutil.move(dst_path, src_path)
                logger.info(f"Undid move: {dst_path} → {src_path}")
                messagebox.showinfo("Success", f"Undo successful: {os.path.basename(src_path)}")
                self.display_current_scene()  # Refresh display
            
            # Update undo button state
            self.btn_undo.config(state="normal" if self.move_history else "disabled")
        except Exception as e:
            logger.error(f"Undo error: {e}")
            messagebox.showerror("Error", f"Undo failed: {e}")
    
    # =========================
    # SELECT FILE
    # =========================
    def select_file(self, path):
        try:
            # Check if we've finished all scenes
            if self.current_scene_idx >= len(self.scene_ids):
                messagebox.showinfo("Done", "✅ All scenes processed!")
                logger.info("All scenes completed")
                return
            
            # Track completion
            self.scenes_completed += 1
            
            sid = self.scene_ids[self.current_scene_idx]

            ext = os.path.splitext(path)[1]
            new_name = f"Scene {sid}{ext}"

            # Determine output folder based on file type
            if self.is_video(path):
                output_folder = self.videos_output_dir
                file_type = "video"
            else:
                output_folder = self.images_output_dir
                file_type = "image"

            dst_path = os.path.join(output_folder, new_name)

            # CRITICAL: Release any active video captures BEFORE moving file
            # This prevents "file in use by another process" error
            if self.is_video(path):
                logger.info(f"Releasing video captures before moving: {path}")
                for lbl, data in list(self.active_videos.items()):
                    try:
                        if data.get("cap"):
                            data["cap"].release()
                            logger.info(f"Released video capture for label")
                    except:
                        pass
                self.active_videos.clear()

            if os.path.exists(dst_path):
                os.remove(dst_path)

            # Track move for undo
            self.move_history.append((path, dst_path))
            self.btn_undo.config(state="normal")
            
            # Move file (faster than copy) and rename
            shutil.move(path, dst_path)
            logger.info(f"✅ Scene {sid} → moved {file_type} to {dst_path}")
            print(f"✅ Scene {sid} → moved {file_type} & renamed to {new_name}")

        except Exception as e:
            logger.error(f"Error selecting file: {e}")
            print(f"Lỗi: {e}")
            messagebox.showerror("Error", f"Failed to move file: {e}")

        self.next_scene()

    def next_scene(self):
        self.current_scene_idx += 1
        # Check if we've finished all scenes
        if self.current_scene_idx >= len(self.scene_ids):
            logger.info("All scenes have been processed")
            final_stats = self._get_final_stats()
            messagebox.showinfo("Complete", final_stats)
            self.root.quit()
            return
        self.display_current_scene()
    
    def _get_stats_text(self):
        """Generate formatted statistics text for status bar"""
        # Current position
        current_pos = self.current_scene_idx + 1
        total = self.total_scenes
        
        # Calculate speed (seconds per scene)
        if self.start_time and self.scenes_completed > 0:
            elapsed = time.time() - self.start_time
            speed = elapsed / self.scenes_completed
            speed_text = f"{speed:.1f}s"
        else:
            speed_text = "--s"
        
        # Calculate remaining time estimate
        if self.start_time and self.scenes_completed > 0:
            elapsed = time.time() - self.start_time
            speed_per_scene = elapsed / self.scenes_completed
            remaining_scenes = total - self.current_scene_idx
            remaining_time = remaining_scenes * speed_per_scene
            remaining_text = f" | ⏱️ ETA: {int(remaining_time)}s" if remaining_time > 0 else ""
        else:
            remaining_text = ""
        
        # Format: "Scene 5/120 | ✅ 4 done | Speed: 12.5s" + ETA
        return f"Scene {current_pos}/{total} | ✅ {self.scenes_completed} processed | 🚀 Speed: {speed_text}{remaining_text}"
    
    def _get_final_stats(self):
        """Generate final statistics when done"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = elapsed / self.scenes_completed if self.scenes_completed > 0 else 0
        
        return (
            f"✅ HOÀN THÀNH!\n\n"
            f"📊 Thống kê:\n"
            f"  • Tổng scenes: {self.total_scenes}\n"
            f"  • Đã xử lý: {self.scenes_completed}\n"
            f"  • Thời gian: {int(elapsed)}s\n"
            f"  • Tốc độ: {speed:.1f}s/scene"
        )

    # =========================
    # KEYBOARD
    # =========================
    def handle_keypress(self, event):
        try:
            if not hasattr(self, 'current_options_paths') or not self.current_options_paths:
                logger.debug(f"Key pressed but no options available: {event.keysym}")
                return

            if event.char in ['1', '2', '3']:
                idx = int(event.char) - 1
                if idx < len(self.current_options_paths):
                    logger.info(f"Selected option: {idx+1}")
                    self.select_file(self.current_options_paths[idx])
                else:
                    logger.warning(f"Option {idx+1} out of range")

            elif event.keysym == "space":
                logger.info("Next scene")
                self.next_scene()

            elif event.keysym == "Escape":
                logger.info("Escape pressed - closing app")
                self.on_closing()
        except Exception as e:
            logger.error(f"Error in keypress handler: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePickerApp(root)
    root.mainloop()