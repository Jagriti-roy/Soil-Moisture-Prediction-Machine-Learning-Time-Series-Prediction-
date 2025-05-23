# 🌾 Soil Moisture Forecasting Using Remote Sensing and Machine Learning

This project predicts **soil moisture** for the next 1–10 years using satellite data (Sentinel-2, Landsat-8, SMAP) and machine learning models (Random Forest, XGBoost, LightGBM, GBR). The system is deployed via a Flask web app for easy access and visualization.

---

## 📌 Table of Contents
- [📖 About the Project](#about-the-project)
- [🛰️ Data Sources](#data-sources)
- [🧠 Machine Learning Models](#machine-learning-models)
- [⚙️ Features](#features)
- [📊 Visualizations](#visualizations)
- [🌍 Use Case](#use-case)
- [💻 Running the App](#running-the-app)
- [📦 Project Structure](#project-structure)
- [📈 Performance](#performance)
- [🧩 Future Work](#future-work)

---

## 📖 About the Project

Soil moisture is a key parameter in agriculture and drought monitoring. However, physical sensors are expensive and hard to maintain. This project uses **remote sensing data** and **machine learning** to forecast soil moisture **without IoT devices**, making it cost-effective and scalable.

---

## 🛰️ Data Sources

- **Sentinel-2**: Surface reflectance data (Bands: B4, B5, B6, B7, B8)
- **Landsat-8**: Reflectance bands (B4–B7)
- **NASA SMAP**: Surface soil moisture (used as target)

Processed using: **Google Earth Engine**

---

## 🧠 Machine Learning Models

The following regression models were trained using historical satellite features:

- ✅ Random Forest Regressor
- ✅ XGBoost Regressor
- ✅ LightGBM Regressor
- ✅ Gradient Boosting Regressor (GBR)

Forecasts are made for future years by simulating input features using climatology.

---

## ⚙️ Features

- 📁 Uploads or selects a region/state
- 📅 Forecasts soil moisture for next 1–10 years
- 📊 Visualizes predicted trends and metrics
- ✅ Supports multiple ML models and comparisons
- 🚫 No IoT sensor required – purely satellite-based

---

## 📊 Visualizations

- Soil moisture trends over time
- Model performance metrics (R², RMSE, MAE)
- Comparison across models
- Monthly and yearly predictions

---

## 🌍 Use Case

- 📉 Drought prediction and mitigation
- 💧 Smart irrigation planning
- 📊 Agricultural resource management
- 🌱 Research & policy decision-making

---

## 💻 Running the App

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/soil-moisture-forecast.git
cd soil-moisture-forecast

2. Install Requirements
pip install -r requirements.txt

3. Run the Flask App
python app.py

4. 📦 Project Structure
📁 static/
    └── Forecast images and plots
📁 templates/
    ├── index.html
    └── result.html
📄 app.py
📄 requirements.txt

5. 📈 Performance
| Model             | R² Score | RMSE  | MAE   |
| ----------------- | -------- | ----- | ----- |
| Random Forest     | 0.82     | 0.040 | 0.030 |
| XGBoost           | 0.84     | 0.030 | 0.025 |
| LightGBM          | 0.86     | 0.028 | 0.021 |
| Gradient Boosting | 0.87     | 0.026 | 0.020 |


🧩 Future Work:
Integrate real-time weather forecast data

Add LSTM or deep learning for time series modeling

Enable state-wise interactive maps

Add forecast export as PDF/Excel


🛠️ Built With
Python, Flask

scikit-learn, XGBoost, LightGBM

Pandas, Matplotlib

Google Earth Engine

Tailwind CSS (for frontend)


📫 Contact
Made with ❤️ by Jagriti Kumari

For questions, drop a mail at royjagriti2003@gmail.com
