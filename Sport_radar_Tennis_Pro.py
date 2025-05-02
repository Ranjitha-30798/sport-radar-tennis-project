import streamlit as st
import pandas as pd
import pymysql

# Tittle
st.set_page_config(page_title="Tennis Rankings Explorer", layout="wide")
st.title("🎾 TENNIS RANKINGS EXPLORER")
st.header("Rankings Dashboard")

#SQL
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    port=3306,
    database="tennis_project"
)
cursor = connection.cursor()
#Total number of competitors.
cursor.execute("SELECT COUNT(*) FROM competitor")
total_competitors = cursor.fetchone()[0]
st.metric("Total Competitors", total_competitors)

#Number of countries represented
cursor.execute("SELECT COUNT(DISTINCT country) FROM competitor")
num_countries = cursor.fetchone()[0]
st.metric("Countries Represented", num_countries)

#Highest points scored by a competitor.
cursor.execute("SELECT MAX(points) FROM ranking")
max_points = cursor.fetchone()[0]
st.metric("Highest Points Scored", max_points)

#Allow users to search for a competitor by name.
st.sidebar.header("🔍 Filter Competitors")
name_search = st.sidebar.text_input("Search by Name")
min_rank, max_rank = st.sidebar.slider("Rank Range", 1, 500, (1, 100))
min_points = st.sidebar.number_input("Minimum Points", min_value=0, value=0)

#Filter competitors by rank range, country, or points threshold.
cursor.execute("SELECT DISTINCT country FROM competitor ORDER BY country")
countries = [row[0] for row in cursor.fetchall()]
selected_country = st.sidebar.selectbox("Country", options=["All"] + countries)

# Competitor Details Viewer:
query = """
    SELECT c.name, r.rank, c.country, r.points
    FROM ranking r
    JOIN competitor c ON r.competitor_id = c.competitor_id
    WHERE 1=1
"""
params = []

if name_search:
    query += " AND c.name LIKE %s"
    params.append(f"%{name_search}%")

query += " AND r.rank BETWEEN %s AND %s"
params.extend([min_rank, max_rank])

if min_points > 0:
    query += " AND r.points >= %s"
    params.append(min_points)

if selected_country != "All":
    query += " AND c.country = %s"
    params.append(selected_country)

cursor.execute(query, params)
filtered_results = cursor.fetchall()
filtered_df = pd.DataFrame(filtered_results, columns=["Name", "Rank", "Country", "Points"])
filtered_df.drop_duplicates(inplace=True)
st.subheader("🎯 Filtered Competitors")
st.dataframe(filtered_df, use_container_width=True)


# --- Get list of unique competitors for dropdown ---
st.sidebar.header("👤 Competitor Details")
cursor.execute("SELECT DISTINCT name FROM competitor ORDER BY name")
competitor_names = [row[0] for row in cursor.fetchall()]

selected_name = st.sidebar.selectbox("Select a Competitor", ["None"] + competitor_names)

# --- Show details if a competitor is selected ---
if selected_name and selected_name != "None":
    detail_query = """
        SELECT c.name, r.rank, r.movement, r.competitions_played, c.country
        FROM competitor c
        JOIN ranking r ON c.competitor_id = r.competitor_id
        WHERE c.name = %s
    """
    try:
        cursor.execute(detail_query, (selected_name,))
        detail = cursor.fetchone()
        if detail:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📋 Competitor Info")
            st.sidebar.write(f"**Name:** {detail[0]}")
            st.sidebar.write(f"**Rank:** {detail[1]}")
            st.sidebar.write(f"**Movement:** {detail[2]}")
            st.sidebar.write(f"**Competitions Played:** {detail[3]}")
            st.sidebar.write(f"**Country:** {detail[4]}")
    except Exception as e:
        st.sidebar.error(f"Database error: {e}")

# Country-Wise Analysis:
st.subheader("🌍 Country-Wise Analysis")

country_query = """
    SELECT c.country, COUNT(*) AS total_competitors, ROUND(AVG(r.points), 2) AS avg_points
    FROM competitor c
    JOIN ranking r ON c.competitor_id = r.competitor_id
    GROUP BY c.country
    ORDER BY total_competitors DESC
"""
cursor.execute(country_query)
country_data = cursor.fetchall()
country_df = pd.DataFrame(country_data, columns=["Country", "Total Competitors", "Avg Points"])
country_df.drop_duplicates(inplace=True)
st.dataframe(country_df, use_container_width=True)

# Leaderboards:
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top-Ranked Competitors")
    top_rank_query = """
        SELECT c.name, r.rank, c.country, r.points
        FROM ranking r
        JOIN competitor c ON r.competitor_id = c.competitor_id
        ORDER BY r.rank ASC
        LIMIT 10
    """
    cursor.execute(top_rank_query)
    top_rank_df = pd.DataFrame(cursor.fetchall(), columns=["Name", "Rank", "Country", "Points"])
    top_rank_df.drop_duplicates(inplace=True)
    st.dataframe(top_rank_df, use_container_width=True)

with col2:
    st.subheader("🔥 Highest Point Scorers")
    top_points_query = """
        SELECT c.name, r.points, r.rank, c.country
        FROM ranking r
        JOIN competitor c ON r.competitor_id = c.competitor_id
        ORDER BY r.points DESC
        LIMIT 10
    """
    cursor.execute(top_points_query)
    top_points_df = pd.DataFrame(cursor.fetchall(), columns=["Name", "Points", "Rank", "Country"])
    top_points_df.drop_duplicates(inplace=True)
    st.dataframe(top_points_df, use_container_width=True)

cursor.close()
connection.close()




