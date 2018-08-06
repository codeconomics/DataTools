import yaml
import pandas as pd
import re
import os 
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
from bokeh.io import show, output_file, reset_output, save
from bokeh.layouts import widgetbox
import sys
#import click

#@click.command()
def check_missing_file(root_path, config_path):
    config = ''
    with open(config_path, 'r') as file:
        config = yaml.load(file)
        
    if config['pid'] is None:
        config['pid'] = [name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name))]

    if 'sensor_locations' not in config:
        config['sensor_locations'] = None

    config = __specify_config(config)
    
    if not __validate_config_missing_file(config):
        raise Exception('Invalid Configuration')

    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    
    for check in config:
        missing_file = missing_file.append(__check_meta_data(root_path, check['pid'], check['num_sensor'], check['sensor_locations']))
        missing_file = missing_file.append(__check_hourly_data(root_path, check['pid'], 
                                                               check['check_annotation'], check['check_event'], 
                                                               check['check_EMA'], check['check_GPS'], 
                                                               check['num_sensor'], check['num_annotator']))
    
    pid_grouped = missing_file.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','missing_files.csv'))
        __graph_report(os.path.join(root_path, pid, 'Derived'), data)
        
    __graph_report(root_path, missing_file)
    

def __specify_config(config):
    new_config = []
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
        

def __validate_config_missing_file(config):
    valid =  all(all(x in y.keys() for x in ['pid','check_annotation', 
               'check_event','check_EMA','check_GPS','num_annotator','num_sensor', 'sensor_locations']) for y in config)
    
    for check in config:
        if check['sensor_locations'] is not None:
            valid = valid and len(check['sensor_locations']) == check['num_sensor']
        
    return valid

    
def __check_meta_data(root_path, pid, num_sensor, sensor_locations):
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    target_path = os.path.join(root_path, pid, 'Derived')
    if not os.path.isdir(target_path):
        os.mkdir(target_path)
            
    required_file_name_list = ['location_mapping.csv', 'subject.csv', 'sessions.csv']
    for required_file in required_file_name_list:
        not_there = True
        for existed_file in os.listdir(target_path):
            if re.findall(required_file, existed_file):
                not_there = False

                if required_file == 'location_mapping.csv':
                    location_mapping = pd.read_csv(os.path.join(target_path, existed_file))
                    if sensor_locations is None:
                        if num_sensor != location_mapping.shape[0]:
                            missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': os.path.join(target_path, required_file),
                                                'Note': '{} sensors missing in location mapping'.format(num_sensor - location_mapping.shape[0])},
                                                ignore_index=True)
                    else:
                        existed_location = list(location_mapping.iloc[:,2].values)
                        for location in sensor_locations:
                            if location not in existed_location:
                                missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': os.path.join(target_path, required_file),
                                                'Note': location + ' missing in location mapping'},
                                                ignore_index=True)
                            
                break
        
        if not_there:
            missing_file = missing_file.append({'PID': pid,
                                                'FileType': 'meta',
                                                'FilePath': os.path.join(target_path, required_file),
                                                'Note': ''},
                                                ignore_index=True)    
    return missing_file
                

def __check_hourly_data(root_path, pid, check_annotation, check_event, check_EMA, check_GPS, num_sensor, num_annotator):
    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    # traverse the directory tree to find the start time and end time
    hourly_path = __get_hourly_path(root_path, pid)
    start_time = hourly_path[0]
    end_time = hourly_path[-1]
    
    expected_range = list(pd.date_range(start_time, end_time, freq='H').strftime('%Y-%m-%d-%H'))
    for file_name in expected_range:
        if file_name not in hourly_path:
            missing_file = missing_file.append({'PID':pid,
                                 'FileType': 'directory',
                                 'FilePath': os.path.join(root_path, pid, 'MasterSynced'),
                                 'Note': 'No directory for the time ' + file_name},
                                ignore_index=True)
    
    for time in hourly_path:
        time_path = os.path.join(*time.split('-'))
        target_path = os.path.join(root_path, pid, 'MasterSynced', time_path)
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
    output_file(os.path.join(root_path,'report.html') , mode='inline')
    #output_file("report.html")
    
    source = ColumnDataSource(missing_file)
    
    columns = [TableColumn(field=name, title=name) for name in missing_file.columns.values]
    
    data_table = DataTable(source=source, columns=columns, width=1000, height=280,
                           fit_columns=True)

    save(widgetbox(data_table))
    

def check_sampling_rate(root_path, config_path):
    root_path = os.path.realpath(root_path)
    config = []
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    if config['pid'] is None:
        config['pid'] = [name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name))]
    
    config = __specify_config(config)
    abnormal_rate = pd.DataFrame(columns = ['PID','TimePeriod', 'SamplingRate', 'FilePath'])
    
    for check in config:
        abnormal_rate = abnormal_rate.append(__parse_sampling_rate(check['pid'], check['claimed_rate'], check['accept_range'], root_path))
        
    abnormal_rate.to_csv(os.path.join(root_path, 'sensor_exceptions.csv'))
    
    pid_grouped = abnormal_rate.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','sensor_exceptions.csv'))


def __parse_sampling_rate(pid, claim_rate, accept_range, root_path):
    abnormal_rate = pd.DataFrame(columns = ['PID','TimePeriod', 'SamplingRate', 'FilePath'])
    hourly_path = __get_hourly_path(root_path, pid)

    for time in hourly_path:
        time_path = os.path.join(*time.split('-'))
        target_path = os.path.join(root_path, pid, 'MasterSynced', time_path)
        files = list(os.listdir(target_path))
        files = list(filter(lambda x: re.findall('.sensor.csv', x), files))
        
        for sensor_file in files:
            print('CHECKING SAMPLING RATE ', pid, sensor_file)
            sensor_data = pd.read_csv(os.path.join(target_path, sensor_file))
            sensor_data.iloc[:,0] = pd.to_datetime(sensor_data.iloc[:,0])
            groups = sensor_data.iloc[:,[0,1]].groupby(pd.Grouper(key=sensor_data.columns[0], freq = '1min')).count()
            normalrate = 60*claim_rate
            for index, count in groups.iterrows():
                if count[0] <= normalrate*(1-accept_range) or count[0] >= normalrate*(1+accept_range):
                    abnormal_rate = abnormal_rate.append({'PID' : pid,
                                                          'TimePeriod': index,
                                                          'SamplingRate': count[0],
                                                          'FilePath': os.path.join(target_path, sensor_file)},
                                        ignore_index=True)
    return abnormal_rate
            

def __get_hourly_path(root_path, pid):
    hourly_path = []
    for path, dirs, files in os.walk(os.path.join(root_path, pid, 'MasterSynced')):
        finds = re.findall('MasterSynced[/\\\\](\d{4})[/\\\\](\d{2})[/\\\\](\d{2})[/\\\\](\d{2})', path)
        if finds:
            hourly_path.append('-'.join(finds[0]))
    return hourly_path


def check_annotation(root_path, config_path):
    root_path = os.path.realpath(root_path)
    config = []
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    if config['pid'] is None:
        config['pid'] = [name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name))]
    
    config = __specify_config(config)
    annotation_exceptions = pd.DataFrame(columns=['PID','ANNOTATOR','START_TIME','STOP_TIME','LABEL_NAME','ISSUE'])

    for check in config:
        annotation_exceptions = annotation_exceptions.append(__parse_annotation(check['pid'], check['lower_bound'], check['upper_bound'], root_path))

    annotation_exceptions.to_csv(os.path.join(root_path, 'annotation_exceptions.csv'))
    
    pid_grouped = annotation_exceptions.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','annotation_exceptions.csv'))

def __parse_annotation(pid, lower_bound, upper_bound, root_path):
    annotation_exceptions = pd.DataFrame(columns=['PID','ANNOTATOR','START_TIME','STOP_TIME','LABEL_NAME','ISSUE'])
    hourly_path = __get_hourly_path(root_path, pid)
    all_annotation_files = {}

    for time in hourly_path:
        time_path = os.path.join(*time.split('-'))
        target_path = os.path.join(root_path, pid, 'MasterSynced', time_path)
        files = list(os.listdir(target_path))
        files = list(filter(lambda x: re.findall('.annotation.csv', x), files))
        for file_path in files:
            file_id = re.findall('(.*)\\.\d{4}-\d{2}-\d{2}', file_path)
            if len(file_id) != 1:
                raise Exception('Failed to parse annotation file name:', file_path) 
            else:
                file_id = file_id[0]
            if file_id in all_annotation_files:
                all_annotation_files[file_id].append(os.path.join(target_path, file_path))
            else:
                all_annotation_files[file_id] = [os.path.join(target_path, file_path)]

    all_annotation_table = __combine_annotation(all_annotation_files)
    
    lower_bound = pd.Timedelta(lower_bound)
    upper_bound = pd.Timedelta(upper_bound)
    
    # check the length of annotations
    for annotator, annotation_table in all_annotation_table.items():
        annotation_table.iloc[:,1] = pd.to_datetime(annotation_table.iloc[:,1])
        annotation_table.iloc[:,2] = pd.to_datetime(annotation_table.iloc[:,2])
        for index, series in annotation_table.iterrows():
            start_time = series[1]
            stop_time = series[2]
            if stop_time - start_time < lower_bound:
                annotation_exceptions = annotation_exceptions.append({'PID': pid,
                                              'ANNOTATOR': annotator,
                                              'START_TIME': start_time,
                                              'STOP_TIME': stop_time,
                                              'LABEL_NAME': series[3],
                                              'ISSUE': 'Too short, duration: {}'.format(stop_time - start_time),
                                              },
                                             ignore_index = True)
                
            if stop_time - start_time > upper_bound:
                annotation_exceptions = annotation_exceptions.append({'PID': pid,
                                              'ANNOTATOR': annotator,
                                              'START_TIME': start_time,
                                              'STOP_TIME': stop_time,
                                              'LABEL_NAME': series[3],
                                              'ISSUE': 'Too long, duration: {}'.format(stop_time - start_time),
                                              },
                                             ignore_index = True)   
                
        # create histogram of activities by pid
        annotation_table['DURATION'] = annotation_table.iloc[:,2] - annotation_table.iloc[:,1]
        annotation_table['DAY'] = annotation_table.iloc[:,1].dt.day
        group_by_activity = annotation_table.iloc[:,[3,-1,-2]].groupby(by=['DAY','LABEL_NAME']).sum()
        
        """
        TODO: Create Histogram Here
        """
            
    
    return annotation_exceptions


def __combine_annotation(all_annotation_files):
    all_annotation_table = {}
    for key, value in all_annotation_files.items():
        all_annotation = []
        for file_path in value:
            annotation_table = pd.read_csv(file_path)
            for index, series in annotation_table.iterrows():
                if len(all_annotation) > 0 and all_annotation[-1].iloc[3] == series.iloc[3]:
                    if all_annotation[-1].iloc[2] == series.iloc[1] or ((pd.to_datetime(all_annotation[-1].iloc[2]) + dt.timedelta(seconds=1)).hour == pd.to_datetime(series.iloc[1]).hour
                                     and pd.to_datetime(series.iloc[1]).second == 0 and pd.to_datetime(series.iloc[1]).minute == 0):
                        #print('Concatenate activity', all_annotation[-1].iloc[1:4], series.iloc[1:4])
                        all_annotation[-1].iloc[2] = series.iloc[2]
                else:
                    all_annotation.append(series)

        all_annotation = pd.DataFrame(all_annotation)
        all_annotation_table[key] = all_annotation
    
    return all_annotation_table
                    

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('INSTRUCTION: MISSING_FILE/SAMPLING_RATE [root_path] [config_path]')
    else:
        if sys.argv[1] == 'MISING_FILE':
            check_missing_file(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == 'SAMPLING_RATE':
            check_sampling_rate(sys.argv[2], sys.argv[3])
        else:
            print('wrong command')