document.addEventListener('DOMContentLoaded', function() {
    const previewImage = document.getElementById('preview-image');
    const refreshIntervalInput = document.getElementById('refresh-interval');
    const refreshValueDisplay = document.getElementById('refresh-value');
    const btnRefreshCameraParams = document.getElementById('btn-refresh-camera-params');
    
    let refreshInterval = parseInt(refreshIntervalInput.value);
    let refreshTimer = null;
    let isPageVisible = true;
    
    // Mise à jour de l'affichage de l'intervalle
    refreshIntervalInput.addEventListener('input', function() {
        refreshInterval = parseInt(this.value);
        refreshValueDisplay.textContent = refreshInterval;
        restartRefreshTimer();
    });
    
    // Fonction pour rafraîchir l'aperçu
    function refreshPreview() {
        if (!isPageVisible) return;
        
        // Ajouter timestamp pour éviter le cache
        previewImage.src = `/api/capture/preview?t=${Date.now()}`;
    }
    
    // Fonction pour démarrer/redémarrer le timer
    function restartRefreshTimer() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        refreshTimer = setInterval(refreshPreview, refreshInterval * 1000);
    }
    
    // Détecter la visibilité de la page
    document.addEventListener('visibilitychange', function() {
        isPageVisible = document.visibilityState === 'visible';
        
        if (isPageVisible) {
            // Rafraîchir immédiatement et redémarrer le timer quand la page devient visible
            refreshPreview();
            restartRefreshTimer();
        } else {
            // Arrêter le timer quand la page n'est pas visible
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
        }
    });
    
    // Chargement des paramètres de la caméra
    function loadCameraParams() {
        const loadingElement = document.getElementById('camera-params-loading');
        const errorElement = document.getElementById('camera-params-error');
        const displayElement = document.getElementById('camera-params-display');
        
        // Afficher l'indicateur de chargement
        loadingElement.classList.remove('d-none');
        errorElement.classList.add('d-none');
        displayElement.classList.add('d-none');
        
        // Appel à l'API pour récupérer les paramètres
        fetch('/api/settings/params')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur lors de la récupération des paramètres');
                }
                return response.json();
            })
            .then(data => {
                // Masquer l'indicateur de chargement
                loadingElement.classList.add('d-none');
                displayElement.classList.remove('d-none');
                
                // Afficher les informations de format et résolution
                if (data.resolution) {
                    const format = data.resolution.format || '-';
                    const width = data.resolution.width || 0;
                    const height = data.resolution.height || 0;
                    
                    document.getElementById('camera-format').textContent = format;
                    document.getElementById('camera-resolution').textContent = `${width} x ${height}`;
                }
                
                // Afficher les contrôles
                if (data.controls) {
                    for (const [name, info] of Object.entries(data.controls)) {
                        const paramElement = document.getElementById(`param-${name}`);
                        if (paramElement) {
                            paramElement.textContent = info.value;
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                loadingElement.classList.add('d-none');
                errorElement.classList.remove('d-none');
                errorElement.textContent = `Impossible de charger les paramètres: ${error.message}`;
            });
    }
    
    // Bouton de rafraîchissement des paramètres
    if (btnRefreshCameraParams) {
        btnRefreshCameraParams.addEventListener('click', loadCameraParams);
    }
    
    // Charger les paramètres au chargement de la page
    loadCameraParams();
    
    // Démarrer le timer initial et charger l'aperçu
    refreshPreview();
    restartRefreshTimer();
});