# DEVELOPERS.md

## Локальний розвиток

### Вимоги
- Python 3.9+
- Docker & Docker Compose
- Redis (у docker-compose)
- ClickHouse (у docker-compose)

### Інсталяція

```bash
git clone https://github.com/romanchaa997/st-risk-platform.git
cd st-risk-platform

# Встановити залежності
pип install -r requirements.txt

# Запустити інфраструктуру (Redis, ClickHouse)
docker-compose up -d

# Запустити FastAPI-сервіси
python app.py  # або для feature-service, model-service
```

### Змінні середовища (.env)

```env
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
REDIS_URL=redis://localhost:6379
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
```

### Моніторинг локально

1. **Prometheus**: http://localhost:9090
   - Помітки FastAPI: http://localhost:8000/metrics

2. **Grafana** (після запуску): http://localhost:3000
   - За замовчуванням: admin/admin
   - Імпортувати dashboard з `monitoring/grafana_dashboard.json`

3. **ClickHouse**: http://localhost:8123/play

### Нагрузкові тести

```bash
# Встановити locust
pип install locust

# Запустити тести
locust -f load_test.py --host=http://localhost:8000

# Веб-UI: http://localhost:8089
```

### Структура репозиторія

```
st-risk-platform/
├── app.py                          # FastAPI gateway
├── services/
│   ├── feature_service.py
│   └── model_service.py
├── contracts/                      # AsyncAPI schemas
├── sql/                            # ClickHouse schemas
├── monitoring/
│   ├── prometheus.yml
│   └── grafana_dashboard.json
├── tests/
│   └── load_test.py
├── docker-compose.yml
├── requirements.txt
├── PERFORMANCE_CHECKLIST.md        # Plan оптимізації
├── SPRINT_PLAN.md                  # План на місяць
└── DEVELOPERS.md                   # Цей файл
```

### Корисні команди

```bash
# Логи FastAPI
docker-compose logs -f app

# Логи ClickHouse
docker-compose logs -f clickhouse

# Перезапустити все
docker-compose down && docker-compose up -d

# Входити в контейнер
docker-compose exec app bash
```

### Решення проблем

- **Redis connection error**: перевір що Redis запущен `docker-compose ps`
- **ClickHouse timeout**: збільш CLICKHOUSE_TIMEOUT у .env
- **Port 8000 занят**: змініть PORT у app.py або kill процес на port 8000
