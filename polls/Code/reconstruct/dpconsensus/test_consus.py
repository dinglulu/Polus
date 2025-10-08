from datetime import datetime

import Levenshtein
import torch
import torch.utils.data as Data
# from dpconsensus.MHA import Transformer
# from dpconsensus.config import tgt_vocab_size, dpconsensus_path
# from dpconsensus.embedding import trans_seq_hottest_nophred
# from dpconsensus.train_test import testnet
from .embedding import trans_seq_hottest_nophred, trans_seq_hottest,trans_seq_hottest_nophred_fast
from .MHA_cpu import Transformer
from .train_test import testnet, testnet_batch
from .config import tgt_vocab_size, dpconsensus_path
from torch import nn


class MyDataSet(Data.Dataset):
    def __init__(self, enc_inputs, dec_inputs, dec_outputs, maxindexs):
        super(MyDataSet, self).__init__()
        self.enc_inputs = enc_inputs
        self.dec_inputs = dec_inputs
        self.dec_outputs = dec_outputs
        self.maxindexs = maxindexs

    def __len__(self):
        return self.enc_inputs.shape[0]

    def __getitem__(self, idx):
        return self.enc_inputs[idx], self.dec_inputs[idx], self.dec_outputs[idx], self.maxindexs[idx]


# 定义一个标准化层
class Standardize(nn.Module):
    def __init__(self, feature_dim):
        super(Standardize, self).__init__()
        self.feature_dim = feature_dim

    def forward(self, x):
        mean = x.mean(dim=-1, keepdim=True)
        std = x.std(dim=-1, keepdim=True)
        return (x - mean) / (std + 1e-6)


def load_model(model_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Transformer().to(device)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)  # weights_only=True 加上试试
    print(f"checkpoint.keys():{checkpoint.keys()}")
    # print(f"checkpoint['model_state_dict'].keys():{checkpoint['model_state_dict'].keys}")

    model.load_state_dict(checkpoint['model_state_dict'])
    return model

import os
# def getconsensus(oriseqs,testseqs,testphreds,copy_num = 5,modelpath=dpconsensus_path+'/modelsecond.pth'):
# def getconsensus(oriseqs,testseqs,testphreds,copy_num = 5,modelpath=dpconsensus_path+'/modelnosf6k.pth'):
# def getconsensus(oriseqs,testseqs,testphreds,copy_num = 5,modelpath=dpconsensus_path+'/badread.pth'):
def getconsensus(oriseqs, testseqs, testphreds, copy_num=5, modelpath='/modelsecond.pth',device=torch.device('cpu')):
    modelpath=dpconsensus_path + modelpath
    print(f"Using device: {device}")
    # 1.读取训练和测试数据
    # os.environ["CUDA_VISIBLE_DEVICES"] = "6"  # ✅ 强制只使用 GPU 6
    # device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')  # ✅ cuda:0 就是当前设置的 GPU 6
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # torch.cuda.set_device(8)

    # device=torch.device("cpu")
    # if (modelpath.find('modelsecond')) >= 0:
    #     n_layers = 4
    # else:
    #     # n_layers = 6
    #     n_layers = 2

    if (modelpath.find('modelsecond')) >= 0:
        n_layers = 4
        model = Transformer(n_layers).to(device)
        model.load_state_dict(torch.load(modelpath, map_location=device))
        model.to(device)
    else:
        # modelnosf6k.pth效果更好，但更慢,层数更多
        # n_layers = 6
        # modelpath = dpconsensus_path + '/modelnosf6k.pth'
        n_layers = 2
        modelpath = dpconsensus_path + '/modelbadread.pth'
        model = Transformer(n_layers).to(device)
        checkpoint = torch.load(modelpath)
        model.load_state_dict(checkpoint['model_state_dict'])

    # sequence_length = len(oriseqs[0])

    # testoriseqs,testseqs = getAllphred_quality_secondseqs('myfiles/seqsmerge.fasta')
    # ori_dna_sequences,all_seqs,all_quas = testoriseqs,testseqs,testseqs
    # print(len(ori_dna_sequences),len(all_seqs),len(all_quas))
    # testoriseqs = testoriseqs[choose_seqsnums:choose_seqsnums+select_nums]
    # testseqs = testseqs[choose_seqsnums:choose_seqsnums+select_nums]
    # testseqssquas = testseqs

    # print(len(testphreds),len(testseqs))
    if testseqs[0][0] == testphreds[0][0]:
        # dnatest_sequences, all_consus, all_consusori, selectseqs, bsalign_aliseqs = trans_seq_hottest_nophred_fast(testseqs,copy_num)
        dnatest_sequences, all_consus, selectseqs, bsalign_aliseqs = trans_seq_hottest_nophred_fast(testseqs,copy_num)
        dnatest_sequences_phreds = dnatest_sequences
    else:
        dnatest_sequences, dnatest_sequences_phreds, all_consus, selectseqs, bsalign_aliseqs= trans_seq_hottest(testseqs, testphreds, copy_num)

    # max_indices = np.argmax(dnatest_sequences, axis=-1)
    # max_indices = torch.Tensor(max_indices)
    enc_inputstest = torch.Tensor(dnatest_sequences).to(device)
    dec_inputstest = torch.Tensor(dnatest_sequences).to(device)


    enc_inputstest, dec_inputstest = Standardize(tgt_vocab_size)(enc_inputstest), Standardize(tgt_vocab_size)(dec_inputstest)

    # model = Transformer().cuda()

    # model = load_model(modelpath)
    # if os.path.exists(modelpath):
    #     print("找到模型" + modelpath)
    #     model = Transformer(n_layers).to(device)
    #     model.load_state_dict(torch.load(modelpath, map_location=device))
    #     model.to(device)
    starttime3=datetime.now()
    print("找到模型" + modelpath)
    print("模型参数已成功加载！")

    # 不分批全部丢进去
    # print('-----------------------------------deep learning--------------------------------')
    # pre_seqs, phred_scores, prewith_seqs, phredwith_scores = testnet(model, enc_inputstest, dec_inputstest, testseqs,testphreds)

############原本的代码
    print('-----------------------------------deep learning--------------------------------')
    # 初始化保存结果
    all_pre_seqs, all_phred_scores = [], []
    all_prewith_seqs, all_phredwith_scores = [], []

    batch_size = 5000
    total_samples = len(enc_inputstest)

    for i in range(0, total_samples, batch_size):
        print(f"Processing batch {i} - {min(i + batch_size, total_samples)}")

        batch_enc = enc_inputstest[i:i + batch_size]
        batch_dec = dec_inputstest[i:i + batch_size]
        batch_testseqs = testseqs[i:i + batch_size]
        batch_testphreds = testphreds[i:i + batch_size]

        pre_seqs, phred_scores, prewith_seqs, phredwith_scores = testnet(
            model, batch_enc, batch_dec, batch_testseqs, batch_testphreds,device
        )

        all_pre_seqs.extend(pre_seqs)
        all_phred_scores.extend(phred_scores)
        all_prewith_seqs.extend(prewith_seqs)
        all_phredwith_scores.extend(phredwith_scores)
    print(f"seqformer花费了{str(datetime.now() - starttime3)}")

#原本的结果


#修改的多进程的测试的
    # 分批输入
    # print('-----------------------------------deep learning--------------------------------')
    # all_pre_seqs, all_phred_scores = [], []
    # all_prewith_seqs, all_phredwith_scores = [], []
    #
    # batch_size = 64
    # total_samples = len(enc_inputstest)
    #
    # for i in range(0, total_samples, batch_size):
    #     print(f"Processing batch {i} - {min(i + batch_size, total_samples)}")
    #
    #     batch_enc = enc_inputstest[i:i + batch_size]
    #     batch_dec = dec_inputstest[i:i + batch_size]
    #     batch_testseqs = testseqs[i:i + batch_size]
    #     batch_testphreds = testphreds[i:i + batch_size]
    #
    #     pre_seqs, phred_scores, prewith_seqs, phredwith_scores = (testnet_batch(
    #         model, batch_enc, batch_dec, batch_testseqs, batch_testphreds
    #     ))
    #
    #     all_pre_seqs.extend(pre_seqs)
    #     all_phred_scores.extend(phred_scores)
    #     all_prewith_seqs.extend(prewith_seqs)
    #     all_phredwith_scores.extend(phredwith_scores)
    #
    # print(f"seqformer花费了{str(datetime.now() - starttime3)}")

    # 如果你需要返回或者使用这些结果：
    # all_pre_seqs, all_phred_scores, all_prewith_seqs, all_phredwith_scores


    # # pre_seqs,phredwith_scores = testnet(loadertest,model,len(enc_inputstest),testseqs)
    # with open(dpconsensus_path + '/oriandpreseqswith_.fasta', 'w') as file:
    #     for i in range(len(oriseqs)):
    #         dis = Levenshtein.distance(oriseqs[i],pre_seqs[i])
    #         disbs = Levenshtein.distance(oriseqs[i],all_consus[i])
    #         disbsori = Levenshtein.distance(oriseqs[i],all_consusori[i])
    #         file.write(f">oriseq{i}\n{oriseqs[i]}\n>bs_oriseq{i} dis:{disbsori}\n{all_consusori[i]}\n>bs_seq{i} dis:{disbs}\n{all_consus[i]}\n>preseq{i} dis:{dis}\n{pre_seqs[i]}\n>prewith_seq{i}\n{prewith_seqs[i]}\n"
    #                    f">phredwith_scores{i}\n{phredwith_scores[i]}\n>selectseqs{i}\n{selectseqs[i]}\n>bsalign_aliseqs{i}\n{bsalign_aliseqs[i]}\n")
    #         # file.write(f">oriseq{i}\n{oriseqs[i]}\n>preseq{i} dis:{dis}\n{pre_seqs[i]}\n>prewith_seq{i}\n{prewith_seqs[i]}\n>phredwith_scores{i}\n{phredwith_scores[i]}\n"
    #            f">bsalign_aliseqs{i}\n{bsalign_aliseqs[i]}\n>bs_seq{i} dis:{disbs}\n{all_consus[i]}\n")
    # with open(dpconsensus_path + '/cluseterseqs.fasta', 'w') as file:
    #     for i in range(len(oriseqs)):
    #         file.write(f">oriseq{i}\n{oriseqs[i]}\n>preseq{i}\n")
    #         for j in range(len(testseqs[i])):
    #             file.write(f"{testseqs[i][j]}\n")
    return all_pre_seqs, all_phred_scores, all_consus