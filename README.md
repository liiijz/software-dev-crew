# 软件开发团队 CrewAI A2A 模板

中文版 | [English](./README.en.md)

## 简介
本项目使用 CrewAI 框架自动化软件开发任务。CrewAI 协调自主 AI 代理协作构建各类软件项目，支持多种编程语言（Python、JavaScript/TypeScript、Go、Rust、Java 等），包括 CLI 工具、Web 应用、桌面应用、移动应用等。

## 演示

![软件开发团队实时流式输出演示](https://github.com/user-attachments/assets/606474a6-7fc4-4369-a5b0-7504dd01f8a9)

*实时流式输出展示 AI 代理的思考和工作过程*

## 功能特性
- **多语言支持**：支持 Python、JavaScript/TypeScript、Go、Rust、Java 等多种编程语言
- **全栈开发能力**：前端框架（React、Vue、Svelte）、后端框架（FastAPI、Express、Django）
- **自动化代码审查**：多阶段质量保证流程
- **实时流式输出**：实时显示 AI 代理的思考和工作过程，提供更好的用户体验
- **交互式和命令行模式**：支持交互式使用或通过命令行参数
- **生产就绪代码**：生成完整、有文档且经过测试的代码

## 支持的项目类型
- CLI 工具（多语言）
- 各类编程语言库（Python、JavaScript、Go 等）
- 实用程序和脚本
- Web 应用（前端 + 后端）
- 桌面应用
- 移动应用
- 数据处理工具

## CrewAI 框架
CrewAI 促进角色扮演 AI 代理之间的协作。本团队包括：
- **产品经理**：分析用户需求，制定详细的产品规格和技术方案，推荐最合适的技术栈
- **全栈软件工程师**：根据产品规格实现高质量的软件解决方案，精通多种编程语言和技术栈
- **质量保证工程师**：全面审查代码质量，验证功能完整性，并交付最终产品

### 工作流程
```
产品经理（需求分析 + 技术选型）
    ↓
软件工程师（代码实现）
    ↓
QA 工程师（审查 + 保存）
    ├─ 发现问题 → 委托工程师修复 ↺
    └─ 通过 → 创建目录 → 保存文件 ✓
```

## 安装

### 前置要求
- Python 3.10, 3.11, 3.12 或 3.13
- 兼容的 LLM API 访问权限（OpenAI、千问等）

### 使用 uv 安装和运行（推荐）

#### 1. 安装 uv
uv 是一个极快的 Python 包管理器和项目管理工具。

**Windows (PowerShell)**：
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux**：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**使用 pip**：
```bash
pip install uv
```

#### 2. 配置环境变量
创建 `.env` 文件并填入 API 凭证：
```env
OPENAI_API_KEY=你的API密钥
OPENAI_API_BASE=你的API基础URL  # 可选，用于自定义端点
MODEL=你的模型名称
```

#### 3. 安装项目依赖
使用 uv 同步安装所有依赖：
```bash
uv sync
```

这将自动：
- 创建虚拟环境（如果不存在）
- 安装 `pyproject.toml` 中定义的所有依赖
- 以可编辑模式安装项目本身

#### 4. 运行项目
使用 uv 运行项目：
```bash
# 交互模式
uv run software_dev_crew

# 命令行模式
uv run software_dev_crew "CLI 工具" "创建一个支持正则表达式的批量文件重命名工具"
```

### 传统安装方式（使用 pip）

如果不使用 uv，可以使用传统的 pip 方式：

1. **配置环境**：创建 `.env` 文件（同上）

2. **安装依赖**：
   ```bash
   pip install -e .
   ```

## 使用方法

### 交互模式
直接运行命令并按提示操作：
```bash
software_dev_crew
```

### 命令行模式
将项目类型和需求作为参数提供：
```bash
# CLI 工具
software_dev_crew "CLI 工具" "创建一个支持正则表达式的批量文件重命名工具"

# Python 库
software_dev_crew "Python 库" "创建一个带重试逻辑的简单 HTTP 客户端封装"

# 实用工具
software_dev_crew "实用程序" "创建一个 JSON 格式化和验证工具"
```

### 训练模式
使用自定义示例训练团队：
```bash
software_dev_crew train 5 training_data.pkl
```

## 项目结构
```
software-dev-crew/
├── src/
│   └── software_dev_crew/
│       ├── main.py              # 入口点，支持 CLI
│       ├── crew.py              # 团队配置
│       ├── config/
│       │   ├── agents.yaml      # 代理定义
│       │   └── tasks.yaml       # 任务模板
│       └── tools/               # 自定义工具
├── pyproject.toml               # 项目配置
├── .env                         # 环境变量
└── README.md                    # 本文件
```

## 核心组件
- **`main.py`**：处理用户输入和团队执行
- **`crew.py`**：定义代理团队和工作流
- **`agents.yaml`**：配置代理角色和能力
- **`tasks.yaml`**：定义开发、审查和评估任务

## 更新日志

### 最新更新 (2026-03-20)

#### 依赖升级
- **CrewAI**: 升级到 `1.11.0` 版本
- **Python 支持**: 扩展到 Python 3.10-3.13（之前仅支持 3.10-3.11）
- **依赖管理**: 移除 `python-dotenv` 显式依赖（已包含在 crewai 中）
- **构建系统**: 添加 hatchling 构建后端配置

#### 功能改进
- **流式输出**: 启用实时流式输出，可以实时查看 AI 代理的工作过程
- **环境变量**: 简化 LLM 配置，使用 `MODEL` 环境变量替代 `OPENAI_MODEL_NAME`
- **输出优化**: 改进控制台输出格式，提供更清晰的执行反馈

#### 配置文件更新
- 更新 `.env.example` 使用标准的 `MODEL` 环境变量
- 添加 `.python-version` 文件指定 Python 3.13
- 更新 `pyproject.toml` 配置以匹配最新的 CrewAI 最佳实践

#### 文档改进
- 更新 README 中的环境变量配置说明
- 添加 Python 版本兼容性说明
- 改进安装和使用说明

## License
This project is released under the MIT License.
