from openai import OpenAI
import json
import os
import time
import concurrent.futures
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import traceback

# 从环境变量获取API密钥
api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-c15d06213b87484dbc9003d144f74e08")
# 模型名称
model_name = os.environ.get("DASHSCOPE_MODEL", "qwen-turbo")  # 阿里云百炼模型

# 在Vercel环境中使用简化的超时设置
VERCEL_TIMEOUT = 8.0  # Vercel函数有10秒的执行限制，我们设置为8秒以增加成功率
DEFAULT_TIMEOUT = 30.0  # 非Vercel环境中使用更长的超时时间
STAGE3_TIMEOUT = 60.0  # 第三阶段使用更长的超时时间

# 全局客户端
global_client = None

# 获取或创建OpenAI客户端
def get_client():
    global global_client
    if global_client is None:
        global_client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    return global_client

# 判断是否在Vercel环境中运行
def is_vercel_env() -> bool:
    """检查是否在Vercel环境中运行"""
    return os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None

# 故事生成功能的回退方案
def generate_fallback_story(
    male_name: str, 
    female_name: str, 
    stage: int, 
    relationship: str,
    events: List[Dict]
) -> str:
    """生成后备故事，当API调用失败时使用
    
    Args:
        male_name: 男主角名字
        female_name: 女主角名字
        stage: 当前游戏阶段
        relationship: 角色关系状态
        events: 事件列表
        
    Returns:
        生成的简单故事文本
    """
    logging.info("使用后备故事生成方法")
    
    # 根据当前阶段生成简单的故事模板
    stage_templates = {
        1: f"{male_name}和{female_name}初次相遇，他们开始了解彼此，建立了初步的联系。",
        2: f"{male_name}和{female_name}在共同经历中逐渐熟悉，关系逐渐加深。",
        3: f"{male_name}和{female_name}的关系面临一些挑战，但他们试图共同解决问题。"
    }
    
    # 获取当前阶段的基本故事
    base_story = stage_templates.get(stage, f"{male_name}和{female_name}继续他们的故事。")
    
    # 添加事件描述
    event_descriptions = []
    for event in events:
        if isinstance(event, dict) and 'description' in event:
            event_descriptions.append(event['description'])
    
    events_text = ""
    if event_descriptions:
        events_text = "\n\n在这个阶段中，发生了以下事件：\n" + "\n".join([f"- {desc}" for desc in event_descriptions])
    
    # 根据关系状态添加结尾
    endings = {
        "陌生人": f"目前，{male_name}和{female_name}还只是普通的认识关系，他们之间的故事才刚刚开始。",
        "朋友": f"{male_name}和{female_name}已经成为了好朋友，他们享受彼此的陪伴，期待着未来的发展。",
        "恋人": f"{male_name}和{female_name}已经确认了彼此的感情，他们的爱情故事正在甜蜜地发展着。"
    }
    
    ending = endings.get(relationship, f"{male_name}和{female_name}继续着他们的故事。")
    
    # 组合完整故事
    full_story = f"{base_story}{events_text}\n\n{ending}"
    
    return full_story

# 添加API调用优化函数
def api_call_with_timeout(messages: List[Dict[str, str]], timeout: Optional[int] = None) -> Optional[str]:
    """
    使用超时控制安全地调用API
    
    Args:
        messages: 消息列表
        timeout: 超时时间(秒)，如果为None则根据环境和阶段自动设置
        
    Returns:
        生成的内容或None(如果调用失败)
    """
    start_time = time.time()
    
    # 确定是否是第三阶段(通过检查消息内容)
    is_third_stage = any("从恋人关系迈入婚姻" in msg.get("content", "") 
                         for msg in messages if msg.get("role") == "user")
    
    # 如果未指定超时，根据环境和阶段设置默认值
    if timeout is None:
        # Vercel环境下使用更短的超时
        if is_vercel_env():
            timeout = 15 if not is_third_stage else 20
        else:
            timeout = 20 if not is_third_stage else 30
    
    print(f"使用超时设置: {timeout}秒")
    
    # 使用线程池执行器来处理超时
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 提交API调用任务
        future = executor.submit(_call_api, messages)
        try:
            # 等待结果，设置超时
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"API调用超时(超过{timeout}秒)")
            return None
        except Exception as e:
            print(f"API调用执行错误: {e}")
            return None

def _call_api(messages: List[Dict[str, str]]) -> Optional[str]:
    """
    实际执行API调用
    
    Args:
        messages: 消息列表
        
    Returns:
        生成的内容或None(如果调用失败)
    """
    start_time = time.time()
    client = get_client()
    
    try:
        # 调用API
        response = client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,  # 固定token限制
            top_p=0.8,
            frequency_penalty=0.5
        )
        
        # 处理响应
        end_time = time.time()
        content = response.choices[0].message.content
        
        # 计算token使用量
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        print(f"API调用成功，耗时: {end_time - start_time:.2f}秒")
        print(f"Token使用: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")
        
        return content
    except Exception as e:
        end_time = time.time()
        print(f"API调用失败: {e}, 耗时: {end_time - start_time:.2f}秒")
        return None

# 处理故事内容，确保生成完整可读的故事
def process_story_content(content: str, male_name: str, female_name: str) -> str:
    """
    处理故事内容，替换可能的占位符，清理特殊字符
    
    Args:
        content: 原始故事内容
        male_name: 男主角名字
        female_name: 女主角名字
        
    Returns:
        处理后的故事内容
    """
    if not content:
        return content
    
    # 替换可能的占位符（A和B, 男主和女主等）
    replacements = {
        "A": male_name,
        "B": female_name,
        "男主": male_name,
        "女主": female_name,
        "男主角": male_name,
        "女主角": female_name,
        "[男主]": male_name,
        "[女主]": female_name,
        "{男主}": male_name,
        "{女主}": female_name
    }
    
    for placeholder, name in replacements.items():
        content = content.replace(placeholder, name)
    
    # 移除特殊非中文标点符号
    special_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]
    for char in special_chars:
        content = content.replace(char, "")
    
    # 移除故事阶段标记和其他不需要的格式
    content = content.replace("【第1阶段的故事】", "").replace("【第2阶段的故事】", "").replace("【第3阶段的故事】", "")
    content = content.replace("【第一阶段的故事】", "").replace("【第二阶段的故事】", "").replace("【第三阶段的故事】", "")
    
    # 确保段落之间有适当的间隔
    content = content.replace("\n\n\n", "\n\n").strip()
    
    return content

def generate_love_story(game_state: Dict[str, Any], forget_previous_content: bool = False) -> str:
    """生成爱情故事
    
    Args:
        game_state: 游戏状态
        forget_previous_content: 是否忘记之前的内容
        
    Returns:
        生成的爱情故事
    """
    start_time = time.time()
    
    # 检查游戏状态是否有效
    if not game_state:
        logging.error("游戏状态无效")
        return "游戏状态无效，无法生成故事。"
    
    # 提取角色信息
    male_info = extract_character_info(game_state, "male")
    female_info = extract_character_info(game_state, "female")
    
    male_name = male_info["name"]
    female_name = female_info["name"]
    
    # 计算平均好感度
    avg_affection = (male_info["affection"] + female_info["affection"]) / 2
    relationship_status = get_relationship_status(avg_affection)
    
    logging.info(f"生成爱情故事 - 阶段: {game_state.get('stage', 1)}, 关系: {relationship_status}, "
                f"男方好感度: {male_info['affection']}, 女方好感度: {female_info['affection']}")
    
    # 获取事件
    events = get_current_stage_events(game_state) if forget_previous_content else get_all_events(game_state)
    
    # 根据关系状态设置严格的情节约束
    relationship_constraints = {
        "陌生人": "双方刚认识或偶遇，情节应严格限制在初次接触的好奇、礼貌交谈或试探性了解，绝对不可出现亲密互动、告白、约会等超前情节",
        "朋友": "双方处于友谊阶段，可以有日常交往、互相帮助、轻微暧昧，但绝对不能出现表白、亲吻、牵手等亲密行为，更不能出现求婚、同居、结婚等严重超前的情节",
        "恋人": "双方已确认恋爱关系，可以有浪漫约会、情感表达和适度的亲密互动，但不应出现求婚、结婚、同居等超前情节"
    }
    
    current_constraints = relationship_constraints.get(relationship_status, "请根据当前关系状态合理设定情节")
    
    # 构建系统提示词
    system_prompt = f"""你是一位优秀的言情小说作家，擅长创作晋江风格的言情故事。请根据以下信息创作一个引人入胜的爱情故事章节。

故事要求：
1. 严格遵循晋江言情小说的写作风格，包括：细腻的心理描写、恰到好处的对白、浪漫且略带戏剧性的情节发展
2. 故事中必须包含男女主角之间微妙的情感变化和心理活动
3. 根据两位主角的属性（金钱、健康、好感度）适当调整故事情节
4. 男主角名字：{male_name}，女主角名字：{female_name}
5. 【极其重要】他们当前的关系是：{relationship_status}
6. 【关系约束】{current_constraints}
7. 故事必须基于已发生的游戏事件，不要编造新事件
8. 字数控制在700字以内
9. 文风富有感染力，语言优美且富有节奏感
10. 故事情节要符合逻辑，人物性格要前后一致
11. 不要在故事结尾添加"【完】"或任何结束标记
12. 不要在故事结尾添加总结段落或创作感想

当前阶段：{game_state.get('stage', 1)}
当前关系：{relationship_status}

违禁情节清单：
- 如果关系是"陌生人"：禁止出现任何亲密行为、表白、约会等超前情节
- 如果关系是"朋友"：禁止出现表白、亲吻、牵手、求婚、同居、结婚等超前情节
- 如果关系是"恋人"：禁止出现求婚、同居、结婚等超前情节，除非特别指示
"""

    # 构建用户提示词
    user_prompt = f"""男主角 {male_name} 的属性：金钱 {male_info['money']}，健康 {male_info['health']}，好感度 {male_info['affection']}
女主角 {female_name} 的属性：金钱 {female_info['money']}，健康 {female_info['health']}，好感度 {female_info['affection']}

当前关系状态：{relationship_status}（请严格遵循这一关系状态，不要出现不符合关系阶段的情节）

已发生的事件：
"""
    
    # 添加事件描述
    for i, event in enumerate(events):
        if isinstance(event, dict):
            character = event.get("character", "未知")
            option = event.get("option", "未知")
            effects = event.get("effects", {})
            stage = event.get("stage", "未知")
            
            user_prompt += f"事件{i+1}（阶段{stage}）：{character}选择了\"{option}\"，";
            
            effect_descriptions = []
            for attr, value in effects.items():
                if attr in ["money", "health", "affection"]:
                    direction = "增加" if value > 0 else "减少"
                    effect_descriptions.append(f"{attr} {direction} {abs(value)}")
            
            if effect_descriptions:
                user_prompt += "导致" + "，".join(effect_descriptions)
            
            user_prompt += "。\n"
    
    user_prompt += f"""
请根据以上信息创作一个引人入胜的爱情故事章节，遵循晋江风格的言情小说写作特点。
请特别关注两位主角之间的情感发展和微妙变化。
故事必须基于已发生的事件，不要添加未在事件中提及的新情节。
字数控制在700字以内。
再次强调，故事情节必须严格符合"{relationship_status}"的关系状态，不要出现超前的情节发展。
"""
    
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="qwen-max",  # 使用阿里云模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=2000,
        )
        story = response.choices[0].message.content
        
        # 记录成功信息
        elapsed_time = time.time() - start_time
        logging.info(f"成功生成故事，耗时 {elapsed_time:.2f} 秒，字数约 {len(story)} 字")
        
        return story
    except Exception as e:
        logging.error(f"生成故事时出错: {str(e)}")
        return generate_fallback_story(
            male_name=male_name,
            female_name=female_name,
            stage=game_state.get("stage", 1),
            relationship=relationship_status,
            events=events
        )

def get_relationship_status(avg_affection: float) -> str:
    """根据平均好感度获取关系状态
    
    Args:
        avg_affection: 平均好感度
        
    Returns:
        关系状态: "陌生人", "朋友" 或 "恋人"
    """
    if avg_affection < 3:
        return "陌生人"
    elif avg_affection < 7:
        return "朋友"
    else:
        return "恋人"

def generate_bad_ending_story(game_state: Dict[str, Any]) -> str:
    """为游戏结束生成一个不好的结局故事
    
    Args:
        game_state: 游戏状态
        
    Returns:
        生成的坏结局故事
    """
    start_time = time.time()
    
    # 提取角色信息
    male_info = extract_character_info(game_state, "male")
    female_info = extract_character_info(game_state, "female")
    
    male_name = male_info["name"]
    female_name = female_info["name"]
    
    # 计算平均好感度
    avg_affection = (male_info["affection"] + female_info["affection"]) / 2
    relationship_status = get_relationship_status(avg_affection)
    
    # 确定失败原因
    failure_reason = ""
    failure_detail = ""
    if male_info["health"] <= 0:
        failure_reason = "健康问题"
        failure_detail = f"{male_name}的健康状况恶化"
    elif female_info["health"] <= 0:
        failure_reason = "健康问题"
        failure_detail = f"{female_name}的健康状况恶化"
    elif male_info["money"] <= 0:
        failure_reason = "经济压力"
        failure_detail = f"{male_name}的经济状况陷入困境"
    elif female_info["money"] <= 0:
        failure_reason = "经济压力"
        failure_detail = f"{female_name}的经济状况陷入困境"
    elif avg_affection <= 0:
        failure_reason = "感情破裂"
        failure_detail = "双方感情不和，关系无法维系"
    else:
        failure_reason = "多种因素"
        failure_detail = "多种因素导致关系无法继续"
    
    logging.info(f"生成坏结局故事 - 关系: {relationship_status}, 失败原因: {failure_reason}, 详情: {failure_detail}")
    
    # 获取所有事件
    events = get_all_events(game_state)
    
    # 构建系统消息
    system_message = f"""你是一位擅长创作浪漫爱情小说的AI，需要根据给定的场景和角色创作具有晋江言情小说风格的爱情故事的结局。你的任务是根据提供的游戏事件和角色情况，生成一个以"{failure_reason}"为核心的遗憾结局。

故事要求：
1. 严格使用晋江言情小说的写作风格，包括：细腻的心理描写、恰到好处的对白、略带忧伤的结局氛围
2. 故事需基于提供的事件和角色信息，不要编造与给定信息不符的情节
3. 男女主角的名字固定为{male_name}和{female_name}
4. 故事必须将"{failure_reason}"作为失败的核心原因，具体表现为：{failure_detail}
5. 故事情节必须与当前关系状态"{relationship_status}"相符合：
   - 如果是陌生人：结局体现初步认识后无法继续发展的遗憾
   - 如果是朋友：结局体现友情无法升华为爱情的遗憾
   - 如果是恋人：结局体现恋爱关系面临危机或分手的痛苦
   - 如果是夫妻：结局体现婚姻关系中的困境或挑战
6. 字数控制在700字以内
7. 根据当前关系（{relationship_status}）调整故事的情感基调
8. 表现人物的细腻情感变化和心理活动，让读者感受到角色之间的情感互动
9. 提供生动的场景描写，让故事更有画面感和代入感
10. 使用符合当代年轻人的语言风格，要优美又不做作
11. 确保故事情节符合逻辑，人物行为符合其性格特点
12. 故事是遗憾的，但可以留下一丝希望或成长的意味
13. 不要在故事结尾添加"【完】"或任何结束标记
14. 不要在故事结尾添加总结段落或创作感想

当前阶段：{game_state.get('stage', 1)}（注意：游戏只有3个阶段）
当前关系：{relationship_status}
失败原因：{failure_detail}"""

    # 构建用户消息
    user_message = f"""男主角 {male_name} 的属性：金钱 {male_info['money']}，健康 {male_info['health']}，好感度 {male_info['affection']}
女主角 {female_name} 的属性：金钱 {female_info['money']}，健康 {female_info['health']}，好感度 {female_info['affection']}

请根据以下事件创作一个以"{failure_reason}"为核心原因的遗憾爱情故事结局：
"""

    # 添加事件描述
    for i, event in enumerate(events):
        if isinstance(event, dict):
            character = event.get("character", "未知")
            option = event.get("option", "未知")
            effects = event.get("effects", {})
            stage = event.get("stage", "未知")
            
            user_message += f"事件{i+1}（阶段{stage}）：{character}选择了\"{option}\"，";
            
            effect_descriptions = []
            for attr, value in effects.items():
                if attr in ["money", "health", "affection"]:
                    direction = "增加" if value > 0 else "减少"
                    effect_descriptions.append(f"{attr} {direction} {abs(value)}")
            
            if effect_descriptions:
                user_message += "导致" + "，".join(effect_descriptions)
            
            user_message += "。\n"
    
    user_message += f"""
请根据以上信息创作一个遗憾的爱情故事结局，遵循晋江风格的言情小说写作特点。
重点描述{failure_detail}如何导致他们的故事结束。
故事字数控制在700字以内。
"""
    
    # 调用API获取故事
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="qwen-max",  # 使用阿里云模型
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        story = response.choices[0].message.content
        
        # 记录成功信息
        elapsed_time = time.time() - start_time
        logging.info(f"成功生成坏结局故事，耗时 {elapsed_time:.2f} 秒，字数约 {len(story)} 字")
        
        return story
    except Exception as e:
        logging.error(f"生成坏结局故事时出错: {e}")
        return generate_fallback_story(
            male_name=male_name,
            female_name=female_name,
            stage=game_state.get("stage", 1),
            relationship=relationship_status,
            events=events
        )

def generate_ongoing_story(game_state: Dict[str, Any], forget_previous_content: bool = False) -> str:
    """生成一个进行中的爱情故事
    
    Args:
        game_state: 游戏状态
        forget_previous_content: 是否忽略之前的故事内容
        
    Returns:
        生成的故事内容
    """
    start_time = time.time()
    
    # 提取角色信息
    male_info = extract_character_info(game_state, "male")
    female_info = extract_character_info(game_state, "female")
    
    male_name = male_info["name"]
    female_name = female_info["name"]
    
    # 计算平均好感度
    avg_affection = (male_info["affection"] + female_info["affection"]) / 2
    relationship_status = get_relationship_status(avg_affection)
    
    current_stage = game_state.get("stage", 1)
    logging.info(f"生成进行中的故事 - 阶段: {current_stage}, 关系: {relationship_status}")
    
    # 获取当前阶段的事件
    current_stage_events = []
    for event in game_state.get("events", []):
        if isinstance(event, dict) and event.get("stage") == current_stage:
            current_stage_events.append(event)
    
    # 获取之前的故事内容
    previous_story = game_state.get("story", "")
    
    # 获取阶段描述
    stage_description = ""
    if current_stage == 1:
        stage_description = "初识阶段 - 初次相遇"
    elif current_stage == 2:
        stage_description = "熟悉阶段 - 相互了解，建立友谊"
    elif current_stage == 3:
        stage_description = "恋爱阶段 - 感情升温，确认关系"
    
    # 根据关系状态设置严格的情节约束
    relationship_constraints = {
        "陌生人": "双方刚认识或偶遇，情节应限制在初次接触的好奇、礼貌交谈或试探性了解，不可出现亲密互动、告白、约会等超前情节",
        "朋友": "双方处于友谊阶段，可以有日常交往、互相帮助、轻微暧昧，但绝对不能出现表白、亲吻、牵手等亲密行为，更不能出现求婚、同居、结婚等严重超前的情节",
        "恋人": "双方已确认恋爱关系，可以有浪漫约会、情感表达和适度的亲密互动，但不应出现求婚、结婚、同居等超前情节"
    }
    
    current_constraints = relationship_constraints.get(relationship_status, "请根据当前关系状态合理设定情节")
    
    # 构建系统消息
    system_message = f"""你是一位擅长创作浪漫爱情小说的AI，需要根据给定的场景和角色创作具有晋江言情小说风格的爱情故事。每个故事都是一段恋爱关系中的重要时刻。

故事要求：
1. 严格使用晋江言情小说的写作风格，包括：细腻的心理描写、恰到好处的对白、优美的场景描写
2. 根据给定的游戏事件和角色属性创作故事
3. 男女主角的名字固定为{male_name}和{female_name}
4. 【非常重要】故事必须严格遵循当前的关系状态：{relationship_status}
5. 【关系约束】{current_constraints}
6. 字数控制在700字以内
7. 故事要有情感深度，展现人物内心世界
8. 提供生动的场景描写，让故事更有画面感
9. 使用符合当代年轻人的语言风格，优美又不做作
10. 确保故事情节符合逻辑，人物行为符合其性格特点
11. 故事应该积极向上，充满希望
12. 不要在故事结尾添加"【完】"或任何结束标记
13. 不要在故事结尾添加总结段落或创作感想

当前阶段：{current_stage} - {stage_description}
当前关系：{relationship_status}

违禁情节：
- 如果关系是"陌生人"：禁止出现任何亲密行为、表白、约会等超前情节
- 如果关系是"朋友"：禁止出现表白、亲吻、牵手、求婚、同居、结婚等超前情节
- 如果关系是"恋人"：禁止出现求婚、同居、结婚等超前情节，除非特别指示"""

    # 构建用户消息
    user_message = f"""男主角 {male_name} 的属性：金钱 {male_info['money']}，健康 {male_info['health']}，好感度 {male_info['affection']}
女主角 {female_name} 的属性：金钱 {female_info['money']}，健康 {female_info['health']}，好感度 {female_info['affection']}

当前关系：{relationship_status}（请严格遵循这一关系状态创作情节，不要出现超前发展的情节）

"""

    # 添加当前阶段事件
    if current_stage_events:
        user_message += "本阶段发生的事件：\n"
        for i, event in enumerate(current_stage_events):
            if isinstance(event, dict):
                character = event.get("character", "未知")
                option = event.get("option", "未知")
                effects = event.get("effects", {})
                
                user_message += f"事件{i+1}：{character}选择了\"{option}\"，";
                
                effect_descriptions = []
                for attr, value in effects.items():
                    if attr in ["money", "health", "affection"]:
                        direction = "增加" if value > 0 else "减少"
                        effect_descriptions.append(f"{attr} {direction} {abs(value)}")
                
                if effect_descriptions:
                    user_message += "导致" + "，".join(effect_descriptions)
                
                user_message += "。\n"
    else:
        user_message += f"当前阶段还没有发生具体事件，请基于{male_name}和{female_name}处于{relationship_status}关系的背景创作故事。\n"
    
    # 添加之前的故事内容
    if previous_story and not forget_previous_content:
        user_message += f"\n之前的故事内容：\n{previous_story}\n\n请继续之前的故事，创作新的内容。记住，严格遵循关系状态为{relationship_status}的情节限制。"
    else:
        user_message += f"\n请根据以上信息创作一个全新的爱情故事，遵循晋江风格的言情小说写作特点。\n故事字数控制在700字以内。严格确保情节与{relationship_status}的关系状态相符。"
    
    # 调用API获取故事
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="qwen-max",  # 使用阿里云模型
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        story = response.choices[0].message.content
        
        # 记录成功信息
        elapsed_time = time.time() - start_time
        logging.info(f"成功生成进行中的故事，耗时 {elapsed_time:.2f} 秒，字数约 {len(story)} 字")
        
        return story
    except Exception as e:
        logging.error(f"生成进行中的故事时出错: {e}")
        return generate_fallback_story(
            male_name=male_name,
            female_name=female_name,
            stage=current_stage,
            relationship=relationship_status,
            events=current_stage_events
        )

def format_events_for_prompt(events: List[Dict[str, Any]], male_name: str, female_name: str) -> str:
    """格式化事件列表为提示文本

    Args:
        events: 事件列表
        male_name: 男性角色名称
        female_name: 女性角色名称

    Returns:
        格式化后的事件文本
    """
    if not events:
        return ""
    
    formatted_events = []
    for i, event in enumerate(events):
        player = event.get("player")
        player_name = male_name if player == "male" else female_name
        option = event.get("option", {})
        option_desc = option.get("description", "未知选项")
        formatted_event = f"{i+1}. {player_name}选择了：{option_desc}"
        
        # 添加属性变化
        effects = option.get("effects", {})
        effect_texts = []
        for attr, value in effects.items():
            if value != 0:
                change = "增加" if value > 0 else "减少"
                effect_texts.append(f"{attr} {change} {abs(value)}")
        
        if effect_texts:
            formatted_event += f"，导致{', '.join(effect_texts)}"
        
        formatted_events.append(formatted_event)
    
    return "\n".join(formatted_events)

def get_stage_description(stage: int) -> str:
    """获取阶段描述

    Args:
        stage: 游戏阶段

    Returns:
        阶段描述文本
    """
    stage_descriptions = {
        1: "初次相识",
        2: "相知相熟",
        3: "浪漫约会",
        4: "情感升温",
        5: "共同生活",
    }
    return stage_descriptions.get(stage, f"第{stage}阶段")

def get_stage_events(game_state: Dict[str, Any], stage: int) -> List[Dict[str, Any]]:
    """从游戏状态中提取指定阶段的事件
    
    Args:
        game_state: 游戏状态字典
        stage: 要提取的阶段编号
        
    Returns:
        该阶段的事件列表
    """
    events = game_state.get("events", [])
    return [event for event in events if event.get("stage") == stage]

def build_system_prompt(current_stage: int, relationship: str) -> str:
    """构建系统提示词
    
    Args:
        current_stage: 当前游戏阶段
        relationship: 当前关系状态
        
    Returns:
        系统提示词
    """
    stage_desc = {
        1: "初识阶段",
        2: "互相了解培养感情阶段",
        3: "确认关系发展恋情阶段"
    }.get(current_stage, "未知阶段")
    
    # 根据关系状态设置严格的情节约束
    relationship_constraints = {
        "陌生人": "双方刚认识或偶遇，情节应严格限制在初次接触的好奇、礼貌交谈或试探性了解，绝对不可出现亲密互动、告白、约会等超前情节",
        "朋友": "双方处于友谊阶段，可以有日常交往、互相帮助、轻微暧昧，但绝对不能出现表白、亲吻、牵手等亲密行为，更不能出现求婚、同居、结婚等严重超前的情节",
        "恋人": "双方已确认恋爱关系，可以有浪漫约会、情感表达和适度的亲密互动，但不应出现求婚、结婚、同居等超前情节"
    }
    
    current_constraints = relationship_constraints.get(relationship, "请根据当前关系状态合理设定情节")
    
    system_prompt = f"""你是一位专业的言情小说作家，擅长写爱情故事。
请根据用户提供的情境，以晋江言情小说风格，写一段精彩的爱情故事片段。
当前处于{stage_desc}，主角关系是{relationship}。

要求：
1. 故事要符合真实的恋爱发展过程
2. 【极其重要】故事情节必须严格符合当前关系状态：{relationship}
3. 【关系约束】{current_constraints}
4. 使用优美细腻的文笔，有细节描写和心理活动
5. 根据男女主角的属性状态合理安排剧情
6. 故事要有起承转合，情节连贯且有感情发展
7. 根据提供的事件列表，按时间顺序合理展开故事
8. 故事篇幅控制在700字以内
9. 以第三人称视角描写，语言活泼自然，符合年轻人表达方式
10. 不要出现任何超出现实的情节
11. 不要在故事结尾添加"【完】"或任何结束标记
12. 不要在故事结尾添加总结段落或创作感想

违禁情节清单：
- 如果关系是"陌生人"：禁止出现任何亲密行为、表白、约会等超前情节
- 如果关系是"朋友"：禁止出现表白、亲吻、牵手、求婚、同居、结婚等超前情节
- 如果关系是"恋人"：禁止出现求婚、同居、结婚等超前情节，除非特别指示
"""
    return system_prompt

def build_user_prompt(
    male_name: str, female_name: str,
    male_money: int, male_affection: int, male_health: int,
    female_money: int, female_affection: int, female_health: int,
    current_stage: int, relationship: str, events: List[Dict[str, Any]]
) -> str:
    """构建用户提示词
    
    Args:
        male_name: 男主角名字
        female_name: 女主角名字
        male_money/affection/health: 男主角属性
        female_money/affection/health: 女主角属性
        current_stage: 当前游戏阶段
        relationship: 当前关系状态
        events: 事件列表
        
    Returns:
        用户提示词
    """
    stage_desc = {
        1: "初识阶段",
        2: "互相了解培养感情阶段",
        3: "确认关系发展恋情阶段"
    }.get(current_stage, "未知阶段")
    
    # 角色信息
    user_prompt = f"""请根据以下信息，创作一段爱情故事片段：

【角色信息】
男主角：{male_name}（金钱:{male_money}，好感度:{male_affection}，健康值:{male_health}）
女主角：{female_name}（金钱:{female_money}，好感度:{female_affection}，健康值:{female_health}）
当前阶段：{stage_desc}
当前关系：{relationship}

【事件列表】
"""
    
    # 添加事件
    if events:
        for i, event in enumerate(events, 1):
            event_desc = event.get("description", "未知事件")
            event_turn = "男主角" if event.get("turn") == "male" else "女主角"
            event_choice = event.get("choice_description", "未知选择")
            user_prompt += f"{i}. {event_turn}遇到：{event_desc}，选择了：{event_choice}\n"
    else:
        user_prompt += "暂无事件发生\n"
    
    user_prompt += "\n请根据以上信息，创作一个情节连贯、有感情发展的爱情故事片段。"
    
    return user_prompt

def generate_bad_ending(game_state: Dict[str, Any]) -> str:
    """生成游戏失败结局
    
    Args:
        game_state: 游戏状态
        
    Returns:
        失败结局故事
    """
    return generate_bad_ending_story(game_state)

def get_events_for_stage(game_state: Dict[str, Any], stage: int) -> List[Dict[str, Any]]:
    """获取特定阶段的事件
    
    Args:
        game_state: 游戏状态
        stage: 要获取事件的阶段
        
    Returns:
        该阶段的事件列表
    """
    events = game_state.get("events", [])
    return [event for event in events if event.get("stage", 1) == stage]

def extract_character_info(game_state: Dict[str, Any], character_type: str) -> Dict[str, Any]:
    """提取角色信息
    
    Args:
        game_state: 游戏状态
        character_type: 角色类型，"male"或"female"
        
    Returns:
        包含角色信息的字典
    """
    character = game_state.get(character_type, {})
    return {
        "name": character.get("name", "男主角" if character_type == "male" else "女主角"),
        "money": character.get("money", 5),
        "health": character.get("health", 5),
        "affection": character.get("affection", 5)
    }

def get_current_stage_events(game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """获取当前阶段的事件
    
    Args:
        game_state: 游戏状态
        
    Returns:
        当前阶段的事件列表
    """
    current_stage = game_state.get("stage", 1)
    # 首先尝试使用events_happened键
    all_events = game_state.get("events_happened", [])
    if not all_events:
        # 如果没有，回退到使用events键
        all_events = game_state.get("events", [])
    
    current_stage_events = []
    
    for event in all_events:
        if isinstance(event, dict) and event.get("stage") == current_stage:
            # 创建符合story_generator期望格式的事件对象
            formatted_event = {
                "stage": event.get("stage", current_stage),
                "character": event.get("character", "未知"),
                "option": event.get("option_chosen", event.get("option", "未知选择")),
                "effects": event.get("effects", {})
            }
            current_stage_events.append(formatted_event)
    
    logging.info(f"获取当前阶段 {current_stage} 的事件, 共 {len(current_stage_events)} 个")
    return current_stage_events

def get_all_events(game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """获取所有阶段的事件
    
    Args:
        game_state: 游戏状态
        
    Returns:
        所有事件列表
    """
    # 首先尝试使用events_happened键
    all_events = game_state.get("events_happened", [])
    if not all_events:
        # 如果没有，回退到使用events键
        all_events = game_state.get("events", [])
    
    formatted_events = []
    for event in all_events:
        if isinstance(event, dict):
            # 创建符合story_generator期望格式的事件对象
            formatted_event = {
                "stage": event.get("stage", 1),
                "character": event.get("character", "未知"),
                "option": event.get("option_chosen", event.get("option", "未知选择")),
                "effects": event.get("effects", {})
            }
            formatted_events.append(formatted_event)
    
    logging.info(f"获取所有事件, 共 {len(formatted_events)} 个")
    return formatted_events 