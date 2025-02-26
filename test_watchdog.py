#!/usr/bin/env python3
"""
Test script to verify the bot's watchdog functionality.
This script simulates a bot crash by sending a SIGSTOP signal to the bot process.
"""

import os
import time
import signal
import subprocess
import sys

def find_bot_pid():
    """Find the PID of the running bot process."""
    try:
        # Check if PID file exists
        if os.path.exists("bot.pid"):
            with open("bot.pid", "r") as f:
                pid = int(f.read().strip())
                # Verify process exists
                try:
                    os.kill(pid, 0)  # Signal 0 doesn't kill the process, just checks if it exists
                    return pid
                except OSError:
                    print("PID file exists but process is not running")
                    return None
        else:
            print("No PID file found")
            
            # Try to find the process using ps
            try:
                result = subprocess.check_output(["ps", "aux"]).decode()
                for line in result.split("\n"):
                    if "python bot.py" in line and "grep" not in line:
                        pid = int(line.split()[1])
                        print(f"Found bot process with PID {pid}")
                        return pid
            except Exception as e:
                print(f"Error finding process: {e}")
                
        return None
    except Exception as e:
        print(f"Error finding bot PID: {e}")
        return None

def test_watchdog():
    """Test the watchdog functionality by simulating a bot crash."""
    pid = find_bot_pid()
    
    if not pid:
        print("❌ Bot process not found. Make sure the bot is running.")
        return
    
    print(f"✅ Found bot process with PID {pid}")
    print("🔍 Testing watchdog functionality...")
    
    try:
        # Send SIGSTOP to freeze the process (simulating a hang)
        print(f"⏸️ Sending SIGSTOP to process {pid} to simulate a hang...")
        os.kill(pid, signal.SIGSTOP)
        
        print("⏳ Waiting for watchdog to detect inactivity (this may take up to 5 minutes)...")
        print("   You can check the logs in another terminal with: tail -f bot.log")
        
        # Wait for up to 6 minutes (watchdog should trigger at 5 minutes)
        for i in range(36):  # 36 * 10 seconds = 360 seconds = 6 minutes
            time.sleep(10)
            
            # Check if original process is still stopped
            try:
                os.kill(pid, 0)
                print(f"   Original process {pid} still exists after {i*10} seconds")
            except OSError:
                print(f"   Original process {pid} no longer exists after {i*10} seconds")
                break
                
            # Check if a new process has started
            new_pid = find_bot_pid()
            if new_pid and new_pid != pid:
                print(f"✅ Watchdog worked! New bot process started with PID {new_pid}")
                # Resume the original process so it can exit properly
                try:
                    os.kill(pid, signal.SIGCONT)
                except OSError:
                    pass  # Process might be gone already
                return
        
        # If we get here, the watchdog didn't work
        print("❌ Watchdog did not restart the bot within the expected time")
        
        # Resume the original process
        try:
            print(f"▶️ Resuming original process {pid}...")
            os.kill(pid, signal.SIGCONT)
        except OSError:
            print(f"   Process {pid} no longer exists")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        # Try to resume the process if it's still around
        try:
            os.kill(pid, signal.SIGCONT)
        except:
            pass

if __name__ == "__main__":
    test_watchdog() 