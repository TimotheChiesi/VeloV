import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
import os

# Page configuration
st.set_page_config(
    page_title="Vélo'v Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Database connection from environment variables
@st.cache_resource
def get_connection():
    """
    Create a connection to PostgreSQL database using environment variables.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'airflow'),
            user=os.getenv('POSTGRES_USER', 'airflow'),
            password=os.getenv('POSTGRES_PASSWORD', 'airflow'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


# Test connection
@st.cache_data(ttl=60)
def test_connection(_conn):
    """Test database connection and table existence"""
    try:
        cursor = _conn.cursor()
        cursor.execute("""
                       SELECT COUNT(*)
                       FROM velov_processed
                       """)
        count = cursor.fetchone()[0]
        cursor.close()
        return True, count
    except Exception as e:
        return False, str(e)


# Data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_latest_data(_conn):
    """Load the most recent data for each station"""
    query = """
            WITH latest_updates AS (SELECT number, MAX(last_update) as max_update \
                                    FROM velov_processed \
                                    GROUP BY number)
            SELECT v.*
            FROM velov_processed v
                     INNER JOIN latest_updates l
                                ON v.number = l.number AND v.last_update = l.max_update
            ORDER BY v.number \
            """
    return pd.read_sql_query(query, _conn)


@st.cache_data(ttl=300)
def load_historical_data(_conn, hours=24):
    """Load historical data for the specified number of hours"""
    query = """
            SELECT *
            FROM velov_processed
            WHERE last_update >= NOW() - INTERVAL '%s hours'
            ORDER BY last_update DESC \
            """
    return pd.read_sql_query(query, _conn, params=(hours,))


@st.cache_data(ttl=300)
def load_station_history(_conn, station_number, hours=24):
    """Load history for a specific station"""
    query = """
            SELECT *
            FROM velov_processed
            WHERE number = %s
              AND last_update >= NOW() - INTERVAL '%s hours'
            ORDER BY last_update \
            """
    return pd.read_sql_query(query, _conn, params=(station_number, hours))


def create_alerts_section(latest_data):
    """Create alerts for problematic stations"""
    empty_stations = latest_data[latest_data['available_bikes'] == 0]
    full_stations = latest_data[latest_data['available_bike_stands'] == 0]

    if len(empty_stations) > 0 or len(full_stations) > 0:
        st.warning("⚠️ **Alerts**")
        col1, col2 = st.columns(2)

        with col1:
            if len(empty_stations) > 0:
                st.error(f"🚫 **{len(empty_stations)} stations with no bikes available**")
                with st.expander("View stations"):
                    st.dataframe(
                        empty_stations[['name', 'commune', 'bike_stands']].sort_values('name'),
                        hide_index=True,
                        use_container_width=True
                    )

        with col2:
            if len(full_stations) > 0:
                st.error(f"🅿️ **{len(full_stations)} stations with no parking available**")
                with st.expander("View stations"):
                    st.dataframe(
                        full_stations[['name', 'commune', 'available_bikes']].sort_values('name'),
                        hide_index=True,
                        use_container_width=True
                    )


# Main dashboard
def main():
    st.title("🚲 Vélo'v Bike Sharing Dashboard")
    st.caption("Real-time monitoring of bike-sharing stations")

    # Sidebar
    st.sidebar.header("⚙️ Settings")

    # Database connection
    conn = get_connection()
    if conn is None:
        st.error("Cannot connect to database. Please check your connection settings.")
        return

    # Test connection
    is_connected, result = test_connection(conn)
    if not is_connected:
        st.error(f"Database table issue: {result}")
        st.info("Make sure the velov_processed table exists and has data.")
        return

    st.sidebar.success(f"✅ Connected ({result:,} total records)")

    # Time range selector
    time_range = st.sidebar.selectbox(
        "📅 Historical Data Range",
        ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
        index=2
    )

    hours_map = {
        "Last Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24,
        "Last 7 Days": 168
    }
    hours = hours_map[time_range]

    # Display options
    st.sidebar.subheader("📊 Display Options")
    show_alerts = st.sidebar.checkbox("Show Alerts", value=True)
    show_commune_analysis = st.sidebar.checkbox("Show Geographic Analysis", value=True)
    show_time_series = st.sidebar.checkbox("Show Temporal Trends", value=True)

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("Cache TTL: 300s")

    # Load data
    with st.spinner("Loading data..."):
        latest_data = load_latest_data(conn)
        if hours <= 168:
            historical_data = load_historical_data(conn, hours)
        else:
            historical_data = pd.DataFrame()

    if latest_data.empty:
        st.warning("No data available in the database.")
        return

    # Alerts section
    if show_alerts:
        create_alerts_section(latest_data)
        st.markdown("---")

    # Key Metrics Row
    st.header("📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    total_stations = len(latest_data)
    total_bikes = latest_data['available_bikes'].sum()
    total_stands = latest_data['bike_stands'].sum()
    total_available_stands = latest_data['available_bike_stands'].sum()
    avg_occupancy = (total_bikes / total_stands * 100) if total_stands > 0 else 0

    with col1:
        st.metric("Total Stations", f"{total_stations:,}")

    with col2:
        st.metric("Available Bikes", f"{total_bikes:,}")

    with col3:
        st.metric("Total Capacity", f"{total_stands:,}")

    with col4:
        st.metric("Available Stands", f"{total_available_stands:,}")

    with col5:
        st.metric("Avg Occupancy", f"{avg_occupancy:.1f}%")

    st.markdown("---")

    # Status Overview
    st.header("🚦 Station Status Overview")
    col1, col2 = st.columns(2)

    with col1:
        # Status distribution
        status_counts = latest_data['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Station Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.3
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)

    with col2:
        # Availability distribution
        availability_counts = latest_data['availability'].value_counts()
        fig_avail = px.pie(
            values=availability_counts.values,
            names=availability_counts.index,
            title="Bike Availability Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.3
        )
        fig_avail.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_avail, use_container_width=True)

    st.markdown("---")

    # Occupancy Analysis
    st.header("📈 Occupancy Analysis")

    latest_data['occupancy_rate'] = (latest_data['available_bikes'] / latest_data['bike_stands'] * 100).fillna(0)

    col1, col2 = st.columns(2)

    with col1:
        # Occupancy histogram
        fig_hist = px.histogram(
            latest_data,
            x='occupancy_rate',
            nbins=20,
            title="Station Occupancy Rate Distribution",
            labels={'occupancy_rate': 'Occupancy Rate (%)', 'count': 'Number of Stations'},
            color_discrete_sequence=['#636EFA']
        )
        fig_hist.update_layout(showlegend=False, bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        # Top 10 busiest stations
        top_stations = latest_data.nlargest(10, 'available_bikes')[['name', 'available_bikes', 'bike_stands']]
        fig_top = px.bar(
            top_stations,
            x='available_bikes',
            y='name',
            orientation='h',
            title="Top 10 Stations by Available Bikes",
            labels={'available_bikes': 'Available Bikes', 'name': 'Station'},
            color='available_bikes',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("---")

    # Geographic Analysis by Commune
    if show_commune_analysis and 'commune' in latest_data.columns and latest_data['commune'].notna().any():
        st.header("🗺️ Geographic Distribution")

        commune_stats = latest_data.groupby('commune').agg({
            'number': 'count',
            'available_bikes': 'sum',
            'bike_stands': 'sum'
        }).reset_index()
        commune_stats.columns = ['Commune', 'Stations', 'Available Bikes', 'Total Capacity']
        commune_stats['Occupancy %'] = (commune_stats['Available Bikes'] / commune_stats['Total Capacity'] * 100).round(
            1)

        col1, col2 = st.columns(2)

        with col1:
            fig_commune = px.bar(
                commune_stats.sort_values('Stations', ascending=False),
                x='Commune',
                y='Stations',
                title="Stations per Commune",
                color='Occupancy %',
                color_continuous_scale='RdYlGn',
                labels={'Stations': 'Number of Stations'}
            )
            fig_commune.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_commune, use_container_width=True)

        with col2:
            fig_bikes = px.bar(
                commune_stats.sort_values('Available Bikes', ascending=False),
                x='Commune',
                y='Available Bikes',
                title="Available Bikes per Commune",
                color='Occupancy %',
                color_continuous_scale='RdYlGn'
            )
            fig_bikes.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_bikes, use_container_width=True)

        st.markdown("---")

    # Time Series Analysis
    if show_time_series and not historical_data.empty and hours <= 24:
        st.header("⏱️ Temporal Trends")

        # Aggregate by time
        historical_data['last_update'] = pd.to_datetime(historical_data['last_update'])
        time_series = historical_data.groupby('last_update').agg({
            'available_bikes': 'sum',
            'available_bike_stands': 'sum'
        }).reset_index()

        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(
            x=time_series['last_update'],
            y=time_series['available_bikes'],
            mode='lines',
            name='Available Bikes',
            line=dict(color='#636EFA', width=2),
            fill='tonexty'
        ))
        fig_time.add_trace(go.Scatter(
            x=time_series['last_update'],
            y=time_series['available_bike_stands'],
            mode='lines',
            name='Available Stands',
            line=dict(color='#EF553B', width=2),
            fill='tonexty'
        ))
        fig_time.update_layout(
            title=f"System-wide Availability Over Time ({time_range})",
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("---")

    # Station Details
    st.header("🔍 Station Details")

    # Station selector
    station_options = latest_data.sort_values('name')[['number', 'name']].apply(
        lambda x: f"{x['number']} - {x['name']}", axis=1
    ).tolist()

    selected_station = st.selectbox("Select a station to view details:", station_options, key='station_selector')

    if selected_station:
        station_number = int(selected_station.split(' - ')[0])
        station_data = latest_data[latest_data['number'] == station_number].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📍 Station Information")
            st.write(f"**Name:** {station_data['name']}")
            st.write(f"**Address:** {station_data['address']}")
            if pd.notna(station_data.get('commune')):
                st.write(f"**Commune:** {station_data['commune']}")
            st.write(f"**Status:** {station_data['status']}")
            st.write(f"**Availability:** {station_data['availability']}")
            st.write(f"**Last Update:** {station_data['last_update']}")

        with col2:
            st.subheader("🚲 Current Availability")
            st.metric("Available Bikes", station_data['available_bikes'])
            st.metric("Available Stands", station_data['available_bike_stands'])
            st.metric("Total Capacity", station_data['bike_stands'])

            occupancy = (station_data['available_bikes'] / station_data['bike_stands'] * 100) if station_data[
                                                                                                     'bike_stands'] > 0 else 0
            st.metric("Occupancy Rate", f"{occupancy:.1f}%")

        with col3:
            st.subheader("📊 Occupancy Gauge")
            occupancy = (station_data['available_bikes'] / station_data['bike_stands'] * 100) if station_data[
                                                                                                     'bike_stands'] > 0 else 0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=occupancy,
                title={'text': "Occupancy Rate (%)"},
                delta={'reference': 50},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightcoral"},
                        {'range': [25, 75], 'color': "lightgreen"},
                        {'range': [75, 100], 'color': "lightyellow"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Station history
        if hours <= 24:
            st.subheader(f"📈 Station History ({time_range})")
            station_history = load_station_history(conn, station_number, hours)

            if not station_history.empty:
                station_history['last_update'] = pd.to_datetime(station_history['last_update'])

                fig_station_time = go.Figure()
                fig_station_time.add_trace(go.Scatter(
                    x=station_history['last_update'],
                    y=station_history['available_bikes'],
                    mode='lines+markers',
                    name='Available Bikes',
                    line=dict(color='#636EFA'),
                    marker=dict(size=4)
                ))
                fig_station_time.add_trace(go.Scatter(
                    x=station_history['last_update'],
                    y=station_history['available_bike_stands'],
                    mode='lines+markers',
                    name='Available Stands',
                    line=dict(color='#EF553B'),
                    marker=dict(size=4)
                ))
                fig_station_time.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=350
                )
                st.plotly_chart(fig_station_time, use_container_width=True)
            else:
                st.info("No historical data available for this station in the selected time range.")

    # Raw Data Table
    st.markdown("---")
    with st.expander("📋 View Raw Data"):
        # Add download button
        csv = latest_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv,
            file_name=f"velov_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        st.dataframe(
            latest_data.sort_values('name'),
            use_container_width=True,
            hide_index=True
        )

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    with col2:
        st.caption(f"*Monitoring {total_stations} stations*")
    with col3:
        st.caption(f"*Data range: {time_range}*")


if __name__ == "__main__":
    main()