from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time
import pandas as pd
import os
from datetime import datetime


def driver():
    # Настройка Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--headless")  # Отключить для отображения браузера

    # Настройка пользовательских заголовков
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Инициализация драйвера
    browser = webdriver.Chrome(options=chrome_options)

    # Использование stealth для маскировки автоматизации
    stealth(browser,
            languages=["ru-RU", "ru"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=False
            )
    # Установка разрешения окна браузера
    browser.set_window_size(1600, 2200)
    time.sleep(4)

    return browser


def gradual_scroll(driver):
    scroll_step = 1600  # Размер шага прокрутки (в пикселях)
    max_iterations = 500  # Ограничение на количество итераций
    previous_height = 0
    iteration = 0
    current_position = 0

    while iteration < max_iterations:
        # Получаем текущую высоту страницы
        page_height = driver.execute_script("return document.body.scrollHeight")
        print(f"Итерация {iteration + 1}: Текущая высота страницы: {page_height}px, Позиция: {current_position}px")

        # Прокручиваем на шаг вниз
        current_position += scroll_step
        driver.execute_script(f"window.scrollTo({{ top: {current_position}, behavior: 'smooth' }});")
        time.sleep(10)  # Даем время на подгрузку контента

        # Проверяем новую высоту страницы
        new_page_height = driver.execute_script("return document.body.scrollHeight")

        # Если высота увеличилась, обновляем значение и продолжаем
        if new_page_height > previous_height:
            print(f"Высота страницы увеличилась: {new_page_height}px")

        previous_height = new_page_height
        iteration += 1

    # Проверяем, сколько отзывов подгрузилось
    review_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.qs_31')
    print(f"Подгружено {len(review_blocks)} отзывов после скроллинга.")
    return len(review_blocks)


def scrape_ozon_reviews(url, driver):
    try:
        driver.get(url)
        time.sleep(3)

        # Постепенный скроллинг
        gradual_scroll(driver)

        # Собираем отзывы
        review_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.qs_31')

        reviews_data = []
        for block in review_blocks:
            try:
                review_id = block.get_attribute('data-review-uuid') or 'unknown'
                published_at = block.get_attribute('publishedat') or ''  # Оставляем как строку
                author_elem = block.find_element(By.CSS_SELECTOR, 'span.py0_31')
                author = author_elem.text.strip() if author_elem else 'Anonymous'
                date_elem = block.find_element(By.CSS_SELECTOR, 'div.r2q_31')
                date = date_elem.text.strip() if date_elem else ''
                rating_stars = block.find_elements(By.CSS_SELECTOR, 'div.q3r_31 svg')
                rating = sum(1 for star in rating_stars if 'rgb(255, 165, 0)' in star.get_attribute('style'))
                text_elem = block.find_element(By.CSS_SELECTOR, 'span.q4r_31')
                text = text_elem.text.strip() if text_elem else ''
                pros = ''
                cons = ''

                review = {
                    'review_id': review_id,
                    'published_at': published_at,
                    'author': author,
                    'date': date,
                    'rating': rating,
                    'text': text,
                    'pros': pros,
                    'cons': cons
                }
                reviews_data.append(review)
            except Exception as e:
                print(f"Ошибка при парсинге отзыва: {e}")
                continue

        df = pd.DataFrame(reviews_data)
        print(f"Собрано {len(df)} отзывов.")
        return df

    except Exception as e:
        print(f"Ошибка при сборе данных: {e}")
        return pd.DataFrame()
    finally:
        driver.quit()


def save_raw_data(df):
    os.makedirs('data', exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"data/ozon_reviews_{today}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Сохранено в {filename}")
    return filename


if __name__ == "__main__":
    url = "https://www.ozon.ru/product/umnaya-kolonka-yandeks-stantsiya-2-s-alisoy-na-yagpt-pesochnyy-30vt-697054148/?reviewsVariantMode=1&sh=Iqml_fOO7g&start_page_id=323c825e2707dd3bc8fed2d41043921d"
    df = scrape_ozon_reviews(url, driver())
    if not df.empty:
        save_raw_data(df)
    else:
        print("Не удалось собрать данные.")