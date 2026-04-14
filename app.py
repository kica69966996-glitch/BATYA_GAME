from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>УБЕГИ ОТ БАТИ 67 (SAVE PROGRESS)</title>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Arial Black', sans-serif; background: #000; color: white; user-select: none; }
        canvas { display: block; margin: 0 auto; background: #222; border-bottom: 20px solid #111; }
        .ui { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); padding: 15px; border-radius: 10px; border: 2px solid #ff00ff; z-index: 50; }
        #achievements { position: absolute; bottom: 30px; left: 10px; display: flex; flex-direction: column; gap: 5px; }
        .ach-item { padding: 5px 10px; background: #333; border: 1px solid #555; color: #777; font-size: 12px; border-radius: 5px; }
        .ach-unlocked { border-color: gold; color: gold; background: #443300; }
        #menu { position: fixed; inset: 0; background: rgba(0,0,0,0.95); display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000; }
        #shop-ui { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 85%; height: 75%; background: #111; border: 5px solid #ff00ff; padding: 20px; display: none; z-index: 2000; text-align: center; overflow-y: auto; }
        button { padding: 12px; margin: 5px; cursor: pointer; width: 220px; font-weight: bold; border-radius: 8px; border: none; font-size: 12px; }
        .btn-play { background: lime; font-size: 20px; height: 60px; width: 300px; }
        .btn-buy { background: #4CAF50; color: white; }
        #win-btn { display: none; position: absolute; top: 20%; left: 50%; transform: translateX(-50%); z-index: 300; background: linear-gradient(to right, red,orange,yellow,green,blue,indigo,violet); color: white; font-size: 24px; width: 350px; height: 80px; border: 5px solid white; cursor: pointer; }
        #ending-screen { position: fixed; inset: 0; background: black; display: none; flex-direction: column; justify-content: center; align-items: center; z-index: 5000; text-align: center; }
    </style>
</head>
<body>

    <audio id="bgMusic" loop><source src="/static/bg_music.mp3" type="audio/mpeg"></audio>
    <audio id="jumpSound"><source src="/static/jump.mp3" type="audio/mpeg"></audio>

    <div class="ui">
        <div>Счёт: <span id="score">0</span> | Рекорд: <span id="best">0</span></div>
        <div>Монеты: <span id="coins">0</span></div>
    </div>

    <div id="achievements">
        <div id="ach-67" class="ach-item">🔒 ??? (Секретный скин)</div>
        <div id="ach-gay" class="ach-item">🔒 ??? (Радужный скин)</div>
        <div id="ach-win" class="ach-item">🔒 ??? (Прохождение)</div>
    </div>

    <div id="menu">
        <h1 style="color: red; font-size: 40px; text-align: center;">УБЕГИ ОТ САНЕНОГО ОТЦА</h1>
        <button class="btn-play" onclick="startGame()">ИГРАТЬ</button>
        <button onclick="toggleShop(true)" style="background: cyan;">МАГАЗИН</button>
        <button onclick="resetProgress()" style="background: gray; width: 150px; font-size: 10px; margin-top: 20px;">СБРОС ПРОГРЕССА</button>
    </div>

    <div id="shop-ui">
        <h2 style="color: #ff00ff;">ГАРДЕРОБ</h2>
        <p>Баланс: <span id="shop-coins">0</span> 🪙</p>
        <div id="skins-container" style="display: flex; flex-wrap: wrap; justify-content: center;"></div>
        <hr style="border-color: #333;">
        <div id="special-skins" style="display: flex; flex-wrap: wrap; justify-content: center;">
             <button id="btn-rainbow-skin" style="background: #333; color: #666;">🌈 РАДУЖНЫЙ</button>
             <button id="btn-67-skin" style="background: #333; color: #666;">💀 67-ДРОССЕЛЬ</button>
        </div>
        <button onclick="toggleShop(false)" style="background: red; color: white; margin-top: 10px;">ВЫХОД</button>
    </div>

    <button id="win-btn" onclick="showChoices()">ЗАКОНЧИТЬ ИГРУ?</button>

    <div id="ending-screen">
        <h1 id="ending-text" style="color:white;"></h1>
        <div id="ending-choices">
            <button style="background: #333; color: white; width: 400px;" onclick="triggerFinal()">ДА</button>
            <button style="background: #333; color: white; width: 400px;" onclick="triggerFinal()">А НЕ ПОЙТИ КА ЛИ ТЕБЕ НАЗУЙ ДРОСЕЛЬ</button>
        </div>
    </div>

    <canvas id="game"></canvas>

    <script>
        const canvas = document.getElementById('game');
        const ctx = canvas.getContext('2d');
        const bgMusic = document.getElementById('bgMusic');
        const jumpSound = document.getElementById('jumpSound');

        canvas.width = window.innerWidth; canvas.height = 550;
        const GROUND_Y = 510;

        // --- ЛОГИКА СОХРАНЕНИЯ ---
        let score = 0, obstacles = [], spawnTimer = null, active = false;

        // Загрузка данных из LocalStorage
        let bestScore = parseInt(localStorage.getItem('bestScore')) || 0;
        let coins = parseInt(localStorage.getItem('coins')) || 0;
        let inventory = JSON.parse(localStorage.getItem('inventory')) || { 
            bought: ['std'], 
            currentSkin: '#228B22', 
            isSpecial: false, 
            activeId: 'std' 
        };
        let achData = JSON.parse(localStorage.getItem('achData')) || {
            s67: false, gay: false, win: false
        };

        function saveGame() {
            localStorage.setItem('bestScore', bestScore);
            localStorage.setItem('coins', coins);
            localStorage.setItem('inventory', JSON.stringify(inventory));
            localStorage.setItem('achData', JSON.stringify(achData));
        }

        function resetProgress() {
            if(confirm("Удалить весь прогресс?")) {
                localStorage.clear();
                location.reload();
            }
        }
        // -------------------------

        let speed = 2.3;
        const player = { x: 250, y: 0, w: 60, h: 90, dy: 0, jump: -8.5, grav: 0.18, grounded: false };

        const colors = [
            {id: 'c1', name: 'Красный', val: 'red'}, {id: 'c2', name: 'Оранжевый', val: 'orange'},
            {id: 'c3', name: 'Желтый', val: 'yellow'}, {id: 'c4', name: 'Зеленый', val: 'lime'},
            {id: 'c5', name: 'Голубой', val: 'deepskyblue'}, {id: 'c6', name: 'Синий', val: 'blue'},
            {id: 'c7', name: 'Фиолетовый', val: 'purple'}
        ];

        function startGame() {
            document.getElementById('menu').style.display = 'none';
            bgMusic.play().catch(() => {});
            active = true; score = 0; speed = 2.3; obstacles = [];
            player.y = GROUND_Y - player.h; player.dy = 0;
            if(spawnTimer) clearTimeout(spawnTimer);
            spawnObstacle(); update();
        }

        function toggleShop(show) {
            if(show) renderShop();
            document.getElementById('shop-ui').style.display = show ? 'block' : 'none';
            document.getElementById('shop-coins').innerText = Math.floor(coins);
        }

        function renderShop() {
            const container = document.getElementById('skins-container');
            container.innerHTML = `<button class="btn-buy" onclick="setSkin('std','#228B22', false)">ДЕФОЛТ</button>`;
            colors.forEach((c, i) => {
                const price = 200 + (i * 50);
                const isBought = inventory.bought.includes(c.id);
                const btn = document.createElement('button');
                btn.className = 'btn-buy';
                btn.style.background = c.val;
                btn.innerText = isBought ? c.name : `${c.name} (${price})`;
                btn.onclick = () => buySkin(c.id, price, c.val, false);
                container.appendChild(btn);
            });

            const allColorsBought = colors.every(c => inventory.bought.includes(c.id));
            if (allColorsBought) {
                const rbBtn = document.getElementById('btn-rainbow-skin');
                rbBtn.style.background = 'linear-gradient(to right, red, violet)'; rbBtn.style.color = 'white'; rbBtn.style.cursor = 'pointer';
                rbBtn.innerText = inventory.bought.includes('rainbow_skin') ? 'РАДУЖНЫЙ' : 'РАДУЖНЫЙ (4242)';
                rbBtn.onclick = () => buySkin('rainbow_skin', 4242, 'rainbow', true);
            }
            if (bestScore >= 2067) {
                const s67Btn = document.getElementById('btn-67-skin');
                s67Btn.style.background = '#676767'; s67Btn.style.color = 'white'; s67Btn.style.cursor = 'pointer';
                s67Btn.innerText = inventory.bought.includes('67') ? '67-ДРОССЕЛЬ' : '67-ДРОССЕЛЬ (3000)';
                s67Btn.onclick = () => buySkin('67', 3000, 'rainbow', true);
            }
        }

        function buySkin(id, price, colorVal, isSpec) {
            if (inventory.bought.includes(id)) { setSkin(id, colorVal, isSpec); }
            else if (coins >= price) {
                coins -= price; inventory.bought.push(id); 
                if(id === '67') achData.s67 = true;
                if(id === 'rainbow_skin') achData.gay = true;
                saveGame();
                setSkin(id, colorVal, isSpec);
                renderShop();
                checkAchievements();
            }
        }

        function setSkin(id, colorVal, isSpec) { 
            inventory.currentSkin = colorVal; inventory.isSpecial = isSpec; inventory.activeId = id; 
            saveGame();
            toggleShop(false); 
        }

        function checkAchievements() {
            if(achData.s67) unlockAchDisplay('ach-67', 'ты еще не заебался?');
            if(achData.gay) unlockAchDisplay('ach-gay', 'теперь ты официально сменил ориентацию!');
            if(achData.win) unlockAchDisplay('ach-win', 'а зачем я все это делал?');
        }

        function unlockAchDisplay(domId, text) {
            const el = document.getElementById(domId);
            el.classList.add('ach-unlocked'); el.innerText = '✅ ' + text;
        }

        function spawnObstacle() {
            if (!active) return;
            const type = Math.random();
            let ob = { x: canvas.width, w: 50, h: 60 }; 
            if (type < 0.3) { ob.w = 35; ob.h = 95; } else if (type < 0.6) { ob.w = 100; ob.h = 40; }
            ob.y = GROUND_Y - ob.h; obstacles.push(ob);
            spawnTimer = setTimeout(spawnObstacle, Math.max(1000, 3000 - (score * 5)));
        }

        function update() {
            if (!active) return;
            player.dy += player.grav; player.y += player.dy;
            if (player.y + player.h > GROUND_Y) { player.y = GROUND_Y - player.h; player.dy = 0; player.grounded = true; }
            speed += 0.0001;
            for (let i = obstacles.length - 1; i >= 0; i--) {
                obstacles[i].x -= speed;
                if (player.x < obstacles[i].x + obstacles[i].w && player.x + player.w > obstacles[i].x && player.y < obstacles[i].y + obstacles[i].h && player.y + player.h > obstacles[i].y) {
                    active = false; bgMusic.pause();
                    if (score > bestScore) {
                        bestScore = score;
                        saveGame();
                    }
                    document.getElementById('best').innerText = bestScore;
                    document.getElementById('menu').style.display = 'flex';
                }
                if (obstacles[i].x + obstacles[i].w < 0) { 
                    obstacles.splice(i, 1); score++; coins += 5; 
                    saveGame(); // Сохраняем монеты после каждого очка
                }
            }
            if (inventory.activeId === '67' && score >= 5252) document.getElementById('win-btn').style.display = 'block';
            draw(); requestAnimationFrame(update);
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "red"; ctx.fillRect(20, GROUND_Y - 150, 100, 150);
            ctx.fillStyle = "white"; ctx.fillText("САНЯ-ОТЕЦ", 30, GROUND_Y - 160);
            if (inventory.isSpecial) { ctx.fillStyle = `hsl(${Date.now() % 360}, 100%, 50%)`; } else { ctx.fillStyle = inventory.currentSkin; }
            ctx.fillRect(player.x, player.y, player.w, player.h);
            ctx.fillStyle = "orange"; obstacles.forEach(ob => ctx.fillRect(ob.x, ob.y, ob.w, ob.h));
            document.getElementById('score').innerText = score;
            document.getElementById('best').innerText = bestScore;
            document.getElementById('coins').innerText = Math.floor(coins);
        }

        function showChoices() { active = false; document.getElementById('ending-screen').style.display = 'flex'; document.getElementById('ending-text').innerText = "ЗАКОНЧИТЬ ИГРУ?"; }

        function triggerFinal() {
            achData.win = true;
            saveGame();
            checkAchievements();
            document.getElementById('ending-choices').style.display = 'none';
            const txt = document.getElementById('ending-text');
            txt.innerText = "676767спасибо за просранное время в пустую676767";
            setTimeout(() => { txt.innerText = "67 дросель нюхает какаху 67"; txt.style.fontSize = "45px"; txt.style.color = "lime"; }, 3000);
        }

        window.addEventListener('keydown', (e) => { if (e.code === 'Space') { e.preventDefault(); if(active && player.grounded) { player.dy = player.jump; player.grounded = false; jumpSound.currentTime = 0; jumpSound.play().catch(()=>{}); } } });
        canvas.addEventListener('mousedown', () => { if(active && player.grounded) { player.dy = player.jump; player.grounded = false; jumpSound.currentTime = 0; jumpSound.play().catch(()=>{}); } });

        // Инициализация при загрузке
        document.getElementById('best').innerText = bestScore;
        checkAchievements();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    app.run(debug=True)