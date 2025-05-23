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

# Function to get Landsat 8 data (Converted to Reflectance) for a specific month
def get_landsat_data(region, year, month):
    start_date = f"{year}-{month:02d}-01"
    end_date = (datetime.datetime(year, month, 1) + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                 .filterBounds(region) \
                 .filterDate(start_date, end_date) \
                 .select(['SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']) \
                 .median()  # Use median to get stable values
    
    # Convert scaled reflectance values
    image = image.multiply(0.0000275).subtract(0.2)
    return image.rename(['L8_B4', 'L8_B5', 'L8_B6', 'L8_B7'])  # Rename to avoid conflicts

# Function to mask clouds in Sentinel-2
def mask_s2_clouds(image):
    cloud_mask = image.select('QA60').lt(10000)  # Less than 10% cloud probability
    return image.updateMask(cloud_mask).divide(10000)  # Normalize reflectance


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

    for year in range(2019, 2024):  # From 2018 to 2023
        print(f"📅 Year: {year}")

        landsat_dfs = []


        for month in range(1, 13):  # January to December
            print(f"   🔄 Processing Month: {month:02d}")

            # Fetch Landsat data
            landsat_img = get_landsat_data(region, year, month)
            landsat_df = image_to_dataframe(landsat_img, region)
            if not landsat_df.empty:
                landsat_df['Year'] = year
                landsat_df['Month'] = month
                landsat_dfs.append(landsat_df)



            # Wait to avoid exceeding memory limits
            time.sleep(5)

        # Combine all months of the year into one DataFrame
        landsat_final_df = pd.concat(landsat_dfs, axis=0).dropna() if landsat_dfs else pd.DataFrame()
        
        # Save data for each year
        if not landsat_final_df.empty:
            landsat_final_df.to_csv(f'{state}_landsat_{year}.csv', index=False)


        print(f"✅ Data saved for {state}, {year}.\n")

print("✅✅✅ All states processed successfully! 🚀")
