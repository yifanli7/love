import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.app import app

# 导出应用以供Vercel使用
if __name__ == "__main__":
    app.run() 