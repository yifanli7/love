from openai import OpenAI
import json

# 初始化OpenAI客户端（使用阿里云DeepSeek API）
api_key = "sk-c15d06213b87484dbc9003d144f74e08"
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def generate_love_story(game_state):
    """
    根据游戏状态生成爱情故事
    """
    # 提取角色名称
    male_name = game_state["male"]["name"]
    female_name = game_state["female"]["name"]
    
    # 提取关系状态
    relationship = game_state["relationship"]
    
    # 提取属性值
    male_money = game_state["male"]["money"]
    male_affection = game_state["male"]["affection"]
    male_health = game_state["male"]["health"]
    
    female_money = game_state["female"]["money"]
    female_affection = game_state["female"]["affection"]
    female_health = game_state["female"]["health"]
    
    # 提取事件历史
    events = game_state["events_happened"]
    
    # 构建事件描述
    events_text = ""
    for event in events:
        character = male_name if event["character"] == "male" else female_name
        events_text += f"- {character}遇到了"{event['title']}"，选择了"{event['option_chosen']}"\n"
    
    # 构建爱情状态描述
    status_text = f"现在{male_name}和{female_name}是{relationship}关系。\n"
    status_text += f"{male_name}的属性：金钱 {male_money}，好感度 {male_affection}，健康度 {male_health}\n"
    status_text += f"{female_name}的属性：金钱 {female_money}，好感度 {female_affection}，健康度 {female_health}\n"
    
    # 确定当前阶段
    stage = game_state["stage"] - 1  # 因为显示故事时，阶段已经+1了
    stage_text = ""
    if stage == 1:
        stage_text = "他们从陌生人变成了朋友"
    elif stage == 2:
        stage_text = "他们从朋友变成了恋人"
    elif stage == 3:
        stage_text = "他们从恋人变成了夫妻"
    
    # 构建提示
    prompt = f"""
作为一个爱情故事作家，请根据以下信息为我创作一个浪漫、生动的短篇爱情故事，长度控制在500字以内：

主角：{male_name}（男）和{female_name}（女）
当前关系：{relationship}
关系变化：{stage_text}

主要事件：
{events_text}

当前状态：
{status_text}

请根据上述情节创作一个连贯、浪漫的爱情故事，描述这对主角是如何相识、相知，以及他们关系发展的过程。
故事应该包含情感变化，高潮转折，以及与他们属性（金钱、好感度、健康度）相关的细节。
请确保故事流畅、有趣，并与上述事件保持一致。
"""

    try:
        # 调用DeepSeek API生成故事
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用DeepSeek的模型
            messages=[
                {"role": "system", "content": "你是一个专业的爱情故事作家，擅长创作浪漫、感人的故事。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # 提取生成的故事
        story = response.choices[0].message.content
        return story
    except Exception as e:
        print(f"生成故事时出错: {e}")
        return f"无法生成故事，请稍后再试。错误信息: {str(e)}" 