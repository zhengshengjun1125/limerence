# AI 视频检测器

使用 **EfficientNet-B4** 检测上传视频是否由 AI 生成（Deepfake）。

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开浏览器访问：http://localhost:8000

---

## 使用真实模型权重（可选）

默认以 **演示模式** 运行（ImageNet 预训练骨干网络 + 随机分类头），结果没有实际意义，仅用于测试流程。

要使用真实 Deepfake 检测权重：

1. 从以下来源下载 `.pth` 文件：
   - [FaceForensics++](https://github.com/ondyari/FaceForensics)
   - [Kaggle Deepfake Detection Challenge](https://www.kaggle.com/c/deepfake-detection-challenge)
   - [DFDC](https://ai.facebook.com/datasets/dfdc/)

2. 将权重文件放到 `app/models/weights/detector.pth`

3. 重启服务，系统会自动加载权重（`DEMO_MODE` 变为 `False`）

---

## API

### `POST /api/detect`

上传视频文件，返回检测结果。

**请求**：`multipart/form-data`，字段名 `file`

**响应示例**：
```json
{
  "label": "AI Generated",
  "confidence": 0.8712,
  "frame_scores": [0.91, 0.85, 0.88, 0.72, 0.93, 0.89, 0.81, 0.76, 0.94, 0.87],
  "demo_mode": false,
  "filename": "test.mp4"
}
```

### `GET /api/health`

服务健康检查。

---

## Docker 部署

```bash
# 构建镜像
docker build -t ai-video-detector .

# 运行容器
docker run -p 8000:8000 ai-video-detector

# 挂载自定义权重
docker run -p 8000:8000 \
  -v /path/to/detector.pth:/app/app/models/weights/detector.pth \
  ai-video-detector
```

---

## 项目结构

```
limerence/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── models/
│   │   ├── detector.py          # 模型加载与推理
│   │   └── weights/             # 放置 .pth 权重文件
│   ├── utils/
│   │   └── video_processor.py   # OpenCV 帧提取
│   └── routes/
│       └── api.py               # /detect 端点
├── static/
│   ├── css/style.css
│   ├── js/upload.js
│   └── uploads/                 # 临时文件（自动清理）
├── templates/
│   └── index.html
├── requirements.txt
├── Dockerfile
└── README.md
```

## 技术栈

| 组件 | 版本 |
|------|------|
| Python | 3.10+ |
| FastAPI | 0.111 |
| PyTorch | 2.3 |
| OpenCV | 4.9 |
| EfficientNet-B4 | torchvision 内置 |
