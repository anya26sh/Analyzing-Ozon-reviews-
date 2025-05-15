import os
import subprocess
import sys
import time
from datetime import datetime

# Импорт функций из других модулей проекта
from scripts.scrape_ozon_reviews import scrape_ozon_reviews, driver, save_raw_data
from scripts.data_cleaning import load_latest_data, clean_data, save_cleaned_data

# URL для парсинга отзывов
OZON_URL = "https://www.ozon.ru/product/umnaya-kolonka-yandeks-stantsiya-2-s-alisoy-na-yagpt-pesochnyy-30vt-697054148/?reviewsVariantMode=1&sh=Iqml_fOO7g&start_page_id=323c825e2707dd3bc8fed2d41043921d"


def run_scraping():
    """
    Функция для запуска этапа сбора данных.
    Использует scrape_ozon_reviews.py для парсинга отзывов с Ozon.
    """
    print("Этап 1: Сбор данных с Ozon...")
    try:
        # Инициализация веб-драйвера для парсинга
        browser = driver()
        # Парсинг отзывов с указанного URL
        df = scrape_ozon_reviews(OZON_URL, browser)
        if not df.empty:
            # Сохранение сырых данных в CSV
            raw_file = save_raw_data(df)
            print(f"Данные успешно собраны и сохранены в {raw_file}")
        else:
            print("Не удалось собрать данные. Проверьте URL или подключение.")
            sys.exit(1)
    except Exception as e:
        print(f"Ошибка на этапе сбора данных: {e}")
        sys.exit(1)


def run_data_cleaning():
    """
    Функция для запуска этапа очистки данных.
    Использует data_cleaning.py для обработки сырых данных.
    """
    print("Этап 2: Очистка данных...")
    try:
        # Загрузка последнего файла с сырыми данными
        df = load_latest_data()
        print(f"Загружено {len(df)} отзывов для очистки.")
        # Очистка данных (преобразование дат, удаление дубликатов и т.д.)
        cleaned_df = clean_data(df)
        # Сохранение очищенных данных
        cleaned_file = save_cleaned_data(cleaned_df)
        print(f"Очищенные данные сохранены в {cleaned_file}")
    except Exception as e:
        print(f"Ошибка на этапе очистки данных: {e}")
        sys.exit(1)


def run_analysis():
    """
    Функция для запуска этапа анализа данных.
    Выполняет Jupyter Notebook (data_analysis.ipynb) для анализа.
    """
    print("Этап 3: Анализ данных...")
    try:
        notebook_path = os.path.join("../notebooks", "data_analysis.ipynb")
        if not os.path.exists(notebook_path):
            print(f"Ноутбук {notebook_path} не найден.")
            sys.exit(1)

        # Команда для выполнения Jupyter Notebook с помощью nbconvert
        command = [
            "jupyter", "nbconvert", "--to", "notebook", "--execute",
            "--inplace", notebook_path
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("Анализ данных успешно выполнен. Результаты доступны в data_analysis.ipynb")
        else:
            print("Ошибка при выполнении анализа данных:")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Ошибка на этапе анализа данных: {e}")
        sys.exit(1)


def run_flask_dashboard():
    """
    Функция для запуска Flask-дашборда.
    Запускает app.py в отдельном процессе.
    """
    print("Этап 4: Запуск Flask-дашборда...")
    try:
        # Запуск Flask-приложения в отдельном процессе
        flask_process = subprocess.Popen(
            [sys.executable, os.path.join("../dashboard", "app.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Flask-дашборд запущен. Доступен по адресу http://localhost:5000")
        return flask_process
    except Exception as e:
        print(f"Ошибка при запуске Flask-дашборда: {e}")
        sys.exit(1)


def run_dash_dashboard():
    """
    Функция для запуска Dash-дашборда.
    Запускает dashboard_for_data_analysis.py в отдельном процессе.
    """
    print("Этап 5: Запуск Dash-дашборда...")
    try:
        # Запуск Dash-приложения в отдельном процессе
        dash_process = subprocess.Popen(
            [sys.executable, os.path.join("../dashboard", "dashboard_for_data_analysis.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dash-дашборд запущен. Доступен по адресу http://localhost:8050")
        return dash_process
    except Exception as e:
        print(f"Ошибка при запуске Dash-дашборда: {e}")
        sys.exit(1)


def main():
    """
    Главная функция для последовательного выполнения всех этапов проекта.
    """
    print(f"Запуск проекта анализа отзывов Ozon")

    # Этап 1: Сбор данных
    run_scraping()

    # Этап 2: Очистка данных
    run_data_cleaning()

    # Этап 3: Анализ данных
    run_analysis()

    # Этап 4: Запуск Flask-дашборда
    flask_process = run_flask_dashboard()

    # Этап 5: Запуск Dash-дашборда
    dash_process = run_dash_dashboard()

    # Ожидание завершения работы дашбордов (нажмите Ctrl+C для остановки)
    try:
        print("Дашборды запущены. Нажмите Ctrl+C для завершения работы.")
        while True:
            time.sleep(1)  # Бесконечный цикл для поддержания работы дашбордов
    except KeyboardInterrupt:
        print("Завершение работы дашбордов...")
        # Завершение процессов Flask и Dash
        flask_process.terminate()
        dash_process.terminate()
        print("Работа завершена.")


if __name__ == "__main__":
    main()