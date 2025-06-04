
# 📘 Project Documentation: Pomodoro Productivity Dashboard

## 📌 Overview
**Pomodoro Productivity Dashboard** is a Streamlit web app that helps users manage focus and track their productivity using the Pomodoro technique. It supports session tracking, session completion analytics, work/break ratio insights, streak visualization, and personalized charts — all powered by a Supabase backend.

## 🛠️ Features
- ⏱️ Pomodoro Timer with pause, resume, and stop
- 📊 Interactive Analytics Dashboard (Plotly)
  - Session completion rate
  - Work vs break time ratio
  - Daily/weekly productivity trends
  - Focus efficiency score
  - Streak tracking, activity heatmap, and more
- 🔐 User Authentication (via Supabase)
- 📁 Supabase PostgreSQL backend for session storage
- 🎨 Animated UI (hover/click interactions, splash animation)
- ☁️ Deployed via Streamlit Community Cloud

## 📂 Project Structure
```
/pomodash_streamlit
├── app.py                  # Main entry point (Streamlit UI)
├── auth.py                 # Login and registration logic
├── timer.py                # Pomodoro timer logic and session control
├── analytics.py            # Analytics dashboard with interactive charts
├── supabase_client.py      # Supabase client setup
├── requirements.txt        # Python package dependencies
└── .streamlit/
    └── config.toml         # Streamlit configuration
```

## 🔑 Secrets Management
Secrets such as Supabase `url` and `key` are securely stored using:
- **Local dev**: `.streamlit/secrets.toml` (not pushed to GitHub)
- **Deployment**: Streamlit Cloud → Settings → Advanced → Secrets

Example:
```toml
[supabase]
url = "https://your-url.supabase.co"
key = "your-anon-key"
```

## 🧪 Technologies Used
| Purpose             | Technology     |
|---------------------|----------------|
| Frontend UI         | Streamlit      |
| Charts & Plots      | Plotly         |
| Data Manipulation   | Pandas         |
| Backend DB          | Supabase (PostgreSQL) |
| Auth & Storage      | Supabase Auth  |
| Hosting             | Streamlit Cloud |
| Time Handling       | Python datetime, time |
| Numerical Analysis  | NumPy (optional) |

## 🚀 How to Run Locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/pomodash_streamlit.git
   cd pomodash_streamlit
   ```

2. **Set up secrets**
   Create `.streamlit/secrets.toml`:
   ```toml
   [supabase]
   url = "https://your-url.supabase.co"
   key = "your-anon-key"
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## 📝 Future Improvements
- 🧠 Machine Learning-based productivity suggestions
- 📆 Calendar view for session logs
- 🗃 Export reports (CSV/PDF)
- 📱 Responsive mobile UI
- 🔔 Reminder/Notification system
