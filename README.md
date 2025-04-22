# 爱情冒险游戏

一个基于Flask的爱情文字冒险游戏，采用Roguelike随机事件机制，带有AI生成的爱情故事。

## 项目介绍

这是一个文字冒险游戏，玩家将跟随一对男女主角的爱情故事，从陌生人到朋友，再到恋人，最后成为夫妻。游戏共分为三个阶段，每个阶段都有10个随机事件，玩家需要做出选择，这些选择将影响角色的金钱、好感度和健康度。游戏结束时，AI将根据游戏过程中的选择和角色状态生成一个独特的爱情故事。

## 主要功能

- **角色定制**：玩家可以自定义男女主角的名字
- **随机事件**：每个阶段有多个随机事件，玩家需要做出选择
- **属性系统**：角色有金钱、好感度和健康度三种属性
- **关系演变**：角色关系从陌生人逐渐发展为朋友、恋人和夫妻
- **AI故事生成**：游戏结束时生成基于游戏进程的个性化爱情故事
- **移动端适配**：游戏界面对移动设备进行了优化

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML5, CSS3, JavaScript
- **AI故事生成**：基于DeepSeek API
- **部署**：支持Vercel云函数部署

## 使用方法

### 本地运行

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/love-adventure-game.git
cd love-adventure-game
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量（可选）：
```bash
export DEEPSEEK_API_KEY=your_api_key_here
export FLASK_SECRET_KEY=your_secret_key
```

4. 运行游戏：
```bash
python game/app.py
```

5. 在浏览器中访问：`http://localhost:8080`

### Vercel部署

1. Fork这个仓库
2. 在Vercel上导入项目
3. 设置环境变量：`DEEPSEEK_API_KEY` 和 `FLASK_SECRET_KEY`
4. 部署

## 游戏玩法

1. 输入男女主角的名字，开始游戏
2. 每个阶段有10个随机事件，代表不同的场景和情境
3. 针对每个事件，玩家可以选择一个选项作为回应
4. 不同的选择会影响角色的属性值
5. 完成每个阶段的目标后，游戏会生成一段爱情故事
6. 所有三个阶段完成后，游戏胜利

## 注意事项

- 任何属性降至0以下，游戏将结束
- 每个阶段有不同的目标要求，需要保持良好的属性状态才能通过
- 在Vercel环境中，故事生成功能使用预设模板，以遵守Vercel的执行时间限制

## 贡献

欢迎提交Pull Request或创建Issue来改进这个项目！

## 许可

MIT License
