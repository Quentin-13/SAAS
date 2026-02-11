# Energy Autopilot - SaaS de Gestion Énergétique Prédictive

Plateforme SaaS qui optimise automatiquement la consommation énergétique des bâtiments tertiaires grâce à l'IA prédictive.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Next.js 14  │────▶│  FastAPI      │────▶│  PostgreSQL     │
│  Frontend    │     │  Backend      │     │  + TimescaleDB  │
│  :3000       │     │  :8000        │     │  :5432          │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────┴───────┐     ┌─────────────────┐
                    │  Celery       │────▶│  Redis          │
                    │  Workers/Beat │     │  :6379          │
                    └──────────────┘     └─────────────────┘
```

### Stack Technique

**Backend:** FastAPI, SQLAlchemy, Alembic, Celery, Prophet (ML), scikit-learn
**Frontend:** Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Recharts, Zustand
**Base de données:** PostgreSQL 15 + TimescaleDB (séries temporelles)
**Cache/Queue:** Redis 7
**Conteneurisation:** Docker + Docker Compose

### Intégrations

- **Enedis Data Connect** (Linky) - consommation électrique
- **Google Nest API** - thermostats connectés
- **Netatmo Energy API** - thermostats Netatmo
- **OpenWeatherMap** - données météorologiques

> Toutes les intégrations fonctionnent en **mode mock** si aucune clé API n'est configurée.

## Installation

### Prérequis

- Docker & Docker Compose
- Git

### Démarrage rapide

```bash
# Cloner le repo
git clone <repo-url>
cd energy-autopilot

# Configurer l'environnement
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Lancer tous les services
docker-compose up -d

# Attendre que PostgreSQL soit prêt, puis lancer les migrations
docker-compose exec backend alembic upgrade head

# Charger les données de démo
docker-compose exec backend python seed_data.py
```

### Accès

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API ReDoc:** http://localhost:8000/redoc

### Compte démo

```
Email: demo@energy-autopilot.fr
Mot de passe: demo1234
```

## API Endpoints

### Auth (`/api/v1/auth`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/register` | Créer un compte |
| POST | `/login` | Connexion (JWT) |
| POST | `/refresh` | Rafraîchir le token |
| GET | `/me` | Profil utilisateur |

### Sites (`/api/v1/sites`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Lister les sites |
| POST | `/` | Créer un site |
| GET | `/{id}` | Détail d'un site |
| PATCH | `/{id}` | Modifier un site |
| DELETE | `/{id}` | Supprimer un site |
| POST | `/{id}/autopilot/enable` | Activer l'autopilot |
| POST | `/{id}/autopilot/disable` | Désactiver l'autopilot |

### Devices (`/api/v1/devices`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Lister les équipements |
| POST | `/` | Ajouter un équipement |
| GET | `/{id}` | Détail équipement |
| POST | `/{id}/control` | Contrôle manuel |
| POST | `/sync/nest` | Synchroniser Nest |
| POST | `/sync/netatmo` | Synchroniser Netatmo |
| POST | `/sync/linky` | Connecter Linky |

### Energy (`/api/v1/energy`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/readings` | Historique consommation |
| GET | `/analytics/daily` | Agrégats journaliers |
| GET | `/analytics/monthly` | Agrégats mensuels |
| GET | `/forecast` | Prévisions (Prophet) |
| GET | `/anomalies` | Anomalies détectées |

### Autopilot (`/api/v1/autopilot`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/actions` | Historique actions |
| GET | `/actions/{id}` | Détail action |
| POST | `/actions/{id}/feedback` | Feedback utilisateur |
| GET | `/savings` | Économies réalisées |
| GET | `/config` | Configuration autopilot |

### Dashboard (`/api/v1/dashboard`)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/overview` | Métriques globales |

### System
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/readiness` | Readiness check |
| WS | `/ws/dashboard` | WebSocket temps réel |

## Moteur Autopilot

L'autopilot s'exécute toutes les 15 minutes via Celery Beat et applique ces règles :

1. **Évitement des pics tarifaires** : Réduit la température de 1°C pendant les heures de pointe (8h-13h, 17h-20h)
2. **Optimisation thermique prédictive** : Utilise les prévisions météo pour anticiper les besoins de chauffage
3. **Gestion de l'occupation** : Passe en mode éco quand les zones sont inoccupées
4. **Protection antigel** : Maintient un minimum de 16°C en toutes circonstances
5. **Limitation des changements** : Maximum 2°C de variation par action, 3 changements/heure/appareil

### Contraintes de sécurité

- Température toujours entre les bornes min/max de chaque zone
- Protection antigel à 16°C
- Maximum 2°C de changement par action
- Rate limiting : 3 changements max par appareil par heure

## Variables d'environnement

### Backend (`.env`)

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://user:password@postgres:5432/energy_autopilot` |
| `REDIS_URL` | URL Redis | `redis://redis:6379/0` |
| `SECRET_KEY` | Clé JWT | (requis) |
| `MOCK_APIS` | Mode mock APIs | `true` |
| `OPENWEATHER_API_KEY` | Clé OpenWeatherMap | (optionnel) |
| `SENTRY_DSN` | DSN Sentry | (optionnel) |

### Frontend (`.env.local`)

| Variable | Description | Défaut |
|----------|-------------|--------|
| `NEXT_PUBLIC_API_URL` | URL de l'API | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_WS_URL` | URL WebSocket | `ws://localhost:8000/ws` |

## Tests

```bash
# Backend
docker-compose exec backend pytest --cov=app --cov-report=term-missing -v

# Frontend
docker-compose exec frontend npm run test
```

## Développement

```bash
# Logs en temps réel
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Reconstruire après changements
docker-compose up -d --build

# Accéder au shell backend
docker-compose exec backend bash
```

## Troubleshooting

### Docker Compose ne démarre pas
```bash
docker-compose down -v
docker-compose up -d --build
```

### Migrations échouent
```bash
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

### Celery ne traite pas les tâches
```bash
docker-compose logs celery-worker
docker-compose restart celery-worker celery-beat
```

## Licence

Propriétaire - Tous droits réservés.
