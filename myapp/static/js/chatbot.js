/* =====================================================
   CHATBOT – LÓGICA COMPLETA Y OPTIMIZADA CON DJANGO
===================================================== */

/* ============================
   REFERENCIAS DEL DOM
============================ */
const chatBtn = document.getElementById("chatbot-btn");
const chatBox = document.getElementById("chatbot-box");
const closeBtn = document.getElementById("chatbot-close");
const messages = document.getElementById("chatbot-messages");

const input = document.getElementById("chatbot-input");
const sendBtn = document.getElementById("chatbot-send");
const voiceBtn = document.getElementById("chatbot-voice");

// Control para mensaje de bienvenida
let greeted = false;

/* ============================
   OBTENER CSRF TOKEN (Django)
============================ */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

/* ============================
   OBTENER HORA ACTUAL
============================ */
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ============================
   TOGGLE DEL CHATBOT
============================ */
chatBtn.addEventListener("click", () => {
    const isOpen = chatBox.style.display === "flex";

    if (isOpen) {
        chatBox.style.display = "none";
    } else {
        chatBox.style.display = "flex";

        if (!greeted) {
            setTimeout(() => {
                addMessage(
                    "👋 ¡Hola! Soy el Asistente Virtual de Becas UTPL. Estoy aquí para ayudarte con postulación, renovación, requisitos o cualquier consulta. ¿En qué puedo ayudarte hoy?",
                    "bot"
                );
            }, 300);

            greeted = true;
        }
    }
});

closeBtn.addEventListener("click", () => {
    chatBox.style.display = "none";
});

/* ============================
   CONVERTIR MARKDOWN A HTML
============================ */
function markdownToHtml(text) {
    if (!text) return '';
    
    // Convertir negritas **texto** a <strong>texto</strong>
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convertir listas con * al inicio de línea
    let lines = text.split('\n');
    let inList = false;
    let html = '';
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Detectar inicio de lista (línea que empieza con *)
        if (line.startsWith('* ')) {
            if (!inList) {
                html += '<ul style="margin: 10px 0; padding-left: 20px;">';
                inList = true;
            }
            // Remover el asterisco y espacios del inicio
            let listItem = line.substring(2).trim();
            html += '<li style="margin: 5px 0;">' + listItem + '</li>';
        } else {
            // Fin de la lista
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            // Línea normal
            if (line) {
                html += '<p style="margin: 5px 0;">' + line + '</p>';
            }
        }
    }
    
    // Cerrar lista si quedó abierta
    if (inList) {
        html += '</ul>';
    }
    
    return html;
}

/* ============================
   FUNCIÓN PARA CREAR MENSAJES
============================ */
function addMessage(text, sender = "bot") {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", sender); 

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");

    // Avatar según el remitente (usar archivos estáticos de Django)
    avatar.src = sender === "bot" ? "/static/img/bot.png" : "/static/img/user.png";

    const msg = document.createElement("div");
    msg.classList.add("message", sender);

    // Contenido del mensaje - convertir Markdown a HTML
    const content = document.createElement("div");
    const htmlContent = sender === "bot" ? markdownToHtml(text) : text;
    content.innerHTML = htmlContent;

    // Hora del mensaje
    const time = document.createElement("span");
    time.classList.add("timestamp");
    time.textContent = getCurrentTime();

    msg.appendChild(content);
    msg.appendChild(time);

    // Organización del wrapper según remitente
    if (sender === "bot") {
        wrapper.appendChild(avatar);
        wrapper.appendChild(msg);
    } else {
        wrapper.appendChild(msg);
        wrapper.appendChild(avatar);
    }

    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
}

/* ============================
   MOSTRAR INDICADOR DE CARGA
============================ */
function showTypingIndicator() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", "bot", "typing-indicator");
    wrapper.id = "typing-indicator";

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = "/static/img/bot.png";

    const dots = document.createElement("div");
    dots.classList.add("typing-dots");
    dots.innerHTML = '<span></span><span></span><span></span>';

    wrapper.appendChild(avatar);
    wrapper.appendChild(dots);
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) {
        indicator.remove();
    }
}

/* ============================
   ENVIAR MENSAJE VIA AJAX (Django)
============================ */
async function sendMessage() {
    const text = input.value.trim();
    if (text === "") return;
    
    // Reiniciar timer de inactividad
    resetInactivityTimer();
    
    // Mostrar mensaje del usuario
    addMessage(text, "user");
    input.value = "";
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        // Enviar mensaje via AJAX POST a Django
        const response = await fetch('/send-message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `message=${encodeURIComponent(text)}`
        });
        
        const data = await response.json();
        
        // Remover indicador de escritura
        removeTypingIndicator();
        
        if (data.success) {
            // Mostrar respuesta del bot
            addMessage(data.response, "bot");
            
            // Reiniciar timer después de la respuesta del bot
            resetInactivityTimer();
            
            // Mostrar fuentes si existen
            if (data.sources) {
                let sourcesText = "<br><small><strong>Fuentes consultadas:</strong></small>";
                
                // PDFs
                if (data.sources.pdf_sources && Object.keys(data.sources.pdf_sources).length > 0) {
                    sourcesText += "<br><small>📄 Documentos: ";
                    const pdfList = Object.entries(data.sources.pdf_sources)
                        .map(([name, pages]) => `${name} (p.${pages.join(',')})`)
                        .join(", ");
                    sourcesText += pdfList + "</small>";
                }
                
                // Web
                if (data.sources.web_sources && Object.keys(data.sources.web_sources).length > 0) {
                    sourcesText += "<br><small>🌐 Base de becas UTPL</small>";
                }
                
                // Descomentar para mostrar fuentes
                // addMessage(sourcesText, "bot");
            }
        } else {
            // Error del servidor
            addMessage("⚠️ " + (data.error || "Hubo un error al procesar tu consulta."), "bot");
        }
        
    } catch (error) {
        removeTypingIndicator();
        console.error('❌ Error al enviar mensaje:', error);
        addMessage("❌ Error de conexión. Por favor intenta de nuevo.", "bot");
    }
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

/* ============================
   RECONOCIMIENTO DE VOZ
============================ */
let recognition;
let recognizing = false;

// Validar soporte del navegador
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    // Usar el prefijo correcto según el navegador
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    // Configuración mejorada
    recognition.lang = "es-ES"; // Español de España
    recognition.continuous = false; // Detener después de una frase
    recognition.interimResults = true; // Mostrar resultados parciales
    recognition.maxAlternatives = 1; // Solo la mejor alternativa
    
    // Evento: Al iniciar el reconocimiento
    recognition.onstart = () => {
        console.log("🎤 Reconocimiento de voz iniciado");
        recognizing = true;
        voiceBtn.classList.add("listening");
        voiceBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        voiceBtn.title = "Escuchando... (haz clic para detener)";
    };
    
    // Evento: Al finalizar el reconocimiento
    recognition.onend = () => {
        console.log("🎤 Reconocimiento de voz finalizado");
        recognizing = false;
        voiceBtn.classList.remove("listening");
        voiceBtn.innerHTML = '<i class="bi bi-mic"></i>';
        voiceBtn.title = "Usar voz";
    };
    
    // Evento: Resultados del reconocimiento
    recognition.onresult = (event) => {
        let transcript = "";
        
        // Obtener todos los resultados
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
            } else {
                // Resultados parciales (mientras hablas)
                const interim = event.results[i][0].transcript;
                input.value = interim;
                console.log("🎤 Resultado parcial:", interim);
            }
        }
        
        // Resultado final
        if (transcript) {
            console.log("🎤 Resultado final:", transcript);
            input.value = transcript;
            
            // Enviar automáticamente después de 500ms
            setTimeout(() => {
                if (input.value.trim()) {
                    sendMessage();
                }
            }, 500);
        }
    };
    
    // Evento: Errores
    recognition.onerror = (event) => {
        console.error("❌ Error de reconocimiento de voz:", event.error);
        recognizing = false;
        voiceBtn.classList.remove("listening");
        voiceBtn.innerHTML = '<i class="bi bi-mic"></i>';
        
        let errorMsg = "Error en el reconocimiento de voz";
        switch (event.error) {
            case "no-speech":
                errorMsg = "No se detectó ningún audio. Intenta hablar más cerca del micrófono.";
                break;
            case "audio-capture":
                errorMsg = "No se detectó micrófono. Verifica que esté conectado.";
                break;
            case "not-allowed":
                errorMsg = "Permiso denegado. Permite el acceso al micrófono en tu navegador.";
                break;
            case "network":
                errorMsg = "Error de red. Verifica tu conexión a internet.";
                break;
            case "aborted":
                console.log("Reconocimiento cancelado por el usuario");
                return; // No mostrar alerta si el usuario canceló
            default:
                errorMsg = `Error: ${event.error}`;
        }
        
        // Solo mostrar alerta si es un error importante
        if (event.error !== "aborted") {
            alert(errorMsg);
        }
    };
    
    // Evento: No se obtuvo resultado
    recognition.onnomatch = () => {
        console.warn("⚠️ No se reconoció ninguna palabra");
        alert("No se pudo entender lo que dijiste. Por favor, intenta de nuevo hablando más claro.");
    };
    
    console.log("✅ Reconocimiento de voz configurado correctamente");
} else {
    console.warn("⚠️ El navegador no soporta reconocimiento de voz.");
}

// Botón de voz
voiceBtn.addEventListener("click", () => {
    if (!recognition) {
        alert("Tu navegador no soporta entrada de voz. Usa Chrome, Edge o Safari para esta funcionalidad.");
        return;
    }

    if (recognizing) {
        console.log("🛑 Deteniendo reconocimiento de voz");
        recognition.stop();
    } else {
        console.log("▶️ Iniciando reconocimiento de voz");
        try {
            recognition.start();
        } catch (error) {
            console.error("❌ Error al iniciar reconocimiento:", error);
            alert("No se pudo iniciar el reconocimiento de voz. Asegúrate de dar permiso al micrófono.");
        }
    }
});

/* ============================
   GESTIÓN DE SESIONES Y TIMEOUT
============================ */
let sessionTimeout = null;
const INACTIVITY_TIMEOUT = 2 * 60 * 1000; // 2 minutos en milisegundos
let sessionActive = true;

// Reiniciar el temporizador de inactividad
function resetInactivityTimer() {
    // Limpiar temporizador anterior
    if (sessionTimeout) {
        clearTimeout(sessionTimeout);
    }
    
    // Solo crear nuevo timeout si la sesión está activa
    if (sessionActive) {
        sessionTimeout = setTimeout(() => {
            handleSessionTimeout();
        }, INACTIVITY_TIMEOUT);
        
        console.log("⏱️ Temporizador de inactividad reiniciado (2 minutos)");
    }
}

// Manejar el timeout de la sesión
async function handleSessionTimeout() {
    console.log("⏰ Sesión inactiva por 2 minutos, cerrando conversación...");
    
    sessionActive = false;
    
    // Mensaje de despedida del bot
    addMessage(
        "👋 He notado que has estado inactivo. Por motivos de seguridad y eficiencia, voy a cerrar esta conversación. Si necesitas más ayuda, no dudes en escribirme de nuevo. ¡Que tengas un excelente día!",
        "bot"
    );
    
    // Esperar 2 segundos para que el usuario vea el mensaje
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Limpiar la conversación en el backend
    try {
        await clearConversation();
        console.log("✅ Conversación limpiada por inactividad");
    } catch (error) {
        console.error("❌ Error al limpiar conversación:", error);
    }
    
    // Marcar que se puede iniciar nueva sesión
    sessionActive = true;
    greeted = false;
}

// Función para limpiar la conversación
async function clearConversation() {
    try {
        const response = await fetch('/clear-chat/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Limpiar mensajes del DOM (excepto la despedida)
            const messagesToRemove = messages.querySelectorAll('.message-wrapper');
            // Mantener solo el último mensaje (despedida)
            for (let i = 0; i < messagesToRemove.length - 1; i++) {
                messagesToRemove[i].remove();
            }
            
            console.log("🗑️ Historial limpiado exitosamente");
        }
        
        return data;
    } catch (error) {
        console.error("❌ Error al limpiar conversación:", error);
        throw error;
    }
}

// Monitorear actividad del usuario
function monitorUserActivity() {
    // Resetear timer cuando el usuario escribe
    input.addEventListener('input', () => {
        if (sessionActive) {
            resetInactivityTimer();
        }
    });
    
    // Resetear timer cuando el usuario hace clic en el chat
    chatBox.addEventListener('click', () => {
        if (sessionActive) {
            resetInactivityTimer();
        }
    });
    
    // Resetear timer cuando se envía un mensaje
    sendBtn.addEventListener('click', () => {
        if (sessionActive) {
            resetInactivityTimer();
        }
    });
    
    console.log("👁️ Monitoreo de actividad iniciado");
}

// Iniciar monitoreo cuando se abre el chat
chatBtn.addEventListener("click", () => {
    const isOpen = chatBox.style.display === "flex";
    
    if (!isOpen) {
        // Si se está abriendo el chat, iniciar el timer
        resetInactivityTimer();
    } else {
        // Si se está cerrando, pausar el timer
        if (sessionTimeout) {
            clearTimeout(sessionTimeout);
            console.log("⏸️ Temporizador pausado (chat cerrado)");
        }
    }
});

// Iniciar monitoreo al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    monitorUserActivity();
    console.log("✅ Sistema de gestión de sesiones inicializado");
});

/* ============================
   CARGAR HISTORIAL AL INICIAR (OPCIONAL)
============================ */
async function loadChatHistory() {
    try {
        const response = await fetch('/get-chat-history/');
        const data = await response.json();
        
        if (data.success && data.messages) {
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role === 'human' ? 'user' : 'bot');
            });
        }
    } catch (error) {
        console.log('No se pudo cargar el historial:', error);
    }
}

// Descomentar si quieres cargar historial al abrir el chat
// chatBtn.addEventListener("click", () => {
//     if (!greeted) {
//         loadChatHistory();
//     }
// });
