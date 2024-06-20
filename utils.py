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

# loading the data
forecasted_df = pd.read_csv('forecasted_pollutant.csv')

# getting the current date hour in pakistan
def get_pakistan_time():
    # getting the current date and time in Pakistan
    now = datetime.now(timezone('Asia/Karachi'))
    # returning it in this format '2021-09-01 00:00:00'
    formatted_time = now.strftime('%Y-%m-%d %H:00:00')
    return formatted_time

@st.cache_data
def get_AQI(date_hour, forecasted_df):
    return forecasted_df.loc[date_hour, ['Aqi', 'Location_id', 'District']]

@st.cache_data
def replace_space_with_underscore(aqi_color_dict):
    for key in list(aqi_color_dict.keys()):
        if ' ' in key:
            new_key = key.replace(' ', '_')
            aqi_color_dict[new_key] = aqi_color_dict.pop(key)
    return aqi_color_dict

# classifyint the AQI value with colours based on range

def get_AQI_color(aqi):
    if aqi <= 50:
        return 'Green'
    elif aqi <= 100:
        return 'Yellow'
    elif aqi <= 150:
        return 'Orange'
    elif aqi <= 200:
        return 'Red'
    elif aqi <= 300:
        return 'Purple'
    else:
        return 'Maroon'

@st.cache_data
def get_shapefiles():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(parent_dir, 'district_by_name')
    shapefiles = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.shp'):
                shapefiles.append(file.split('.')[0])
    return shapefiles

# Function to convert AQI to color
def aqi_to_color(aqi):
    if aqi <= 50:
        return '#00E400'  # Good
    elif aqi <= 100:
        return '#FFFF00'  # Moderate
    elif aqi <= 150:
        return '#FF7E00'  # Unhealthy for sensitive groups
    elif aqi <= 200:
        return '#FF0000'  # Unhealthy
    elif aqi <= 300:
        return '#8F3F97'  # Very Unhealthy
    else:
        return '#7E0023'  # Hazardous

# Function to create the Plotly plot
@st.cache_data
def plot_aqi_histogram(df):
    # Ensure the 'AQI' column exists in the DataFrame
    if 'Aqi' not in df.columns:
        raise ValueError("The DataFrame must contain an 'AQI' column.")

    # Create the figure
    fig = go.Figure()

    # Add bars to the plot
    for i in range(len(df)):
        fig.add_trace(go.Bar(
            x=[df.index[i]],
            y=[df['Aqi'].iloc[i]],
            marker_color=aqi_to_color(df['Aqi'].iloc[i]),
            width=1000000,  
            showlegend=False
        ))

    # Set layout properties
    fig.update_layout(
        title='AQI Over Time',
        xaxis_title='Date and Time',
        yaxis_title='AQI',
        xaxis_tickformat='%d %b, %I %p',
        bargap=1  # Remove gaps between bars
    )

    return fig


# @st.cache_data
# Function to create a colored map
def create_colored_map(locations_colors):
    # Calculate the centroid for the initial map position (average coordinates of Punjab region)
    center_x = 31.1471
    center_y = 75.3412

    # Create the Folium map
    m = folium.Map(location=[center_x, center_y], zoom_start=7)

    # adding a general map boundary
    gdf_1 = gpd.read_file('./punjabaoi/aoi_punjab.shp')
    # Add a GeoJSON layer
    folium.GeoJson(data=gdf_1.to_json(), name='My Shapefile').add_to(m)

    # Define a style function to set the color for each location
    def style_function(color):
        return {
            'fillColor': color,
            'weight': 2,  # Increase border thickness
            'color': color,
            'fillOpacity': 0.7,  # Increase fill opacity
            'opacity': 1,
        }

    # Loop through the locations and their colors
    for location, color in locations_colors.items():
        # Load the shapefile
        shp_path = f'district_by_name/{location}.shp'
        gdf = gpd.read_file(shp_path)
        
        # Add GeoJSON layer to the map
        # Add GeoJSON layer to the map
        folium.GeoJson(
            data=gdf.to_json(),
            name=location,
            style_function=lambda feature, color=color: style_function(color),
            tooltip=folium.GeoJsonTooltip(fields=['district'], aliases=['District:']),
            overlay=True
        ).add_to(m)

    # Return the map object
    return m


# @st.cache_data
def prepare_map_data():
    #########################################################
    # loading the forecasted data
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    # print(forecasted_df.head())
    ###########################################################
    date_hour = get_pakistan_time()
    aqi_hour = get_AQI(date_hour, forecasted_df)
    # aggregating the AQI values for each district
    aqi_district = aqi_hour.groupby('District').mean()
    # implementing on the aqi_hour and pollutant_values
    aqi_district['AQI_color'] = aqi_district['Aqi'].apply(lambda x: get_AQI_color(x))
    # getting the shapefiles
    shapefiles = get_shapefiles()
    # creating the aqi_color_dict
    aqi_color_dict = aqi_district['AQI_color'].to_dict()
    # fixing possible space issue   
    aqi_color_dict = replace_space_with_underscore(aqi_color_dict)
    # filtering aqi_color_dict based on the shapefiles
    aqi_color_dict_ = {k: v for k, v in aqi_color_dict.items() if k in shapefiles}
    ##############################################################
    # getting the current time in pakistan
    # current_time = get_pakistan_time()
    # Create the map with the sample data
    map_object = create_colored_map(aqi_color_dict_)
    return map_object

def get_pollutant_values(date_hour):
    # loading the forecasted data
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    pollutant_values = forecasted_df.loc[date_hour, ['Aqi', 'Carbon_monoxide', 'District', 'Dust',
       'Nitrogen_dioxide', 'Ozone', 'Pm_10', 'Pm_25', 'Sulphur_dioxide']]
    pollutant_values_agg = pollutant_values.groupby('District').mean()
    return pollutant_values_agg



@st.cache_data
def create_aqi_legend():
    # Define the AQI ranges and their corresponding colors
    aqi_categories = ['Good', 'Moderate', 'Unhealthy for sensitive groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    ranges = ['0-50', '51-100', '101-150', '151-200', '201-300', '301-500']
    colors = ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8F3F97', '#7E0023']

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(19, 2))
    ax.set_xlim(0, len(aqi_categories))
    ax.set_ylim(0, 2)
    ax.axis('off')  # Turn off the axis

    # Plot each AQI category with its color and name
    for i, (category, range_, color) in enumerate(zip(aqi_categories, ranges, colors)):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color))
        ax.text(i + 0.5, 1.5, f'{category}: {range_}', color='black', ha='center', va='center', fontsize=9)

    return fig


@st.cache_data
def aggregate_pollutants(initial_time, district):
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    # converting the index to datetime
    forecasted_df.index = pd.to_datetime(forecasted_df.index)
    # Parse the initial time
    initial_time = pd.to_datetime(initial_time)
    final_time = initial_time + pd.Timedelta(days=30)

    # Filter the DataFrame for the specified district and time range
    filtered_df = forecasted_df[(forecasted_df.index >= initial_time) & (forecasted_df.index <= final_time) & (forecasted_df['District'] == district)]

    # Select only numeric columns for aggregation
    numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns

    # Group by hour and aggregate pollutants
    aggregated_df = filtered_df[numeric_columns].resample('H').mean()
    
    return aggregated_df.drop(columns=['Location_id'])


@st.cache_data
def last_year_aggregate_pollutants(initial_time, district):
    forecasted_df = pd.read_csv('last_year_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('Date')
    # converting the index to datetime
    forecasted_df.index = pd.to_datetime(forecasted_df.index)
    # Parse the initial time
    initial_time = pd.to_datetime(initial_time)
    # converting initial time to last year
    initial_time = initial_time - pd.Timedelta(days=366)
    final_time = initial_time + pd.Timedelta(days=60)

    # Filter the DataFrame for the specified district and time range
    filtered_df = forecasted_df[(forecasted_df.index >= initial_time) & (forecasted_df.index <= final_time) & (forecasted_df['District'] == district)]

    # Select only numeric columns for aggregation
    numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns

    # Group by hour and aggregate pollutants
    aggregated_df = filtered_df[numeric_columns].resample('H').mean()
    
    return aggregated_df.drop(columns=['Location_id'])

@st.cache_data
def daily_aggregate_pollutants(initial_time, district):
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    # converting the index to datetime
    forecasted_df.index = pd.to_datetime(forecasted_df.index)
    # Parse the initial time
    initial_time = pd.to_datetime(initial_time)
    final_time = initial_time + pd.Timedelta(days=14)

    # Filter the DataFrame for the specified district and time range
    filtered_df = forecasted_df[(forecasted_df.index >= initial_time) & (forecasted_df.index <= final_time) & (forecasted_df['District'] == district)]

    # Select only numeric columns for aggregation
    numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns

    # Group by daily and aggregate pollutants
    aggregated_df = filtered_df[numeric_columns].resample('D').mean()
    
    return aggregated_df.drop(columns=['Location_id'])


@st.cache_data
def range_aggregate_pollutants(initial_time, district, pollutant):
    forecasted_df = pd.read_csv('forecasted_pollutant.csv')
    # replacing unnamed column with date
    forecasted_df = forecasted_df.rename(columns={'Unnamed: 0': 'date'})
    # setting the date column as index
    forecasted_df = forecasted_df.set_index('date')
    # converting the index to datetime
    forecasted_df.index = pd.to_datetime(forecasted_df.index)
    # Parse the initial time
    initial_time = pd.to_datetime(initial_time)
    final_time = initial_time + pd.Timedelta(days=14)

    # Filter the DataFrame for the specified district and time range
    filtered_df = forecasted_df[(forecasted_df.index >= initial_time) & (forecasted_df.index <= final_time) & (forecasted_df['District'] == district)]

    # Select only numeric columns for aggregation
    numeric_columns = filtered_df.select_dtypes(include=['float64', 'int64']).columns

    # Group by hour and aggregate pollutants
    aggregated_df = filtered_df[numeric_columns].resample('H').mean()
    
     # Calculate the AQI
    aggregated_df['Aqi'] = (
        aggregated_df['Pm_25'] * 0.25 +
        aggregated_df['Pm_10'] * 0.25 +
        aggregated_df['Nitrogen_dioxide'] * 0.15 +
        aggregated_df['Sulphur_dioxide'] * 0.1 +
        aggregated_df['Carbon_monoxide'] * 0.1 +
        aggregated_df['Ozone'] * 0.1 +
        aggregated_df['Dust'] * 0.05
    )

    # selecting pollutant to view
    new_df = aggregated_df[[pollutant]]

    # assuming the model accuracy of 85%
    new_df['min ' + pollutant] = new_df[pollutant] * 0.90
    new_df['max ' + pollutant] = new_df[pollutant] * 1.10
    
    return new_df


# color paletter
# Color palette based on the provided list
color_palette = [
    "#00FF00", "#19F719", "#32EF32", "#4BE74B", "#64DF64", "#7DD77D", "#96CF96", "#AFC7AF", 
    "#C8BFC8", "#E1B7E1", "#FF9FFF", "#FF99E5", "#FF92CC", "#FF8CB2", "#FF8699", "#FF7F80", 
    "#FF7966", "#FF734D", "#FF6C33", "#FF662A", "#FF6020", "#FF5917", "#FF5313", "#FF4C0F", 
    "#FF460B", "#FF4007", "#FF3A03", "#FF3300", "#FF2D00", "#FF2600", "#FF2000", "#FF1A00", 
    "#FF1400", "#FF0D00", "#FF0700", "#FF0000"
]

def display_colored_table(df):
    df_html = df.to_html(escape=False, index=False)
    st.markdown(df_html, unsafe_allow_html=True)
def display_district_color(df):

    # Sort DataFrame by AQI in ascending order
    df_sorted = df.sort_values(by='Aqi', ascending=True)

    # Add a column for colors based on AQI values
    df_sorted['Color'] = color_palette[:len(df_sorted)]

    # Convert the DataFrame to a format suitable for display in Streamlit
    df_display = df_sorted.reset_index()
    # Apply color formatting to the AQI column
    df_display['Aqi'] = df_display.apply(lambda row: f'<div style="background-color:{row["Color"]}; color:black;">{np.round(row["Aqi"], 5)}</div)', axis=1)
    # Apply color formatting to the district column
    # df_display['district'] = df_display.apply(lambda row: f'<div style="background-color:{row["Color"]};color:black;">{row["district"]}</div>', axis=1)

    # adding id
    df_display['Ranking'] = df_display.index

    # Display the colored table
    return display_colored_table(df_display[['Ranking','District', 'Aqi']])

def plot_separate(df1, df2, y1_column, y2_column, title1="Last Year Hourly Trends", title2="This Year Hourly Trends", y1_label="Last Year", y2_label="This Year"):
    # Ensure the index is a datetime type for proper plotting
    if not pd.api.types.is_datetime64_any_dtype(df1.index):
        raise ValueError("The index of df1 must be a datetime type")
    if not pd.api.types.is_datetime64_any_dtype(df2.index):
        raise ValueError("The index of df2 must be a datetime type")

    # Plot for last year
    fig1, ax1 = plt.subplots(figsize=(15, 4))
    ax1.plot(df1.index, df1[y1_column], label=y1_label, color='b')
    ax1.set_title(title1)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Values')
    ax1.legend()
    st.pyplot(fig1)

    # Plot for this year
    fig2, ax2 = plt.subplots(figsize=(15, 4))
    ax2.plot(df2.index, df2[y2_column], label=y2_label, color='r')
    ax2.set_title(title2)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Values')
    ax2.legend()
    st.pyplot(fig2)
