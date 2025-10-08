from datetime import datetime

from polls.Code.encode_decode_m.codec import DNAFountainEncode, YinYangCodeEncode, DerrickEncode, HedgesEncode, \
    PolarEncode, DNAFountainDecode, YinYangCodeDecode, DerrickDecode, HedgesDecode, PolarDecode
from polls.Code.utils import getparamdict


def test11():
    return 111


def append_info_to_first_line(file_path, info_dict):
    try:
        # 构造要追加的字段串：key1=val1,key2=val2,...
        extra_fields = "," + ",".join(f"{k}={v}" for k, v in info_dict.items())

        # 读取原文件所有行
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if lines:
            # 续写到第一行末尾（确保结尾换行符在）
            if lines[0].endswith('\n'):
                lines[0] = lines[0].rstrip('\n') + extra_fields + "\n"
            else:
                lines[0] = lines[0] + extra_fields
        else:
            # 如果文件是空的，就直接写 info
            lines = [",".join(f"{k}={v}" for k, v in info_dict.items()) + "\n"]

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[INFO] 已将 info 续写到第一行: {file_path}")
    except Exception as e:
        print(f"[ERROR] 修改第一行失败: {e}")

# def getencodeinfo(user_input,filename):
def getDnaFountainEncodeInfo(user_input,filename,file_folfer):
    encode_worker = DNAFountainEncode(input_file_path=filename, output_dir=file_folfer,
                                      sequence_length=int(user_input.get('seq_length_fountain', 120)),
                                      max_homopolymer=int(user_input.get('homopolymer_fountain', 4)),
                                      rs_num=int(user_input.get('rs_num_fountain', 0)), add_redundancy=False, add_primer=False,
                                      primer_length=20, redundancy=float(user_input.get('redundancy_rate_fountain', 0)),gc_bias=float(user_input.get('gc_fountain',0.2))
                                      ,c_dist=float(user_input.get('c_dist_fountain',0.03)),delta=float(user_input.get('delta_fountain',0.5)),
                                      crc_num=int(user_input.get('crc_fountain',0)))
    print(f"------开始编码DnaFountain------")
    encode_worker.common_encode()
    print(f"------编码结束DnaFountain------")
    print(f"编码文件为：{encode_worker.input_file_path}，编码后的文件位置为:{encode_worker.output_file_path}")
    info = {
        'total_bit': encode_worker.total_bit,
        'total_base': encode_worker.total_base,
        'encode_time': encode_worker.encode_time,
        'density': encode_worker.density,
        'gc': encode_worker.gc,
        'seq_num': encode_worker.seq_num,
        'max_homopolymer': encode_worker.max_homopolymer,

    }
    # append_info_to_first_line(encode_worker.output_file_path, info)
    output_file_path = encode_worker.output_file_path
    return info, output_file_path


def getDnaFountainDecodeInfo(seqspath,orifile,allseqs,soft_data,param):
    print(f"------DnaFountain解码前处理------，去掉>seq,无param首行\nseqspath:{seqspath},param:{param}")
    with open(seqspath,'w') as f:
        for i in range(len(allseqs)):
            # for j in range(5):
            f.write(f"{allseqs[i]}\n")
    allconfidence=soft_data.get('allconfidence',[])
    decision=soft_data.get('decision','hard')
    with open(seqspath+'.phred','w') as f:
        for i in range(len(allconfidence)):
            for j in range(len(allconfidence[i])):
                f.write(f"{allconfidence[i][j]} ")
            f.write(f"\n")
    param = getparamdict(param)
    # [method,seq_len,gc_bias,max_homopolymer,rs_num,redundancy,delta,c_dist,chunk_num] = param.rstrip().split(',')

    # return
    decode_worker = DNAFountainDecode(input_file_path=seqspath, orifile=orifile, output_dir='./files',
                                      chunk_num=int(param.get('chunk_num')),
                                      max_homopolymer=int(param.get('max_homopolymer',4)),
                                      rs_num=int(param.get('rs_num',0)),gc_bias=float(param.get('gc',0.2)),
                                      c_dist=float(param.get('c_dist',0.03)),delta=float(param.get('delta',0.5)),
                                      crc_num=int(param.get('crc_num',0)),phreds=allconfidence,decision=decision)
    return decode_worker.common_decode()


def getYYCEncodeInfo(user_input,filename,file_folfer):
    encode_worker = YinYangCodeEncode(input_file_path=filename, output_dir=file_folfer, sequence_length=int(user_input.get('seq_length_yyc', 120)),
                                      max_homopolymer=int(user_input.get('homopolymer_yyc', 4)),rs_num=int(user_input.get('rs_num_yyc', 0)),
                                      add_redundancy=False,add_primer=False, primer_length=20,max_iterations=int(user_input.get('max_iterations_yyc',100)),
                                      gc_bias=float(user_input.get('gc_yyc',0.2)),crcyyc=int(user_input.get('crcyyc',0)))

    print(f"------开始编码YYC------")
    encode_worker.common_encode()
    print(f"------编码结束YYC------")
    print(f"编码文件为：{encode_worker.input_file_path}，编码后的文件位置为:{encode_worker.output_file_path}")
    info={
        'total_bit': encode_worker.total_bit,
        'total_base': encode_worker.total_base,
        'encode_time':  encode_worker.encode_time,
        'density':  encode_worker.density,
        'gc':encode_worker.gc,
        'seq_num':encode_worker.seq_num,
        'max_homopolymer': encode_worker.max_homopolymer,
    }
    # append_info_to_first_line(encode_worker.output_file_path, info)
    #将info加入到编码之后的文件中
    output_file_path=encode_worker.output_file_path
    return info,output_file_path

def getYYCDecodeInfo(seqspath,orifile,allseqs,soft_data,param,output_dir):
    print(f"------YYC解码前处理------，去掉>seq,有param首行\nseqspath:{seqspath},param:{param}")
    with open(seqspath,'w') as f:
        f.write(param+"\n")
        for i in range(len(allseqs)):
            # for j in range(5):
            f.write(f"{allseqs[i]}\n")
    # allcon = [[] for _ in range(len(allseqs))]
    allconfidence=soft_data.get('allconfidence',[])
    # allconfidence=allcon
    decision=soft_data.get('decision','hard')
    if decision == 'hard':
        allconfidence = []
    print(f'allseqs:{len(allseqs)},allconfidence:{len(allconfidence)}')
    with open(seqspath+'.phred','w') as f:
        for i in range(len(allconfidence)):
            for j in range(len(allconfidence[i])):
                f.write(f"{allconfidence[i][j]} ")
            f.write(f"\n")
    param = getparamdict(param)

    decode_worker = YinYangCodeDecode(input_file_path=seqspath, orifile=orifile, output_dir=output_dir, index_length=int(param.get('index_length',12)),
                                      total_count=int(param.get('total_count',0)),crc_num=int(param.get('crc_num',0)),phreds=allconfidence,decision=decision)
    return decode_worker.common_decode()

def getDerrickEncodeInfo(user_input,filename,file_folfer):

    encode_worker = DerrickEncode(input_file_path=filename, output_dir=file_folfer, sequence_length=int(user_input.get('seq_length_derrick', 120))-12,
                                  max_homopolymer=int(user_input.get('homopolymer_derrick', 4)),rs_num=int(user_input.get('rs_num_derrick', 0)),
                                  add_redundancy=False, add_primer=False,primer_length=20,matrix_code=True,
                                  matrix_n=int(user_input.get('matrix_n_derrick', 255)), matrix_r=int(user_input.get('matrix_r_derrick', 32)))

    print(f"------开始编码Derrick------")
    encode_worker.common_encode_matrix()
    print(f"------编码结束Derrick------")
    print(f"编码文件为：{encode_worker.input_file_path}，编码后的文件位置为:{encode_worker.output_file_path}")
    info={
        'total_bit': encode_worker.total_bit,
        'total_base': encode_worker.total_base,
        'encode_time':  encode_worker.encode_time,
        'density':  encode_worker.density,
        'gc':encode_worker.gc,
        'seq_num':encode_worker.seq_num,
        'max_homopolymer': encode_worker.max_homopolymer,
    }
    # append_info_to_first_line(encode_worker.output_file_path, info)
    output_file_path=encode_worker.output_file_path
    return info,output_file_path

def getDerrickDecodeInfo(seqspath,orifile,allseqs,param,output_dir):
    print(f"------derrick解码前处理------，去掉>seq,无param首行\nseqspath:{seqspath},param:{param}")
    with open(seqspath,'w') as f:
        # f.write(param+"\n")
        for i in range(len(allseqs)):
            # for j in range(5):
            f.write(f"{allseqs[i]}\n")
    param = getparamdict(param)

    decode_worker = DerrickDecode(input_file_path=seqspath, output_dir=output_dir,inputfileforcompare=orifile,
                                  matrix_code=True,matrix_n=int(param.get('matrix_n',0)),matrix_r=int(param.get('matrix_r',0)),
                                  sequence_length=int(param.get('seq_len',260)))
    # decode_worker = DerrickDecode(input_file_path=encode_worker.output_file_path, output_dir=output_dir,inputfileforcompare=file_input,
    #                               matrix_code=matrix_code,matrix_n=matrix_n,matrix_r=matrix_r)
    return decode_worker.common_decode_matrix()

    # return decode_worker.common_decode()

def getPolarEncodeInfo(user_input,filename,file_folfer):

    encode_worker = PolarEncode(input_file_path=filename, output_dir=file_folfer, frozen_bits_len=int(user_input.get('frozen_bits_len_polar', 5)),)


    print(f"-----------编码中-----------:{encode_worker.input_file_path}")
    encode_worker.common_encode()
    print(f"编码后的文件位置为:{encode_worker.output_file_path}")
    info={
        'total_bit': encode_worker.total_bit,
        'total_base': encode_worker.total_base,
        'encode_time':  encode_worker.encode_time,
        'density':  encode_worker.density,
        'gc':encode_worker.gc,
        'seq_num':encode_worker.seq_num,
        'max_homopolymer': encode_worker.max_homopolymer,
        'matrices_ori':  encode_worker.matrices_ori,
        'matrices_dna_ori':  encode_worker.matrices_dna_ori,
        'matrices_01_ori': encode_worker.matrices_01_ori,
    }
    # append_info_to_first_line(encode_worker.output_file_path, info)
    output_file_path=encode_worker.output_file_path
    return info,output_file_path


def getPolarDecodeInfo(seqspath,orifile,allseqs,allconfidence,param,matrices,output_dir):
    tm_run = datetime.now()
    print(f"------Polar解码前处理------，去掉>seq,无param首行\nseqspath:{seqspath},param:{param}")
    with open(seqspath,'w') as f:
        for i in range(len(allseqs)):
            f.write(f"{allseqs[i]}\n")
    with open(seqspath+'.phred','w') as f:
        for i in range(len(allconfidence)):
            for j in range(len(allconfidence[i])):
                f.write(f"{allconfidence[i][j]} ")
            f.write(f"\n")
    param = getparamdict(param)
    decode_worker = PolarDecode(input_file_path=seqspath, orifile=orifile,
                                   output_dir=output_dir,
                                   matrices_ori=matrices['matrices_ori'],
                                   matrices_dna_ori=matrices['matrices_dna_ori'],
                                   matrices_01_ori=matrices['matrices_01_ori'],
                                   frozen_bits_len=param.get('frozen_bits_len',5))
    return decode_worker.common_decode()



def getHedgesEncodeInfo(user_input,filename,file_folfer):

    encode_worker = HedgesEncode(input_file_path=filename, output_dir=file_folfer, sequence_length=int(user_input.get('seq_length_hedges', 120)),
                                 max_homopolymer=int(user_input.get('homopolymer_hedges', 4)),
                                 rs_num=int(user_input.get('rs_num_hedges', 0)),
                                 add_redundancy=False, add_primer=False,primer_length=20,matrix_code=True,
                                 matrix_n=int(user_input.get('matrix_n_hedges', 255)), matrix_r=int(user_input.get('matrix_r_hedges', 32)),
                                 coderatecode=int(user_input.get('coderatecode_hedges', 3)))


    print(f"-----------编码中-----------:{encode_worker.input_file_path}")
    encode_worker.common_encode_matrix()
    print(f"编码后的文件位置为:{encode_worker.output_file_path}")
    info={
        'total_bit': encode_worker.total_bit,
        'total_base': encode_worker.total_base,
        'encode_time':  encode_worker.encode_time,
        'density':  encode_worker.density,
        'gc':encode_worker.gc,
        'seq_num':encode_worker.seq_num,
        'max_homopolymer': encode_worker.max_homopolymer,
    }
    # append_info_to_first_line(encode_worker.output_file_path, info)
    output_file_path=encode_worker.output_file_path
    return info,output_file_path


def getHedgesDecodeInfo(seqspath,orifile,allseqs,param,output_dir):
    print(f"------hedges解码前处理------，去掉>seq,有param首行\nseqspath:{seqspath},param:{param}")
    with open(seqspath,'w') as f:
        f.write(param+"\n")
        for i in range(len(allseqs)):
            f.write(f"{allseqs[i]}\n")
    param = getparamdict(param)

    decode_worker = HedgesDecode(input_file_path=seqspath,orifile=orifile, output_dir=output_dir)

    return decode_worker.common_decode_matrix()
