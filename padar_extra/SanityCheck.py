import yaml
import pandas as pd
import re
import os 
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models import ColumnDataSource
from bokeh.io import show, output_file, reset_output, save
from bokeh import layouts
from bokeh.plotting import figure
from bokeh.models import DatetimeTickFormatter, DateFormatter
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.tools import HoverTool
import math
import sys
import datetime as dt
import numpy as np
import copy
import re
from dateutil.parser import parse
from bokeh.models.widgets import Paragraph

def sanity_check(root_path, config_path):
    root_path = os.path.realpath(root_path)
    config = dict()
    with open(config_path, 'r') as file:
        config = yaml.load(file)
    
    if config['pid'] is None:
        config['pid'] = [name for name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, name))]
    
    if 'sensor_locations' not in config:
        config['sensor_locations'] = None
    
    if 'check_episode_duration' not in config:
        config['check_episode_duration'] = None
        
    if 'check_episode_time' not in config:
        config['check_episode_time'] = None

    config = __specify_config(config)

    to_check_missing_file = any([x['check_missing_file'] for x in config])
    to_check_sampling_rate = any([x['check_sampling_rate'] for x in config])
    to_check_annotation = any([x['check_annotation'] for x in config])

    # create the report elements according to configuration
    total_report_elements = []
    pid_report_elements = dict()
    
    total_report_elements.append(Paragraph(text='Missing File List', style={'color':'blue'}))
    if to_check_missing_file:
        missing_file, missing_file_table_pid = check_missing_file(root_path, config)
        for pid in missing_file_table_pid:
            if pid not in pid_report_elements:
                pid_report_elements[pid] = []
            pid_report_elements[pid].append(missing_file_table_pid[pid])
        total_report_elements.append(missing_file)
    
    total_report_elements.append(Paragraph(text='Sensor File Exceptions', style={'color':'blue'}))
    if to_check_sampling_rate:
        abnormal_rate, sensor_tables = check_sampling_rate(root_path, config)
        for pid in sensor_tables:
            if pid not in pid_report_elements:
                pid_report_elements[pid] = []
            pid_report_elements[pid].append(sensor_tables[pid])
        total_report_elements.append(abnormal_rate)
    
    total_report_elements.append(Paragraph(text='Annotation Reports and Exceptions', style={'color':'blue'}))
    if to_check_annotation:
        total_annotation_graphs, histogram_by_day = check_annotation(root_path, config)
        for pid in histogram_by_day:
            if pid not in pid_report_elements:
                pid_report_elements[pid] = []
            pid_report_elements[pid].append(histogram_by_day[pid])
        total_report_elements += total_annotation_graphs

    __write_report(root_path, total_report_elements)
    for pid in pid_report_elements:
        __write_report(os.path.join(root_path, pid, 'Derived'), pid_report_elements[pid])
    
     
def __write_report(root_path, element_list):
    reset_output()
    output_file(os.path.join(root_path,'report.html') , mode='inline')
    #output_file("report.html")
    report = layouts.column(element_list)
    save(report)
        

def check_missing_file(root_path, config):
    
    # if not __validate_config_missing_file(config):
    #     raise Exception('Invalid Configuration')

    missing_file = pd.DataFrame(columns=['PID', 'FileType', 'FilePath', 'Note'])
    
    for check in config:
        if check['check_missing_file']:
            missing_file = missing_file.append(__check_meta_data(root_path, check['pid'], check['num_sensor'], check['sensor_locations']))
            missing_file = missing_file.append(__check_hourly_data(root_path, check['pid'], 
                                                                check['check_annotation_file'], check['check_event'], 
                                                                check['check_EMA'], check['check_GPS'], 
                                                                check['num_sensor'], check['num_annotator']))
        
    pid_grouped = missing_file.groupby('PID')
    missing_file_table_pid = dict()

    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','missing_files.csv'))
        missing_file_table_pid[pid] = __graph_table(data)
        
    return __graph_table(missing_file), missing_file_table_pid
    

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
                    temp_dict.update(copy.deepcopy(specification))
                    break
        
        new_config.append(temp_dict)
    
    return new_config
        

def __validate_config_missing_file(config):
    valid =  all(all(x in y.keys() for x in ['pid','check_annotation_file', 
               'check_event','check_EMA','check_GPS','num_annotator','num_sensor', 'sensor_locations']) for y in config)
    
    for check in config:
        if check['sensor_locations'] is not None:
            valid = valid and len(check['sensor_locations']) == check['num_sensor']
        
    return valid

    
def __check_meta_data(root_path, pid, num_sensor, sensor_locations):
    print('CHECKING META DATA FILE', pid)
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
                

def __check_hourly_data(root_path, pid, check_annotation_file, check_event, check_EMA, check_GPS, num_sensor, num_annotator):
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
        print('CHECKING HOURLY DATA FILE', pid, time)
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
        
        if check_annotation_file:
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
        
    
def __graph_table(table):
    source = ColumnDataSource(table)
    columns = []
    for name in table.columns.values:
        if pd.core.dtypes.common.is_datetime_or_timedelta_dtype(table[name]):
            columns.append(TableColumn(field=name, title=name, formatter=DateFormatter(format='%T')))
        else:
            columns.append(TableColumn(field=name, title=name))
    
    columns[-1].width = 1000
    data_table = DataTable(source=source, columns=columns, width=1000, height=280,
                           fit_columns=True)

    return layouts.widgetbox(data_table)
    

def check_sampling_rate(root_path, config):
    abnormal_rate = pd.DataFrame(columns = ['PID','TimePeriod', 'SamplingRate', 'FilePath'])
    
    for check in config:
        if check['check_sampling_rate']:
            abnormal_rate = abnormal_rate.append(__parse_sampling_rate(check['pid'], check['claimed_rate'], check['accept_range'], root_path))
        
    abnormal_rate.to_csv(os.path.join(root_path, 'sensor_exceptions.csv'))
    sensor_tables = dict()

    pid_grouped = abnormal_rate.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','sensor_exceptions.csv'))
        sensor_tables[pid] = __graph_table(data)
        
    return __graph_table(abnormal_rate), sensor_tables


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


def check_annotation(root_path, config):
    annotation_exceptions = pd.DataFrame(columns=['PID','ANNOTATOR','START_TIME','STOP_TIME','LABEL_NAME','ISSUE'])
    
    histogram_by_day = dict()
    
    for check in config:
        if check['check_annotation']:
            new_exceptions, figures = __parse_annotation(check['pid'], check['lower_bound'], check['upper_bound'], 
                                                         check['check_episode_duration'], 
                                                         check['check_episode_time'],
                                                         root_path)
            annotation_exceptions = annotation_exceptions.append(new_exceptions)
            histogram_by_day[check['pid']] = figures

    annotation_exceptions.to_csv(os.path.join(root_path, 'annotation_exceptions.csv'))
    
    pid_grouped = annotation_exceptions.groupby('PID')
    for pid, data in pid_grouped:  
        data.to_csv(os.path.join(root_path,pid,'Derived','annotation_exceptions.csv'))
    
    histogram_tabs = []
    for pid, graphs in histogram_by_day.items():
        histogram_tabs.append(Panel(child=layouts.column(*graphs[0:-1]), title=pid))
        histogram_by_day[pid] = layouts.column(*graphs)

    total_annotation_graphs = []
    total_annotation_graphs.append(layouts.widgetbox(Tabs(tabs=histogram_tabs)))
    total_annotation_graphs.append(__graph_table(annotation_exceptions))
    # return the elements need to included in the report
    return total_annotation_graphs, histogram_by_day


def __parse_annotation(pid, lower_bound, upper_bound, check_episode_duration, check_episode_time, root_path):
    print('CHECKING ANNOTATION', pid)
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
    histogram_list = []
    episode_table_list = []

    for annotator, annotation_table in all_annotation_table.items():
        
        # check if the duration of annotations within specified length
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
            
            if check_episode_duration is not None:
                annotation_exceptions = annotation_exceptions.append(__check_episode_duration(series, 
                                                                                              check_episode_duration, pid, annotator),
                                                                    ignore_index = True)
            if check_episode_time is not None:
                annotation_exceptions = annotation_exceptions.append(__check_episode_time(series, 
                                                                                              check_episode_time, pid, annotator),
                                                                    ignore_index = True)
                
          
        # create annotation table by pid
        annotation_table['DURATION'] = annotation_table.iloc[:,2] - annotation_table.iloc[:,1]
        annotation_table['DAY'] = annotation_table.iloc[:,1].dt.day
        group_by_activity = annotation_table.iloc[:,[3,-1,-2]].groupby(by='DAY')

        # create graphs by day
        
        histogram_graph_list = []
        episode_graph_list = []
        
        for day, data in group_by_activity:
            # create histogram of duration per activity by day
            
            group_by_duration= data.iloc[:,[0,2]].groupby('LABEL_NAME').sum()
            group_by_duration = group_by_duration.sort_values('DURATION', ascending=False)
            source = ColumnDataSource(data=dict(activity=group_by_duration.index.values, 
                                                duration=group_by_duration.iloc[:,0],
                                                time=group_by_duration.iloc[:,0].apply(__format_time_delta)))
            p = figure(x_range=group_by_duration.index.values, plot_height=350,
                       plot_width = 500,
                       toolbar_location=None,
                       tooltips=[('activity','@activity'),
                                  ('duration','@time')])

            p.vbar(x='activity', top='duration', width=0.9, source=source)
            # TODO: solve the problem of multiple annotator here
            histogram_graph_list.append(Panel(child=p, title=pid + ": day "+str(day)))
            p.yaxis.formatter=DatetimeTickFormatter(
                hours = ['%Hh', '%Hh:%Mm'],
                minutes = ['%Mm'],
                minsec = ['%Mm:%Ss']

            )
            p.xaxis.major_label_orientation = 1.2
            
            # compute episodes statistics: episodes count, duration mean, duration std by day
            
            stats_table = pd.DataFrame(columns=['Activity','Count','DurationMean','DurationStd'])
            
            for activity in group_by_duration.index.values:
                stats_table = stats_table.append(pd.Series({'Activity': activity,
                                              'Count': data[data['LABEL_NAME'] == activity].shape[0],
                                              'DurationMean': np.mean(data[data['LABEL_NAME'] == activity]['DURATION']),
                                              'DurationStd': np.std(data[data['LABEL_NAME'] == activity]['DURATION'])
                                                  }),
                                    ignore_index=True)
            episode_graph_list.append(Panel(child=__graph_table(stats_table), title=pid + ": day "+str(day)))
            
    
        histogram_list.append(layouts.widgetbox(Tabs(tabs=histogram_graph_list), width=500))
        episode_table_list.append(layouts.widgetbox(Tabs(tabs=episode_graph_list), width=500))
        
        
        
    table_graph = __graph_table(annotation_exceptions)

    return annotation_exceptions, [*histogram_list, *episode_table_list,table_graph]


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


def __check_episode_duration(series, episode_duration_limits, pid, annotator):
    """
    Check the episode duration by activity time
    """
    
    if series[3].lower() in episode_duration_limits:
        duration = series[2] - series[1]
        limits = episode_duration_limits[series[3].lower()]
        if not isinstance(limits, list):
            limits = [limits]
            
        for time_limit in limits:
            if '>' in time_limit:
                time_token = pd.Timedelta(re.findall('>(.*)', time_limit)[0])
                if duration > time_token:
                    return pd.Series({'PID':pid,
                                      'ANNOTATOR': annotator,
                                      'START_TIME':series[1],
                                      'STOP_TIME': series[2],
                                      'LABEL_NAME': series[3],
                                      'ISSUE': 'Activity {} beyond specified limit {}, duration: {}'.format(
                                              series[3], __format_time_delta(time_token), duration)})
            elif '<' in time_limit:
                time_token = pd.Timedelta(re.findall('<(.*)', time_limit)[0])
                if duration < time_token:
                    return pd.Series({'PID':pid,
                                      'ANNOTATOR': annotator,
                                      'START_TIME':series[1],
                                      'STOP_TIME': series[2],
                                      'LABEL_NAME': series[3],
                                      'ISSUE': 'Activity {} below specified limit {}, duration: {}'.format(
                                              series[3], __format_time_delta(time_token), duration)})    
    return None


def __format_time_delta(s):
    return  '{:02}:{:02}:{:02}'.format(int(s.total_seconds()) // 3600, int(s.total_seconds()) % 3600 // 60, int(s.total_seconds()) % 60)


def __check_episode_time(series, episode_time_limits, pid, annotator):
    """
    Check if the episode happened in specified abnormal period of time
    """
    
    if series[3].lower() in episode_time_limits:
        limits = episode_time_limits[series[3].lower()]
        lower_bound = parse(limits[0]).time()
        upper_bound = parse(limits[1]).time()
        start_time = pd.to_datetime(series[1]).time()
        stop_time = pd.to_datetime(series[2]).time()
        if stop_time > lower_bound and start_time < upper_bound:
            return pd.Series({'PID':pid,
                              'ANNOTATOR': annotator,
                              'START_TIME': series[1],
                              'STOP_TIME': series[2],
                              'LABEL_NAME': series[3],
                              'ISSUE': 'Activity {} in specified abnormal period of time: {} to {}'.format(
                                      series[3], lower_bound, upper_bound)})
            
        
if __name__ == '__main__':
    sanity_check("/Users/zhangzhanming/Desktop/mHealth/Data/SPADES_2day", "/Users/zhangzhanming/Desktop/mHealth/Test/sanitycheck/config.txt")
    if len(sys.argv) != 3:
        print('INSTRUCTION: [root_path] [config_path]')
    else:
        sanity_check(sys.argv[1], sys.argv[2])
        
        
        
