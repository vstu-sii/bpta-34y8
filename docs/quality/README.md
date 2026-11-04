# Quality & Safety — Lab 2

Владелец: Quality & Safety. Дата: 2026-11-04. Ветка: `lab2-quality-safety-design`.

Комплект подготовлен для review; согласование командой и испытания работающего
продукта не подменяются фактом создания документов.

- [DoD всех артефактов](dod.md).
- [Golden dataset v1 и порядок использования](golden-dataset/README.md).
- [Тест-план](test-plan.md).
- [Модель угроз](threat-model.md).
- [Полный отчёт](lab2-quality-safety-report.md).

Проверка без API-ключей и вызовов модели:

```powershell
python -m pip install -r tools/quality/requirements.txt
python tools/quality/evaluate.py validate
```

Предыдущие `dod-draft.md`, `golden-dataset-plan.md`, `success-criteria.md`
сохранены как материалы лабы 1. Для лабы 2 пути, метки и правила задаёт этот
комплект: JSONL в `docs/quality/golden-dataset/`, трёхклассовая оценка ответа
из текущего OpenAPI. Порог p95 ≤ 10 с из старого черновика не является
утверждённым требованием: новый тест-план требует сначала базового измерения.
