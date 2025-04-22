#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import glob

def compile_events():
    """编译所有事件到一个文件"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 确定events文件夹路径
    events_dir = os.path.join(current_dir, "events")
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(current_dir), "game", "static", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "all_events.json")
    
    # 初始化事件结构
    all_events = {
        "stage1": {"male": [], "female": []},
        "stage2": {"male": [], "female": []},
        "stage3": {"male": [], "female": []}
    }
    
    print(f"正在从 {events_dir} 读取事件文件...")
    
    # 遍历每个阶段目录
    for stage in range(1, 4):
        stage_key = f"stage{stage}"
        stage_dir = os.path.join(events_dir, stage_key)
        
        if not os.path.exists(stage_dir):
            print(f"警告: {stage_dir} 目录不存在，已跳过")
            continue
        
        # 遍历每个角色目录
        for character in ["male", "female"]:
            character_dir = os.path.join(stage_dir, character)
            
            if not os.path.exists(character_dir):
                print(f"警告: {character_dir} 目录不存在，已跳过")
                continue
            
            # 查找所有事件文件
            event_files = glob.glob(os.path.join(character_dir, "*.json"))
            print(f"在 {character_dir} 中找到 {len(event_files)} 个事件文件")
            
            for event_file in event_files:
                try:
                    with open(event_file, 'r', encoding='utf-8') as f:
                        event = json.load(f)
                        all_events[stage_key][character].append(event)
                        print(f"已添加事件: {event_file}")
                except Exception as e:
                    print(f"错误: 无法加载事件文件 {event_file}: {e}")
    
    # 保存到输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, ensure_ascii=False, indent=2)
        print(f"所有事件已编译到 {output_file}")
    except Exception as e:
        print(f"错误: 无法保存编译文件 {output_file}: {e}")
        
    # 统计每个阶段每个角色的事件数量
    for stage_key, stage_data in all_events.items():
        for character, events in stage_data.items():
            print(f"{stage_key} - {character}: {len(events)} 个事件")

if __name__ == "__main__":
    compile_events() 