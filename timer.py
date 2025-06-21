import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from supabase_client import supabase
from url_session_manager import get_current_user

def pomodoro_ui():
    st.title("⏳ Pomodoro Timer")
    st.markdown("Boost your productivity using the Pomodoro technique!")

    # Ensure we have a valid user
    current_user = get_current_user()
    if not current_user:
        st.error("❌ Authentication required. Please log in again.")
        return

    restore_timer_from_db()

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
        st.session_state.original_work_duration = work_duration  # Track original work duration
        st.session_state.phase = "Work"
        st.session_state.start_time = time.time()
        st.session_state.start_timestamp = datetime.now(timezone.utc)
        st.session_state.elapsed = 0
        st.session_state.running = True
        st.session_state.paused = False
        st.session_state.skip_to_break = False
        st.session_state.partial_work_minutes = 0
        st.session_state.partial_break_minutes = 0

        log_active_timer("Work", work_duration, break_duration, work_duration)
        st.rerun()

    if st.session_state.get("running", False):
        run_timer()


def run_timer():
    # Ensure we have a valid user
    current_user = get_current_user()
    if not current_user:
        st.error("❌ Authentication required. Please log in again.")
        st.session_state.running = False
        return

    # Initialize session state variables if they don't exist
    if "paused" not in st.session_state:
        st.session_state.paused = False
    if "elapsed" not in st.session_state:
        st.session_state.elapsed = 0
    if "partial_work_minutes" not in st.session_state:
        st.session_state.partial_work_minutes = 0
    if "partial_break_minutes" not in st.session_state:
        st.session_state.partial_break_minutes = 0
    if "original_work_duration" not in st.session_state:
        st.session_state.original_work_duration = 25  # Default fallback

    phase = st.session_state.phase
    duration = st.session_state.work_duration if phase == "Work" else st.session_state.break_duration
    total_time = duration * 60

    st.subheader(f"🕒 {phase} Session")
    timer_placeholder = st.empty()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    if col1.button("⏸ Pause"):
        st.session_state.paused = True
        st.session_state.elapsed += time.time() - st.session_state.start_time
        # Update database with current state
        update_active_timer_pause_state()

    if col2.button("▶ Resume"):
        if st.session_state.paused:
            st.session_state.paused = False
            st.session_state.start_time = time.time()
            # Update database with resumed state
            log_active_timer(phase, duration, st.session_state.break_duration, st.session_state.original_work_duration)

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
        delete_active_timer()
        st.warning(f"⛔ Session stopped early. Logged {elapsed_minutes} min of {phase}.")
        clear_timer_state()
        return

    if phase == "Work" and col4.button("⏭ Skip to Break"):
        total_elapsed = st.session_state.elapsed + (time.time() - st.session_state.start_time)
        elapsed_minutes = round(total_elapsed / 60)
        st.session_state.partial_work_minutes += elapsed_minutes

        # DON'T log here - only accumulate work time for final logging
        st.session_state.phase = "Break"
        st.session_state.start_time = time.time()
        st.session_state.start_timestamp = datetime.now(timezone.utc)
        st.session_state.elapsed = 0
        st.session_state.skip_to_break = True
        # DON'T reset partial_work_minutes - keep it for final logging
        log_active_timer("Break", st.session_state.break_duration, st.session_state.break_duration, st.session_state.original_work_duration)
        st.info("⏭ Skipped to Break.")
        st.rerun()

    if not st.session_state.paused:
        elapsed = time.time() - st.session_state.start_time + st.session_state.elapsed
        remaining = int(total_time - elapsed)

        if remaining <= 0:
            st.success(f"✅ {phase} session completed!")
            elapsed_minutes = round(elapsed / 60)

            if phase == "Work":
                st.session_state.partial_work_minutes += elapsed_minutes
                st.session_state.phase = "Break"
                st.session_state.start_time = time.time()
                st.session_state.start_timestamp = datetime.now(timezone.utc)
                st.session_state.elapsed = 0
                log_active_timer("Break", st.session_state.break_duration, st.session_state.break_duration, st.session_state.original_work_duration)
                st.rerun()
            else:
                # Only log when BOTH work and break are complete
                st.session_state.partial_break_minutes += elapsed_minutes
                st.session_state.running = False
                log_to_supabase(
                    work=st.session_state.partial_work_minutes,
                    rest=st.session_state.partial_break_minutes,
                    status="Completed"
                )
                delete_active_timer()
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
        current_user = get_current_user()
        if not current_user:
            st.error("❌ Authentication required to log session.")
            return
            
        supabase.table("sessions").insert({
            "user_id": current_user.id,
            "work_minutes": work,
            "break_minutes": rest,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()
        st.toast("✅ Session logged to Supabase.")
    except Exception as e:
        st.error(f"❌ Failed to log session: {e}")


def log_active_timer(phase, duration_minutes, break_duration=None, original_work_duration=None):
    try:
        current_user = get_current_user()
        if not current_user:
            st.error("❌ Authentication required to store timer.")
            return
        
        # Store additional data in a JSON-like format using the break_duration field
        # Since we can't change the DB, we'll store JSON data in break_duration field
        timer_data = {
            "user_id": current_user.id,
            "phase": phase,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "status": "running"
        }
        
        # Store both break_duration and original_work_duration
        # We'll use a simple encoding: break_duration * 1000 + original_work_duration
        if break_duration is not None and original_work_duration is not None:
            encoded_value = break_duration * 1000 + original_work_duration
            timer_data["break_duration"] = encoded_value
        elif break_duration is not None:
            timer_data["break_duration"] = break_duration * 1000 + 25  # Default work duration
        elif hasattr(st.session_state, 'break_duration'):
            work_dur = getattr(st.session_state, 'original_work_duration', 25)
            timer_data["break_duration"] = st.session_state.break_duration * 1000 + work_dur
            
        supabase.table("active_timer").upsert(timer_data).execute()
    except Exception as e:
        st.error(f"❌ Failed to store timer: {e}")


def update_active_timer_pause_state():
    """Update the active timer when paused to maintain accurate timing"""
    try:
        current_user = get_current_user()
        if not current_user:
            return
        
        # Calculate elapsed time and update start_time to account for pause
        current_time = datetime.now(timezone.utc)
        elapsed_seconds = st.session_state.elapsed
        new_start_time = current_time - timedelta(seconds=elapsed_seconds)
        
        supabase.table("active_timer").update({
            "start_time": new_start_time.isoformat()
        }).eq("user_id", current_user.id).execute()
    except Exception as e:
        st.error(f"❌ Failed to update timer state: {e}")


def decode_break_duration(encoded_value):
    """Decode the break_duration and original_work_duration from encoded value"""
    if encoded_value is None:
        return 5, 25  # Default values
    
    break_dur = encoded_value // 1000
    work_dur = encoded_value % 1000
    
    # Sanity checks
    if break_dur <= 0 or break_dur > 60:
        break_dur = 5
    if work_dur <= 0 or work_dur > 120:
        work_dur = 25
        
    return break_dur, work_dur


def restore_timer_from_db():
    try:
        current_user = get_current_user()
        if not current_user or st.session_state.get("running", False):
            return
            
        res = supabase.table("active_timer").select("*").eq("user_id", current_user.id).limit(1).execute()
        data = res.data[0] if res.data else None

        if data:
            start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            duration = data["duration_minutes"]
            phase = data["phase"]
            elapsed = (now - start_time).total_seconds()
            remaining = duration * 60 - elapsed
            
            # Decode break duration and original work duration
            stored_break_duration, original_work_duration = decode_break_duration(data.get("break_duration"))

            if remaining <= 0:
                if phase == "Work":
                    # Work session completed in background - DON'T log yet, just start break
                    st.session_state.partial_work_minutes = duration  # Store completed work time
                    st.session_state.partial_break_minutes = 0
                    st.session_state.phase = "Break"
                    st.session_state.work_duration = duration
                    st.session_state.break_duration = stored_break_duration
                    st.session_state.original_work_duration = original_work_duration
                    st.session_state.start_time = time.time()
                    st.session_state.start_timestamp = datetime.now(timezone.utc)
                    st.session_state.elapsed = 0
                    st.session_state.running = True
                    st.session_state.paused = False
                    log_active_timer("Break", stored_break_duration, stored_break_duration, original_work_duration)
                    st.toast("✅ Work session auto-completed. Break started.")
                    st.rerun()
                else:
                    # Break session completed in background - NOW log the complete session
                    completed_work_minutes = original_work_duration
                    st.session_state.partial_break_minutes = duration
                    log_to_supabase(
                        work=completed_work_minutes,
                        rest=st.session_state.partial_break_minutes,
                        status="Completed"
                    )
                    delete_active_timer()
                    clear_timer_state()
                    st.toast("✅ Pomodoro session auto-completed.")
                    st.rerun()
            else:
                # Restore timer if still running
                st.session_state.work_duration = duration if phase == "Work" else original_work_duration
                st.session_state.break_duration = stored_break_duration
                st.session_state.original_work_duration = original_work_duration
                st.session_state.phase = phase
                st.session_state.start_time = time.time() - elapsed
                st.session_state.elapsed = 0
                st.session_state.running = True
                st.session_state.paused = False
                st.session_state.partial_work_minutes = 0
                st.session_state.partial_break_minutes = 0
                st.toast(f"🔁 Restored {phase} session!")
    except Exception as e:
        st.error(f"❌ Timer restore error: {e}")


def delete_active_timer():
    try:
        current_user = get_current_user()
        if current_user:
            supabase.table("active_timer").delete().eq("user_id", current_user.id).execute()
    except:
        pass


def clear_timer_state():
    for key in [
        "work_duration", "break_duration", "phase", "start_time",
        "elapsed", "running", "paused", "partial_work_minutes",
        "partial_break_minutes", "skip_to_break", "start_timestamp",
        "original_work_duration"
    ]:
        st.session_state.pop(key, None)
