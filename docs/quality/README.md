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

Обновление 05.11.2026: набор v2.0.0 подготовлен по
[Example.pdf](../experiments/materials/Example.pdf), перенесённому в каталог
учебных материалов. 40 кейсов покрывают 5 UC и 19 ветвей; 20 ответов оценены
по [рубрике 0/1/2](golden-dataset/scoring-rubric.md) с учётом ETS, Ragas и DeepEval.
34 теста проверяют scorer, источники, кодировку и согласованность оценок.
[Ведомость](golden-dataset/reference-annotations.md) содержит вопросы уровня
выше среднего, эталоны, страницы и объяснения оценок.
