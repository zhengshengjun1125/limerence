/**
 * upload.js – handles drag-and-drop, file selection, upload progress,
 * result rendering and gauge animation for the AI Video Detector UI.
 */

(() => {
  'use strict';

  // ---------------------------------------------------------------------------
  // DOM refs
  // ---------------------------------------------------------------------------
  const dropZone       = document.getElementById('dropZone');
  const fileInput      = document.getElementById('fileInput');
  const filePreview    = document.getElementById('filePreview');
  const fileName       = document.getElementById('fileName');
  const fileSize       = document.getElementById('fileSize');
  const clearBtn       = document.getElementById('clearBtn');
  const progressWrap   = document.getElementById('progressWrap');
  const progressFill   = document.getElementById('progressFill');
  const progressLabel  = document.getElementById('progressLabel');
  const submitBtn      = document.getElementById('submitBtn');
  const uploadCard     = document.getElementById('uploadCard');
  const resultCard     = document.getElementById('resultCard');
  const resetBtn       = document.getElementById('resetBtn');
  const errorToast     = document.getElementById('errorToast');
  const errorMsg       = document.getElementById('errorMsg');
  const toastClose     = document.getElementById('toastClose');

  // Result elements
  const gaugeArc        = document.getElementById('gaugeArc');
  const gaugePercent    = document.getElementById('gaugePercent');
  const verdictBadge    = document.getElementById('verdictBadge');
  const detailFilename  = document.getElementById('detailFilename');
  const detailConfidence= document.getElementById('detailConfidence');
  const detailFrames    = document.getElementById('detailFrames');
  const detailMode      = document.getElementById('detailMode');
  const frameScoresBars = document.getElementById('frameScoresBars');

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  let selectedFile = null;
  const MAX_SIZE_BYTES = 100 * 1024 * 1024; // 100 MB
  const ALLOWED_EXTS = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
  // Gauge arc total length (semi-circle of r=90, πr ≈ 283)
  const ARC_LEN = 283;

  // ---------------------------------------------------------------------------
  // Utilities
  // ---------------------------------------------------------------------------
  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function getExtension(name) {
    const idx = name.lastIndexOf('.');
    return idx >= 0 ? name.slice(idx).toLowerCase() : '';
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    errorToast.hidden = false;
  }

  function hideError() {
    errorToast.hidden = true;
  }

  // ---------------------------------------------------------------------------
  // File handling
  // ---------------------------------------------------------------------------
  function setFile(file) {
    if (!file) return;

    const ext = getExtension(file.name);
    if (!ALLOWED_EXTS.includes(ext)) {
      showError(`不支持的文件类型 "${ext}"，请上传 MP4 / AVI / MOV / MKV / WebM。`);
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      showError(`文件过大（${formatBytes(file.size)}），最大允许 100 MB。`);
      return;
    }

    hideError();
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    filePreview.hidden = false;
    submitBtn.disabled = false;
    dropZone.classList.add('drop-zone--has-file');
  }

  function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    filePreview.hidden = true;
    submitBtn.disabled = true;
    dropZone.classList.remove('drop-zone--has-file');
    progressWrap.hidden = true;
    progressFill.style.width = '0%';
  }

  // ---------------------------------------------------------------------------
  // Drag & drop
  // ---------------------------------------------------------------------------
  ['dragenter', 'dragover'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
      e.preventDefault();
      dropZone.classList.add('drop-zone--active');
    })
  );

  ['dragleave', 'drop'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
      e.preventDefault();
      dropZone.classList.remove('drop-zone--active');
    })
  );

  dropZone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length) setFile(files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) setFile(fileInput.files[0]);
  });

  clearBtn.addEventListener('click', clearFile);

  // ---------------------------------------------------------------------------
  // Upload & detection
  // ---------------------------------------------------------------------------
  submitBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    hideError();
    submitBtn.disabled = true;
    progressWrap.hidden = false;
    progressLabel.textContent = '上传中…';
    progressFill.style.width = '0%';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Use XMLHttpRequest for upload progress events
      const result = await uploadWithProgress(formData);
      renderResult(result);
    } catch (err) {
      showError(err.message || '上传失败，请重试。');
      submitBtn.disabled = false;
      progressWrap.hidden = true;
    }
  });

  function uploadWithProgress(formData) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', e => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          progressFill.style.width = pct + '%';
          progressLabel.textContent = pct < 100 ? `上传中… ${pct}%` : '分析中，请稍候…';
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error('服务器返回了无效的数据。'));
          }
        } else {
          let detail = `请求失败（HTTP ${xhr.status}）`;
          try {
            const body = JSON.parse(xhr.responseText);
            if (body.detail) detail = body.detail;
          } catch { /* ignore */ }
          reject(new Error(detail));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('网络错误，请检查连接。')));
      xhr.addEventListener('abort', () => reject(new Error('上传已取消。')));

      xhr.open('POST', '/api/detect');
      xhr.send(formData);
    });
  }

  // ---------------------------------------------------------------------------
  // Result rendering
  // ---------------------------------------------------------------------------
  function renderResult(data) {
    // Transition cards
    uploadCard.hidden = true;
    resultCard.hidden = false;

    const pct = Math.round(data.confidence * 100);
    const isAI = data.label === 'AI Generated';

    // Gauge animation
    animateGauge(pct, isAI);

    // Verdict badge
    verdictBadge.textContent = isAI ? '⚠ AI 生成' : '✓ 真实视频';
    verdictBadge.className = 'verdict ' + (isAI ? 'verdict--fake' : 'verdict--real');

    // Details table
    detailFilename.textContent   = data.filename || '—';
    detailConfidence.textContent = (data.confidence * 100).toFixed(2) + '%';
    detailFrames.textContent     = data.frame_scores ? data.frame_scores.length + ' 帧' : '—';
    detailMode.textContent       = data.demo_mode ? '演示模式（随机权重）' : '正式模型';

    // Frame score bars
    renderFrameBars(data.frame_scores || []);
  }

  function animateGauge(targetPct, isAI) {
    gaugeArc.style.stroke = isAI ? '#ef4444' : '#22c55e';
    gaugePercent.style.color = isAI ? '#ef4444' : '#22c55e';

    const targetOffset = ARC_LEN - (targetPct / 100) * ARC_LEN;
    let current = ARC_LEN;
    const step = (ARC_LEN - targetOffset) / 40;

    const timer = setInterval(() => {
      current -= step;
      if (current <= targetOffset) {
        current = targetOffset;
        clearInterval(timer);
      }
      gaugeArc.setAttribute('stroke-dashoffset', current.toFixed(2));
      const shown = Math.round(((ARC_LEN - current) / ARC_LEN) * 100);
      gaugePercent.textContent = shown + '%';
    }, 16);
  }

  function renderFrameBars(scores) {
    frameScoresBars.innerHTML = '';
    scores.forEach((score, i) => {
      const pct = Math.round(score * 100);
      const bar = document.createElement('div');
      bar.className = 'frame-bar';
      bar.innerHTML = `
        <span class="frame-bar__label">帧 ${i + 1}</span>
        <div class="frame-bar__track">
          <div class="frame-bar__fill ${pct >= 50 ? 'frame-bar__fill--fake' : 'frame-bar__fill--real'}"
               style="width: ${pct}%"></div>
        </div>
        <span class="frame-bar__val">${pct}%</span>
      `;
      frameScoresBars.appendChild(bar);
    });
  }

  // ---------------------------------------------------------------------------
  // Reset
  // ---------------------------------------------------------------------------
  resetBtn.addEventListener('click', () => {
    clearFile();
    resultCard.hidden = true;
    uploadCard.hidden = false;
  });

  toastClose.addEventListener('click', hideError);

})();
