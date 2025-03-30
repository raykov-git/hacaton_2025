import sqlite3
from collections import defaultdict
import csv, re

def get_grouped_schedule():
    """Получает и структурирует данные расписания из БД"""
    # Устанавливаем соединение с базой данных
    conn = sqlite3.connect('files/clinic_schedule.db')

    cursor = conn.cursor()

    # Подготавливаем структуру для возвращаемого результата
    result = {
        'data': defaultdict(list),
        'total_departments': 0,
        'total_records': 0,
        'error': None
    }

    try:
        # Выполняем SQL-запрос для получения расписания
        # Сортируем по отделениям и дням недели для удобной группировки
        cursor.execute('SELECT address, department, weekday, time FROM schedule ORDER BY department, weekday')
        records = cursor.fetchall()
        result['total_records'] = len(records)

        # Если нет данных, возвращаем пустой результат
        if not records:
            return result
        # Группируем данные по комбинации адрес+отделение
        for address, department, weekday, time in records:
            result['data'][(address, department)].append((weekday, time))

        result['total_departments'] = len(result['data'])

    except sqlite3.Error as e:
        result['error'] = str(e)
    finally:
        conn.close()

    return result

# Преобразование данных расписания в текстовый формат
def format_schedule_as_text(data):
    if data['error']:
        return f"Ошибка: {data['error']}"

    if not data['data']:
        return "В базе данных нет записей."

    text_lines = []

    for i, ((address, department), schedules) in enumerate(data['data'].items(), 1):
        text_lines.append(f" Адрес: {address or 'Не указан'}")
        text_lines.append(f"   Подразделение: {department or 'Не указано'}")
        text_lines.append("   Режим работы:")

        for weekday, time in schedules:
            text_lines.append(f"     - {weekday}: {time}")
    # Объединяем все строки
    return '\n'.join(text_lines)



def get_contacts_as_text(csv_file='files/contacts.csv'):
    """
    Читает CSV-файл с контактами и возвращает данные в текстовом формате

    Args:
        csv_file (str): Путь к CSV-файлу (по умолчанию 'contacts.csv')

    Returns:
        str: Отформатированная текстовая строка с контактами
    """
    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Формируем текстовый вывод
            text_output = "Список контактов подразделений:\n"

            for i, row in enumerate(reader, 1):
                text_output += (
                    f"{i}. Подразделение: {row['подразделение']}\n"
                    f"   Телефон: {row['номер телефона']}\n"
                )

            return text_output

    except FileNotFoundError:
        return f"Ошибка: файл {csv_file} не найден"
    except Exception as e:
        return f"Ошибка при чтении файла: {str(e)}"


# Функция предобработки текста
#def preprocess_text(text):
#    if text is None:  # Проверка на None
#        return ""
#    text = text.lower()
#    text = re.sub(r"[^a-zа-яё\s]", "", text)
#    return text.strip()