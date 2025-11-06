"""
olmOCR Web 服务 - 部署在 Render
使用外部 API 进行模型推理
"""

import os
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import subprocess
import uuid
import json
import logging
from datetime import datetime

# 配置日志
log_handlers = [logging.StreamHandler()]

# 尝试在临时目录创建日志文件（适配 Render 等云平台）
try:
    log_file = os.path.join(tempfile.gettempdir(), 'olmocr_app.log')
    log_handlers.append(logging.FileHandler(log_file))
except (PermissionError, OSError):
    # 如果无法创建日志文件，只输出到控制台
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 最大文件大小
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# 从环境变量获取配置
PROVIDER = os.environ.get('OLMOCR_PROVIDER', 'deepinfra')
API_KEY = os.environ.get('OLMOCR_API_KEY', '')

# 支持自定义 API URL 和模型
CUSTOM_API_URL = os.environ.get('OLMOCR_CUSTOM_API_URL', '')
CUSTOM_MODEL = os.environ.get('OLMOCR_CUSTOM_MODEL', '')

# 提供商配置
PROVIDERS = {
    'deepinfra': {
        'server': 'https://api.deepinfra.com/v1/openai',
        'model': 'allenai/olmOCR-2-7B-1025',
    },
    'cirrascale': {
        'server': 'https://ai2endpoints.cirrascale.ai/api',
        'model': 'olmOCR-2-7B-1025',
    },
    'parasail': {
        'server': 'https://api.parasail.io/v1',
        'model': 'allenai/olmOCR-2-7B-1025',
    },
    'custom': {
        'server': CUSTOM_API_URL or 'http://localhost:8000/v1',
        'model': CUSTOM_MODEL or 'olmocr',
    },
}

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_pdf_with_olmocr(pdf_path, output_dir):
    """使用 olmOCR 处理 PDF"""
    logger.info(f"开始处理 PDF: {pdf_path}")
    logger.info(f"输出目录: {output_dir}")

    if not API_KEY:
        logger.error("未设置 OLMOCR_API_KEY 环境变量")
        raise ValueError("未设置 OLMOCR_API_KEY 环境变量")

    provider_config = PROVIDERS.get(PROVIDER)
    if not provider_config:
        logger.error(f"未知的提供商: {PROVIDER}")
        raise ValueError(f"未知的提供商: {PROVIDER}")

    logger.info(f"使用提供商: {PROVIDER}")
    logger.info(f"API 服务器: {provider_config['server']}")
    logger.info(f"模型: {provider_config['model']}")

    # 构建 olmocr 命令
    cmd = [
        'python', '-m', 'olmocr.pipeline',
        output_dir,
        '--server', provider_config['server'],
        '--api_key', API_KEY,
        '--model', provider_config['model'],
        '--markdown',
        '--pdfs', pdf_path
    ]

    logger.info(f"执行命令: {' '.join([c if c != API_KEY else '***' for c in cmd])}")

    # 执行命令
    start_time = datetime.now()
    logger.info("开始执行 olmOCR 处理...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5分钟超时
    )

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"olmOCR 处理完成,耗时: {duration:.2f}秒")

    if result.returncode != 0:
        logger.error(f"olmOCR 处理失败,返回码: {result.returncode}")
        logger.error(f"错误输出: {result.stderr}")
        raise Exception(f"olmOCR 处理失败: {result.stderr}")

    logger.info("olmOCR 处理成功")
    if result.stdout:
        logger.debug(f"标准输出: {result.stdout[:200]}...")

    return result.stdout


@app.route('/')
def index():
    """主页"""
    logger.info(f"访问主页,来自 IP: {request.remote_addr}")
    provider_config = PROVIDERS.get(PROVIDER, {})
    return render_template(
        'index.html',
        provider=PROVIDER,
        api_url=provider_config.get('server', ''),
        model=provider_config.get('model', '')
    )


@app.route('/health')
def health():
    """健康检查"""
    logger.debug(f"健康检查请求,来自 IP: {request.remote_addr}")
    provider_config = PROVIDERS.get(PROVIDER, {})
    health_status = {
        'status': 'ok',
        'provider': PROVIDER,
        'api_url': provider_config.get('server', ''),
        'model': provider_config.get('model', ''),
        'api_key_configured': bool(API_KEY)
    }
    logger.debug(f"健康检查结果: {health_status}")
    return jsonify(health_status)


@app.route('/api/convert', methods=['POST'])
def convert():
    """PDF 转换 API"""
    logger.info(f"收到转换请求,来自 IP: {request.remote_addr}")

    # 检查文件
    if 'file' not in request.files:
        logger.warning("请求中未包含文件")
        return jsonify({'error': '未上传文件'}), 400

    file = request.files['file']

    if file.filename == '':
        logger.warning("文件名为空")
        return jsonify({'error': '文件名为空'}), 400

    logger.info(f"上传文件: {file.filename}")

    if not allowed_file(file.filename):
        logger.warning(f"不支持的文件格式: {file.filename}")
        return jsonify({'error': f'不支持的文件格式，支持: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    job_id = None
    work_dir = None

    try:
        # 创建唯一的工作目录
        job_id = str(uuid.uuid4())
        work_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'olmocr_{job_id}')
        os.makedirs(work_dir, exist_ok=True)
        logger.info(f"创建任务 {job_id},工作目录: {work_dir}")

        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(work_dir, filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        logger.info(f"文件保存成功: {file_path} (大小: {file_size} 字节)")

        # 创建输出目录
        output_dir = os.path.join(work_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"创建输出目录: {output_dir}")

        # 处理 PDF
        logger.info(f"开始处理任务 {job_id}")
        process_pdf_with_olmocr(file_path, output_dir)

        # 读取生成的 Markdown 文件
        markdown_dir = os.path.join(output_dir, 'markdown')
        logger.info(f"查找 Markdown 文件: {markdown_dir}")
        markdown_files = list(Path(markdown_dir).glob('*.md'))
        logger.info(f"找到 {len(markdown_files)} 个 Markdown 文件")

        if not markdown_files:
            logger.error("未生成 Markdown 文件")
            return jsonify({'error': '未生成 Markdown 文件'}), 500

        # 读取第一个 Markdown 文件
        markdown_file = markdown_files[0]
        logger.info(f"读取 Markdown 文件: {markdown_file}")
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        markdown_size = len(markdown_content)
        logger.info(f"Markdown 内容大小: {markdown_size} 字符")

        # 清理工作目录
        logger.info(f"清理工作目录: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)

        logger.info(f"任务 {job_id} 处理成功")
        return jsonify({
            'success': True,
            'filename': filename,
            'markdown': markdown_content,
            'job_id': job_id
        })

    except subprocess.TimeoutExpired:
        logger.error(f"任务 {job_id} 处理超时")
        if work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
        return jsonify({'error': '处理超时，请稍后重试'}), 504

    except Exception as e:
        logger.error(f"任务 {job_id} 处理错误: {str(e)}", exc_info=True)
        # 清理工作目录
        if work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

        return jsonify({'error': f'处理失败: {str(e)}'}), 500


@app.route('/api/providers')
def list_providers():
    """列出可用的提供商"""
    logger.info(f"列出提供商列表,来自 IP: {request.remote_addr}")
    providers_info = {
        'providers': list(PROVIDERS.keys()),
        'current': PROVIDER
    }
    logger.debug(f"提供商列表: {providers_info}")
    return jsonify(providers_info)


if __name__ == '__main__':
    # 检查配置
    logger.info("=" * 60)
    logger.info("启动 olmOCR Web 服务")
    logger.info("=" * 60)
    logger.info(f"当前提供商: {PROVIDER}")
    logger.info(f"API 密钥已配置: {bool(API_KEY)}")
    logger.info(f"上传文件夹: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"最大文件大小: {app.config['MAX_CONTENT_LENGTH'] / (1024*1024):.0f}MB")

    # 日志文件位置
    if len(log_handlers) > 1:
        logger.info(f"日志文件: {log_file}")
    else:
        logger.info("日志输出: 仅控制台 (无文件)")

    if not API_KEY:
        logger.warning("⚠️  警告: 未设置 OLMOCR_API_KEY 环境变量")
        print("⚠️  警告: 未设置 OLMOCR_API_KEY 环境变量")
        print("请设置环境变量: export OLMOCR_API_KEY=your_api_key")

    # 开发模式
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False') == 'True'
    logger.info(f"服务器端口: {port}")
    logger.info(f"调试模式: {debug_mode}")
    logger.info("=" * 60)

    try:
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
        raise
