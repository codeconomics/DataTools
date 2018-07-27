import yaml
import pandas as pd
import re
import os 
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
from bokeh.io import show, output_file, reset_output
from bokeh.layouts import widgetbox
import sys


def sanity_check(root_path, config_path):
    config = ''
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    config = __specify_config(config)
    
    if not __validate_config(config):
        raise Exception('Invalid Configuration')
    
    if root_path[-1] != '/':
        root_path += '/'
        
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    
    for check in config:
        missing_file = missing_file.append(__check_meta_data(root_path, check['pid'], check['num_sensor'], check['sensor_locations']))
        missing_file = missing_file.append(__check_hourly_data(root_path, check['pid'], 
                                                               check['check_annotation'], check['check_event'], 
                                                               check['check_EMA'], check['check_GPS'], 
                                                               check['num_sensor'], check['num_annotator']))
    
    pid_grouped = missing_file.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(root_path+pid+'/Derived/SanityCheck.csv')
        __graph_report(root_path + pid + '/Derived/', data)
        
    __graph_report(root_path, missing_file)
    

def __specify_config(config):
    new_config = []
    if 'sensor_locations' not in config:
        config['sensor_locations'] = None
    keys = list(config.keys())

    if 'specification' in keys:
        keys.remove('specification')
    keys.remove('pid')
    pid_list = config['pid']
    
    # populate a list of different pids
    for pid in pid_list:
        temp_dict = {}
        temp_dict['pid'] = pid
        for key in keys:
            temp_dict[key] = config[key]
        
        if 'specification' in config:
            for specification in config['specification']:
                if specification['pid'] == pid:
                    temp_dict.update(specification)
                    break
        
        new_config.append(temp_dict)
    
    return new_config
        
            
    
    
    


def __validate_config(config):
    valid =  all(all(x in y.keys() for x in ['pid','check_annotation', 
               'check_event','check_EMA','check_GPS','num_annotator','num_sensor', 'sensor_locations']) for y in config)
    
    for check in config:
        if check['sensor_locations'] is not None:
            valid = valid and len(check['sensor_locations']) == check['num_sensor']
        
    return valid

    
def __check_meta_data(root_path, pid, num_sensor, sensor_locations):
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
                    if sensor_locations is None:
                        if num_sensor != location_mapping.shape[0]:
                            missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': target_path + required_file,
                                                'Note': '{} sensors missing in location mapping'.format(num_sensor - location_mapping.shape[0])},
                                                ignore_index=True)
                    else:
                        existed_location = list(location_mapping.iloc[:,2].values)
                        for location in sensor_locations:
                            if location not in existed_location:
                                missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': target_path + required_file,
                                                'Note': location + ' missing in location mapping'},
                                                ignore_index=True)
                            
                break
        
        if not_there:
            missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': target_path + required_file,
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
    
    return missing_file
        
        
def __graph_report(root_path, missing_file):
    reset_output()
    output_file(root_path + 'report.html' , mode='absolute')
    #output_file("report.html")
    
    source = ColumnDataSource(missing_file)
    
    columns = [TableColumn(field=name, title=name) for name in missing_file.columns.values]
    
    data_table = DataTable(source=source, columns=columns, width=1000, height=280,
                           fit_columns=True)

    show(widgetbox(data_table))
    

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('INSTRUCTION: [root_path] [config_path]')
    else:
        sanity_chec(sys.argv[1], sys.argv[2])




