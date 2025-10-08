"""
重构后的 DNA 存储平台 Django 视图（views）

改动要点（结构与思路均有中文注释）：
- 统一与去重 imports，集中常量定义，避免魔法字符串散落各处；
- 抽取文件/预览/会话等通用逻辑为小型工具函数，减少重复代码；
- 通过守卫式（guard-clauses）提前返回，使命令式流程更清晰；
- 对外暴露的视图与关键工具函数均提供多行中文文档注释（说明功能、输入/输出、返回值、异常与边界）；
- I/O 层（上传/下载/预览）最小化且统一，方便后续替换为对象存储或队列；
- 保留原有行为与 URL，不改变前端依赖；若需增量迁移，可在测试环境中按路由逐步替换。

使用说明：将本文件替换原 views.py（或在 urls.py 中指向新的模块路径），首先在开发环境验证 imports 与路径是否正确。
"""
from __future__ import annotations

# ===============
# 标准库
# ===============
import base64
import mimetypes
import os
import sys
import traceback
from pathlib import Path
from typing import Dict

# ===============
# Django 依赖
# ===============
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render

# ===============
# 项目内部依赖（根据你的项目结构调整）
# ===============
from polls.Code.encode_all import (
    getDnaFountainEncodeInfo,
    getYYCEncodeInfo,
    getDerrickEncodeInfo,
    getHedgesEncodeInfo,
    getPolarEncodeInfo,
)
from polls.Code.utils import (
    SimuInfo,
    write_dict_to_csv,
    initial_params,
)
from polls.Code.simulate import adddt4simu_advanced
from polls.forms import EncodeHiddenForm

# ==============================================================================
# 常量
# ==============================================================================
UPLOAD_FOLDER = Path(os.getcwd()) / "upload"
MEDIA_ROOT_DIR = Path(os.getcwd()) / "media"
WRITE_FILEPATH = Path("./encodedecode_infos_0519.txt")
MAX_PREVIEW_LINES = 100

# ==============================================================================
# 工具函数：IP、路径、文件预览
# ==============================================================================

def get_client_ip(request) -> str:
    """
    获取客户端 IP（兼容反向代理后的 X-Forwarded-For）。

    参数
    ----
    request : HttpRequest
        Django 请求对象。

    返回
    ----
    str
        最佳可用的客户端 IP 字符串；若不可得，返回空串。

    说明
    ----
    - 若部署在 Nginx/Traefik 等反向代理后，应在代理层正确设置/透传
      X-Forwarded-For，否则此处可能拿到的是代理的内网地址。
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_ip_media_folder(ip_address: str, base_address: str = "media") -> str:
    """
    基于 IP 的隔离目录：确保并返回 `<cwd>/<base_address>/<ip>`。

    参数
    ----
    ip_address : str
        客户端 IP（会将冒号替换为下划线以兼容文件系统）。
    base_address : str, 默认 "media"
        根目录名；可切换为 "files" 等不同命名空间。

    返回
    ----
    str
        已确保存在的绝对路径。

    设计动机
    --------
    - 让每个用户/会话有独立工作区，避免文件名冲突与相互覆盖；
    - 后续若迁移到对象存储（S3/OSS），可用相同的 key 前缀策略。
    """
    base_media_folder = Path(os.getcwd()) / base_address
    ip_folder = base_media_folder / ip_address.replace(":", "_")
    ip_folder.mkdir(parents=True, exist_ok=True)
    return str(ip_folder)


def get_media_path_from_request(request) -> str:
    """
    便利函数：返回当前请求对应的基于 IP 的 `media/` 子目录。

    说明
    ----
    - 当前端进行预览/上传时，统一落盘到该目录，便于隔离与清理。
    """
    return get_ip_media_folder(get_client_ip(request), "media")


def get_files_path_from_request(request) -> str:
    """
    返回并确保 `files/` 下的按 IP 隔离的工作区，并创建常用子目录。

    行为
    ----
    - 自动创建 `decode/`, `plot/`, `simu/` 子目录；
    - 作为流水线各阶段（编码/模拟/解码/评估）的统一根目录。

    返回
    ----
    str
        绝对路径。
    """
    base = get_ip_media_folder(get_client_ip(request), "files")
    for sub in ("decode", "plot", "simu"):
        Path(base, sub).mkdir(parents=True, exist_ok=True)
    return base


def read_file_head(filepath: str, max_lines: int = MAX_PREVIEW_LINES) -> str:
    """
    安全读取文本文件前 `max_lines` 行，用于页面预览。

    参数
    ----
    filepath : str
        文本/类文本文件路径。
    max_lines : int, 默认 MAX_PREVIEW_LINES
        读取最大行数。

    返回
    ----
    str
        合并后的预览文本；若读取失败，返回用户友好提示。

    细节
    ----
    - 仅做轻量读取，不加载整文件，避免大文件阻塞请求线程；
    - 上层可考虑将重型预览改为异步任务 + 轮询。
    """
    try:
        out = []
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                out.append(line.rstrip())
        return "\n".join(out)
    except Exception:
        return "Please upload a correct file."


def get_preview_data(file_path: str) -> Dict[str, str]:
    """
    生成预览载荷：
    - 图片/视频：返回 base64 data URL；
    - 文本：返回前 ~3000 字符；
    - 其他：标记为不支持或错误。

    参数
    ----
    file_path : str
        目标文件的绝对路径。

    返回
    ----
    dict
        {"success": bool, "file_type": str, "file_content": str}

    设计权衡
    --------
    - 为兼容前端统一展示，直接返回 data URL；
    - 大文件请谨慎，必要时应限制大小或改为流式/缩略图。
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            return {"success": False, "file_type": "unknown", "file_content": ""}

        raw = Path(file_path).read_bytes()
        if mime_type.startswith("image/"):
            return {
                "success": True,
                "file_type": "image",
                "file_content": f"data:{mime_type};base64,{base64.b64encode(raw).decode()}",
            }
        if mime_type.startswith("video/"):
            return {
                "success": True,
                "file_type": "video",
                "file_content": f"data:{mime_type};base64,{base64.b64encode(raw).decode()}",
            }
        if mime_type.startswith("text/") or file_path.endswith((".txt", ".csv", ".log", ".py", ".md")):
            return {
                "success": True,
                "file_type": "text",
                "file_content": raw.decode("utf-8", errors="ignore")[:3000],
            }
        return {"success": False, "file_type": "unsupported", "file_content": ""}
    except Exception:
        return {"success": False, "file_type": "error", "file_content": ""}

# ==============================================================================
# 轻量 I/O 封装
# ==============================================================================

def save_uploaded_file(django_file, dest_dir: str) -> str:
    """
    将上传文件流式保存到 `dest_dir`（使用 Django storage 后端）。

    参数
    ----
    django_file : UploadedFile
        来自 `request.FILES` 的文件对象。
    dest_dir : str
        目标目录（若不存在会自动创建）。

    返回
    ----
    str
        新文件的绝对路径。

    注意
    ----
    - 通过 `chunks()` 迭代写入，避免一次性读入内存；
    - 若后端换成云存储，仅需改 storage 配置。
    """
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    save_path = str(Path(dest_dir) / django_file.name)
    with default_storage.open(save_path, "wb+") as dst:
        for chunk in django_file.chunks():
            dst.write(chunk)
    return save_path


def send_file_response(abs_path: str, download_name: str | None = None) -> HttpResponse:
    """
    以下载形式返回本地文件（设置合适的响应头）。

    参数
    ----
    abs_path : str
        待下载文件的绝对路径。
    download_name : str | None
        建议给浏览器使用的文件名（默认取 abs_path 的 basename）。

    返回
    ----
    HttpResponse
        二进制响应；若文件不存在则抛 404。

    安全
    ----
    - 需确保 abs_path 指向允许下载的目录，避免任意文件下载。
    """
    if not os.path.exists(abs_path):
        raise Http404("File not found")
    with open(abs_path, "rb") as fh:
        resp = HttpResponse(fh.read(), content_type="application/octet-stream")
    resp["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(download_name or abs_path)}\""
    return resp

# ==============================================================================
# 表单与便捷封装
# ==============================================================================

def make_encode_hidden_form(user_input: dict) -> EncodeHiddenForm:
    """
    用 `user_input` 预填充 EncodeHiddenForm，封装表单样板逻辑。

    参数
    ----
    user_input : dict
        前端提交的表单字段集合。

    返回
    ----
    EncodeHiddenForm
        已填充初始值的表单对象。
    """
    fields = (
        "hidden_method1","hidden_method2","hidden_mingc","hidden_maxgc",
        "hidden_sequence_length","info_density1","encode_time1","sequence_number1","index_length1",
        "info_density2","encode_time2","sequence_number2","index_length2",
    )
    init = {k: user_input.get(k) for k in fields}
    return EncodeHiddenForm(initial=init)

# ==============================================================================
# 视图（Views）
# ==============================================================================

def upload_for_preview(request):
    """
    上传并生成文件预览（图片/视频/文本），返回 JSON。

    流程
    ----
    1) 将上传文件保存到按 IP 隔离的 `media/` 目录；
    2) 将绝对路径写入 `session['filename']` 以便后续步骤复用；
    3) 探测类型并返回前端可直接渲染的预览载荷。

    请求
    ----
    - 仅支持 POST；字段名：`file_for_preview`。

    响应
    ----
    JsonResponse
    { success, file_name, file_type, file_content } 或错误信息。

    边界
    ----
    - 若 MIME 探测失败或读取异常，会返回 `success=False` 与错误码。
    """
    try:
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Invalid method."})
        uploaded = request.FILES.get("file_for_preview")
        if not uploaded:
            return JsonResponse({"success": False, "error": "No file was uploaded."})
        media_dir = get_media_path_from_request(request)
        save_path = save_uploaded_file(uploaded, media_dir)
        request.session["filename"] = save_path
        preview = get_preview_data(save_path)
        return JsonResponse({"success": True, "file_name": uploaded.name, **preview})
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Upload failed: {e}"})


def upload_file(request, name: str = "file") -> HttpResponse:
    """
    通用上传端点：将 FILES[name] 保存到全局 MEDIA 目录。

    参数
    ----
    request : HttpRequest（POST）
        包含 `name` 对应的上传文件。
    name : str
        上传字段名，默认 "file"。

    返回
    ----
    HttpResponse
        200：返回保存路径；400：请求非法或缺少文件。

    提示
    ----
    - 更推荐使用 `upload_for_preview`，其带有类型识别与预览能力。
    """
    if request.method == "POST" and name in request.FILES:
        uploaded = request.FILES[name]
        save_path = str(MEDIA_ROOT_DIR / uploaded.name)
        with default_storage.open(save_path, "wb+") as dst:
            for chunk in uploaded.chunks():
                dst.write(chunk)
        return HttpResponse(f"File uploaded successfully: {save_path}", status=200)
    return HttpResponse("Invalid request or no file uploaded", status=400)


def download_file(request, mode: str = "encode") -> HttpResponse:
    """
    根据 `mode` 从 session 取路径并触发下载。

    支持的 mode
    -----------
    - encode            -> `session['encode_outfile']`
    - simulate          -> `session['simulate_outfile']`
    - fordecode_outfile -> `session['cluster_or_rec_file']`
    - evaluate          -> `session['evaluate_filename']`
    - 其他              -> `session['decodefile']`

    返回
    ----
    HttpResponse
        成功时返回文件下载；缺失时抛 404。

    设计
    ----
    - 通过统一键映射，避免多处硬编码，便于扩展与维护。
    """
    default_path = os.path.join(settings.MEDIA_URL, "index_DNAFountain.fasta")
    key = {
        "encode": "encode_outfile",
        "simulate": "simulate_outfile",
        "fordecode_outfile": "cluster_or_rec_file",
        "evaluate": "evaluate_filename",
    }.get(mode, "decodefile")
    abs_path = request.session.get(key, default_path)
    return send_file_response(abs_path)


def dna_encoding(request):
    """
    *编码* 页面逻辑：触发编码流程并展示输入/输出预览与指标。

    流程概览
    --------
    - 解析用户工作区（基于 IP 路径）；
    - 从 session 或上传文件确定输入；
    - 按 `method` 分派到具体编码器（Fountain/YYC/Derrick/Polar/Hedges）；
    - 保存编码结果路径与统计信息到 session；
    - 渲染 `encode.html`，显示预览与元信息。

    请求
    ----
    - POST 且包含 `encodeBtn`：执行编码；
    - GET 带 `reset=1`：重置但保留评估等关键信息；
    - 其他 GET：载入默认示例并初始化页面。

    返回
    ----
    HttpResponse
        `encode.html` 渲染结果。

    关键思路
    --------
    - 以 session 作为跨页面数据总线（输入/输出/指标），避免表单反复传递；
    - 统一预览读取，通过 `read_file_head` 保持轻量与响应性；
    - 对异常进行捕获并打印堆栈，保障页面可回退到安全状态。
    """
    media_dir = get_media_path_from_request(request)
    files_dir = get_files_path_from_request(request)
    default_input = str(UPLOAD_FOLDER / "SZU_logo.jpg")

    if request.method == "POST" and "encodeBtn" in request.POST:
        user_input = request.POST
        filename = request.session.get("filename")
        if not filename:
            # 强制要求先上传
            if "file" not in request.FILES or not request.FILES["file"].name:
                return render(request, "encode.html", {"errors": "请先上传文件再进行编码。", "base": {**initial_params}})
            # 校验上传文件是否已存在于服务器路径
            uploaded = request.FILES["file"]
            server_path = os.path.join(media_dir, uploaded.name)
            if not os.path.exists(server_path):
                return render(request, "encode.html", {"errors": f"文件 '{uploaded.name}' 不存在，请重新上传。", "base": {**initial_params}})
            request.session["filename"] = server_path
            filename = server_path

        method = user_input.get("method", "fountain")
        try:
            if method == "fountain":
                info, output_file_path = getDnaFountainEncodeInfo(user_input, filename, files_dir)
            elif method == "YYC":
                info, output_file_path = getYYCEncodeInfo(user_input, filename, files_dir)
            elif method == "derrick":
                info, output_file_path = getDerrickEncodeInfo(user_input, filename, files_dir)
            elif method == "PolarCode":
                info, output_file_path = getPolarEncodeInfo(user_input, filename, files_dir)
                request.session["matrices"] = info
            else:
                info, output_file_path = getHedgesEncodeInfo(user_input, filename, files_dir)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("Encoding failed:\n" + "".join(traceback.format_exception(exc_type, exc_obj, exc_tb)))
            return render(request, "encode.html", {"base": initial_params})

        # 指标写入 session
        infos = {
            "method": method,
            "density": info.get("density"),
            "total_bit": info.get("total_bit"),
            "total_base": info.get("total_base"),
            "seq_num": info.get("seq_num"),
            "max_homopolymer": info.get("max_homopolymer"),
            "gc": info.get("gc"),
            "encode_time": info.get("encode_time"),
        }
        metrics = {
            "Costs": None,
            "Sequencing Depth Requirement": None,
            "Encoding Runtime": infos["encode_time"],
            "Decoding Runtime": None,
            "Physical Ratio": None,
            "Logical Density": infos["density"],
            "GC Contents": infos["gc"],
            "Maximum Homopolymers Length": infos["max_homopolymer"],
            "File Recovery": None,
        }
        request.session["metrics"] = metrics
        request.session["encode_input"] = dict(user_input)
        request.session["encode_outfile"] = str(Path(files_dir) / Path(output_file_path).name)
        request.session["encoded_data"] = info

        # 输出预览
        try:
            with open(output_file_path, "r", encoding="utf-8") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= MAX_PREVIEW_LINES:
                        break
                    lines.append(line)
            file_content = "".join(lines)
        except Exception as e:
            file_content = f"[ERROR] Failed to read encoded file: {e}"

        ctx = {
            "base": user_input,
            "encoded_data": info,
            "filename": os.path.basename(filename),
            "encoded_file_content": file_content,
            "disable": True,
        }
        file_path = request.session.get("filename", "")
        ctx["preview_data"] = get_preview_data(file_path)
        ctx["input_file_front"] = os.path.basename(file_path)
        return render(request, "encode.html", ctx)

    # GET + reset 处理
    if request.GET.get("reset") == "1":
        backup_evaluate = dict(request.session.get("evaluate", {}))
        request.session.flush()
        request.session["evaluate"] = backup_evaluate
        request.session["filename"] = default_input
        ctx = {"base": {**initial_params}, "filename": os.path.basename(default_input)}
        file_path = request.session.get("filename", "")
        ctx["preview_data"] = get_preview_data(file_path)
        ctx["input_file_front"] = os.path.basename(file_path)
        return render(request, "encode.html", ctx)

    # 初次 GET
    request.session.flush()
    request.session["filename"] = default_input
    ctx = {"base": {**initial_params}, "filename": os.path.basename(default_input)}
    file_path = request.session.get("filename", "")
    ctx["preview_data"] = get_preview_data(file_path)
    ctx["input_file_front"] = os.path.basename(file_path)
    return render(request, "encode.html", ctx)


def simulate_view(request):
    """
    *模拟* 页面逻辑（合成+测序等通道）。

    流程
    ----
    - POST `stepsok`：记录选中的通道并展示编码输出预览；
    - POST `synseqBtn`：根据表单构造 `SimuInfo`，调用 `adddt4simu_advanced` 运行模拟，
      将输出路径和用时写入 session；
    - GET `reset=1`：保留 matrices/metrics，重置页面。

    返回
    ----
    HttpResponse
        `simulate.html` 渲染结果。

    思路
    ----
    - 输入/输出目录均挂到 `files/<ip>/simu/` 之下，便于定位与清理；
    - 仅在成功后写入 session，失败时给出提示并保留用户输入。
    """
    files_dir = get_files_path_from_request(request)
    simu_dir = Path(files_dir) / "simu"

    if request.method == "POST" and "stepsok" in request.POST:
        user_input = request.POST
        request.session["channel"] = user_input.getlist("channel", ["synthesis"])  # 选择阶段
        encode_front = os.path.basename(request.session.get("encode_outfile", ""))
        preview_content = read_file_head(request.session.get("encode_outfile", ""), MAX_PREVIEW_LINES)
        ctx = {"simulate": True, "base": {**initial_params, **request.session}}
        ctx["base"]["filename"] = encode_front
        ctx["preview_content"] = preview_content
        encode_out = request.session.get("encode_outfile")
        size_kb = round((os.path.getsize(encode_out) if encode_out and os.path.exists(encode_out) else 0) / 1024, 2)
        ctx["encode_outfile_size_kb"] = size_kb
        return render(request, "simulate.html", ctx)

    if request.method == "POST" and "synseqBtn" in request.POST:
        user_input = request.POST
        encode_outfile = request.session.get("encode_outfile", "")
        if not encode_outfile:
            return render(request, "simulate.html", {"errors": "请先完成编码，或上传有效文件。", "base": {**initial_params}})

        encode_front = os.path.basename(encode_outfile)
        simu_dir.mkdir(parents=True, exist_ok=True)
        if user_input.get("sequencing_method", "paired-end") in ("Nanopone", "Pacbio"):
            out_path = str(simu_dir / f"{encode_front}_simulated_seqsr1r2.fastq")
        else:
            out_path = str(simu_dir / f"{encode_front}_simulated_seqsr1r2.fasta")

        info = SimuInfo(
            inputfile_path=encode_outfile,
            synthesis_method=user_input.get("synthesis_method", "electrochemical"),
            channel=request.session.get("channel", []),
            oligo_scale=user_input.get("oligo_scale", 1),
            sample_multiple=user_input.get("sample_multiple", 100),
            pcrcycle=user_input.get("pcrcycle", 2),
            pcrpro=user_input.get("pcrpro", 0.8),
            decay_year=user_input.get("decay_year", 2),
            decaylossrate=user_input.get("decaylossrate", 0.3),
            sample_ratio=user_input.get("sample_ratio", 0.005),
            sequencing_method=user_input.get("sequencing_method", "paired-end"),
            depth=user_input.get("depth", 10),
            badparams=user_input.get("badparams", ""),
            thread=initial_params.get("thread_num"),
        )

        try:
            infos = adddt4simu_advanced(info, out_path, str(simu_dir), encode_front)
        except Exception:
            print("Simulation failed:\n" + traceback.format_exc())
            return render(request, "simulate.html", {"errors": "please upload a valid file", "base": {**initial_params}})

        request.session["simulate_outfile"] = infos.get("path")
        write_dict_to_csv({"simulate_time": infos.get("time", "")}, str(WRITE_FILEPATH))

        ctx = {"base": {**initial_params, **request.session}, "disable": True}
        ctx["base"]["filename"] = os.path.basename(request.session.get("encode_outfile", ""))
        ctx["preview_content"] = read_file_head(request.session.get("encode_outfile", ""), MAX_PREVIEW_LINES)
        ctx["sequencing_data"] = {"time": infos.get("time")}
        return render(request, "simulate.html", ctx)

    if request.GET.get("reset") == "1":
        matrices = request.session.get("matrices", {})
        encode_outfile = request.session.get("encode_outfile", "")
        metrics = request.session.get("metrics", {})
        filename = request.session.get("filename", "")
        request.session.flush()
        request.session.update({"metrics": metrics, "encode_outfile": encode_outfile, "filename": filename, "matrices": matrices})
        return render(request, "simulate.html", {"base": {**initial_params}})

    # 初次 GET 模拟页
    matrices = request.session.get("matrices", {})
    encode_outfile = request.session.get("encode_outfile", "")
    filename = request.session.get("filename", "")
    metrics = request.session.get("metrics", {})
    request.session.flush()
    request.session.update({"metrics": metrics, "encode_outfile": encode_outfile, "filename": filename, "matrices": matrices})
    return render(request, "simulate.html", {"base": {**initial_params}})


def _build_decode_page_context(initial_params: dict, request, forclusterfile: str, encode_outfile: str, error_msg: str | None = None) -> dict:
    """
    组装 `decode.html` 的上下文：统一填充多处预览与文件名。

    参数
    ----
    initial_params : dict
        基础参数（在多页面共享）。
    request : HttpRequest
        用于读取 session（聚类/重建/原始文件等路径）。
    forclusterfile : str
        用于聚类/重建的模拟数据路径（若为空则回退到编码输出）。
    encode_outfile : str
        编码产物（参考）文件路径。
    error_msg : str | None
        可选的错误消息，供页面顶部提示。

    返回
    ----
    dict
        可直接用于 `render(request, 'decode.html', ctx)` 的上下文字典。

    设计
    ----
    - 将多处 `read_file_head`/`get_preview_data` 的调用集中，减少模板变量散落；
    - 当 `cluster_or_rec_file` 缺失时，自动回退，保障页面可渲染。
    """
    ctx = {"base": {**initial_params, **request.session}}
    cluster_or_rec = request.session.get("cluster_or_rec_file", "") or forclusterfile
    origin_file = request.session.get("filename", "")

    # 预览内容
    ctx["preview_simulate"] = read_file_head(forclusterfile) if forclusterfile else ""
    ctx["preview_ref"] = read_file_head(encode_outfile) if encode_outfile else ""
    ctx["preview_decode"] = read_file_head(cluster_or_rec) if cluster_or_rec and os.path.exists(cluster_or_rec) else ""
    ctx["preview_origin"] = get_preview_data(origin_file) if origin_file else ""

    # 展示名称
    ctx["forclusterfile_filename"] = os.path.basename(forclusterfile) if forclusterfile else ""
    ctx["encode_outfile_filename"] = os.path.basename(encode_outfile) if encode_outfile else ""
    ctx["cluster_or_rec_filename"] = os.path.basename(cluster_or_rec) if cluster_or_rec else ""
    ctx["origin_filename"] = os.path.basename(origin_file) if origin_file else ""

    if error_msg:
        ctx["error_msg"] = error_msg
    return ctx
