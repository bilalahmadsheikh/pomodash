import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from supabase_client import supabase
@st.cache_data(ttl=60)
# ---------------------- Data Fetch ----------------------
def fetch_sessions():
    try:
        user_id = st.session_state.user.id
        response = supabase.table("sessions").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def preprocess(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["total"] = df["work_minutes"] + df["break_minutes"]
    df["efficiency"] = df["work_minutes"] / df["total"] * 100
    return df
# ---------------------- Dashboard ----------------------
def show_dashboard():
     # ----------- INTRO ANIMATION -----------
    if "intro_shown" not in st.session_state:
        st.session_state.intro_shown = False

    if not st.session_state.intro_shown:
        st.markdown("""
        <style>
        .intro-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.92);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }

        .intro-overlay img {
            width: 130px;
            height: 130px;
            margin-bottom: 20px;
            animation: dropBounce 1s ease-out forwards;
            animation-delay: 0.1s;
        }

        .intro-overlay h1 {
            color: #00f2ff;
            font-size: 2.2rem;
            font-weight: 600;
            margin: 0;
            opacity: 0;
            animation: fadeInText 1s ease-in 1.1s forwards, fadeOutText 1s ease-out 3.2s forwards;
        }

        @keyframes dropBounce {
            0%   { transform: translateY(-200px); }
            60%  { transform: translateY(30px); }
            80%  { transform: translateY(-15px); }
            100% { transform: translateY(0); }
        }

        @keyframes fadeInText {
            to { opacity: 1; }
        }

        @keyframes fadeOutText {
            to { opacity: 0; }
        }

        @keyframes fadeOutImage {
            to { opacity: 0; }
        }

        @keyframes fadeOutOverlay {
            to { opacity: 0; visibility: hidden; }
        }
        </style>

        <div class="intro-overlay" id="intro">
            <img id="intro-img" src="https://i.gifer.com/Z30J.gif" alt="Loading..." />
            <h1 id="intro-text">Welcome to PomodoroDash</h1>
        </div>

        <script>
        setTimeout(() => {
            const img = document.getElementById('intro-img');
            if (img) {
                img.style.animation = 'fadeOutImage 1s ease forwards';
            }
        }, 5200); // Image fades out after text disappears

        setTimeout(() => {
            const intro = document.getElementById('intro');
            if (intro) {
                intro.style.animation = 'fadeOutOverlay 1s ease forwards';
            }
        }, 5700); // Overlay fades after image
        </script>
        """, unsafe_allow_html=True)

        time.sleep(6)
        st.session_state.intro_shown = True
        st.rerun()


    # ----------- DASHBOARD STYLES -----------
    st.markdown("""
    <style>
        .kpi-block {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 1rem;
            margin-bottom: 2rem;
        }

        .kpi {
            flex: 1 1 250px;
            min-width: 200px;
            background: #1b1f2b;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 0 12px rgba(0,255,255,0.08);
            transition: transform 0.3s ease;
        }

        .kpi:hover {
            transform: scale(1.03);
            box-shadow: 0 0 25px rgba(0, 255, 255, 0.3);
        }

        .kpi h1 {
            font-size: 2.2rem;
            margin: 0;
            color: #00f2ff;
            word-break: break-word;
        }

        .kpi p {
            margin: 8px 0 0;
            font-size: 1rem;
            color: #bbb;
            word-wrap: break-word;
        }

        @media screen and (max-width: 768px) {
            .kpi-block {
                flex-direction: column;
                align-items: stretch;
            }
            .kpi {
                width: 100%;
                min-width: unset;
            }
            .kpi h1 {
                font-size: 1.8rem;
            }
            .kpi p {
                font-size: 0.95rem;
            }
        }

        .insight-wrapper {
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-top: 60px;
            padding-left: 30px;
        }

        .insight-line {
            opacity: 0;
            animation: fadeIn 0.7s ease-in-out forwards;
            font-size: 16px;
            color: #e0e0e0;
            padding: 6px 0;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)

    # ----------- DASHBOARD CONTENT -----------
    st.markdown("<h2 style='color:#00f2ff; font-weight:600;'>📊 Productivity Dashboard</h2>", unsafe_allow_html=True)

    df_raw = fetch_sessions()
    if df_raw.empty:
        st.info("No session data found.")
        return
    df = preprocess(df_raw)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["total"] = df["work_minutes"] + df["break_minutes"]
    df["efficiency"] = df["work_minutes"] / df["total"] * 100

    total_sessions = len(df)
    total_minutes = df["total"].sum()
    avg_efficiency = round(df["efficiency"].mean(), 1)

    st.markdown(f"""
        <div class='kpi-block'>
            <div class='kpi'><h1>{total_sessions}</h1><p>Total Pomodoro Sessions</p></div>
            <div class='kpi'><h1>{total_minutes} min</h1><p>Focus Time Logged</p></div>
            <div class='kpi'><h1>{avg_efficiency}%</h1><p>Average Efficiency</p></div>
        </div>
    """, unsafe_allow_html=True)

    # ----------- Charts & Insights -----------
    st.markdown("### 🎯 Session Completion")
    chart_col, insight_col = st.columns([1, 1])
    with chart_col:
        st.plotly_chart(session_completion_chart(df), use_container_width=True)
    with insight_col:
        completed_count = (df["status"] == "Completed").sum()
        early_stop_count = (df["status"] == "Early Stop").sum()
        completed_time = df[df["status"] == "Completed"]["total"].sum()
        early_stop_time = df[df["status"] == "Early Stop"]["total"].sum()
        st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
        insights = [
            f"✅ <strong>Completed Sessions:</strong> {completed_count}",
            f"❌ <strong>Early Stops:</strong> {early_stop_count}",
            f"⏱️ <strong>Completed Time:</strong> {completed_time} minutes",
            f"🛑 <strong>Early Stop Time:</strong> {early_stop_time} minutes",
            f"💡 <em>Tracking early stops can reveal patterns of distraction or fatigue.</em>"
        ]
        for line in insights:
            st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
            time.sleep(0.6)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🕓 Time Allocation")
    chart_col2, insight_col2 = st.columns([1, 1])
    with chart_col2:
        st.plotly_chart(work_break_chart(df), use_container_width=True)
    with insight_col2:
        total_work = df["work_minutes"].sum()
        total_break = df["break_minutes"].sum()
        work_percent = round((total_work / (total_work + total_break)) * 100, 1) if total_work + total_break > 0 else 0
        break_percent = round(100 - work_percent, 1)

        st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
        insights = [
            f"🔵 <strong>Total Work Time:</strong> {total_work} minutes",
            f"🟠 <strong>Total Break Time:</strong> {total_break} minutes",
            f"📊 <strong>Work vs Break Ratio:</strong> {work_percent}% / {break_percent}%",
            f"💡 <em>Maintaining balance between work and rest boosts long-term productivity.</em>"
        ]
        for line in insights:
            st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
            time.sleep(0.6)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📅 Daily Focus Breakdown")
    st.plotly_chart(daily_stack_chart(df), use_container_width=True)

    st.markdown("### ⚡ Efficiency Over Time")
    st.plotly_chart(efficiency_line_chart(df), use_container_width=True)

    st.markdown("### 📈 Cumulative Focus Progress")
    st.plotly_chart(cumulative_focus_chart(df), use_container_width=True)

    st.markdown("### 📊 Explore Pomodoro Insights")
    chart_option = st.selectbox(
        "📊 Choose a chart to view:",
        [
            "Weekly Work Duration Trends",
            "Session Timing Patterns",
            "Streak Tracking",
            "Session Duration Scatter Plot",
            "Activity Heatmap",
            "View Sessions from Last 7 Days",
            "View Last 10 Sessions"
        ]
    )

    fig = None

    if chart_option == "Weekly Work Duration Trends":
        df['week'] = pd.to_datetime(df['timestamp']).dt.isocalendar().week
        weekly = df.groupby('week')['work_minutes'].sum().reset_index()

        fig = px.line(
            weekly,
            x='week',
            y='work_minutes',
            title='📆 Weekly Work Duration Trends',
            markers=True,
            labels={'week': 'Week Number', 'work_minutes': 'Total Work Minutes'}
        )
        fig.update_layout(margin=dict(t=40, b=20, l=30, r=30))

        # UI Columns
        chart_col, insight_col = st.columns([1.7, 1])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="weekly_work_chart")

        with insight_col:
            st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
            insights = [
                "📅 What it shows:",
                "This chart displays the total number of focused work minutes you logged each week.",
                "",
                "📈 How it works:",
                "It groups your sessions by calendar week and sums up all work minutes per week.",
                "",
                "🎯 Why it's useful:",
                "- Helps identify consistency or drops in productivity over time.",
                "- Useful for weekly reflections or adjusting future work plans.",
                "- Spot trends in workload spikes or burnout patterns."
            ]
            for line in insights:
                st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
                time.sleep(0.4)
            st.markdown("</div>", unsafe_allow_html=True)

    elif chart_option == "Session Timing Patterns":
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        hourly_counts = df.groupby('hour').size().reset_index(name='session_count')

        fig = px.bar(
            hourly_counts,
            x='hour',
            y='session_count',
            title='⏰ Session Timing Patterns',
            labels={
                'hour': 'Hour of the Day (24h Format)',
                'session_count': 'Number of Sessions Started'
            }
        )
        fig.update_layout(
            xaxis=dict(tickmode='linear', tick0=0, dtick=1),
            yaxis=dict(title='Session Count'),
            margin=dict(t=40, b=20, l=30, r=30)
        )

        chart_col, insight_col = st.columns([1.7, 1])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="timing_pattern_chart")
        with insight_col:
            st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
            for line in [
                "⏰ What it shows:",
                "This chart displays the number of Pomodoro sessions started at each hour of the day.",
                "",
                "🔍 How it works:",
                "It extracts the hour from each session timestamp and counts how many sessions started in that hour.",
                "",
                "💡 Why it's useful:",
                "- Reveals your peak focus hours during the day.",
                "- Helps in aligning task scheduling with your natural productivity cycle.",
                "- Useful to spot irregularities or gaps in your daily focus habits."
            ]:
                st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
                time.sleep(0.4)
            st.markdown("</div>", unsafe_allow_html=True)
        custom_rendered = True


    elif chart_option == "Streak Tracking":
    # Prepare data: Count completed sessions per date
        streaks = df[df['status'] == 'Completed'].groupby('date').size().reset_index(name='count')

        # Create the bar chart
        fig = px.bar(
            streaks,
            x='date',
            y='count',
            title='🔥 Streak Tracking',
            labels={
                'date': 'Date',
                'count': 'Number of Completed Sessions'
            }
        )
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Completed Sessions',
            margin=dict(t=40, b=20, l=30, r=30)
        )

        # UI Layout with chart and explanation
        chart_col, insight_col = st.columns([1.7, 1])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="streak_tracking_chart")

        with insight_col:
            st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
            insights = [
                "🔥 What it shows:",
                "Visualizes how many Pomodoro sessions you successfully completed each day.",
                "",
                "⚙️ How it works:",
                "It filters for sessions marked as 'Completed', groups them by date, and counts daily totals.",
                "",
                "🎯 Why it's useful:",
                "- Helps you identify consistency and build streaks of productivity.",
                "- Motivates you to maintain daily momentum.",
                "- Great for habit tracking and accountability."
            ]
            for line in insights:
                st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
                time.sleep(0.4)
            st.markdown("</div>", unsafe_allow_html=True)


    elif chart_option == "Session Duration Scatter Plot":
    # Create scatter plot: session duration over time
        fig = px.scatter(
            df,
            x='timestamp',
            y='total',
            color='status',
            title='🎯 Session Duration Scatter Plot',
            labels={
                'timestamp': 'Session Start Time',
                'total': 'Session Duration (minutes)',
                'status': 'Session Type'
            }
        )
        fig.update_layout(
            xaxis_title='Date & Time',
            yaxis_title='Duration (min)',
            margin=dict(t=40, b=30, l=30, r=30)
        )

        # UI layout
        chart_col, insight_col = st.columns([1.7, 1])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="scatter_duration_chart")

        with insight_col:
            st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
            insights = [
                "🎯 What it shows:",
                "A timeline of each Pomodoro session with its duration and status.",
                "",
                "🧠 How it works:",
                "Each point represents a session. The X-axis shows the start time, Y-axis shows its total duration, and color indicates if it was completed or ended early.",
                "",
                "📊 Why it's useful:",
                "- Helps visualize consistency and irregular sessions.",
                "- Spot clusters or outliers (very short or very long sessions).",
                "- Understand trends in productivity or burnout over time."
            ]
            for line in insights:
                st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
                time.sleep(0.4)
            st.markdown("</div>", unsafe_allow_html=True)


    elif chart_option == "Activity Heatmap":
    # Extract hour and weekday from timestamp
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['weekday'] = pd.to_datetime(df['timestamp']).dt.day_name()

        # Optional: Order weekdays for better heatmap readability
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['weekday'] = pd.Categorical(df['weekday'], categories=weekday_order, ordered=True)

        # Aggregate session counts by weekday and hour
        heatmap_data = df.groupby(['weekday', 'hour']).size().reset_index(name='sessions')

        # Create the density heatmap
        fig = px.density_heatmap(
            heatmap_data,
            x='hour',
            y='weekday',
            z='sessions',
            color_continuous_scale='Viridis',
            title='🔥 Activity Heatmap',
            labels={
                'hour': 'Hour of Day (24h)',
                'weekday': 'Weekday',
                'sessions': 'Session Count'
            }
        )
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title='Day of Week'),
            coloraxis_colorbar=dict(title='Sessions'),
            margin=dict(t=40, b=30, l=30, r=30)
        )

        # Layout with insights
        chart_col, insight_col = st.columns([1.7, 1])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="activity_heatmap_chart")

        with insight_col:
            st.markdown("<div class='insight-wrapper'>", unsafe_allow_html=True)
            insights = [
                "🌡️ What it shows:",
                "This heatmap visualizes how many Pomodoro sessions were started for each hour of each day.",
                "",
                "🧮 How it works:",
                "It counts how many sessions were logged for each hour of the day, across all weekdays.",
                "",
                "🔍 Why it's useful:",
                "- Identifies your most active days and hours.",
                "- Helps schedule deep work during your personal productivity peaks.",
                "- Reveals patterns like weekend dips or late-night focus spikes."
            ]
            for line in insights:
                st.markdown(f"<div class='insight-line'>{line}</div>", unsafe_allow_html=True)
                time.sleep(0.4)
            st.markdown("</div>", unsafe_allow_html=True)


    elif chart_option == "View Last 10 Sessions":
        recent_sessions = (
            df.sort_values('timestamp', ascending=False)
            .head(10)
            .loc[:, ['timestamp', 'work_minutes', 'break_minutes', 'status']]
            .rename(columns={
                'timestamp': 'Date & Time',
                'work_minutes': 'Work Duration (min)',
                'break_minutes': 'Break Duration (min)',
                'status': 'Session Status'
            })
        )
        
        st.markdown("### 🧾 Last 10 Pomodoro Sessions")
        st.dataframe(recent_sessions, use_container_width=True)


    elif chart_option == "View Sessions from Last 7 Days":
        recent = df[df['timestamp'] >= datetime.now(timezone.utc) - timedelta(days=7)].copy()
        display_recent = recent[["timestamp", "work_minutes", "break_minutes", "status"]].sort_values("timestamp", ascending=False)

        st.markdown("#### 🗓️ Your Sessions in the Last 7 Days")
        st.dataframe(display_recent, use_container_width=True)



    # Avoid duplicate rendering if already shown in custom layout
    if fig and chart_option not in [
        "Weekly Work Duration Trends",
        "Session Timing Patterns",
        "Streak Tracking",
        "Session Duration Scatter Plot",
        "Activity Heatmap",
        "View Last 10 Sessions",
        "View Sessions from Last 7 Days"
    ]:
        st.plotly_chart(fig, use_container_width=True)
    # Calculate Most Active Day
    df['weekday'] = pd.to_datetime(df['timestamp']).dt.day_name()
    most_active_day = df['weekday'].value_counts().idxmax()

    # Calculate Peak Productivity Week
    df['week'] = pd.to_datetime(df['timestamp']).dt.isocalendar().week
    weekly_work = df.groupby('week')['work_minutes'].sum()
    peak_week = weekly_work.idxmax()
    from statistics import mode

# 🕐 Most Common Session Hour
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    common_hour = df['hour'].mode()[0]

    # 🔁 Longest Streak of Consecutive Days with Sessions
    dates_with_sessions = sorted(df['date'].unique())
    longest_streak = current_streak = 1
    for i in range(1, len(dates_with_sessions)):
        if (dates_with_sessions[i] - dates_with_sessions[i-1]).days == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1

    # ⏱️ Average Session Duration
    average_duration = round(df['total'].mean(), 1)

    # 🧠 Best Focus Day (Highest Avg Efficiency)
    best_focus_day = (
        df.groupby('weekday')['efficiency'].mean()
        .sort_values(ascending=False)
        .idxmax()
    )
    # 🎯 Consistency Score = Average number of active days per week
    df['week'] = pd.to_datetime(df['timestamp']).dt.isocalendar().week
    df['year'] = pd.to_datetime(df['timestamp']).dt.isocalendar().year
    week_day_counts = df.groupby(['year', 'week'])['date'].nunique()
    consistency_score = round(week_day_counts.mean(), 2)
    # Ensure timestamps are timezone-aware
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter last 30 days
    last_30 = df[df['timestamp'] >= datetime.now(timezone.utc) - timedelta(days=30)].copy()

    # Define time ranges
    cutoff = datetime.now(timezone.utc) - timedelta(days=15)
    first_half = last_30[last_30['timestamp'] < cutoff]['work_minutes'].sum()
    second_half = last_30[last_30['timestamp'] >= cutoff]['work_minutes'].sum()

    # Progress calculation
    if first_half > 0:
        progress_percent = round(((second_half - first_half) / first_half) * 100, 1)
    else:
        progress_percent = 0  # To avoid division by zero



    # Add after all dropdown charts are rendered
    st.markdown("### 🧠 Final Productivity Summary")
    st.markdown(f"""
    <style>
    .final-summary-box {{
        background: linear-gradient(145deg, #1c1e26, #1b1d24);
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.08);
        color: #e0e0e0;
        font-size: 16px;
        line-height: 1.8;
        margin-top: 30px;
    }}
    .final-summary-box ul {{
        padding-left: 20px;
    }}
    .final-summary-box li {{
        margin-bottom: 12px;
    }}
    .final-summary-box strong {{
        color: #00f2ff;
    }}
    </style>

    <div class='final-summary-box'>
        <ul>
            <li>✅ <strong>Total Sessions Logged:</strong> {total_sessions}</li>
            <li>🕓 <strong>Focus Time Accumulated:</strong> {total_minutes} minutes</li>
            <li>⚡ <strong>Average Efficiency:</strong> {avg_efficiency}%</li>
            <li>📅 <strong>Most Active Day:</strong> {most_active_day}</li>
            <li>📈 <strong>Peak Productivity Week:</strong> Week {peak_week}</li>
            <li>💡 <strong>Tip:</strong> Maintain your streak and aim for consistent daily progress!</li>
            <li>🎯 <strong>Consistency Score:</strong> {consistency_score} active days/week</li>
            <li>🚀 <strong>Progress (Last 30 Days):</strong> {progress_percent}% change in work time</li>
            <li>🧠 <strong>Best Focus Day:</strong> {best_focus_day}</li>
            <li>⏱️ <strong>Average Session Duration:</strong> {average_duration} minutes</li>
            <li>🕐 <strong>Most Frequent Start Hour:</strong> {common_hour}:00</li>
            <li>🔥 <strong>Longest Daily Streak:</strong> {longest_streak} days</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    # ------- Footer -------
    st.markdown("""
    <hr style="margin-top: 3rem; margin-bottom: 1rem; border: none; border-top: 1px solid #444;">
    <div style='text-align: center; font-size: 14px; color: #888; padding-bottom: 15px;'>
         Created by <strong>Bilal Ahmad</strong>
    </div>
    """, unsafe_allow_html=True)

        




# ---------------------- Charts ----------------------
def session_completion_chart(df):
    fig = px.pie(df, names="status", hole=0.45,
             title="🎯 Session Completion",
             color_discrete_map={"Completed": "#00ffcc", "Early Stop": "#ff6b6b"})

    fig.update_traces(textinfo="percent+label", pull=[0.02]*len(df))
    return fig

def work_break_chart(df):
    work = df["work_minutes"].sum()
    break_ = df["break_minutes"].sum()
    fig = px.pie(
        names=["Work", "Break"],
        values=[work, break_],
        hole=0.45,
        title="🕓 Time Allocation",
        color_discrete_sequence=["#00d2ff", "#ffaa00"]

    )
    fig.update_traces(textinfo="percent+label")
    return fig

def daily_stack_chart(df):
    grouped = df.groupby("date")[["work_minutes", "break_minutes"]].sum().reset_index()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=grouped["date"],
        y=grouped["work_minutes"],
        name="Work",
        marker_color="#00f2ff",
        text=grouped["work_minutes"],
        texttemplate='%{text} min',
        textposition='inside'
    ))

    fig.add_trace(go.Bar(
        x=grouped["date"],
        y=grouped["break_minutes"],
        name="Break",
        marker_color="#ffaa00",
        text=grouped["break_minutes"],
        texttemplate='%{text} min',
        textposition='inside'
    ))

    fig.update_layout(
        barmode="stack",
        autosize=True,
        dragmode=False,  # Disables zoom/drag
        title=dict(
            text="📅 Daily Focus Breakdown<br><span style='font-size:13px; color:gray;'>Work vs Break distribution</span>",
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Date",
        yaxis_title="Minutes",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font=dict(color="white"),
        margin=dict(l=40, r=40, t=80, b=40)
    )
    return fig



def efficiency_line_chart(df):
    # Filter for valid sessions (exclude ones where total time is 0)
    df = df[(df["work_minutes"] > 0) & ((df["work_minutes"] + df["break_minutes"]) > 0)]

    # Truncate timestamp to just date (important for grouping)
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # Group total work and break time by date (includes all session types)
    grouped = df.groupby("date")[["work_minutes", "break_minutes"]].sum().reset_index()

    # Compute efficiency as a decimal (0–1)
    grouped["efficiency"] = grouped["work_minutes"] / (grouped["work_minutes"] + grouped["break_minutes"])

    # Build the chart
    fig = px.line(
        grouped,
        x="date",
        y="efficiency",
        markers=True,
        title="⚡ Average Daily Efficiency (All Sessions)",
        color_discrete_sequence=["#ff914d"]
    )

    fig.update_traces(
        mode="lines+markers",
        marker=dict(size=7, line=dict(width=2, color='white')),
        hovertemplate="Date: %{x}<br>Avg Efficiency: %{y:.2f}"
    )

    fig.update_layout(
        yaxis=dict(title="Efficiency (0–1)", range=[0, 1]),
        xaxis_title="Date",
        title=dict(x=0.5, xanchor='center'),
        font=dict(color="white"),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        dragmode=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig





def cumulative_focus_chart(df):
    # Ensure date column is in datetime format and extract date only
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # Group by date and calculate cumulative sums
    cumulative = df.groupby("date")[["work_minutes", "break_minutes"]].sum().cumsum().reset_index()

    # Create the cumulative area chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cumulative["date"],
        y=cumulative["work_minutes"],
        mode="lines",
        name="Work",
        fill="tozeroy",
        line=dict(color="#00ffcc"),
        hovertemplate="Date: %{x}<br>Work: %{y} min"
    ))
    fig.add_trace(go.Scatter(
        x=cumulative["date"],
        y=cumulative["break_minutes"],
        mode="lines",
        name="Break",
        fill="tozeroy",
        line=dict(color="#f39c12"),
        hovertemplate="Date: %{x}<br>Break: %{y} min"
    ))

    # Customize layout for dark theme and mobile optimization
    fig.update_layout(
        title="📈 Cumulative Work & Break Time",
        xaxis_title="Date",
        yaxis_title="Minutes",
        font=dict(color="white"),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        dragmode=False,  # Disable zooming on mobile
        margin=dict(l=40, r=40, t=60, b=40),
        title_x=0.5  # Center the title
    )

    return fig

