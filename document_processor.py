import os
import tempfile
from openai import OpenAI
from config import load_config

class DocumentProcessor:
    """
    文档处理模块 - 负责处理用户上传的文档
    """
    def __init__(self, config=None):
        self.config = config or load_config()
        self.client = OpenAI(
            api_key=self.config["api"]["deepseek_key"],
            base_url=self.config["api"]["deepseek_base_url"]
        )
    
    def process_reference_docs(self, file_paths, ref_type="document"):
        """
        处理参考文档或参考文章，提取风格特征
        
        参数:
            file_paths: 参考文件的文件路径列表
            ref_type: 参考类型，"document"(文档) 或 "article"(文章)
            
        返回:
            文档内容和风格特征的摘要
        """
        combined_text = ""
        
        # 读取所有参考文件内容
        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_text += f"\n文件: {os.path.basename(file_path)}\n{content}\n"
        
        # 如果没有文件内容，返回空字典
        if not combined_text.strip():
            return {}
        
        # 根据参考类型使用不同的提示词
        if ref_type == "document":
            prompt = """
            请分析以下参考文档的内容和风格特征，提取以下元素：
            1. 文章的主要内容和主题
            2. 语言风格（如正式/非正式、学术性/通俗性等）
            3. 常用词汇和表达方式
            4. 论证方式和结构特点
            5. 行文逻辑和思维方式
            
            请关注文档的理论性、学术性和指导性特点，这些将用于指导文章润色。
            提供简洁清晰的总结，以便用作文章润色的参考依据。不要使用markdown格式。
            """
        else:  # ref_type == "article"
            prompt = """
            请分析以下参考文章的文学风格和艺术特点，提取其中的以下元素：
            1. 文体风格（如抒情、叙事、议论、写意等）
            2. 语言特色（如简练、华丽、含蓄、直白等）
            3. 修辞手法和表现技巧
            4. 情感基调和氛围营造
            5. 结构安排和节奏变化
            6. 独特的词汇选择和句式特点
            
            请特别关注文章的文学性、艺术性和风格鲜明度，这些将用于文章的风格润色。
            提供简洁清晰的风格特征总结，以便用作文章润色的风格参考。不要使用markdown格式。
            """
        
        # 使用DeepSeek分析参考文件风格
        response = self.client.chat.completions.create(
            model=self.config["api"]["model"],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": combined_text}
            ],
            stream=False
        )
        
        style_analysis = response.choices[0].message.content
        
        return {
            "content": combined_text,
            "style_analysis": style_analysis
        }
    
    def save_temp_file(self, file_content, file_name):
        """
        保存临时文件
        
        参数:
            file_content: 文件内容（字节或字符串）
            file_name: 文件名
            
        返回:
            临时文件路径
        """
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_name)
        
        # 确定内容类型并保存
        mode = 'wb' if isinstance(file_content, bytes) else 'w'
        encoding = None if isinstance(file_content, bytes) else 'utf-8'
        
        with open(file_path, mode, encoding=encoding) as f:
            f.write(file_content)
        
        return file_path
    
    def extract_mechanical_words(self, text):
        """
        从文本中提取机械用语
        
        参数:
            text: 要分析的文本
            
        返回:
            找到的机械用语列表
        """
        prompt = """
        请从以下文本中提取所有的机械用语，例如：
        "总而言之"、"总之"、"因此"、"故而"、"所以"、"换句话说"、
        "诚然"、"显而易见"、"毫无疑问"、"众所周知"、"不言而喻"等。
        
        仅返回找到的机械用语列表，每个词一行，不要添加其他解释或编号。
        """
        
        response = self.client.chat.completions.create(
            model=self.config["api"]["model"],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            stream=False
        )
        
        mechanical_words = response.choices[0].message.content.strip().split('\n')
        return [word.strip() for word in mechanical_words if word.strip()]
    
    def remove_mechanical_words(self, text, mechanical_words):
        """
        从文本中移除机械用语
        
        参数:
            text: 要处理的文本
            mechanical_words: 要移除的机械用语列表
            
        返回:
            处理后的文本
        """
        prompt = f"""
        请重写以下文本，移除或替换其中的机械用语，使文章更加流畅自然。
        
        需要注意的机械用语有：{', '.join(mechanical_words)}
        
        重写时，应保持原文的意思和风格，但使表达更加生动、自然。
        直接输出重写后的文本，不要添加任何解释或额外内容。
        """
        
        response = self.client.chat.completions.create(
            model=self.config["api"]["model"],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            stream=False
        )
        
        return response.choices[0].message.content
    
    def process_reference_text(self, text, ref_type="article"):
        """
        处理参考文本内容，提取风格特征
        
        参数:
            text: 参考文本内容
            ref_type: 参考类型，"document"(文档) 或 "article"(文章)
            
        返回:
            文本内容和风格特征的摘要
        """
        # 如果没有文本内容，返回空字典
        if not text.strip():
            return {}
        
        # 根据参考类型使用不同的提示词
        if ref_type == "document":
            prompt = """
            请分析以下参考文档的内容和风格特征，提取以下元素：
            1. 文章的主要内容和主题
            2. 语言风格（如正式/非正式、学术性/通俗性等）
            3. 常用词汇和表达方式
            4. 论证方式和结构特点
            5. 行文逻辑和思维方式
            
            请关注文档的理论性、学术性和指导性特点，这些将用于指导文章润色。
            提供简洁清晰的总结，以便用作文章润色的参考依据。不要使用markdown格式。
            """
        else:  # ref_type == "article"
            prompt = """
            请分析以下参考文章的文学风格和艺术特点，提取其中的以下元素：
            1. 文体风格（如抒情、叙事、议论、写意等）
            2. 语言特色（如简练、华丽、含蓄、直白等）
            3. 修辞手法和表现技巧
            4. 情感基调和氛围营造
            5. 结构安排和节奏变化
            6. 独特的词汇选择和句式特点
            
            请特别关注文章的文学性、艺术性和风格鲜明度，这些将用于文章的风格润色。
            提供简洁清晰的风格特征总结，以便用作文章润色的风格参考。不要使用markdown格式。
            """
        
        # 使用DeepSeek分析参考文本风格
        response = self.client.chat.completions.create(
            model=self.config["api"]["model"],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            stream=False
        )
        
        style_analysis = response.choices[0].message.content
        
        return {
            "content": text,
            "style_analysis": style_analysis
        } 