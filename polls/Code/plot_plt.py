import csv

import Levenshtein
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns

def saveseqsdistributed_data(all_seqs, output_filepath='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/plot'):
    # 假设 all_seqs 是一个列表的列表，每个子列表是一个聚类
    # 计算每个聚类中的序列数量
    cluster_sizes = [len(cluster) for cluster in all_seqs]
    # with open(f'{output_filepath}/distributed.csv', 'w', newline='') as file:
    #     writer = csv.writer(file)
    #     for g in cluster_sizes:
    #         t = (g,)
    #         writer.writerow(t)
    with open(f'{output_filepath}/distributed.txt', "a") as file:
        # 遍历列表中的每个元素
        for item in cluster_sizes:
            # 将元素写入文件，并在每个元素后添加一个换行符（'\n'）
            file.write(f"{item} ")
        file.write(f"\n")

def saveseqsdistributed_fig(all_seqs, output_filepath='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/plot'):
    # 假设 all_seqs 是一个列表的列表，每个子列表是一个聚类
    # 计算每个聚类中的序列数量
    cluster_sizes = [len(cluster) for cluster in all_seqs]
    # total_sequences = sum(cluster_sizes_)
    # cluster_sizes = [cluster/total_sequences for cluster in cluster_sizes_]
    output_filename = output_filepath+'/distributed.jpg'
    # 绘制分布图
    # plt.figure(figsize=(10, 6))
    sns.histplot(cluster_sizes, kde=True, bins=range(min(cluster_sizes), max(cluster_sizes) + 2))
    # sns.histplot(cluster_sizes, kde=True, bins=range(min(cluster_sizes), max(cluster_sizes)))
    plt.title('Sequence Number Distribution in Clusters')
    plt.xlabel('Number of Sequences in Cluster')
    plt.ylabel('Frequency')
    plt.xticks(ticks=np.arange(min(cluster_sizes), max(cluster_sizes) + 1))
    print(f"绘制分布图:{output_filename}")
    # 保存图片
    plt.savefig(output_filename)
    plt.close()


def saveedit_distributed_data(refseqs,all_seqs, output_filepath='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/plot'):
    edit_distances = []
    for i in range(len(refseqs)):
        for j in range(len(all_seqs[i])):
            distance = Levenshtein.distance(refseqs[i], all_seqs[i][j])
            edit_distances.append(distance)

    with open(f'{output_filepath}/edit_dis.txt', "a") as file:
        # 遍历列表中的每个元素
        for item in edit_distances:
            # 将元素写入文件，并在每个元素后添加一个换行符（'\n'）
            file.write(f"{item} ")
        file.write(f"\n")