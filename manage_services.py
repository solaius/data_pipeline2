import subprocess
import sys
import time
import os

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker():
    print("\nChecking Docker status...")
    success, stdout, stderr = run_command("docker info")
    if not success:
        print("✗ Docker is not running or not accessible")
        print(f"Error: {stderr}")
        return False
    print("✓ Docker is running")
    return True

def check_redis():
    print("\nChecking Redis container...")
    success, stdout, stderr = run_command("docker ps --filter name=doc_pipeline2-redis -q")
    if not stdout.strip():
        print("✗ Redis container is not running")
        return False
    print("✓ Redis container is running")
    return True

def start_redis():
    print("\nStarting Redis...")
    success, stdout, stderr = run_command("docker-compose up -d redis")
    if not success:
        print(f"✗ Failed to start Redis: {stderr}")
        return False
    
    # Wait for Redis to be ready
    print("Waiting for Redis to be ready...")
    for _ in range(5):
        if check_redis():
            return True
        time.sleep(2)
    
    print("✗ Redis failed to start properly")
    return False

def stop_redis():
    print("\nStopping Redis...")
    success, stdout, stderr = run_command("docker-compose stop redis")
    if not success:
        print(f"✗ Failed to stop Redis: {stderr}")
        return False
    print("✓ Redis stopped")
    return True

def restart_redis():
    stop_redis()
    time.sleep(2)
    return start_redis()

def show_logs():
    print("\nShowing container logs...")
    success, stdout, stderr = run_command("docker-compose logs --tail=100")
    if not success:
        print(f"✗ Failed to get logs: {stderr}")
    else:
        print("\nLogs:")
        print(stdout)

def main():
    if not check_docker():
        print("Please make sure Docker is running and try again.")
        sys.exit(1)

    while True:
        print("\nService Management Menu:")
        print("1. Check Redis status")
        print("2. Start Redis")
        print("3. Stop Redis")
        print("4. Restart Redis")
        print("5. Show logs")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            check_redis()
        elif choice == "2":
            start_redis()
        elif choice == "3":
            stop_redis()
        elif choice == "4":
            restart_redis()
        elif choice == "5":
            show_logs()
        elif choice == "6":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()