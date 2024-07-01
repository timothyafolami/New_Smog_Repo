import folium
import geopandas as gpd
import random
import matplotlib.pyplot as plt
from datetime import datetime
from pytz import timezone
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import joblib
from datetime import timedelta
import os
import streamlit as st
import plotly.graph_objects as go


# %matplotlib inline


# getting the current date hour in pakistan
def get_pakistan_time():
    # getting the current date and time in Pakistan
    now = datetime.now(timezone('Asia/Karachi'))
    # returning it in this format '2021-09-01 00:00:00'
    formatted_time = now.strftime('%Y-%m-%d %H:00:00')
    return formatted_time

# Define color ranges and values for each pollutant
color_mapping = {
    'Pm_10': [(0, 275, '#FFC080'), (276, 550, '#FFA07A'), (551, 825, '#FF9900'), (826, 1100, '#FF6600'), (1101, 1375, '#FF4400'), (1376, float('inf'), '#FF0000')],
    'Pm_25': [(0, 65, '#FFC0CB'), (66, 130, '#FF69B4'), (131, 195, '#FF0033'), (196, 260, '#FF0000'), (261, 325, '#8B0A1A'), (326, float('inf'), '#660000')],
    'Carbon_monoxide': [(0, 1300, '#ADD8E6'), (1301, 2600, '#87CEEB'), (2601, 3900, '#6495ED'), (3901, 5200, '#0000FF'), (5201, 6500, '#00008B'), (6501, float('inf'), '#00008B')],
    'Dust': [(0, 625, '#C5C3C5'), (626, 1250, '#C5107A'), (1251, 1875, '#7A288A'), (1876, 2500, '#6c5ce7'), (2501, 3125, '#4B0082'), (3126, float('inf'), '#3B3F4E')],
    'Sulphur_dioxide': [(0, 35, '#F5F5DC'), (36, 70, '#964B00'), (71, 105, '#8B4513'), (106, 140, '#663300'), (141, 175, '#4B2E2E'), (176, float('inf'), '#3B2E2E')],
    'Nitrogen_dioxide': [(0, 30, '#F7D2C4'), (31, 60, '#FFC394'), (61, 90, '#FF9900'), (91, 120, '#FF6600'), (121, 150, '#FF4400'), (151, float('inf'), '#FF0000')],
    'Ozone': [(0, 55, '#C7F464'), (56, 110, '#0097A7'), (111, 165, '#00BFFF'), (166, 220, '#008000'), (221, 275, '#00695C'), (276, float('inf'), '#000080')]
}

# Function to create a rectangular plot for a specific pollutant
def plot_pollutant_legend(pollutant):
    if pollutant not in color_mapping:
        raise ValueError(f"Invalid pollutant name: {pollutant}")
    
    # Extract the color ranges and values
    color_ranges = color_mapping[pollutant]
    colors = [color for _, _, color in color_ranges]
    labels = [f'{lower}-{upper}' if upper != float('inf') else f'>{lower}' for lower, upper, _ in color_ranges]

    # Create the figure and plot
    fig, ax = plt.subplots(figsize=(12, 1))
    
    # Plot each color range as a rectangle
    for i, (range_label, color) in enumerate(zip(labels, colors)):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color))
        ax.text(i + 0.5, 0.5, range_label, color='black', ha='center', va='center', fontsize=10, weight='bold')

    # Remove axes
    ax.set_xlim(0, len(labels))
    ax.set_ylim(0, 1)
    ax.axis('off')  # Turn off the axis

    # Set the title
    ax.set_title(f'{pollutant} Levels and Corresponding Colors', fontsize=14, weight='bold')

    plt.tight_layout()
    plt.show()
    
def get_AQI(date_hour, forecasted_df):
    return forecasted_df.loc[date_hour, ['Aqi', 'Location_id', 'District']]    

def get_pollutant(date_hour, forecasted_df, pollutant):
    return forecasted_df.loc[date_hour, [pollutant, 'Location_id', 'District']]

def replace_space_with_underscore(aqi_color_dict):
    for key in list(aqi_color_dict.keys()):
        if ' ' in key:
            new_key = key.replace(' ', '_')
            aqi_color_dict[new_key] = aqi_color_dict.pop(key)
    return aqi_color_dict

def get_shapefiles():
    shapefiles = []
    for root, dirs, files in os.walk('district_by_name'):
        for file in files:
            if file.endswith('.shp'):
                shapefiles.append(file.split('.')[0])
    return shapefiles


def get_pollutant_color(pollutant, value):
    ranges = color_mapping[pollutant]
    for lower, upper, color in ranges:
        if lower <= value <= upper:
            return color
    # return the first color if no range matches as a default
    return ranges[0][2]


def create_colored_map(locations_colors):
    center_x = 30.9709
    center_y = 72.4826
    m = folium.Map(location=[center_x, center_y], zoom_start=7)
    gdf_1 = gpd.read_file('./punjabaoi/aoi_punjab.shp')
    folium.GeoJson(data=gdf_1.to_json(), name='My Shapefile').add_to(m)

    def style_function(color):
        return {
            'fillColor': color,
            'weight': 2,
            'color': color,
            'fillOpacity': 0.7,
            'opacity': 1,
        }

    for location, color in locations_colors.items():
        shp_path = f'district_by_name/{location}.shp'
        gdf = gpd.read_file(shp_path)
        folium.GeoJson(
            data=gdf.to_json(),
            name=location,
            style_function=lambda feature, color=color: style_function(color),
            tooltip=folium.GeoJsonTooltip(fields=['district'], aliases=['District:']),
            overlay=True
        ).add_to(m)

    return m

def prepare_map_data_pollutant(pollutant):
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    forecasted_df = forecasted_df.set_index('date')
    date_hour = get_pakistan_time()
    aqi_hour = get_pollutant(date_hour, forecasted_df, pollutant)
    aqi_district = aqi_hour.groupby('District').mean()
    # print("getting the color")
    aqi_district['Color'] = aqi_district[pollutant].apply(lambda x: get_pollutant_color(pollutant, float(x)))
    # printing the color
    # print(f"Color for {pollutant} is {aqi_district['Color']}")
    # print("getting the shapefiles")
    shapefiles = get_shapefiles()
    # print("getting the color dict")
    color_dict = aqi_district['Color'].to_dict()
    # print("replacing space with underscore")
    color_dict = replace_space_with_underscore(color_dict)
    color_dict_ = {k: v for k, v in color_dict.items() if k in shapefiles}
    map_object = create_colored_map(color_dict_)
    return map_object

# color palatte for aqi ranking map
color_palette = [
    "#00FF00", "#19F719", "#32EF32", "#4BE74B", "#64DF64", "#7DD77D", "#96CF96", "#AFC7AF", 
    "#C8BFC8", "#E1B7E1", "#FF9FFF", "#FF99E5", "#FF92CC", "#FF8CB2", "#FF8699", "#FF7F80", 
    "#FF7966", "#FF734D", "#FF6C33", "#FF662A", "#FF6020", "#FF5917", "#FF5313", "#FF4C0F", 
    "#FF460B", "#FF4007", "#FF3A03", "#FF3300", "#FF2D00", "#FF2600", "#FF2000", "#FF1A00", 
    "#FF1400", "#FF0D00", "#FF0700", "#FF0000"
]

def prepare_ranking_map():
    #########################################################
    # loading the forecasted data
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # print(forecasted_df.head())
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # print('done')
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    
    ###########################################################
    date_hour = get_pakistan_time()
    aqi_hour = get_AQI(date_hour, forecasted_df)
    # aggregating the AQI values for each district
    aqi_district = aqi_hour.groupby('District').mean()
    # sorting aqi values in ascending order
    aqi_district = aqi_district.sort_values(by='Aqi', ascending=True)
    # implementing on the aqi_hour and pollutant_values
    aqi_district['AQI_color'] = color_palette
    # getting the shapefiles
    shapefiles = get_shapefiles()
    # creating a dictionary with district and AQI color
    aqi_color_dict = aqi_district['AQI_color'].to_dict()
    # fixing possible space issue   
    aqi_color_dict = replace_space_with_underscore(aqi_color_dict)
    # filtering aqi_color_dict based on the shapefiles
    aqi_color_dict_ = {k: v for k, v in aqi_color_dict.items() if k in shapefiles}
    ##############################################################
    # Create the map with the sample data
    map_object = create_colored_map(aqi_color_dict_)
    return map_object


def plot_aqi_for_district(district_name):
    # Load the datasets
    
    day_7 = pd.read_csv('aqi_7_days_lag.csv')
    day_14 = pd.read_csv('aqi_14_days_lag.csv')
    day_30 = pd.read_csv('aqi_30_days_lag.csv')
    histo = pd.read_csv('ready_historical.csv')
    
    # Filter DataFrames by the given district
    day_30_district = day_30[day_30['District'] == district_name]
    day_14_district = day_14[day_14['District'] == district_name]
    day_7_district = day_7[day_7['District'] == district_name]
    histo_district = histo[histo['District'] == district_name]

    # Convert 'date' column to datetime for each DataFrame
    day_30_district['date'] = pd.to_datetime(day_30_district['date'])
    day_14_district['date'] = pd.to_datetime(day_14_district['date'])
    day_7_district['date'] = pd.to_datetime(day_7_district['date'])
    histo_district['date'] = pd.to_datetime(histo_district['date'])

    # Set 'date' as the index for resampling
    day_30_district.set_index('date', inplace=True)
    day_14_district.set_index('date', inplace=True)
    day_7_district.set_index('date', inplace=True)
    histo_district.set_index('date', inplace=True)

    # Resample to daily frequency and select the maximum AQI for each day
    day_30_daily = day_30_district.resample('D').max()
    day_14_daily = day_14_district.resample('D').max()
    day_7_daily = day_7_district.resample('D').max()
    histo_daily = histo_district.resample('D').max()

    # Filter the data to include only the relevant date ranges
    end_date = pd.to_datetime('today').normalize()
    start_date_day_30 = end_date - pd.Timedelta(days=30)
    start_date_day_14 = end_date - pd.Timedelta(days=14)
    start_date_day_7 = end_date - pd.Timedelta(days=7)

    day_30_filtered = day_30_daily.loc[start_date_day_30:end_date]
    day_14_filtered = day_14_daily.loc[start_date_day_14:end_date]
    day_7_filtered = day_7_daily.loc[start_date_day_7:end_date]
    histo_filtered = histo_daily.loc[start_date_day_30:end_date]

    # Plot the data
    plt.figure(figsize=(20, 6))

    plt.plot(day_30_filtered.index, day_30_filtered['Aqi'], label='Day 30', color='blue')
    plt.plot(day_14_filtered.index, day_14_filtered['Aqi'], label='Day 14', color='green')
    plt.plot(day_7_filtered.index, day_7_filtered['Aqi'], label='Day 7', color='red')
    plt.plot(histo_filtered.index, histo_filtered['Aqi'], label='Historical', color='orange')

    plt.xlabel('Date')
    plt.ylabel('AQI')
    plt.title(f'Max AQI in {district_name} District from Different Lag Periods')
    plt.legend()
    plt.grid(True)
    plt.show()


def forecast_plot_predicted_aqi(district_name):
    # Load the dataset
    aqi_pollutant = pd.read_csv('aqi_forecast.csv')
    
    # Filter DataFrame by the given district
    district_data = aqi_pollutant[aqi_pollutant['District'] == district_name]
    
    # Convert 'date' column to datetime
    district_data['date'] = pd.to_datetime(district_data['date'])
    
    # Resample to daily frequency and select the maximum AQI for each day
    district_daily_max = district_data.resample('D', on='date').max()
    
    # Define the start date and end dates for the segments
    start_date = pd.to_datetime('today').normalize()
    end_date_7 = start_date + pd.Timedelta(days=7)
    end_date_14 = start_date + pd.Timedelta(days=14)
    end_date_60 = start_date + pd.Timedelta(days=60)

    # Filter the data for each segment
    segment_1 = district_daily_max.loc[start_date:end_date_7]
    segment_2 = district_daily_max.loc[end_date_7+pd.Timedelta(days=1):end_date_14]
    segment_3 = district_daily_max.loc[end_date_14+pd.Timedelta(days=1):end_date_60]

    # Combine the segments to ensure they are connected in the plot
    combined_segments = pd.concat([segment_1, segment_2, segment_3])
    
    # Plot the data
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(combined_segments.index, combined_segments['Aqi'], color='darkgreen', label='Day 0 to Day 60')
    ax.plot(segment_1.index, segment_1['Aqi'], color='darkgreen', label='Day 0 to Day 7')
    ax.plot(segment_2.index, segment_2['Aqi'], color='lightgreen', label='Day 8 to Day 14')
    ax.plot(segment_3.index, segment_3['Aqi'], color='yellowgreen', label='Day 15 to Day 60')

    ax.set_xlabel('Date')
    ax.set_ylabel('AQI')
    ax.set_title(f'Predicted AQI in {district_name} District')
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
