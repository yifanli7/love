from flask import Flask, render_template, request, jsonify, session, make_response
import json
import random
import os
from datetime import datetime
import secrets

# 获取当前文件的目录
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 使用cookie存储游戏状态
def get_game_state():
    state_cookie = request.cookies.get('game_state')
    if state_cookie:
        try:
            return json.loads(state_cookie)
        except:
            return None
    return None

# 设置游戏状态到cookie
def set_game_state(response, game_state):
    response.set_cookie('game_state', json.dumps(game_state), max_age=60*60*24*7)  # 7天过期
    return response

# 加载所有事件
def load_events():
    try:
        events_path = os.path.join(base_dir, 'static/data/all_events.json')
        with open(events_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果文件不存在，返回一个样例事件
        return {
            "stage1": {
                "male": [{"id": "sample", "title": "示例事件", "description": "这是一个示例事件", 
                         "options": [{"text": "选项1", "effects": {"male": {"money": 1, "affection": 1, "health": 1}, 
                                                            "female": {"money": 0, "affection": 1, "health": 0}}}]}],
                "female": []
            },
            "stage2": {"male": [], "female": []},
            "stage3": {"male": [], "female": []}
        }

# 游戏状态初始化
def init_game(male_name="A", female_name="B"):
    return {
        "male": {
            "name": male_name,
            "money": 40,
            "affection": 5,
            "health": 80
        },
        "female": {
            "name": female_name,
            "money": 40,
            "affection": 5,
            "health": 80
        },
        "stage": 1,
        "events_happened": [],
        "relationship": "陌生人",
        "current_turn": "male",
        "events_in_stage": 0
    }

# 检查游戏是否结束
def check_game_over(game_state):
    male = game_state["male"]
    female = game_state["female"]
    
    # 检查是否有属性小于0
    if male["money"] < 0:
        return True, f"{male['name']}的金钱不足"
    if male["affection"] < 0:
        return True, f"{male['name']}的好感度过低"
    if male["health"] < 0:
        return True, f"{male['name']}的健康度过低"
    if female["money"] < 0:
        return True, f"{female['name']}的金钱不足"
    if female["affection"] < 0:
        return True, f"{female['name']}的好感度过低"
    if female["health"] < 0:
        return True, f"{female['name']}的健康度过低"
    
    # 检查阶段性目标
    stage = game_state["stage"]
    if game_state["events_in_stage"] >= 10:  # 阶段结束
        if stage == 1:
            if male["money"] + female["money"] <= 15:
                return True, f"{male['name']}和{female['name']}的共同财富不足，未能发展为朋友关系"
            if male["affection"] <= 50 or female["affection"] <= 50:
                return True, f"双方好感度不够，未能发展为朋友关系"
            if male["health"] <= 80 or female["health"] <= 80:
                return True, f"健康状况不佳，未能发展为朋友关系"
        elif stage == 2:
            if male["money"] + female["money"] <= 30:
                return True, f"{male['name']}和{female['name']}的共同财富不足，未能发展为恋人关系"
            if male["affection"] <= 80 or female["affection"] <= 80:
                return True, f"双方好感度不够，未能发展为恋人关系"
            if male["health"] <= 80 or female["health"] <= 80:
                return True, f"健康状况不佳，未能发展为恋人关系"
        elif stage == 3:
            if male["money"] + female["money"] <= 50:
                return True, f"{male['name']}和{female['name']}的共同财富不足，未能步入婚姻"
            if male["affection"] <= 100 or female["affection"] <= 100:
                return True, f"双方好感度不够，未能步入婚姻"
            if male["health"] <= 80 or female["health"] <= 80:
                return True, f"健康状况不佳，未能步入婚姻"
    
    return False, ""

# 检查游戏是否胜利
def check_victory(game_state):
    male = game_state["male"]
    female = game_state["female"]
    
    if (male["affection"] > 150 and female["affection"] > 150 and
        male["health"] > 60 and female["health"] > 60 and
        male["money"] > 30 and female["money"] > 30 and
        game_state["relationship"] == "夫妻"):
        return True
    
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init', methods=['POST'])
def initialize_game():
    data = request.json
    male_name = data.get('male_name', 'A')
    female_name = data.get('female_name', 'B')
    
    if not male_name:
        male_name = 'A'
    if not female_name:
        female_name = 'B'
    
    game_state = init_game(male_name, female_name)
    
    response = make_response(jsonify({"status": "success", "game_state": game_state}))
    return set_game_state(response, game_state)

@app.route('/start_stage', methods=['POST'])
def start_stage():
    game_state = get_game_state()
    if not game_state:
        return jsonify({"status": "error", "message": "游戏未初始化"}), 400
    
    # 重置阶段事件计数
    game_state["events_in_stage"] = 0
    # 确保阶段开始时，由男性角色开始
    game_state["current_turn"] = "male"
    
    # 输出调试信息
    print(f"开始阶段 {game_state['stage']}，重置事件计数，当前角色设为 {game_state['current_turn']}")
    
    response = make_response(jsonify({"status": "success", "game_state": game_state}))
    return set_game_state(response, game_state)

@app.route('/get_event', methods=['GET'])
def get_event():
    game_state = get_game_state()
    if not game_state:
        return jsonify({"status": "error", "message": "游戏未初始化"}), 400
    
    all_events = load_events()
    stage = game_state["stage"]
    current_turn = game_state["current_turn"]
    
    # 获取当前阶段对应角色的事件
    stage_key = f"stage{stage}"
    
    # 检查当前阶段是否存在对应角色的事件
    if stage_key not in all_events or current_turn not in all_events[stage_key] or not all_events[stage_key][current_turn]:
        return jsonify({"status": "error", "message": f"没有可用的第{stage}阶段{current_turn}角色事件"}), 400
    
    events_pool = all_events[stage_key][current_turn]
    
    # 打印调试信息
    print(f"获取第{stage}阶段{current_turn}角色事件，事件池大小: {len(events_pool)}")
    
    # 移除已经发生过的特殊事件
    filtered_events = []
    for event in events_pool:
        event_id = event.get("id", "")
        if "special" in event and event.get("special", False):
            if event_id not in [e["id"] for e in game_state["events_happened"]]:
                filtered_events.append(event)
        else:
            filtered_events.append(event)
    
    if not filtered_events:
        return jsonify({"status": "error", "message": "没有可用事件"}), 400
    
    # 随机选择一个事件
    event = random.choice(filtered_events)
    
    return jsonify({"status": "success", "event": event})

@app.route('/choose_option', methods=['POST'])
def choose_option():
    game_state = get_game_state()
    if not game_state:
        return jsonify({"status": "error", "message": "游戏未初始化"}), 400
    
    data = request.json
    event_id = data.get('event_id')
    option_index = data.get('option_index')
    event = data.get('event')
    
    if not event or not isinstance(option_index, int) or option_index < 0 or option_index >= len(event.get('options', [])):
        return jsonify({"status": "error", "message": "无效的选项"}), 400
    
    # 应用选项效果
    option = event['options'][option_index]
    effects = option.get('effects', {})
    
    for character, changes in effects.items():
        for attribute, value in changes.items():
            game_state[character][attribute] += value
    
    # 记录事件
    game_state["events_happened"].append({
        "id": event_id,
        "title": event.get("title"),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "character": game_state["current_turn"],
        "option_chosen": option.get("text")
    })
    
    # 切换角色回合
    current_turn_before = game_state["current_turn"]
    game_state["current_turn"] = "female" if game_state["current_turn"] == "male" else "male"
    game_state["events_in_stage"] += 1
    
    # 输出调试信息
    print(f"事件完成：阶段 {game_state['stage']}，回合从 {current_turn_before} 切换到 {game_state['current_turn']}，阶段中的事件数：{game_state['events_in_stage']}")
    
    # 检查阶段是否完成
    stage_complete = False
    if game_state["events_in_stage"] >= 10:
        # 输出调试信息
        print(f"阶段 {game_state['stage']} 达到10个事件，进行判定")
        
        game_over, reason = check_game_over(game_state)
        if game_over:
            print(f"游戏结束原因: {reason}")
            return jsonify({
                "status": "game_over",
                "reason": reason,
                "game_state": game_state
            })
        
        # 升级关系
        if game_state["stage"] == 1:
            game_state["relationship"] = "朋友"
            print("关系升级为朋友")
        elif game_state["stage"] == 2:
            game_state["relationship"] = "恋人"
            print("关系升级为恋人")
        elif game_state["stage"] == 3:
            game_state["relationship"] = "夫妻"
            print("关系升级为夫妻")
            
            # 检查是否胜利
            if check_victory(game_state):
                print("游戏胜利")
                return jsonify({
                    "status": "victory",
                    "game_state": game_state
                })
        
        # 增加阶段
        game_state["stage"] += 1
        # 重置事件计数
        game_state["events_in_stage"] = 0
        # 重置当前回合为男性角色，以便在下一阶段开始时从男性角色开始
        game_state["current_turn"] = "male"
        stage_complete = True
        print(f"进入新阶段: {game_state['stage']}")
    else:
        # 检查属性是否小于0
        game_over, reason = check_game_over(game_state)
        if game_over:
            print(f"游戏提前结束: {reason}")
            return jsonify({
                "status": "game_over",
                "reason": reason,
                "game_state": game_state
            })
    
    response = make_response(jsonify({
        "status": "success",
        "game_state": game_state,
        "stage_complete": stage_complete
    }))
    return set_game_state(response, game_state)

@app.route('/reset_game', methods=['POST'])
def reset_game():
    response = make_response(jsonify({"status": "success"}))
    response.delete_cookie('game_state')
    return response

if __name__ == '__main__':
    # 确保静态数据目录存在
    data_dir = os.path.join(base_dir, 'static/data')
    os.makedirs(data_dir, exist_ok=True)
    app.run(debug=True, port=8080) 