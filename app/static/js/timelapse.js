document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const projectsList = document.getElementById('projects-list');
    const newProjectForm = document.getElementById('new-project-form');
    const editProjectForm = document.getElementById('edit-project-form');
    const projectDetails = document.getElementById('project-details');
    const deleteModal = new bootstrap.Modal(document.getElementById('delete-project-modal'));

    // Variables d'état
    let currentProjectId = null;
    let statusTimer = null;
    let isPageVisible = true;

    // Paramètres
    const defaultRefreshSeconds = 5;

    // Fonctions utilitaires
    function showElement(element) {
        if (element) element.classList.remove('d-none');
    }

    function hideElement(element) {
        if (element) element.classList.add('d-none');
    }

    function showLoading(container) {
        if (!container) return;
        container.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
                <p class="mt-2">Chargement en cours...</p>
            </div>
        `;
    }

    function showError(container, message) {
        if (!container) return;
        container.innerHTML = `
            <div class="alert alert-danger my-3">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message || 'Une erreur est survenue'}
            </div>
        `;
    }

    function formatDuration(seconds) {
        seconds = Math.round(seconds);
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

    // Fonction pour charger la liste des projets
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
            projectsList.innerHTML = `
                <div class="text-center my-5">
                    <i class="fas fa-folder-open fa-3x text-muted mb-3"></i>
                    <p class="lead">Aucun projet time-lapse existant</p>
                    <p>Créez votre premier projet en utilisant le formulaire</p>
                </div>
            `;
            return;
        }

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

            projectItem.querySelector('.load-project').addEventListener('click', function() {
                loadProjectDetails(this.dataset.id);
            });

            projectItem.querySelector('.delete-project').addEventListener('click', function() {
                const projectId = this.dataset.id;
                const projectName = this.dataset.name;

                document.getElementById('delete-project-name').textContent = projectName;
                document.getElementById('confirm-delete-btn').dataset.id = projectId;

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

        showElement(projectDetails);
        hideElement(newProjectForm);

        fetch(`/api/timelapse/projects/${projectId}`)
            .then(response => {
                if (!response.ok) throw new Error('Impossible de récupérer les détails du projet');
                return response.json();
            })
            .then(project => {
                renderProjectDetails(project);
                startStatusRefresh(projectId);
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
                    <!-- Section de capture automatique -->
                    <div class="card mb-4">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0"><i class="fas fa-clock me-2"></i>Capture automatique</h4>
                        </div>
                        <div class="card-body">
                            <div id="auto-capture-status" class="mb-3">
                                <div class="alert alert-info mb-0">
                                    <i class="fas fa-spinner fa-spin me-2"></i>
                                    Vérification de l'état de la capture automatique...
                                </div>
                            </div>
                            <div class="d-flex justify-content-center">
                                <button id="start-auto-capture" class="btn btn-success me-2">
                                    <i class="fas fa-play me-1"></i>Démarrer la capture automatique
                                </button>
                                <button id="stop-auto-capture" class="btn btn-danger d-none">
                                    <i class="fas fa-stop me-1"></i>Arrêter la capture automatique
                                </button>
                            </div>
                            <div class="alert alert-light border mt-3">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>Time-lapse :</strong> Le système va automatiquement capturer 
                                ${project.total_captures} images à intervalle de ${project.interval_seconds} secondes 
                                sur une durée totale de ${project.duration_minutes} minutes.
                            </div>
                        </div>
                    </div>
                
                    <div class="row">
                        <!-- Informations du projet -->
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Informations</h5>
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
                                    <h5 class="mb-0"><i class="fas fa-tasks me-2"></i>Progression</h5>
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
            stopStatusRefresh();
            hideElement(projectDetails);
            showElement(newProjectForm);
            currentProjectId = null;
        });

        document.getElementById('edit-project-btn').addEventListener('click', function() {
            setupEditForm(project);
        });

        // Écouteurs pour les boutons de capture automatique
        document.getElementById('start-auto-capture').addEventListener('click', function() {
            startAutoCapture(project.id);
        });

        document.getElementById('stop-auto-capture').addEventListener('click', function() {
            stopAutoCapture(project.id);
        });

        // Vérifier l'état initial de la capture automatique
        checkAutoCaptureStatus(project.id);
    }

    // Fonction pour vérifier l'état de la capture automatique
    function checkAutoCaptureStatus(projectId) {
        fetch(`/api/timelapse/projects/${projectId}/auto-capture/status`)
            .then(response => response.json())
            .then(data => {
                updateAutoCaptureUI(data);
            })
            .catch(error => {
                console.error('Erreur lors de la vérification du statut de capture auto:', error);
                const statusContainer = document.getElementById('auto-capture-status');
                if (statusContainer) {
                    statusContainer.innerHTML = `
                        <div class="alert alert-warning mb-0">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Impossible de vérifier l'état de la capture automatique.
                        </div>
                    `;
                }
            });
    }

    // Fonction pour mettre à jour l'interface utilisateur en fonction de l'état de la capture auto
    function updateAutoCaptureUI(status) {
        const statusContainer = document.getElementById('auto-capture-status');
        const startBtn = document.getElementById('start-auto-capture');
        const stopBtn = document.getElementById('stop-auto-capture');
        const editBtn = document.getElementById('edit-project-btn');

        if (!statusContainer || !startBtn || !stopBtn) return;

        if (status.active) {
            // Capture active
            startBtn.classList.add('d-none');
            stopBtn.classList.remove('d-none');

            if (editBtn) editBtn.disabled = true;

            const nextCapture = status.seconds_to_next > 0 
                ? `Prochaine capture dans <strong>${status.seconds_to_next} secondes</strong>` 
                : "Capture en cours...";

            statusContainer.innerHTML = `
                <div class="alert alert-success mb-0">
                    <i class="fas fa-cog fa-spin me-2"></i>
                    <strong>Capture automatique en cours !</strong> ${nextCapture}
                    <div class="progress mt-2" style="height: 10px;">
                        <div class="progress-bar bg-success progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: ${status.project.completion_percentage}%">
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Capture inactive
            startBtn.classList.remove('d-none');
            stopBtn.classList.add('d-none');

            if (editBtn) editBtn.disabled = false;

            statusContainer.innerHTML = `
                <div class="alert alert-secondary mb-0">
                    <i class="fas fa-info-circle me-2"></i>
                    Capture automatique inactive. Cliquez sur "Démarrer" pour lancer le time-lapse.
                </div>
            `;
        }
    }

    // Fonction pour démarrer la capture automatique
    function startAutoCapture(projectId) {
        const startBtn = document.getElementById('start-auto-capture');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Démarrage...';
        }

        fetch(`/api/timelapse/projects/${projectId}/auto-capture/start`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.detail || 'Échec du démarrage de la capture');
                });
            }
            return response.json();
        })
        .then(data => {
            showNotification('success', 'Capture automatique démarrée', data.message);
            checkAutoCaptureStatus(projectId);
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification('danger', 'Erreur', error.message);

            if (startBtn) {
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="fas fa-play me-1"></i>Démarrer la capture automatique';
            }
        });
    }

    // Fonction pour arrêter la capture automatique
    function stopAutoCapture(projectId) {
        const stopBtn = document.getElementById('stop-auto-capture');
        if (stopBtn) {
            stopBtn.disabled = true;
            stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Arrêt...';
        }

        fetch(`/api/timelapse/projects/${projectId}/auto-capture/stop`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.detail || 'Échec de l\'arrêt de la capture');
                });
            }
            return response.json();
        })
        .then(data => {
            showNotification('info', 'Capture automatique arrêtée', data.message);
            checkAutoCaptureStatus(projectId);
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification('danger', 'Erreur', error.message);

            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Arrêter la capture automatique';
            }
        });
    }

    // Fonction pour démarrer le rafraîchissement du statut
    function startStatusRefresh(projectId, interval = 2) {
        stopStatusRefresh();

        statusTimer = setInterval(function() {
            if (!isPageVisible || !currentProjectId) return;
            checkAutoCaptureStatus(projectId);
        }, interval * 1000);
    }

    // Fonction pour arrêter le rafraîchissement du statut
    function stopStatusRefresh() {
        if (statusTimer) {
            clearInterval(statusTimer);
            statusTimer = null;
        }
    }

    // Fonction pour configurer le formulaire d'édition
    function setupEditForm(project) {
        if (!editProjectForm) return;

        const form = editProjectForm.querySelector('form');
        form.dataset.id = project.id;
        form.elements.name.value = project.name;
        form.elements.duration_minutes.value = project.duration_minutes;
        form.elements.interval_seconds.value = project.interval_seconds;
        form.elements.fps.value = project.fps;

        // Sélectionner l'option de rotation
        const rotationSelect = form.elements.rotation;
        for (let i = 0; i < rotationSelect.options.length; i++) {
            if (parseInt(rotationSelect.options[i].value) === project.rotation) {
                rotationSelect.options[i].selected = true;
                break;
            }
        }

        // Afficher la modale
        const editModal = new bootstrap.Modal(editProjectForm);
        editModal.show();
    }

    // Fonction pour afficher une notification
    function showNotification(type, title, message) {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <strong>${title}</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
            </div>
        `;

        const alertContainer = document.createElement('div');
        alertContainer.innerHTML = alertHTML;

        const container = document.querySelector('.container');
        if (container) {
            container.prepend(alertContainer.firstChild);

            // Auto-fermeture après 5 secondes
            setTimeout(() => {
                const alertElement = container.querySelector(`.alert-${type}`);
                if (alertElement) {
                    const bsAlert = new bootstrap.Alert(alertElement);
                    bsAlert.close();
                }
            }, 5000);
        }
    }

    // Écouteurs pour la visibilité de la page
    document.addEventListener('visibilitychange', function() {
        isPageVisible = document.visibilityState === 'visible';

        if (isPageVisible && currentProjectId) {
            checkAutoCaptureStatus(currentProjectId);
            startStatusRefresh(currentProjectId);
        } else {
            // Arrêter les timers lorsque la page n'est pas visible
            stopStatusRefresh();
        }
    });

    // Écouteur pour le formulaire de création
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
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Échec de la création du projet');
                    });
                }
                return response.json();
            })
            .then(project => {
                showNotification('success', 'Projet créé', `Le projet "${project.name}" a été créé avec succès.`);
                form.reset();
                loadProjects();
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('danger', 'Erreur', error.message);
            });
        });
    }

    // Écouteur pour le formulaire d'édition
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
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Échec de la mise à jour du projet');
                    });
                }
                return response.json();
            })
            .then(project => {
                bootstrap.Modal.getInstance(editProjectForm).hide();
                showNotification('success', 'Projet mis à jour', 'Les modifications ont été enregistrées.');
                loadProjectDetails(projectId);
                loadProjects();
            })
            .catch(error => {
                console.error('Erreur:', error);

                // Afficher l'erreur dans la modale
                const alertContainer = editProjectForm.querySelector('.modal-body .alert-container');
                if (alertContainer) {
                    alertContainer.innerHTML = `
                        <div class="alert alert-danger">
                            ${error.message}
                        </div>
                    `;
                } else {
                    showNotification('danger', 'Erreur', error.message);
                }
            });
        });
    }

    // Écouteur pour la suppression
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const projectId = this.dataset.id;

            fetch(`/api/timelapse/projects/${projectId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Échec de la suppression du projet');
                    });
                }
                return response.json();
            })
            .then(data => {
                deleteModal.hide();
                showNotification('success', 'Projet supprimé', data.message);

                if (currentProjectId === projectId) {
                    stopStatusRefresh();
                    hideElement(projectDetails);
                    showElement(newProjectForm);
                    currentProjectId = null;
                }

                loadProjects();
            })
            .catch(error => {
                console.error('Erreur:', error);
                deleteModal.hide();
                showNotification('danger', 'Erreur', error.message);
            });
        });
    }

    // Charger la liste des projets au démarrage
    loadProjects();
});