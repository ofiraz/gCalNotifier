import subprocess

def send_mac_notification(title, message):
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ])

# Example usage
send_mac_notification("Hello!", "This is a notification from Python.")