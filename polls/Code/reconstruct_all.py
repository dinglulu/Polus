import os
import re
import subprocess
from datetime import datetime

import Levenshtein
import torch

# from Evaluation_platform_z.process_test_main import output_dir
from polls.Code.plot_plt import saveseqsdistributed_fig
from polls.Code.reconstruct.dpconsensus import test_consus
from polls.Code.utils import getoriandallseqs_nophred, getrandomseqs, parse_dna_phred, getoriandallseqs

basedir = os.getcwd() + '/polls/Code/reconstruct'
from concurrent.futures import ProcessPoolExecutor, as_completed
import math

# ====== 新增：并行调度与worker ======
import os, uuid, shutil, subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
from functools import partial
def _worker_one_cluster(cluster_seqs, tmp_root):
    if not cluster_seqs:
        return '', []
    _, _, qua, consusno_ = bsalign_alitest_para(cluster_seqs, tmp_root=tmp_root)
    return consusno_, qua

def bsalign_parallel(all_seqs, nproc=None, dir='files/tmp'):
    if nproc is None:
        nproc = max(1, cpu_count() - 1)
    worker = partial(_worker_one_cluster, tmp_root=dir)   # 把 dir 固定住
    with Pool(processes=nproc, maxtasksperchild=4) as pool:
        results = pool.map(worker, all_seqs, chunksize=1)
    all_consus = [r[0] for r in results]
    all_quas   = [r[1] for r in results]
    return all_consus, all_quas


# def reconstruct_seq(method,confidence,param,cluster_file_path,copy_number=10,
#                     dir='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/djangot2/files/decode/'):
def reconstruct_seq(method, confidence, param, cluster_file_path, reconstruct_model, copy_number=10,
                        dir='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/djangot2/files/decode/'):

    """
       all_seqs_ori包含了测序序列为0的reads，all_seqs为不含测序序列为0的reads
    """

    print(f"--------开始重建reconstruct_seq--------\ncluster_file_path:{cluster_file_path}")
    cluster_seqs_path=cluster_file_path['cluster_seqs_path']
    cluster_phreds_path=cluster_file_path.get('cluster_phred_path','')
    starttime = datetime.now()
    # cluster_file_path=dir+'cluster.fasta'

    print(f"使用的序列重建方法为：{method}")
    all_consus,all_quas = [],[]



    if cluster_phreds_path != '':
        ori_dna_sequences_ori, all_seqs_ori, all_quas, _ = getoriandallseqs(cluster_seqs_path, cluster_phreds_path, copy_number)
        print(f'序列重建-存在碱基置信度值可使用！')
    else:
        ori_dna_sequences_ori, all_seqs_ori, _ = getoriandallseqs_nophred(cluster_seqs_path, copy_number)
        # all_quas = parse_dna_phred(cluster_phreds_path)
    # saveseqsdistributed_fig(all_seqs)
    lasti = [i for i in range(len(all_seqs_ori)) if len(all_seqs_ori[i]) == 0]
    # last_oriseqs = [ori_dna_sequences[i] for i in lasti]
    all_seqs = [all_seqs_ori[i] for i in range(len(all_seqs_ori)) if i not in lasti]
    if len(all_quas) == 0:
        all_quas = all_seqs
    else:
        all_quas = [all_quas[i] for i in range(len(all_seqs_ori)) if i not in lasti]
    ori_dna_sequences = [ori_dna_sequences_ori[i] for i in range(len(ori_dna_sequences_ori)) if i not in lasti]
    # print(f"注意，这里有{len(last_oriseqs)}条序列丢失！")
    if copy_number==1:
        print(f"注意，这里仅使用1条序列！")
        all_consus = getrandomseqs(all_seqs, copy_number)
        all_consus = [all_consus[i][0] for i in range(len(all_consus))]
        all_quas = [[0.99 for _ in range(len(all_consus[i]))] for i in range(len(all_consus))]
    # elif method == 'bsalign':
    #     for seqsi in range(len(all_seqs)):
    #         if len(all_seqs[seqsi])==0:
    #             all_consus.append('')
    #             all_quas.append([])
    #             continue
    #         _, _, qua, consusno_ = bsalign_alitest_1119(all_seqs[seqsi])
    #
    #         all_consus.append(consusno_)
    #         all_quas.append(qua)
    # ====== 修改点 1：并行入口 ======
    elif method == 'bsalign':
        all_consus, all_quas = bsalign_parallel(all_seqs, nproc=4,dir=dir)  # nproc=None -> 自动用CPU核数-1


    elif method == 'SeqFormer':
        # 解码前纠错，得到共识序列,（使用我们的模型进行纠错）
        # print(f'copy_number:{copy_number}')
        # all_consus, all_quas,bs_consus = test_consus.getconsensus(ori_dna_sequences,all_seqs,all_quas,copy_number)

        print(f'copy_number:{copy_number},reconstruct_model:{reconstruct_model}')

        if reconstruct_model == 'second':
            print("使用二代模型")
            all_consus, all_quas,bs_consus = test_consus.getconsensus(ori_dna_sequences,all_seqs,all_quas,copy_number,device=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu'))
        else:
            print("使用三代模型")
            all_consus, all_quas,bs_consus = test_consus.getconsensus(ori_dna_sequences,all_seqs,all_quas,copy_number,'/modelbadread.pth',device=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu'))



    else:
        all_consus = bmarun(method,cluster_file_path['cluster_seqs_path'],dir)

    all_consus, all_quas = getdatas(all_seqs_ori, all_quas, all_consus)
    # if confidence == 'yes':
    #     save_seqs_with_dis(all_consus,ori_dna_sequences_ori,param,dir+'reconstruct.fasta')
    #     num,editerrorrate,seqerrorrate = save_seqs_and_confidence(all_consus,all_quas,ori_dna_sequences_ori,param,path)
    # else:
    #     path = dir+'reconstruct.fasta'
    #     num,editerrorrate,seqerrorrate = save_seqs_with_dis(all_consus,ori_dna_sequences_ori,param,path)
    # print(f"--------重建结束reconstruct_seq--------\n重建序列共有{len(all_consus)}条，重建序列与原序列总编辑距离为：{num}")
    import os

    # 获取 basename
    basename = os.path.basename(cluster_file_path['cluster_seqs_path'])
    # 去掉开头的 'cluster.' 前缀
    if basename.startswith("cluster."):
        basename = basename[len("cluster."):]

    # 去掉扩展名，并加上 _reconstruct.fasta
    basename_noext = os.path.splitext(basename)[0]
    output_filename = f"{basename_noext}_reconstruct.fasta"

    if confidence == 'yes':
        output_filename_fastq = f"{basename_noext}_reconstruct.fastq"
        path=os.path.join(dir, output_filename_fastq)
        save_seqs_with_dis(
            all_consus,
            ori_dna_sequences_ori,
            param,
            os.path.join(dir, output_filename)
        )
        num, editerrorrate, seqerrorrate = save_seqs_and_confidence(
            all_consus,
            all_quas,
            ori_dna_sequences_ori,
            param,
            path
        )
    else:
        path = os.path.join(dir, output_filename)
        num, editerrorrate, seqerrorrate = save_seqs_with_dis(
            all_consus,
            ori_dna_sequences_ori,
            param,
            path
        )

    print(
        f"--------重建结束reconstruct_seq--------\n重建序列共有{len(all_consus)}条，重建序列与原序列总编辑距离为：{num}"
    )

    return path,datetime.now()-starttime,editerrorrate,seqerrorrate

def getdatas(lastseqs,consensus_phreds,con_consensus_seqs):
    if len(lastseqs) != len(con_consensus_seqs):
        consensus_seqs = []
        consensus_p = []
        j = 0
        for i in range(len(lastseqs)):
            if len(lastseqs[i]) == 0:
                consensus_seqs.append('')
                consensus_p.append('')

            else:
                consensus_seqs.append(con_consensus_seqs[j])
                consensus_p.append(consensus_phreds[j])
                j += 1
    else:
        consensus_seqs = con_consensus_seqs
        consensus_p = consensus_phreds
    return consensus_seqs,consensus_p

# def bmarun(m,filepath,dir):
#     with open(filepath,'r') as f:
#
#         lines = f.readlines()
#     print(f"文件 {filepath} 共有 {len(lines)} 行")
#
#     # shell = f'{basedir}/{m}/DNA {filepath} out > {basedir}/{m}/result.txt'
#     shell = f'{basedir}/{m}/DNA {filepath} out > ./result.txt'
#     result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     print(f"shell语句为：{shell}\n使用{m}重建完成，result.stderr:{result.stderr}")
#     # print(f"重建完成，result.stderr:{result.stderr}")
#     # return process_file(f'{basedir}/{m}/result.txt')
#     return process_file(f'./result.txt')
import os
import subprocess
from pathlib import Path
import uuid
import time

def bmarun(m, filepath, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)

    with open(filepath, 'r') as f:
        lines = f.readlines()
    print(f"文件 {filepath} 共有 {len(lines)} 行")

    # 唯一的 result 文件名（带时间戳 + 随机字符串）
    uniq_name = f"result_{int(time.time())}_{uuid.uuid4().hex[:6]}.txt"
    result_file = os.path.join(outdir, uniq_name)
    outdir_result = os.path.join(outdir, m, "out")
    Path(outdir_result).mkdir(parents=True, exist_ok=True)

    # 调用 DNA 程序，把 stdout 重定向到 result_file
    shell = f"{basedir}/{m}/DNA {filepath} {outdir_result} > {result_file}"
    print(f"执行命令: {shell}")

    result = subprocess.run(
        shell, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 使用 {m} 重建失败，stderr:\n{result.stderr}")
        return None
    else:
        print(f"✅ 使用 {m} 重建完成，输出文件：{result_file}")

    # 返回解析结果
    return process_file(result_file)

def process_file(path):
    allseqs=[]
    with open(path, 'r') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if lines[i].find('Total number of clusters') != -1:
            break
        if re.match(r"[ACGT]",lines[i][0]):
            allseqs.append(lines[i].rstrip())
    return allseqs

def bsalign_alitest_1119(cluster_seqs):
    num = len(cluster_seqs)
    # 0925 hm改，为了得到bsalign的质量值
    # save_seqs_remove_dis(cluster_seqs, './files/seqs.fasta')
    save_seqs(cluster_seqs, './files/seqs.fasta')

    shell = 'polls/Code/reconstruct/bsalign/bsalign poa files/seqs.fasta -o files/consus.txt -L > files/ali.ali'
    result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # sleep(300)
    seqs,bsquas,aliconsus = read_alifilestest('files/ali.ali', num)
    # 将ASCII质量分数转换为整数
    bsquas = quality_scores_to_probabilities(bsquas)
    quasdict = []
    # quasno_ = []
    # with open('files/consus.txt', 'r') as file:
    #     lines = file.readlines()
    #     for line in lines:
    #         consus = line.strip('\n')
    # return seqs, consus, bsquas, consus
    consus = aliconsus
    # # if num <=3:
    #     return seqs,consus,bsquas,consus
    myseq = "" #包含了-的序列
    myseqno_ = ""
    for i in range(len(seqs[0])):
        dict = {'A':0,'C':0,'G':0,'T':0,'-':0}
        for j in range(num):
            dict[seqs[j][i].upper()]+=1
        max_key = max(dict, key=dict.get)
        myseq+=max_key
        quasdict.append(dict)
    # newquasdict = []
    for i in range(len(myseq)):
        flag = False
        if myseq[i] != '-':
            max_key = myseq[i]
            flag = True
        # if myseq[i] == '-' and quasdict[i][myseq[i]] <= 0.6:
        #     max_value = sorted(dict.values())[-2]
        #     max_key = next(key for key, value in dict.items() if value == max_value)
        #     flag = True
        if flag:
            myseqno_ += max_key
            # newquasdict.append(quasdict[i])
    # quasdict = newquasdict
    indexori,insertindexs,delindex = getfirstindex(consus,myseqno_)
    index = indexori
    newmyseqno_ = ""
    quasno_ = []
    indexd = 0
    try:
        for i in range(len(myseqno_)+len(delindex)):
            if i in insertindexs:
                continue
            elif i in delindex:
                newmyseqno_+=consus[index]
                # quasno_.append(0.35)
                # thisqua = 0.35
                thisqua = bsquas[index]
                indexd+=1
                index+=1
            else:
                thisqua = bsquas[index]
                if myseqno_[i-indexd] == consus[index]:
                    newmyseqno_+=consus[index]
                    # quasno_.append(quasdict[i-indexd][myseqno_[i-indexd]]/num)
                    # thisqua = quasdict[i-indexd][myseqno_[i-indexd]]/num
                    index+=1
                else:
                    newmyseqno_+=consus[index]
                    # quasno_.append(quasdict[i-indexd][consus[index]]/num)
                    # thisqua = quasdict[i-indexd][consus[index]]/num
                    index+=1
            # if thisqua > 0.99999:
            #     thisqua = 0.99
            quasno_.append(thisqua)
    except IndexError:
        # print(f"!!!!!!!!!!!!!!!!!!!!!!!!--------------------------bsalign-IndexError--------------------------!!!!!!!!!!!!!!!!!!!!!!!!")
        # print(myseqno_)
        if len(myseqno_) ==len(bsquas):
            # bsquas = ''.join(bsquas)
            return seqs,consus,bsquas,myseqno_
        else:
            quas = [0.99 for _ in range(len(myseqno_))]
            return seqs,consus,quas,myseqno_
    myseqno_ = newmyseqno_
    if len(myseqno_)!=len(quasno_):
        print("error!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # quasno_ = ''.join(quasno_)
    return seqs,consus,quasno_,myseqno_
import os
import uuid
import shutil
import subprocess
# ====== 修改点 2：为每个簇使用独立临时目录/文件，避免并行冲突 ======
def bsalign_alitest_para(cluster_seqs, tmp_root='files/tmp', keep_tmp=False):
    num = len(cluster_seqs)
    # 为当前任务创建独立工作目录：files/tmp/bs_<pid>_<uuid8>/
    workdir = Path(tmp_root) / f"bs_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    workdir.mkdir(parents=True, exist_ok=True)

    seqs_fa   = workdir / 'seqs.fasta'
    consus_tx = workdir / 'consus.txt'
    ali_file  = workdir / 'ali.ali'

    # 保存输入
    save_seqs(cluster_seqs, str(seqs_fa))

    # 调 bsalign，输出重定向到各自的 ali_file
    shell = f'polls/Code/reconstruct/bsalign/bsalign poa {seqs_fa} -o {consus_tx} -L > {ali_file}'
    result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        # 失败时抛错，便于你在上层捕获
        raise RuntimeError(f"bsalign failed (rc={result.returncode}): {result.stderr}")

    # 读取与后处理 —— 仅把路径从固定改为临时路径
    seqs, bsquas, aliconsus = read_alifilestest(str(ali_file), num)
    bsquas = quality_scores_to_probabilities(bsquas)

    consus = aliconsus
    myseq = ""
    myseqno_ = ""
    quasdict = []
    for i in range(len(seqs[0])):
        cnt = {'A':0,'C':0,'G':0,'T':0,'-':0}
        for j in range(num):
            cnt[seqs[j][i].upper()] += 1
        max_key = max(cnt, key=cnt.get)
        myseq += max_key
        quasdict.append(cnt)

    for i in range(len(myseq)):
        if myseq[i] != '-':
            max_key = myseq[i]
            myseqno_ += max_key

    indexori, insertindexs, delindex = getfirstindex_new(consus, myseqno_,workdir)
    index = indexori
    newmyseqno_ = ""
    quasno_ = []
    indexd = 0
    try:
        for i in range(len(myseqno_) + len(delindex)):
            if i in insertindexs:
                continue
            elif i in delindex:
                newmyseqno_ += consus[index]
                thisqua = bsquas[index]
                indexd += 1
                index  += 1
            else:
                thisqua = bsquas[index]
                if myseqno_[i - indexd] == consus[index]:
                    newmyseqno_ += consus[index]
                    index += 1
                else:
                    newmyseqno_ += consus[index]
                    index += 1
            quasno_.append(thisqua)
    except IndexError:
        if len(myseqno_) == len(bsquas):
            # 直接返回已有的
            if not keep_tmp:
                shutil.rmtree(workdir, ignore_errors=True)
            return seqs, consus, bsquas, myseqno_
        else:
            quas = [0.99 for _ in range(len(myseqno_))]
            if not keep_tmp:
                shutil.rmtree(workdir, ignore_errors=True)
            return seqs, consus, quas, myseqno_

    myseqno_ = newmyseqno_
    if len(myseqno_) != len(quasno_):
        print("error!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    # 清理解临时目录（调试时把 keep_tmp=True 即可保留）
    if not keep_tmp:
        shutil.rmtree(workdir, ignore_errors=True)

    return seqs, consus, quasno_, myseqno_

# def bsalign_alitest_para(cluster_seqs, tmp_root='files/tmp', keep_tmp=False):
#     num = len(cluster_seqs)
#     # 为当前任务创建独立工作目录：files/tmp/bs_<pid>_<uuid8>/
#     workdir = Path(tmp_root) / f"bs_{os.getpid()}_{uuid.uuid4().hex[:8]}"
#     workdir.mkdir(parents=True, exist_ok=True)
#
#     seqs_fa   = workdir / 'seqs.fasta'
#     consus_tx = workdir / 'consus.txt'
#     ali_file  = workdir / 'ali.ali'
#
#     # 保存输入
#     save_seqs(cluster_seqs, str(seqs_fa))
#
#     # 调 bsalign，输出重定向到各自的 ali_file
#     shell = f'polls/Code/reconstruct/bsalign/bsalign poa {seqs_fa} -o {consus_tx} -L > {ali_file}'
#     result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     if result.returncode != 0:
#         # 失败时抛错，便于你在上层捕获
#         raise RuntimeError(f"bsalign failed (rc={result.returncode}): {result.stderr}")
#
#     # 读取与后处理 —— 仅把路径从固定改为临时路径
#     seqs, bsquas, aliconsus = read_alifilestest(str(ali_file), num)
#     bsquas = quality_scores_to_probabilities(bsquas)
#
#
#
#     # 清理解临时目录（调试时把 keep_tmp=True 即可保留）
#     if not keep_tmp:
#         shutil.rmtree(workdir, ignore_errors=True)
#
#     return seqs, aliconsus, bsquas, aliconsus
def save_seqs(seq, path):
    with open(path, 'w') as file:
        for j, cus in enumerate(seq):
            file.write('>seq' + str(j) + '\n')
            file.write(str(cus) + '\n')


def save_seqs_with_dis(seq,ori_dna_sequences,param,path):
    editnum = 0
    num = 0
    with open(path, 'w') as file:
        # file.write(f"{param}")
        for j, cus in enumerate(seq):
            dis = Levenshtein.distance(ori_dna_sequences[j],cus)
            editnum += dis
            if dis > 0:
                num += 1
            file.write(f">seq{j}  dis:{dis}\n{cus}\n")
    # print(f"deep dpdis:{num}")
    editerrorrate = editnum/len(ori_dna_sequences)/len(ori_dna_sequences[0])
    seqerrorrate = num/len(ori_dna_sequences)
    return editnum,editerrorrate,seqerrorrate

def save_seqs_and_confidence(seq,phred,ori_dna_sequences,param,path):
    editnum = 0
    num = 0
    with open(path, 'w') as file:
        # file.write(f"{param}")
        for j, cus in enumerate(seq):
            dis = Levenshtein.distance(ori_dna_sequences[j],cus)
            editnum += dis
            if dis > 0:
                num += 1
            file.write(f"@seq_confidence{j}  dis:{dis}\n{cus}\n+\n{phred[j]}\n")
    editerrorrate = editnum/len(ori_dna_sequences)/len(ori_dna_sequences[0])
    seqerrorrate = num/len(ori_dna_sequences)
    return editnum,editerrorrate,seqerrorrate


def read_alifilestest(path,num):
    seq_inf = []
    with open(path, "r") as file:
        lines = file.readlines()
    for i in range(2,num+2):
        templine = lines[i].strip('\n').split(' ')[3].replace('.','-')
        seq_inf.append(templine)
    # lii = lines[num+7].strip('\n').split(' ')[3]
    qua = lines[num+7].strip('\n').split(' ')[1].split('\t')[2]
    consus = lines[num+6].strip('\n').split(' ')[1].split('\t')[2]
    return seq_inf,qua,consus

def quality_scores_to_probabilities(quality_scores):
    probabilities = []

    for score in quality_scores:
        # 将ASCII质量分数转换为整数
        Q = ord(score) - 33
        # 计算错误概率P
        P = 10 ** (-Q / 10)
        # 转换为0到1的形式
        probabilities.append(1 - P)

    return probabilities

def getdelinsert(lines):
    mismatchdelinsertindexs = []
    delinsertindexs = []
    upnums = 0
    line = lines[0].strip('\n').split('\t')
    mismatch, delnum, insertnum = line[-3], line[-2], line[-1]
    line = lines[2].strip('\n')
    upnumsindex = []
    # print(line)
    for i in range(len(line)):
        # a = line[i]
        # print(a)
        if line[i] == '-' or line[i] == '*':
            mismatchdelinsertindexs.append(i)
            if line[i] == '-':
                delinsertindexs.append(i)
    line = lines[3].strip('\n')
    delindex = [i for i in range(len(line)) if line[i] == '-']
    insertindexs = [x for x in delinsertindexs if x not in delindex]
    mismatchindexs = [x for x in mismatchdelinsertindexs if x not in delinsertindexs]
    # insertindexs = delinsertindexs - delindex
    for i in range(len(delindex)):
        if len(delindex) > i + 1:
            if delindex[i + 1] == delindex[i] + 1:
                continue
        for misi in range(len(mismatchdelinsertindexs)):
            if mismatchdelinsertindexs[misi] > delindex[i]:
                mismatchdelinsertindexs[misi] -= 1
        for misi in range(len(insertindexs)):
            if insertindexs[misi] > delindex[i]:
                insertindexs[misi] -= 1
        for misi in range(len(mismatchindexs)):
            if mismatchindexs[misi] > delindex[i]:
                mismatchindexs[misi] -= 1
    return insertindexs,delindex

def getfirstindex(seq1,seq2):
    with open('files/errors1.fasta', 'w') as file:
        # with open('seqs.fasta', 'w') as file:
        for j, cus in enumerate([seq1, seq2]):
            file.write('>' + str(j) + '\n')
            file.write(str(cus) + '\n')
    # shell = '../bsalign-master/bsalign align seqs.fasta > ali.ali'
    shell = 'polls/Code/reconstruct/bsalign/bsalign align files/errors1.fasta > files/alierrors1.ali'
    result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with open('files/alierrors1.ali','r') as file:
        lines = file.readlines()
    if len(lines)>0:
        line = lines[0].strip('\n').split('\t')
        insertindexs,delindex = getdelinsert(lines)
        return int(line[3]),insertindexs,delindex
    return 0

import os, uuid, shutil, subprocess
from pathlib import Path

def getfirstindex_new(seq1, seq2, workdir='files/tmp', keep_tmp=False):
    """
    对两条序列跑 bsalign align，返回 (int(line[3]), insertindexs, delindex)
    - tmp_root: 临时根目录
    - keep_tmp: True 时保留工作目录
    """
    # 1) 为当前调用创建唯一工作目录

    # 2) 统一的文件路径（不和别人冲突）
    seqs_fa  = workdir / 'seqs.fasta'
    ali_file = workdir / 'ali.ali'

    try:
        # 3) 写入输入 fasta
        with open(seqs_fa, 'w') as f:
            for j, cus in enumerate([seq1, seq2]):
                f.write(f'>{j}\n{cus}\n')

        # 4) 调用 bsalign（注意这里用 align，与你原来一致）
        shell = f'polls/Code/reconstruct/bsalign/bsalign align {seqs_fa} > {ali_file}'
        result = subprocess.run(shell, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 可选：遇到错误时抛出，便于定位
        if result.returncode != 0:
            raise RuntimeError(f'bsalign failed (code {result.returncode}): {result.stderr}')

        # 5) 读取对齐结果并解析
        if ali_file.exists():
            with open(ali_file, 'r') as f:
                lines = f.readlines()
            if len(lines) > 0:
                line = lines[0].strip('\n').split('\t')
                insertindexs, delindex = getdelinsert(lines)  # 复用你原来的解析函数
                return int(line[3]), insertindexs, delindex

        # 没有结果时返回与原函数一致
        return 0

    finally:
        # 6) 清理
        if not keep_tmp:
            try:
                shutil.rmtree(workdir, ignore_errors=True)
            except Exception:
                pass
