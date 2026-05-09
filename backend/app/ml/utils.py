import re


def _extract(text, key):
    """Извлекает значение по ключу из строки вида 'Ключ: значение | ...'"""
    if not text:
        return ''
    match = re.search(rf'{re.escape(key)}\s*:\s*([^|]+)', text, re.IGNORECASE)
    return match.group(1).strip() if match else ''


def format_resume_for_ml(resume_obj):
    """
    Форматирует резюме в формат обучающих данных:
    Должность: X | Опыт: X лет | Образование: X | Занятость: X | Отрасль: X | Зарплата ожидаемая: X | Навыки: X
    """
    content = resume_obj.content or ''
    parts = []

    parts.append(f"Должность: {resume_obj.title or ''}")

    for label in ('Опыт', 'Образование', 'Занятость', 'Отрасль', 'Зарплата ожидаемая', 'Навыки'):
        val = _extract(content, label)
        if val:
            parts.append(f"{label}: {val}")

    # Если content — свободный текст без структуры, добавляем как Навыки
    if not any(p.startswith(('Опыт:', 'Навыки:')) for p in parts) and content:
        parts.append(f"Навыки: {content}")

    return " | ".join(parts)


def format_vacancy_for_ml(vacancy_obj):
    """
    Форматирует вакансию в формат обучающих данных:
    Вакансия: X | Требуемый опыт: X лет | Занятость: X | Отрасль: X | Зарплата от: X до: X | Требования: X
    """
    desc = vacancy_obj.description or ''
    parts = []

    parts.append(f"Вакансия: {vacancy_obj.title or ''}")

    # Поля из requirements таблицы
    reqs = {vr.requirement.name: vr.value for vr in
            vacancy_obj.vacancy_requirements.select_related('requirement').all()}

    exprns = _extract(desc, 'Требуемый опыт') or reqs.get('Опыт работы', '')
    if exprns:
        parts.append(f"Требуемый опыт: {exprns}")

    employment = _extract(desc, 'Занятость')
    if employment :
        parts.append(f"Занятость: {employment}")

    industry = _extract(desc, 'Отрасль')
    if industry:
        parts.append(f"Отрасль: {industry}")

    salary_min = reqs.get('Зарплата мин', '')
    salary_max = reqs.get('Зарплата макс', '')
    if salary_min or salary_max:
        parts.append(f"Зарплата от: {salary_min} до: {salary_max}")

    requirments = _extract(desc, 'Требования')
    if requirments:
        parts.append(f"Требования: {requirments}")
    elif desc and not any(p.startswith('Требования:') for p in parts):
        parts.append(f"Требования: {desc}")

    return " | ".join(parts)
