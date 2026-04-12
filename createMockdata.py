import os
import random
from PIL import Image, ImageDraw, ImageFont


def generate_test_images(folder="test_data", num_scenes=20):
    os.makedirs(folder, exist_ok=True)

    # dùng font mặc định (an toàn nhất)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    for scene in range(1, num_scenes + 1):
        for option in [1, 2]:
            img = Image.new("RGB", (1280, 720), color=random_color())
            draw = ImageDraw.Draw(img)

            text = f"Scene {scene} - Option {option}"

            # căn giữa text
            text_w, text_h = draw.textbbox((0, 0), text, font=font)[2:]
            x = (1280 - text_w) // 2
            y = (720 - text_h) // 2

            draw.text((x, y), text, fill="white", font=font)

            # vẽ shape random
            for _ in range(5):
                x1 = random.randint(0, 1000)
                y1 = random.randint(0, 600)
                x2 = x1 + random.randint(50, 200)
                y2 = y1 + random.randint(50, 200)
                draw.rectangle([x1, y1, x2, y2], outline=random_color(), width=3)

            filename = f"{scene}_{option}.jpg"
            img.save(os.path.join(folder, filename))

    print(f"✅ Generated {num_scenes*2} images in '{folder}'")


def random_color():
    return (
        random.randint(50, 255),
        random.randint(50, 255),
        random.randint(50, 255)
    )


# chạy thử
if __name__ == "__main__":
    generate_test_images("test_data", num_scenes=20)