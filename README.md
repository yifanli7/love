# 爱情冒险 - Roguelike文字游戏

这是一个基于Python和Flask的Roguelike风格的中文文字冒险游戏。游戏讲述了一对男女主角从相识、相知到相爱的故事，玩家通过做出选择来影响他们的发展。

## 游戏特点

- 简洁的黑白界面设计，适合手机网页浏览
- 随机生成的事件系统，每次游戏体验都不同
- 三个游戏阶段：从陌生人到朋友，从朋友到恋人，从恋人到夫妻
- 男女主角轮流发生事件，玩家需要平衡属性以通过各个阶段

## 角色属性

每个角色有三种属性：
- 金钱：代表经济状况
- 好感度：代表对对方的感情深度
- 健康度：代表身体健康状况

## 游戏目标

帮助男女主角通过所有三个阶段，最终成为幸福的夫妻。游戏胜利条件：
- 双方好感度均超过150
- 双方健康度均大于60
- 双方金钱均大于30
- 关系状态为"夫妻"

## 项目结构

```
.
├── game/                  # 游戏核心代码
│   ├── app.py             # Flask应用主文件
│   ├── templates/         # HTML模板
│   └── static/            # 静态资源
│       ├── css/           # 样式文件
│       ├── js/            # JavaScript文件
│       └── data/          # 游戏数据
│           └── all_events.json  # 所有游戏事件
├── event/                 # 事件管理
│   ├── event_generator.py # 事件生成工具
│   ├── event_compiler.py  # 事件编译工具
│   └── events/            # 事件文件存储
│       ├── stage1/        # 第一阶段事件
│       ├── stage2/        # 第二阶段事件
│       └── stage3/        # 第三阶段事件
└── README.md              # 项目说明
```

## 如何运行

1. 安装依赖：
```bash
pip install flask
```

2. 运行游戏：
```bash
cd game
python app.py
```

3. 在浏览器中访问：
```
http://127.0.0.1:5000/
```

## 如何添加新事件

1. 使用事件生成工具：
```bash
python event/event_generator.py --stage 1 --character male
```

2. 按照提示填写事件信息

3. 编译所有事件：
```bash
python event/event_compiler.py
```

## 许可

本项目仅用于学习和个人使用，不得用于商业目的。
