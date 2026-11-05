# Проверка комплекта Delivery

Дата: 2026-11-05. Ветка: `lab2-delivery-design`.

| Проверка | Результат |
|---|---|
| aact 3.0.0-beta.29 check | PASS, 0 violations |
| PlantUML: context, container, ERD | PASS, 3 SVG пересобраны в Docker; XML валиден |
| Прототип в Edge | PASS: ограничения demo, правка, удаление, принятие, пустой/заполненный ответ, самооценка |
| Клавиатура / JavaScript | PASS: Tab между полями, 0 pageerror; полная accessibility-приёмка не проводилась |
| Мобильный экран 390 px | Горизонтального скролла нет, скриншот сохранён |
| PostgreSQL 16, новая база | Начальная миграция проходит |
| database/check-schema.sql | PASS: 10 проверок, ROLLBACK |
| API / Compose / SQL mapping | PASS: 18 схем API, адрес ai-service:8000 и словари статусов сверены |
| Ruff check и format всего репозитория | PASS |
| Compose config | Проходит с переменными из .env.example |
| Compose up --wait | PASS: web, app, agent, db healthy |
| HTTP и DNS | PASS: web, app /health, app → ai-service:8000/health |
| Изоляция БД | PASS: нет общей сети agent/db, agent не разрешает имя db |
| Уборка smoke | PASS: удалены только контейнеры/сети/volume уникального тестового проекта |

Это технические проверки, а не приёмка Product и не проживание UC человеком.
Не проверены реальная генерация, качество модели, пользовательская авторизация,
сохранение карточек через API, PDF/OCR и расписание: в лабе 2 это проектирование.

В CI добавлены aact, рендер диаграмм, проверка контрактов, браузерный сценарий
со скриншотами и smoke Compose/HTTP/SQL. Серверный CI не выдаётся за пройденный
до появления результата GitHub Actions.

Команды воспроизведения и ограничения — в [delivery-report.md](delivery-report.md).
