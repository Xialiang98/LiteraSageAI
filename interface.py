import os
import gradio as gr
from engine import Engine
from utils import save_upload_file, format_round_result, count_words
from config import load_config

# 全局变量
final_result_data = {
    "status": "idle",
    "final_content": "",
    "stats_text": "",
    "conversation_html": "",
    "progress": 0,
    "error": None
}

def create_interface(config=None):
    """
    创建Gradio界面
    
    参数:
        config: 系统配置（可选）
        
    返回:
        Gradio接口对象
    """
    global final_result_data
    
    if not config:
        config = load_config()
    
    # 创建引擎实例
    engine = Engine()
    
    # 用于存储上传文件的路径
    reference_doc_paths = []
    
    # 创建处理队列
    with gr.Blocks(title="LiteraSageAI", theme=gr.themes.Default()) as demo:
        # 启用队列功能，支持流式更新
        demo.queue(concurrency_count=5, max_size=20)
        
        # CSS样式
        css = """
        .agent-response {
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
        }
        .agent-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .blue-bg { background-color: rgba(0, 123, 255, 0.1); border-left: 5px solid #007bff; }
        .green-bg { background-color: rgba(40, 167, 69, 0.1); border-left: 5px solid #28a745; }
        .orange-bg { background-color: rgba(255, 193, 7, 0.1); border-left: 5px solid #ffc107; }
        .purple-bg { background-color: rgba(111, 66, 193, 0.1); border-left: 5px solid #6f42c1; }
        .red-bg { background-color: rgba(220, 53, 69, 0.1); border-left: 5px solid #dc3545; }
        .error-bg { background-color: rgba(220, 53, 69, 0.05); border: 1px dashed #dc3545; }
        .loading-spinner {
            display: inline-block;
            width: 15px;
            height: 15px;
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top-color: #3498db;
            animation: spin 1s linear infinite;
            margin-left: 5px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        """
        
        gr.Markdown("# LiteraSageAI")
        
        # API密钥警告提示状态
        api_warning_state = gr.State(True)  # 默认显示警告
        
        # API密钥警告提示
        api_warning = gr.HTML(
            value="<div style='padding: 10px; background-color: #ffebee; border-left: 5px solid #f44336; margin-bottom: 15px; display: flex; align-items: center;'>"
                  "<span style='font-size: 24px; margin-right: 10px;'>⚠️</span>"
                  "<div>"
                  "<div style='font-weight: bold; color: #d32f2f;'>警告: 未检测到API密钥</div>"
                  "<div>请在左侧面板中填写DeepSeek API密钥，否则润色功能将无法使用</div>"
                  "</div>"
                  "</div>"
        )
        
        # 状态变量
        agent_responses = gr.State({})
        
        # 添加一个状态变量来跟踪正在处理中的Agent
        processing_agents = gr.State([])
        
        # 当前润色状态
        polishing_status = gr.State("idle")  # idle, running, completed, error
        
        # 添加一个全局变量来存储润色结果
        polishing_result = gr.State(None)
        
        with gr.Tabs() as tabs:
            with gr.TabItem("文章润色"):
                with gr.Row():
                    with gr.Column(scale=1):
                        # API配置部分
                        gr.Markdown("## API配置")
                        api_key = gr.Textbox(
                            label="DeepSeek API Key",
                            placeholder="请输入您的DeepSeek API Key",
                            type="password"
                        )
                        
                        model_choice = gr.Dropdown(
                            choices=list(config["api"]["models"].keys()),
                            value="DeepSeek-V3",
                            label="选择模型"
                        )
                        
                        update_api_btn = gr.Button("更新API设置")
                        
                        with gr.Tabs() as reference_tabs:
                            with gr.TabItem("参考文档"):
                                gr.Markdown("## 参考文档 (理论/学术/指导性文档)")
                                reference_docs = gr.File(
                                    label="上传参考文档（可多选）",
                                    file_count="multiple",
                                    type="binary"
                                )
                                
                                process_docs_btn = gr.Button("处理参考文档")
                                
                            with gr.TabItem("参考文章"):
                                gr.Markdown("## 参考文章 (优质文学/风格样本)")
                                reference_article_text = gr.Textbox(
                                    label="输入参考文章",
                                    lines=10,
                                    placeholder="请在此输入参考文章内容..."
                                )
                                
                                process_articles_btn = gr.Button("处理参考文章")
                        
                        ref_status = gr.Textbox(label="处理状态", placeholder="尚未处理参考资料")
                        
                        gr.Markdown("## 风格分析")
                        style_analysis = gr.Textbox(label="参考资料风格分析", lines=5, placeholder="处理参考资料后将显示风格分析")
                        
                        gr.Markdown("## 机械用语过滤")
                        mechanical_words = gr.Textbox(
                            label="机械用语（每行一个）",
                            lines=5,
                            placeholder="总而言之\n总之\n因此\n故而\n所以\n换句话说",
                            value="\n".join(config["mechanical_words"])
                        )
                        
                        update_words_btn = gr.Button("更新机械用语")
                        extract_words_btn = gr.Button("从文章中提取机械用语")
                        
                        rounds_slider = gr.Slider(
                            minimum=1,
                            maximum=5,
                            value=config["max_rounds"],
                            step=1,
                            label="对话轮次"
                        )
                        
                    with gr.Column(scale=2):
                        gr.Markdown("## 原始文章")
                        original_text = gr.Textbox(
                            label="待润色的文章",
                            lines=10,
                            placeholder="请输入需要润色的文章内容..."
                        )
                        
                        start_btn = gr.Button("开始润色", variant="primary")
                        next_round_btn = gr.Button("进行下一轮润色")
                        stop_btn = gr.Button("停止润色", variant="stop")
                        
                        # 进度显示
                        progress_html = gr.HTML(
                            value='<div style="width: 100%; height: 30px; background-color: #f3f3f3; border-radius: 5px; overflow: hidden; margin: 10px 0;">'
                                  '<div id="progress-bar" style="width: 0%; height: 100%; background-color: #4CAF50; text-align: center; line-height: 30px; color: white;">0%</div>'
                                  '</div>'
                        )
                        
                        gr.Markdown("## 对话过程")
                        conversation_display = gr.HTML(
                            label="Agent对话过程",
                            value="<div style='padding: 20px; background-color: #f8f9fa; border-radius: 10px;'><p>对话将在此处显示...</p></div>"
                        )
                        
                        gr.Markdown("## 最终润色结果")
                        final_text = gr.Textbox(
                            label="润色后的文章",
                            lines=10,
                            placeholder="润色完成后将显示最终结果"
                        )
                        
                        stats = gr.Textbox(label="文章统计", value="原文字数: 0 | 润色后字数: 0")
        
        # 检查API密钥状态并更新警告
        def check_api_key():
            current_config = load_config()
            api_key = current_config["api"]["deepseek_key"]
            should_show_warning = not api_key
            
            # 如果不需要显示警告，返回空HTML
            if not should_show_warning:
                return gr.update(visible=False)
            else:
                return gr.update(visible=True)
        
        # 初始化后检查API密钥
        api_warning.update(check_api_key)
        
        # 格式化对话HTML
        def format_conversation_html(round_data):
            """
            格式化对话结果为HTML显示
            
            参数:
                round_data: 轮次数据
                
            返回:
                格式化的HTML字符串
            """
            html = f"<h3>第 {round_data['round']} 轮对话结果</h3>"
            
            for response in round_data["responses"]:
                agent_name = response["agent_name"]
                agent_color = response["agent_color"]
                content = response["content"]
                
                html += f"""
                <div class="agent-response {agent_color}-bg">
                    <div class="agent-name">{agent_name}</div>
                    <div>{content}</div>
                </div>
                """
            
            return html
        
        # 初始化Agent响应回调函数
        def on_agent_response(data):
            """
            处理来自Agent的响应更新
            
            参数:
                data: 包含agent_name, content等的字典
            
            返回:
                更新后的HTML字符串
            """
            nonlocal agent_responses, processing_agents, polishing_status
            
            # 提取数据
            agent_name = data["agent_name"]
            agent_color = data["agent_color"]
            content = data["content"]
            is_chunk = data.get("is_chunk", False)
            is_error = data.get("is_error", False)
            
            # 更新Agent状态
            if agent_name not in agent_responses:
                agent_responses[agent_name] = {
                    "color": agent_color,
                    "content": "",
                    "completed": False,
                    "error": False
                }
            
            # 更新内容
            if is_chunk:
                agent_responses[agent_name]["content"] += content
            else:
                agent_responses[agent_name]["content"] = content
                agent_responses[agent_name]["completed"] = True
            
            # 标记错误
            if is_error:
                agent_responses[agent_name]["error"] = True
                agent_responses[agent_name]["completed"] = True
            
            # 处理完成后从进行中列表中移除
            if agent_responses[agent_name]["completed"] and agent_name in processing_agents:
                processing_agents.remove(agent_name)
            
            # 生成HTML
            html = generate_agent_progress_html()
            
            # 计算进度百分比
            progress_percentage = calculate_progress_percentage()
            progress_html = update_progress_bar(progress_percentage)
            
            # 如果所有Agent都完成了，更新状态
            if len(processing_agents) == 0 and polishing_status == "running":
                polishing_status = "completed"
            
            # 返回更新后的HTML和进度条
            return html, progress_html
        
        def generate_agent_progress_html():
            """
            生成实时的Agent进度HTML
            
            返回:
                HTML字符串
            """
            html = "<h3>当前润色进度</h3>"
            
            # 添加已响应的Agent
            for agent_name, data in agent_responses.items():
                color = data["color"]
                content = data["content"]
                completed = data["completed"]
                is_error = data["error"]
                
                # 生成状态指示器
                status_indicator = ""
                if not completed:
                    status_indicator = '<div class="loading-spinner"></div>'
                
                # 错误样式
                extra_class = " error-bg" if is_error else ""
                
                html += f"""
                <div class="agent-response {color}-bg{extra_class}">
                    <div class="agent-name">{agent_name} {status_indicator}</div>
                    <div>{content}</div>
                </div>
                """
            
            # 添加等待中的Agent
            for agent_name in processing_agents:
                if agent_name not in agent_responses:
                    html += f"""
                    <div class="agent-response" style="background-color: #f8f9fa; border-left: 5px solid #6c757d;">
                        <div class="agent-name">{agent_name} <div class="loading-spinner"></div></div>
                        <div>正在生成响应...</div>
                    </div>
                    """
            
            return html
        
        def calculate_progress_percentage():
            """
            计算当前进度百分比
            
            返回:
                进度百分比 (0-100)
            """
            total_agents = len(engine.conversation.agents)
            if total_agents == 0:
                return 0
            
            completed_agents = sum(1 for data in agent_responses.values() if data["completed"])
            percentage = min(100, int((completed_agents / total_agents) * 100))
            
            return percentage
        
        def update_progress_bar(percentage):
            """
            更新进度条HTML
            
            参数:
                percentage: 进度百分比 (0-100)
                
            返回:
                更新后的HTML字符串
            """
            return f'<div style="width: 100%; height: 30px; background-color: #f3f3f3; border-radius: 5px; overflow: hidden; margin: 10px 0;">' \
                   f'<div id="progress-bar" style="width: {percentage}%; height: 100%; background-color: #4CAF50; text-align: center; line-height: 30px; color: white;">{percentage}%</div>' \
                   f'</div>'
        
        # 启动润色流程
        def start_polishing(text, max_rounds, style_analysis_text):
            """
            开始润色流程
            
            参数:
                text: 原始文本
                max_rounds: 最大轮次
                style_analysis_text: 风格分析文本
                
            返回:
                状态信息，对话HTML，进度HTML，更新是否完成
            """
            nonlocal agent_responses, processing_agents, polishing_status
            
            # 检查API密钥
            current_config = load_config()
            api_key = current_config["api"]["deepseek_key"]
            
            if not api_key:
                error_html = "<div style='padding: 15px; background-color: #ffebee; border-left: 5px solid #f44336; margin-bottom: 15px;'>" \
                             "<div style='font-weight: bold; color: #d32f2f; margin-bottom: 5px;'>错误: 未设置API密钥</div>" \
                             "<div>请在左侧面板中填写DeepSeek API密钥并点击'更新API设置'按钮。</div>" \
                             "</div>"
                
                return "错误: 未设置API密钥", error_html, update_progress_bar(0), "", "原文字数: 0 | 润色后字数: 0", None
            
            if not text.strip():
                error_html = "<div style='padding: 15px; background-color: #ffebee; border-left: 5px solid #f44336; margin-bottom: 15px;'>" \
                             "<div style='font-weight: bold; color: #d32f2f; margin-bottom: 5px;'>错误: 文章内容为空</div>" \
                             "<div>请输入需要润色的文章内容。</div>" \
                             "</div>"
                
                return "错误: 文章内容为空", error_html, update_progress_bar(0), "", "原文字数: 0 | 润色后字数: 0", None
            
            # 重置引擎和状态变量
            engine.reset()
            
            # 如果有风格分析结果，将其传递给引擎
            if style_analysis_text and style_analysis_text.strip():
                print(f"📋 使用用户提供的风格分析: {len(style_analysis_text)} 字符")
                
                # 更新参考文章或文档中的风格分析
                if engine.reference_articles:
                    engine.reference_articles["style_analysis"] = style_analysis_text
                elif engine.reference_docs:
                    engine.reference_docs["style_analysis"] = style_analysis_text
                else:
                    # 如果没有参考资料，创建一个临时的参考
                    engine.reference_articles = {
                        "content": text,
                        "style_analysis": style_analysis_text,
                        "ref_type": "custom"
                    }
            
            agent_responses = {}
            processing_agents = [agent.name for agent in engine.conversation.agents]
            polishing_status = "running"
            
            # 注册回调函数
            engine.register_agent_callback(lambda data: (
                gr.update(value=on_agent_response(data)[0]),  # 更新对话显示
                gr.update(value=on_agent_response(data)[1])   # 更新进度条
            ))
            
            # 启动润色流程
            try:
                # 在后台线程中启动润色，不阻塞UI
                import threading
                
                # 定义一个全局变量来保存最终结果
                global final_result_data 
                final_result_data = {
                    "status": "running",
                    "final_content": "",
                    "stats_text": "",
                    "conversation_html": "",
                    "progress": 0,
                    "error": None
                }
                
                def run_polishing():
                    global final_result_data
                    try:
                        # 开始润色流程
                        result = engine.start_polishing(text, max_rounds)
                        
                        # 处理完成后更新结果数据
                        if result["success"]:
                            # 获取最终结果
                            final_result = engine.conversation.generate_final_text()
                            final_text_value = final_result.get("final_text", "")
                            
                            # 从最终结果中提取润色后的文章内容
                            if "# 最终润色结果" in final_text_value:
                                parts = final_text_value.split("# 最终润色结果")
                                if len(parts) > 1:
                                    final_content = parts[1].strip()
                                else:
                                    final_content = final_text_value
                            else:
                                final_content = final_text_value
                            
                            # 计算统计信息
                            original_count = count_words(text)
                            final_count = count_words(final_content)
                            stats_text = f"原文字数: {original_count} | 润色后字数: {final_count}"
                            
                            # 更新结果数据
                            final_result_data = {
                                "status": "completed",
                                "final_content": final_content,
                                "stats_text": stats_text,
                                "conversation_html": f"<div style='padding: 20px; background-color: #f8f9fa; border-radius: 10px;'><p>润色已完成!</p></div>",
                                "progress": 100,
                                "error": None
                            }
                            
                            print("✅ 润色完成，已保存最终结果")
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"❌ 润色过程出错: {str(e)}")
                        
                        # 更新错误信息
                        final_result_data = {
                            "status": "error",
                            "final_content": "",
                            "stats_text": "",
                            "conversation_html": f"<div style='padding: 15px; background-color: #ffebee; border-left: 5px solid #f44336; margin-bottom: 15px;'>" \
                                                 f"<div style='font-weight: bold; color: #d32f2f; margin-bottom: 5px;'>润色过程出错</div>" \
                                                 f"<div>{str(e)}</div>" \
                                                 f"</div>",
                            "progress": 0,
                            "error": str(e)
                        }
                
                # 启动后台线程
                thread = threading.Thread(target=run_polishing)
                thread.daemon = True
                thread.start()
                
                # 返回初始状态
                initial_html = generate_agent_progress_html()
                
                return (
                    "润色进行中...",
                    initial_html,
                    update_progress_bar(0),
                    "",
                    f"原文字数: {count_words(text)} | 润色后字数: 0",
                    None  # 返回初始的polishing_result
                )
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                
                error_html = f"<div style='padding: 15px; background-color: #ffebee; border-left: 5px solid #f44336; margin-bottom: 15px;'>" \
                             f"<div style='font-weight: bold; color: #d32f2f; margin-bottom: 5px;'>错误</div>" \
                             f"<div>{str(e)}</div>" \
                             f"</div>"
                
                polishing_status = "error"
                
                return f"启动润色出错: {str(e)}", error_html, update_progress_bar(0), "", "原文字数: 0 | 润色后字数: 0", None
        
        # 检查润色状态的函数
        def check_polishing_status():
            """
            定期检查润色状态，更新UI
            
            返回:
                状态信息，对话HTML，进度HTML，最终文本，统计信息
            """
            global final_result_data
            
            try:
                # 如果没有结果数据，返回None
                if not final_result_data:
                    return None, None, None, None, None
                
                # 如果正在运行中，返回None
                if final_result_data.get("status") == "running":
                    return None, None, None, None, None
                
                # 如果已完成或出错，返回结果
                if final_result_data.get("status") == "completed" or final_result_data.get("status") == "error":
                    return (
                        "润色完成" if final_result_data.get("status") == "completed" else f"错误: {final_result_data.get('error')}",
                        final_result_data.get("conversation_html", ""),
                        update_progress_bar(final_result_data.get("progress", 0)),
                        final_result_data.get("final_content", ""),
                        final_result_data.get("stats_text", "")
                    )
                
                # 默认返回None
                return None, None, None, None, None
            except Exception as e:
                print(f"检查润色状态时出错: {str(e)}")
                return None, None, None, None, None
        
        # 事件绑定
        start_btn.click(
            start_polishing,
            inputs=[original_text, rounds_slider, style_analysis],
            outputs=[ref_status, conversation_display, progress_html, final_text, stats, polishing_result]
        )
        
        # 添加一个定时器，定期检查润色状态
        demo.load(
            check_polishing_status,
            inputs=None,
            outputs=[ref_status, conversation_display, progress_html, final_text, stats],
            every=3  # 每3秒检查一次
        )
        
        # 更新API设置
        def update_api_config(api_key_value, model_name):
            if not api_key_value.strip():
                return "请输入有效的API密钥", gr.update(visible=True)
                
            try:
                # 获取当前配置
                current_config = load_config()
                
                # 更新API配置
                current_config["api"]["deepseek_key"] = api_key_value
                current_config["api"]["model"] = current_config["api"]["models"][model_name]
                
                # 保存配置
                from config import save_config
                save_config(current_config)
                
                # 重新初始化引擎
                nonlocal engine
                engine = Engine()
                
                # 隐藏警告
                return f"API设置已更新，当前使用模型: {model_name}", gr.update(visible=False)
            except Exception as e:
                return f"更新API设置时出错: {str(e)}", gr.update(visible=True)
        
        update_api_btn.click(
            update_api_config,
            inputs=[api_key, model_choice],
            outputs=[ref_status, api_warning]
        )
        
        # 处理参考文档
        def process_reference_docs(files):
            if not files:
                return "请先上传参考文档", "处理失败"
            
            file_paths = []
            # 保存上传的文件
            for file in files:
                file_path = save_upload_file(file, os.path.basename(file.name))
                file_paths.append(file_path)
            
            # 处理参考文档
            result = engine.process_reference_documents(file_paths, "document")
            
            if result["success"]:
                return (
                    f"成功处理 {len(files)} 个参考文档",
                    result.get("style_analysis", "无法提取风格特征")
                )
            else:
                return (result["message"], "处理失败")
        
        process_docs_btn.click(
            process_reference_docs,
            inputs=[reference_docs],
            outputs=[ref_status, style_analysis]
        )
        
        # 处理参考文章
        def process_reference_articles(article_text):
            if not article_text.strip():
                return "请先输入参考文章内容", "处理失败"
            
            # 直接处理文本内容
            result = engine.process_reference_text(article_text, "article")
            
            if result["success"]:
                return (
                    "成功处理参考文章",
                    result.get("style_analysis", "无法提取风格特征")
                )
            else:
                return (result["message"], "处理失败")
        
        process_articles_btn.click(
            process_reference_articles,
            inputs=[reference_article_text],
            outputs=[ref_status, style_analysis]
        )
        
        # 更新机械用语
        def update_mechanical_words(words_text):
            words_list = [w.strip() for w in words_text.split("\n") if w.strip()]
            result = engine.update_mechanical_words(words_list)
            
            if result["success"]:
                return result["message"]
            else:
                return result["message"]
        
        update_words_btn.click(
            update_mechanical_words,
            inputs=[mechanical_words],
            outputs=[ref_status]
        )
        
        # 从文章中提取机械用语
        def extract_mechanical_words(text):
            if not text.strip():
                return "请先输入文章内容"
            
            result = engine.extract_mechanical_words(text)
            
            if result["success"]:
                words = result.get("mechanical_words", [])
                return "\n".join(words)
            else:
                return result["message"]
        
        extract_words_btn.click(
            extract_mechanical_words,
            inputs=[original_text],
            outputs=[mechanical_words]
        )
        
        # 进行下一轮润色
        def next_polishing_round():
            nonlocal agent_responses, processing_agents, polishing_status
            
            # 重置状态
            agent_responses = {}
            processing_agents = [agent.name for agent in engine.conversation.agents]
            polishing_status = "running"
            
            result = engine.next_round()
            
            if not result["success"]:
                return result["message"], "<p>进行下一轮润色时出现错误</p>", update_progress_bar(0), "", ""
            
            # 更新进度
            progress = engine.get_progress()
            progress_value = progress["progress_percentage"]
            
            if result.get("is_final", False):
                # 最终结果
                final_result = result.get("final_result", {})
                final_text_content = final_result.get("final_text", "")
                
                # 显示完整对话历史
                history = final_result.get("history", [])
                complete_html = ""
                for round_data in history:
                    complete_html += format_conversation_html(round_data)
                
                # 计算统计信息
                original_count = count_words(engine.original_text)
                final_count = count_words(final_text_content)
                stats_text = f"原文字数: {original_count} | 润色后字数: {final_count}"
                
                return (
                    "润色完成！",
                    complete_html,
                    update_progress_bar(100),
                    final_text_content,
                    stats_text
                )
            else:
                # 中间轮次
                round_result = result.get("result", {})
                
                # 返回初始状态，让callback更新界面
                initial_html = generate_agent_progress_html()
                
                return (
                    f"开始第 {round_result.get('round', '?')} 轮润色",
                    initial_html,
                    update_progress_bar(0),
                    "",
                    ""
                )
        
        next_round_btn.click(
            next_polishing_round,
            inputs=[],
            outputs=[ref_status, conversation_display, progress_html, final_text, stats]
        )
        
        # 停止润色
        def stop_polishing():
            nonlocal polishing_status
            polishing_status = "stopped"
            return "已停止润色流程", update_progress_bar(0)
        
        stop_btn.click(
            stop_polishing,
            inputs=[],
            outputs=[ref_status, progress_html]
        )
        
    return demo 