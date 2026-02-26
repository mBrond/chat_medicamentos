
const API_BASE_URL = window.location.origin;

const messagesDiv = document.getElementById('messages');
const questionInput = document.getElementById('question');
const sendBtn = document.getElementById('send');
const healthIndicator = document.getElementById('health-indicator');

const BOT_AVATAR = '/static/img/pfp_bot.png';
const quickOptionsHome = ['Onde retirar Medicamento', 'Informações com CID', 'Informações com Medicamento'];
const quickOptionsPosConsulta = ['Onde Retirar?', 'Voltar'];

let currentIntent = null;
let state = 'CHOOSING_OPTION';
let lastSearchTerm = null;

const delay = ms => new Promise(res => setTimeout(res, ms));

/* ===== MONITORAMENTO (HEALTH CHECK) ===== */
async function checkHealth() {
    try {
        const r = await fetch(`${API_BASE_URL}/health`);
        if (r.ok) {
            healthIndicator.textContent = 'online';
            healthIndicator.className = 'status-ok';
        } else {
            healthIndicator.textContent = 'offline';
            healthIndicator.className = 'status-fail';
        }
    } catch {
        healthIndicator.textContent = 'offline';
        healthIndicator.className = 'status-fail';
    }
}

/* ===== COMUNICAÇÃO COM BACKEND ===== */
async function callConversationAPI(text, intent) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, intent: intent })
    });
    if (!response.ok) throw new Error("Erro na API");
    return await response.json();
}

/* ===== HANDLERS DE INTERFACE ===== */
async function handleOptionsClick(option) {
    const text = option.trim();
    addMessage(text, 'user');

    if (text.toLowerCase() === 'voltar') {
        await delay(500);
        resetToHome();
        return;
    }

    if (text === 'Onde retirar Medicamento') {
        state = 'WAITING_VALUE';
        currentIntent = 'onde retirar medicamento';
        await delay(500);
        addMessage("Certo! Digite o nome do medicamento para eu localizar as farmácias:", 'bot');
    }
    else if (text === 'Informações com CID') {
        state = 'WAITING_VALUE';
        currentIntent = 'cid';
        await delay(500);
        addMessage("Ok! Qual o código CID?", 'bot');
    }
    else if (text === 'Informações com Medicamento') {
        state = 'WAITING_VALUE';
        currentIntent = 'medicamento';
        await delay(500);
        addMessage("Qual o nome do medicamento para eu buscar as informações?", 'bot');
    }
    else if (text === 'Onde Retirar?') {
        if (lastSearchTerm) {
            currentIntent = 'onde retirar medicamento';
            addMessage(`Buscando pontos de retirada para: ${lastSearchTerm}...`, 'bot');
            await chatHandler(lastSearchTerm);
        } else {
            state = 'WAITING_VALUE';
            currentIntent = 'onde retirar medicamento';
            addMessage("Digite o nome do medicamento para eu localizar:", 'bot');
        }
    }
}

async function chatHandler(text) {
    if (state === 'PROCESSING') return;

    const typing = showTypingIndicator();
    state = 'PROCESSING';

    try {
        const data = await callConversationAPI(text, currentIntent);
        typing.remove();


        console.log(data);

        if (data.erro){
            console.log(data.erro);
            conversaSobreErro(data.erro);
            await delay(1000)
            resetToHome();
        }

        else if (data.map_data) {
            addMessage("Encontrei os seguintes locais para retirada:", 'bot', null, null, data.map_data);
            state = 'CHOOSING_OPTION';
            await delay(1000);
            addBotOptions("Deseja realizar outra busca?", quickOptionsHome);
        }
        else if (data.answer) {
            addMessage(data.answer, 'bot', data.latency);
            state = 'FINISHED_SEARCH';

            lastSearchTerm = text;
            await delay(500);
            addBotOptions("O que deseja fazer agora?", quickOptionsPosConsulta);
        }
    } catch (error) {
        if(typing) typing.remove();
        addMessage("Desculpe, tive um problema ao consultar essas informações.", 'bot');
        resetToHome();
    } 
}

/* ===== RENDERIZAÇÃO DE MENSAGENS ===== */
function addMessage(text, type='user', latency = null, imageUrl = null, mapData = null) {
    const div = document.createElement('div');
    div.className = `message ${type}`;

    if (type === 'bot') {
        const avatar = document.createElement('img');
        avatar.src = BOT_AVATAR;
        avatar.className = 'avatar';
        div.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.style.whiteSpace = 'pre-wrap';
    bubble.textContent = text;

    if (mapData) mapa_msg(mapData, bubble);
    if (imageUrl) img_msg(imageUrl, bubble);

    if (latency) {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = `⏱️ ${latency}s`;
        bubble.appendChild(timeDiv);
    }

    div.appendChild(bubble);
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addBotOptions(text, options) {
    const div = document.createElement('div');
    div.className = 'message bot';
    div.innerHTML = `<img src="${BOT_AVATAR}" class="avatar">`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'quick-options';

    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.textContent = opt;
        btn.onclick = () => handleOptionsClick(opt);
        buttonsDiv.appendChild(btn);
    });

    bubble.appendChild(buttonsDiv);
    div.appendChild(bubble);
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/* ===== FUNÇÕES DE APOIO (MAPA E VISUAL) ===== */
function showTypingIndicator() {
    const typing = document.createElement('div');
    typing.className = 'message bot typing-indicator';
    typing.innerHTML = `<img src="${BOT_AVATAR}" class="avatar"><div class="bubble">Digitando...</div>`;
    messagesDiv.appendChild(typing);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return typing;
}

function img_msg(imageUrl, parentBubble) {
    const img = document.createElement('img');
    img.src = imageUrl;
    img.className = 'bot-image';
    img.style.width = '100%';
    img.style.borderRadius = '8px';
    parentBubble.appendChild(img);
}

function mapa_msg(mapData, parentBubble) {
    const mapId = `map-${Date.now()}`;
    const mapDiv = document.createElement('div');
    mapDiv.id = mapId;
    mapDiv.className = 'map-container';
    mapDiv.style.height = '250px';
    parentBubble.appendChild(mapDiv);

    setTimeout(() => {
        const map = L.map(mapId);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        const bounds = L.latLngBounds();
        if (mapData.markers && mapData.markers.length > 0) {
            mapData.markers.forEach(m => {
                let popupContent = `<b>${m.nome}</b><p>${m.endereco || ''}</p>`;
                if (m.imagem) popupContent += `<img src="${m.imagem}" style="width:100%">`;

                const marker = L.marker([m.lat, m.lng]).addTo(map).bindPopup(popupContent);
                bounds.extend(marker.getLatLng());
            });

            if (mapData.markers.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
            else map.setView([mapData.markers[0].lat, mapData.markers[0].lng], 15);
        } else {
            map.setView(mapData.center || [-29.684, -53.806], 13);
        }
        setTimeout(() => map.invalidateSize(), 200);
    }, 0);
}

function resetToHome() {
    state = 'CHOOSING_OPTION';
    currentIntent = null;
    lastSearchTerm = null;
    addBotOptions("Como posso ajudar?", quickOptionsHome);
}

function conversaSobreErro(erro) {
    if (erro === 'CID inválido') {
        addMessage("Não entendi qual CID você procura. Informe um CID com no mínimo 3 e no máximo 5 caracteres.", 'bot');
    } else {
        addMessage(`Ops! Ocorreu um problema: ${erro}`, 'bot');
    }
}

/* ===== EVENTOS E INICIALIZAÇÃO ===== */
async function sendMessage() {
    const text = questionInput.value.trim();
    if (!text || state === 'PROCESSING') return;
    addMessage(text, 'user');
    questionInput.value = '';

    if(text.toLowerCase() === 'voltar') {
        resetToHome();
        return;
    }

    if (state === 'WAITING_VALUE') {
        await chatHandler(text);
    } else {
        addMessage("Por favor, selecione uma das opções abaixo para começar.", 'bot');
        await delay(500);
        resetToHome();
    }
}

sendBtn.addEventListener('click', sendMessage);
questionInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMessage(); });

// Ajuste para Mobile (Teclado)
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', () => {
        const viewHeight = window.visualViewport.height;
        const appContainer = document.querySelector('.app');
        if(appContainer) appContainer.style.height = `${viewHeight}px`;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
}

window.onload = () => {
    checkHealth();
    state = 'CHOOSING_OPTION';
    currentIntent = null;
    lastSearchTerm = null;
    addBotOptions("Olá! Como posso ajudar?", quickOptionsHome);
};