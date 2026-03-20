# Software Development Crew - CrewAI A2A Template

[中文版](./README.md) | English

## Introduction
This project uses the CrewAI framework to automate software development tasks. CrewAI orchestrates autonomous AI agents to collaborate on building various software projects, supporting multiple programming languages (Python, JavaScript/TypeScript, Go, Rust, Java, etc.), including CLI tools, web applications, desktop applications, mobile applications, and more.

## Demo

![Software Development Crew Real-time Streaming Output Demo](https://github.com/user-attachments/assets/606474a6-7fc4-4369-a5b0-7504dd01f8a9)

*Real-time streaming output showing AI agents' thinking and working process*

## Features
- **Multi-language Support**: Supports Python, JavaScript/TypeScript, Go, Rust, Java, and more
- **Full-stack Development**: Frontend frameworks (React, Vue, Svelte), Backend frameworks (FastAPI, Express, Django)
- **Automated Code Review**: Multi-stage quality assurance process
- **Real-time Streaming Output**: Live display of AI agents' thinking and working process for better user experience
- **Interactive and CLI Modes**: Supports both interactive usage and command-line arguments
- **Production-ready Code**: Generates complete, documented, and tested code

## Supported Project Types
- CLI tools (multi-language)
- Programming language libraries (Python, JavaScript, Go, etc.)
- Utilities and scripts
- Web applications (frontend + backend)
- Desktop applications
- Mobile applications
- Data processing tools

## CrewAI Framework
CrewAI facilitates collaboration between role-playing AI agents. This crew includes:
- **Product Manager**: Analyzes user requirements, creates detailed product specifications and technical solutions, recommends the most suitable tech stack
- **Full-stack Software Engineer**: Implements high-quality software solutions based on product specifications, proficient in multiple programming languages and tech stacks
- **Quality Assurance Engineer**: Comprehensively reviews code quality, verifies functional completeness, and delivers the final product

### Workflow
```
Product Manager (Requirements Analysis + Tech Selection)
    ↓
Software Engineer (Code Implementation)
    ↓
QA Engineer (Review + Save)
    ├─ Issues Found → Delegate to Engineer for Fix ↺
    └─ Passed → Create Directory → Save Files ✓
```

## Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Compatible LLM API access (OpenAI, Qwen, etc.)

### Install and Run with uv (Recommended)

#### 1. Install uv
uv is an extremely fast Python package manager and project management tool.

**Windows (PowerShell)**:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pip**:
```bash
pip install uv
```

#### 2. Configure Environment Variables
Create a `.env` file and fill in your API credentials:
```env
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base_url  # Optional, for custom endpoints
MODEL=your_model_name
```

#### 3. Install Project Dependencies
Use uv to sync and install all dependencies:
```bash
uv sync
```

This will automatically:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies defined in `pyproject.toml`
- Install the project itself in editable mode

#### 4. Run the Project
Use uv to run the project:
```bash
# Interactive mode
uv run software_dev_crew

# CLI mode
uv run software_dev_crew "CLI tool" "Create a batch file renaming tool with regex support"
```

### Traditional Installation (Using pip)

If you prefer not to use uv, you can use the traditional pip approach:

1. **Configure Environment**: Create a `.env` file (same as above)

2. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

## Usage

### Interactive Mode
Run the command directly and follow the prompts:
```bash
software_dev_crew
```

### CLI Mode
Provide project type and requirements as arguments:
```bash
# CLI tool
software_dev_crew "CLI tool" "Create a batch file renaming tool with regex support"

# Python library
software_dev_crew "Python library" "Create a simple HTTP client wrapper with retry logic"

# Utility
software_dev_crew "Utility" "Create a JSON formatting and validation tool"
```

### Training Mode
Train the crew with custom examples:
```bash
software_dev_crew train 5 training_data.pkl
```

## Project Structure
```
software-dev-crew/
├── src/
│   └── software_dev_crew/
│       ├── main.py              # Entry point with CLI support
│       ├── crew.py              # Crew configuration
│       ├── config/
│       │   ├── agents.yaml      # Agent definitions
│       │   └── tasks.yaml       # Task templates
│       └── tools/               # Custom tools
├── pyproject.toml               # Project configuration
├── .env                         # Environment variables
└── README.md                    # This file
```

## Core Components
- **`main.py`**: Handles user input and crew execution
- **`crew.py`**: Defines the agent crew and workflow
- **`agents.yaml`**: Configures agent roles and capabilities
- **`tasks.yaml`**: Defines development, review, and evaluation tasks

## Changelog

### Latest Update (2026-03-20)

#### Dependency Upgrades
- **CrewAI**: Upgraded to version `1.11.0`
- **Python Support**: Extended to Python 3.10-3.13 (previously only 3.10-3.11)
- **Dependency Management**: Removed explicit `python-dotenv` dependency (already included in crewai)
- **Build System**: Added hatchling build backend configuration

#### Feature Improvements
- **Streaming Output**: Enabled real-time streaming output to view AI agents' working process in real-time
- **Environment Variables**: Simplified LLM configuration, using `MODEL` environment variable instead of `OPENAI_MODEL_NAME`
- **Output Optimization**: Improved console output format for clearer execution feedback

#### Configuration File Updates
- Updated `.env.example` to use standard `MODEL` environment variable
- Added `.python-version` file specifying Python 3.13
- Updated `pyproject.toml` configuration to match latest CrewAI best practices

#### Documentation Improvements
- Updated environment variable configuration instructions in README
- Added Python version compatibility notes
- Improved installation and usage instructions

## License
This project is released under the MIT License.
