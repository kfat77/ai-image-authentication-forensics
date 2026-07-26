# AI Photo Reconstructor

一个用于**反向拆解 AI 图片**的开源 MVP：上传一张图片，获得可编辑的视觉描述、候选生图模型配置，以及可用于重新生成相似画面的提示词。

> 本项目不声称能确定一张图片的原始模型或恢复专有模型的内部权重。输出是基于画面特征的**概率化重建建议**。

## MVP 能力

- 读取图片尺寸、纵横比、主色调与亮度。
- 以视觉启发式推断摄影/插画风格、镜头感、光线、构图。
- 为 SDXL、FLUX、Midjourney 与 DALL·E 生成各自格式的提示词和参数建议。
- 提供轻量 Web 界面与 JSON API。

## 运行

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

另开一个终端：

```bash
cd frontend
python -m http.server 5173
```

打开 `http://localhost:5173`，上传图片后即可查看建议。API 文档位于 `http://localhost:8000/docs`。

## API

`POST /analyze`，表单字段为 `image`。响应包含 `analysis`、`candidates` 与 `disclaimer`。

## 后续演进

- 接入 BLIP / LLaVA 等视觉语言模型，替代 MVP 启发式描述。
- 用带来源标签的数据集训练模型来源分类器，并报告置信区间与数据集边界。
- 增加 ComfyUI / Automatic1111 工作流导出和 A/B 再生成评估。

