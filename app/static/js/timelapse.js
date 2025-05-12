document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const projectsList = document.getElementById('projects-list');
    const newProjectForm = document.getElementById('new-project-form');
    const editProjectForm = document.getElementById('edit-project-form');
    const projectDetails = document.getElementById('project-details');
    const previewImage = document.getElementById('preview-image');
    const refreshInterval = document.getElementById('refresh-interval');
    const deleteModal = new bootstrap.Modal(document.getElementById('delete-project-modal'));
    const captureBtn = document.getElementById('capture-button');
    
    // État de l'application
    let currentProjectId = null;
    let refreshTimer = null;
    let isPageVisible = true;
    
    // Paramètres initiaux
    const initialRefreshSeconds = 5;
    
    // Fonctions utilitaires
    function showElement(element) {
        if (element) element.classList.remove('d-none');
    }
    
    function hideElement(element) {
        if (element) element.classList.add('d-none');
    }
    
    function showLoading(container) {
        // Ajouter un spinner à l'élément spécifié
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner text-center my-5';
        spinner.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
            <p class="mt-2">Chargement en cours...</p>
        `;
        
        // Vider le conteneur et ajouter le spinner
        if (container) {
            container.innerHTML = '';
            container.appendChild(spinner);
        }
    }
    
    function showError(container, message) {
        // Afficher un message d'erreur dans l'élément spécifié
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger';
        errorAlert.textContent = message || 'Une erreur est survenue';
        
        // Vider le conteneur et ajouter l'alerte
        if (container) {
            container.innerHTML = '';
            container.appendChild(errorAlert);
        }
    }
    
    // Fonction pour formater la durée en format lisible
    function formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds} secondes`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes} min ${remainingSeconds} s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const remainingMinutes = Math.floor((seconds % 3600) / 60);
            return `${hours} h ${remainingMinutes} min`;
        }
    }
    
    // Fonction pour charger tous les projets
    function loadProjects() {
        showLoading(projectsList);
        
        fetch('/api/timelapse/projects')
            .then(response => {
                if (!response.ok) throw new Error('Impossible de récupérer les projets');
                return response.json();
            })
            .then(projects => {
                renderProjectsList(projects);
            })
            .catch(error => {
                console.error('Erreur:', error);
                showError(projectsList, 'Impossible de charger les projets: ' + error.message);
            });
    }
    
    // Fonction pour afficher la liste des projets
    function renderProjectsList(projects) {
        if (!projectsList) return;
        
        projectsList.innerHTML = '';
        
        if (projects.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'text-center my-5';
            emptyState.innerHTML = `
                <i class="fas fa-folder-open fa-3x text-muted mb-3"></i>
                <p class="lead">Aucun projet time-lapse existant</p>
                <p>Créez votre premier projet en utilisant le formulaire</p>
            `;
            projectsList.appendChild(emptyState);
            return;
        }
        
        // Créer un élément de liste pour chaque projet
        projects.forEach(project => {
            const projectItem = document.createElement('div');
            projectItem.className = 'card mb-3';
            projectItem.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${project.name}</h5>
                    <p class="card-text">
                        <small class="text-muted">
                            Créé le ${new Date(project.created_at).toLocaleString()}
                        </small>
                    </p>
                    <div class="progress mb-3" style="height: 10px;">
                        <div class="progress-bar" role="progressbar" 
                            style="width: ${project.completion_percentage}%;" 
                            aria-valuenow="${project.completion_percentage}" 
                            aria-valuemin="0" aria-valuemax="100">
                        </div>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Captures: ${project.captures_count}/${project.total_captures}</span>
                        <span>${Math.round(project.completion_percentage)}% terminé</span>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <button class="btn btn-primary btn-sm load-project" data-id="${project.id}">
                        <i class="fas fa-edit me-1"></i>Ouvrir
                    </button>
                    <button class="btn btn-danger btn-sm delete-project" data-id="${project.id}" data-name="${project.name}">
                        <i class="fas fa-trash me-1"></i>Supprimer
                    </button>
                </div>
            `;
            
            // Ajouter des écouteurs d'événements aux boutons
            const loadBtn = projectItem.querySelector('.load-project');
            const deleteBtn = projectItem.querySelector('.delete-project');
            
            loadBtn.addEventListener('click', function() {
                loadProjectDetails(this.dataset.id);
            });
            
            deleteBtn.addEventListener('click', function() {
                const projectId = this.dataset.id;
                const projectName = this.dataset.name;
                
                // Configurer la modal de confirmation
                document.getElementById('delete-project-name').textContent = projectName;
                document.getElementById('confirm-delete-btn').dataset.id = projectId;
                
                // Afficher la modal
                deleteModal.show();
            });
            
            projectsList.appendChild(projectItem);
        });
    }
    
    // Fonction pour charger les détails d'un projet
    function loadProjectDetails(projectId) {
        if (!projectId) return;
        
        currentProjectId = projectId;
        showLoading(projectDetails);
        
        // Afficher la section des détails
        showElement(projectDetails);
        
        // Masquer le formulaire de création de projet
        hideElement(newProjectForm);
        
        fetch(`/api/timelapse/projects/${projectId}`)
            .then(response => {
                if (!response.ok) throw new Error('Impossible de récupérer les détails du projet');
                return response.json();
            })
            .then(project => {
                renderProjectDetails(project);
                startPreviewRefresh(projectId);
            })
            .catch(error => {
                console.error('Erreur:', error);
                showError(projectDetails, 'Impossible de charger les détails du projet: ' + error.message);
            });
    }
    
    // Fonction pour afficher les détails d'un projet
    function renderProjectDetails(project) {
        if (!projectDetails) return;
        
        // Calculer les informations dérivées
        const totalCaptures = project.total_captures;
        const videoDuration = formatDuration(project.video_duration_seconds);
        
        // Mettre à jour les détails du projet
        projectDetails.innerHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3>${project.name}</h3>
                    <div>
                        <button id="edit-project-btn" class="btn btn-primary btn-sm">
                            <i class="fas fa-edit me-1"></i>Modifier
                        </button>
                        <button id="back-to-list-btn" class="btn btn-secondary btn-sm">
                            <i class="fas fa-arrow-left me-1"></i>Retour
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <!-- Aperçu de la caméra -->
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h5 class="mb-0">Aperçu</h5>
                                </div>
                                <div class="card-body text-center">
                                    <div class="position-relative">
                                        <img id="preview-image" src="/api/timelapse/projects/${project.id}/preview" 
                                             alt="Aperçu" class="img-fluid mb-2" 
                                             style="max-height: 300px; width: auto;">
                                        <div class="position-absolute top-0 end-0 m-2">
                                            <div class="form-group">
                                                <label for="refresh-interval">Rafraîchir: <span id="refresh-value">${initialRefreshSeconds}</span>s</label>
                                                <input type="range" class="form-range" id="refresh-interval" 
                                                       min="1" max="20" value="${initialRefreshSeconds}">
                                            </div>
                                        </div>
                                    </div>
                                    <button id="capture-button" class="btn btn-success mt-2">
                                        <i class="fas fa-camera me-1"></i>Capturer
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informations du projet -->
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h5 class="mb-0">Informations</h5>
                                </div>
                                <div class="card-body">
                                    <ul class="list-group list-group-flush">
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Durée totale:</span>
                                            <span>${project.duration_minutes} minutes</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Intervalle de capture:</span>
                                            <span>${project.interval_seconds} secondes</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Images par seconde (fps):</span>
                                            <span>${project.fps} fps</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Rotation de la caméra:</span>
                                            <span>${project.rotation}°</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Nombre total de captures:</span>
                                            <span>${totalCaptures}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Durée estimée de la vidéo:</span>
                                            <span>${videoDuration}</span>
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between align-items-center">
                                            <span>Captures effectuées:</span>
                                            <span>${project.captures_count} / ${totalCaptures}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            
                            <!-- Progression -->
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Progression</h5>
                                </div>
                                <div class="card-body">
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar" role="progressbar" 
                                             style="width: ${project.completion_percentage}%;" 
                                             aria-valuenow="${project.completion_percentage}" 
                                             aria-valuemin="0" aria-valuemax="100">
                                             ${Math.round(project.completion_percentage)}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Ajouter les écouteurs d'événements
        document.getElementById('back-to-list-btn').addEventListener('click', function() {
            stopPreviewRefresh();
            hideElement(projectDetails);
            showElement(newProjectForm);
            currentProjectId = null;
        });
        
        document.getElementById('edit-project-btn').addEventListener('click', function() {
            setupEditForm(project);
        });
        
        document.getElementById('capture-button').addEventListener('click', function() {
            captureImage(project.id);
        });
        
        const refreshIntervalInput = document.getElementById('refresh-interval');
        const refreshValueDisplay = document.getElementById('refresh-value');
        
        refreshIntervalInput.addEventListener('input', function() {
            const refreshInterval = parseInt(this.value);
            refreshValueDisplay.textContent = refreshInterval;
            restartPreviewRefresh(project.id, refreshInterval);
        });
    }
    
    // Fonction pour configurer le formulaire d'édition
    function setupEditForm(project) {
        if (!editProjectForm) return;
        
        // Remplir le formulaire avec les valeurs actuelles
        const form = editProjectForm.querySelector('form');
        form.dataset.id = project.id;
        form.elements.name.value = project.name;
        form.elements.duration.value = project.duration_minutes;
        form.elements.interval.value = project.interval_seconds;
        form.elements.fps.value = project.fps;
        
        // Sélectionner la bonne option de rotation
        const rotationOptions = form.elements.rotation.options;
        for (let i = 0; i < rotationOptions.length; i++) {
            if (parseInt(rotationOptions[i].value) === project.rotation) {
                rotationOptions[i].selected = true;
                break;
            }
        }
        
        // Afficher le formulaire d'édition dans une modale
        const editModal = new bootstrap.Modal(editProjectForm);
        editModal.show();
    }
    
    // Fonction pour démarrer le rafraîchissement de l'aperçu
    function startPreviewRefresh(projectId, interval = initialRefreshSeconds) {
        // Arrêter tout timer existant
        stopPreviewRefresh();
        
        // Démarrer un nouveau timer
        refreshTimer = setInterval(function() {
            if (!isPageVisible || !currentProjectId) return;
            
            const previewImage = document.getElementById('preview-image');
            if (previewImage) {
                previewImage.src = `/api/timelapse/projects/${projectId}/preview?t=${Date.now()}`;
            }
        }, interval * 1000);
    }
    
    // Fonction pour arrêter le rafraîchissement de l'aperçu
    function stopPreviewRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }
    
    // Fonction pour redémarrer le timer avec un nouvel intervalle
    function restartPreviewRefresh(projectId, interval) {
        stopPreviewRefresh();
        startPreviewRefresh(projectId, interval);
    }
    
    // Fonction pour capturer une image
    function captureImage(projectId) {
        if (!projectId) return;
        
        const captureBtn = document.getElementById('capture-button');
        
        // Désactiver le bouton pendant la capture
        if (captureBtn) {
            captureBtn.disabled = true;
            captureBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Capture en cours...';
        }
        
        fetch(`/api/timelapse/projects/${projectId}/capture`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) throw new Error('Échec de la capture');
            return response.json();
        })
        .then(data => {
            // Mise à jour réussie, recharger les détails du projet
            loadProjectDetails(projectId);
            
            // Afficher une notification de succès
            const alert = document.createElement('div');
            alert.className = 'alert alert-success alert-dismissible fade show';
            alert.innerHTML = `
                <strong>Capture réussie!</strong> ${data.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
            `;
            
            document.querySelector('.container').prepend(alert);
            
            // Supprimer l'alerte après quelques secondes
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 500);
            }, 3000);
        })
        .catch(error => {
            console.error('Erreur:', error);
            
            // Afficher une notification d'erreur
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                <strong>Erreur!</strong> Impossible de capturer l'image: ${error.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
            `;
            
            document.querySelector('.container').prepend(alert);
        })
        .finally(() => {
            // Réactiver le bouton de capture
            if (captureBtn) {
                captureBtn.disabled = false;
                captureBtn.innerHTML = '<i class="fas fa-camera me-1"></i>Capturer';
            }
        });
    }
    
    // Écouteurs d'événements pour la visibilité de la page
    document.addEventListener('visibilitychange', function() {
        isPageVisible = document.visibilityState === 'visible';
        
        if (isPageVisible && currentProjectId) {
            // Rafraîchir l'aperçu immédiatement lorsque la page redevient visible
            const previewImage = document.getElementById('preview-image');
            if (previewImage) {
                previewImage.src = `/api/timelapse/projects/${currentProjectId}/preview?t=${Date.now()}`;
            }
            
            // Redémarrer le timer si nécessaire
            const refreshIntervalInput = document.getElementById('refresh-interval');
            if (refreshIntervalInput) {
                restartPreviewRefresh(currentProjectId, parseInt(refreshIntervalInput.value));
            }
        } else {
            // Arrêter le timer lorsque la page n'est pas visible
            stopPreviewRefresh();
        }
    });
    
    // Écouteur d'événement pour la soumission du formulaire de création
    if (newProjectForm) {
        const form = newProjectForm.querySelector('form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/api/timelapse/projects', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) throw new Error('Échec de la création du projet');
                return response.json();
            })
            .then(project => {
                // Afficher une notification de succès
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Projet créé!</strong> Le projet "${project.name}" a été créé avec succès.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                document.querySelector('.container').prepend(alert);
                
                // Recharger la liste des projets
                loadProjects();
                
                // Réinitialiser le formulaire
                form.reset();
            })
            .catch(error => {
                console.error('Erreur:', error);
                
                // Afficher une notification d'erreur
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Erreur!</strong> Impossible de créer le projet: ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                document.querySelector('.container').prepend(alert);
            });
        });
    }
    
    // Écouteur d'événement pour la soumission du formulaire d'édition
    if (editProjectForm) {
        const form = editProjectForm.querySelector('form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const projectId = this.dataset.id;
            const formData = new FormData(this);
            
            fetch(`/api/timelapse/projects/${projectId}`, {
                method: 'PUT',
                body: formData
            })
            .then(response => {
                if (!response.ok) throw new Error('Échec de la mise à jour du projet');
                return response.json();
            })
            .then(project => {
                // Fermer la modale
                bootstrap.Modal.getInstance(editProjectForm).hide();
                
                // Afficher une notification de succès
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Projet mis à jour!</strong> Les modifications ont été enregistrées.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                document.querySelector('.container').prepend(alert);
                
                // Recharger les détails du projet
                loadProjectDetails(projectId);
                
                // Recharger la liste des projets
                loadProjects();
            })
            .catch(error => {
                console.error('Erreur:', error);
                
                // Afficher une notification d'erreur
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Erreur!</strong> Impossible de mettre à jour le projet: ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                editProjectForm.querySelector('.modal-body').prepend(alert);
            });
        });
    }
    
    // Écouteur d'événement pour la confirmation de suppression
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const projectId = this.dataset.id;
            
            fetch(`/api/timelapse/projects/${projectId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) throw new Error('Échec de la suppression du projet');
                return response.json();
            })
            .then(data => {
                // Fermer la modale
                deleteModal.hide();
                
                // Afficher une notification de succès
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Projet supprimé!</strong> ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                document.querySelector('.container').prepend(alert);
                
                // Si le projet supprimé est le projet courant, revenir à la liste
                if (currentProjectId === projectId) {
                    stopPreviewRefresh();
                    hideElement(projectDetails);
                    showElement(newProjectForm);
                    currentProjectId = null;
                }
                
                // Recharger la liste des projets
                loadProjects();
            })
            .catch(error => {
                console.error('Erreur:', error);
                
                // Fermer la modale
                deleteModal.hide();
                
                // Afficher une notification d'erreur
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger alert-dismissible fade show';
                alert.innerHTML = `
                    <strong>Erreur!</strong> Impossible de supprimer le projet: ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
                `;
                
                document.querySelector('.container').prepend(alert);
            });
        });
    }
    
    // Charger la liste des projets au chargement de la page
    loadProjects();
});