# LiteraSageAI

这是一个基于多Agent协同工作的文学润色系统，专为提升文学文章的质量和表现力而设计。系统利用DeepSeek API，通过5个提示词驱动Agent的多轮对话，不断优化和提升文章质量。

## 功能特点

- **多Agent协同**：5个不同专业方向的Agent共同分析和润色文章
- **多轮对话**：Agent之间进行多轮对话，不断改进润色效果
- **参考文档分析**：能够分析参考文档的风格特点，作为润色参考
- **机械用语过滤**：自动识别和替换常见的机械用语，使文章更加自然流畅
- **直观界面**：基于Gradio构建的友好用户界面，操作简单直观

## 系统架构

系统由以下几个核心模块组成：

1. **Agent模块**：实现5个不同专业Agent角色
2. **交互引擎**：控制Agent之间的对话流程和文章润色过程
3. **文档处理模块**：负责处理用户上传的参考文档和待润色文章
4. **界面模块**：基于Gradio构建的用户交互界面
5. **配置管理**：处理系统配置，如机械用语词库等

## Agent角色介绍

系统包含5个专业Agent，各自关注文章润色的不同方面：

- **文学专家**：专注于文学性、修辞手法和格调，提升文章的文学价值和艺术性
- **语言优化师**：专注于语法、词汇选择和句式优化，提高语言表达的准确性和多样性
- **结构分析师**：专注于文章结构、段落组织和逻辑连贯性，优化文章的整体结构和逻辑流
- **风格塑造师**：专注于文体风格、语调和情感表达，塑造特定的文章风格和调性
- **综合评审员**：负责整合各个专家的建议并做最终决策，平衡各方观点形成最优方案
##  程序运行展示
-![效果1.png](https://img.picui.cn/free/2025/03/20/67dafe82e3790.png)
-![效果2.png](https://img.picui.cn/free/2025/03/20/67dafe8295b25.png)

##  优化后的文本展示（Ｖ３模型）

- **晨光中，铁门的金属光泽流转，如同凝固的时间长河，折射出工业文明的冷峻与岁月的无情。锈迹盘桓如时光的泪痕，在阳光下泛着冷光，每一道裂痕都在诉说着机械时代的沧桑。田埂上，农药瓶列队如残兵，塑料壳相撞的闷响，是土地最后的挽歌，惊飞了栖息其上的鹧鸪，也惊醒了沉睡的乡愁。这些沉默的容器整齐排列，瓶身斑驳，标签褪色，仿佛在等待工业文明对自然的最后审判。

新生儿的啼哭划破黎明的寂静，如希望之剑刺穿工业文明的阴霾，在太平间的阴影中绽放生命的光芒。医院的走廊里，啼哭与车轮声交织成生命的二重奏，一者宣告开始，一者见证终结，却都在诉说着生命的永恒。洁白的墙壁映照着新生儿的红润，冰冷的太平间回荡着车轮的沉重，生命的无常与永恒在此刻达成微妙的平衡，恰如阴阳两极的永恒流转。

铁门的絮语低沉而缓慢，农药瓶的闷响急促而断续，二者在时间的维度上交织，谱写出工业文明的变奏曲。声纹如量子波动般在月光下舒展，每一道频率都是生命的密码，每一圈涟漪都是时间的印记。铁门的锈迹、农药瓶的沉默、新生儿的啼哭、太平间的车轮声，所有这些意象在月光下交织，形成一幅跨越时空的生命画卷，恰似“人生代代无穷已，江月年年只相似”的永恒咏叹。

月光如水，流淌在工业文明的废墟与生命的绿洲之间。声纹在时空中延展，如年轮般层层叠叠，每一圈都是生命的刻度，每一道都是时光的刻痕。在这幅跨越时空的生命画卷中，工业文明的沉重与生命的希望交织，时间的无情与永恒的追求共鸣，共同谱写出一曲关于文明、生命与时间的永恒交响。而那道声纹，仍在月光下舒展，如同生命本身，永远在终结中开始，在消逝中永恒。
**

## 安装与使用

### 环境要求

- Python 3.8+
- DeepSeek API密钥
- 必要的Python包（见`requirements.txt`）

### 安装步骤

1. 克隆本仓库：
   ```
   git clone https://github.com/Xialiang98/LiteraSageAI.git
   cd LiteraSageAI
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置DeepSeek API密钥：
   在`config.py`中设置您的API密钥，或者通过环境变量设置。

### 使用方法

1. 启动系统：
   ```
   python main.py
   ```

2. 在浏览器中打开Gradio界面（默认地址：http://127.0.0.1:7860）

3. 使用步骤：
   - 上传参考文档（可选）
   - 输入需要润色的文章
   - 设置对话轮次和其他选项
   - 点击"开始润色"
   - 查看Agent对话过程和最终润色结果

## 技术细节

- **API调用**：使用DeepSeek API进行自然语言处理
- **多Agent实现**：基于角色提示工程实现不同专业方向的Agent
- **对话管理**：自动管理多轮对话，保持上下文连贯性
- **异步处理**：支持异步处理多个请求，提高系统响应速度
- **文本分析**：使用NLP技术分析文档风格特征和机械用语

## 开发者指南

### 项目结构

- `main.py` - 程序入口
- `agents.py` - Agent类定义和实现
- `engine.py` - 交互引擎核心逻辑
- `document_processor.py` - 文档处理模块
- `conversation.py` - 对话管理模块
- `interface.py` - Gradio界面实现
- `config.py` - 配置管理模块
- `models.py` - 数据模型定义
- `utils.py` - 工具函数集合
- `README.md` - 项目说明文档

### 自定义扩展

- **添加新Agent**：在`agents.py`中创建新的Agent子类，并在`create_agents`函数中注册
- **修改提示词**：调整各Agent的`_create_prompt`方法可以优化提示词
- **界面定制**：在`interface.py`中可以调整Gradio界面布局和功能

##　下一步开发计划

- **MCP Server**：准备接入MCP Server，让其拥有爬取对应文种写作手法并学习的能力。
- **外挂写作知识库**：让接入的模型能学习到更多的有关写作知识，纠正部分ＡＩ用词

  
## 许可证

本项目采用MIT许可证。详见LICENSE文件。 
