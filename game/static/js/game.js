// 游戏管理器
const GameManager = {
    gameState: null,
    currentEvent: null,
    
    // 初始化游戏
    init: function(maleName, femaleName) {
        // 确保游戏从头开始
        this.resetGame(true).then(() => {
            fetch('/init', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    male_name: maleName,
                    female_name: femaleName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.gameState = data.game_state;
                    UI.updateStatsDisplay(this.gameState);
                    UI.showStageIntro(this.gameState.stage);
                } else {
                    console.error('初始化游戏失败:', data.message);
                }
            })
            .catch(error => console.error('初始化游戏出错:', error));
        });
    },
    
    // 开始阶段
    startStage: function() {
        fetch('/start_stage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.gameState = data.game_state;
                UI.updateStatsDisplay(this.gameState);
                UI.showGameScreen();
                this.getNextEvent();
            } else {
                console.error('开始阶段失败:', data.message);
            }
        })
        .catch(error => console.error('开始阶段出错:', error));
    },
    
    // 获取下一个事件
    getNextEvent: function() {
        fetch('/get_event')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.currentEvent = data.event;
                UI.displayEvent(this.currentEvent, this.gameState.current_turn);
            } else {
                console.error('获取事件失败:', data.message);
            }
        })
        .catch(error => console.error('获取事件出错:', error));
    },
    
    // 选择选项
    chooseOption: function(optionIndex) {
        if (!this.currentEvent) return;
        
        fetch('/choose_option', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_id: this.currentEvent.id,
                option_index: optionIndex,
                event: this.currentEvent
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.gameState = data.game_state;
                UI.updateStatsDisplay(this.gameState);
                
                if (data.stage_complete) {
                    UI.showStageComplete(this.gameState);
                } else {
                    this.getNextEvent();
                }
            } else if (data.status === 'game_over') {
                this.gameState = data.game_state;
                UI.showGameOver(data.reason, this.gameState);
            } else if (data.status === 'victory') {
                this.gameState = data.game_state;
                UI.showVictory(this.gameState);
            } else {
                console.error('选择选项失败:', data.message);
            }
        })
        .catch(error => console.error('选择选项出错:', error));
    },
    
    // 重置游戏
    resetGame: function(silent = false) {
        return fetch('/reset_game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.gameState = null;
                this.currentEvent = null;
                if (!silent) {
                    UI.showIntroScreen();
                }
                return true;
            } else {
                console.error('重置游戏失败:', data.message);
                return false;
            }
        })
        .catch(error => {
            console.error('重置游戏出错:', error);
            return false;
        });
    }
};

// UI管理器
const UI = {
    // 显示介绍页面
    showIntroScreen: function() {
        this.hideAllScreens();
        document.getElementById('intro-screen').classList.remove('hidden');
    },
    
    // 显示角色命名页面
    showNamingScreen: function() {
        this.hideAllScreens();
        document.getElementById('naming-screen').classList.remove('hidden');
    },
    
    // 显示阶段介绍页面
    showStageIntro: function(stage) {
        this.hideAllScreens();
        
        const titleElement = document.getElementById('stage-title');
        const descriptionElement = document.getElementById('stage-description');
        const infoElement = document.getElementById('stage-specific-info');
        
        if (stage === 1) {
            titleElement.textContent = '第一阶段：相识';
            descriptionElement.textContent = '在这个阶段，两位主角初次相遇，你需要帮助他们建立友谊。';
            infoElement.innerHTML = '<p>要求：结束时两方金钱之和大于15，双方好感度均大于50，健康度均大于80。</p>';
        } else if (stage === 2) {
            titleElement.textContent = '第二阶段：相恋';
            descriptionElement.textContent = '在这个阶段，两位主角的感情逐渐升温，你需要帮助他们成为恋人。';
            infoElement.innerHTML = '<p>要求：结束时两方金钱之和大于30，双方好感度均大于80，健康度均大于80。</p>';
        } else if (stage === 3) {
            titleElement.textContent = '第三阶段：相守';
            descriptionElement.textContent = '在这个阶段，两位主角的感情更加稳固，你需要帮助他们迈向婚姻。';
            infoElement.innerHTML = '<p>要求：结束时两方金钱之和大于50，双方好感度均大于100，健康度均大于80。</p>';
        }
        
        document.getElementById('stage-intro-screen').classList.remove('hidden');
    },
    
    // 显示阶段完成页面
    showStageComplete: function(gameState) {
        this.hideAllScreens();
        
        const titleElement = document.getElementById('completion-title');
        const relationshipElement = document.getElementById('relationship-status');
        const summaryElement = document.getElementById('stats-summary');
        
        // 根据关系状态更新
        const relationship = gameState.relationship;
        titleElement.textContent = '恭喜！';
        relationshipElement.textContent = `${gameState.male.name}和${gameState.female.name}已成为${relationship}！`;
        
        // 显示当前属性
        summaryElement.innerHTML = `
            <h3>当前属性</h3>
            <div class="summary-stats">
                <div>
                    <strong>${gameState.male.name}：</strong>
                    <ul>
                        <li>金钱：${gameState.male.money}</li>
                        <li>好感度：${gameState.male.affection}</li>
                        <li>健康度：${gameState.male.health}</li>
                    </ul>
                </div>
                <div>
                    <strong>${gameState.female.name}：</strong>
                    <ul>
                        <li>金钱：${gameState.female.money}</li>
                        <li>好感度：${gameState.female.affection}</li>
                        <li>健康度：${gameState.female.health}</li>
                    </ul>
                </div>
            </div>
        `;
        
        // 添加一个"正在生成故事"的提示
        const storyElement = document.createElement('div');
        storyElement.id = 'love-story';
        storyElement.className = 'love-story';
        storyElement.innerHTML = '<p class="loading-text">正在生成爱情故事，请稍等...</p>';
        summaryElement.after(storyElement);
        
        // 调用API生成故事
        this.generateLoveStory(gameState);
        
        document.getElementById('stage-complete-screen').classList.remove('hidden');
    },
    
    // 生成爱情故事
    generateLoveStory: function(gameState) {
        fetch('/generate_story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            const storyElement = document.getElementById('love-story');
            if (data.status === 'success') {
                // 格式化并显示故事
                const story = data.story;
                storyElement.innerHTML = `
                    <h3>爱情故事</h3>
                    <div class="story-content">
                        ${story.replace(/\n/g, '<br>')}
                    </div>
                `;
            } else {
                storyElement.innerHTML = `<p class="error-text">生成故事失败: ${data.message}</p>`;
            }
        })
        .catch(error => {
            console.error('获取故事出错:', error);
            const storyElement = document.getElementById('love-story');
            storyElement.innerHTML = `<p class="error-text">获取故事时出错，请稍后再试</p>`;
        });
    },
    
    // 显示游戏主界面
    showGameScreen: function() {
        this.hideAllScreens();
        document.getElementById('game-screen').classList.remove('hidden');
    },
    
    // 显示游戏结束页面
    showGameOver: function(reason, gameState) {
        this.hideAllScreens();
        
        document.getElementById('game-over-reason').textContent = reason;
        
        // 显示故事总结
        const summaryElement = document.getElementById('story-summary');
        summaryElement.innerHTML = this.generateStorySummary(gameState);
        
        // 如果有存储的爱情故事，显示最后一个
        if (gameState.story && Object.keys(gameState.story).length > 0) {
            const lastStage = Math.max(...Object.keys(gameState.story).map(Number));
            const lastStory = gameState.story[lastStage];
            
            if (lastStory) {
                const storyElement = document.createElement('div');
                storyElement.className = 'love-story';
                storyElement.innerHTML = `
                    <h3>最后的爱情故事</h3>
                    <div class="story-content">
                        ${lastStory.replace(/\n/g, '<br>')}
                    </div>
                `;
                summaryElement.after(storyElement);
            }
        }
        
        document.getElementById('game-over-screen').classList.remove('hidden');
    },
    
    // 显示胜利页面
    showVictory: function(gameState) {
        this.hideAllScreens();
        
        // 显示属性总结
        const statsElement = document.getElementById('victory-stats-summary');
        statsElement.innerHTML = `
            <h3>最终属性</h3>
            <div class="summary-stats">
                <div>
                    <strong>${gameState.male.name}：</strong>
                    <ul>
                        <li>金钱：${gameState.male.money}</li>
                        <li>好感度：${gameState.male.affection}</li>
                        <li>健康度：${gameState.male.health}</li>
                    </ul>
                </div>
                <div>
                    <strong>${gameState.female.name}：</strong>
                    <ul>
                        <li>金钱：${gameState.female.money}</li>
                        <li>好感度：${gameState.female.affection}</li>
                        <li>健康度：${gameState.female.health}</li>
                    </ul>
                </div>
            </div>
        `;
        
        // 显示故事总结
        const summaryElement = document.getElementById('victory-story-summary');
        summaryElement.innerHTML = this.generateStorySummary(gameState);
        
        // 添加一个"正在生成故事"的提示
        const storyElement = document.createElement('div');
        storyElement.id = 'victory-love-story';
        storyElement.className = 'love-story';
        storyElement.innerHTML = '<p class="loading-text">正在生成最终爱情故事，请稍等...</p>';
        summaryElement.after(storyElement);
        
        // 调用API生成最终故事
        this.generateLoveStory(gameState);
        
        document.getElementById('victory-screen').classList.remove('hidden');
    },
    
    // 隐藏所有页面
    hideAllScreens: function() {
        const screens = document.querySelectorAll('.screen');
        screens.forEach(screen => screen.classList.add('hidden'));
    },
    
    // 更新属性显示
    updateStatsDisplay: function(gameState) {
        if (!gameState) return;
        
        // 更新男性属性
        document.getElementById('male-name-display').textContent = gameState.male.name;
        document.getElementById('male-money').textContent = gameState.male.money;
        document.getElementById('male-affection').textContent = gameState.male.affection;
        document.getElementById('male-health').textContent = gameState.male.health;
        
        // 更新女性属性
        document.getElementById('female-name-display').textContent = gameState.female.name;
        document.getElementById('female-money').textContent = gameState.female.money;
        document.getElementById('female-affection').textContent = gameState.female.affection;
        document.getElementById('female-health').textContent = gameState.female.health;
        
        // 更新关系状态
        const relationshipDisplay = document.getElementById('relationship-display');
        relationshipDisplay.textContent = gameState.relationship;
        relationshipDisplay.setAttribute('data-status', gameState.relationship);
    },
    
    // 显示事件
    displayEvent: function(event, currentTurn) {
        if (!event) return;
        
        const turnIndicator = document.getElementById('turn-indicator');
        const currentCharacter = currentTurn === 'male' ? GameManager.gameState.male.name : GameManager.gameState.female.name;
        turnIndicator.textContent = `当前回合：${currentCharacter}`;
        
        // 显示事件标题和描述
        document.getElementById('event-title').textContent = event.title;
        document.getElementById('event-description').textContent = event.description;
        
        // 清空选项容器
        const optionsContainer = document.querySelector('.options');
        optionsContainer.innerHTML = '';
        
        // 确保总是显示三个选项，即使事件只有一两个选项也保持UI布局一致
        const optionsCount = event.options.length;
        const maxOptions = 3;
        
        // 创建选项按钮
        event.options.forEach((option, index) => {
            this.createOptionButton(optionsContainer, option, index);
        });
        
        // 如果选项不足三个，填充空白选项保持布局一致
        for (let i = optionsCount; i < maxOptions; i++) {
            const dummyOption = document.createElement('div');
            dummyOption.className = 'option-btn dummy';
            dummyOption.style.visibility = 'hidden';
            dummyOption.style.height = '60px';
            optionsContainer.appendChild(dummyOption);
        }
    },
    
    // 创建选项按钮
    createOptionButton: function(container, option, index) {
        const button = document.createElement('button');
        button.className = 'option-btn';
        button.textContent = option.text;
        button.dataset.index = index;
        button.addEventListener('click', () => GameManager.chooseOption(index));
        container.appendChild(button);
    },
    
    // 生成故事总结
    generateStorySummary: function(gameState) {
        const events = gameState.events_happened;
        if (!events || events.length === 0) return '<p>没有记录任何事件。</p>';
        
        let html = '<h3>故事总结</h3><ul>';
        
        events.forEach(event => {
            const character = event.character === 'male' ? gameState.male.name : gameState.female.name;
            html += `<li><strong>${event.time}</strong>: ${character} "${event.title}" - 选择了 "${event.option_chosen}"</li>`;
        });
        
        html += '</ul>';
        return html;
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 显示介绍页面
    UI.showIntroScreen();
    
    // 介绍页面点击事件
    document.getElementById('start-btn').addEventListener('click', function() {
        UI.showNamingScreen();
    });
    
    // 角色命名页面点击事件
    document.getElementById('name-confirm-btn').addEventListener('click', function() {
        const maleName = document.getElementById('male-name').value.trim();
        const femaleName = document.getElementById('female-name').value.trim();
        GameManager.init(maleName, femaleName);
    });
    
    // 阶段介绍页面点击事件
    document.getElementById('stage-start-btn').addEventListener('click', function() {
        GameManager.startStage();
    });
    
    // 阶段完成页面点击事件
    document.getElementById('next-stage-btn').addEventListener('click', function() {
        UI.showStageIntro(GameManager.gameState.stage);
    });
    
    // 游戏结束页面点击事件
    document.getElementById('restart-btn').addEventListener('click', function() {
        GameManager.resetGame();
    });
    
    // 胜利页面点击事件
    document.getElementById('victory-restart-btn').addEventListener('click', function() {
        GameManager.resetGame();
    });
}); 