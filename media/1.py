import os
import pandas as pd

# 设置你的目录路径
folder_path = './'  # 修改为你的实际路径

# 初始化两个列表分别收集数据
seqformer_data = []
bsalign_data = []

# 遍历文件夹中的CSV文件
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        filepath = os.path.join(folder_path, filename)
        df = pd.read_csv(filepath)

        # 取最后一行（平均值）
        avg_row = df.iloc[-1]

        # 添加方法名和copy_num
        copy_num = filename.split('_')[-1].replace('.csv', '')
        method = 'seqformer' if filename.startswith('seqformer') else 'bsalign'

        # 提取所需字段
        row_data = {
            'copy_num': int(copy_num),
            'block_rec':float(avg_row['block_rec']),

            'edit_distance': avg_row['edit_distance'],
            'base_error_rate': avg_row['base_error_rate']
        }

        if method == 'seqformer':
            seqformer_data.append(row_data)
        else:
            bsalign_data.append(row_data)

# 转为DataFrame并按copy_num排序
seqformer_df = pd.DataFrame(bsalign_data).sort_values(by='copy_num')

# 保存为CSV文件
seqformer_df.to_csv('bsalign_data.csv', index=False)

print("汇总完成，已保存为 'seqformer_summary.csv' 和 'bsalign_summary.csv'")
