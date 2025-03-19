import gradio as gr
import os
import shutil
from interface import create_interface
from config import load_config

def clean_output_files():
    """
    清理输出文件目录
    """
    output_dir = "agent_outputs"
    
    print(f"🧹 程序启动时清理旧的输出文件...")
    if os.path.exists(output_dir):
        try:
            # 列出所有文件但不删除目录
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"🗑️ 已删除: {file_path}")
            print(f"✅ 已清理 {output_dir} 中的所有输出文件")
        except Exception as e:
            print(f"⚠️ 清理输出文件时出错: {str(e)}")
    else:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 已创建输出目录: {output_dir}")

def main():
    """
    LiteraSageAI 主程序入口
    文学智慧AI - 多Agent协同文章润色系统
    """
    # 清理旧的输出文件
    clean_output_files()
    
    # 加载配置
    config = load_config()
    
    # 创建并启动Gradio界面
    demo = create_interface(config)
    demo.launch(share=True)

if __name__ == "__main__":
    main() 