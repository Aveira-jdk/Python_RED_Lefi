# Remote Administration Tool

This project comprises a client-side and server-side script written in Python for enabling remote administration and management of client machines over a network connection. The system allows the server to control various aspects of the client machines, including executing commands, transferring files, and retrieving system information.

## Client-Side Script

### Overview:

The client-side script serves as the interface between the client machine and the remote server. It establishes a socket connection with the server and listens for commands and instructions. The script executes commands received from the server, performs file upload and download operations, and provides system information upon request.

### Key Features:

- **Socket Communication**: Utilizes Python's `socket` module to establish and maintain a network connection with the remote server.
- **File Transfer**: Implements segmented file upload and download operations to efficiently handle large files. Ensures file integrity using MD5 hash verification.
- **Command Execution**: Executes shell commands sent from the server, allowing for remote control and management of the client machine.
- **Platform Compatibility**: Provides platform-specific functions for retrieving system information tailored for macOS, Linux, and Windows operating systems.
- **Error Handling**: Gracefully handles various exceptions, including connection errors, timeouts, and file-related issues, ensuring robust operation.
- **Mutex Handling**: Implements a mutex mechanism to prevent multiple instances of the client script from running simultaneously on the same machine.
- **Cleanup**: Removes the mutex file upon termination to ensure a clean exit and avoid conflicts with future executions.

### Usage:

1. Clone or download the client-side script onto the target machines that require remote administration.
2. Customize the script parameters, such as the server's IP address, port, and desired functionality.
3. Run the script on the client machines to establish a connection with the remote server.
4. Ensure the server-side script is running and accessible from the client machines.
5. Use the server-side interface to send commands and manage the client machines remotely.

### Dependencies:

- Python 3.12.x
- `requests` module (for location retrieval functionality)
- `socket` module (for socket communication)
- `os` module (for platform-specific functions)
- `time` module (for sleep functionality)
- `threading` module (for multiple client handling)
- `sys` module (for system information retrieval)
- `subprocess` module (for command execution)
- `hashlib` module (for MD5 hash verification)
- `random` module (for random number generation)
- `json` module (for json functionality)
### Compatibility:

- Tested on macOS, Linux, and Windows operating systems.

## Server-Side Script

### Overview:

The server-side script acts as the central control hub for managing and administering the client machines. It listens for incoming connections from client scripts and responds to requests by sending commands, receiving system information, and facilitating file transfers.

### Key Features:

- **Socket Communication**: Utilizes Python's `socket` module to accept and handle incoming connections from client machines.
- **Command Dispatching**: Processes commands received from the client scripts and executes appropriate actions, such as running shell commands or initiating file transfers.
- **Session Management**: Maintains a list of active client sessions and provides functionality to connect to, disconnect from, or manage individual sessions.
- **Remote Command Execution**: Sends commands to client machines for execution and receives output responses for display or further processing.
- **File Transfer Control**: Facilitates file upload and download operations between the server and client machines, ensuring data integrity and security.
- **Error Handling**: Implements robust error handling mechanisms to handle unexpected situations and maintain system stability.

### Usage:

1. Run the server-side script on a designated server machine with network connectivity to the client machines.
2. Customize the script parameters, such as the listening port and any additional configuration options.
3. Monitor incoming connections and client sessions using the server-side interface.
4. Send commands, retrieve system information, and manage client machines remotely via the server-side interface.
5. Terminate the server-side script when administration tasks are complete or as needed.

### Dependencies:

- Python 3.12.x
- `socket` module (for socket communication)
- `os` module (for platform-specific functions)
- `threading` module (for multiple client handling)
- `termcolor` module (for adding colored output to the terminal)
- `prettytable` module (for formatting tabular data in a visually appealing way)
- `hashlib` module (for MD5 hash verification)
- `logging` module (for logging functionality)
### Compatibility:

- Tested on various platforms with Python 3.12.3 support.

## Disclaimer:

This remote administration system is intended for educational and authorized remote administration purposes only. Any unauthorized or malicious use of this system is strictly prohibited and may result in legal consequences. Use this system responsibly and in accordance with applicable laws and regulations.
