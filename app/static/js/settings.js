document.addEventListener('DOMContentLoaded', function() {
    const previewImage = document.getElementById('preview-image');
    const refreshIntervalInput = document.getElementById('refresh-interval');
    const refreshValueDisplay = document.getElementById('refresh-value');
    
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
    
    // Démarrer le timer initial et charger l'aperçu
    refreshPreview();
    restartRefreshTimer();
});
