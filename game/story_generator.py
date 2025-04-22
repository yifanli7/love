from openai import OpenAI
import json
import os
import time
import concurrent.futures
from typing import Dict, Any, Optional

# 从环境变量获取API密钥
api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-c15d06213b87484dbc9003d144f74e08")

# 在Vercel环境中使用简化的超时设置
VERCEL_TIMEOUT = 5.0  # Vercel函数有10秒的执行限制，我们设置为5秒留出余量

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
def generate_fallback_story(male_name: str, female_name: str, relationship: str, stage: int) -> str:
    """
    当API调用失败时生成一个简单的故事
    
    Args:
        male_name: 男主角名字
        female_name: 女主角名字
        relationship: 当前关系
        stage: 当前阶段
        
    Returns:
        生成的故事文本
    """
    if stage == 1:  # 朋友阶段
        return f"{male_name}和{female_name}经过一系列的相遇和互动，从最初的陌生关系逐渐建立了信任。他们一起度过了许多美好时光，共同克服了一些小困难，这使他们的友谊更加牢固。现在，他们已经成为了彼此信赖的朋友，期待着未来有更多共同的经历和回忆。"
    elif stage == 2:  # 恋人阶段
        return f"随着时间的推移，{male_name}和{female_name}的友谊悄然发生了变化。他们开始期待每次见面，心跳也因对方的一个微笑而加速。在一次偶然的机会，{male_name}鼓起勇气表达了自己的心意，而{female_name}也回应了这份感情。如今，他们已经成为恋人，彼此的生活因对方而变得更加丰富多彩。"
    elif stage == 3:  # 夫妻阶段
        return f"在相恋一段时间后，{male_name}和{female_name}决定携手迈向人生的新阶段。他们经历了甜蜜的求婚，筹备了温馨的婚礼，最终在亲友的祝福中成为了夫妻。现在的他们，面对生活的挑战时更加坚定，因为知道无论发生什么，都有对方在身边相伴。这段婚姻是他们爱情故事的新篇章，而不是结束。"
    else:
        return f"{male_name}和{female_name}的故事正在继续发展，充满了无限可能。他们一起经历了许多事情，这些经历让他们更加了解彼此，也让他们的关系更进一步。无论未来如何，这段关系都将是他们人生中重要的一部分。"

# 安全的API调用函数
def api_call_with_timeout(messages: list, model: str = "deepseek-chat", timeout: float = VERCEL_TIMEOUT) -> Optional[str]:
    """
    安全地调用API，包含超时控制和错误处理
    
    Args:
        messages: 消息列表
        model: 模型名称
        timeout: 超时时间(秒)
        
    Returns:
        生成的文本，如果失败则返回None
    """
    def call_api():
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=400  # 减少token数量，加速生成
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"API调用内部错误: {e}")
            return None
    
    # 使用并发执行器和超时控制
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(call_api)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"API调用超时({timeout}秒)")
            return None
        except Exception as e:
            print(f"执行器异常: {e}")
            return None

def generate_love_story(game_state: Dict[str, Any]) -> str:
    """
    根据游戏状态生成爱情故事
    
    Args:
        game_state: 游戏状态字典
        
    Returns:
        生成的爱情故事文本
    """
    start_time = time.time()
    
    try:
        # 提取角色信息
        male_name = game_state["male"]["name"]
        female_name = game_state["female"]["name"]
        relationship = game_state["relationship"]
        
        # 提取属性值
        male_money = game_state["male"]["money"]
        male_affection = game_state["male"]["affection"]
        male_health = game_state["male"]["health"]
        
        female_money = game_state["female"]["money"]
        female_affection = game_state["female"]["affection"]
        female_health = game_state["female"]["health"]
        
        # 确定当前阶段
        stage = game_state["stage"] - 1  # 因为显示故事时，阶段已经+1了
        
        # 阶段对应的关系变化描述
        stage_descriptions = {
            1: f"他们从陌生人变成了朋友，建立了信任和友谊的纽带",
            2: f"他们从朋友关系发展为恋人，感情逐渐升温",
            3: f"他们从恋人关系迈入婚姻，开始人生新的篇章"
        }
        stage_text = stage_descriptions.get(stage, "他们的关系正在发展")
        
        # 检查是否在Vercel环境中，如果是则直接使用回退方案
        if is_vercel_env():
            print("在Vercel环境中使用预设故事模板")
            story = generate_fallback_story(male_name, female_name, relationship, stage)
            end_time = time.time()
            print(f"故事生成完成，总耗时: {end_time - start_time:.2f}秒")
            return story
        
        # 提取当前阶段的事件历史，确保只关注当前阶段的事件
        events = []
        for event in game_state.get("events_happened", []):
            # 筛选当前阶段的事件
            if len(events) < 10:  # 只考虑最近的10个事件，即当前阶段的事件
                events.append(event)
        
        # 构建事件描述，包含事件标题、选择和效果
        events_text = ""
        for event in events:
            character = male_name if event["character"] == "male" else female_name
            event_title = event.get("title", "某事件")
            event_option = event.get("option_chosen", "做出了选择")
            events_text += f"- {character}遇到了\"{event_title}\"，选择了\"{event_option}\"\n"
        
        # 为不同阶段设置不同的提示词模板
        stage_prompts = {
            1: f"""请创作一个关于{male_name}和{female_name}如何从陌生人变成朋友的故事。
故事应该反映出他们初次相识、相互了解并建立友谊的过程。
请着重描写他们共同经历的事件如何帮助他们建立信任，以及友情如何逐渐深厚。
故事应该温馨、有趣，展现友谊的珍贵。""",
            
            2: f"""请创作一个关于{male_name}和{female_name}从朋友发展为恋人的浪漫故事。
故事应该描写他们逐渐意识到对彼此的情感不仅仅是友情，以及他们如何跨越友谊与爱情的界限。
请包含一些感人的告白或特别的时刻，展现两人情感升温的过程。
故事应该充满浪漫气息，但也要符合他们之前建立的友谊基础。""",
            
            3: f"""请创作一个关于{male_name}和{female_name}从恋人转变为夫妻的温馨故事。
故事应该描述他们如何决定共度余生，包括求婚、婚礼筹备或新婚生活的甜蜜片段。
请强调他们如何一起规划未来，以及婚姻如何让他们的爱情更加坚固。
故事应该温暖、感人，展现成熟爱情和承诺的美好。"""
        }
        
        stage_prompt = stage_prompts.get(stage, f"请创作一个关于{male_name}和{female_name}关系发展的故事")
        
        # 构建系统和用户消息
        system_message = {"role": "system", "content": "你是一个专业的爱情故事作家，擅长创作浪漫、感人的故事。请根据提供的信息创作一个短篇爱情故事，确保故事与两位主角的属性和经历相符。"}
        
        user_content = f"""请根据以下信息为我创作一个浪漫、生动的短篇爱情故事，长度控制在300字以内：

主角：{male_name}（男）和{female_name}（女）
当前关系：{relationship}
关系变化：{stage_text}

{stage_prompt}

主要事件历史（请参考这些事件创作故事情节）：
{events_text}

当前属性（请将这些属性反映在故事中）：
{male_name}的属性：金钱 {male_money}，好感度 {male_affection}，健康度 {male_health}
{female_name}的属性：金钱 {female_money}，好感度 {female_affection}，健康度 {female_health}

重要提示：请确保故事是全新的，不要重复之前阶段的情节。根据当前阶段和关系创作独特的内容。
"""
        
        user_message = {"role": "user", "content": user_content}
        messages = [system_message, user_message]
        
        try:
            # 调用API生成故事，使用安全的调用方法
            story = api_call_with_timeout(messages)
            
            # 如果API调用失败，使用回退方案
            if not story:
                print("API调用未返回结果，使用回退方案")
                story = generate_fallback_story(male_name, female_name, relationship, stage)
            
            end_time = time.time()
            print(f"故事生成完成，总耗时: {end_time - start_time:.2f}秒")
            return story
            
        except Exception as api_error:
            print(f"API调用错误: {api_error}")
            return generate_fallback_story(male_name, female_name, relationship, stage)
            
    except Exception as e:
        end_time = time.time()
        print(f"故事生成过程中出现错误: {e}, 耗时: {end_time - start_time:.2f}秒")
        return "由于技术原因，无法生成故事。但这并不影响您的游戏体验，请继续游戏。" 