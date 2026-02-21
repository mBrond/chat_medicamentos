const API_BASE_URL = 'http://127.0.0.1:8000'; // Sem barra no final

const messagesDiv = document.getElementById('messages');
const questionInput = document.getElementById('question');
const sendBtn = document.getElementById('send');
const healthIndicator = document.getElementById('health-indicator');

const BOT_AVATAR = '/static/img/pfp_bot.png';
const quickOptionsHome = ['Onde retirar Medicamento', 'Informações com CID', 'Informações com Medicamento'];
const quickOptionsPosConsulta = ['Onde Retirar?', 'Voltar'];

/* ===== ESTADO DO CHAT ===== */
let currentIntent = null; 
let state = 'CHOOSING_OPTION'; 
let lastSearchTerm = null;

/* ===== UTILS ===== */
const delay = ms => new Promise(res => setTimeout(res, ms));

function showTypingIndicator() {
    const typing = document.createElement('div');
    typing.className = 'message bot typing-indicator';
    typing.innerHTML = `<img src="${BOT_AVATAR}" class="avatar"><div class="bubble">Digitando...</div>`;
    messagesDiv.appendChild(typing);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return typing;
}

/* ===== COMUNICAÇÃO COM BACKEND UNIFICADA ===== */
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
        resetToHome();
        return;
    }

    // Mapeamento de Intenções baseadas nos botões
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
            // O estado muda para processando e chama o handler com o termo salvo
            await chatHandler(lastSearchTerm);
        } else {
            // Caso o usuário clique sem ter buscado nada antes
            state = 'WAITING_VALUE';
            currentIntent = 'onde retirar medicamento';
            addMessage("Certo! Digite o nome do medicamento para eu localizar:", 'bot');
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



        console.log("Resposta do backend:", data);
        
        if (data.map_data) {
            addMessage("Encontrei os seguintes locais para retirada:", 'bot', null, null, data.map_data);
            state = 'CHOOSING_OPTION'; 
            await delay(1000);
            addBotOptions("Deseja realizar outra busca?", quickOptionsHome);
        } 
        // Se o backend retornar apenas texto (Resposta de CID ou Medicamento)
        else if (data.answer) {
            addMessage(data.answer, 'bot', data.latency);
            state = 'FINISHED_SEARCH';
            await delay(500);
            addBotOptions("O que deseja fazer agora?", quickOptionsPosConsulta);
        }
        lastSearchTerm = text;

    } catch (error) {
        if(typing) typing.remove();
        addMessage("Desculpe, tive um problema ao consultar essas informações.", 'bot');
        resetToHome();
    } finally {
        state = state === 'PROCESSING' ? 'CHOOSING_OPTION' : state;
    }
}

/* ===== CORE DO CHAT (MENSAGENS) ===== */

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
    
    if (mapData) {
        console.log("Renderizando mapa com dados:", mapData);
        mapa_msg(mapData, bubble);
    }

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

async function sendMessage() {
    const text = questionInput.value.trim();
    if (!text || state === 'PROCESSING') return;

    addMessage(text, 'user');
    questionInput.value = '';

    if (state === 'WAITING_VALUE') {
        await chatHandler(text);
    } else {
        addMessage("Por favor, selecione uma das opções abaixo para começar.", 'bot');
        await delay(500);
        resetToHome();
    }
}

function resetToHome() {
    state = 'CHOOSING_OPTION';
    currentIntent = null;
    addBotOptions("Olá! Sou o assistente do SUS. Como posso ajudar hoje?", quickOptionsHome);
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
questionInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMessage(); });
window.onload = resetToHome;


//mensagens

function mapa_msg(mapData, parentBubble) {
    const mapId = `map-${Date.now()}`;
    const mapDiv = document.createElement('div');
    mapDiv.id = mapId;
    mapDiv.className = 'map-container';
    parentBubble.appendChild(mapDiv);

    setTimeout(() => {
        const map = L.map(mapId);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);


        map.on('popupopen', function(e) {
            const px = map.project(e.target._popup._latlng); // pega a posição do popup
            px.y -= e.target._popup._container.clientHeight / 2; // compensa a altura do balão
            map.panTo(map.unproject(px), { animate: true }); // centraliza suavemente
        });

        const bounds = L.latLngBounds();

        if (mapData.markers && mapData.markers.length > 0) {
            mapData.markers.forEach(m => {
                let popupContent = `<div style="max-width: 200px;">
                    <b style="font-size: 14px;">${m.nome}`;
                
                
                if (m.imagem) {
                    popupContent += `<img src="${m.imagem}" alt="${m.nome}" 
                                    style="width: 100%; height: auto; border-radius: 8px; margin-top: 8px;">`;
                }

                popupContent += `<p style="margin-top: 8px; font-size: 12px;">${m.endereco || ''}</p>
                </div>`;

                const marker = L.marker([m.lat, m.lng])
                    .addTo(map)
                    .bindPopup(popupContent);
                
                bounds.extend(marker.getLatLng());
            });

            

            // 3. Ajustar o mapa para que TODOS os marcadores fiquem visíveis
            if (mapData.markers.length > 1) {
                map.fitBounds(bounds, { padding: [50, 50] });
            } else {
                // Se for apenas um, centraliza normalmente com zoom fixo
                map.setView([mapData.markers[0].lat, mapData.markers[0].lng], 15);
            }
        } else {
            // Caso receba uma lista vazia, usa o centro padrão
            map.setView(mapData.center || [-29.684, -53.806], 13);
        }

        setTimeout(() => { map.invalidateSize(); }, 200);
    }, 0);
}