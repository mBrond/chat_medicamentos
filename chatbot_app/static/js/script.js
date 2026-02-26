
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
const statusDot = document.getElementById('status-dot');

async function checkHealth() {
    try {
        const r = await fetch(`${API_BASE_URL}/health`);
        if (r.ok) {
            healthIndicator.textContent = 'online';
            statusDot.className = 'status-dot online';
        } else {
            healthIndicator.textContent = 'offline';
            statusDot.className = 'status-dot offline';
        }
    } catch {
        healthIndicator.textContent = 'offline';
        statusDot.className = 'status-dot offline';
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

        if (data.invalido) {
            conversaSobreErro(data.invalido);
            await delay(1000);
            resetToHome();
        }
        else if (data.map_data) {
            addMessage(
                "Encontrei os seguintes locais para retirada:",
                'bot', null, null, data.map_data,
                data.match_type, data.nome_encontrado
            );
            state = 'CHOOSING_OPTION';
            await delay(1000);
            addBotOptions("Deseja realizar outra busca?", quickOptionsHome);
        }
        else if (data.answer) {
            addMessage(
                data.answer,
                'bot', data.latency, null, null,
                data.match_type, data.nome_encontrado
            );
            state = 'FINISHED_SEARCH';
            lastSearchTerm = text;
            await delay(500);
            addBotOptions("O que deseja fazer agora?", quickOptionsPosConsulta);
        }
    } catch (error) {
        if (typing) typing.remove();
        addMessage("Desculpe, tive um problema ao consultar essas informações.", 'bot');
        resetToHome();
    }
}

/* ===== RENDERIZAÇÃO DE MENSAGENS ===== */
function addMessage(text, type = 'user', latency = null, imageUrl = null, mapData = null, matchType = null, nomeEncontrado = null) {
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

    // referente ao match do csv
    if (type === 'bot' && matchType && nomeEncontrado) {
        const badge = document.createElement('div');
        badge.className = `match-badge ${matchType}`;

        if (matchType === 'exato') {
            badge.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
                Resultado exato: <strong style="margin-left:3px">${nomeEncontrado}</strong>
            `;
        } else {
            badge.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Resultado semelhante: <strong style="margin-left:3px">${nomeEncontrado}</strong>
            `;
        }

        bubble.appendChild(badge);
    }

    //texto principal
    const textNode = document.createElement('span');
    textNode.style.whiteSpace = 'pre-wrap';
    textNode.textContent = text;
    bubble.appendChild(textNode);

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

    // Wrapper relativo para o hint ficar posicionado
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';

    const mapDiv = document.createElement('div');
    mapDiv.id = mapId;
    mapDiv.className = 'map-container';

    // Hint "Toque num marcador"
    const hint = document.createElement('div');
    hint.className = 'map-hint';
    hint.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/>
            <circle cx="12" cy="10" r="3"/>
        </svg>
        Toque num marcador
    `;

    wrapper.appendChild(mapDiv);
    wrapper.appendChild(hint);
    parentBubble.appendChild(wrapper);

    setTimeout(() => {
        const map = L.map(mapId, {
            zoomControl: true,
            tap: true,          // habilita tap no iOS
            tapTolerance: 15,   // maior tolerância de toque
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        const bounds = L.latLngBounds();

        if (mapData.markers && mapData.markers.length > 0) {
            mapData.markers.forEach((m, i) => {
                // Ícone numerado customizado
                const icon = L.divIcon({
                    className: '',
                    html: `<div style="
                        width: 32px; height: 32px;
                        background: #004a99;
                        color: #fff;
                        border-radius: 50% 50% 50% 0;
                        transform: rotate(-45deg);
                        display: flex; align-items: center; justify-content: center;
                        font-size: 12px; font-weight: 700;
                        border: 2px solid #fff;
                        box-shadow: 0 2px 8px rgba(0,74,153,0.5);
                        cursor: pointer;
                    "><span style="transform: rotate(45deg)">${i + 1}</span></div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                });

                const marker = L.marker([m.lat, m.lng], { icon })
                    .addTo(map)
                    .on('click', () => openMapSheet(m, i));

                bounds.extend(marker.getLatLng());
            });

            if (mapData.markers.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
            else map.setView([mapData.markers[0].lat, mapData.markers[0].lng], 15);
        } else {
            map.setView(mapData.center || [-29.684, -53.806], 13);
        }

        // Esconde o hint após 3s
        setTimeout(() => {
            hint.style.transition = 'opacity 0.5s';
            hint.style.opacity = '0';
            setTimeout(() => hint.remove(), 500);
        }, 3000);

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
    if (erro === 'CID invalido') {
        addMessage("Não entendi qual CID você procura. Informe um CID com no mínimo 3 e no máximo 5 caracteres.", 'bot');
    }
    else if(erro === 'cid nao encontrado'){
        addMessage("Não encontrei o CID informado na minha base de dados. Informe um CID com no mínimo 3 e no máximo 5 caracteres.", 'bot');
    } else {
        addMessage(`Ops! Ocorreu um problema: ${erro}`, 'bot');
    }
}

function closeMapSheet() {
    const sheet   = document.getElementById('map-sheet');
    const overlay = document.getElementById('map-sheet-overlay');
    sheet.classList.remove('open');
    overlay.classList.remove('open');
}

function setupMapSheet() {
    if (document.getElementById('map-sheet')) return; // já existe

    const overlay = document.createElement('div');
    overlay.className = 'map-sheet-overlay';
    overlay.id = 'map-sheet-overlay';

    const sheet = document.createElement('div');
    sheet.className = 'map-sheet';
    sheet.id = 'map-sheet';
    sheet.innerHTML = `
        <div class="map-sheet-handle" id="map-sheet-handle"></div>
        <div class="map-sheet-header">
            <span class="map-sheet-title" id="map-sheet-title">Farmácia</span>
            <button class="map-sheet-close" id="map-sheet-close" aria-label="Fechar">✕</button>
        </div>
        <div class="map-sheet-body" id="map-sheet-body"></div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(sheet);

    // Fechar ao clicar no overlay ou no botão ✕
    overlay.addEventListener('click', closeMapSheet);
    document.getElementById('map-sheet-close').addEventListener('click', closeMapSheet);

    // Fechar com swipe para baixo no handle
    let startY = 0;
    const handle = document.getElementById('map-sheet-handle');
    handle.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
    handle.addEventListener('touchend', e => {
        if (e.changedTouches[0].clientY - startY > 60) closeMapSheet();
    }, { passive: true });
}

function openMapSheet(marker, index) {
    const title  = document.getElementById('map-sheet-title');
    const body   = document.getElementById('map-sheet-body');
    const sheet  = document.getElementById('map-sheet');
    const overlay = document.getElementById('map-sheet-overlay');

    title.textContent = marker.nome || 'Farmácia';

    body.innerHTML = `
        <div class="map-sheet-name">
            <span class="map-sheet-badge">${index + 1}</span>
            ${marker.nome || ''}
        </div>
        ${marker.endereco ? `
        <div class="map-sheet-address">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
            </svg>
            <span>${marker.endereco}</span>
        </div>` : ''}
        ${marker.imagem ? `<img class="map-sheet-img" src="${marker.imagem}" alt="${marker.nome}">` : ''}
    `;

    overlay.classList.add('open');
    // Pequeno delay para a transição funcionar corretamente
    requestAnimationFrame(() => sheet.classList.add('open'));
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
    setupMapSheet();
    checkHealth();
    state = 'CHOOSING_OPTION';
    currentIntent = null;
    lastSearchTerm = null;
    addBotOptions("Olá! Como posso ajudar?", quickOptionsHome);
};

