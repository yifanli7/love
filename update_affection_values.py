import os
import json

def update_stage_events(stage_dir, increase_range, decrease_range):
    """
    更新指定阶段目录下所有事件文件中的好感度数值
    
    increase_range: (min_increase, max_increase) 增加好感度的范围
    decrease_range: (min_decrease, max_decrease) 减少好感度的范围
    """
    print(f"更新阶段目录: {stage_dir}")
    
    for gender in ['male', 'female']:
        gender_dir = os.path.join(stage_dir, gender)
        print(f"检查性别目录: {gender_dir}")
        
        if not os.path.exists(gender_dir):
            print(f"目录不存在: {gender_dir}")
            continue
            
        for filename in os.listdir(gender_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(gender_dir, filename)
            print(f"处理文件: {file_path}")
            
            # 读取事件文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
                
                # 修改每个选项的好感度数值
                modified = False
                for option in event_data['options']:
                    effects = option['effects']
                    
                    # 男性角色的好感度
                    original_male = effects['male']['affection']
                    if effects['male']['affection'] > 0:
                        effects['male']['affection'] = max(increase_range[0], min(increase_range[1], effects['male']['affection']))
                        if original_male != effects['male']['affection']:
                            modified = True
                    elif effects['male']['affection'] < 0:
                        effects['male']['affection'] = max(decrease_range[0], min(decrease_range[1], effects['male']['affection']))
                        if original_male != effects['male']['affection']:
                            modified = True
                    
                    # 女性角色的好感度
                    original_female = effects['female']['affection']
                    if effects['female']['affection'] > 0:
                        effects['female']['affection'] = max(increase_range[0], min(increase_range[1], effects['female']['affection']))
                        if original_female != effects['female']['affection']:
                            modified = True
                    elif effects['female']['affection'] < 0:
                        effects['female']['affection'] = max(decrease_range[0], min(decrease_range[1], effects['female']['affection']))
                        if original_female != effects['female']['affection']:
                            modified = True
                
                # 保存修改后的事件文件
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(event_data, f, ensure_ascii=False, indent=2)
                    print(f"已更新 {file_path}")
                else:
                    print(f"无需更新 {file_path}")
                    
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")

# 根据用户要求设置各阶段的好感度变化范围
# 第一阶段：好感度增加和减少量都大
# 第二阶段：好感度增加量较小，减少量较大
# 第三阶段：好感度增加量较小，减少量较少

# 获取事件目录的根路径
events_root = os.path.join(os.getcwd(), "event", "events")
print(f"事件根目录: {events_root}")

# 第一阶段：好感度增加和减少量都大
stage1_dir = os.path.join(events_root, "stage1")
update_stage_events(stage1_dir, (5, 10), (-8, -5))  # 增加5-10，减少5-8

# 第二阶段：好感度增加量较小，减少量较大
stage2_dir = os.path.join(events_root, "stage2")
update_stage_events(stage2_dir, (2, 4), (-10, -6))  # 增加2-4，减少6-10

# 第三阶段：好感度增加量较小，减少量较少
stage3_dir = os.path.join(events_root, "stage3")
update_stage_events(stage3_dir, (2, 5), (-3, -1))  # 增加2-5，减少1-3

print("所有事件文件的好感度数值更新完成！") 