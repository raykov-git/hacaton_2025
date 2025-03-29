

from bs4 import BeautifulSoup
import sqlite3
import requests
import re, csv
from datetime import datetime

# .db
url1 = "https://clinica.chitgma.ru/diagnosticheskaya-poliklinika"
url2 = "https://clinica.chitgma.ru/kliniko-diagnosticheskaya-laboratoriya"
url3 = "https://clinica.chitgma.ru/otdelenie-konsultativnoj-pomoshchi-detyam"

# contacts.csv
url4 = "https://clinica.chitgma.ru/diagnosticheskaya-poliklinika"


def create_database():
    # TODO путь
    conn = sqlite3.connect('clinic_schedule.db')
    cursor = conn.cursor()

    # Полностью пересоздаем таблицу (удаляем если существует)
    cursor.execute('DROP TABLE IF EXISTS schedule')
    cursor.execute('''
        CREATE TABLE schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            department TEXT,
            weekday TEXT,
            time TEXT,
            scrape_date TEXT
        )
    ''')
    conn.commit()
    return conn, cursor


def save_to_database(cursor, conn, data):
    for item in data:
        cursor.execute('''
            INSERT INTO schedule (address, department, weekday, time, scrape_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            item['address'],
            item['department'],
            item['weekday'],
            item['time'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    print(f"Данные успешно сохранены в БД")    
    conn.commit()
    

def scrape_clinic_phone(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        all_text = soup.get_text()
        phone_number = re.search(r'8\s?\(\d{3,5}\)\s?\d{2,3}-\d{2}-\d{2}', all_text)
        if phone_number:
            return {
                'department': "Единый центр обработки звонков диагностической поликлиники",
                'phone': phone_number.group()
            }

        return None

    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def save_to_csv(data, filename='contacts.csv'):
    """Функция для сохранения данных контактов колл-центра диагностической поликлиники в CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Подразделение', 'Номер телефона'])
            writer.writerow([data['department'], data['phone']])
        print(f"Данные успешно сохранены в {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")

        
def parse_schedule(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []

        # Улучшенный поиск адресов
        def find_address(table):
            # Ищем в ближайших элементах перед таблицей
            for elem in table.find_all_previous(['p', 'td', 'tr']):
                # Вариант: адрес в strong с цветом #ce5d09
                strong = elem.find('strong', style=lambda s: s and '#ce5d09' in s.lower())
                if not strong:
                    strong = elem.find('strong', color='#ce5d09')
                if strong:
                    address = strong.get_text(strip=True)
                    # Очищаем адрес от лишних пробелов и форматирования
                    address = ' '.join(address.split())
                    # Удаляем возможные повторы "ул. Бабушкина"
                    if 'ул. Бабушкина' in address and address.count('ул. Бабушкина') > 1:
                        address = address.split('ул. Бабушкина')[-1].strip()
                        address = 'ул. Бабушкина ' + address
                    return address



        # Улучшенный поиск подразделений
        def find_department(table):
            department_parts = []

            # Ищем в предыдущих ячейках той же строки
            parent_td = table.find_parent('td')
            if parent_td:
                prev_tds = []
                prev_td = parent_td.find_previous_sibling('td')
                while prev_td:
                    prev_tds.insert(0, prev_td)
                    prev_td = prev_td.find_previous_sibling('td')

                for td in prev_tds:
                    # Собираем весь текст из ячейки (включая многострочные)
                    text = ' '.join(td.stripped_strings)
                    if text:
                        department_parts.append(text)

            # Ищем в тексте перед таблицей
            if not department_parts:
                prev_elem = table.find_previous(['p', 'td'])
                if prev_elem:
                    text = ' '.join(prev_elem.stripped_strings)
                    if text:
                        department_parts.append(text)

            # Объединяем все части подразделения
            department = ' '.join(department_parts)

            # Очистка названия подразделения
            department = ' '.join(department.split())
            department = department.replace('  ', ' ')

            # Удаляем возможные дублирования
            if 'Режим сдачи анализов' in department and department.count('Режим сдачи анализов') > 1:
                department = department.split('Режим сдачи анализов')[-1].strip()
                department = 'Режим сдачи анализов ' + department

            return department

        # Ищем все таблицы с расписанием
        schedule_tables = soup.find_all('table', style=lambda s: s and
                                      ('width: 350px' in str(s) or
                                       'width: 386px' in str(s) or
                                       'width: 387px' in str(s) or
                                       'width: 378px' in str(s)))

        for table in schedule_tables:
            current_address = find_address(table)
            current_department = find_department(table)

            # Парсим расписание
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    weekday = ' '.join(cols[0].get_text(strip=True).split())
                    time = " ".join(cols[1].get_text(strip=True).split())

                    # Очистка данных
                    weekday = weekday.replace(' ,', ',').replace(',,', ',')
                    time = time.replace(' ,', ',').replace(',,', ',')

                    data.append({
                        'address': current_address,
                        'department': current_department,
                        'weekday': weekday,
                        'time': time
                    })

        return data

    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return []



def parse_special_schedule(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []

        # Находим основной контейнер с расписанием
        main_table = soup.find('table', style=lambda s: s and 'width: 644px' in str(s))
        if not main_table:
            return []

        # Извлекаем адрес
        address_elem = main_table.find('strong', style=lambda s: 'color: #ce5d09' in str(s))
        current_address = address_elem.get_text(strip=True) if address_elem else "ул. Бабушкина, 44"

        # Извлекаем подразделение (может потребоваться адаптация под конкретный случай)
        current_department = "Отделение консультативной помощи детям"

        # Находим таблицу с расписанием
        schedule_table = main_table.find('table', style=lambda s: 'width: 628px' in str(s))
        if schedule_table:
            rows = schedule_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    weekday = ' '.join(cols[0].get_text(strip=True).split())
                    time = ' '.join(cols[1].get_text(strip=True).split())

                    data.append({
                        'address': current_address,
                        'department': current_department,
                        'weekday': weekday,
                        'time': time
                    })

        return data

    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return []
        


def main():
    # Создаем/пересоздаем базу данных
    conn, cursor = create_database()
    print("База данных успешно создана/очищена")

    # Парсим данные с url1
    schedule_data = parse_schedule(url1)

    if schedule_data:
        # Сохраняем в базу
        save_to_database(cursor, conn, schedule_data)
        print(f"\nУспешно сохранено {len(schedule_data)} записей")
    else:
        print("Не удалось извлечь данные")

    # Парсим данные с url2
    schedule_data = parse_schedule(url2)

    if schedule_data:
        # Сохраняем в базу
        save_to_database(cursor, conn, schedule_data)
        print(f"\nУспешно сохранено {len(schedule_data)} записей")
    else:
        print("Не удалось извлечь данные")

    # Парсим данные с url3
    schedule_data = parse_special_schedule(url3)

    if schedule_data:
        # Сохраняем в базу
        save_to_database(cursor, conn, schedule_data)
        print(f"\nУспешно сохранено {len(schedule_data)} записей")
    else:
        print("Не удалось извлечь данные")


    # Парсим данные с url4
    result = scrape_clinic_phone(url4)

    if result:
        print(f"Найдены данные")
        # Сохраняем результат в CSV
        save_to_csv(result)
    else:
        print("Не удалось найти телефонный номер на странице")

    # Закрываем соединение
    conn.close()

if __name__ == "__main__":
    main()
    