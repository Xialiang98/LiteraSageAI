import os
import threading
from document_processor import DocumentProcessor
from conversation import Conversation
from config import load_config, update_mechanical_words

class Engine:
    """
    交互引擎 - 管理整个文章润色流程
    """
    def __init__(self):
        self.config = load_config()
        self.document_processor = DocumentProcessor(self.config)
        self.conversation = Conversation(self.config)
        self.reference_docs = {}
        self.reference_articles = {}
        self.original_text = ""
        self.lock = threading.Lock()
        self.processing = False
        self.agent_callback = None  # 用于Agent响应的回调函数
    
    def register_agent_callback(self, callback_fn):
        """
        注册Agent响应回调函数，用于实时更新UI
        
        参数:
            callback_fn: 回调函数 callback_fn(response_data)，其中response_data包含agent_name, content等字段
        """
        self.agent_callback = callback_fn
        # 同时注册到conversation对象
        self.conversation.register_callback("on_agent_response", callback_fn)
    
    def process_reference_documents(self, file_paths, ref_type="document"):
        """
        处理参考文档或参考文章
        
        参数:
            file_paths: 参考文件的文件路径列表
            ref_type: 参考类型，"document"(文档) 或 "article"(文章)
            
        返回:
            处理结果
        """
        with self.lock:
            self.processing = True
        
        try:
            # 根据不同类型的参考资料，传递不同的处理指令
            if ref_type == "document":
                result = self.document_processor.process_reference_docs(file_paths, ref_type)
                self.reference_docs = result
                ref_name = "参考文档"
            else:  # ref_type == "article"
                result = self.document_processor.process_reference_docs(file_paths, ref_type)
                self.reference_articles = result
                ref_name = "参考文章"
            
            return {
                "success": True,
                "message": f"成功处理 {len(file_paths)} 个{ref_name}",
                "style_analysis": result.get("style_analysis", "")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"处理{ref_type}时出错: {str(e)}"
            }
        finally:
            with self.lock:
                self.processing = False
    
    def process_reference_text(self, text, ref_type="article"):
        """
        处理参考文本内容
        
        参数:
            text: 参考文本内容
            ref_type: 参考类型，"document"(文档) 或 "article"(文章)
            
        返回:
            处理结果
        """
        with self.lock:
            self.processing = True
        
        try:
            # 根据不同类型的参考资料，传递不同的处理指令
            result = self.document_processor.process_reference_text(text, ref_type)
            
            if ref_type == "document":
                self.reference_docs = result
                ref_name = "参考文档"
            else:  # ref_type == "article"
                self.reference_articles = result
                ref_name = "参考文章"
            
            return {
                "success": True,
                "message": f"成功处理{ref_name}",
                "style_analysis": result.get("style_analysis", "")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"处理{ref_type}时出错: {str(e)}"
            }
        finally:
            with self.lock:
                self.processing = False
    
    def start_polishing(self, original_text, max_rounds=None):
        """
        开始文章润色流程
        
        参数:
            original_text: 待润色的原始文章
            max_rounds: 最大对话轮次（可选）
            
        返回:
            第一轮对话结果
        """
        with self.lock:
            if self.processing:
                return {
                    "success": False,
                    "message": "系统正在处理其他任务，请稍后再试"
                }
            
            self.processing = True
        
        try:
            # 清理旧的输出文件目录
            output_dir = "agent_outputs"
            if os.path.exists(output_dir):
                print(f"🧹 清理旧的输出文件...")
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
            
            self.original_text = original_text
            
            # 合并参考文档和参考文章
            references = {}
            
            # 首先检查是否有参考文章，文章优先级高于文档
            if self.reference_articles:
                references = self.reference_articles
                references["ref_type"] = "article"
                print(f"📊 参考资料类型: article，风格分析长度: {len(references.get('style_analysis', ''))} 字符")
            # 其次检查是否有参考文档
            elif self.reference_docs:
                references = self.reference_docs
                references["ref_type"] = "document"
                print(f"📊 参考资料类型: document，风格分析长度: {len(references.get('style_analysis', ''))} 字符")
            # 如果两者都没有，使用原始文章作为参考
            else:
                references = {
                    "content": original_text,
                    "style_analysis": "未提供参考资料，将基于原始文章进行润色。",
                    "ref_type": "self"
                }
                print("📊 参考资料类型: self")
            
            print(f"📝 原始文章长度: {len(original_text)} 字符")
            print(f"🔄 设置最大轮次: {max_rounds}")
            print("🚀 开始调用Agent进行润色...")
            
            # 开始会话
            result = self.conversation.start_conversation(
                original_text,
                references,
                max_rounds
            )
            
            return {
                "success": True,
                "message": "成功启动润色流程",
                "result": result
            }
        except Exception as e:
            import traceback
            print(f"❌ 启动润色流程时出错: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "message": f"启动润色流程时出错: {str(e)}"
            }
        finally:
            with self.lock:
                self.processing = False
    
    def next_round(self):
        """
        进行下一轮润色
        
        返回:
            下一轮对话结果或最终结果
        """
        with self.lock:
            if self.processing:
                return {
                    "success": False,
                    "message": "系统正在处理其他任务，请稍后再试"
                }
            
            self.processing = True
        
        try:
            result = self.conversation.next_round()
            
            if result.get("is_final", False):
                # 最终轮次
                return {
                    "success": True,
                    "message": "润色完成！",
                    "is_final": True,
                    "final_result": result
                }
            else:
                # 普通轮次
                return {
                    "success": True,
                    "message": f"完成第 {result.get('round', '?')} 轮润色",
                    "is_final": False,
                    "result": result
                }
        except Exception as e:
            import traceback
            print(f"❌ 进行下一轮润色时出错: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "message": f"进行下一轮润色时出错: {str(e)}"
            }
        finally:
            with self.lock:
                self.processing = False
    
    def get_progress(self):
        """
        获取当前润色进度
        
        返回:
            进度信息
        """
        current_round = self.conversation.current_round
        max_rounds = self.conversation.max_rounds
        
        # 计算百分比进度
        if max_rounds > 0:
            progress_percentage = min(100, int((current_round / max_rounds) * 100))
        else:
            progress_percentage = 0
        
        return {
            "success": True,
            "current_round": current_round,
            "max_rounds": max_rounds,
            "progress_percentage": progress_percentage
        }
    
    def update_mechanical_words(self, new_words):
        """
        更新机械用语列表
        
        参数:
            new_words: 新的机械用语列表
            
        返回:
            更新结果
        """
        try:
            # 调用config模块中的update_mechanical_words函数
            result = update_mechanical_words(new_words)
            
            # 重新加载更新后的配置
            self.config = load_config()
            
            # 更新其他组件的配置
            self.document_processor.config = self.config
            self.conversation.config = self.config
            
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"更新机械用语时出错: {str(e)}"
            }
    
    def extract_mechanical_words(self, text):
        """
        从文本中提取可能的机械用语
        
        参数:
            text: 要分析的文本
            
        返回:
            提取结果
        """
        try:
            # 这里实现一个简单的机械用语提取算法
            # 实际应用中可能需要更复杂的NLP技术
            
            # 预定义的常见机械用语列表
            common_mechanical_words = [
                "总而言之", "总之", "因此", "故而", "所以", "换句话说",
                "诚然", "显而易见", "毫无疑问", "众所周知", "不言而喻",
                "事实上", "实际上", "客观上", "主观上", "可以说",
                "说到底", "归根结底", "说白了", "简而言之"
            ]
            
            # 从文本中提取出现的机械用语
            words = []
            for word in common_mechanical_words:
                if word in text:
                    words.append(word)
            
            return {
                "success": True,
                "message": f"成功从文本中提取到 {len(words)} 个机械用语",
                "mechanical_words": words
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"提取机械用语时出错: {str(e)}"
            }
    
    def reset(self):
        """
        重置引擎状态
        """
        with self.lock:
            self.processing = False
            # 注意：我们不重置参考文档和参考文章，只重置会话状态
            self.original_text = ""
            
            # 创建一个新的会话对象
            self.conversation = Conversation(self.config)
            
            # 如果有回调函数，重新注册
            if self.agent_callback:
                self.conversation.register_callback("on_agent_response", self.agent_callback)
            
            print("🔄 引擎状态已重置") 