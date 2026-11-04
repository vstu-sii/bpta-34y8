# Контракт контейнеров, API и хранения — Lab 2 Delivery

Дата: 2026-11-05. Канонический контракт: [`../../api/openapi.yaml`](../../api/openapi.yaml).
Версия 0.3.0 — совместимое необязательное расширение `exam_questions`.
Это предложение Delivery для review AI Engineer, а не утверждение о принятии командой.
Старая ссылка `docs/api/openapi.yaml` сохранена идентичной копией; CI сверяет файлы.

## Ответственность контейнеров

| Контейнер | Контракт / адрес | Ответственность |
|---|---|---|
| web | `http://localhost:8080` | Прототип материала, принятия и повторения; данные только в памяти |
| app | `http://localhost:8000/health` | Сейчас health-заглушка. В MVP: identity, ownership, БД, jobs и расписание |
| agent | `http://ai-service:8000` в ai-сети | Сейчас health-заглушка. В MVP: внутренние AI endpoints, без БД/tools |
| db | `db:5432` в internal backend | PostgreSQL 16; приложение — единственный клиент |

Контрактные `/ai/v1/*` ещё не реализованы; HTTP health и старт контейнера не
доказывают, что эти операции доступны. API ключ провайдера не требуется для smoke.

## Поток задания

1. App проверяет владельца материала, извлекает текст и создаёт persistent job.
2. Chunk получает UUID внутри БД, положительный sequence_no и устойчивый locator.
3. В AI request передаются document_id, prompt_version, chunks и, если есть,
   exam_questions. Последние используются только для выбора знания, не как источник фактов.
4. AI job создаётся/опрашивается по OpenAPI. Владелец продуктового job — app;
   AI job_id используется как внешний корреляционный ID (в лабе 3 добавить поле
   и recovery-механику при реализации асинхронного транспорта).
5. App проверяет структуру, цитату и принадлежность chunk, сохраняет draft.
6. Только принятие пользователем включает карточку в повторение; ответ модели
   не может самостоятельно изменить accepted/deleted или расписание.

Открытый вопрос реализации: идемпотентность внутреннего AI job и восстановление
после рестарта. У app есть scoped idempotency_key; AI контракт пока не задаёт
Idempotency-Key. До лабы 3 согласовать retry/polling и версию контракта с AI.

## Mapping данных

| AI поле | Хранение | Правило |
|---|---|---|
| document_id | document.id UUID | Ownership проверяет app до любого вызова |
| chunk_id integer | source_chunk.sequence_no | Уникален внутри document; UUID FK остаётся внутренним |
| source_locator, source_page | source_chunk.source_locator, page_number | Карточка ссылается на chunk; page может быть null |
| card_type | card.card_type | short_qa / summary / formula |
| answer | card.reference_answer | Проверить непустоту и смысл по источнику |
| source_fragment | card.source_quote | Непрерывная точная подстрока именно этого chunk |
| formula, variables | card.formula, card.variables JSONB | Для formula оба обязательны; для остальных null и [] |
| approval_status=pending | card.status=draft | После ручного одобрения accepted, после удаления deleted |
| job status | generation_job.status | queued / running / completed / partial / failed |
| status оценки | review.model_result | correct / partially_correct / incorrect |
| confidence / requires_self_check | review.model_confidence / requires_self_check | Сохранить отдельно от финальной самооценки |
| итог пользователя | review.result, assessed_by=student | correct / partially_correct / incorrect / skipped |
| usage/errors | quality_event.payload и job.error_code | Минимальные технические данные; не сохранять ключи и полный конспект в лог |

Ограничения JSON на длины, типы variables и точную цитату проверяет app по OpenAPI;
SQL добавляет целостность и минимальные CHECK/FK. FK не заменяет авторизацию.
Транспортные статусы не позволяют модели менять расписание.

## Режимы провайдера и review

AI Engineer выбирает модель в `docs/model-candidates.md`. Delivery фиксирует
границу процесса, права и адреса, а не заменяет этот выбор ADR.
Передача пользовательского текста в облако требует явного выбранного режима;
автоматически отправлять локальный документ в облако при отказе запрещено дизайном.
Проверки реальных моделей, качества, прав доступа и восстановления — лаба 3.
