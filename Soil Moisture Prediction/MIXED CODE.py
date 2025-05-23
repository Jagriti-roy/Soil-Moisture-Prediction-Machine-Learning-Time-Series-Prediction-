from qgis.core import *
from qgis.utils import iface
import ee
import pandas as pd
import time
import datetime

# Authenticate and initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# Dictionary of drought-prone Indian states with bounding boxes
states_regions = {
    "Maharashtra": ee.Geometry.BBox(72.5, 15.5, 80.5, 22.0)
}

# Function to get Landsat 8 data
def get_landsat_data(region, year, month):
    start_date = f"{year}-{month:02d}-01"
    end_date = (datetime.datetime(year, month, 1) + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                 .filterBounds(region) \
                 .filterDate(start_date, end_date) \
                 .select(['SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']) \
                 .median()
    image = image.multiply(0.0000275).subtract(0.2)
    return image.rename(['L8_B4', 'L8_B5', 'L8_B6', 'L8_B7'])

# Function to mask clouds in Sentinel-2
def mask_s2_clouds(image):
    cloud_mask = image.select('QA60').lt(10000)
    return image.updateMask(cloud_mask).divide(10000)

# Function to get Sentinel-2 data
def get_sentinel2_data(region, year, month):
    start_date = f"{year}-{month:02d}-01"
    end_date = (datetime.datetime(year, month, 1) + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
              .filterBounds(region) \
              .filterDate(start_date, end_date) \
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
              .map(mask_s2_clouds) \
              .select(['B4', 'B5', 'B6', 'B7', 'B8']) \
              .median()
    return image.rename(['S2_B4', 'S2_B5', 'S2_B6', 'S2_B7', 'S2_B8'])

# Function to get soil moisture data
def get_soil_moisture_data(region, year):
    image_collection = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007") \
                        .filterBounds(region) \
                        .filterDate(f'{year}-01-01', f'{year}-12-31') \
                        .select(['sm_surface'])

    all_months_data = []
    for month in range(1, 13):
        month_start = f"{year}-{month:02d}-01"
        month_end = f"{year}-{month:02d}-28"
        image = image_collection.filterDate(month_start, month_end).mean()

        if image.bandNames().size().getInfo() == 0:
            print(f"⚠ No valid image found for month {month}. Skipping.")
            continue

        sampled_points = image.sample(region=region, scale=750, numPixels=5000, seed=42, projection='EPSG:4326')
        try:
            features = sampled_points.getInfo()['features']
            if len(features) == 0:
                print(f"⚠ No data extracted for month {month}. Skipping.")
                continue
            properties = [f['properties'] for f in features]
            df = pd.DataFrame(properties)
            df['Month'] = month
            if len(df) > 750:
                df = df.sample(n=750, random_state=42).reset_index(drop=True)
            elif len(df) < 750:
                df = df.sample(n=750, replace=True, random_state=42).reset_index(drop=True)
            all_months_data.append(df)
        except Exception as e:
            print(f"❌ Error extracting soil moisture data for month {month}:", e)

    return pd.concat(all_months_data, ignore_index=True) if all_months_data else pd.DataFrame()

# Function to extract and save data
def extract_and_save_data():
    for state, region in states_regions.items():
        print(f"🚀 Processing {state}...")
        for year in range(2019, 2024):
            print(f"📅 Year: {year}")
            
            landsat_df, sentinel2_df, smap_df = [], [], []
            for month in range(1, 13):
                print(f"   🔄 Processing Month: {month:02d}")
                
                landsat_img = get_landsat_data(region, year, month)
                sentinel2_img = get_sentinel2_data(region, year, month)
                smap_img = get_soil_moisture_data(region, year)
                
                landsat_data = image_to_dataframe(landsat_img, region)
                sentinel2_data = image_to_dataframe(sentinel2_img, region)
                
                if not landsat_data.empty and not sentinel2_data.empty:
                    landsat_data['Year'] = sentinel2_data['Year'] = year
                    landsat_data['Month'] = sentinel2_data['Month'] = month
                    landsat_df.append(landsat_data)
                    sentinel2_df.append(sentinel2_data)
                    
                time.sleep(5)
            
            if landsat_df:
                pd.concat(landsat_df).to_csv(f'{state}_landsat_{year}.csv', index=False)
            if sentinel2_df:
                pd.concat(sentinel2_df).to_csv(f'{state}_sentinel2_{year}.csv', index=False)
            if not smap_df.empty:
                smap_df.to_csv(f'{state}_soil_moisture_{year}.csv', index=False)

            print(f"✅ Data saved for {state}, {year}.")

extract_and_save_data()
print("✅✅✅ All data extracted successfully! 🚀")
