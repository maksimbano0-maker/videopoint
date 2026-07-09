from PIL import Image, ImageDraw
import numpy as np
import subprocess
import os
from pathlib import Path

def process_video(input_video, output_video, dot_size=5, density=1.1, fps=30):
    # Создаём временную папку для кадров
    temp_dir = Path("temp_frames")
    temp_dir.mkdir(exist_ok=True)
    
    # Извлекаем кадры с помощью ffmpeg
    subprocess.run([
        'ffmpeg', '-i', input_video, '-vf', f'fps={fps}',
        str(temp_dir / "%06d.png")
    ], check=True)
    
    print("Обработка кадров...")
    frame_files = sorted(temp_dir.glob("*.png"))
    
    for i, frame_path in enumerate(frame_files):
        if i % 10 == 0:
            print(f"Кадр {i}/{len(frame_files)}")
        
        img = Image.open(frame_path).convert('L')
        width, height = img.size
        output = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(output)
        pixels = np.array(img)
        
        for y in range(0, height, dot_size):
            for x in range(0, width, dot_size):
                block = pixels[y:y+dot_size, x:x+dot_size]
                if block.size == 0:
                    continue
                brightness = np.mean(block) / 255.0
                radius = int(dot_size * (1 - brightness) * density * 0.85)
                if radius > 1:
                    draw.ellipse([
                        x + dot_size//2 - radius,
                        y + dot_size//2 - radius,
                        x + dot_size//2 + radius,
                        y + dot_size//2 + radius
                    ], fill=(0, 0, 0))
        
        output.save(frame_path)  # перезаписываем
    
    # Собираем обратно в видео
    subprocess.run([
        'ffmpeg', '-y', '-framerate', str(fps), '-i', str(temp_dir / "%06d.png"),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23',
        output_video
    ], check=True)
    
    # Очистка
    for f in temp_dir.glob("*.png"):
        f.unlink()
    temp_dir.rmdir()
    print(f"Готово! Видео сохранено: {output_video}")

# Использование
process_video("Download.mp4", "output_dots.mp4", dot_size=6, density=1.15)