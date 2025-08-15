#!/usr/bin/env python3
"""
Utility script to check the status of Heroku Postgres databases
and monitor when Fork/Follow functionality becomes available.
"""
import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                                capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def check_database_status(app_name):
    """Check the status of Heroku Postgres databases for the app"""
    print(f"Checking database status for app: {app_name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get database info
    cmd = f"heroku pg:info -a {app_name}"
    output = run_command(cmd)
    
    if not output:
        return False
    
    # Look for Fork/Follow status in the output
    database_blocks = output.split("===")
    
    for block in database_blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        db_name = lines[0].strip()
        
        print(f"Database: {db_name}")
        
        fork_follow_status = "Unknown"
        db_plan = "Unknown"
        
        for line in lines:
            if "Fork/Follow:" in line:
                fork_follow_status = line.split(":", 1)[1].strip()
                print(f"  Fork/Follow: {fork_follow_status}")
            elif "Plan:" in line:
                db_plan = line.split(":", 1)[1].strip()
                print(f"  Plan: {db_plan}")
        
        # Check if this is our target database and if Fork/Follow is available
        if "DATABASE_URL" in db_name and "Standard" in db_plan:
            if fork_follow_status == "Available":
                print("\n✅ Fork/Follow functionality is now available!\n")
                return True
            elif fork_follow_status == "Temporarily Unavailable":
                print("\n⏳ Fork/Follow functionality is temporarily unavailable. Please wait...\n")
            else:
                print(f"\n❓ Unknown Fork/Follow status: {fork_follow_status}\n")
    
    return False

def monitor_database_status(app_name, interval=300, max_attempts=None):
    """Monitor database status at regular intervals"""
    print(f"Starting database status monitor for app: {app_name}")
    print(f"Checking every {interval} seconds")
    if max_attempts:
        print(f"Will check {max_attempts} times then exit")
    print("-" * 50)
    
    attempt = 1
    while True:
        print(f"Attempt {attempt}:")
        success = check_database_status(app_name)
        
        if success:
            print("Fork/Follow functionality is now available!")
            print("You can now create a follower database with:")
            print(f"heroku addons:create heroku-postgresql:standard-0 --app {app_name} -- --follow DATABASE_URL")
            break
            
        if max_attempts and attempt >= max_attempts:
            print(f"Reached maximum number of attempts ({max_attempts}). Exiting.")
            break
            
        attempt += 1
        print(f"Waiting {interval} seconds for next check...")
        print("-" * 50)
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Heroku Postgres database status")
    parser.add_argument("app_name", help="Heroku application name")
    parser.add_argument("--monitor", action="store_true", help="Monitor database status continuously")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds between checks (default: 300)")
    parser.add_argument("--max-attempts", type=int, help="Maximum number of attempts before exiting")
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_database_status(args.app_name, args.interval, args.max_attempts)
    else:
        check_database_status(args.app_name)