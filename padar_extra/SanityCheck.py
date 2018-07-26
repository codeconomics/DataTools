import yaml
import pandas as pd
import re
import os 
import bokeh


def sanity_check(root_path, config_path):
    config = ''
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    if not __validate_config(config):
        raise Exception('Invalid Configuration')
    
    if root_path[-1] != '/':
        root_path += '/'
        
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    
    for check in config:
        missing_file = missing_file.append(__check_meta_data(root_path, check['pid'], check['num_sensor']))
        missing_file = missing_file.append(__check_hourly_data(root_path, check['pid'], 
                                                               check['check_annotation'], check['check_event'], 
                                                               check['check_EMA'], check['check_GPS'], 
                                                               check['num_sensor'], check['num_annotator']))
        
    pd.to_csv(missing_file, root_path+'/Derived/SanityCheck.csv')
    

def __validate_config(config):
    return all(all(x in y.keys() for x in ['pid','check_annotation', 
               'check_event','check_EMA','check_GPS','num_annotator','num_sensor']) for y in config)

    
def __check_meta_data(root_path, pid, num_sensor):
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    target_path = root_path +pid+'/Derived/'
    required_file_name_list = ['location_mapping.csv', 'subject.csv', 'sessions.csv']
    for required_file in required_file_name_list:
        not_there = True
        for existed_file in os.listdir(target_path):
            if re.findall(required_file, existed_file):
                not_there = False

                if required_file == 'location_mapping.csv':
                    location_mapping = pd.read_csv(target_path + existed_file)
                    # TODO: how to count sensors
                    # TODO: find missing location
                break
        
        if not_there:
            missing_file = missing_file.append({'PID': pid,
                                                'FileType': required_file,
                                                'FilePath': target_path,
                                                'Note': ''},
                                                ignore_index=True)    
    return missing_file
                

def __check_hourly_data(root_path, pid, check_annotation, check_event, check_EMA, check_GPS, num_sensor, num_annotator):
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    # traverse the directory tree to find the start time and end time
    hourly_path = []
    for path, dirs, files in os.walk(root_path + pid + '/MasterSynced/'):
        finds = re.findall('MasterSynced/(\d{4}/\d{2}/\d{2}/\d{2})', path)
        if finds:
            hourly_path += finds
    start_time = hourly_path[0]
    end_time = hourly_path[-1]
    
    expected_range = list(pd.date_range(start_time, end_time, freq='H').strftime('%Y/%m/%d/%H'))
    for file_name in expected_range:
        if file_name not in hourly_path:
            missing_file = missing_file.append({'PID':pid,
                                 'FileType': 'directory',
                                 'FilePath': root_path + pid + '/MasterSynced/',
                                 'Note': 'No directory for the time ' + file_name},
                                ignore_index=True)
    
    for time in hourly_path:
        print(time)
        target_path = root_path + pid + '/MasterSynced/'+ time
        files = os.listdir(target_path)
        
        sensor_count = 0
        for file_name in files:
            if re.findall('.sensor.csv', file_name):
                sensor_count += 1
        
        if sensor_count < num_sensor:
            missing_file = missing_file.append({'PID': pid,
                                        'FileType': 'sensor',
                                        'FilePath': target_path,
                                        'Note': '{} sensor files missing in {}'.format(
                                                num_sensor-sensor_count,
                                                time) 
                                    },
                                    ignore_index=True)
        
        if check_annotation:
            annotation_count = 0
            for file_name in files:
                if re.findall('.annotation.csv', file_name):
                    annotation_count += 1
                    
            if annotation_count < num_annotator:
                missing_file = missing_file.append({'PID': pid,
                                            'FileType': 'annotation',
                                            'FilePath': target_path,
                                            'Note': '{} annotation files missing in {}'.format(
                                                    num_annotator-annotation_count,
                                                    time) 
                                        },
                                        ignore_index=True)
        
        if check_event:
            if all(not re.findall('.event.csv', file_name) for file_name in files):
                missing_file = missing_file.append({'PID':pid,
                     'FileType': 'event',
                     'FilePath': target_path,
                     'Note': ''},
                    ignore_index=True) 
         
        #TODO: How to check EMA?
        if check_EMA:
            if all(not re.findall('.EMA.csv', file_name) for file_name in files):
                missing_file = missing_file.append({'PID':pid,
                     'FileType': 'EMA',
                     'FilePath': target_path,
                     'Note': ''},
                    ignore_index=True)
                
        #TODO: How to check GPS?
        if check_GPS:
            if all(not re.findall('.GPS.csv', file_name) for file_name in files):
                missing_file = missing_file.append({'PID':pid,
                     'FileType': 'GPS',
                     'FilePath': target_path,
                     'Note': ''},
                    ignore_index=True)
        
        
    
    
    
    


