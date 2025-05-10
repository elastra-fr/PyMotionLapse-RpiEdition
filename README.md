# PyMotionLapse

En cours de développement

## Configuration

### Création d'un environnement virtuel

#### Windows

```bash
python -m venv env

.\env\Scripts\activate
```
#### Linux

```bash
python3 -m venv env

source env/bin/activate

```

### Génération du fichier requirements.txt

```bash
pip freeze > requirements.txt
```

### Installation des dépendances

```bash
pip install -r requirements.txt
```
### Utilisation de l'interface graphique fastapi

```bash

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```




