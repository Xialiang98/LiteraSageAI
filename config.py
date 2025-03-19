import os
import json

# DeepSeek API配置
DEEPSEEK_API_KEY = ""  # API密钥由用户提供，不硬编码
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"  # 使用DeepSeek-V3模型（通过deepseek-chat调用）

# 可用模型选项
MODELS = {
    "DeepSeek-V3": "deepseek-chat",
    "DeepSeek-R1": "deepseek-reasoner"
}

# Agent配置
DEFAULT_MAX_ROUNDS = 3  # 默认对话轮次
AGENTS = [
    {
        "name": "文学专家",
        "description": "专注于文学性、修辞手法和格调，擅长提升文章的文学价值和艺术性。",
        "color": "blue"
    },
    {
        "name": "语言优化师",
        "description": "专注于语法、词汇选择和句式优化，擅长提高语言表达的准确性和多样性。",
        "color": "green"
    },
    {
        "name": "结构分析师",
        "description": "专注于文章结构、段落组织和逻辑连贯性，擅长优化文章的整体结构和逻辑流。",
        "color": "orange"
    },
    {
        "name": "风格塑造师",
        "description": "专注于文体风格、语调和情感表达，擅长塑造特定的文章风格和调性。",
        "color": "purple"
    },
    {
        "name": "综合评审员",
        "description": "负责整合各个专家的建议并做最终决策，擅长平衡各方观点形成最优方案。",
        "color": "red"
    }
]

# 机械用语过滤词库（默认值，可通过界面添加）
DEFAULT_MECHANICAL_WORDS = [
    "总而言之", "总之", "因此", "故而", "所以", "换句话说",
    "诚然", "显而易见", "毫无疑问", "众所周知", "不言而喻",
    "事实上", "实际上", "客观上", "主观上", "可以说",
    "说到底", "归根结底", "说白了", "简而言之"
]

# 配置文件路径
CONFIG_FILE = "agent_config.json"

def load_config():
    """
    加载配置，如果配置文件不存在则创建默认配置
    """
    config = None
    need_save = False
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 检查配置是否完整，如果缺少某些字段，则添加默认值
            need_save = ensure_config_complete(config)
                
        except Exception as e:
            print(f"读取配置文件时出错: {str(e)}，将使用默认配置")
            config = None
    
    if config is None:
        # 默认配置
        config = {
            "api": {
                "deepseek_key": DEEPSEEK_API_KEY,
                "deepseek_base_url": DEEPSEEK_BASE_URL,
                "model": DEFAULT_MODEL,
                "models": MODELS
            },
            "agents": AGENTS,
            "max_rounds": DEFAULT_MAX_ROUNDS,
            "mechanical_words": DEFAULT_MECHANICAL_WORDS
        }
        need_save = True
    
    # 如果配置有更新，保存到文件
    if need_save:
        save_config(config)
        
    return config

def ensure_config_complete(config):
    """
    确保配置包含所有必要的字段，如果缺少则添加默认值
    
    参数:
        config: 当前配置
        
    返回:
        是否修改了配置
    """
    modified = False
    
    # 确保api字段存在
    if "api" not in config:
        config["api"] = {
            "deepseek_key": DEEPSEEK_API_KEY,
            "deepseek_base_url": DEEPSEEK_BASE_URL,
            "model": DEFAULT_MODEL,
            "models": MODELS
        }
        modified = True
    else:
        # 确保api下的必要字段存在
        api_config = config["api"]
        
        if "deepseek_key" not in api_config:
            api_config["deepseek_key"] = DEEPSEEK_API_KEY
            modified = True
            
        if "deepseek_base_url" not in api_config:
            api_config["deepseek_base_url"] = DEEPSEEK_BASE_URL
            modified = True
            
        if "model" not in api_config:
            api_config["model"] = DEFAULT_MODEL
            modified = True
            
        if "models" not in api_config:
            api_config["models"] = MODELS
            modified = True
    
    # 确保agents字段存在
    if "agents" not in config:
        config["agents"] = AGENTS
        modified = True
    
    # 确保max_rounds字段存在
    if "max_rounds" not in config:
        config["max_rounds"] = DEFAULT_MAX_ROUNDS
        modified = True
    
    # 确保mechanical_words字段存在
    if "mechanical_words" not in config:
        config["mechanical_words"] = DEFAULT_MECHANICAL_WORDS
        modified = True
    
    return modified

def save_config(config):
    """
    保存配置到文件
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存配置文件时出错: {str(e)}")
        return False

def update_mechanical_words(new_words):
    """
    更新机械用语列表
    """
    config = load_config()
    config["mechanical_words"] = new_words
    save_config(config)
    return {"success": True, "message": "成功更新机械用语列表"} 