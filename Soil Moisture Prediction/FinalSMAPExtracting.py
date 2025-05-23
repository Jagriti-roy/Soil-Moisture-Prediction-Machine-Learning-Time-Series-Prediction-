from qgis.core import *
from qgis.utils import iface
import ee
import pandas as pd
import time

# Dictionary of drought-prone Indian states with bounding boxes
states_regions = {
    "Rajasthan": ee.Geometry.BBox(69.5, 23.3, 76.5, 30.2)
}


# Function to get minimum soil moisture data to avoid memory issues
def get_soil_moisture_data(region):
    image = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007") \
                .filterBounds(region) \
                .filterDate('2019-01-01', '2024-12-31') \
                .select(['sm_surface']) \
                .first()

    # Sample at SMAP resolution (~9 km)
    sampled_points = image.sample(
        region=region,
        scale=750,  # Match SMAP pixel size
        numPixels=1000,  # Start with only 10 pixels!
        seed=42  # Ensure reproducibility
    )

    # Convert to Pandas DataFrame (with size check)
    try:
        features = sampled_points.getInfo()['features']
        if len(features) == 0:
            print("No data extracted. Try increasing numPixels or time range.")
            return pd.DataFrame()
        properties = [f['properties'] for f in features]
        return pd.DataFrame(properties)
    except Exception as e:
        print("Error extracting soil moisture data:", e)
        return pd.DataFrame()
# Loop through each state and extract data

for state, region in states_regions.items():
    print(f"Processing {state}...")
    soil_moisture_df = get_soil_moisture_data(region)
    soil_moisture_df.to_csv(f'{state}_soil_moisture.csv', index=False)

