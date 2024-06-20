import streamlit as st
from streamlit_folium import st_folium
import folium
from folium import plugins
import datetime
from datetime import date, timedelta
from utils import get_pakistan_time, prepare_map_data,plot_separate, last_year_aggregate_pollutants,  get_pollutant_values, aggregate_pollutants, range_aggregate_pollutants, create_colored_map, create_aqi_legend, daily_aggregate_pollutants, plot_aqi_histogram, display_district_color
import geopandas as gpd
st.set_page_config(layout="wide")
st.title("AQI in Punjab, Pakistan")
st.set_option('deprecation.showPyplotGlobalUse', False)

# Getting the current time in pakistan
time = get_pakistan_time()

# display the current time
st.markdown(f"## Current Time in Pakistan: {time}")


########################################################
# displaying the coloured map
map = prepare_map_data()

# map_object = create_colored_map(aqi_colour_dict, time)

# Display the map with desired width
st_folium(map, width='100%', height=800)
st.markdown("## AQI Legend")
legend = create_aqi_legend()
st.pyplot(legend)
########################################################


########################################################
# Section for District Pollutant forecast
st.markdown("## District Hourly Pollutant Forecast")
poll_hr = get_pollutant_values(time)
st.dataframe(poll_hr)
########################################################
# Function to display the AQI table with colored AQI values
# sorting poll_hr by aqi in acsending order
poll_hr = poll_hr.sort_values(by='Aqi', ascending=True)
st.markdown("## District Hourly Pollutant Forecast with AQI")
# showing the first five rows of the dataframe
display_district_color(poll_hr.iloc[:5])
# adding a show more button to display the rest of the data
if st.button("Show More", key='show_more'):
    display_district_color(poll_hr.iloc[5:])

# Section for the next 14 days prediction for punjab
st.markdown("## Punjab Daily AQI Forecast for the next 14 days")
district = ['Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar', 'Chakwal', 'Chiniot', 'Faisalabad', 'Gujranwala', 'Gujrat', 
            'Hafizabad', 'Jhang', 'Jhelum', 'Kasur', 'Khanewal', 'Khushab', 'Lahore', 'Layyah', 'Lodhran', 'Mianwali', 'Multan', 
            'Muzaffargarh', 'Narowal', 'Okara', 'Pakpattan', 'Rajanpur', 'Rawalpindi', 'Sahiwal', 'Sargodha', 'Sheikhupura', 
            'Sialkot', 'Vehari', 'Dera_Ghazi_Khan', 'Mandi_Bahuddin', 'Nankana_Sahib', 'Rahim_Yar_Khan', 'Toba_Tek_Singh']

# create a dropdown for the district
district_name = st.selectbox("Select a district", district)
initial_time = time
result = daily_aggregate_pollutants(initial_time, district_name)
st.dataframe(result)
# hourly 
result_1 = aggregate_pollutants(initial_time, district_name)
aqi_plot = plot_aqi_histogram(result_1.iloc[:48])
# creating two columns for the plots
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Hourly AQI for the next 2 days")
    st.plotly_chart(aqi_plot)
with col2:
    last_year_data = last_year_aggregate_pollutants(initial_time, district_name)
    print(last_year_data.columns)
    st.markdown("### Last Year AQI for the same day")
    plot_separate(last_year_data, result_1 , 'Aqi', 'Aqi')

# st.plotly_chart(aqi_plot)
# last_year_data = last_year_aggregate_pollutants(initial_time, district)
# st.markdown("### Last Year AQI for the same day")
# st.pyplot(plot_separate(last_year_data.iloc[:60], district_name.iloc[:60],  'Aqi', 'Aqi'))


#  Section for the min and max AQI for the next 14 days
st.markdown("## Min and Max Pollutant for the next 14 days")
district = ['Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar', 'Chakwal', 'Chiniot', 'Faisalabad', 'Gujranwala', 'Gujrat', 
            'Hafizabad', 'Jhang', 'Jhelum', 'Kasur', 'Khanewal', 'Khushab', 'Lahore', 'Layyah', 'Lodhran', 'Mianwali', 'Multan', 
            'Muzaffargarh', 'Narowal', 'Okara', 'Pakpattan', 'Rajanpur', 'Rawalpindi', 'Sahiwal', 'Sargodha', 'Sheikhupura', 
            'Sialkot', 'Vehari', 'Dera_Ghazi_Khan', 'Mandi_Bahuddin', 'Nankana_Sahib', 'Rahim_Yar_Khan', 'Toba_Tek_Singh']

district_name = st.selectbox("Select a district", district, key='district')
pollutant = ['Carbon_monoxide', 'Dust', 'Nitrogen_dioxide', 'Ozone', 'Pm_10', 'Pm_25', 'Sulphur_dioxide', 'Aqi']
pollutant_name = st.selectbox("Select a pollutant", pollutant, key='pollutant')
range_result = range_aggregate_pollutants(initial_time, district_name, pollutant_name)
st.dataframe(range_result)

