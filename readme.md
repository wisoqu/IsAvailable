# IsAvailable

Мониторинг веб-инфраструктуры с послойной диагностикой root-cause: вместо бинарного «доступен / недоступен» показывает, **на каком именно слое** произошёл сбой — DNS, TCP, TLS или HTTP.

> Проект в разработке в рамках трека **ITMO.STARS**. Текущая стадия — Этап 0 (CLI-скрипт, работающий от и до), см. `IsAvailable-roadmap.docx`.

Репозиторий: [github.com/wisoqu/IsAvailable](https://github.com/wisoqu/IsAvailable)

## Идея

Большинство мониторингов (UptimeRobot, Uptime Kuma, Beszel, Smokeping) отвечают на вопрос «сайт жив?». IsAvailable отвечает на вопрос «**на каком уровне сломалось**?»:

- DNS не резолвится → проблема на уровне домена / DNS-провайдера
- DNS ок, TCP не коннектится → сервер не слушает, файрвол, хостинг
- TCP ок, TLS падает → сертификат просрочен или неверен
- TLS ок, HTTP 5xx → проблема на уровне приложения

## Архитектурный принцип

Один слой — одна функция. Ни одна функция не знает о соседних слоях; порядок и связывание слоёв знает только оркестратор (`main.py`).

```
network/
├── ip_resolve.py      # DNS resolve
├── tcp_handshake.py    # TCP connect
├── tls_handshake.py    # TLS handshake (принимает TCP-соединение)
└── main.py             # оркестратор: вызывает слои по порядку, собирает LOGS
```

Каждая функция уровня возвращает `(conn | None, log_dict)`, где `log_dict` — то, что уходит в JSON, а `conn` — рабочий объект (сокет / TLS-обёртка), который **не сериализуется** и используется только для передачи в следующий слой.

## Контракт лога слоя

Каждый `*_log` — независимо от слоя — содержит:

| Поле | Тип | Описание |
|---|---|---|
| `type` | `str` | Идентификатор слоя: `TCP_CONN`, `TLS_CONN` и т.д. |
| `success` | `bool` | Успешно ли прошла проверка |
| `elapsed_ms` | `float` | Время выполнения в миллисекундах |
| `error_type` | `str` | Класс ошибки (`""`, если успех) |
| `explanation` | `str` | Человекочитаемое объяснение результата |
| `recommendation` | `str` | Что делать дальше (опционально — отсутствует, если запрос по этому слою не выполнялся) |

## Структура `LOGS`

```json
{
    "domain": "google.com",
    "ip": "64.233.165.102",
    "ip_logs": {
        "success": true,
        "elapsed_ms": 28.86,
        "error_type": "",
        "explanation": "Domain 'google.com' was successfully resolved to IP address 64.233.165.102.",
        "recommendation": "No errors detected."
    },
    "ports": {
        "443": {
            "tcp_log": {
                "type": "TCP_CONN",
                "success": true,
                "elapsed_ms": 51.87,
                "error_type": "",
                "explanation": "TCP connection established successfully.",
                "recommendation": "No TCP problems detected."
            },
            "tls_log": {
                "type": "TLS_CONN",
                "success": true,
                "elapsed_ms": 132.11,
                "error_type": "",
                "explanation": "TLS handshake successful."
            }
        }
    }
}
```

Каждый порт в `ports` хранит свои `tcp_log` и `tls_log` независимо — без перезаписи между итерациями (баг ранних версий).

Если TCP-соединение не установлено, TLS-слой всё равно логируется, но с явным `InvalidConnection`, а не молча пропускается:

```json
"tls_log": {
    "type": "TLS_CONN",
    "success": false,
    "elapsed_ms": 0.001,
    "error_type": "InvalidConnection",
    "explanation": "TCP connection is None. TLS handshake cannot be started."
}
```

## Roadmap

Подробная дорожная карта по этапам (9 → 11 класс) — в `IsAvailable-roadmap.docx`. Коротко:

- **Этап 0** — CLI-скрипт: DNS + TCP + TLS + HTTP TTFB для одного домена *(текущий)*
- **Этап 1** — постоянство, множественные цели, rule-based root-cause, веб-дашборд
- **Этап 2** — Telegram-алерты, детекция деградации, traceroute по требованию
- **Этап 3** — AI-объяснение инцидентов, публичные статус-страницы, первые пользователи
- **Этап 4** — подготовка заявки на ITMO.STARS

## Стек

Python (asyncio) → FastAPI · SQLite → Postgres при росте · Jinja2/htmx на фронте · Docker Compose для деплоя.