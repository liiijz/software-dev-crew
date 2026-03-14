import sys
import ssl
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

from software_dev_crew.crew import SoftwareDevCrew


def run():
    """
    运行软件开发团队，根据用户提供的需求生成代码。
    """
    print("## 欢迎使用软件开发团队")
    print('=' * 50)
    
    # 从用户获取项目类型、需求和输出目录
    if len(sys.argv) > 1:
        # 命令行模式
        project_type = sys.argv[1] if len(sys.argv) > 1 else "CLI 工具"
        requirements = sys.argv[2] if len(sys.argv) > 2 else "创建一个简单的实用工具"
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "./output"
    else:
        # 交互模式
        print("\n项目类型：CLI 工具、Python 库、实用程序、Web 应用、桌面应用")
        project_type = input("请输入项目类型（默认：CLI 工具）：").strip() or "CLI 工具"
        print("\n请描述你想要构建的内容：")
        requirements = input("> ").strip() or "创建一个简单的文件处理工具"
        print("\n请输入输出目录（默认：./output）：")
        output_dir = input("> ").strip() or "./output"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📋 项目类型：{project_type}")
    print(f"📝 需求说明：{requirements}")
    print(f"📁 输出目录：{os.path.abspath(output_dir)}")
    print('=' * 50)
    
    inputs = {
        'project_type': project_type,
        'requirements': requirements,
        'output_dir': os.path.abspath(output_dir)
    }
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行任务
    result = SoftwareDevCrew().crew().kickoff(inputs=inputs)
    
    # 计算执行时间
    execution_time = time.time() - start_time

    print("\n\n" + "=" * 50)
    print("## 开发完成！")
    print("=" * 50)
    
    # 显示统计信息
    print("\n📊 执行统计：")
    print(f"⏱️  执行时间：{execution_time:.2f} 秒 ({execution_time/60:.2f} 分钟)")
    
    # 尝试获取 token 使用情况
    try:
        if hasattr(result, 'token_usage'):
            token_usage = result.token_usage
            print(f"🔢 Token 使用：")
            print(f"   - 总计：{token_usage.get('total_tokens', 'N/A')}")
            print(f"   - 输入：{token_usage.get('prompt_tokens', 'N/A')}")
            print(f"   - 输出：{token_usage.get('completion_tokens', 'N/A')}")
        elif hasattr(result, 'usage_metrics'):
            metrics = result.usage_metrics
            print(f"🔢 使用指标：{metrics}")
    except Exception as e:
        print(f"⚠️  无法获取 token 统计信息")
    
    print("\n" + "=" * 50)
    print("生成的代码：")
    print("=" * 50 + "\n")
    print(result)
    

def train():
    """
    训练团队，进行指定次数的迭代。
    用法：software_dev_crew train <迭代次数> <文件名>
    """
    if len(sys.argv) < 3:
        print("用法：software_dev_crew train <迭代次数> <文件名>")
        print("示例：software_dev_crew train 5 training_data.pkl")
        return
    
    # 示例训练输入
    inputs = {
        'project_type': 'CLI 工具',
        'requirements': '创建一个文件重命名工具'
    }
    
    try:
        SoftwareDevCrew().crew().train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"训练团队时发生错误：{e}")
