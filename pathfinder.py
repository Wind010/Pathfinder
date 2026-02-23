#!/usr/bin/env python3
import subprocess
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
import os
import pwd
import traceback
import yaml
from collections import defaultdict
from colorama import Fore, Style, init

from hosts_manager import update_hosts

# Initialize colorama
init(autoreset=True)

# Global debug flag
DEBUG = False

def load_config(config_file):
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def expand_path(path):
    """Expand ~ to the correct user's home directory, even when running with sudo"""
    # If running with sudo, use the original user's home directory
    if 'SUDO_USER' in os.environ:
        sudo_user = os.environ['SUDO_USER']
        # Get the original user's home directory
        try:
            user_home = pwd.getpwnam(sudo_user).pw_dir
            # Replace ~ with the actual home directory
            if path.startswith('~/'):
                return os.path.join(user_home, path[2:])
            elif path == '~':
                return user_home
        except KeyError:
            pass
    # Fall back to normal expansion
    return os.path.expanduser(path)

def run_tool(tool_config, variables):
    """Run a tool based on its configuration"""
    name = tool_config['name']
    tool_name = tool_config['tool_name']
    
    # Merge global variables with tool-specific variables
    tool_vars = variables.copy()
    
    # If tool has a wordlist field, use it (with expansion)
    if 'wordlist' in tool_config:
        tool_vars['wordlist'] = expand_path(tool_config['wordlist'])
    
    # Build command with variable substitution
    cmd = [tool_name]
    for arg in tool_config.get('arguments', []):
        cmd.append(arg.format(**tool_vars))
    
    # Add output file if specified
    output_file = None
    if 'output_file' in tool_config:
        output_file = tool_config['output_file'].format(**tool_vars)
        if 'output_args' in tool_config:
            cmd.extend(tool_config['output_args'])
            cmd.append(output_file)
    
    print(f"{Fore.CYAN}\n[*] Running {name}...")
    print(f"{Fore.CYAN}    Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            print(f"{Fore.GREEN}[+] {name} completed")
        else:
            print(f"{Fore.RED}[!] {name} completed with errors (return code: {result.returncode})")
        
        if output_file:
            print(f"{Fore.GREEN}    Output saved to: {output_file}")
        
        if DEBUG:
            print(f"{Fore.YELLOW}    Return code: {result.returncode}")
            if result.stdout:
                print(f"{Fore.YELLOW}    STDOUT: {result.stdout[:500]}")
            if result.stderr:
                print(f"{Fore.YELLOW}    STDERR: {result.stderr[:500]}")
        
        return {'name': name, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}[!] {name} timed out")
        return {'name': name, 'returncode': -1, 'error': 'timeout'}
    except Exception as e:
        print(f"{Fore.RED}[!] {name} failed: {e}")
        if DEBUG:
            print(f"{Fore.YELLOW}    {traceback.format_exc()}")
        return {'name': name, 'returncode': -1, 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description="Automated host scanning with configurable tools")
    parser.add_argument("--ip", required=True, help="IP address of target")
    parser.add_argument("--hostname", required=True, help="Hostname for /etc/hosts")
    parser.add_argument("-c", "--config", default="./config.yaml",
                       help="Path to configuration file")
    parser.add_argument("-o", "--output-dir", required=True,
                       help="Output directory for results")
    parser.add_argument("-s", "--skip-hosts", action="store_true",
                       help="Skip updating /etc/hosts file")
    parser.add_argument("-d", "--debug", action="store_true",
                       help="Enable debug logging with detailed error information")
    
    args = parser.parse_args()
    
    # Set debug flag
    global DEBUG
    DEBUG = args.debug
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Config file not found: {args.config}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"{Fore.RED}[!] Error parsing config file: {e}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Update /etc/hosts
    if not args.skip_hosts:
        if not update_hosts(args.ip, args.hostname):
            print(f"{Fore.RED}[!] Failed to update /etc/hosts. Continue anyway? (y/n)")
            if input().lower() != 'y':
                sys.exit(1)
    
    # Prepare variables for substitution
    variables = {
        'ip': args.ip,
        'hostname': args.hostname,
        'output_dir': args.output_dir
    }
    # Group tools by order
    tools_by_order = defaultdict(list)
    for tool in config.get('tools', []):
        order = tool.get('order', 999)
        tools_by_order[order].append(tool)
    
    # Execute tools in order
    all_results = []
    for order in sorted(tools_by_order.keys()):
        tools = tools_by_order[order]
        
        if len(tools) == 1:
            # Run single tool sequentially
            result = run_tool(tools[0], variables)
            all_results.append(result)
        else:
            # Run multiple tools in parallel
            print(f"{Fore.CYAN}\n[*] Running {len(tools)} tools in parallel (order {order})...")
            with ThreadPoolExecutor(max_workers=len(tools)) as executor:
                futures = [executor.submit(run_tool, tool, variables) for tool in tools]
                results = [future.result() for future in futures]
                all_results.extend(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"{Fore.GREEN}[+] All scans complete!")
    print(f"{Fore.GREEN}    Results saved to: {args.output_dir}/")
    print(f"\n[*] Summary:")
    for result in all_results:
        if result.get('returncode') == 0:
            print(f"{Fore.GREEN}    ✓ {result['name']}")
        else:
            print(f"{Fore.RED}    ✗ {result['name']}")
            if DEBUG:
                print(f"{Fore.YELLOW}      Return code: {result.get('returncode')}")
                if 'error' in result:
                    print(f"{Fore.YELLOW}      Error: {result['error']}")
                if result.get('stderr'):
                    print(f"{Fore.YELLOW}      STDERR: {result['stderr'][:200]}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()