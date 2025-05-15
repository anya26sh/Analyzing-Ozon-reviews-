import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime


def load_latest_data():
    data_files = glob.glob('../data/ozon_reviews_*.csv')
    if not data_files:
        raise FileNotFoundError("No data files found in the data directory")

    latest_file = max(data_files, key=os.path.getmtime)
    print(f"Loading data from {latest_file}")
    df = pd.read_csv(latest_file, encoding='utf-8-sig')
    return df


def clean_date(date_str):
    if pd.isna(date_str) or date_str == '':
        return pd.NaT

    try:
        # Учитываем формат "изменен 8 мая 2025"
        date_str = date_str.replace('изменен ', '')
        months = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
            'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        parts = date_str.split()
        day = int(parts[0])
        month = months[parts[1].lower()]
        year = int(parts[2])
        date_obj = datetime(year, month, day)
        return date_obj
    except Exception as e:
        print(f"Ошибка преобразования даты '{date_str}': {e}")
        return pd.NaT


def clean_published_at(published_at_str):
    if pd.isna(published_at_str) or published_at_str == '':
        return pd.NaT

    try:
        # Преобразуем строку в целое число
        timestamp = int(float(published_at_str))  # На случай, если это число с плавающей точкой
        # Проверяем, не превышает ли timestamp допустимый диапазон
        max_timestamp = 2 ** 31 - 1  # Максимум для 32-битного времени (2038 год)
        if timestamp > max_timestamp:
            print(f"Предупреждение: timestamp {timestamp} слишком большой. Ограничиваем до 2038 года.")
            timestamp = max_timestamp
        date_obj = datetime.fromtimestamp(timestamp)
        return date_obj
    except (ValueError, OverflowError) as e:
        print(f"Ошибка преобразования published_at '{published_at_str}': {e}")
        return pd.NaT


def extract_text_length(text):
    if pd.isna(text) or text == '':
        return 0
    return len(text)


def clean_data(df):
    clean_df = df.copy()

    # Преобразуем даты
    clean_df['date'] = clean_df['date'].apply(clean_date)
    clean_df['published_at'] = clean_df['published_at'].apply(clean_published_at)

    # Извлекаем год, месяц, день
    clean_df['review_year'] = clean_df['date'].dt.year.fillna(clean_df['published_at'].dt.year)
    clean_df['review_month'] = clean_df['date'].dt.month.fillna(clean_df['published_at'].dt.month)
    clean_df['review_day'] = clean_df['date'].dt.day.fillna(clean_df['published_at'].dt.day)

    # Длина текста
    clean_df['text_length'] = clean_df['text'].apply(extract_text_length)
    clean_df['pros_length'] = clean_df['pros'].apply(extract_text_length)
    clean_df['cons_length'] = clean_df['cons'].apply(extract_text_length)

    # Заполняем пропуски
    clean_df['text'] = clean_df['text'].fillna('')
    clean_df['pros'] = clean_df['pros'].fillna('')
    clean_df['cons'] = clean_df['cons'].fillna('')
    clean_df['author'] = clean_df['author'].fillna('Anonymous')

    # Группировка рейтингов
    def group_rating(rating):
        if pd.isna(rating):
            return 'Unknown'
        rating = int(rating)
        if rating <= 2:
            return 'Negative'
        elif rating == 3:
            return 'Neutral'
        else:
            return 'Positive'

    clean_df['rating_group'] = clean_df['rating'].apply(group_rating)

    # Удаляем дубликаты
    print(f" {len(clean_df)}")
    clean_df.drop_duplicates(subset=['review_id'], keep='first', inplace=True)
    print(f"{len(clean_df)}")

    # Сбрасываем индекс
    clean_df.reset_index(drop=True, inplace=True)

    return clean_df


def save_cleaned_data(df):
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"../data/cleaned_ozon_reviews_{today}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Сохранено в {filename}")
    return filename


def main():
    try:
        df = load_latest_data()
        cleaned_df = clean_data(df)
        save_cleaned_data(cleaned_df)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
