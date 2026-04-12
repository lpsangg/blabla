import os
import cv2
import numpy as np
import random
import subprocess
import tempfile
from pydub import AudioSegment

def generate_test_video_with_audio(folder="test_videos", num_scenes=20, duration_sec=2, fps=24):
    """Generate test videos with different audio per scene and option"""
    os.makedirs(folder, exist_ok=True)
    
    width, height = 1280, 720
    total_frames = duration_sec * fps
    
    print("🎬 Generating test videos with audio...")
    
    for scene in range(1, num_scenes + 1):
        for option in [1, 2]:
            filename = f"{scene}_{option}.mp4"
            video_path = os.path.join(folder, filename)
            audio_path = os.path.join(tempfile.gettempdir(), f"audio_{scene}_{option}.wav")
            output_path = os.path.join(folder, f"temp_{scene}_{option}.mp4")
            
            print(f"  📹 Scene {scene} - Option {option}...", end=" ", flush=True)
            
            # ===== CREATE VIDEO =====
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            
            color = random_color()
            
            for frame_idx in range(total_frames):
                frame = np.full((height, width, 3), color, dtype=np.uint8)
                
                # TEXT
                text = f"Scene {scene} - Option {option}"
                cv2.putText(
                    frame, text, (100, 350),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                    (255, 255, 255), 3, cv2.LINE_AA
                )
                
                # Moving rectangle
                x = int((frame_idx * 10 + random.randint(0, 50)) % width)
                y = int((frame_idx * 5 + random.randint(0, 50)) % height)
                cv2.rectangle(frame, (x, y), (x + 200, y + 100),
                            random_color(), 3)
                
                out.write(frame)
            
            out.release()
            
            # ===== CREATE AUDIO =====
            # Generate different audio for each option
            if option == 1:
                # Left option: Low frequency tone (150 Hz)
                audio = generate_tone_audio(frequency=150, duration_ms=int(duration_sec*1000))
            else:
                # Right option: High frequency tone (600 Hz)
                audio = generate_tone_audio(frequency=600, duration_ms=int(duration_sec*1000))
            
            # Add variation based on scene
            variation_db = -12 + (scene % 5) * 2  # -12 to -2 dB
            audio = audio.apply_gain(variation_db)
            
            audio.export(audio_path, format="wav")
            
            # ===== COMBINE VIDEO + AUDIO =====
            try:
                ffmpeg_path = r"C:\Users\Sang\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
                cmd = [
                    ffmpeg_path, "-i", video_path, "-i", audio_path,
                    "-c:v", "copy", "-c:a", "aac",
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-y", output_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, check=False)
                
                # Replace original with audio version
                if os.path.exists(output_path):
                    os.replace(output_path, video_path)
                    print("✅")
                else:
                    print("⚠️  (ffmpeg not available)")
            except Exception as e:
                print(f"⚠️  ({e})")
            finally:
                # Cleanup temp audio
                if os.path.exists(audio_path):
                    os.remove(audio_path)
    
    print(f"\n✅ Generated {num_scenes * 2} videos with audio in '{folder}'")


def generate_tone_audio(frequency=440, duration_ms=2000, sample_rate=44100):
    """Generate pure sine wave tone using numpy"""
    duration_sec = duration_ms / 1000.0
    num_samples = int(sample_rate * duration_sec)
    
    # Generate time array
    t = np.linspace(0, duration_sec, num_samples)
    
    # Generate sine wave (amplitude: 16-bit signed int range)
    amplitude = 32767 * 0.3  # 30% volume to avoid clipping
    sine_wave = np.sin(2 * np.pi * frequency * t) * amplitude
    
    # Convert to 16-bit PCM
    sine_wave = sine_wave.astype(np.int16)
    
    # Create AudioSegment from numpy array
    audio = AudioSegment(
        sine_wave.tobytes(),
        frame_rate=sample_rate,
        sample_width=sine_wave.dtype.itemsize,
        channels=1
    )
    
    return audio


def random_color():
    """Random RGB color"""
    return (
        random.randint(50, 255),
        random.randint(50, 255),
        random.randint(50, 255)
    )


if __name__ == "__main__":
    # Generate videos with audio
    # - Left video (option 1): 150 Hz tone (low frequency, like bass)
    # - Right video (option 2): 600 Hz tone (high frequency, like treble)
    # 
    # When played through stereo headphones:
    # - Left tone goes to LEFT ear
    # - Right tone goes to RIGHT ear
    
    generate_test_video_with_audio(num_scenes=10)
    print("\n🎧 Audio Setup:")
    print("   - Left video (Option 1): 150 Hz (Low - Bass)")
    print("   - Right video (Option 2): 600 Hz (High - Treble)")
    print("   - Different volume per scene for variation")
