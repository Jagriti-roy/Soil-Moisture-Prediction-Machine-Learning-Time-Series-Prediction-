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
    "Bihar": ee.Geometry.BBox(83.0, 24.5, 88.0, 27.5)
}

# Function to mask clouds in Sentinel-2
def mask_s2_clouds(image):
    cloud_mask = image.select('QA60').lt(10000)  # Less than 10% cloud probability
    return image.updateMask(cloud_mask).divide(10000)  # Normalize reflectance

# Function to get Sentinel-2 data for a specific month
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

    # Force CRS to WGS84 to avoid missing CRS error
    image = image.setDefaultProjection('EPSG:4326', None, 10)

    return image.rename(['S2_B4', 'S2_B5', 'S2_B6', 'S2_B7', 'S2_B8'])

# Function to sample image data properly
def image_to_dataframe(image, region, scale=750, numPixels=1000):
    try:
        sampled_points = image.sample(
            region=region,
            scale=scale,
            numPixels=numPixels,
            geometries=True
        )
        features = sampled_points.getInfo()['features']
        properties = [f['properties'] for f in features]
        return pd.DataFrame(properties)
    except Exception as e:
        print("Error extracting data:", e)
        return pd.DataFrame()

# Main loop: Process each state, year, and month
for state, region in states_regions.items():
    print(f"Processing {state}...")

    for year in range(2020, 2021):  # From 2018 to 2023
        print(f"📅 Year: {year}")

        sentinel2_dfs = []

        for month in range(1, 13):  # January to December
            print(f"   🔄 Processing Month: {month:02d}")

            # Fetch Sentinel-2 data
            sentinel2_img = get_sentinel2_data(region, year, month)
            sentinel2_df = image_to_dataframe(sentinel2_img, region)

            if not sentinel2_df.empty:
                sentinel2_df['Year'] = year
                sentinel2_df['Month'] = month
                sentinel2_dfs.append(sentinel2_df)

            # Wait to avoid exceeding memory limits
            time.sleep(5)

        # Combine all months of the year into one DataFrame
        sentinel2_final_df = pd.concat(sentinel2_dfs, axis=0).dropna() if sentinel2_dfs else pd.DataFrame()

        # Save Sentinel-2 data for each year
        if not sentinel2_final_df.empty:
            sentinel2_final_df.to_csv(f'{state}_sentinel2_{year}.csv', index=False)
            print(f"✅ Data saved for {state}, {year}.")

print("✅✅✅ All Sentinel-2 data processed successfully! 🚀")
