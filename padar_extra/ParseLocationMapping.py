import os
import sys
from glob import glob
import pandas as pd
from itertools import islice
import re
import yaml


def parse_location_mapping(root_path, config_path):
    root_path = os.path.realpath(root_path)
    config = []
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    if config['pid'] is None:
        config['pid'] = [name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name))]
 
    for pid in config['pid']:
        __parse(pid, root_path)

def __parse(pid, root_path):
    original_raws = glob(os.path.join(root_path, pid, 'OriginalRaw', '*.csv'))
    results = []
    for filepath in original_raws:
        filepath = os.path.abspath(filepath)
        print("parse location from " + filepath)
        # tokens = os.path.basename(filepath).split(' ')[0].split('_')
        # loc = list(filter(lambda token: 'Left' in token or 'Right' in token, tokens))[0]
        loc = re.search('_((DominantAnkle)|(DominantThigh)|(DominantWaist)|(Wrist_NonDominant)) ',
            os.path.basename(filepath), re.IGNORECASE).group(1)
        with open(filepath, 'r') as f:
            headers = list(islice(f, 2))
            matches = re.search('Serial Number: ([A-Z0-9]+)', headers[1])
            sn = matches.group(1)
        result = pd.DataFrame(data={'PID': [pid], 'SENSOR_ID': [sn], 'LOCATION': [loc]})
        result = result[['PID', 'SENSOR_ID', 'LOCATION']]
        results.append(result)  
        result = pd.concat(results)
        result.reset_index(drop=True, inplace=True)
        output_path = os.path.join(root_path, pid, 'Derived', 'location_mapping.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.to_csv(output_path, index=False)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('INSTRUCTION: [root_path] [config_path]')
    else:
        parse_location_mapping(sys.argv[1], sys.argv[2])