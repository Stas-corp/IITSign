# IITSign

Звернути увагу на README.md в `src\sign\keys\`

## Конфігурація `.env`:

```
ALL_KEYS='{
    "key": ".crt",
}'

DB_SERVER=localhost
DB_NAME=mydb
DB_USER_ID=sa
DB_PASSWORD=Password123
```

## Для запуску docker контейнера і тесту:

```
docker compose up --build
```
Потім в інтерактивному режимі зайти в контейнер:

```
docker exec -it iitsign-app /bin/bash
```

Запустити тест в дерикторії `/app`:
```
pytest tests
```