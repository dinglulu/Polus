import os
from PIL import Image

files_to_compress = [
    "demo.png", "120.png", "115.png", "decode.png", "evaluate.png",
    "simulate.png", "encode.png", "117.png", "114.png", "116.png",
    "113.png", "112.png"
]

def compress_png_keep_quality(input_path, output_path, target_min_kb=200, target_max_kb=300):
    """压缩 PNG，保持分辨率不变，仅减少颜色数，尽量控制在 200–300KB"""
    img = Image.open(input_path)
    target_min, target_max = target_min_kb * 1024, target_max_kb * 1024

    colors = 256
    best_size = None

    while colors >= 16:
        paletted = img.convert("P", palette=Image.ADAPTIVE, colors=colors)
        paletted.save(output_path, format="PNG", optimize=True)
        size = os.path.getsize(output_path)

        if target_min <= size <= target_max:
            print(f"{os.path.basename(input_path)} -> {size/1024:.1f}KB (colors={colors})")
            return

        best_size = size
        colors //= 2  # 逐步减少颜色

    print(f"{os.path.basename(input_path)} 最终 {best_size/1024:.1f}KB (colors={colors})")

# 批量执行（当前目录）
current_dir = os.getcwd()
output_dir = os.path.join(current_dir, "compressed_png")
os.makedirs(output_dir, exist_ok=True)

for fname in files_to_compress:
    in_path = os.path.join(current_dir, fname)
    if os.path.exists(in_path):
        out_name = os.path.splitext(fname)[0] + "_compressed.png"
        out_path = os.path.join(output_dir, out_name)
        compress_png_keep_quality(in_path, out_path, target_min_kb=200, target_max_kb=300)
    else:
        print(f"⚠️ 找不到文件: {fname}")
