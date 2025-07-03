import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openai
from io import BytesIO

# --- SET OPENAI KEY (NEW SDK) ---
openai.api_key = "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"

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="StatStreak", layout="wide")
st.title("⚾️ StatStreak: Baseball Analytics Dashboard")

# --- FILE UPLOAD ---
uploaded_files = st.file_uploader("📁 Upload CSV files for one or more players", type="csv", accept_multiple_files=True)

if uploaded_files:
    data_dict = {}
    st.subheader("📄 Uploaded Players' Data Preview")

    for file in uploaded_files:
        name = file.name.replace(".csv", "")
        df = pd.read_csv(file)
        df['source'] = name
        data_dict[name] = df

        st.markdown(f"**{name}**")
        st.dataframe(df.head())

    # --- MULTI-PLAYER MULTI-STAT COMPARISON ---
    st.subheader("📈 Compare Players Across Stats")
    compare_stats = st.multiselect("Select stats to compare", ['OPS', 'WAR', 'HR', 'RBI'], default=['OPS'])
    fig_compare = go.Figure()

    for stat in compare_stats:
        for name, df_temp in data_dict.items():
            year_col_temp = 'Year' if 'Year' in df_temp.columns else 'Season' if 'Season' in df_temp.columns else None
            if year_col_temp and stat in df_temp.columns:
                df_temp = df_temp.sort_values(year_col_temp)
                fig_compare.add_trace(go.Scatter(
                    x=df_temp[year_col_temp],
                    y=df_temp[stat],
                    mode='lines+markers',
                    name=f"{name} - {stat}"
                ))

    fig_compare.update_layout(title="Stat Comparison Over Time", height=500)
    st.plotly_chart(fig_compare, use_container_width=True)

    # --- SINGLE PLAYER ANALYSIS ---
    selected_player = st.selectbox("🔍 Select a player for detailed analysis", list(data_dict.keys()))
    df = data_dict[selected_player]
    year_col = 'Year' if 'Year' in df.columns else 'Season' if 'Season' in df.columns else None
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    if year_col:
        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
        year_min, year_max = int(df[year_col].min()), int(df[year_col].max())
        year_range = st.slider("📆 Filter by Year", year_min, year_max, (year_min, year_max))
        df = df[df[year_col].between(year_range[0], year_range[1])]

    # --- RADAR CHART: 5-TOOL PROFILE ---
    five_tool_stats = ['AVG', 'OBP', 'SLG', 'HR', 'SB']
    if all(stat in df.columns for stat in five_tool_stats):
        st.subheader("🕸️ 5-Tool Radar Chart")
        radar_values = [
            round(df[stat].mean(), 3) if stat not in ['HR', 'SB'] else int(df[stat].sum())
            for stat in five_tool_stats
        ]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=radar_values, theta=five_tool_stats, fill='toself'))
        fig_radar.update_layout(title="5-Tool Profile", polar=dict(radialaxis=dict(visible=True)), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- MULTI-STAT LINE CHART (SINGLE PLAYER) ---
    st.subheader("📊 Multi-Stat Trend")
    selected_stats = st.multiselect("Choose stats to plot", numeric_cols, default=['OPS', 'WAR'])
    if selected_stats and year_col:
        fig_multi = px.line(df, x=year_col, y=selected_stats, markers=True, title="Player Stat Trends")
        st.plotly_chart(fig_multi, use_container_width=True)

    # --- SINGLE-STAT BAR CHART + DOWNLOADS ---
    stat_choice = st.selectbox("📈 Select a stat for detailed bar chart", numeric_cols)
    if stat_choice and year_col:
        st.subheader(f"{stat_choice} by {year_col}")
        y_max = df[stat_choice].max()
        y_margin = y_max * 0.05
        fig = px.bar(df, x=year_col, y=stat_choice, height=600, title=f"{stat_choice} by {year_col}")
        fig.update_yaxes(range=[0, y_max + y_margin])
        st.plotly_chart(fig, use_container_width=True)

        # Export PNG
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("⬇️ Download Chart as PNG", buffer.getvalue(), file_name=f"{selected_player}_{stat_choice}.png")

        # Top 10
        st.subheader(f"🏅 Top 10 Years by {stat_choice}")
        top10 = df[[year_col, stat_choice]].sort_values(by=stat_choice, ascending=False).head(10)
        st.dataframe(top10)
        st.download_button("⬇️ Download Top 10 CSV", top10.to_csv(index=False), file_name=f"{selected_player}_top10_{stat_choice}.csv")

    # --- SIDEBAR: CAREER SUMMARY ---
    st.sidebar.subheader("📌 Career Summary")
    if 'WAR' in df.columns:
        st.sidebar.metric("Total WAR", round(df['WAR'].sum(), 2))
    if 'OPS' in df.columns:
        st.sidebar.metric("Average OPS", round(df['OPS'].mean(), 3))
    if 'HR' in df.columns:
        st.sidebar.metric("Total HR", int(df['HR'].sum()))

    # --- AI CHATBOT (OPENAI >=1.0.0) ---
    st.subheader("🤖 Ask AI a question about player performance")

    user_question = st.text_input("Examples: 'How might Bryce Harper perform in 2026?' or 'Who had the better 2022 season?'")

    if user_question:
        stats_summary = ""
        for name, df_temp in data_dict.items():
            year_col_temp = 'Year' if 'Year' in df_temp.columns else 'Season' if 'Season' in df_temp.columns else None
            stats_cols = [col for col in df_temp.columns if col in ['WAR', 'OPS', 'HR', 'SB']]
            if year_col_temp:
                stats_cols.insert(0, year_col_temp)
            preview = df_temp[stats_cols].to_string(index=False)
            stats_summary += f"\n{name}:\n{preview}\n"

        prompt = f"""
You are a baseball analyst. Based on the stats below, answer the user's question with a helpful and analytical explanation.

Player Stats:
{stats_summary}

Question: {user_question}
"""

        with st.spinner("Thinking..."):
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"OpenAI error: {e}")

else:
    st.info("Upload one or more player CSV files to begin.")


