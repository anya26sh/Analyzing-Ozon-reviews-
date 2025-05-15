from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)


total_reviews = 0
avg_rating = 0.0
avg_text_length = 0.0
rating_data = []
hourly_data = []
text_length_data = []
correlation_data = []
sample_data = []
filtered_df = None
eda_columns = []
eda_dtypes = []
eda_missing = []
eda_numeric_stats = []

def load_data(start_date=None, end_date=None, category=None):
    global total_reviews, avg_rating, avg_text_length, rating_data, hourly_data, text_length_data, correlation_data, sample_data, filtered_df, eda_columns, eda_dtypes, eda_missing, eda_numeric_stats
    df = pd.read_csv('../data/cleaned_ozon_reviews_2025-05-13.csv')


    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[filtered_df['published_at'] >= start_date]
    if end_date:
        filtered_df = filtered_df[filtered_df['published_at'] <= end_date]
    if category and category != 'all':
        filtered_df = filtered_df[filtered_df['category'] == category]  # Adjust 'category' to your column name

    total_reviews = len(filtered_df)
    avg_rating = filtered_df['rating'].mean() if not filtered_df.empty else 0.0
    avg_text_length = filtered_df['text_length'].mean() if not filtered_df.empty else 0.0

    rating_distribution = filtered_df['rating'].value_counts().sort_index().to_dict()
    rating_data = [{'rating': k, 'count': v} for k, v in rating_distribution.items()]

    hourly_distribution = filtered_df['published_at'].str.split(' ').str[1].str.split(':').str[0].astype(int).value_counts().sort_index().to_dict()
    hourly_data = [{'hour': k, 'count': v} for k, v in hourly_distribution.items()]

    text_length_ranges = pd.cut(filtered_df['text_length'], bins=[0, 20, 40, 60, 80, 100, 150, 200, float('inf')],
                               labels=['0-20', '21-40', '41-60', '61-80', '81-100', '101-150', '151-200', '201+']).value_counts().sort_index().to_dict()
    text_length_data = [{'range': k, 'count': v} for k, v in text_length_ranges.items()]

    correlation_data = [
        {'rating': 1, 'avgLength': 85},
        {'rating': 2, 'avgLength': 75},
        {'rating': 3, 'avgLength': 65},
        {'rating': 4, 'avgLength': 60},
        {'rating': 5, 'avgLength': 45}
    ]
    sample_data = filtered_df.head().to_dict(orient='records') if not filtered_df.empty else []


    eda_columns = filtered_df.columns.tolist()
    eda_dtypes = filtered_df.dtypes.astype(str).to_dict()
    eda_missing = filtered_df.isnull().sum().to_dict()

    numeric_cols = filtered_df.select_dtypes(include=['int64', 'float64']).columns
    eda_numeric_stats = {col: {
        'mean': filtered_df[col].mean(),
        'min': filtered_df[col].min(),
        'max': filtered_df[col].max(),
        'std': filtered_df[col].std()
    } for col in numeric_cols}


load_data()

scheduler = BackgroundScheduler()
scheduler.add_job(load_data, 'interval', minutes=1)
scheduler.start()

@app.route('/', methods=['GET'])
def dashboard():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category', 'all')
    load_data(start_date, end_date, category)
    return render_template('index.html',
                           total_reviews=total_reviews,
                           avg_rating=avg_rating,
                           avg_text_length=avg_text_length,
                           rating_data=json.dumps(rating_data),
                           hourly_data=json.dumps(hourly_data),
                           text_length_data=json.dumps(text_length_data),
                           correlation_data=json.dumps(correlation_data),
                           sample_data=sample_data,
                           start_date=start_date or '',
                           end_date=end_date or '',
                           category=category,
                           eda_columns=eda_columns,
                           eda_dtypes=eda_dtypes,
                           eda_missing=eda_missing,
                           eda_numeric_stats=eda_numeric_stats)

@app.route('/refresh_data', methods=['GET'])
def refresh_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category', 'all')
    load_data(start_date, end_date, category)
    return jsonify({
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'avg_text_length': avg_text_length,
        'rating_data': rating_data,
        'hourly_data': hourly_data,
        'text_length_data': text_length_data,
        'correlation_data': correlation_data,
        'sample_data': sample_data,
        'eda_columns': eda_columns,
        'eda_dtypes': eda_dtypes,
        'eda_missing': eda_missing,
        'eda_numeric_stats': eda_numeric_stats
    })


import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)