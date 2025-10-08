# -*- coding: utf-8 -*-
"""
Created on Thu Aug  5 10:37:21 2021

@author: Wei QWiang
"""

import argparse

from tqdm import tqdm

# map_dic = {'0':['A', 'G'], '1':['C', 'T']}
map_dic = {'0':['A', 'C'], '1':['G', 'T']}


def linuxCommand():
    parser = argparse.ArgumentParser(description = "Church's algorithm in the pipeline of ATOM.")
    parser.add_argument('i')
    parser.add_argument('o')
    parser.add_argument('-r','--repeat', type = int, default = 4, help = "repeats number, default=[4].")
    args = parser.parse_args()

    return args.i, args.o, args.repeat

 

def seqEncode(bin_seq: str, map_dic: dict =map_dic, rep_num: int = 4) -> str:
    nt_seq_list = []
    for i in range(len(bin_seq)):
        _conti_list = nt_seq_list[-rep_num:] + [map_dic[bin_seq[i]][0]]

        if len(set(_conti_list)) == 1 and (len(_conti_list)==rep_num+1):
            nt_seq_list.append(map_dic[bin_seq[i]][1])
        else:
            nt_seq_list.append(map_dic[bin_seq[i]][0])

    nt_seq = "".join(nt_seq_list)
    return nt_seq

def churchEncode(bin_seq_list: list, map_dic: dict =map_dic, rep_num: int = 4):
    nt_seq_list = []
    pro_bar = tqdm(total=len(bin_seq_list), desc="Encoding")
    for bin_seq in bin_seq_list:
        nt_seq = seqEncode(bin_seq, map_dic=map_dic, rep_num=rep_num)
        nt_seq_list.append(nt_seq)
        pro_bar.update()
    pro_bar.close()

    return nt_seq_list


def chruchMain(input_path: str, output_path: str, map_dic: dict = map_dic, rep_num: int = 4):

    o_f = open(output_path, "w")
    with open(input_path) as f:
        for i in f:
            _bin_seq = i.strip()
            _nt_seq = seqEncode(_bin_seq, map_dic, rep_num)

            # output
            _output_line = _nt_seq + "\n"
            o_f.write(_output_line)

    o_f.close()

map_dic = {"A":"0", "C":"0", "G":"1", "T":"1"}

def linuxCommand():
    parser = argparse.ArgumentParser(description = "Church's algorithm in the pipeline of ATOM.")
    parser.add_argument('i')
    parser.add_argument('o')
    args = parser.parse_args()

    return args.i, args.o


def seqDecode(nt_seq: str, map_dic : dict = map_dic) -> str:
    bin_str = ""
    for nt in nt_seq:
        bin_str += map_dic[nt]

    return bin_str

def churchDecode(seq_list: list, map_dic : dict = map_dic) -> list:
    bin_list = []
    pro_bar = tqdm(total=len(seq_list), desc="Decoding")
    for nt_seq in seq_list:
        bin_str = seqDecode(nt_seq)
        bin_list.append(bin_str)
        pro_bar.update()
    pro_bar.close()

    return bin_list

def churchDecodeMain(input_path, output_path, map_dic : dict = map_dic):
    o_f = open(output_path, "w")
    with open(input_path) as f:
        for i in f:
            nt_seq = i.strip()
            bin_str = seqDecode(nt_seq)
            o_f.write(bin_str+"\n")

    o_f.close()

