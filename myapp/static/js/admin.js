// === CSRF Token ===
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

// === Loading Functions ===
function showLoading(text = 'Cargando...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

// === Alert Functions ===
function showAlert(type, message) {
    const alertsContainer = document.getElementById('alerts-container');
    const alertHTML = `
        <div class="alert alert-${type} alert-custom alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    alertsContainer.innerHTML = alertHTML;
    
    setTimeout(() => {
        const alert = alertsContainer.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }
    }, 5000);
}

// ======================================================
// INICIALIZACIÓN DE CONTENIDO ESPECÍFICO DEL ADMIN
// ======================================================
// Este archivo maneja la lógica específica de cada página del admin
// El router SPA está en spa.js

// Escuchar cuando se carga una nueva página
document.addEventListener('spa:navigate', function(e) {
    const url = e.detail.url;
    console.log('Admin: Navegación a', url);
    
    // Inicializar contenido específico según la página
    initPageContent();
});

// También inicializar en la carga inicial
document.addEventListener('DOMContentLoaded', function() {
    initPageContent();
});

// ======================================================
// INICIALIZAR CONTENIDO DE PÁGINA
// ======================================================
function initPageContent() {
    const pageEl = document.querySelector('#dynamic-content [data-page]');
    if (!pageEl) return;
    
    const pageName = pageEl.dataset.page;
    
    switch(pageName) {
        case 'dashboard':
            initDashboard();
            break;
        case 'corpus':
            initCorpus();
            break;
        case 'pdf':
            initPDF();
            break;
        case 'messages':
            initMessages();
            break;
        case 'scraping':
            initScraping();
            break;
    }
}

// ======================================================
// INICIALIZACIÓN DE PÁGINAS ESPECÍFICAS
// ======================================================
function initDashboard() {
    console.log('Inicializando Dashboard...');
    // Aquí iría la lógica para inicializar gráficos del dashboard
    // Por ejemplo: cargar Chart.js, fetch de datos, etc.
}

function initCorpus() {
    console.log('Inicializando Corpus...');
    // Lógica específica de corpus
}

function initPDF() {
    console.log('Inicializando PDF...');
    // Lógica específica de PDFs
}

function initMessages() {
    console.log('Inicializando Messages...');
    // Lógica específica de mensajes
}

function initScraping() {
    console.log('Inicializando Scraping...');
    // Lógica específica de scraping
}

// === Scraping Function ===
// Reemplaza URL_BACKEND_SCRAPING por tu endpoint real
function runScraping() {
    if (confirm('¿Estás seguro de ejecutar el scraping? Esto puede tomar varios minutos.')) {
        showLoading('Ejecutando scraping...');
        
        fetch("URL_BACKEND_SCRAPING", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showAlert('success', data.message);
                setTimeout(() => location.reload(), 2000);
            } else {
                showAlert('danger', data.message);
            }
        })
        .catch(error => {
            hideLoading();
            showAlert('danger', 'Error al ejecutar scraping: ' + error);
        });
    }
}

// === CHART PLACEHOLDERS ===
// Reemplaza estos arrays con tus datos reales

const messagesData = []; 
const messagesCtx = document.getElementById('messagesChart').getContext('2d');
new Chart(messagesCtx, {
    type: 'line',
    data: {
        labels: messagesData.map(d => d.day),
        datasets: [{
            label: 'Mensajes',
            data: messagesData.map(d => d.count),
            borderColor: '#667eea',
            tension: 0.4
        }]
    }
});

// Scraping Chart
const scrapingData = { success: 0, fail: 0 };
const scrapingCtx = document.getElementById('scrapingChart').getContext('2d');
new Chart(scrapingCtx, {
    type: 'doughnut',
    data: {
        labels: ['Exitosos', 'Fallidos'],
        datasets: [{
            data: [scrapingData.success, scrapingData.fail],
            backgroundColor: ['#43e97b', '#f5576c']
        }]
    }
});

// Corpus Chart
const corpusData = [];
const corpusCtx = document.getElementById('corpusChart').getContext('2d');
new Chart(corpusCtx, {
    type: 'bar',
    data: {
        labels: corpusData.map(d => d.corpus_type),
        datasets: [{
            label: 'Cantidad',
            data: corpusData.map(d => d.count),
            backgroundColor: '#667eea'
        }]
    }
});

// PDFs Chart
const pdfsData = [];
const pdfsCtx = document.getElementById('pdfsChart').getContext('2d');
new Chart(pdfsCtx, {
    type: 'bar',
    data: {
        labels: pdfsData.map(d => d.document_type),
        datasets: [{
            label: 'Cantidad',
            data: pdfsData.map(d => d.count),
            backgroundColor: '#f093fb'
        }]
    }
});
