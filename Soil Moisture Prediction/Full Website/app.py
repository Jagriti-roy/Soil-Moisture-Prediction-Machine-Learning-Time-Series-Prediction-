from flask import Flask, render_template, request, url_for
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import os
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime

app = Flask(__name__)

def get_monthly_climatology(file_path):
    df = pd.read_csv(file_path)
    monthly_avg = df.groupby('Month').mean().reset_index()
    feature_cols = monthly_avg.columns.difference(['sm_surface', 'Year'])
    monthly_avg = monthly_avg[feature_cols]
    return df, monthly_avg

def generate_future_data(monthly_avg, years, original_df):
    future_years = list(range(2025, 2025 + int(years)))
    future_data = []

    for year in future_years:
        for _, row in monthly_avg.iterrows():
            data_row = row.to_dict()
            data_row['Year'] = year
            data_row['Month'] = int(row['Month'])
            future_data.append(data_row)

    future_df = pd.DataFrame(future_data)
    ordered_cols = [col for col in original_df.columns if col != 'sm_surface']
    future_df = future_df[ordered_cols]
    return future_df,future_years

def evaluate_model(model, X):
    preds = model.predict(X)
    return preds

def compute_metrics(y_pred):
    r2 = r2_score([0]*len(y_pred), y_pred)
    rmse = root_mean_squared_error([0]*len(y_pred), y_pred)
    mae = mean_absolute_error([0]*len(y_pred), y_pred)
    return r2, rmse, mae

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    region = request.form['region'].replace(" ", "").lower()
    years = int(request.form['years'])

    state_title = region.title().replace(" ", "")
    csv_path = f"Data - {state_title} Done.csv"
    df, monthly_avg = get_monthly_climatology(csv_path)
    future_df, future_years = generate_future_data(monthly_avg, years, df)
    

    model_dir = os.path.join('models', state_title)
    model_files = {
        "Random Forest": next((f for f in os.listdir(model_dir) if "Random" in f), None),
        "XGBoost": next((f for f in os.listdir(model_dir) if "XGB" in f), None),
        "LightGBM": next((f for f in os.listdir(model_dir) if "LGBM" in f), None),
        "GBR Model": next((f for f in os.listdir(model_dir) if "GBR" in f), None)
    }

    results = {}
    preds_all = {}
    r2_list, rmse_list, mae_list = [], [], []

    for model_name, file_name in model_files.items():
        if file_name:
            model_path = os.path.join(model_dir, file_name)
            model = joblib.load(model_path)
            preds = evaluate_model(model, future_df)
            preds_all[model_name] = preds
            r2, rmse, mae = compute_metrics(preds)
            r2_list.append(r2)
            rmse_list.append(rmse)
            mae_list.append(mae)
            results[model_name] = {
                'r2': round(r2, 3),
                'rmse': round(rmse, 3),
                'mae': round(mae, 3)
            }

    plt.figure(figsize=(10, 4))
    for name, preds in preds_all.items():
        plt.plot(preds[:100], label=name)
    plt.title(f"Soil Moisture Forecast for {state_title}")
    plt.xlabel("Sample Index")
    plt.ylabel("Soil Moisture")
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/trend_plot.png")
    plt.close()

    plt.figure(figsize=(6, 4))
    for name, preds in preds_all.items():
        plt.plot(preds[:100], label=name)
    plt.title("Predicted Soil Moisture (No Actual Available)")
    plt.xlabel("Index")
    plt.ylabel("Soil Moisture")
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/actual_vs_pred.png")
    plt.close()

    selected_model = 'XGBoost'
    forecast_values = preds_all[selected_model]

    # Split forecast values into yearly & monthly predictions
    forecast_array = np.array(forecast_values).reshape(years, 12)
    yearly_predictions = forecast_array.mean(axis=1)
    monthly_predictions = forecast_array.tolist()
    forecast_years = [datetime.now().year + i + 1 for i in range(years)]
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    start_year = datetime.now().year
    total_months = len(forecast_values)
    forecast_dates = pd.date_range(start=f'{start_year}-01', periods=total_months, freq='M')

    # Step 1: Prepare monthly labels
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Step 2: Break down forecast into monthly/yearly values
    forecast_years = list(range(start_year, start_year + years))
    forecast_values = preds_all[selected_model]

    # Ensure total values = years * 12
    forecast_values = forecast_values[:years * 12]
    monthly_predictions = [forecast_values[i * 12:(i + 1) * 12] for i in range(years)]
    yearly_predictions = [round(np.mean(month), 3) for month in monthly_predictions]

    # Step 3: Zip year and monthly values for Jinja2
    yearly_data = list(zip(forecast_years, yearly_predictions))
    # Pre-zip month labels with each monthly prediction
    monthly_data = [
        (year, list(zip(month_labels, monthly)))
        for year, monthly in zip(forecast_years, monthly_predictions)
    ]

    
    plt.figure(figsize=(10, 5))
    plt.plot(forecast_dates, forecast_values, marker='o', linestyle='-', color='seagreen')
    plt.title(f"📆 Soil Moisture Forecast ({forecast_dates[0].year}–{forecast_dates[-1].year})")
    plt.xlabel("Date")
    plt.ylabel("Predicted Soil Moisture (%)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/forecast_trend.png")
    plt.close()
    

    return render_template('result.html',
                           years=years,
                           r2=max(r2_list),
                           rmse=min(rmse_list),
                           mae=min(mae_list),
                           prediction=round(np.median(forecast_values), 5),
                           rf_r2=results['Random Forest']['r2'], rf_rmse=results['Random Forest']['rmse'], rf_mae=results['Random Forest']['mae'],
                           xgb_r2=results['XGBoost']['r2'], xgb_rmse=results['XGBoost']['rmse'], xgb_mae=results['XGBoost']['mae'],
                           lgbm_r2=results['LightGBM']['r2'], lgbm_rmse=results['LightGBM']['rmse'], lgbm_mae=results['LightGBM']['mae'],
                           hybrid_r2=results['GBR Model']['r2'], hybrid_rmse=results['GBR Model']['rmse'], hybrid_mae=results['GBR Model']['mae'],
                           forecast_years=forecast_years,
                            yearly_data=yearly_data,
                            monthly_data=monthly_data,
                            month_labels=month_labels,)

if __name__ == '__main__':
    app.run(debug=True)

