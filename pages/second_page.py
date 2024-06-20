import streamlit as st
from streamlit_folium import st_folium
import folium
from folium import plugins
import datetime
from datetime import date, timedelta
from utils import get_pakistan_time, prepare_map_data, get_pollutant_values, create_aqi_legend,  display_district_color
from utils_1 import prepare_map_data_pollutant, plot_pollutant_legend, plot_aqi_for_district
import geopandas as gpd
st.set_page_config(layout="wide")
st.title("AQI in Punjab, Pakistan (page 2)")
st.set_option('deprecation.showPyplotGlobalUse', False)


# getting the time in pakistan
time = get_pakistan_time()

# Starting witl three columns layout
col1, col2, col3 = st.columns([1, 1, 1])
# displaying name of best district in the first, worst in the second and the carbon monoxide in the third column
with col1:
    st.markdown("## Best District Name and AQI ")
    best_district = get_pollutant_values(time).sort_values(by='Aqi', ascending=True).iloc[0]
    
    # displaying the best district
    st.markdown(f"### {best_district.name}")
    st.markdown(f"#### AQI: {best_district['Aqi']}")

with col2:
    st.markdown("## Worst District Name and AQI ")
    worst_district = get_pollutant_values(time).sort_values(by='Aqi', ascending=False).iloc[0]
    
    # displaying the worst district
    st.markdown(f"### {worst_district.name}")
    st.markdown(f"#### AQI: {worst_district['Aqi']}")
    
with col3:
    st.markdown("## Worst Smog Contributor")    
    # displaying the worst district
    st.markdown(f"### Carbon Monoxide")
    
    
# two new columns with this titles; AQI in Punjab, Pakistan Pollution in Punjab, then the legend plot displayed for both
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("## AQI in Punjab, Pakistan")
    legend = create_aqi_legend()
    st.pyplot(legend)
    
with col2:
    st.markdown("## Pollution in Punjab")
    legend = create_aqi_legend()
    st.pyplot(legend)
    
# two new columns, one for the map, the other for Map of AQI Map of Ranking AQI table 
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("## Map of AQI")
    map = prepare_map_data()
    st_folium(map, width='100%', height=400, key='map')

with col2:
    st.markdown("## AQI Ranking table")
    poll_hr = get_pollutant_values(time)
    poll_hr = poll_hr.sort_values(by='Aqi', ascending=True)
    display_district_color(poll_hr.iloc[:10])
    
# Creating a new section for pollutant map

st.markdown("## Pollutant Map")

# creating two columns for the pollutant map
pollutant = ''
col1, col2 = st.columns([1, 1])
with col1:
    selected_pollutant = st.selectbox("Select Pollutant", ['Pm_10', 'Pm_25', 'Ozone', 'Nitrogen_dioxide', 'Sulphur_dioxide', 'Carbon_monoxide', 'Dust'])
    pollutant+= selected_pollutant
    st.markdown(f"### {selected_pollutant}")
with col2:
    # displaying the legend for the pollutant map
    st.markdown("## Legend")
    legend = plot_pollutant_legend(selected_pollutant)
    st.pyplot(legend)
    
# pollutant map
st.markdown("### Pollutant Map")
map = prepare_map_data_pollutant(selected_pollutant)
st_folium(map, width='100%', height=800, key='pollutant_map')

st.markdown("### Forecast lagging")
# creating a district dropdown
district = ['Attock', 'Bahawalnagar', 'Bahawalpur', 'Bhakkar', 'Chakwal', 'Chiniot', 'Faisalabad', 'Gujranwala', 'Gujrat', 
            'Hafizabad', 'Jhang', 'Jhelum', 'Kasur', 'Khanewal', 'Khushab', 'Lahore', 'Layyah', 'Lodhran', 'Mianwali', 'Multan', 
            'Muzaffargarh', 'Narowal', 'Okara', 'Pakpattan', 'Rajanpur', 'Rawalpindi', 'Sahiwal', 'Sargodha', 'Sheikhupura', 
            'Sialkot', 'Vehari', 'Dera_Ghazi_Khan', 'Mandi_Bahuddin', 'Nankana_Sahib', 'Rahim_Yar_Khan', 'Toba_Tek_Singh']
district_name = st.selectbox("Select a district", district)
plot_aqi_for_district(district_name)