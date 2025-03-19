from agents import create_agents
from config import load_config
import time
import asyncio
import threading
import concurrent.futures
import os

class Conversation:
    """
    管理多Agent对话流程，支持并发执行
    """
    def __init__(self, config=None):
        self.config = config or load_config()
        print("🤖 初始化Conversation，创建Agent...")
        self.agents = create_agents(self.config)
        print(f"✅ 成功创建 {len(self.agents)} 个Agent")
        self.history = []
        self.current_round = 0
        self.max_rounds = self.config["max_rounds"]
        self.original_text = ""
        self.reference_data = {}
        self.final_text = ""
        self.callbacks = {"on_agent_response": None}  # 回调函数
    
    def register_callback(self, event_name, callback_fn):
        """
        注册回调函数，用于实时通知UI更新
        
        参数:
            event_name: 事件名称
            callback_fn: 回调函数
        """
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback_fn
    
    def start_conversation(self, original_text, reference_data, max_rounds=None):
        """
        开始一次新的多Agent对话
        
        参数:
            original_text: 待润色的原始文章
            reference_data: 参考资料信息（处理后的，包含类型标记）
            max_rounds: 最大对话轮次（可选，默认使用配置中的值）
        
        返回:
            第一轮对话结果
        """
        print("📝 开始新的对话流程...")
        self.original_text = original_text
        self.reference_data = reference_data
        self.history = []
        self.current_round = 0
        
        # 清理旧的输出文件
        self._clean_output_files()
        
        if max_rounds is not None:
            self.max_rounds = max_rounds
        
        # 开始第一轮对话
        try:
            return self.next_round()
        except Exception as e:
            import traceback
            print(f"❌ 启动对话时出错: {str(e)}")
            traceback.print_exc()
            raise
    
    def _clean_output_files(self):
        """
        清理之前的输出文件
        """
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
    
    def next_round(self):
        """
        进行下一轮对话，使用串行执行但快速传递结果的方式
        
        返回:
            当前轮次的对话结果，如果已达到最大轮次，则返回最终润色结果
        """
        if self.current_round >= self.max_rounds:
            print(f"🏁 已达到最大轮次 {self.max_rounds}，生成最终结果")
            return self.generate_final_text()
        
        print(f"🔄 开始第 {self.current_round + 1} 轮对话...")
        round_responses = []
        context = self._get_conversation_context()
        
        # 获取参考资料类型
        ref_type = self.reference_data.get("ref_type", "self")
        print(f"📚 使用参考资料类型: {ref_type}")
        
        try:
            # 获取所有Agent（包括最后一个综合评审员）
            agents = self.agents
            
            # 当前文本，初始为原始文本
            current_text = self.original_text
            
            # 当前上下文，初始为空
            current_context = context
            
            # 创建一个目录用于保存中间结果
            output_dir = "agent_outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            # 依次执行每个Agent
            for i, agent in enumerate(agents):
                agent_name = agent.name
                print(f"🤖 正在处理: {agent_name}")
                
                start_time = time.time()
                
                # 创建响应对象
                response = {
                    "agent_name": agent_name,
                    "agent_color": agent.color,
                    "content": ""
                }
                
                # 流式回调函数
                def agent_callback(name, chunk):
                    response["content"] += chunk
                    # 通知UI更新
                    if self.callbacks["on_agent_response"]:
                        self.callbacks["on_agent_response"]({
                            "agent_name": name,
                            "agent_color": agent.color,
                            "content": chunk,
                            "is_chunk": True
                        })
                
                try:
                    # 执行Agent，使用流式输出
                    agent_response = agent.generate_response(
                        current_text,
                        self.reference_data,
                        current_context,
                        stream=True,
                        callback=agent_callback
                    )
                    
                    # 更新响应内容
                    response["content"] = agent_response
                    
                    # 将结果保存为Markdown文件
                    markdown_file = os.path.join(output_dir, f"round_{self.current_round + 1}_{agent_name}.md")
                    with open(markdown_file, "w", encoding="utf-8") as f:
                        f.write(f"# {agent_name} 的润色建议\n\n")
                        f.write(agent_response)
                    
                    print(f"✅ 已保存 {agent_name} 的处理结果到 {markdown_file}")
                    
                    # 更新上下文，加入当前Agent的输出
                    current_context += f"\n{agent_name}: {agent_response}"
                    
                    # 提取修改后的文章内容（如果存在）
                    if "# 修改后的文章内容" in agent_response:
                        parts = agent_response.split("# 修改后的文章内容")
                        if len(parts) > 1:
                            # 提取修改后的文章内容作为下一个Agent的输入
                            modified_text = parts[1].strip()
                            print(f"🔄 从 {agent_name} 的输出中提取了修改后的文章内容: {len(modified_text)} 字符")
                            
                            # 更新当前文本，作为下一个Agent的输入
                            current_text = modified_text
                        else:
                            print(f"⚠️ 无法从 {agent_name} 的输出中提取修改后的文章内容")
                    else:
                        print(f"⚠️ {agent_name} 的输出中没有找到修改后的文章内容部分")
                    
                except Exception as e:
                    import traceback
                    print(f"❌ Agent {agent_name} 执行失败: {str(e)}")
                    traceback.print_exc()
                    # 添加错误响应
                    response["content"] = f"[处理过程中出错: {str(e)}]"
                    # 通知UI更新错误
                    if self.callbacks["on_agent_response"]:
                        self.callbacks["on_agent_response"]({
                            "agent_name": agent_name,
                            "agent_color": agent.color,
                            "content": response["content"],
                            "is_error": True
                        })
                
                # 记录Agent响应
                round_responses.append(response)
                
                elapsed = time.time() - start_time
                print(f"✅ {agent_name} 响应完成，耗时: {elapsed:.2f}秒，长度: {len(response['content'])} 字符")
            
            # 更新历史记录
            round_result = {
                "round": self.current_round + 1,
                "responses": round_responses
            }
            
            self.history.append(round_result)
            self.current_round += 1
            
            print(f"🎉 第 {self.current_round} 轮对话完成，共 {len(round_responses)} 个响应")
            return round_result
        except Exception as e:
            import traceback
            print(f"❌ 对话过程中出错: {str(e)}")
            traceback.print_exc()
            
            # 返回错误响应而不是抛出异常，让程序能够继续运行
            error_result = {
                "round": self.current_round + 1,
                "responses": round_responses,
                "error": str(e)
            }
            
            # 尝试增加当前轮次，以便下次调用能继续
            self.current_round += 1
            
            return error_result
    
    def _execute_agent_task(self, agent, text, reference_data, context, use_stream=False):
        """
        执行单个Agent任务的辅助函数
        
        参数:
            agent: Agent对象
            text: 需要润色的文本
            reference_data: 参考资料
            context: 对话上下文
            use_stream: 是否使用流式输出
            
        返回:
            格式化的Agent响应字典
        """
        agent_name = agent.name
        print(f"🤖 请求 {agent_name} 生成响应...")
        start_time = time.time()
        
        # 创建中间结果，用于流式输出时记录
        result = {
            "agent_name": agent_name,
            "agent_color": agent.color,
            "content": ""
        }
        
        # 流式输出的回调函数
        def agent_callback(agent_name, chunk):
            result["content"] += chunk
            
            # 如果已注册回调函数，通知UI更新
            if self.callbacks["on_agent_response"]:
                self.callbacks["on_agent_response"]({
                    "agent_name": agent_name,
                    "agent_color": agent.color,
                    "content": chunk,
                    "is_chunk": True  # 标记这是一个流式块
                })
        
        try:
            # 调用Agent生成响应，根据需要使用流式输出
            if use_stream:
                response = agent.generate_response(
                    text, 
                    reference_data, 
                    context,
                    stream=True,
                    callback=agent_callback
                )
            else:
                response = agent.generate_response(text, reference_data, context)
                result["content"] = response
            
            elapsed = time.time() - start_time
            print(f"✅ {agent_name} 响应完成，耗时: {elapsed:.2f}秒，长度: {len(result['content'])} 字符")
        
        except Exception as e:
            import traceback
            print(f"❌ Agent {agent_name} 执行出错: {str(e)}")
            traceback.print_exc()
            
            # 出错时返回错误信息
            result["content"] = f"[生成过程中出错: {str(e)}]"
            
            # 如果已注册回调函数，通知UI更新错误信息
            if self.callbacks["on_agent_response"]:
                self.callbacks["on_agent_response"]({
                    "agent_name": agent_name,
                    "agent_color": agent.color,
                    "content": result["content"],
                    "is_error": True
                })
        
        # 如果未使用流式输出但有回调函数，通知UI完整结果
        if not use_stream and self.callbacks["on_agent_response"]:
            self.callbacks["on_agent_response"](result)
        
        return result
    
    def generate_final_text(self):
        """
        生成最终润色后的文章
        
        返回:
            最终润色后的文章和对话历史
        """
        print("🏆 生成最终润色结果...")
        
        try:
            # 收集所有Agent的建议
            expert_suggestions = ""
            for round_data in self.history:
                expert_suggestions += f"\n轮次 {round_data['round']}:\n"
                for response in round_data["responses"]:
                    expert_suggestions += f"{response['agent_name']}: {response['content']}\n"
            
            print(f"📋 汇总了 {len(self.history)} 轮对话的建议")
            
            # 使用综合评审员生成最终文章
            reviewer = self.agents[-1]
            print(f"🤖 请求 {reviewer.name} 生成最终文章...")
            start_time = time.time()
            
            self.final_text = reviewer.generate_final_text(
                self.original_text,
                expert_suggestions,
                self.reference_data.get("style_analysis", "")
            )
            
            elapsed = time.time() - start_time
            print(f"✅ 最终文章生成完成，耗时: {elapsed:.2f}秒，长度: {len(self.final_text)} 字符")
            
            # 确保输出目录存在
            output_dir = "agent_outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            # 将最终结果保存为文件
            final_file = os.path.join(output_dir, "final_result.md")
            with open(final_file, "w", encoding="utf-8") as f:
                f.write(self.final_text)
            
            print(f"💾 已保存最终润色结果到 {final_file}")
            
            # 检查是否包含了所需的两个部分
            if "# 综合评审员的润色建议" not in self.final_text or "# 最终润色结果" not in self.final_text:
                print("⚠️ 警告: 最终结果可能格式不正确，缺少必要的部分")
                
                # 如果格式不正确，尝试修复
                if "# 综合评审员的润色建议" not in self.final_text and "# 最终润色结果" not in self.final_text:
                    # 两个部分都缺失，创建一个基本结构
                    fixed_text = f"# 综合评审员的润色建议\n\n[综合建议未正确格式化]\n\n# 最终润色结果\n\n{self.final_text}"
                    self.final_text = fixed_text
                elif "# 综合评审员的润色建议" in self.final_text and "# 最终润色结果" not in self.final_text:
                    # 缺少最终结果部分
                    parts = self.final_text.split("# 综合评审员的润色建议")
                    suggestions = parts[1].strip() if len(parts) > 1 else ""
                    fixed_text = f"# 综合评审员的润色建议\n\n{suggestions}\n\n# 最终润色结果\n\n{self.original_text}"
                    self.final_text = fixed_text
            
            # 标记为最终结果
            result = {
                "final_text": self.final_text,
                "history": self.history,
                "is_final": True
            }
            
            print("🎉 对话流程全部完成")
            return result
        except Exception as e:
            import traceback
            print(f"❌ 生成最终文章时出错: {str(e)}")
            traceback.print_exc()
            raise
    
    def _get_conversation_context(self):
        """
        获取当前对话上下文
        
        返回:
            格式化的对话历史字符串
        """
        context = ""
        for round_data in self.history:
            context += f"\n轮次 {round_data['round']}:\n"
            for response in round_data["responses"]:
                context += f"{response['agent_name']}: {response['content']}\n"
        
        context_length = len(context)
        print(f"📜 获取对话上下文，长度: {context_length} 字符")
        return context
    
    def get_progress(self):
        """
        获取当前对话进度
        
        返回:
            进度信息（当前轮次/总轮次）
        """
        progress = {
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "progress_percentage": (self.current_round / self.max_rounds) * 100 if self.max_rounds > 0 else 0
        }
        
        print(f"📊 当前进度: {progress['progress_percentage']:.1f}%")
        return progress 