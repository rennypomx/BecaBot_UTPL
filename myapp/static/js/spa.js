// ======================================================
// SPA Router – Maneja navegación sin recargar toda la app
// ======================================================

// === Restaurar estado del sidebar (colapsado/abierto) ===
function restoreSidebar() {
  const sidebar = document.getElementById("sidebar");
  const isClosed = localStorage.getItem("sidebarCollapsed") === "true";

  if (isClosed && sidebar) {
    sidebar.classList.add("collapsed");
  }
}

// ======================================================
// Inicialización principal del router
// ======================================================
document.addEventListener("DOMContentLoaded", () => {
  restoreSidebar();

  const container = document.getElementById("dynamic-content");
  const currentUrl = window.location.pathname;

  // Si no hay contenido cargado inicialmente, cargar el dashboard
  if (container && !container.querySelector("[data-page]") && container.innerHTML.trim() === '') {
    loadPartial(currentUrl, false);
  }

  // Interceptar clics de navegación
  initNavigationLinks();

  // Botón atrás/adelante del navegador
  window.addEventListener("popstate", (e) => {
    if (e.state && e.state.url) {
      loadPartial(e.state.url, false);
    } else {
      loadPartial(window.location.pathname, false);
    }
  });

  // Establecer estado inicial en el historial
  window.history.replaceState({ url: currentUrl }, '', currentUrl);
});

// ======================================================
// Inicializar enlaces de navegación
// ======================================================
function initNavigationLinks() {
  document.querySelectorAll('a[data-link]').forEach(link => {
    // Remover listeners previos clonando el elemento
    const newLink = link.cloneNode(true);
    link.parentNode.replaceChild(newLink, link);
  });

  document.querySelectorAll('a[data-link]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const url = link.getAttribute('href');
      
      if (url) {
        loadPartial(url, true);
      }
    });
  });
}

// ======================================================
// Cargar contenido dinámico (partials)
// ======================================================
function loadPartial(url, push = true) {
  const container = document.getElementById("dynamic-content");
  
  if (!container) {
    console.error('Contenedor #dynamic-content no encontrado');
    return;
  }

  container.innerHTML = '<p style="text-align:center; padding:40px; opacity:0.7;">⏳ Cargando...</p>';

  fetch(url, { 
    headers: { 
      "X-Requested-With": "XMLHttpRequest" 
    } 
  })
    .then(res => {
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.text();
    })
    .then(html => {
      container.innerHTML = html;

      // Actualizar URL visible
      if (push) {
        window.history.pushState({ url: url }, "", url);
      }

      // Actualizar navegación activa
      setActiveNav(url);

      // Re-inicializar enlaces en el nuevo contenido
      initNavigationLinks();

      // Evento global para otros módulos JS
      document.dispatchEvent(
        new CustomEvent("spa:navigate", { detail: { url } })
      );

      // Ejecutar inicializador auxiliar
      runPageInitializer();

      // Recalcular tamaño (charts, grids, etc.)
      setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    })
    .catch(err => {
      container.innerHTML = `
        <div class="alert alert-danger" style="margin: 20px;">
          <i class="bi bi-exclamation-triangle"></i>
          ⚠️ No se pudo cargar el contenido.
        </div>`;
      console.error("SPA Error:", err);
    });
}

// ======================================================
// Establecer enlace activo en la navegación
// ======================================================
function setActiveNav(url) {
  document.querySelectorAll('.sidebar .nav-link').forEach(link => {
    link.classList.remove('active');
    const linkHref = link.getAttribute('href');
    if (linkHref === url) {
      link.classList.add('active');
    }
  });
}

// ======================================================
// Inicializador auxiliar centralizado
// ======================================================
function runPageInitializer() {
  const pageEl = document.querySelector('#dynamic-content [data-page]');
  if (!pageEl) return;
  
  const pageName = pageEl.dataset.page;
  
  // Aquí otros módulos pueden escuchar spa:navigate
  // y ejecutar sus propias inicializaciones
  console.log('Página cargada:', pageName);
}
