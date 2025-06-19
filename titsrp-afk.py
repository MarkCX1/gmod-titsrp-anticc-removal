import time
import psutil
import os
import subprocess
from colorama import init, Fore, Style
from datetime import datetime, timedelta
import tzlocal
import webbrowser

init()

# Save/load run time and duration
def get_config(current_time):
    config_file = "config.txt"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    return int(lines[0].strip()), int(lines[1].strip())
        except:
            pass
    print(f"Current time: {current_time.strftime('%I:%M %p')}")
    while True:
        user_input = input("Enter hour to run (0-23, e.g., 2 for 2 AM, or Enter to start now): ").strip()
        run_hour = None if user_input == "" else None
        if user_input != "":
            try:
                run_hour = int(user_input)
                if not 0 <= run_hour <= 23:
                    print("Enter hour between 0-23.")
                    continue
            except ValueError:
                print("Enter valid number or press Enter.")
                continue
        while True:
            try:
                duration = int(input("Enter AFK session duration in hours (1-24): "))
                if 1 <= duration <= 24:
                    if run_hour is not None or duration:
                        with open(config_file, 'w') as f:
                            f.write(f"{run_hour if run_hour is not None else ''}\n{duration}")
                    return run_hour, duration * 3600  # Convert to seconds
                print("Enter duration between 1-24 hours.")
            except ValueError:
                print("Enter valid number.")
    return run_hour, duration

# Terminate gmod.exe
def terminate_gmod():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == 'gmod.exe':
            try:
                proc.terminate()
                return True
            except:
                pass
    return False

# Launch GMod and join server
def launch_gmod_and_join():
    try:
        subprocess.Popen(["start", "steam://rungameid/4000", "-condebug"], shell=True)
        print(f"{Fore.GREEN}[STATUS] Launched Garry's Mod{Style.RESET_ALL}")
        time.sleep(15)
        webbrowser.open("steam://connect/193.243.190.39:27015")
        print(f"{Fore.GREEN}[STATUS] Initiated server join{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[STATUS] Failed to launch or join: {e}{Style.RESET_ALL}")

# Monitor log file
def tail_log(log_path, duration):
    start_time = time.time()
    file_exists = False
    while time.time() - start_time < duration:
        if os.path.exists(log_path) and not file_exists:
            file_exists = True
        if file_exists:
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while time.time() - start_time < duration:
                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        line = line.strip()
                        if "Connecting to" in line:
                            print(f"{Fore.GREEN}[STATUS] Connecting to server{Style.RESET_ALL}")
                        elif "Connected to" in line:
                            print(f"{Fore.GREEN}[STATUS] Joined server{Style.RESET_ALL}")
                        elif "DarkRP Message of the day!" in line:
                            print(f"{Fore.GREEN}[STATUS] Server join complete{Style.RESET_ALL}")
                            return True
                        elif any(error in line for error in [
                            "CClientSteamContext OnSteamServersDisconnected",
                            "CClientSteamContext OnSteamServerConnectFailure",
                            "Achievements disabled: Steam not running.",
                            "Disconnected: Connection failed after 6 retries."
                        ]):
                            print(f"{Fore.RED}[STATUS] Connection error. Restarting in 60s{Style.RESET_ALL}")
                            terminate_gmod()
                            time.sleep(5)
                            if os.path.exists(log_path):
                                try:
                                    os.remove(log_path)
                                except:
                                    pass
                            time.sleep(55)
                            return False
            except:
                time.sleep(1)
        else:
            time.sleep(1)
    print(f"{Fore.YELLOW}[STATUS] Session duration reached, closing Garry's Mod{Style.RESET_ALL}")
    terminate_gmod()
    return True

# Countdown display
def display_countdown(seconds, run_hour):
    while seconds > 0:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        print(f"\r{Fore.CYAN}[STATUS] Next run at {run_hour}:00 ({time_str} remaining){Style.RESET_ALL}", end="")
        time.sleep(1)
        seconds -= 1
    print()

# Main loop
local_tz = tzlocal.get_localzone()
current_time = datetime.now(local_tz)
run_hour, duration = get_config(current_time)
while True:
    current_time = datetime.now(local_tz)
    if run_hour is None:
        next_run = current_time
    else:
        next_run = current_time.replace(hour=run_hour, minute=0, second=0, microsecond=0)
        if current_time > next_run:
            next_run += timedelta(days=1)
    wait_seconds = (next_run - current_time).total_seconds()
    if wait_seconds > 0:
        print(f"{Fore.CYAN}[STATUS] Waiting until {run_hour}:00 in {local_tz}{Style.RESET_ALL}")
        display_countdown(wait_seconds, run_hour if run_hour is not None else current_time.hour)
    log_path = os.path.expanduser("~/AppData/Local/GarrysMod/garrysmod/console.log")
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except:
            pass
    print("Ensure '-condebug' is set in Garry's Mod launch options.")
    while True:
        launch_gmod_and_join()
        if tail_log(log_path, duration):
            break
    if run_hour is None:
        break
    print(f"{Fore.CYAN}[STATUS] Waiting for next run at {run_hour}:00 in {local_tz}{Style.RESET_ALL}")
    next_run = current_time.replace(hour=run_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
    wait_seconds = (next_run - current_time).total_seconds()
    display_countdown(wait_seconds, run_hour)