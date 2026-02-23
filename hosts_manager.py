"""
Hosts Manager Module
Manages /etc/hosts file entries with automatic IP/hostname updates
"""
import os
import re
import subprocess
import tempfile
import shutil


def update_hosts(ip, hostname):
    """
    Update /etc/hosts file with new IP/hostname entry.
    
    If the hostname already exists, it will be updated with the new IP.
    Otherwise, a new entry will be added.
    
    Args:
        ip (str): IP address to add
        hostname (str): Hostname to associate with the IP
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Determine hosts file path based on OS
    if os.name == 'nt':  # Windows
        hosts_file = r'C:\Windows\System32\drivers\etc\hosts'
    else:  # Linux/Unix
        hosts_file = '/etc/hosts'
    
    # Validate IP address format (basic validation)
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if not ip_pattern.match(ip):
        print(f"[!] Invalid IP address format: {ip}")
        return False
    
    # Validate each octet is 0-255
    octets = ip.split('.')
    if not all(0 <= int(octet) <= 255 for octet in octets):
        print(f"[!] Invalid IP address: {ip}")
        return False
    
    try:
        # Read current hosts file
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        
        # Check if hostname already exists and remove it
        new_lines = []
        hostname_found = False
        pattern = re.compile(rf'\s+{re.escape(hostname)}(\s|$)')
        
        for line in lines:
            if pattern.search(line):
                hostname_found = True
                print(f"[*] Hostname '{hostname}' found in {hosts_file}. Updating IP address...")
            else:
                new_lines.append(line)
        
        # Add new entry
        new_entry = f"{ip} {hostname}\n"
        new_lines.append(new_entry)
        
        # Create backup
        backup_file = f"{hosts_file}.bak"
        shutil.copy2(hosts_file, backup_file)
        
        # Write updated content to a temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='hosts_') as temp_file:
            temp_file.writelines(new_lines)
            temp_path = temp_file.name
        
        # Use sudo/elevated privileges to update hosts file
        if os.name == 'nt':  # Windows
            # On Windows, just try to copy (requires admin rights)
            shutil.move(temp_path, hosts_file)
        else:  # Linux/Unix
            # Check if we're already running as root
            if os.geteuid() == 0:
                # Already root, no need for sudo
                shutil.move(temp_path, hosts_file)
                os.chmod(hosts_file, 0o644)
            else:
                # Use sudo to move the file
                subprocess.run(['sudo', 'mv', temp_path, hosts_file], check=True)
                subprocess.run(['sudo', 'chmod', '644', hosts_file], check=True)
        
        if hostname_found:
            print(f"[+] Updated: {ip} {hostname}")
        else:
            print(f"[+] Added: {ip} {hostname}")
        
        return True
        
    except PermissionError:
        print(f"[!] Permission denied. Run with sudo/administrator privileges.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
    except FileNotFoundError:
        print(f"[!] Hosts file not found: {hosts_file}")
        return False
    except Exception as e:
        print(f"[!] Error updating hosts file: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def remove_host(hostname):
    """
    Remove a hostname entry from /etc/hosts file.
    
    Args:
        hostname (str): Hostname to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Determine hosts file path based on OS
    if os.name == 'nt':  # Windows
        hosts_file = r'C:\Windows\System32\drivers\etc\hosts'
    else:  # Linux/Unix
        hosts_file = '/etc/hosts'
    
    try:
        # Read current hosts file
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        
        # Filter out lines with the hostname
        new_lines = []
        hostname_found = False
        pattern = re.compile(rf'\s+{re.escape(hostname)}(\s|$)')
        
        for line in lines:
            if pattern.search(line):
                hostname_found = True
            else:
                new_lines.append(line)
        
        if not hostname_found:
            print(f"[*] Hostname '{hostname}' not found in {hosts_file}")
            return True
        
        # Create backup
        backup_file = f"{hosts_file}.bak"
        shutil.copy2(hosts_file, backup_file)
        
        # Write updated content to a temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='hosts_') as temp_file:
            temp_file.writelines(new_lines)
            temp_path = temp_file.name
        
        # Use sudo/elevated privileges to update hosts file
        if os.name == 'nt':  # Windows
            shutil.move(temp_path, hosts_file)
        else:  # Linux/Unix
            subprocess.run(['sudo', 'mv', temp_path, hosts_file], check=True)
            subprocess.run(['sudo', 'chmod', '644', hosts_file], check=True)
        
        print(f"[+] Removed: {hostname}")
        return True
        
    except Exception as e:
        print(f"[!] Error removing hostname: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False
