你是一个专业的Python开发者，擅长使用FastAPI、PyTorch和OpenCV构建Web应用。现在，我需要你帮助开发一个AI视频识别网站，用于检测上传的视频是否由AI生成（例如Deepfake视频）。项目要求如下：

- **项目概述**：Web应用支持用户上传视频（MP4等格式），使用预训练的Deepfake检测模型分析视频帧，输出是否AI生成及置信度。准确率目标>80%，处理时间<1分钟。无用户认证，简单MVP版本。
- **技术栈**：
  - 后端：Python 3.10+，FastAPI（异步API）。
  - AI模型：PyTorch-based Deepfake检测模型（如基于ResNet或Xception的预训练模型，从GitHub下载权重）。
  - 视频处理：OpenCV（帧提取），FFmpeg可选。
  - 前端：简单HTML + JavaScript（使用JinJa2模板）。
  - 部署：本地运行，支持Docker。
- **项目结构**：
  limerence/
  ├── app/                  # 后端
  │   ├── __init__.py
  │   ├── main.py           # FastAPI入口
  │   ├── models/           # AI模型
  │   │   ├── detector.py
  │   │   └── weights/      # 模型权重
  │   ├── utils/            # 工具
  │   │   └── video_processor.py
  │   └── routes/           # API
  │       └── api.py
  ├── static/               # 前端静态
  │   ├── css/style.css
  │   ├── js/upload.js
  │   └── uploads/          # 临时存储
  ├── templates/            # HTML
  │   └── index.html
  ├── requirements.txt
  ├── README.md
  └── Dockerfile            # 可选

- **初始化与环境设置要求**（必须从这里开始，确保项目能从零运行）：
  1. 解释如何创建项目文件夹和虚拟环境：如使用`mkdir ai_video_detector`、`python -m venv venv`、`source venv/bin/activate`（包括Windows版本）。
  2. 生成requirements.txt，并提供安装命令`pip install -r requirements.txt`。依赖包括：fastapi, uvicorn, opencv-python, torch, torchvision, pillow, jinja2, python-multipart。
  3. 解释如何获取和放置模型权重：提供GitHub链接示例（如https://github.com/ondyari/FaceForensics 或其他Deepfake模型仓库），下载.pth文件到app/models/weights/，并处理CPU/GPU兼容（map_location='cpu'）。
  4. 添加.gitignore文件内容，忽略venv、uploads等。
  5. 提供启动脚本或命令，如`uvicorn app.main:app --reload`。

- **开发步骤要求**：
  1. 生成requirements.txt并解释安装。
  2. 提供模型detector.py：加载预训练权重，二分类预测（真实/AI生成），输入视频帧列表，输出概率。
  3. 提供video_processor.py：从视频提取10帧。
  4. 提供main.py和api.py：API端点/detect处理上传，调用模型，返回JSON。
  5. 提供前端index.html、upload.js和style.css：支持文件上传和结果显示。
  6. 包括测试代码和启动命令（uvicorn）。
  7. 添加异常处理、安全措施（如删除临时文件、文件类型检查、视频大小限制<100MB）。
  8. 解释如何获取模型权重（e.g., 从GitHub下载）。
  9. 提供Dockerfile和部署指南（Heroku/AWS），包括生产启动如Gunicorn。

输出格式：先概述项目和初始化步骤（包括命令），然后按文件逐一提供完整代码（用代码块），最后给出测试/部署步骤。确保代码可运行，如果需要假设模型权重路径。不要遗漏任何部分，包括环境初始化。