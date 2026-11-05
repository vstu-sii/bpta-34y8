# Quality & Safety — Lab 2

Владелец: Quality & Safety. Дата: 2026-11-04. Ветка: `lab2-quality-safety-design`.

Комплект подготовлен для review; согласование командой и испытания работающего
продукта не подменяются фактом создания документов.

- [DoD всех артефактов](dod.md).
- [Golden dataset v1 и порядок использования](golden-dataset/README.md).
- [Исходные QS-UC с альтернативами и исключениями](../use-cases/README.md).
- [Матрица UC → ветвь → кейс](golden-dataset/traceability.json).
- [Тест-план](test-plan.md).
- [Модель угроз](threat-model.md).
- [Полный отчёт](lab2-quality-safety-report.md).

Проверка без API-ключей и вызовов модели:

```powershell
python -m pip install -r tools/quality/requirements.txt
python tools/quality/evaluate.py validate
python -m unittest discover -s tools/quality -p 'test_*.py' -v
```

Предыдущие `dod-draft.md`, `golden-dataset-plan.md`, `success-criteria.md`
сохранены как материалы лабы 1. Для лабы 2 пути, метки и правила задаёт этот
комплект: JSONL в `docs/quality/golden-dataset/`, трёхклассовая оценка ответа
из текущего OpenAPI. Порог p95 ≤ 10 с из старого черновика не является
утверждённым требованием: новый тест-план требует сначала базового измерения.

Обновление 05.11.2026: восстановленный набор v1.1.0 заменяет повреждённую
кириллицу v1.0.0. Проверяются 40 кейсов, 5 UC, 19 ветвей и кодировка;
22 теста валидатора/scorer. Новые эталоны ожидают проверки человеком.
