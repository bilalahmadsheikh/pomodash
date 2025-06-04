import streamlit as st
import time
from datetime import datetime
from supabase_client import supabase

def pomodoro_ui():
    st.title("⏳ Pomodoro Timer")
    st.markdown("Boost your productivity using the Pomodoro technique!")

    with st.form(key="pomodoro_form"):
        col1, col2 = st.columns(2)
        with col1:
            work_duration = st.number_input("Work Duration (minutes)", min_value=1, value=25)
        with col2:
            break_duration = st.number_input("Break Duration (minutes)", min_value=1, value=5)
        submit = st.form_submit_button("▶ Start Timer")

    if submit and not st.session_state.get("running", False):
        st.session_state.work_duration = work_duration
        st.session_state.break_duration = break_duration
        st.session_state.phase = "Work"
        st.session_state.start_time = time.time()
        st.session_state.elapsed = 0
        st.session_state.running = True
        st.session_state.paused = False
        st.session_state.skip_to_break = False
        st.session_state.partial_work_minutes = 0
        st.session_state.partial_break_minutes = 0
        st.rerun()

    if st.session_state.get("running", False):
        run_timer()

def run_timer():
    phase = st.session_state.phase
    duration = st.session_state.work_duration if phase == "Work" else st.session_state.break_duration
    total_time = duration * 60

    st.subheader(f"🕒 {phase} Session")
    timer_placeholder = st.empty()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    if col1.button("⏸ Pause"):
        st.session_state.paused = True
        st.session_state.elapsed += time.time() - st.session_state.start_time

    if col2.button("▶ Resume"):
        if st.session_state.paused:
            st.session_state.paused = False
            st.session_state.start_time = time.time()

    if col3.button("⏹ Stop"):
        st.session_state.running = False
        total_elapsed = st.session_state.elapsed + (time.time() - st.session_state.start_time)
        elapsed_minutes = round(total_elapsed / 60)

        if phase == "Work":
            st.session_state.partial_work_minutes += elapsed_minutes
        else:
            st.session_state.partial_break_minutes += elapsed_minutes

        log_to_supabase(
            work=st.session_state.partial_work_minutes,
            rest=st.session_state.partial_break_minutes,
            status="Early Stop"
        )
        st.warning(f"⛔ Session stopped early. Logged {elapsed_minutes} min of {phase}.")
        clear_timer_state()
        return

    if phase == "Work" and col4.button("⏭ Skip to Break"):
        total_elapsed = st.session_state.elapsed + (time.time() - st.session_state.start_time)
        elapsed_minutes = round(total_elapsed / 60)
        st.session_state.partial_work_minutes += elapsed_minutes

        st.session_state.phase = "Break"
        st.session_state.start_time = time.time()
        st.session_state.elapsed = 0
        st.session_state.skip_to_break = True
        st.info("⏭ Skipped to Break.")
        st.rerun()

    if not st.session_state.paused:
        elapsed = time.time() - st.session_state.start_time + st.session_state.get("elapsed", 0)
        remaining = int(total_time - elapsed)

        if remaining <= 0:
            st.success(f"✅ {phase} session completed!")
            elapsed_minutes = round(elapsed / 60)

            if phase == "Work":
                st.session_state.partial_work_minutes += elapsed_minutes
                st.session_state.phase = "Break"
                st.session_state.start_time = time.time()
                st.session_state.elapsed = 0
                st.rerun()
            else:
                st.session_state.partial_break_minutes += elapsed_minutes
                st.session_state.running = False
                log_to_supabase(
                    work=st.session_state.partial_work_minutes,
                    rest=st.session_state.partial_break_minutes,
                    status="Completed"
                )
                st.balloons()
                st.success("🎉 Pomodoro Session Complete!")
                clear_timer_state()
            return

        mins, secs = divmod(remaining, 60)
        timer_placeholder.markdown(f"### ⏱ Time Left: {mins:02d}:{secs:02d}")
        time.sleep(1)
        st.rerun()
    else:
        st.info("⏸ Timer is paused.")

def log_to_supabase(work, rest, status="Completed"):
    try:
        supabase.table("sessions").insert({
            "user_id": st.session_state.user.id,
            "work_minutes": work,
            "break_minutes": rest,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
        st.toast("✅ Session logged to Supabase.")
    except Exception as e:
        st.error(f"❌ Failed to log session: {e}")

def clear_timer_state():
    for key in [
        "work_duration", "break_duration", "phase", "start_time",
        "elapsed", "running", "paused", "partial_work_minutes",
        "partial_break_minutes", "skip_to_break"
    ]:
        st.session_state.pop(key, None)
