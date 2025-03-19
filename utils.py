import os
import re
import tempfile
from typing import List, Dict, Any, Optional

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    参数:
        filename: 原始文件名
        
    返回:
        清理后的文件名
    """
    # 移除不安全字符
    sanitized = re.sub(r'[^\w\s.-]', '_', filename)
    # 确保文件名不为空
    if not sanitized:
        sanitized = "unnamed_file"
    return sanitized

def save_upload_file(file_content: bytes, filename: str) -> str:
    """
    保存上传的文件
    
    参数:
        file_content: 文件内容
        filename: 文件名
        
    返回:
        保存后的文件路径
    """
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 清理文件名
    safe_filename = sanitize_filename(filename)
    
    # 构建文件路径
    file_path = os.path.join(temp_dir, safe_filename)
    
    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    return file_path

def format_agent_response(response: Dict[str, Any]) -> str:
    """
    格式化Agent的回应，用于显示
    
    参数:
        response: Agent回应数据
        
    返回:
        格式化后的文本
    """
    return f"{response['agent_name']}: {response['content']}"

def format_round_result(round_result: Dict[str, Any]) -> str:
    """
    格式化一轮对话结果，用于显示
    
    参数:
        round_result: 轮次结果数据
        
    返回:
        格式化后的文本
    """
    result = f"轮次 {round_result['round']}:\n"
    for response in round_result['responses']:
        result += f"{response['agent_name']}:\n{response['content']}\n\n"
    return result

def count_words(text: str) -> int:
    """
    计算文本中的字数
    
    参数:
        text: 要计算的文本
        
    返回:
        字数
    """
    # 移除空白字符
    text = re.sub(r'\s+', '', text)
    return len(text)

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    截断文本
    
    参数:
        text: 原始文本
        max_length: 最大长度
        
    返回:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def detect_format(text: str) -> str:
    """
    检测文本格式（普通文本、Markdown等）
    
    参数:
        text: 要检测的文本
        
    返回:
        格式类型
    """
    # 检测是否为Markdown
    md_patterns = [
        r'^#+ ',  # 标题
        r'\*\*.*\*\*',  # 粗体
        r'\*.*\*',  # 斜体
        r'^\s*[-*+] ',  # 无序列表
        r'^\s*\d+\. ',  # 有序列表
        r'```',  # 代码块
        r'\[.*\]\(.*\)'  # 链接
    ]
    
    for pattern in md_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return "markdown"
    
    return "text"

def remove_markdown_formatting(text: str) -> str:
    """
    移除Markdown格式
    
    参数:
        text: 包含Markdown格式的文本
        
    返回:
        移除格式后的纯文本
    """
    # 替换标题
    text = re.sub(r'^#+ (.*?)$', r'\1', text, flags=re.MULTILINE)
    
    # 替换粗体和斜体
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # 替换列表
    text = re.sub(r'^\s*[-*+] ', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\. ', '', text, flags=re.MULTILINE)
    
    # 替换代码块
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 替换链接
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    return text 