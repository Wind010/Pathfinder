# Pathfinder - Automated Recon Tool

A flexible, configuration-based reconnaissance automation tool for penetration testing.

## Features

- **Config-driven**: Define tools and their execution order in YAML
- **Parallel execution**: Tools with the same order run simultaneously
- **Sequential execution**: Different order values run one after another
- **Automatic /etc/hosts management**: Updates host entries before scanning
- **Variable substitution**: Dynamic values in tool arguments

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Make the hosts updater executable (Linux/WSL)
chmod +x update_hosts.sh
```

## Usage

Basic usage:
```bash
python pathfinder.py <ip_address> <hostname>
```

Example:
```bash
python pathfinder.py 10.10.10.10 example.htb
```

Advanced options:
```bash
# Custom config file
python pathfinder.py 10.10.10.10 example.htb -c custom_config.yaml

# Custom wordlists
python pathfinder.py 10.10.10.10 example.htb -w /path/to/dirs.txt -s /path/to/subs.txt

# Skip /etc/hosts update
python pathfinder.py 10.10.10.10 example.htb --skip-hosts

# Custom output directory
python pathfinder.py 10.10.10.10 example.htb -o /path/to/output
```

## Configuration

Edit `config.yaml` to customize tools and their execution:

```yaml
tools:
  - name: tool_name
    order: 1              # Execution order (same = parallel)
    tool_name: command    # Actual command to run
    arguments:            # List of arguments
      - "-flag"
      - "{variable}"
    output_file: "{output_dir}/result.txt"
    output_args:          # How to pass output file
      - "-o"
```

### Available Variables

- `{ip}` - Target IP address
- `{hostname}` - Target hostname
- `{output_dir}` - Output directory path
- `{wordlist}` - Directory wordlist path
- `{subdomain_wordlist}` - Subdomain wordlist path

### Order Parameter

- Tools with `order: 1` run in parallel
- Tools with `order: 2` wait for order 1 to complete, then run in parallel
- And so on...

## Adding New Tools

Simply add a new entry to the `tools` section in `config.yaml`:

```yaml
  - name: nmap_detailed
    order: 2              # Runs after order 1 tools
    tool_name: nmap
    arguments:
      - "-sV"
      - "-sC"
      - "{hostname}"
    output_file: "{output_dir}/nmap_{hostname}.txt"
    output_args:
      - "-oN"
```

## Examples

### Run gobuster after initial scans

```yaml
  - name: gobuster
    order: 2              # Waits for order 1 to finish
    tool_name: gobuster
    arguments:
      - "dir"
      - "-u"
      - "http://{hostname}"
      - "-w"
      - "{wordlist}"
    output_file: "{output_dir}/gobuster_{hostname}.txt"
    output_args:
      - "-o"
```

### Multiple tools in sequence

```yaml
tools:
  # Phase 1: Quick recon (parallel)
  - { name: rustscan, order: 1, ... }
  - { name: ffuf, order: 1, ... }
  
  # Phase 2: Detailed scan (parallel)
  - { name: nmap, order: 2, ... }
  - { name: nikto, order: 2, ... }
  
  # Phase 3: Exploitation (sequential)
  - { name: custom_exploit, order: 3, ... }
```
