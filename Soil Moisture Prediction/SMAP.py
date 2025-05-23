from qgis.core import *
from qgis.utils import iface
import ee
import pandas as pd

# Initialize Google Earth Engine
ee.Initialize()


# Dictionary of drought-prone Indian states with bounding boxes
states_regions = {
    "Rajasthan": ee.Geometry.BBox(69.5, 23.3, 76.5, 30.2)
    
}

# Function to get soil moisture data ensuring 750 rows per month
def get_soil_moisture_data(region):
    image_collection = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007") \
                        .filterBounds(region) \
                        .filterDate('2020-01-01', '2020-12-31') \
                        .select(['sm_surface'])

    all_months_data = []

    for month in range(1, 13):
        # Filter for the specific month
        month_start = f"2023-{str(month).zfill(2)}-01"
        month_end = f"2023-{str(month).zfill(2)}-28"  # End of the month
        image = image_collection.filterDate(month_start, month_end).mean()

        sampled_points = image.sample(
            region=region,
            scale=750,
            numPixels=5000,
            seed=42,
            projection='EPSG:4326'  # Specify CRS explicitly
        )

        # Convert to Pandas DataFrame (with size check)
        try:
            features = sampled_points.getInfo()['features']
            if len(features) == 0:
                print(f"⚠ No data extracted for month {month}. Skipping.")
                continue
            properties = [f['properties'] for f in features]
            df = pd.DataFrame(properties)
            df['Month'] = month

            # Ensure exactly 750 rows per month
            if len(df) > 750:
                df = df.sample(n=750, random_state=42).reset_index(drop=True)
            elif len(df) < 750:
                df = df.sample(n=750, replace=True, random_state=42).reset_index(drop=True)

            all_months_data.append(df)

        except Exception as e:
            print(f"❌ Error extracting soil moisture data for month {month}:", e)

    # Concatenate all months
    if all_months_data:
        final_df = pd.concat(all_months_data, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()

# Process each state
for state, region in states_regions.items():
    print(f"🚀 Processing {state} for 2020...")
    soil_moisture_df = get_soil_moisture_data(region)
    
    if not soil_moisture_df.empty:
        output_file = f"{state}_soil_moisture_2020_9000rows.csv"
        soil_moisture_df.to_csv(output_file, index=False)
        print(f"✅ Saved {output_file} ({len(soil_moisture_df)} rows)")
    else:
        print(f"⚠ No data saved for {state}")

print("🎯 All months processed successfully!")
