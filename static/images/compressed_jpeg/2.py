import os
import shutil

# 压缩好的 JPEG 文件目录
input_dir = os.path.join(os.getcwd(), "compressed_jpeg")
# 输出目录
output_dir = os.path.join(os.getcwd(), "fake_png")
os.makedirs(output_dir, exist_ok=True)

for fname in os.listdir(input_dir):
    if fname.lower().endswith(".jpg") or fname.lower().endswith(".jpeg"):
        old_path = os.path.join(input_dir, fname)
        new_name = os.path.splitext(fname)[0] + ".png"  # 只是改后缀
        new_path = os.path.join(output_dir, new_name)
        shutil.copy2(old_path, new_path)
        print(f"已生成: {new_name}")
