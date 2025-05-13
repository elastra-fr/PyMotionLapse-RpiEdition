document.addEventListener('DOMContentLoaded', function() {
    const previewImage = document.getElementById('preview-image');
    const refreshIntervalInput = document.getElementById('refresh-interval');
    const refreshValueDisplay = document.getElementById('refresh-value');
    const btnRefreshCameraParams = document.getElementById('btn-refresh-camera-params');
    const resolutionSelect = document.getElementById('resolution-select');
    
    // Variables pour le suivi de l'état
    let refreshInterval = parseInt(refreshIntervalInput.value);
    let refreshTimer = null;
    let isPageVisible = true;
    let currentResolution = '';
    
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
                    
                    // Sélectionner automatiquement la résolution actuelle
                    const newResolution = `${width}x${height}`;
                    if (currentResolution !== newResolution) {
                        currentResolution = newResolution;
                        
                        // Trouver et sélectionner l'option correspondante sans déclencher d'événement
                        for (const option of resolutionSelect.options) {
                            if (option.value === currentResolution) {
                                option.selected = true;
                                break;
                            }
                        }
                    }
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
    
    // Gestionnaire d'événement pour le changement de résolution
    function handleResolutionChange() {
        const resolution = resolutionSelect.value;
        
        // Ne rien faire si la résolution actuelle est déjà sélectionnée
        if (resolution === currentResolution) {
            return;
        }
        
        // Extraire largeur et hauteur
        const [width, height] = resolution.split('x').map(Number);
        
        // Afficher un message temporaire près du sélecteur
        const statusElement = document.createElement('div');
        statusElement.className = 'alert alert-info mt-2';
        statusElement.textContent = 'Modification de la résolution en cours...';
        resolutionSelect.parentNode.appendChild(statusElement);
        
        // Préparer les données
        const data = {
            width: width,
            height: height,
            fps: 30,  // Par défaut
            format: 'MJPG'  // Format fixe pour cette caméra
        };
        
        // Appeler l'API pour changer la résolution
        fetch('/api/settings/resolution', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors de la modification de la résolution');
            }
            return response.json();
        })
        .then(result => {
            // Mise à jour du message
            statusElement.className = 'alert alert-success mt-2';
            statusElement.textContent = 'Résolution modifiée avec succès!';
            
            // Mettre à jour la résolution actuelle
            currentResolution = resolution;
            
            // Rafraîchir l'aperçu et les paramètres après un court délai
            setTimeout(() => {
                refreshPreview();
                loadCameraParams();
                
                // Supprimer le message après quelques secondes
                setTimeout(() => {
                    statusElement.remove();
                }, 3000);
            }, 1000);
        })
        .catch(error => {
            // Afficher l'erreur
            statusElement.className = 'alert alert-danger mt-2';
            statusElement.textContent = `Erreur: ${error.message}`;
            console.error('Erreur lors de la modification de la résolution:', error);
            
            // Restaurer la sélection précédente
            for (const option of resolutionSelect.options) {
                if (option.value === currentResolution) {
                    option.selected = true;
                    break;
                }
            }
            
            // Supprimer le message d'erreur après un délai plus long
            setTimeout(() => {
                statusElement.remove();
            }, 5000);
        });
    }
    
    // Ajouter un écouteur d'événement sur le changement de résolution
    if (resolutionSelect) {
        resolutionSelect.addEventListener('change', handleResolutionChange);
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

document.addEventListener('DOMContentLoaded', function() {

let rotation = 0;
const previewImage = document.getElementById('preview-image');
const btnRotation = document.getElementById('btn-rotation');

// Charger la rotation depuis le localStorage si présente
if (localStorage.getItem('previewRotation')) {
    rotation = parseInt(localStorage.getItem('previewRotation'), 10) || 0;
    if (previewImage) {
        previewImage.style.transform = `rotate(${rotation}deg)`;
    }
}

if (btnRotation && previewImage) {
    btnRotation.addEventListener('click', function(e) {
        e.preventDefault();
        rotation = (rotation + 90) % 360;
        previewImage.style.transform = `rotate(${rotation}deg)`;
        localStorage.setItem('previewRotation', rotation);
    });
}

// Quand l'image est rechargée, réappliquer la rotation
if (previewImage) {
    previewImage.addEventListener('load', function() {
        previewImage.style.transform = `rotate(${rotation}deg)`;
    });
}


});