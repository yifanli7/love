#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys

"""
游戏功能测试脚本
测试以下功能点：
1. 游戏初始化
2. 事件获取和选择
3. 阶段转换
4. 故事生成
"""

BASE_URL = "http://localhost:8080"
session = requests.Session()

def log(message):
    """日志输出"""
    print(f"[TEST] {message}")
    sys.stdout.flush()  # 确保日志立即显示

def test_init_game():
    """测试游戏初始化"""
    log("测试游戏初始化...")
    response = session.post(f"{BASE_URL}/init", json={
        "male_name": "测试男",
        "female_name": "测试女"
    })
    
    if response.status_code != 200:
        log(f"初始化失败，状态码: {response.status_code}")
        return False
    
    data = response.json()
    if data["status"] != "success":
        log(f"初始化失败，错误信息: {data.get('message', '未知错误')}")
        return False
    
    game_state = data["game_state"]
    log(f"游戏初始化成功: {game_state['male']['name']} 和 {game_state['female']['name']}")
    return True

def test_start_stage():
    """测试开始阶段"""
    log("测试开始阶段...")
    response = session.post(f"{BASE_URL}/start_stage")
    
    if response.status_code != 200:
        log(f"开始阶段失败，状态码: {response.status_code}")
        return False
    
    data = response.json()
    if data["status"] != "success":
        log(f"开始阶段失败，错误信息: {data.get('message', '未知错误')}")
        return False
    
    game_state = data["game_state"]
    log(f"开始阶段 {game_state['stage']} 成功，当前角色: {game_state['current_turn']}")
    return True

def test_get_event():
    """测试获取事件"""
    log("测试获取事件...")
    response = session.get(f"{BASE_URL}/get_event")
    
    if response.status_code != 200:
        log(f"获取事件失败，状态码: {response.status_code}")
        log(f"错误信息: {response.text}")
        return None
    
    data = response.json()
    if data["status"] != "success":
        log(f"获取事件失败，错误信息: {data.get('message', '未知错误')}")
        return None
    
    event = data["event"]
    log(f"获取事件成功: {event['title']}")
    return event

def test_choose_option(event, option_index=0):
    """测试选择选项"""
    if not event:
        log("没有事件，无法选择选项")
        return False
    
    log(f"测试选择选项 {option_index}: {event['options'][option_index]['text']}...")
    response = session.post(f"{BASE_URL}/choose_option", json={
        "event_id": event.get("id", "test_event"),
        "option_index": option_index,
        "event": event
    })
    
    if response.status_code != 200:
        log(f"选择选项失败，状态码: {response.status_code}")
        return False
    
    data = response.json()
    if data["status"] == "game_over":
        log(f"游戏结束: {data.get('reason', '未知原因')}")
        return False
    
    if data["status"] == "victory":
        log(f"游戏胜利!")
        return False
    
    if data["status"] != "success":
        log(f"选择选项失败，错误信息: {data.get('message', '未知错误')}")
        return False
    
    stage_complete = data.get("stage_complete", False)
    game_state = data["game_state"]
    log(f"选择选项成功, 阶段 {game_state['stage']}, 事件数: {game_state['events_in_stage']}, 阶段完成: {stage_complete}")
    
    if stage_complete:
        test_generate_story()
        
    return stage_complete

def test_generate_story():
    """测试生成故事"""
    log("测试生成故事...")
    response = session.post(f"{BASE_URL}/generate_story")
    
    if response.status_code != 200:
        log(f"生成故事失败，状态码: {response.status_code}")
        return False
    
    data = response.json()
    if data["status"] != "success":
        log(f"生成故事失败，错误信息: {data.get('message', '未知错误')}")
        return False
    
    story = data["story"]
    log(f"生成故事成功: {story[:50]}...")
    return True

def run_full_test():
    """运行完整测试"""
    log("开始完整游戏流程测试...")
    
    # 初始化游戏
    if not test_init_game():
        log("初始化游戏失败，测试终止")
        return
    
    # 开始阶段
    if not test_start_stage():
        log("开始阶段失败，测试终止")
        return
    
    # 模拟10次事件（一个完整阶段）
    log("模拟第1阶段事件...")
    for i in range(10):
        log(f"事件 {i+1}/10")
        event = test_get_event()
        if not event:
            log("获取事件失败，测试终止")
            return
        
        # 总是选择第0个选项，好感度通常是正的
        stage_complete = test_choose_option(event, 0)
        if stage_complete:
            log("阶段完成")
            break
    
    # 开始第2阶段
    log("开始第2阶段...")
    if not test_start_stage():
        log("开始第2阶段失败，测试终止")
        return
    
    # 模拟第2阶段10次事件
    log("模拟第2阶段事件...")
    for i in range(10):
        log(f"事件 {i+1}/10")
        event = test_get_event()
        if not event:
            log("获取事件失败，测试终止")
            return
        
        stage_complete = test_choose_option(event, 0)
        if stage_complete:
            log("阶段完成")
            break
    
    # 开始第3阶段
    log("开始第3阶段...")
    if not test_start_stage():
        log("开始第3阶段失败，测试终止")
        return
    
    # 模拟第3阶段10次事件
    log("模拟第3阶段事件...")
    for i in range(10):
        log(f"事件 {i+1}/10")
        event = test_get_event()
        if not event:
            log("获取事件失败，测试终止")
            return
        
        stage_complete = test_choose_option(event, 0)
        if stage_complete:
            log("阶段完成")
            break
    
    log("游戏全流程测试完成!")

if __name__ == "__main__":
    run_full_test() 