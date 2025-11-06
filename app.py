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
    if not API_KEY:
        raise ValueError("未设置 OLMOCR_API_KEY 环境变量")

    provider_config = PROVIDERS.get(PROVIDER)
    if not provider_config:
        raise ValueError(f"未知的提供商: {PROVIDER}")

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

    # 执行命令
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5分钟超时
    )

    if result.returncode != 0:
        raise Exception(f"olmOCR 处理失败: {result.stderr}")

    return result.stdout


@app.route('/')
def index():
    """主页"""
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
    provider_config = PROVIDERS.get(PROVIDER, {})
    return jsonify({
        'status': 'ok',
        'provider': PROVIDER,
        'api_url': provider_config.get('server', ''),
        'model': provider_config.get('model', ''),
        'api_key_configured': bool(API_KEY)
    })


@app.route('/api/convert', methods=['POST'])
def convert():
    """PDF 转换 API"""
    # 检查文件
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'不支持的文件格式，支持: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # 创建唯一的工作目录
        job_id = str(uuid.uuid4())
        work_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'olmocr_{job_id}')
        os.makedirs(work_dir, exist_ok=True)

        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(work_dir, filename)
        file.save(file_path)

        # 创建输出目录
        output_dir = os.path.join(work_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)

        # 处理 PDF
        process_pdf_with_olmocr(file_path, output_dir)

        # 读取生成的 Markdown 文件
        markdown_dir = os.path.join(output_dir, 'markdown')
        markdown_files = list(Path(markdown_dir).glob('*.md'))

        if not markdown_files:
            return jsonify({'error': '未生成 Markdown 文件'}), 500

        # 读取第一个 Markdown 文件
        with open(markdown_files[0], 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 清理工作目录
        shutil.rmtree(work_dir, ignore_errors=True)

        return jsonify({
            'success': True,
            'filename': filename,
            'markdown': markdown_content,
            'job_id': job_id
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': '处理超时，请稍后重试'}), 504
    except Exception as e:
        # 清理工作目录
        if 'work_dir' in locals():
            shutil.rmtree(work_dir, ignore_errors=True)

        app.logger.error(f"处理错误: {str(e)}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


@app.route('/api/providers')
def list_providers():
    """列出可用的提供商"""
    return jsonify({
        'providers': list(PROVIDERS.keys()),
        'current': PROVIDER
    })


if __name__ == '__main__':
    # 检查配置
    if not API_KEY:
        print("⚠️  警告: 未设置 OLMOCR_API_KEY 环境变量")
        print("请设置环境变量: export OLMOCR_API_KEY=your_api_key")

    # 开发模式
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False') == 'True')
