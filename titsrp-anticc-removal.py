import time
import psutil
import os
import subprocess
from colorama import init, Fore, Style
from datetime import datetime, timedelta
init()

#config save
def get_gmod_directory():
    config_file = "config.txt"
    gmod_dir = ""

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                lines = f.read().splitlines()
                gmod_dir = lines[0].strip()
            if os.path.exists(os.path.join(gmod_dir, "gmod.exe")):
                return gmod_dir
        except Exception:
            pass

    while True:
        gmod_dir = input("Enter the Garry's Mod directory (where gmod.exe is located, e.g., C:\\Program Files (x86)\\Steam\\steamapps\\common\\GarrysMod): ").strip()
        if os.path.exists(os.path.join(gmod_dir, "gmod.exe")):
            try:
                with open(config_file, 'w') as f:
                    f.write(gmod_dir + "\n")
                return gmod_dir
            except Exception:
                print("Error saving to config.txt. Continuing without saving...")
                return gmod_dir
        else:
            print("Invalid directory or gmod.exe not found. Please try again.")

# first run config 
def get_run_time():
    config_file = "config.txt"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                lines = f.read().splitlines()
                if len(lines) > 1:
                    return int(lines[1])  # Return saved time
        except Exception:
            pass

    # First launch: prompt for time launch
    while True:
        try:
            hour = int(input("Enter the hour to run (0-23 in EST, e.g., 2 for 2 AM EST): "))
            if 0 <= hour <= 23:
                try:
                    with open(config_file, 'a') as f:
                        f.write(f"{hour}\n")
                    return hour
                except Exception:
                    print("Error saving run time. Using 2 AM EST as default...")
                    return 2
            else:
                print("Please enter an hour between 0 and 23.")
        except ValueError:
            print("Please enter a valid number.")

# terminate gmod.exe
def terminate_gmod():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == 'gmod.exe':
            try:
                proc.terminate()
                return True
            except Exception:
                pass
    return False

# launch GMod and connect to server
def launch_gmod(gmod_dir):
    try:
        subprocess.Popen([os.path.join(gmod_dir, "gmod.exe"), "+connect", "193.243.190.39:27015", "-condebug"], cwd=gmod_dir)
        print(f"{Fore.GREEN}[STATUS] Launched Garry's Mod with +connect parameter{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[STATUS] Failed to launch Garry's Mod: {e}{Style.RESET_ALL}")

# log file and monitor keywords
def tail_log(file_path, gmod_dir):
    start_time = time.time()
    file_exists = False
    connection_success = False

    while time.time() - start_time < 7200:  # 2-hour timeout
        if os.path.exists(file_path) and not file_exists:
            file_exists = True

        if file_exists:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while time.time() - start_time < 7200:
                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        line = line.strip()
                        if "Connecting to" in line:
                            print(f"{Fore.GREEN}[STATUS] Attempting to connect to server{Style.RESET_ALL}")
                        elif "Connected to" in line:
                            print(f"{Fore.GREEN}[STATUS] Joining server successfully!{Style.RESET_ALL}")
                        elif "DarkRP Message of the day!" in line:
                            print(f"{Fore.GREEN}[STATUS] Completed server join!{Style.RESET_ALL}")
                            connection_success = True
                        elif any(error in line for error in [
                            "CClientSteamContext OnSteamServersDisconnected logged on = 0",
                            "CClientSteamContext OnSteamServerConnectFailure logged on = 0",
                            "Achievements disabled: Steam not running.",
                            "Disconnected: Connection failed after 6 retries."
                        ]):
                            print(f"{Fore.RED}[STATUS] Connection error detected. Restarting in 60 seconds...{Style.RESET_ALL}")
                            terminate_gmod()
                            time.sleep(5)  # Wait for process to close
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)  # Clear console.log
                                except Exception:
                                    pass
                            time.sleep(55)  # Wait additional 55 
                            return False  # Restart
            except Exception:
                time.sleep(1)
        else:
            time.sleep(1)

    if connection_success:
        print(f"{Fore.YELLOW}[STATUS] 2 hours elapsed, closing Garry's Mod{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}[STATUS] 2 hours elapsed without successful connection, closing Garry's Mod{Style.RESET_ALL}")
    terminate_gmod()
    return True  # Exit

# run at specified time EST
run_hour = get_run_time()  # Get or set the run time (defaults to 2 AM if not set)
while True:
    # Get current time in EST (fixed UTC-5 for simplicity)
    current_time = datetime.utcnow() - timedelta(hours=5)  # EST is UTC-5
    next_run = current_time.replace(hour=run_hour, minute=0, second=0, microsecond=0)
    if current_time > next_run:
        next_run += timedelta(days=1)

    # Wait until the specified time EST
    wait_seconds = (next_run - current_time).total_seconds()
    print(f"{Fore.CYAN}[STATUS] Waiting until {run_hour}:00 AM EST. Next run in {int(wait_seconds // 3600)} hours, {int((wait_seconds % 3600) // 60)} minutes{Style.RESET_ALL}")
    time.sleep(wait_seconds)

    # Get GMod directory
    gmod_dir = get_gmod_directory()

    # Path to console.log
    log_path = os.path.join(gmod_dir, "garrysmod", "console.log")

    # Delete previous console.log file if it exists
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except Exception:
            pass

    # Ensure -condebug is set in GMod launch options
    print("Ensure '-condebug' is set in Garry's Mod launch options to log connection events to 'console.log'.")

    # Launch GMod and start monitoring with retries
    while True:
        launch_gmod(gmod_dir)
        if tail_log(log_path, gmod_dir):
            break  # Exit inner loop after 2 hours or successful run

    # Wait until next day at the same time EST after successful run
    print(f"{Fore.CYAN}[STATUS] Waiting until next {run_hour}:00 AM EST for the next run{Style.RESET_ALL}")
    time.sleep(86400)  # 24 hours