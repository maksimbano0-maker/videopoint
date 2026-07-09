from PIL import Image, ImageDraw
import numpy as np
import random
import subprocess
from pathlib import Path
import sys

def color_halftone_frame(img, dot_size=7, density=0.95, jitter=3, max_radius_factor=0.85):
    """Обрабатывает один кадр"""
    width, height = img.size
    output = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(output)
    
    pixels = np.array(img)
    step = max(1, dot_size)
    
    for y in range(0, height, step):
        for x in range(0, width, step):
            block = pixels[y:y+step, x:x+step]
            if block.size == 0:
                continue
                
            avg_color = np.mean(block, axis=(0, 1)).astype(int)
            brightness = np.mean(avg_color) / 255.0
            
            # Улучшенная формула: меньше перекрытия в тёмных областях
            radius = int(step * (1 - brightness) * density * max_radius_factor)
            radius = min(radius, int(step * 0.9))  # жёсткое ограничение
            
            if radius < 1:
                continue
            
            cx = x + step // 2 + random.randint(-jitter, jitter)
            cy = y + step // 2 + random.randint(-jitter, jitter)
            
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=tuple(avg_color)
            )
    
    return output


def process_video(input_video="Download.mp4", output_video="outcolor.mp4", 
                 dot_size=7, density=0.95, jitter=3, fps=25):
    temp_dir = Path("temp_frames")
    temp_dir.mkdir(exist_ok=True)
    
    print(f"Извлечение кадров из {input_video}...")
    subprocess.run([
        'ffmpeg', '-i', input_video, '-vf', f'fps={fps}',
        str(temp_dir / "%06d.png")
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    frame_files = sorted(temp_dir.glob("*.png"))
    total = len(frame_files)
    print(f"Найдено {total} кадров.")
    
    for i, frame_path in enumerate(frame_files):
        if i % max(10, total//15) == 0:
            print(f"Обработано {i}/{total} ({int(i/total*100)}%)")
        
        img = Image.open(frame_path).convert('RGB')
        processed = color_halftone_frame(img, dot_size, density, jitter)
        processed.save(frame_path)
    
    print("Собираем видео...")
    subprocess.run([
        'ffmpeg', '-y', '-framerate', str(fps),
        '-i', str(temp_dir / "%06d.png"),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '22',
        output_video
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for f in temp_dir.glob("*.png"):
        f.unlink()
    temp_dir.rmdir()
    
    print(f"✅ Готово! Сохранено: {output_video}")


if __name__ == "__main__":
    process_video()
    print("\nЕсли всё ещё слишком плотно уменьши density ещё сильнее.")
