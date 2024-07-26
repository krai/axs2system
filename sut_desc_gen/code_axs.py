import subprocess
import json
import re
import os
import shutil
import math

def if_qaic_util_path_exists(qaic_util_path):
    if os.path.exists(qaic_util_path):
        return True
    return False

def get_uname_output(command):
   
    # Execute the command and capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    if result.returncode != 0:
        return None

    # Replace hostname with 'kernel' in the output
    parts = result.stdout.strip().split()
    if parts[0] == 'Linux' and len(parts) > 2:
        parts[1] = 'kernel'
        # Reconstruct the output string
        modified_output = ' '.join(parts)
        return modified_output
    
    # Return the original output if the condition is not met
    return result.stdout.strip()

def get_lsb_release_output(command):
    
    # Execute the command and capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    if result.returncode != 0:
        return None

    # Parse the output to extract DISTRIB_DESCRIPTION value
    for line in result.stdout.split('\n'):
        if line.startswith('DISTRIB_DESCRIPTION='):
            return line.split('=', 1)[1].strip('"')
        
    return None

def get_version(command):

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return None

def get_software_stack():

    docker_version = get_version(["docker", "--version"])
    python_version = get_version(["python3", "--version"])

    software_stack = []
    if docker_version:
        software_stack.append(docker_version.replace('Docker version', 'Docker'))
    if python_version:
        software_stack.append(python_version)

    return "; ".join(software_stack)

def get_system_info_bak(qaic_util_path=None, device_tool_query=None):

    # Execute manufacturer name details
    manufacturer_cmd = "cat /sys/devices/virtual/dmi/id/bios_vendor"
    manufacturer_result = subprocess.run(manufacturer_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    manufacturer = re.sub(r'(?i)\s*inc\.?', '', manufacturer_result.stdout.strip())

    # Execute product name details
    product_name_cmd = "cat /sys/devices/virtual/dmi/id/product_name"
    product_name_result = subprocess.run(product_name_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    product_name = product_name_result.stdout.strip()
    
    # Count number of qaic devices
    if device_tool_query:
        isQaic = if_qaic_util_path_exists(qaic_util_path) 
        if isQaic:
            accelerators_per_node = device_tool_query.get("accelerators_per_node")
            # Format the system name
            system_name = f"{manufacturer} {product_name} ({accelerators_per_node}x QAIC100 Standard)"
    else:
        system_name = f"{manufacturer} {product_name}"

    return system_name 


def get_host_memory_capacity():
    # Command to get memory size using dmidecode
    command_dmidecode = """sudo dmidecode -t memory | grep -i size | grep -v 'No Module Installed' |
                            awk '{if ($3=="GB") s+=$2; else if ($3=="MB") s+=$2/1024}
                            END {print s}'"""

    try:
        # Execute the dmidecode command
        result = subprocess.run(command_dmidecode, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dmidecode_output = result.stdout.strip()

        # Check if the result is not empty or just whitespace
        if dmidecode_output and dmidecode_output.isdigit():
            total_memory_gb = float(dmidecode_output)
            if total_memory_gb >= 1024:
                return f"{round(total_memory_gb / 1024)} TB"
            else:
                return f"{round(total_memory_gb)} GB"
        else:
            print("dmidecode did not return expected output, switching to /proc/meminfo")
            raise subprocess.CalledProcessError(1, command_dmidecode, "dmidecode returned empty or unexpected output")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else str(e)
        print(f"An error occurred with dmidecode: {error_message}")

        # Fallback to reading /proc/meminfo
        try:
            # Command to get memory size from /proc/meminfo
            command_meminfo = "grep -i memtotal /proc/meminfo"
            result = subprocess.run(command_meminfo, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            meminfo_output = result.stdout.strip()

            # Extract the memory size in kB and convert to GB
            memtotal_kb = int(meminfo_output.split()[1])
            memtotal_gb = memtotal_kb / 1024 / 1024
            return f"{math.ceil(memtotal_gb)} GB"
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while reading /proc/meminfo: {e.stderr.strip()}")
            return None


def get_host_memory_configuration():
    """Get memory configuration as 'number x size GB'."""

    cmd_dmidecode = "sudo dmidecode -t memory | grep -i size | grep -v 'No Module Installed'"
    
    try:
        # Attempt to execute the dmidecode command
        output = subprocess.run(cmd_dmidecode, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        # Correctly access the stdout attribute of the result for splitlines()
        lines = output.stdout.splitlines()
        modules = []

        # Process each line of the output to extract the memory sizes in MB
        for line in lines:
            size_match = re.search(r'^\s*Size:\s*(\d+)\s*(MB|GB)', line, re.IGNORECASE)
            if size_match:
                size, unit = int(size_match.group(1)), size_match.group(2).upper()
                if unit == "GB":
                    size *= 1024  # Convert GB to MB for uniformity
                modules.append(size)

        # Count the occurrences of each module size to get the configuration
        module_counts = {size: modules.count(size) for size in set(modules)}
        configurations = [f'{count}x {(size//1024)} GB' for size, count in module_counts.items()]

        return ", ".join(configurations)

    except subprocess.CalledProcessError as e:
        # If dmidecode fails, fallback to /proc/meminfo
        print(f"dmidecode failed: {e.stderr}")
        try:
            cmd_meminfo = "grep -i memtotal /proc/meminfo"
            output = subprocess.run(cmd_meminfo, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            meminfo_output = output.stdout.strip()
            
            # Extract the memory size in kB and convert to GB
            memtotal_kb = int(meminfo_output.split()[1])
            memtotal_gb = memtotal_kb / 1024 / 1024
            
            # Assume a single module if detailed information is not available
            return f"1x {math.ceil(memtotal_gb)} GB"
        
        except subprocess.CalledProcessError as e:
            # Handle errors in the subprocess
            print(f"An error occurred while reading /proc/meminfo: {e.stderr}")
            return None

def update_sut_desc(cpu_entry, device_tool_query, qaic_util_path=None, __entry__=None):

    """
    Update the SUT description file with the cpu and QAIC device information.

    Usage example: 
                axs byquery sut_desc_gen,sut=chai 
    """

    data_dict = {}

    sut_desc_gen_path = __entry__.get_kernel().byname("sut_desc_gen").get_path()
    
    template_description_path = os.path.join(sut_desc_gen_path, "template_desc.json")

    with open(template_description_path, 'r') as f:
        description = json.load(f)
        data_dict.update(description)

        keys_to_update_from_cpu_entry = [ 
            "host_processor_model_name", 
            "host_processor_frequency", 
            "host_processors_per_node", 
            "host_processor_core_count", 
            "host_processor_caches",
            "host_processor_url"
        ]
            
        keys_to_update_from_device_tool_query = [
            "accelerator_memory_capacity",
            "accelerator_on-chip_memories",
            "accelerators_per_node"
        ]
        
        for key in keys_to_update_from_cpu_entry:
            data_dict[key] = cpu_entry.get(key)
            
        if device_tool_query:
            for key in keys_to_update_from_device_tool_query:
                data_dict[key] = device_tool_query.get(key)
            data_dict['accelerator_model_name'] = device_tool_query.get("accelerator_model_name")

        data_dict['operating_system'] = get_lsb_release_output('cat /etc/lsb-release') + " " + "(" + get_uname_output('uname -a') + ")"
        data_dict['other_software_stack'] = get_software_stack()

        #system_info = get_system_info(device_tool_query)
        #data_dict['system_name'] = system_info

        data_dict['host_memory_capacity'] = get_host_memory_capacity()
        data_dict['host_memory_configuration'] = get_host_memory_configuration()

    # Paths for the original and the new file names
    description_path = os.path.join(__entry__.get_path(), "description.json")
    new_file_path = os.path.join(__entry__.get_path(), "description_manual.json")

    if os.path.isfile(description_path) and os.path.isfile(new_file_path) is False:
        # Rename the existing description.json to the description_override.json
        os.rename(description_path, new_file_path)
        # Copy the renamed file back to the original file name
        shutil.copyfile(new_file_path, description_path)
        print(f"Renamed and created a copy of the description file at {__entry__.get_path()}")
    else:
        print("The original file has been alsready renamed or the new file already exists.")

    # Load the system info from description_manual.json
    if os.path.isfile(new_file_path):
        with open(new_file_path, 'r') as file:
            data = json.load(file)
            keys = ['system_type', 'submitter', 'hw_notes', 'status', 'division', 'system_type_detail', 'system_name', 'host_storage_type',
                'host_storage_capacity', 'cooling', 'host_networking', 'host_networking_topology', 'number_of_nodes',
                'host_network_card_count', 'framework', 'accelerator_frequency', 'accelerator_interconnect', 'accelerator_host_interconnect', 'accelerator_memory_configuration']
            if cpu_entry.get('host_processor_frequency') == "Not Provided":
                keys.append('host_processor_frequency')

            data_dict.update({key: data.get(key) for key in keys})

    if os.path.isfile(description_path):
        with open(description_path, 'w') as f:
            json.dump(data_dict, f, indent=4)
            print(f"Updated the description file at {description_path}.")

    return print(f"WARNING: {description_path} doesn't exist. Using the default template at {template_description_path}.")

