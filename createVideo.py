import os
import cv2
import numpy as np
import random


def generate_test_videos(folder="test_videos", num_scenes=20, duration_sec=2, fps=24):
    os.makedirs(folder, exist_ok=True)

    width, height = 1280, 720
    total_frames = duration_sec * fps

    for scene in range(1, num_scenes + 1):
        for option in [1, 2]:

            filename = f"{scene}_{option}.mp4"
            path = os.path.join(folder, filename)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(path, fourcc, fps, (width, height))

            color = random_color()

            for frame_idx in range(total_frames):
                frame = np.full((height, width, 3), color, dtype=np.uint8)

                # TEXT
                text = f"Scene {scene} - Option {option}"
                cv2.putText(
                    frame,
                    text,
                    (100, 350),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.5,
                    (255, 255, 255),
                    3,
                    cv2.LINE_AA
                )

                # random rectangle moving
                x = int((frame_idx * 10 + random.randint(0, 50)) % width)
                y = int((frame_idx * 5 + random.randint(0, 50)) % height)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + 200, y + 100),
                    random_color(),
                    3
                )

                out.write(frame)

            out.release()

    print(f"✅ Generated {num_scenes * 2} videos in '{folder}'")


def random_color():
    return (
        random.randint(50, 255),
        random.randint(50, 255),
        random.randint(50, 255)
    )


# RUN TEST
if __name__ == "__main__":
    generate_test_videos(num_scenes=10)