# Отчёт по лабораторной работе №2 — Delivery

**Дисциплина:** «Системы искусственного интеллекта», 2026, 6 курс.

**Проект:** БПТА — карточки для повторения из конспекта.

**Роль:** Delivery. **Дата:** 05.11.2026. **Ветка:** `lab2-delivery-design`.

**Автор Git:** существующий пользователь `johnpuhlyj-dev`.

**База:** актуальный `origin/main`, `dee6b81f51b4d173f232c5ef3cb8a82e8eb8a59a`.

## 1. Цель и основание

Подготовить проверяемые чертежи системы, UI-прототип, контракт хранения и
запускаемый Compose-скелет к лабораторной 3. Основание:
[задание лабораторной 2](https://sii.sergeivolchkov.ru/labs/lab2.md),
[бриф](../brief.md), [PRD](../prd.md), [AI-пайплайн](../ai-pipeline.md)
и опубликованный AI-контракт. Учитывались замечания комплекта Quality & Safety,
загруженного ранее в отдельную ветку. Коммиты других ролей в эту ветку не переносились.

## 2. Исходное состояние и выполненные исправления

Локально уже были C4, ADR, SQL, прототип и Compose, но значительная часть не
была добавлена в Git. Запуск полного стека не был подтверждён; документы отражали
проверки октября. После обновления main появились несовпадения с AI Engineer:
адрес/порт AI, типы карточек и формулы, статусы jobs/оценок и идентификаторы chunk.

В ходе работы:

1. Проверены все имеющиеся артефакты и обновлена документация.
2. AI-сервис получил alias `ai-service:8000`, совпадающий с OpenAPI.
3. Сети AI и БД разделены; у agent нет credentials/общей сети с db.
4. SQL дополнен типами карточек, формулами/обозначениями, locator и sequence_no,
   статусами AI и метаданными confidence/self-check.
5. Описано явное преобразование API ↔ БД. Канонический контракт помещён в `api/`,
   а старый путь оставлен идентичной совместимой копией.
6. Предложено необязательное поле exam_questions в AI request, чтобы вопросы
   зачёта передавались отдельно от доказательного контекста. Требуется review AI.
7. Зависимости aact/Playwright зафиксированы lock-файлом; прототип проверяется
   одной командой с автоматическим стартом/остановкой локального сервера.
8. Прототип явно отклоняет замену демонстрационного текста/вопросов; внешняя
   загрузка шрифтов удалена, обновлены четыре скриншота.
9. Создан воспроизводимый smoke-тест чистой БД и четырёх сервисов.
10. Обновлён CI: архитектура, рендер, API mapping, прототип, SQL/HTTP/network checks.

## 3. Соответствие шагам задания Delivery

| Шаг | Результат | Артефакт |
|---|---|---|
| C4 as-code + aact | Context и Container, исходники и SVG; 0 violations | `docs/architecture/c4-*.puml`, `.svg`, `aact.config.ts` |
| ADR архитектуры | Единый владелец данных; изоляция AI; контекст, альтернативы, цена и тесты | `docs/adr/ADR-001-single-data-owner.md`, `ADR-002-ai-boundary.md` |
| Прототип UI агентом | Три экрана, редактирование/принятие/удаление/ответ/самооценка, 4 скриншота | `frontend/prototype/` |
| Схема данных | PostgreSQL 16, 9 таблиц, ERD PlantUML/SVG, порядок миграций | `database/schema.sql`, `erd.puml`, `erd.svg`, `migrations/` |
| Compose-скелет v2 | Четыре сервиса healthy, сети, volume, health checks | `compose.dev.yml`, `compose.yml` |
| Совместный AI API | Канонический контракт, совместимый старый путь, mapping; дополнение вопросов | `api/openapi.yaml`, `docs/architecture/api-mapping.md` |

## 4. Архитектура и принятые в дизайне границы

Context показывает студента, систему и внешнего провайдера модели. Container
разделяет web, app, agent и PostgreSQL. SQL-репозиторий, расписание, persistent jobs
и проверки владельца — компоненты app, а не отдельные контейнеры.
Agent получает минимальный контекст и не владеет данными приложения.

Сети:

- frontend: web + app;
- backend (internal): app + db;
- ai: app + agent, alias AI `ai-service:8000`.

На хост публикуются только web/app и только на 127.0.0.1; БД и agent не публикуют
порты. Исходящий доступ AI к провайдеру сохраняется. Health-заглушки не содержат
клиента БД или модели. Секреты пользователя не читались и не добавлялись в коммит.

Aact проверяет acyclic, dbPerService, cohesion, commonReuse и acl.
apiGateway отключён: один API без отдельного gateway; crud отключён: репозиторий
внутри app; stableDependencies отключён: нет измеренных меток стабильности.
Причины записаны в конфигурации/ADR; 0 violations означает соответствие
включённым правилам, а не доказательство безопасности/правильности всей системы.

C4 использует стандартную библиотеку `<C4/...>` из зафиксированного PlantUML
образа; include ветки master больше не загружается. Рендер выполнялся локально.

## 5. Прототип

Три экрана: «Материалы», «Проверка карточек», «Повторить сегодня».
Демонстрация: исходный пример → черновик → правка → принять → свободный ответ →
эталон → самооценка. Удалённая карточка в повторение не попадает, пустой вопрос
не принимается, эталон не раскрывается до попытки ответа.

Скриншоты: `upload.png`, `approval.png`, `review.png`, `mobile.png` в
`frontend/prototype/screenshots/`. Размеры desktop 1440×1100, mobile шириной 390 px.
Мобильный скриншот также просмотрен визуально: элементы в пределах экрана,
форма и действия доступны. В автоматизации проверены Tab-переход и 0 JS pageerror.
Полная accessibility-приёмка и проживание UC человеком не проводились.

Прототип хранит данные только в памяти страницы. Реальной генерации, PDF/OCR,
авторизации, persistence и расписания в нём нет — это соответствует цели дизайна.

## 6. Хранение и API

Таблицы: student, document, exam_question, source_chunk, generation_job, card,
review_schedule, review, quality_event — **9 таблиц**; ERD и SQL согласованы.
Входы пользователя и результаты модели разделены по назначению.
Составные FK запрещают привязать карточку к chunk/job другого документа.

API chunk_id — integer sequence_no внутри document; UUID остаётся внутренним
PK. `answer/source_fragment` преобразуются в `reference_answer/source_quote`;
`pending` AI-карточки соответствует draft. Формулы и variables хранятся явно.
Jobs: queued/running/completed/partial/failed. Оценки: correct/partially_correct/incorrect;
конфиденс и requires_self_check сохраняются отдельно от результата пользователя.

Начальная схема применяется только к новому пустому volume; существующая БД
не обновляется переписыванием schema.sql. Последующие миграции имеют номера
002, 003 и применяются отдельно после backup; заготовка процесса в migrations/README.md.
Полный runner миграций — задача реализации лабы 3, не имитируется в скелете.

Расширение exam_questions обратно совместимо по структуре, но ещё не реализовано
в AI-заглушке. Модель не должна брать ответ из вопроса: источник доказательств —
chunks. Async polling, корреляция AI job и идемпотентность должны быть согласованы
до реализации; mapping описывает эту границу явно.

## 7. Проведённые проверки

| Проверка | Фактический результат |
|---|---|
| `npm run check:architecture` | PASS, aact 3.0.0-beta.29, 0 violations |
| Рендер PlantUML | PASS, 3 SVG, валидный XML без Syntax Error |
| `python scripts/check-delivery.py` | PASS: 16 артефактов, 4 PNG, 18 схем API, адреса/границы согласованы |
| `npm run check:prototype` | PASS: demo guards, правка, удаление, принятие, ответ, самооценка, Tab и 390 px |
| `python scripts/check-compose.py` | PASS: чистая PostgreSQL 16, web/app/agent/db healthy |
| SQL constraints | PASS, 10 проверок, ROLLBACK |
| HTTP/DNS | PASS: web, app /health, app → ai-service:8000 |
| Сетевая граница БД | PASS: agent и db без общей сети, agent не разрешает имя db |
| Ruff check / format всего проекта | PASS |
| npm install/audit | 0 известных уязвимостей на момент установки |

10 SQL-проверок: чужой chunk, неизвестный job status, неполная formula,
formula у short_qa, не-массив variables, повтор sequence_no, корректная formula
и partial job, partially_correct/self-check, чужой job, каскадное удаление владельца.
Проверка не оставляет данные: SQL делает rollback, smoke удаляет только свой
уникальный тестовый Compose-проект и его volume. Пользовательские volumes не трогаются.

Среда: Windows/PowerShell, Docker Engine 28.5.1, Node.js 22.23.3,
Playwright Core 1.64.1 (Edge), jsonschema 4.23.0, PyYAML 6.0.2, Ruff 0.16.8.
PlantUML digest:
`sha256:9b5071ab56a4192aac458ab4b0d42261c22c8109695894ae5be6013c3be6cac1`.
В CI Linux используется Chromium. Серверный GitHub CI не объявляется пройденным
по одному факту наличия workflow.

## 8. Воспроизведение

Из корня, Node.js 22+, Python и запущенный Docker:

```powershell
npm ci --ignore-scripts
python -m pip install -r scripts/requirements.txt
npm run check:architecture
python scripts/check-delivery.py
npm run check:prototype
python scripts/check-compose.py
python -m ruff check .
python -m ruff format --check .
```

Рендер трёх диаграмм:

```powershell
docker run --rm -v "${PWD}:/work" -w /work plantuml/plantuml@sha256:9b5071ab56a4192aac458ab4b0d42261c22c8109695894ae5be6013c3be6cac1 -tsvg docs/architecture/c4-context.puml docs/architecture/c4-container.puml database/erd.puml
```

Обычный запуск демо без изменения существующего .env:

```powershell
docker compose --env-file .env.example -f compose.dev.yml up -d --build --wait
```

Открыть http://localhost:8080 и http://localhost:8000/health.
Остановка: `docker compose --env-file .env.example -f compose.dev.yml down`.
Рабочий volume сохраняется; удалять его для обновления схемы без backup нельзя.

## 9. Оставшееся командное согласование

- Product: согласованные UC, проживание человеком, приёмка экранов/ADR.
- AI Engineer: review exam_questions и mapping, политика режима провайдера,
  контракт идемпотентности/асинхронных jobs перед реализацией.
- Quality & Safety: приёмка DoD и угроз на общей интегрированной версии команды.

Эти пункты не отмечены как выполненные за других участников. ADR остаются
предложениями для review. Модель, качество генерации, ownership, restart recovery
и расписание работающего приложения ещё не тестировались: в лабе 2 это заглушки.

## 10. Подготовка сдачи

Ветка: `lab2-delivery-design`. Заголовок PR:
`Lab2: [Delivery] — Design Deliverables`.

Описание для PR:

> Добавлен проверенный комплект Delivery: C4/ADR и 0 aact violations,
> интерактивный UI-прототип с четырьмя скриншотами, SQL/ERD и заготовка миграций,
> Compose четырёх сервисов с отдельными сетями БД/AI. Адрес и данные согласованы
> с AI-контрактом; optional exam_questions предложено для review.
> Проверки: чистый Compose healthy, 10 SQL checks, HTTP/DNS/isolation, браузерный
> сценарий, PlantUML, static contract check и Ruff PASS.
> Полный отчёт: docs/architecture/delivery-report.md. Командное review ожидается.

Для защиты: C4 → цена двух ADR → прототип и скриншоты → SQL/API mapping →
smoke на чистом проекте → результаты проверок и открытые согласования.
Публикация ветки Git не подменяет отправку работы в Disputa; последняя требует
отдельного явного разрешения пользователя по AGENTS.md.
