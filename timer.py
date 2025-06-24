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

    # Check for background completed sessions BEFORE starting new timer
    restore_timer_from_db()

    with st.form(key="pomodoro_form"):
        col1, col2 = st.columns(2)
        with col1:
            work_duration = st.number_input("Work Duration (minutes)", min_value=1, value=25)
        with col2:
            break_duration = st.number_input("Break Duration (minutes)", min_value=1, value=5)
        submit = st.form_submit_button("▶ Start Timer")

    if submit and not st.session_state.get("running", False):
        # Clear any existing timer state first
        clear_timer_state()
        delete_active_timer()
        
        st.session_state.work_duration = work_duration
        st.session_state.break_duration = break_duration
        st.session_state.original_work_duration = work_duration
        st.session_state.phase = "Work"
        st.session_state.start_time = time.time()
        st.session_state.start_timestamp = datetime.now(timezone.utc)
        st.session_state.elapsed = 0
        st.session_state.running = True
        st.session_state.paused = False
        st.session_state.session_id = None
        st.session_state.work_logged = False  # Track if work has been logged

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
    if "original_work_duration" not in st.session_state:
        st.session_state.original_work_duration = 25
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "work_logged" not in st.session_state:
        st.session_state.work_logged = False

    phase = st.session_state.phase
    duration = st.session_state.work_duration if phase == "Work" else st.session_state.break_duration
    total_time = duration * 60

    st.subheader(f"🕒 {phase} Session")
    timer_placeholder = st.empty()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    if col1.button("⏸ Pause"):
        st.session_state.paused = True
        st.session_state.elapsed += time.time() - st.session_state.start_time
        update_active_timer_pause_state()

    if col2.button("▶ Resume"):
        if st.session_state.paused:
            st.session_state.paused = False
            st.session_state.start_time = time.time()
            log_active_timer(phase, duration, st.session_state.break_duration, st.session_state.original_work_duration)

    if col3.button("⏹ Stop"):
        handle_timer_stop()
        return

    if phase == "Work" and col4.button("⏭ Skip to Break"):
        handle_skip_to_break()
        return

    if not st.session_state.paused:
        elapsed = time.time() - st.session_state.start_time + st.session_state.elapsed
        remaining = int(total_time - elapsed)

        if remaining <= 0:
            handle_timer_completion(elapsed)
            return

        mins, secs = divmod(remaining, 60)
        timer_placeholder.markdown(f"### ⏱ Time Left: {mins:02d}:{secs:02d}")
        
        # Use a more stable rerun approach
        time.sleep(0.1)
        st.rerun()
    else:
        st.info("⏸ Timer is paused.")


def handle_timer_stop():
    """Handle manual timer stop"""
    phase = st.session_state.phase
    total_elapsed = st.session_state.elapsed + (time.time() - st.session_state.start_time)
    elapsed_minutes = max(1, round(total_elapsed / 60))  # Minimum 1 minute

    if phase == "Work":
        # Log work session
        session_id = log_work_session(elapsed_minutes)
        st.session_state.session_id = session_id
        st.session_state.work_logged = True
    else:
        # Update existing session with break time or create new one
        if st.session_state.session_id and not st.session_state.work_logged:
            update_session_with_break(st.session_state.session_id, elapsed_minutes)
        else:
            log_complete_session(
                work_minutes=st.session_state.get('original_work_duration', 0),
                break_minutes=elapsed_minutes,
                status="Early Stop"
            )

    cleanup_timer()
    st.warning(f"⛔ Session stopped early. Logged {elapsed_minutes} min of {phase}.")


def handle_skip_to_break():
    """Handle skip to break functionality"""
    total_elapsed = st.session_state.elapsed + (time.time() - st.session_state.start_time)
    elapsed_minutes = max(1, round(total_elapsed / 60))
    
    # Log work session
    session_id = log_work_session(elapsed_minutes)
    st.session_state.session_id = session_id
    st.session_state.work_logged = True

    # Switch to break
    st.session_state.phase = "Break"
    st.session_state.start_time = time.time()
    st.session_state.start_timestamp = datetime.now(timezone.utc)
    st.session_state.elapsed = 0
    
    log_active_timer("Break", st.session_state.break_duration, st.session_state.break_duration, st.session_state.original_work_duration)
    st.info("⏭ Skipped to Break.")
    st.rerun()


def handle_timer_completion(elapsed):
    """Handle natural timer completion"""
    phase = st.session_state.phase
    elapsed_minutes = round(elapsed / 60)

    if phase == "Work":
        # Log work session
        session_id = log_work_session(elapsed_minutes)
        st.session_state.session_id = session_id
        st.session_state.work_logged = True
        
        st.success(f"✅ {phase} session completed!")
        
        # Switch to break
        st.session_state.phase = "Break"
        st.session_state.start_time = time.time()
        st.session_state.start_timestamp = datetime.now(timezone.utc)
        st.session_state.elapsed = 0
        
        log_active_timer("Break", st.session_state.break_duration, st.session_state.break_duration, st.session_state.original_work_duration)
        st.rerun()
    else:
        # Complete break session
        st.success(f"✅ {phase} session completed!")
        
        if st.session_state.session_id:
            update_session_with_break(st.session_state.session_id, elapsed_minutes)
        else:
            log_complete_session(
                work_minutes=st.session_state.get('original_work_duration', 25),
                break_minutes=elapsed_minutes,
                status="Completed"
            )
        
        cleanup_timer()
        st.balloons()
        st.success("🎉 Pomodoro Session Complete!")


def log_work_session(work_minutes):
    """Log work session immediately and return session ID for later update"""
    try:
        current_user = get_current_user()
        if not current_user:
            st.error("❌ Authentication required to log session.")
            return None
            
        response = supabase.table("sessions").insert({
            "user_id": current_user.id,
            "work_minutes": work_minutes,
            "break_minutes": 0,
            "status": "Work Completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        session_id = response.data[0]['id'] if response.data else None
        st.toast(f"✅ Work session logged: {work_minutes} minutes")
        return session_id
    except Exception as e:
        st.error(f"❌ Failed to log work session: {e}")
        return None


def update_session_with_break(session_id, break_minutes):
    """Update existing session with break time"""
    try:
        supabase.table("sessions").update({
            "break_minutes": break_minutes,
            "status": "Completed"
        }).eq("id", session_id).execute()
        
        st.toast(f"✅ Session completed with break: {break_minutes} minutes")
    except Exception as e:
        st.error(f"❌ Failed to update session with break: {e}")


def log_complete_session(work_minutes, break_minutes, status="Completed"):
    """Log a complete session (fallback method)"""
    try:
        current_user = get_current_user()
        if not current_user:
            st.error("❌ Authentication required to log session.")
            return
            
        supabase.table("sessions").insert({
            "user_id": current_user.id,
            "work_minutes": work_minutes,
            "break_minutes": break_minutes,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()
        st.toast("✅ Session logged to database.")
    except Exception as e:
        st.error(f"❌ Failed to log session: {e}")


def log_active_timer(phase, duration_minutes, break_duration=None, original_work_duration=None):
    """Store active timer state in database"""
    try:
        current_user = get_current_user()
        if not current_user:
            st.error("❌ Authentication required to store timer.")
            return
        
        timer_data = {
            "user_id": current_user.id,
            "phase": phase,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": duration_minutes,
            "status": "running"
        }
        
        # Encode break_duration and original_work_duration
        if break_duration is not None and original_work_duration is not None:
            encoded_value = break_duration * 1000 + original_work_duration
            timer_data["break_duration"] = encoded_value
        
        supabase.table("active_timer").upsert(timer_data).execute()
    except Exception as e:
        st.error(f"❌ Failed to store timer: {e}")


def update_active_timer_pause_state():
    """Update the active timer when paused"""
    try:
        current_user = get_current_user()
        if not current_user:
            return
        
        current_time = datetime.now(timezone.utc)
        elapsed_seconds = st.session_state.elapsed
        new_start_time = current_time - timedelta(seconds=elapsed_seconds)
        
        supabase.table("active_timer").update({
            "start_time": new_start_time.isoformat()
        }).eq("user_id", current_user.id).execute()
    except Exception as e:
        st.error(f"❌ Failed to update timer state: {e}")


def decode_break_duration(encoded_value):
    """Decode the break_duration and original_work_duration"""
    if encoded_value is None:
        return 5, 25
    
    break_dur = encoded_value // 1000
    work_dur = encoded_value % 1000
    
    # Sanity checks
    if break_dur <= 0 or break_dur > 60:
        break_dur = 5
    if work_dur <= 0 or work_dur > 120:
        work_dur = 25
        
    return break_dur, work_dur


def restore_timer_from_db():
    """Restore timer state from database and handle background completions"""
    try:
        current_user = get_current_user()
        if not current_user or st.session_state.get("running", False):
            return
            
        res = supabase.table("active_timer").select("*").eq("user_id", current_user.id).limit(1).execute()
        data = res.data[0] if res.data else None

        if not data:
            return

        start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        duration = data["duration_minutes"]
        phase = data["phase"]
        elapsed_seconds = (now - start_time).total_seconds()
        remaining_seconds = duration * 60 - elapsed_seconds
        
        # Decode break duration and original work duration
        stored_break_duration, original_work_duration = decode_break_duration(data.get("break_duration"))

        if remaining_seconds <= 0:
            # Timer completed in background
            if phase == "Work":
                # Log work session that completed in background
                session_id = log_work_session(duration)
                
                # Check if enough time has passed to auto-complete break too
                break_completion_time = start_time + timedelta(minutes=duration + stored_break_duration)
                
                if now >= break_completion_time:
                    # Both work and break completed in background
                    if session_id:
                        update_session_with_break(session_id, stored_break_duration)
                    else:
                        log_complete_session(duration, stored_break_duration, "Completed")
                    
                    cleanup_timer()
                    st.success("🎉 Pomodoro session auto-completed while away!")
                else:
                    # Start break session
                    remaining_break = (break_completion_time - now).total_seconds()
                    if remaining_break > 0:
                        st.session_state.session_id = session_id
                        st.session_state.work_logged = True
                        st.session_state.phase = "Break"
                        st.session_state.work_duration = original_work_duration
                        st.session_state.break_duration = stored_break_duration
                        st.session_state.original_work_duration = original_work_duration
                        st.session_state.start_time = time.time() - (stored_break_duration * 60 - remaining_break)
                        st.session_state.elapsed = 0
                        st.session_state.running = True
                        st.session_state.paused = False
                        
                        # Update active timer for break phase
                        break_start_time = start_time + timedelta(minutes=duration)
                        supabase.table("active_timer").update({
                            "phase": "Break",
                            "start_time": break_start_time.isoformat(),
                            "duration_minutes": stored_break_duration
                        }).eq("user_id", current_user.id).execute()
                        
                        st.success("✅ Work completed! Break session in progress.")
                    else:
                        # Break also completed
                        if session_id:
                            update_session_with_break(session_id, stored_break_duration)
                        cleanup_timer()
                        st.success("🎉 Full Pomodoro session completed while away!")
            else:
                # Break session completed in background
                # Try to find the corresponding work session
                work_duration = original_work_duration
                
                log_complete_session(work_duration, duration, "Completed")
                cleanup_timer()
                st.success("🎉 Break session auto-completed!")
        else:
            # Timer still running - restore state
            st.session_state.work_duration = duration if phase == "Work" else original_work_duration
            st.session_state.break_duration = stored_break_duration
            st.session_state.original_work_duration = original_work_duration
            st.session_state.phase = phase
            st.session_state.start_time = time.time() - elapsed_seconds
            st.session_state.elapsed = 0
            st.session_state.running = True
            st.session_state.paused = False
            st.session_state.session_id = None
            st.session_state.work_logged = False
            
            st.toast(f"🔁 Restored {phase} session!")
            
    except Exception as e:
        st.error(f"❌ Timer restore error: {e}")
        cleanup_timer()


def cleanup_timer():
    """Clean up timer state and database"""
    delete_active_timer()
    clear_timer_state()


def delete_active_timer():
    """Delete active timer from database"""
    try:
        current_user = get_current_user()
        if current_user:
            supabase.table("active_timer").delete().eq("user_id", current_user.id).execute()
    except:
        pass


def clear_timer_state():
    """Clear all timer-related session state"""
    keys_to_clear = [
        "work_duration", "break_duration", "phase", "start_time",
        "elapsed", "running", "paused", "start_timestamp",
        "original_work_duration", "session_id", "work_logged"
    ]
    
    for key in keys_to_clear:
        st.session_state.pop(key, None)
