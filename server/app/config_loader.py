import os, yaml

def load_configs(config_dir="configs"):
    configs = {}
    # Loop through each file in the directory
    for filename in os.listdir(config_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            file_path = os.path.join(config_dir, filename)
            with open(file_path, 'r') as file:
                try:
                    # Load the YAML file and store it in the dictionary
                    configs[filename] = yaml.safe_load(file)
                except yaml.YAMLError as e:
                    print(f"Error loading {filename}: {e}")
    return configs
