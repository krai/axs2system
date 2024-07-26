import re

def parse_lscpu_output(lscpu_output_struct):

    lscpu_output_dict = { p["field"][:-1]: p["data"] for p in lscpu_output_struct }

    return lscpu_output_dict

def update_cpu_model_name(host_processor_model_name):

    # Replace spaces and "@" symbols with underscores
    updated_name = re.sub(r"[@ ]", "_", host_processor_model_name)
    # Replace spaces and "(R)" symbols with underscores
    updated_name = re.sub(r"[(R) ]", "", updated_name)
    # Reduce sequences of multiple underscores to a single underscore
    updated_name = re.sub(r"_{2,}", "_", updated_name)

    return updated_name

def find_url_for_cpu_model(host_processor_model_name, updated_cpu_model_name, cpu_model_names_urls):
  
    parts = updated_cpu_model_name.split('_')
    base_model_name = '_'.join(parts[:3]) if len(parts) >= 3 else updated_cpu_model_name
    AMD_url_prefix = "https://www.amd.com/en/products/cpu/amd-epyc-"

    if base_model_name.startswith("AMD"):
        AMD_model_number = ''.join(parts[2]) # get the model numner from parts list
        return AMD_url_prefix + AMD_model_number
        
    for key in cpu_model_names_urls.keys():
        if key.startswith(base_model_name):
            return cpu_model_names_urls[key]
        
    return "Please search for" + " " + f"cpu model: {host_processor_model_name}" + " " + "on the web, copy and paste the url to data_axs.json file, remove the cpu entry from your work_collection and re-run!"

def get_cpu_speed_info(cpu_min_mhz=None, cpu_max_mhz=None, cpu_mhz=None):
    
    if cpu_min_mhz and cpu_max_mhz:
        host_processor_freq = f"{cpu_min_mhz} MHz (min); {cpu_max_mhz} MHz (boost)"
    elif cpu_mhz:
        host_processor_freq = f"{cpu_mhz} MHz"
    else:
        host_processor_freq = f"Not Provided"

    return host_processor_freq


def join_cpu_hierarchy_info(L1d_cache, L1i_cache, L2_cache, L3_cache):
    levels = [
        f"L1d cache: {L1d_cache}",
        f"L1i cache: {L1i_cache}",
        f"L2 cache: {L2_cache}",
        f"L3 cache: {L3_cache}"
    ]
    cache_info = "; ".join(levels)

    return cache_info
