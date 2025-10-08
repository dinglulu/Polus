import os
# print("Current working directory:", os.getcwd())
# print("Sys.path:", sys.path)
import sys
# sys.path.append('/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform')
import traceback

from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from requests import session


from POLUS import settings
from polls.Code.cluster import cluster_by_ref, cluster_by_index
from polls.Code.encode_all import test11, getDnaFountainEncodeInfo, getYYCEncodeInfo, getDerrickEncodeInfo, \
    getHedgesEncodeInfo, getPolarEncodeInfo, getDnaFountainDecodeInfo, getYYCDecodeInfo, getDerrickDecodeInfo, \
    getHedgesDecodeInfo, getPolarDecodeInfo
from polls.Code.reconstruct_all import reconstruct_seq
from polls.Code.simulate import adddt4simu_advanced
from polls.Code.utils import SimuInfo, getoriandallseqs_nophred, read_unknown_andsave, write_dict_to_csv, \
    initial_params, read_unknown_andsave_hedges, readandsave_noline0, savelistfasta, readandsave, readandsavefastq
from polls.forms import EncodeHiddenForm
import base64
from django.http import JsonResponse
# 添加项目根目录到sys.path
# from .forms import EncodeHiddenForm
# from polls.forms import EncodeHiddenForm
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
def check_uploaded_file(request, fieldname, folder):
    uploaded_file = request.FILES.get(fieldname)
    if not uploaded_file or not uploaded_file.name.strip():
        return False, f"Please upload a file for '{fieldname}'."
    filepath = os.path.join(folder, uploaded_file.name)
    if not os.path.exists(filepath):
        return False, f"The file '{uploaded_file.name}' does not exist on server."
    return True, filepath

def getform(user_input:dict):
    form = EncodeHiddenForm(initial={
        'hidden_method1': user_input['hidden_method1'],
        'hidden_method2': user_input['hidden_method2'],
        'hidden_mingc': user_input['hidden_mingc'],
        'hidden_maxgc': user_input['hidden_maxgc'],
        'hidden_sequence_length': user_input['hidden_sequence_length'],
        "info_density1": user_input['info_density1'],
        "encode_time1": user_input['encode_time1'],
        "sequence_number1": user_input['sequence_number1'],
        "index_length1": user_input['index_length1'],
        "info_density2": user_input['info_density2'],
        "encode_time2": user_input['encode_time2'],
        "sequence_number2": user_input['sequence_number2'],
        "index_length2": user_input['index_length2']
    })
    return form


forsimulatefile = 'index_DNAFountain.fasta'
forclusterrecfile = 'simulated_seqsr1r2.fasta'

encodeinfo = {

    'fountain':{
        "info_density": 1.11,
        "encode_time": 10,
        "sequence_number": 85,
        "index_length": 12
    },
    'YYC':{
        "info_density": 0.99,
        "encode_time": 17,
        "sequence_number": 124,
        "index_length": 12
    },
    'derrick':{
        "info_density": 1.02,
        "encode_time": 30,
        "sequence_number": 57,
        "index_length": 12
    },
    'PolarCode':{
        "info_density": 1.0,
        "encode_time": 68,
        "sequence_number": 98,
        "index_length": 15
    },
    'hedges':{
        "info_density": 0.66,
        "encode_time": 50,
        "sequence_number": 33,
        "index_length": 13
    },
}

def get_media_path_from_request(request):
    # 这个函数是为了获得当前用户使用的ip地址，来保存他上传的media
    ip_address = get_client_ip(request)
    return get_ip_media_folder(ip_address,'media')
def get_files_path_from_request(request):
    # 这个函数是为了获得当前用户使用的ip地址，来保存他上传的media
    ip_address = get_client_ip(request)
    user_base_path = get_ip_media_folder(ip_address, 'files')

    # 创建子文件夹
    for subfolder in ['decode', 'plot', 'simu']:
        os.makedirs(os.path.join(user_base_path, subfolder), exist_ok=True)
    return user_base_path
def read_file_head(filepath, max_lines=100):
    """
    读取指定文本文件的前 max_lines 行内容，用于预览展示。

    :param filepath: 文件路径（必须是文本格式）
    :param max_lines: 最大读取行数（默认100）
    :return: 字符串形式的前 max_lines 行内容，若出错返回错误提示
    """
    preview_lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                preview_lines.append(line.rstrip())
        return '\n'.join(preview_lines)
    except Exception as e:
        return "Please upload a correct file."


def handle_file(file):
    file_name = file.name
    file_path = os.path.join('uploads', file_name)
    # 确保上传目录存在
    os.makedirs('uploads', exist_ok=True)
    # 保存文件
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return file_path


def get_client_ip(request):
    # 如果用了反向代理，如 Nginx，需要读取真实 IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For 可能是多个 IP 的列表
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
import os

def get_ip_media_folder(ip_address, base_address='media'):
    base_media_folder = os.path.join(os.getcwd(), base_address)
    ip_folder = os.path.join(base_media_folder, ip_address.replace(':', '_'))  # 替换冒号，避免路径非法
    os.makedirs(ip_folder, exist_ok=True)
    return ip_folder

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
media_FOLDER = os.path.join(os.getcwd(), 'media')


def upload_file(request,name='file'):

    # print(f"-----files--------???:{request}")
    if request.method == 'POST' and name in request.FILES:
        uploaded_file = request.FILES[name]
        print(f"-----files--------???:{uploaded_file}")
        # 生成文件名（这里简单使用原始文件名，实际应用中应该做更安全的处理）
        filename = os.path.join(media_FOLDER, uploaded_file.name)
        print(filename)
        # 保存文件到指定目录
        with default_storage.open(filename, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        return HttpResponse('File uploaded successfully: ' + filename,status=200)
    else:
        return HttpResponse('Invalid request or no file uploaded', status=400)

def download_file(request,mode='encode'):
    # 指定文件存储的根目录
    # file_root = os.path.join(settings.MEDIA_ROOT, 'uploads')
    defaultpath = settings.MEDIA_URL+'index_DNAFountain.fasta'
    if mode=='encode':
        filename=request.session.get('encode_outfile',defaultpath)
    elif mode=='simulate':
        filename=request.session.get('simulate_outfile',defaultpath)
    elif mode == 'fordecode_outfile':
        filename=request.session.get('cluster_or_rec_file',defaultpath)
    elif mode == 'evaluate':
        filename=request.session.get('evaluate_filename',defaultpath)
    else:
        filename=request.session.get('decodefile',defaultpath)
    # 构建文件的完整路径
    # file_path = os.path.join(UPLOAD_FOLDER, filename)
    file_path = filename
    print(f"ppppppppppppppppppppppppppppppppfajeiof:{file_path}")
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise Http404("File not found")

    # 打开文件并读取其内容
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/octet-stream")

    # 设置响应头，指定下载的文件名
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    #
    return response

# def getencodeinfo(user_input,filename):
#     encode_worker = DNAFountainEncode(input_file_path=filename, output_dir='./',
#                                       sequence_length=int(user_input.get('seq_length', 120)),
#                                       max_homopolymer=int(user_input.get('homopolymer', 4)),
#                                       rs_num=int(user_input.get('rs_num', 0)), add_redundancy=False, add_primer=False,
#                                       primer_length=20, redundancy=float(user_input.get('redundancy_rate', 0)))
#
#     print(f"-----------编码中-----------:{encode_worker.input_file_path}")
#     encode_worker.common_encode()
#     print(f"编码后的文件位置为:{encode_worker.output_file_path}")
#     info={
#         'total_bit': encode_worker.total_bit,
#         'total_base': encode_worker.total_base,
#         'encode_time':  encode_worker.encode_time,
#         'density':  encode_worker.density,
#         'gc':encode_worker.gc,
#         'seq_num':encode_worker.seq_num,
#     }
#     output_file_path=encode_worker.output_file_path
#     return info,output_file_path
writefilepath = './encodedecode_infos_0519.txt'
def get_file_preview_lines(file_path: str, max_lines: int = 100) -> str:
    """
    从给定文件读取前 max_lines 行作为预览内容。

    :param file_path: 文件路径
    :param max_lines: 最大读取行数，默认 100
    :return: 拼接后的字符串预览内容（以 \n 分隔）
    """
    preview_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                preview_lines.append(line.rstrip())
    except Exception:
        preview_lines = ["Please encode first, or upload a correct file"]

    return '\n'.join(preview_lines)
import base64
import mimetypes
def view_session(request):
    print("当前 session 内容：")
    for key, value in request.session.items():
        print(f"{key} -> {value}")

def get_image_preview_data(file_path: str) -> dict:
    """
    将图像文件编码为 base64 字符串，供 HTML 预览用。

    :param file_path: 图像文件路径
    :return: 字典，包括是否成功、文件类型、base64 内容
    """
    try:
        with open(file_path, 'rb') as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith("image/"):
                return {
                    "success": True,
                    "file_type": mime_type,
                    "file_content": f"data:{mime_type};base64,{encoded_string}"
                }
            else:
                return {
                    "success": False,
                    "file_type": "unknown",
                    "file_content": ""
                }
    except Exception:
        return {
            "success": False,
            "file_type": "error",
            "file_content": ""
        }
import mimetypes
import base64

import mimetypes
import base64

def get_preview_data(file_path: str) -> dict:
    """
    支持图片、视频和文本文件的预览数据。
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            return {"success": False, "file_type": "unknown", "file_content": ""}

        with open(file_path, 'rb') as f:
            raw = f.read()

        if mime_type.startswith("image/"):
            return {
                "success": True,
                "file_type": "image",
                "file_content": f"data:{mime_type};base64,{base64.b64encode(raw).decode()}"
            }

        elif mime_type.startswith("video/"):
            return {
                "success": True,
                "file_type": "video",
                "file_content": f"data:{mime_type};base64,{base64.b64encode(raw).decode()}"
            }

        elif mime_type.startswith("text/") or file_path.endswith(('.txt', '.csv', '.log', '.py', '.md','.py','.csv')):
            content = raw.decode('utf-8', errors='ignore')[:3000]  # 限制预览长度
            return {
                "success": True,
                "file_type": "text",
                "file_content": content
            }

        else:
            return {"success": False, "file_type": "unsupported", "file_content": ""}
    except Exception as e:
        return {"success": False, "file_type": "error", "file_content": ""}

# @csrf_exempt

decoded_data = {
    "success": True,
    "time": '30s',
    "bit_rev": 0.9971,
    "seq_rev": 0.9878
}


sequencing_data = {
    "time": '192s',
    "size": '1.34MB',
    "file_path": './1.fastq',
    'consensus_file_path':'consus_file1.fasta'
}

def getseques(filename):
    dnasequences = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    for i in range(1,len(lines[1:])):
        dnasequences.append(lines[i].strip('\n'))
    return dnasequences



def dna_encoding(request):
    # encode的后端请求处理
    #设置一个根据用户ip来处理他们的media路径，以及生成的文件（测序，模拟等）
    media_FOLDER=get_media_path_from_request(request)
    # filename = os.path.join(UPLOAD_FOLDER, '1.jpg')
    file_folder=get_files_path_from_request(request)
    filename=UPLOAD_FOLDER + '/SZU_logo.jpg'
    if request.method == 'POST' and 'encodeBtn' in request.POST:
        #如果用户是post请求，并且是点击了编码按钮，那么获取他们提交的一个表单数据。
        user_input = request.POST
        print(user_input)
        # 只有当 session 中没有 filename 时，才进行上传校验，默认的一个filename是一个SZU_logo.jpg
        if 'filename' not in request.session:
            # 如果没有上传文件 那么就警告一下
            if 'file' not in request.FILES or request.FILES['file'].name == '':
                return render(request, 'encode.html', {
                    'errors': 'Please upload a file before encoding.',
                    'base': {**initial_params},
                })

            uploaded_file = request.FILES['file']
            filepath = os.path.join(media_FOLDER, uploaded_file.name)

            if not os.path.exists(filepath):
                # 服务器指定位置没有该文件，提示上传
                return render(request, 'encode.html', {
                    'errors': f"The file '{uploaded_file.name}' does not exist on server. Please upload it.",
                    'base': {**initial_params},
                })

            # 设置 session 中的 filename（可选）
            request.session['filename'] = uploaded_file.name
            filename = request.session['filename']
        else:
            # 如果 session 已有 filename，就从 session 获取
            filename = request.session['filename']

        print(filename)
        # 如果有method 就用 如果没有那就用原本的
        method = user_input.get('method','fountain')
        # 但是由于前端有多个seq_length，所以后续需要区分一下
        try:
            if method == 'fountain':
                print(f"encode 开始编码 fountain-----------:{user_input}")
                info,output_file_path = getDnaFountainEncodeInfo(user_input,filename,file_folder)
            elif method == 'YYC':
                print(f"encode 开始编码 YYC-----------:{user_input}")
                info,output_file_path = getYYCEncodeInfo(user_input,filename,file_folder)
            elif method == 'derrick':
                print(f"encode 开始编码 derrick-----------:{user_input}")
                info,output_file_path = getDerrickEncodeInfo(user_input,filename,file_folder)
            elif method == 'PolarCode':
                print(f"encode 开始编码 PolarCode-----------:{user_input}")
                info,output_file_path = getPolarEncodeInfo(user_input,filename,file_folder)
                request.session['matrices'] = info
                # print(f"??????????????????request.session['matrices']:{request.session.get('matrices').keys()}")
            else:
                print(f"encode 开始编码 hedges-----------:{user_input}")
                info,output_file_path = getHedgesEncodeInfo(user_input,filename,file_folder)
        except Exception as e:
            context = {'base': initial_params,}
            print("捕获到异常:")
            print(f"异常类型: {type(e)}")
            print(f"异常信息: {e}")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(f"完整的堆栈跟踪信息:\n{''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))}")

            return render(request, 'encode.html', context)
        # finally:
            # print(f"***编码介绍，查看info信息:{info}***")
        # 保存用户输入的编码信息+编码后的信息 到session
        # write_dict_to_csv({'':f'\n\n','method':f'--------------------{method}--------------------'},writefilepath)
        # info['method']=method
        infos = {
            'method': method,
            'density':info['density'],
            'total_bit':info['total_bit'],
            'total_base':info['total_base'],
            'seq_num':info['seq_num'],
            'max_homopolymer':info['max_homopolymer'],
            'gc':info['gc'],
            'encode_time':info['encode_time']
        }
        metrics = {
            "Costs": None,   # 先占位，解码时更新
            "Sequencing Depth Requirement": None, # 先占位，解码时更新
            "Encoding Runtime": infos["encode_time"],
            "Decoding Runtime": None,  # 先占位，解码时更新
            "Physical Ratio": None,   # 先占位，解码时更新
            "Logical Ratio": infos["density"],
            "GC Contents": infos["gc"],
            "Maximum Homopolymers Length": infos["max_homopolymer"],
            "File Recovery": None   # 先占位，解码时更新
        }
        request.session["metrics"] = metrics

        # write_dict_to_csv({'':f'\n'},writefilepath)
        # write_dict_to_csv(infos,writefilepath)
        # print(f"???????????????jafoeigj:{request.session.get('matrices','cjfoaeaj')}")
        print(f"编码时间：{info['encode_time']},max_homopolymer:{info['max_homopolymer']}")
        request.session['encode_input'] = user_input
        request.session['encode_outfile'] =os.path.join(file_folder, os.path.basename(output_file_path))
        # info = encodeinfo.get(user_input['method'])
        request.session['encoded_data'] = info

        max_preview_lines = 100
        preview_lines = []

        # input("dasd")
        try:
            with open(output_file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= max_preview_lines:
                        preview_lines.append("...\n[Only first 100 lines shown in preview]")
                        break
                    preview_lines.append(line)
            file_content = ''.join(preview_lines)
        except Exception as e:
            file_content = f"[ERROR] Failed to read encoded file: {str(e)}"
        # 对编码之后的结果做一个网页展示
        context = {
            'base': user_input,
            'encoded_data': info,
            'filename': os.path.basename(filename),
            'encoded_file_content': file_content ,
            'disable':True
        }

        #保存我的结果用于后续的evaluate，
        # evaluate_key = f"{method}_{os.path.basename(filename)}"
        # evaluate_data = {
        #     'density': info['density'],
        #     'max_homopolymer': info['max_homopolymer'],
        #     'gc': info['gc'],
        #     'encode_time': info['encode_time'],
        # }
        # # 初始化或更新 session 中的 evaluate 字典
        # if 'evaluate' not in request.session:
        #     request.session['evaluate'] = {}
        #
        # request.session['evaluate'][evaluate_key] = evaluate_data
        # input("dasd")
        view_session(request)
        # input("dasd")
        file_path = request.session.get('filename', '')
        preview_data = get_preview_data(file_path)

        input_file_front = os.path.basename(file_path)
        context['preview_data'] = preview_data
        context['input_file_front'] = input_file_front
        return render(request, 'encode.html', context)

    elif request.GET.get('reset') == '1':
        context = {
            'base': {**initial_params}, 'filename': os.path.basename(filename),
        }
        backup_evaluate = dict(request.session.get('evaluate', {}))
        request.session.flush()
        # 后续可以重新 set 回来（如果还在同一次请求内）
        request.session['evaluate'] = backup_evaluate
        request.session['filename'] = UPLOAD_FOLDER + '/SZU_logo.jpg'
        view_session(request)
        file_path = request.session.get('filename', '')
        preview_data = get_preview_data(file_path)
        input_file_front = os.path.basename(request.session.get('filename', ''))
        context['preview_data'] = preview_data
        context['input_file_front'] = input_file_front
        return render(request, 'encode.html',context)  # 重定向回干净页面
    #输入一个预览的文件名字，以及他的一个预览内容
    context = {
        'base': {**initial_params}, 'filename': os.path.basename(filename),
    }
    request.session.flush()
    request.session['filename'] = filename
    file_path = request.session.get('filename', '')
    #获取我的预览内容
    preview_data = get_preview_data(file_path)
    input_file_front = os.path.basename(request.session.get('filename', ''))
    context['preview_data']=preview_data
    context['input_file_front']=input_file_front

    view_session(request)

    # print(f"1111filename:{filename}")
    # print(f"开始编码filename-----------:{context['filename']}")
    return render(request, 'encode.html', context)
def simulate_view(request):
    # 加上了ip地址的文件夹
    media_FOLDER = get_media_path_from_request(request)
    FILE_FOLDER=get_files_path_from_request(request)
    simu_path = os.path.join(FILE_FOLDER, 'simu/')
    # simu_path = os.path.join(FILE_FOLDER, 'simu/')
    context = {
        'simulate': True,
        'base': {**initial_params,},
    }
    # 当选择了需要模拟的哪几步之后展示的页面
    if request.method == 'POST' and 'stepsok' in request.POST:
        user_input = request.POST
        # 通过这个来获得用户选择了哪几个channel
        request.session['channel']=user_input.getlist('channel',['synthesis'])
        # 获得文件名
        encode_outfile_front = os.path.basename(request.session.get('encode_outfile', ''))
        # 读取编码之后的文件，并且提取前100行出来作为展示

        preview_content = get_file_preview_lines(request.session.get('encode_outfile', ''),100)
        print("== SESSION DEBUG ==")
        for key, value in request.session.items():
            print(f"{key}: {value}")

        print(f"[Session Keys] {len(request.session.keys())}")

        print(f"user_input.getlist('channel'):{user_input.getlist('channel')}")
        context['base'] = {**initial_params, **request.session}
        context['base']['filename'] = encode_outfile_front
        context['preview_content'] = preview_content
        encode_outfile_path = request.session.get("encode_outfile")
        encode_outfile_size = os.path.getsize(encode_outfile_path) if encode_outfile_path and os.path.exists(
            encode_outfile_path) else 0
        context['encode_outfile_size_kb'] = round(encode_outfile_size / 1024, 2)
        # print(f"steps ok context:{context}")
        return render(request, 'simulate.html', context)
    elif request.method == 'POST' and 'synseqBtn' in request.POST:


        user_input = request.POST

        encode_outfile_filename = request.session.get('encode_outfile', '')
        print(encode_outfile_filename)
        # 如果 session 中没有 encode_outfile（即为空字符串），则执行上传校验逻辑
        if not encode_outfile_filename:
            # 判断是否上传了文件
            if 'file' not in request.FILES or request.FILES['file'].name == '':
                return render(request, 'simulate.html', {
                    'errors': 'Please encode first, or upload a correct file.',
                    'base': {**initial_params},
                })





        encode_outfile_front = os.path.basename(encode_outfile_filename)


        simuInfo = SimuInfo(
            inputfile_path=encode_outfile_filename, synthesis_method=user_input.get('synthesis_method', 'electrochemical'),
            channel=request.session.get('channel', []),
            oligo_scale=user_input.get('oligo_scale', 1), sample_multiple=user_input.get('sample_multiple', 100),
            pcrcycle=user_input.get('pcrcycle', 2), pcrpro=user_input.get('pcrpro', 0.8),
            decay_year=user_input.get('decay_year', 2), decaylossrate=user_input.get('decaylossrate', 0.3),
            sample_ratio=user_input.get('sample_ratio', 0.005),
            sequencing_method=user_input.get('sequencing_method', 'paired-end'),
            depth=user_input.get('depth', 10), badparams=user_input.get('badparams', ''),
            thread=initial_params.get('thread_num'),
        )

        # dnasequences = getseques(filename)
        print(f"synseq_view 开始模拟合成测序-----------:{user_input}")

        if user_input.get('sequencing_method', 'paired-end') == "Nanopone" or simuInfo.sequencing_method == "Pacbio":
            filessave = simu_path+encode_outfile_front + '_simulated_seqsr1r2.fastq'
        else:
            filessave = simu_path +encode_outfile_front+ '_simulated_seqsr1r2.fasta'
        try:
            infos = adddt4simu_advanced(simuInfo, filessave,simu_path,encode_outfile_front)
        # except:
        #     print(f"simulate_view 模拟合成测序失败-----------:{user_input}")
        #     return render(request, 'simulate.html', {
        #         'errors': f"please upload a valid file",
        #         'base': {**initial_params},
        #     })
        except Exception as e:
            print(f"simulate_view 模拟合成测序失败-----------:{user_input}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            print("详细堆栈信息:")
            traceback.print_exc()  # 打印完整的错误堆栈
            return render(request, 'simulate.html', {
                'errors': f"please upload a valid file",
                'base': {**initial_params},
            })
        request.session['simulate_outfile'] = infos.get('path')
        # request.session['sequencinsimulated_seqsr1r2g_method'] = user_input.get('sequencing_method','paired-end')
        # write_dict_to_csv({'simulate_time': infos.get('time', '')}, writefilepath)
        # write_dict_to_csv(infos,writefilepath)
        print(f"已模拟完成,共耗时{infos.get('time')},path为：-----------:{infos.get('path')}")
        context['base'] = {**initial_params, **request.session}
        encode_outfile_front = os.path.basename(request.session.get('encode_outfile', ''))
        # 读取编码之后的文件，并且提取前100行出来作为展示

        preview_content = get_file_preview_lines(request.session.get('encode_outfile', ''), 100)
        context['base']['filename'] = encode_outfile_front
        # context['base']['filename'] = encode_outfile_front
        context['preview_content'] = preview_content
        context['sequencing_data'] = {'time': infos.get('time')}

        print("== SESSION DEBUG ==")
        for key, value in request.session.items():
            print(f"{key}: {value}")
        context['disable']=True
        return render(request, 'simulate.html', context)
    #如果模拟完成 那么可以选择重新模拟
    elif request.GET.get('reset') == '1':
        matrices = request.session.get('matrices', dict())
        encode_outfile = request.session.get('encode_outfile', '')
        metrics = request.session.get("metrics", {})
        filename = request.session.get('filename', '')
        request.session.flush()
        request.session["metrics"] = metrics
        request.session['encode_outfile'] = encode_outfile
        request.session['filename'] = filename
        request.session['matrices'] = matrices
        # polar自带的
        context = {
            'base': {**initial_params, },

        }
        return render(request, 'simulate.html', context)

    matrices = request.session.get('matrices', dict())
    encode_outfile = request.session.get('encode_outfile','')

    filename = request.session.get('filename','')
    metrics = request.session.get("metrics", {})
    request.session.flush()
    request.session["metrics"] = metrics
    request.session['encode_outfile']=encode_outfile
    request.session['filename']=filename
    request.session['matrices']=matrices
    # polar自带的
    context = {
        'base': {**initial_params,},

    }
    return render(request, 'simulate.html', context)

def _build_decode_page_context(initial_params, request, forclusterfile, encode_outfile, error_msg=None):
    """
    统一构造 decode.html 需要的上下文，包含四块预览与文件名
    - simulate（用于聚类的文件，可能是模拟文件或直接 encode_outfile）
    - ref（参考编码输出）
    - decode（聚类或重建后的待解码文件）
    - origin（原始上传文件，例如图片/视频）
    """
    context = {'base': {**initial_params, **request.session}}

    # 这几个路径尽量从 session 拿，拿不到就回落到传参
    cluster_or_rec_file = request.session.get('cluster_or_rec_file', '') or forclusterfile
    origin_file = request.session.get('filename', '')

    # 预览数据
    preview_simulate = read_file_head(forclusterfile) if forclusterfile else ''
    preview_ref = read_file_head(encode_outfile) if encode_outfile else ''
    preview_decode = read_file_head(cluster_or_rec_file) if cluster_or_rec_file and os.path.exists(cluster_or_rec_file) else ''
    preview_origin = get_preview_data(origin_file) if origin_file else ''

    # 填充到 context
    context['preview_simulate'] = preview_simulate
    context['preview_ref'] = preview_ref
    context['preview_decode'] = preview_decode
    context['preview_origin'] = preview_origin

    # 文件名（页面显示用）
    context['forclusterfile_filename'] = os.path.basename(forclusterfile) if forclusterfile else ''
    context['encode_outfile_filename'] = os.path.basename(encode_outfile) if encode_outfile else ''
    context['file_for_decode'] = os.path.basename(cluster_or_rec_file) if cluster_or_rec_file else ''
    context['ori_filename'] = os.path.basename(origin_file) if origin_file else ''

    # 错误提示（如有）
    if error_msg:
        context['errors'] = error_msg

    # 页面状态：显示“已聚类/已重建”的结果（如果存在）
    context['cluster'] = True
    context['reconstruct'] = True
    context['decode'] = False  # 本次是解码失败回填页面，故未完成 decode

    # 让前端可判断“用户可直接重试”
    context['can_retry'] = True

    return context

def decode_view(request):
    #当前session中存储了filename，encodeout，simulate_out，如果没有进行模拟，那么forcluster使用encodeout
    FILE_FOLDER=get_files_path_from_request(request)
    output_dir = os.path.join(FILE_FOLDER, 'decode/')
    media_FOLDER = get_media_path_from_request(request)
    #第一次访问的时候不带上cluster和reconstruct，重置这个context
    context = {
        'cluster': True,
        'reconstruct': True,
        'base': {**initial_params},
    }
    # 极化码需要的参数
    matrices = request.session.get('matrices',dict())
    #模拟之后生成文件的路径,但是可能用户没有进行模拟，那么直接使用encode——out

    simulate_outfile = request.session.get('simulate_outfile','')
    encode_outfile = request.session.get('encode_outfile','')
    #filename：一开始传入的文件地址，如果没有传，那么默认是szu.jpg
    filename = request.session.get('filename','')
    forclusterfile = simulate_outfile
    #如果没有simulate的文件，那么就让encodeout作为一个cluster文件
    if forclusterfile == '':
        forclusterfile = encode_outfile


    #当按下了开始cluster之后的操作
    if request.method == 'POST' and 'clusterBtn' in request.POST:


        try:

            # simulate没有上传，那么就返回一个报错
            if not simulate_outfile or not os.path.exists(simulate_outfile):
                metrics = request.session.get("metrics", {})
                print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")
                request.session.flush()
                request.session["metrics"] = metrics
                request.session['simulate_outfile'] = forclusterfile
                request.session['encode_outfile'] = encode_outfile
                request.session['matrices'] = matrices
                request.session['filename'] = filename
                # forclusterfile = simulate_outfile
                # if forclusterfile =='':
                #     forclusterfile=encode_outfile
                # request.session.flush()

                # 如果有这个文件，那么就进行预览
                preview_simulate = read_file_head(forclusterfile)
                preview_ref = read_file_head(encode_outfile)

                context = {'base': initial_params, }
                context['preview_simulate'] = preview_simulate
                context['preview_ref'] = preview_ref
                context['forclusterfile_filename'] = os.path.basename(forclusterfile)
                context['encode_outfile_filename'] = os.path.basename(encode_outfile)
                context['errors'] = "No simulate file uploaded. Please upload one."
                # filename= forclusterrecfile
                # context['base']['filename'] = filename
                return render(request, 'decode.html', context)

            # encode_output没有上传，那么就返回初始界面，并且附带一个报错
            if not encode_outfile or not os.path.exists(encode_outfile):
                metrics = request.session.get("metrics", {})
                print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")
                request.session.flush()
                request.session["metrics"] = metrics
                request.session['simulate_outfile'] = forclusterfile
                request.session['encode_outfile'] = encode_outfile
                request.session['matrices'] = matrices
                request.session['filename'] = filename
                # forclusterfile = simulate_outfile
                # if forclusterfile =='':
                #     forclusterfile=encode_outfile
                # request.session.flush()

                # 如果有这个文件，那么就进行预览
                preview_simulate = read_file_head(forclusterfile)
                preview_ref = read_file_head(encode_outfile)

                context = {'base': initial_params, }
                context['preview_simulate'] = preview_simulate
                context['preview_ref'] = preview_ref
                context['errors'] = "No reference file uploaded. Please upload one."
                context['forclusterfile_filename'] = os.path.basename(forclusterfile)
                context['encode_outfile_filename'] = os.path.basename(encode_outfile)
                # filename= forclusterrecfile
                # context['base']['filename'] = filename
                return render(request, 'decode.html', context)

            file_simulate_outfile = request.session.get('simulate_outfile', '')
            # filename = os.path.basename(file_simulate_outfile)
            simulate_out_filename = os.path.basename(file_simulate_outfile)
            file_ref = request.session.get('encode_outfile', '')

            def count_bases(file_ref):
                total_bases = 0
                with open(file_ref, "r") as f:
                    for i, line in enumerate(f):
                        if i == 0:  # 跳过第一行
                            continue
                        if not line.startswith(">"):  # 跳过注释行
                            total_bases += len(line.strip())
                return total_bases

            # 使用示例

            print("总碱基数:", count_bases(file_ref))
            request.session['total_base']=count_bases(file_ref)
            ref_filename = os.path.basename(file_ref)
            # 后续可以使用 simulate_outfile 和 encode_outfile 安全处理
            print("Simulate file:", simulate_outfile)
            print("Reference file:", encode_outfile)
            # print(f'file_simulate_outfile:{file_simulate_outfile}\nfile_ref:{file_ref}')
            #获得原始的文件名字
            context['orifile_filename'] = os.path.basename(request.session.get('filename',''))
            # print(f"filename2:{request.session.get('cluster_or_rec_file','')}\norifile_filename:{request.session.get('filename','')}")
#------------------------------------------------------------------------------------------------------------------------------------------

            #1.不需要聚类的情况
            user_input = request.POST
            if user_input.get('cluster_method','reference') == 'no':
                origin_file=request.session.get("filename","")
                request.session['reconstruct']=user_input.get('reconstruct','no')
                request.session['cluster_method']='no'
                context['base'] = {**initial_params,**request.session}
                context['reconstruct'] = False
                request.session['cluster_or_rec_file'] = file_simulate_outfile
                # cluster_or_rec_file用于最后的解码文件
                request.session['real_copy_number'] = None
                cluster_or_rec_file = request.session.get('cluster_or_rec_file', '')
                if cluster_or_rec_file == '':
                    cluster_or_rec_file = forclusterfile

                print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")

                # 如果有这个文件，那么就进行预览
                preview_simulate = read_file_head(forclusterfile)
                preview_ref = read_file_head(encode_outfile)
                preview_decode = read_file_head(cluster_or_rec_file)
                preview_origin = get_preview_data(origin_file)

                context['preview_simulate'] = preview_simulate
                context['preview_ref'] = preview_ref
                context['preview_decode'] = preview_decode
                context['preview_origin'] = preview_origin
                context['forclusterfile_filename'] = os.path.basename(forclusterfile)
                context['encode_outfile_filename'] = os.path.basename(encode_outfile)
                context['file_for_decode'] = os.path.basename(cluster_or_rec_file)
                context['ori_filename'] = os.path.basename(origin_file)
                context["need_copy_num"]=1
                return render(request, 'decode.html', context)
            print(f'file_ref:{file_ref}\nfile_simulate_outfile:{file_simulate_outfile}')
            print(request.POST.keys())

            #------------------------------------------------------------------------------------------------------------------------------------------

            #2.需要聚类的情况，聚类后的序列不保留param，并且重建之后的文件不允许上传 只允许自己生成。
            request.session['reconstruct']=user_input.get('reconstruct','no')
            request.session['confidence'] = user_input.get('confidence', 'no')
            request.session['cluster_method']=user_input.get('cluster_method','index')
            request.session['copy_number']=int(user_input.get('copy_number',10))

            request.session['cluster_or_rec_file'] = file_simulate_outfile
            context['base'] = {**initial_params, **request.session}
            context['reconstruct']=False
            # print(f"context:{context}")
            save_infos={}
            cluster_with_filename = output_dir + f"cluster.{os.path.basename(request.session.get('encode_outfile', 'fasta'))}"

    #------------------------------------------------------------------------------------------------------------------------------------------

            # 2.1 使用ref聚类 聚类不考虑copynum
            if user_input.get('cluster_method','reference') == 'reference':
                lens = -1
                cluster_file_path = cluster_by_ref(file_ref,file_simulate_outfile,int(lens),
                                                   cluster_with_filename,
                                                   # request.session['copy_number'],
                                                   output_dir,)
                # ori_dna_sequences, all_seqs = getoriandallseqs_nophred(cluster_file_path.get('cluster_seqs_path',output_dir+'cluster.fasta'))
                # dna_sequences = getRadomSeqsNoQua(all_seqs, int(user_input.get('copy_number',10)))
                # saveclusterfile(output_dir + 'cluster.fasta', ori_dna_sequences, dna_sequences)
    # ------------------------------------------------------------------------------------------------------------------------------------------

            # 2.2使用index聚类

            else:

                lens = user_input.get('index_length',12)
                cluster_file_path = cluster_by_index(file_ref,file_simulate_outfile,int(lens),cluster_with_filename)
            # request.session['cluster_or_rec_file'] = cluster_file_path.get('cluster_seqs_path',
            #                         output_dir+f"cluster.fasta")

            #对于聚类之后的信息保存到session中
            request.session['cluster_or_rec_file'] = cluster_file_path.get('cluster_seqs_path',cluster_with_filename)
            # 聚类后的序列不保留param，故聚类后保存到session，方便解码时获取
            request.session['param'] = cluster_file_path.get('param','')
            save_infos['cluster_time']=cluster_file_path.get('cluster_time', '')
            save_infos['cluster_phred_path']=cluster_file_path.get('cluster_phred_path', '')
            view_session(request)

            #聚类后检查是否有丢失
            ori_dna_sequences, all_seqs,_ = getoriandallseqs_nophred(request.session['cluster_or_rec_file'],1000)
            lasti = [i for i in range(len(all_seqs)) if len(all_seqs[i]) == 0]
            last_oriseqs = [ori_dna_sequences[i] for i in lasti]
            print(f"注意，这里有{len(last_oriseqs)}条序列丢失！")


# ------------------------------------------------------------------------------------------------------------------------------------------

            # 4.需要重建序列，重建后的序列也不保留param 重建序列考虑 copy_number
            if user_input.get('reconstruct','no') == 'yes':
                # reconstruct_file_path,reconstruct_time,editerrorrate,seqerrorrate = reconstruct_seq(user_input.get('rebuild_method','SeqFormer'),
                #                                         user_input.get('confidence','no'),'',
                #                                         cluster_file_path,
                #                                         int(user_input.get('copy_number',10)),
                #                                         output_dir)

                reconstruct_model = 'second'
                if file_simulate_outfile.find('fastq') > 0:
                    reconstruct_model = 'third'
                reconstruct_file_path,reconstruct_time,editerrorrate,seqerrorrate = reconstruct_seq(user_input.get('rebuild_method','SeqFormer'),
                                                        user_input.get('confidence','no'),'',
                                                        cluster_file_path,reconstruct_model,
                                                        int(user_input.get('copy_number',10)),
                                                        output_dir)


                request.session['cluster_or_rec_file'] = reconstruct_file_path
                save_infos['reconstruct_time']=reconstruct_time
                save_infos['edit_errorrate']=editerrorrate
                save_infos['seq_errorrate']=seqerrorrate
                context["need_copy_num"]=1
                request.session['real_copy_number']=user_input.get('copy_number',10)
            # decode file os.path.basename(request.session.get('cluster_or_rec_file',''))
            # context['file_for_decode'] = os.path.basename(request.session.get('cluster_or_rec_file',''))
            # preview_simulate = read_file_head(forclusterfile)
            cluster_or_rec_file = request.session.get('cluster_or_rec_file', '')
            origin_file = request.session.get("filename", "")
            preview_simulate = read_file_head(forclusterfile)
            preview_ref = read_file_head(encode_outfile)
            preview_decode = read_file_head(cluster_or_rec_file)
            preview_origin = get_preview_data(origin_file)


            context['preview_simulate'] = preview_simulate
            context['preview_ref'] = preview_ref
            context['preview_decode'] = preview_decode
            context['preview_origin'] = preview_origin
            context['forclusterfile_filename'] = os.path.basename(forclusterfile)
            context['encode_outfile_filename'] = os.path.basename(encode_outfile)
            context['file_for_decode'] = os.path.basename(cluster_or_rec_file)
            context['ori_filename'] = os.path.basename(origin_file)

            print( os.path.basename(request.session.get('cluster_or_rec_file','')))
            # write_dict_to_csv(save_infos,writefilepath)
            # context['base']['filename2'] = request.session.get('cluster_or_rec_file','')
            return render(request, 'decode.html', context)
        except Exception as e:
            print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")
            metrics = request.session.get("metrics", {})
            request.session.flush()
            request.session["metrics"] = metrics
            request.session['simulate_outfile'] = forclusterfile
            request.session['encode_outfile'] = encode_outfile
            request.session['matrices'] = matrices
            request.session['filename'] = filename
            # forclusterfile = simulate_outfile
            # if forclusterfile =='':
            #     forclusterfile=encode_outfile
            # request.session.flush()

            # 如果有这个文件，那么就进行预览
            preview_simulate = read_file_head(forclusterfile)
            preview_ref = read_file_head(encode_outfile)

            # 当get的时候不会传入 cluster和decode
            context = {'base': initial_params, }
            #重置这个context
            context['preview_simulate'] = preview_simulate
            context['preview_ref'] = preview_ref
            context['forclusterfile_filename'] = os.path.basename(forclusterfile)
            context['encode_outfile_filename'] = os.path.basename(encode_outfile)
            context['errors']="Please make sure you have performed a simulation or uploaded a simulation file. Clustering cannot be performed without a simulation file."
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(f"完整的堆栈跟踪信息:\n{''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))}")
            return render(request, 'decode.html', context)

# ------------------------------------------------------------------------------------------------------------------------------------------
    #按下了decode按钮之后的操作
    elif request.method == 'POST' and 'decodeBtn' in request.POST:
        #1.默认 通过ref/index聚类，不用重建，得到文件cluster.fasta；
        #2.通过ref/index聚类,需要重建，得到文件reconstruct.fasta/reconstruct.fastq;
        #3.无需聚类，无需重建，使用测序文件simulated_seqsr1r2_.fasta
        decode_file = request.session.get('cluster_or_rec_file', '')

        # request.session['encode_outfile']='/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/7_hedges.fasta'
        #hedges TODO

        print(f"encode_outfile:{request.session.get('encode_outfile', '')}")
        with open(request.session.get('encode_outfile', ''), 'r') as f:
            lines = f.readlines()
        param = lines[0]
        request.session['param'] = param
        if decode_file == '':
            decode_file = forclusterfile

        file_ori = request.session.get('filename', '')
        if not file_ori or not os.path.exists(file_ori):
            cluster_or_rec_file = request.session.get('cluster_or_rec_file', '')
            origin_file = request.session.get("filename", "")
            preview_simulate = read_file_head(forclusterfile)
            preview_ref = read_file_head(encode_outfile)
            preview_decode = read_file_head(cluster_or_rec_file)
            preview_origin = get_preview_data(origin_file)

            context['preview_simulate'] = preview_simulate
            context['preview_ref'] = preview_ref
            context['preview_decode'] = preview_decode
            context['preview_origin'] = preview_origin
            context['forclusterfile_filename'] = os.path.basename(forclusterfile)
            context['encode_outfile_filename'] = os.path.basename(encode_outfile)
            context['file_for_decode'] = os.path.basename(cluster_or_rec_file)
            context['ori_filename'] = os.path.basename(origin_file)
            context['errors']="No origin file uploaded. Please upload one"
            print(os.path.basename(request.session.get('cluster_or_rec_file', '')))
            # write_dict_to_csv(save_infos, writefilepath)
            # context['base']['filename2'] = request.session.get('cluster_or_rec_file','')
            return render(request, 'decode.html', context)
        # 获取上传到服务器的图片地址 file2为decodefile file3为originfile
        # fileres2 = upload_file(request, 'file2')
        # if fileres2.status_code == 200 and 'file2' in request.FILES:
        #     filename = os.path.join(media_FOLDER, request.FILES['file2'].name)
        #     # request.session['encode_outfile'] = filename
        #     print(f"✅ decode file uploaded to: {filename}")
        #
        # # 尝试上传 file3
        # fileres3 = upload_file(request, 'file3')
        # if fileres3.status_code == 200 and 'file3' in request.FILES:
        #     file_ori  = os.path.join(media_FOLDER, request.FILES['file3'].name)
        #     request.session['originfile'] = file_ori
        #     print(f"✅ origin file uploaded to: {file_ori }")
        # else:
        #     file_ori = request.session.get('filename', '')
        #     print(f"the upload originfile path is :{file_ori}")
        #若有文件未上传，则提示
        # file_ori = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/media/1.jpg'
        # if filename == '' or file_ori == '':
        #     context['base'] = {**initial_params, **request.session}
        #     context['errors'] = 'please upload file first！'
        #     context['base']['filename2'] = os.path.basename(request.session.get('cluster_or_rec_file', ''))
        #     return render(request, 'decode.html', context)

        # context['filename1'] = request.session.get('file_ref_name','')
        # context['filename2'] = os.path.basename(filename)
        # context['orifile_filename'] = os.path.basename(file_ori)

        print(f"fordecodefile:{decode_file}\noriginfile:{file_ori}")
        decode_outfile = decode_file
        # decode_outfile = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/decode/cluster.9_DNAFountain.fasta'
        # decode_outfile = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/decode/cluster.6_hedges.fasta'
        # decode_outfile = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/decode/cluster.'
        # decode_outfile = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/decode/reconstruct.fastq'


        # 处理文件，构造成这样
        # >seq0
        # GGAAGGACGAGTGAGGCCGTAAAGCAGCAACGACGGACGGCCGTCCGGCCAGCCTTAATTAGATAACTCCAGACTTCCGACCGTCCGACTTATCTATGTCCCTACTCCGATAAGCAACC
        # >seq1
        # GGAAGGACGAGTGAGGCCGTAAAGCAGCAACGACGGACGGCCGTCCGCCAGCCTTAATTAGATAACTCCAGACTTCCGACCGTCCGTACTTATCTATGTCCCTACTCCGATAAGCAACC
        #1.不用聚类
        # decode_outfile = request.session.get('cluster_or_rec_file',file_simulate_outfile)
        # decode_outfile = '/home1/hongmei/00work_files/0000/0isecondwork/Evaluation_platform/POLUS/files/index_DNAFountain_1.fasta'
        allseqs,allconfidence=[],[]
        user_input = request.POST
        method = user_input.get('method','fountain')
        copy_number = int(user_input.get('copy_number_decode',10))

# ------------------------------------------------------------------------------------------------------------------------------------------
        #1、没有进行聚类的情况
        if str(decode_outfile).find('simulated_seqsr1r2') != -1:
            #直接使用模拟后的序列进行解码则无法限制copy_number解码，如果要限制copy_number，需要先聚类
            print(f"**************************************1*********************************************")
            # 处理 simulated_seqsr1r2_.fasta/simulated_seqsr1r2_.fastq
            allseqs,param = readandsave_noline0(decode_outfile,decode_outfile + '.forreconstruct')


        # 2.需要聚类，不用重建
        elif str(decode_outfile).find('cluster') != -1:
            print(f"**************************************2*********************************************")
            # 处理 cluster.fasta+cluster.phred
            ori_dna_sequences, allclusterseqs,param = getoriandallseqs_nophred(decode_outfile,copy_number)
            allseqs = savelistfasta(decode_outfile + '.forreconstruct',allclusterseqs)
            request.session['real_copy_number']=user_input.get('copy_number_decode',10)

        # 3.需要聚类，需要重建
        elif str(decode_outfile).find('reconstruct') != -1:
            print(f"**************************************3*********************************************")
            # 处理 reconstruct.fasta/reconstruct.fastq
            if str(decode_outfile).endswith('.fastq'):
                allseqs,allconfidence,param = readandsavefastq(decode_outfile,decode_outfile + '.forreconstruct')
            else:
                allseqs,param = readandsave(decode_outfile,decode_outfile + '.forreconstruct')
        else:
            print(f"**************************************4*********************************************")
            # 处理 any
            allseqs,param = read_unknown_andsave(decode_outfile,decode_outfile + '.forreconstruct')
        #处理hedges
        # allseqs,param = read_unknown_andsave_hedges(decode_outfile,decode_outfile + '.forreconstruct',10)
        if param!='':
            request.session['param'] = param.rstrip()
        # TODO 后面需要检查 request.session['param'] 是否存在
        # 如果没有param 那么就报错 并且返回原始的解码界面
        soft_data = {
            'copy_number' : user_input.get('copy_number_decode', 10),
            'allconfidence':allconfidence,
            'decision':user_input.get('decision','hard')
        }
        param = request.session.get('param','')

        print("method:"+method)
        # param = "method:YYC,seq_len:260,gc_bias:0.2,max_homopolymer:5,rs_num:4,crc_num:0,max_iterations:100,index_length:17,total_count:106584,totalBit:22489144,binSegLen:211,leftPrimer:,rightPrimer:,fileExtension:.mp4,bRedundancy:0,RSNum:4"
        # request.session['param'] = param
        try:
            if method == 'fountain':
                print(f"------开始解码------,fountain param:{param}")
                decoded_data = getDnaFountainDecodeInfo(decode_outfile + '.forreconstruct',file_ori,allseqs,soft_data,param)
            elif method == 'YYC':
                print(f"------开始解码------,YYC param----------------:{param}")
                print(decode_outfile + '.forreconstruct')
                decoded_data = getYYCDecodeInfo(decode_outfile + '.forreconstruct',file_ori,allseqs,soft_data,param,output_dir)
            elif method == 'derrick':
                print(f"------开始解码------,derrick param----------------:{param}")
                decoded_data = getDerrickDecodeInfo(decode_outfile + '.forreconstruct',file_ori,allseqs,param,output_dir)
            elif method == 'hedges':
                print(f"------开始解码------,hedges param----------------:{param}")
                decoded_data = getHedgesDecodeInfo(decode_outfile + '.forreconstruct',file_ori,allseqs,param,output_dir)
            elif method == 'PolarCode':
                if request.session.get('matrices', '') != '':
                    matrices = request.session['matrices']
                    print(f'matrices no null:{matrices.keys()}')
                print(f"------开始解码------,Polar param----------------:{param}")
                decoded_data = getPolarDecodeInfo(decode_outfile + '.forreconstruct',file_ori,allseqs,allconfidence,param,matrices,output_dir)
                print(f'decoded_data:{decoded_data}')
        # except Exception as e:
        #     request.session.flush()
        #     request.session['simulate_outfile'] = simulate_outfile
        #     request.session['encode_outfile'] = encode_outfile
        #     context = {'base': initial_params, }
        #     context['filename'] = os.path.basename(forclusterfile)
        #
        #     print("捕获到异常:")
        #     print(f"异常类型: {type(e)}")
        #     print(f"异常信息: {e}")
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     print(f"完整的堆栈跟踪信息:\n{''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))}")
        #     return render(request, 'decode.html', context)
        except Exception as e:
            # ！！不要 flush，会清掉聚类/重建的上下文！！
            # request.session.flush()

            # 打印错误日志
            print("捕获到异常:")
            print(f"异常类型: {type(e)}")
            print(f"异常信息: {e}")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            full_trace = ''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))
            print(f"完整的堆栈跟踪信息:\n{full_trace}")

            # 回填上下文：保留“聚类/重建后”的预览与文件名，附带错误信息，页面可直接修改参数重试
            error_msg = f"Decode failed: {e}"
            context = _build_decode_page_context(
                initial_params=initial_params,
                request=request,
                forclusterfile=forclusterfile,
                encode_outfile=encode_outfile,
                error_msg=error_msg
            )

            # 让前端表单保持用户选择，便于直接重试
            user_input = request.POST
            context['base']['method'] = user_input.get('method', 'fountain')
            context['base']['copy_number_decode'] = user_input.get('copy_number_decode', 10)
            context['base']['decision'] = user_input.get('decision', 'hard')
            context['base']['confidence'] = user_input.get('confidence', request.session.get('confidence', 'no'))

            # 如果有 reconstruct/cluster 信息，补充到页面（可选：显示用）
            context['reconstruct_file'] = request.session.get('cluster_or_rec_file', '')
            context['param'] = request.session.get('param', '')
            # context['errors']="Please make sure you have chosen the right method."
            return render(request, 'decode.html', context)

        # elif method == 'YYC':
        #     print(f"encode 开始解码 YYC-----------:{user_input}")
        #     info,output_file_path = getYYCEncodeInfo(user_input,filename)
        # elif method == 'derrick':
        #     print(f"encode 开始解码 derrick-----------:{user_input}")
        #     info,output_file_path = getDerrickEncodeInfo(user_input,filename)
        # elif method == 'PolarCode':
        #     print(f"encode 开始解码 PolarCode-----------:{user_input}")
        #     info,output_file_path = getPolarEncodeInfo(user_input,filename)
        # else:
        #     print(f"encode 开始解码 hedges-----------:{user_input}")
        #     info,output_file_path = getHedgesEncodeInfo(user_input,filename)
        decoded_data_infos = {'badbits': decoded_data.get('badbits', 0),
                              'allbits': decoded_data.get('allbits', 0),
                              'bits_recov': decoded_data.get('bits_recov', 0),
                              'decode_time':decoded_data.get('decode_time',0),
                              }
        metrics = request.session["metrics"]
        print(f"metrics:{metrics}")
        view_session(request)
        avogadro = 6.022e23  # 阿伏伽德罗常数
        if request.session.get('real_copy_number', 0) != None:

            Physical_Density = (float(metrics['Logical Ratio']) / 8) * (avogadro / 330) * (1 / int(request.session.get('real_copy_number', 0)))
            metrics["Sequencing Depth Requirement"] = request.session.get('real_copy_number', 0)
            if str(decode_outfile).endswith(".fastq"):
                base_cost = 0.000002365  # 三代
            else:
                base_cost = 0.00000328  # 二代
            metrics['Costs'] = (
                    float(request.session.get('real_copy_number', 0))
                    * float(request.session['total_base'])
                    * base_cost
                    + float(request.session['total_base'])
                    * 0.002
            )
            # metrics["Physical Density"] = Physical_Density
            theoretical_max = 4.55e22
            physical_ratio = (theoretical_max - Physical_Density) / theoretical_max
            metrics["Physical Ratio"] = physical_ratio
        method1=user_input.get('method', 'fountain')
        metrics["Decoding Runtime"] = decoded_data.get('decode_time', 0)
        metrics["File Recovery"] = decoded_data.get('bits_recov', 0)
        metrics["Logical Ratio"] = float((2-metrics["Logical Ratio"])/2)


        filename1= os.path.basename(request.session.get("filename"))

        os.makedirs(output_dir, exist_ok=True)

        # 拼接最终文件名，例如 output_dir/method_filename.csv
        csv_filename = os.path.join(output_dir, f"{method1}_{filename1}.csv")

        request.session['evaluate_filename']=csv_filename
        # 写入 CSV 文件
        if metrics:  # metrics 是 dict
            # 复制一份，避免直接修改 session 里的 dict
            row = dict(metrics)
            row["Method"] = method1
            row["Filename"] = filename1

            keys = ["Method", "Filename"] + list(metrics.keys())  # 保证 Method 和 Filename 在最前面

            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerow(row)
        print(f"CSV 文件已生成: {csv_filename}")

        # write_dict_to_csv(decoded_data_infos,writefilepath)
        request.session['decodefile'] = decoded_data.get('decodefile')
        request.session['copy_number']=user_input.get('copy_number',10)
        request.session['decision']=user_input.get('decision','hard')
        context['decode']=True
        context['decoded_data']=decoded_data
        context['base'] = {**initial_params, **request.session}
        context['base']['method'] = method

        # context['base']['confidence']=user_input.get('confidence')
        # context['base']['copy_number']=user_input.get('copy_number')
        # context['base']['decision']=user_input['decision']
        # print(f"synseq_view 开始解码-----------:{context}")
        return render(request, 'decode.html', context)
    elif request.method == 'POST' and 'restart' in request.POST:
        context = {
            'base': initial_params,
        }
        request.session.flush()
        print(f"重新开始-----------")
        return render(request, 'encode.html', context)
    elif request.method == 'POST' and 'redoDecode' in request.POST:
        # ✅ 不要 flush，会保留聚类/重建结果
        # 保留：simulate_outfile / encode_outfile / cluster_or_rec_file / param / 预览
        # 清理：上次解码结果，让前端解码表单解锁
        try:
            # 清掉上次 decode 的状态（避免禁用）
            request.session.pop('decodefile', None)

            # 仍然使用现有的聚类/重建输出作为解码输入
            cluster_or_rec_file = request.session.get('cluster_or_rec_file', '')
            origin_file = request.session.get("filename", "")
            forclusterfile = request.session.get('simulate_outfile', '')
            encode_outfile = request.session.get('encode_outfile', '')

            # 预览区（继续显示，方便对照）
            preview_simulate = read_file_head(forclusterfile) if forclusterfile else ''
            preview_ref = read_file_head(encode_outfile) if encode_outfile else ''
            preview_decode = read_file_head(cluster_or_rec_file) if cluster_or_rec_file else ''
            preview_origin = get_preview_data(origin_file) if origin_file else {'success': False}

            context = {
                'base': {**initial_params, **request.session},
                # 让页面显示“已完成聚类→可解码”的段落
                'cluster': True,
                # 关键：不传 decoded_data / decode，让解码表单解锁
                # 'decode': False,
                # 'decoded_data': None,
                'preview_simulate': preview_simulate,
                'preview_ref': preview_ref,
                'preview_decode': preview_decode,
                'preview_origin': preview_origin,
                'forclusterfile_filename': os.path.basename(forclusterfile) if forclusterfile else '',
                'encode_outfile_filename': os.path.basename(encode_outfile) if encode_outfile else '',
                'file_for_decode': os.path.basename(cluster_or_rec_file) if cluster_or_rec_file else '',
                'ori_filename': os.path.basename(origin_file) if origin_file else '',
            }

            # 为了 UX：把上次的解码参数当默认值回填（如果有）
            # method/decision/copy_number_decode/confidence 这些，优先用 session 或 POST
            user_last_method = request.session.get('method') or 'fountain'
            context['base']['method'] = user_last_method
            context['base']['decision'] = request.session.get('decision', 'hard')
            context['base']['copy_number_decode'] = request.session.get('copy_number_decode', 10)
            context['base']['confidence'] = request.session.get('confidence', request.session.get('confidence', 'no'))

            return render(request, 'decode.html', context)
        except Exception as e:
            # 失败也不要 flush，上报错误并回到页面
            error_msg = f"Reset decode form failed: {e}"
            context = _build_decode_page_context(
                initial_params=initial_params,
                request=request,
                forclusterfile=request.session.get('simulate_outfile', ''),
                encode_outfile=request.session.get('encode_outfile', ''),
                error_msg=error_msg
            )
            return render(request, 'decode.html', context)
    elif request.method == 'POST' and 'redoCluster' in request.POST:
        # ✅ 只回到“聚类参数选择”阶段；不 flush，保留已有文件与预览
        try:
            # 取现有文件路径（可能为空就给空串）
            print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")
            metrics = request.session.get("metrics", {})
            request.session.flush()
            request.session["metrics"] = metrics
            request.session['simulate_outfile'] = forclusterfile
            request.session['encode_outfile'] = encode_outfile
            request.session['matrices'] = matrices
            request.session['filename'] = filename
            # forclusterfile = simulate_outfile
            # if forclusterfile =='':
            #     forclusterfile=encode_outfile
            # request.session.flush()

            # 如果有这个文件，那么就进行预览
            preview_simulate = read_file_head(forclusterfile)
            preview_ref = read_file_head(encode_outfile)

            # 当get的时候不会传入 cluster和decode
            context = {'base': initial_params, }
            context['preview_simulate'] = preview_simulate
            context['preview_ref'] = preview_ref
            context['forclusterfile_filename'] = os.path.basename(forclusterfile)
            context['encode_outfile_filename'] = os.path.basename(encode_outfile)
            # filename= forclusterrecfile
            # context['base']['filename'] = filename
            return render(request, 'decode.html', context)

        except Exception as e:
            error_msg = f"Return to cluster parameters failed: {e}"
            # 复用你的构造器，保留上下文与错误
            context = _build_decode_page_context(
                initial_params=initial_params,
                request=request,
                forclusterfile=request.session.get('simulate_outfile', ''),
                encode_outfile=request.session.get('encode_outfile', ''),
                error_msg=error_msg
            )
            return render(request, 'decode.html', context)

    print(f"simulate_outfile:{forclusterfile},encode_outfile:{encode_outfile}")
    metrics = request.session.get("metrics", {})
    request.session.flush()
    request.session["metrics"] = metrics
    request.session['simulate_outfile']=forclusterfile
    request.session['encode_outfile']=encode_outfile
    request.session['matrices']=matrices
    request.session['filename']=filename
    # forclusterfile = simulate_outfile
    # if forclusterfile =='':
    #     forclusterfile=encode_outfile
    # request.session.flush()

    # 如果有这个文件，那么就进行预览
    preview_simulate = read_file_head(forclusterfile)
    preview_ref = read_file_head(encode_outfile)


    #当get的时候不会传入 cluster和decode
    context = {'base': initial_params,}
    context['preview_simulate'] = preview_simulate
    context['preview_ref'] = preview_ref
    context['forclusterfile_filename'] = os.path.basename(forclusterfile)
    context['encode_outfile_filename'] = os.path.basename(encode_outfile)
    # filename= forclusterrecfile
    # context['base']['filename'] = filename
    return render(request, 'decode.html', context)

def reconstruct_view(request):
    media_FOLDER = get_media_path_from_request(request)
    # DNAFountainEncode(input_file_path=file_input, output_dir=output_dir, sequence_length=sequence_length, max_homopolymer=max_homopolymer,
    #                           rs_num=rs_num,add_redundancy=add_redundancy, add_primer=add_primer, primer_length=primer_length, redundancy=dnafountain_redundancy)
    return render(request, 'test.html',{'test':test11()})


def home(request):
    ip_address = get_client_ip(request)
    media_path = get_ip_media_folder(ip_address,'media')
    return render(request, 'home.html')



#文件上传的处理，文件预览

import os
import base64
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings

def upload_for_preview(request):
    try:
        if request.method == 'POST':
            media_FOLDER = get_media_path_from_request(request)
            uploaded_file = request.FILES.get('file_for_preview')
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file was uploaded.'})

            file_type = uploaded_file.content_type

            # 保存文件到本地
            save_dir = os.path.join(media_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, uploaded_file.name)

            with default_storage.open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            request.session['filename'] = save_path
            view_session(request)
            # 准备预览内容
            file_content = ""
            print("Detected file_type:", file_type)
            if file_type.startswith('image/'):
                uploaded_file.seek(0)
                encoded_string = base64.b64encode(uploaded_file.read()).decode('utf-8')
                file_content = f"data:{file_type};base64,{encoded_string}"
            elif file_type.startswith('audio/') or file_type.startswith('video/'):
                uploaded_file.seek(0)
                print("Matched audio/video preview")
                encoded_string = base64.b64encode(uploaded_file.read()).decode('utf-8')
                file_content = f"data:{file_type};base64,{encoded_string}"
            elif file_type.startswith('text/'):
                uploaded_file.seek(0)
                # 如果文件较大，读取前500行，否则读取4096字节
                if uploaded_file.size > 5 * 1024 * 1024:
                    lines = []
                    for i in range(100):
                        line = uploaded_file.readline()
                        if not line:
                            break
                        lines.append(line.decode('utf-8', errors='ignore'))
                    file_content = ''.join(lines)
                else:
                    file_content = uploaded_file.read(4096).decode('utf-8', errors='ignore')

            else:
                file_content = f"'{uploaded_file.name}' is a binary file. No text preview available."

            return JsonResponse({
                'success': True,
                'file_name': uploaded_file.name,
                'file_type': file_type,
                'file_content': file_content,
                'file_path': save_path,
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#如果重新上传了文件之后 更新一下需要保存的info信息
def update_metrics_from_file(request, save_path):
    """
    从 encode_outfile 第一行提取指标并更新到 request.session['metrics'] 中
    """

    with open(save_path, 'r') as f:
        first_line = f.readline().strip()

    # 转成 dict
    items = dict(x.split(":", 1) for x in first_line.split(","))

    # 如果没有 metrics 就新建
    if request.session["metrics"]=={}:
        metrics = {
            "Costs": None,  # 先占位，解码时更新
            "Sequencing Depth Requirement": None,  # 先占位，解码时更新
            "Encoding Runtime": None,
            "Decoding Runtime": None,  # 先占位，解码时更新
            "Physical Ratio": None,  # 先占位，解码时更新
            "Logical Ratio": None,
            "GC Contents": None,
            "Maximum Homopolymers Length":None,
            "File Recovery": None  # 先占位，解码时更新
        }
        request.session["metrics"] = metrics
    metrics = request.session["metrics"]

    # 更新四个指标
    metrics["Encoding Runtime"] = float(items.get("Encoding Runtime", 0))
    metrics["Logical Ratio"] = float(items.get("Logical Ratio", 0))
    metrics["GC Contents"] = float(items.get("GC Contents", 0))
    metrics["Maximum Homopolymers Length"] = int(float(items.get("Maximum Homopolymers Length", 0)))

    # 保存回 session
    request.session["metrics"] = metrics
    request.session.modified = True

def preview_fasta_file_for_simulate(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES.get('file_for_preview')

            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file was uploaded.'})

            media_FOLDER = get_media_path_from_request(request)
            file_name = uploaded_file.name.lower()

            # 支持 fasta 和 fastq 相关扩展
            allowed_ext = ('.fasta', '.fa', '.fna', '.fastq', '.fq')
            if not file_name.endswith(allowed_ext):
                return JsonResponse({
                    'success': False,
                    'error': 'Only FASTA (.fasta, .fa, .fna) and FASTQ (.fastq, .fq) files are supported for preview.'
                })

            # 保存文件到本地
            save_dir = os.path.join(media_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, uploaded_file.name)

            with default_storage.open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # 读取前 100 行作为预览内容
            # 从保存后的本地文件重新读取前 100 行
            lines = []
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(100):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            file_content = ''.join(lines)

            # 预览文件类型
            file_type = 'text/fasta' if file_name.endswith(('.fasta', '.fa', '.fna')) else 'text/fastq'

            # ✅ 更新 session
            view_session(request)
            request.session['encode_outfile'] = save_path

            request.session['filename'] = "Please upload a new original file"
            update_metrics_from_file(request, save_path)

            print("== SESSION DEBUG ==")
            for key, value in request.session.items():
                print(f"{key}: {value}")

            return JsonResponse({
                'success': True,
                'file_name': uploaded_file.name,
                'file_type': file_type,
                'file_content': file_content,
                'file_path': save_path,
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
def preview_fasta_file_for_cluster_and_reconstruct(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES.get('file_for_preview')
            uploader_prefix = request.POST.get('uploader_prefix')
            print(uploader_prefix)
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file was uploaded.'})

            media_FOLDER = get_media_path_from_request(request)
            file_name = uploaded_file.name.lower()

            # 支持 fasta 和 fastq 相关扩展
            allowed_ext = ('.fasta', '.fa', '.fna', '.fastq', '.fq')
            if not file_name.endswith(allowed_ext):
                return JsonResponse({
                    'success': False,
                    'error': 'Only FASTA (.fasta, .fa, .fna) and FASTQ (.fastq, .fq) files are supported for preview.'
                })

            # 保存文件到本地
            save_dir = os.path.join(media_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, uploaded_file.name)

            with default_storage.open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # 读取前 100 行作为预览内容
            # 从保存后的本地文件重新读取前 100 行
            lines = []
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(100):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            file_content = ''.join(lines)

            # 预览文件类型
            file_type = 'text/fasta' if file_name.endswith(('.fasta', '.fa', '.fna')) else 'text/fastq'

            # ✅ 更新 session
            if uploader_prefix=='ref':

                request.session['encode_outfile'] = save_path
                update_metrics_from_file(request, save_path)

                # request.session['filename'] = uploaded_file.name
            if uploader_prefix=='simulate':
                request.session['simulate_outfile'] = save_path
                update_metrics_from_file(request, save_path)

            print("== SESSION DEBUG ==")
            for key, value in request.session.items():
                print(f"{key}: {value}")

            return JsonResponse({
                'success': True,
                'file_name': uploaded_file.name,
                'file_type': file_type,
                'file_content': file_content,
                'file_path': save_path,
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def preview_fasta_file_for_decode(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES.get('file_for_preview')
            uploader_prefix = request.POST.get('uploader_prefix')
            print(uploader_prefix)
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file was uploaded.'})

            media_FOLDER = get_media_path_from_request(request)
            file_name = uploaded_file.name.lower()

            # 支持 fasta 和 fastq 相关扩展
            allowed_ext = ('.fasta', '.fa', '.fna', '.fastq', '.fq')
            if not file_name.endswith(allowed_ext):
                return JsonResponse({
                    'success': False,
                    'error': 'Only FASTA (.fasta, .fa, .fna) and FASTQ (.fastq, .fq) files are supported for preview.'
                })

            # 保存文件到本地
            save_dir = os.path.join(media_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, uploaded_file.name)

            with default_storage.open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # 读取前 100 行作为预览内容
            # 从保存后的本地文件重新读取前 100 行
            lines = []
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(100):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            file_content = ''.join(lines)

            # 预览文件类型
            file_type = 'text/fasta' if file_name.endswith(('.fasta', '.fa', '.fna')) else 'text/fastq'

            # ✅ 更新 session
            if uploader_prefix=='ref':

                request.session['encode_outfile'] = save_path
                # request.session['filename'] = uploaded_file.name
            if uploader_prefix=='simulate':
                request.session['simulate_outfile'] = save_path
            if uploader_prefix == 'origin':

                request.session['filename'] = save_path
            print("== SESSION DEBUG ==")
            for key, value in request.session.items():
                print(f"{key}: {value}")

            return JsonResponse({
                'success': True,
                'file_name': uploaded_file.name,
                'file_type': file_type,
                'file_content': file_content,
                'file_path': save_path,
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# instruction
def instruction(request):
    return render(request, 'instruction.html')



#demo
def demo(request):

    return render(request, 'demo.html')


#evaluate模块

import csv, io
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

# 你的固定 9 个数值字段（按原始表头写）
NUMERIC_KEYS = {
    'Costs',
    'Sequencing Depth Requirement',
    'Encoding Runtime',
    'Decoding Runtime',
    'Physical Ratio',
    'Logical Ratio',
    'GC Contents',
    'Maximum Homopolymers Length',
    'File Recovery',
}

def _to_number(val):
    print(f"[DEBUG] 原值: {repr(val)}")

    if val == '':
        return 0   # 改成 0
    s = str(val).strip()
    if s == '' or s.lower() in {'na','none','null'}:
        return 0   # 改成 0
    try:
        if '.' in s or 'e' in s.lower():
            return float(s)
        return int(s)
    except Exception:
        # 去掉常见单位 % 和 s
        s_clean = s.replace('%', '').replace('s', '').strip()
        try:
            x = float(s_clean)
            if '%' in s:
                return x / 100.0
            return x
        except Exception:
            return 0   # 改成 0

@require_POST
@csrf_protect
def upload_csv(request):
    """
    接收多个 CSV（需表头），合并为 records。
    只使用你给定的字段名，不做别名映射。
    """
    files = request.FILES.getlist('csv_files')
    if not files:
        return JsonResponse({'status': 'err', 'msg': 'No files received'}, status=400)

    records = []
    seen_headers = set()

    for f in files:
        try:
            raw = f.read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                text = raw.decode('gbk', errors='ignore')

            reader = csv.DictReader(io.StringIO(text))
            if not reader.fieldnames:
                return JsonResponse({'status': 'err', 'msg': f'{f.name}: header not found'}, status=400)

            seen_headers.update(reader.fieldnames)

            for row in reader:
                norm = dict(row)  # 保留原始列名

                # 确保 filename / method 存在
                if 'Filename' not in norm or not str(norm.get('filename') or '').strip():
                    norm['filename'] = f.name
                if 'Method' not in norm or not str(norm.get('method') or '').strip():
                    norm['method'] = 'unknown'

                # 数值字段转型
                for k in NUMERIC_KEYS:
                    if k in norm:
                        norm[k] = _to_number(norm[k])
                    else:
                        norm[k] = None  # 缺失补 None

                records.append(norm)

        except Exception as e:
            return JsonResponse({'status': 'err', 'msg': f'Failed to parse {f.name}: {e}'}, status=400)

    # 表头顺序：filename, method, 你的 9 个指标 + 其它
    canonical_headers = ['Method', 'Filename'] + list(NUMERIC_KEYS)
    other_headers = [h for h in seen_headers if h not in canonical_headers]
    header = canonical_headers + other_headers
    print(records)
    return JsonResponse(
        {'status': 'ok', 'data': records, 'header': header},
        json_dumps_params={'ensure_ascii': False}
    )


def evaluate_view(request):
    media_FOLDER = get_media_path_from_request(request)
    context = {
        'base': {**initial_params},
        'MEDIA_URL':media_FOLDER
    }
    return render(request, 'evaluate.html', context)
