#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import uuid
import argparse

# 默认事件模板
DEFAULT_EVENT = {
    "id": "",
    "title": "",
    "description": "",
    "special": False,
    "options": [
        {
            "text": "",
            "effects": {
                "male": {"money": 0, "affection": 0, "health": 0},
                "female": {"money": 0, "affection": 0, "health": 0}
            }
        },
        {
            "text": "",
            "effects": {
                "male": {"money": 0, "affection": 0, "health": 0},
                "female": {"money": 0, "affection": 0, "health": 0}
            }
        },
        {
            "text": "",
            "effects": {
                "male": {"money": 0, "affection": 0, "health": 0},
                "female": {"money": 0, "affection": 0, "health": 0}
            }
        }
    ]
}

def generate_event_id():
    """生成唯一的事件ID"""
    return str(uuid.uuid4())

def create_new_event(stage, character, special=False):
    """创建新事件"""
    event = DEFAULT_EVENT.copy()
    event["id"] = generate_event_id()
    event["special"] = special
    
    # 如果是特殊事件，修改模板
    if special:
        print(f"创建第{stage}阶段{character}角色的特殊事件")
    else:
        print(f"创建第{stage}阶段{character}角色的普通事件")
    
    # 获取事件标题
    event["title"] = input("请输入事件标题: ")
    
    # 获取事件描述
    event["description"] = input("请输入事件描述: ")
    
    # 获取选项和效果
    options = []
    for i in range(3):
        option = {
            "text": "",
            "effects": {
                "male": {"money": 0, "affection": 0, "health": 0},
                "female": {"money": 0, "affection": 0, "health": 0}
            }
        }
        
        print(f"\n选项 {i+1}:")
        option["text"] = input(f"请输入选项 {i+1} 文本: ")
        
        print("请输入选项对男性角色的影响:")
        option["effects"]["male"]["money"] = int(input("金钱变化: "))
        option["effects"]["male"]["affection"] = int(input("好感度变化: "))
        option["effects"]["male"]["health"] = int(input("健康度变化: "))
        
        print("请输入选项对女性角色的影响:")
        option["effects"]["female"]["money"] = int(input("金钱变化: "))
        option["effects"]["female"]["affection"] = int(input("好感度变化: "))
        option["effects"]["female"]["health"] = int(input("健康度变化: "))
        
        options.append(option)
    
    event["options"] = options
    
    return event

def save_event(event, stage, character):
    """保存事件到文件"""
    events_dir = os.path.join("event", "events")
    stage_dir = os.path.join(events_dir, f"stage{stage}")
    character_dir = os.path.join(stage_dir, character)
    
    # 确保目录存在
    os.makedirs(character_dir, exist_ok=True)
    
    # 生成文件名
    filename = f"{event['id']}.json"
    filepath = os.path.join(character_dir, filename)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(event, f, ensure_ascii=False, indent=2)
    
    print(f"事件已保存到 {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description='事件生成器')
    parser.add_argument('--stage', type=int, choices=[1, 2, 3], required=True, help='事件发生阶段')
    parser.add_argument('--character', type=str, choices=['male', 'female'], required=True, help='事件相关角色')
    parser.add_argument('--special', action='store_true', help='是否为特殊事件')
    
    args = parser.parse_args()
    
    # 创建并保存事件
    event = create_new_event(args.stage, args.character, args.special)
    save_event(event, args.stage, args.character)

if __name__ == "__main__":
    main() 