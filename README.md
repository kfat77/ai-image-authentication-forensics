# AI Photo Reconstructor

一个用于**反向拆解 AI 图片**的开源服务：上传一张图片，获得可编辑的视觉描述、候选生图模型配置，以及可用于重新生成相似画面的提示词。

> 本项目不声称能确定一张图片的原始模型或恢复专有模型的内部权重。输出是基于画面特征的**概率化重建建议**。

## MVP 能力

- 读取图片尺寸、纵横比、主色调与亮度。
- 以视觉启发式推断摄影/插画风格、镜头感、光线、构图。
- 为 SDXL、FLUX、Midjourney 与 DALL·E 生成各自格式的提示词和参数建议。
- 提供轻量 Web 界面与 JSON API。
- 生产环境 API 密钥与角色、无持久化图片处理、最小化审计事件、上传限制和安全响应头。

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

## 机构部署基线

生产环境必须设置 `APP_ENV=production`，并配置 API 密钥或 OIDC（两者可并存）。每项密钥格式是 `client_id:secret:role`，角色可为 `analyst` 或 `operator`；OIDC 则需要 issuer、audience、JWKS URL 与角色声明映射。复制 `.env.example` 作为配置参考，绝不可提交真实密钥。

完整的已实现控制、部署前必需控制和数据流边界见 [安全基线](docs/security-baseline.md)、[运行手册](docs/operations.md)、[模型治理](docs/model-governance.md) 与 [机构保障路线图](docs/assurance-roadmap.md)。这些文档不构成任何政府认证或合规承诺。

每次推送和 Pull Request 都会运行 Python 3.11/3.12 的测试、依赖一致性检查、编译检查与 Docker 镜像构建；Dependabot 每周检查依赖更新。

面向机构集群的 Kubernetes 基线在 [k8s/README.md](k8s/README.md)，含受限运行时、HPA、PDB、资源边界和入口/出口网络策略。部署机构仍须替换镜像、接入 Secret 管理、调整网关标签并在目标环境演练。

## 后续演进

- 接入 BLIP / LLaVA 等视觉语言模型，替代 MVP 启发式描述。
- 用带来源标签的数据集训练模型来源分类器，并报告置信区间与数据集边界。
- 增加 ComfyUI / Automatic1111 工作流导出和 A/B 再生成评估。
