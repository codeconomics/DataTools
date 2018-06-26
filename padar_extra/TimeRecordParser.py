import pandas as pd
import numpy as np
import sys
import re
from datetime import timedelta


def parse(path_in, path_out, split, categorize, annotatoinset, annotator_set_id):
    recordlist = []
    parsed_data = pd.DataFrame(columns=['HEADER_TIME_STAMP','START_TIME',
                                        'STOP_TIME','LABEL_NAME','LABEL_ID',
                                        'RATING_TIME_STAMP','RATING_INTENSITY',
                                        'RATING_CONFIDENCE'])
    parsed_recordlist = []
    with open(path_in,'r') as file_in:
        for line in file_in:
            line = line.strip()
            time = line[line.find('[')+1: line.find(']')]
            tokens = line[line.find(']')+1:].strip().split(' ', 1)
            action = tokens[0]
            if action.startswith('s'):
                if len(tokens) <2:
                    raise ValueError('Incorrect Start Time: '+ line)
                activities = tokens[1].split(',')
                activities = standardize_label(activities)
                if categorize:
                    activities = categorize_label(activities)
                # if there is already activities in the list, add end time and add them to dataframe
                if len(recordlist)!=0:
                    while len(recordlist)>0:
                        record = recordlist.pop()
                        record['STOP_TIME'] = time
                        parsed_recordlist.append(record)
                for activity in activities:
                    recordlist.append(pd.Series([time, time, activity.strip(), np.nan],
                                      index=['HEADER_TIME_STAMP','START_TIME','LABEL_NAME','STOP_TIME']))
            elif action.startswith('e'):
                while len(recordlist)>0:
                    record = recordlist.pop()
                    record['STOP_TIME'] = time
                    parsed_recordlist.append(record)
            else:
                print('Incorrect Record: '+ line)

    if split:
        parsed_recordlist = split_by_hour(parsed_recordlist)

    parsed_data = pd.DataFrame(parsed_recordlist)
    parsed_data = parsed_data.reindex(columns = ['HEADER_TIME_STAMP','START_TIME',
                                        'STOP_TIME','LABEL_NAME','LABEL_ID',
                                        'RATING_TIME_STAMP','RATING_INTENSITY',
                                        'RATING_CONFIDENCE'])
                                        
    parsed_data['HEADER_TIME_STAMP'] = pd.to_datetime(parsed_data['HEADER_TIME_STAMP']).apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    parsed_data['START_TIME'] = pd.to_datetime(parsed_data['START_TIME']).apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    parsed_data['STOP_TIME'] = pd.to_datetime(parsed_data['STOP_TIME']).apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

    write_to_file(parsed_data, split, path_out, annotatoinset, annotator_set_id)

def standardize_label(activities):
    standardized_activities = []
    for activity in activities:

        activity = activity.lower()

        if 'walk' in activity:
            standardized_activities.append('walk')
            continue
        if 'sit' in activity:
            standardized_activities.append('sit')
            continue
        if 'typ' in activity:
            standardized_activities.append('type')
            continue
        if 'run' in activity:
            standardized_activities.append('run')
            continue
        if 'stand' in activity:
            standardized_activities.append('stand')
            continue
        if re.findall('us.*computer',activity):
            standardized_activities.append('use_computer')
            continue
        if re.findall('in\s*door',activity):
            standardized_activities.append('indoor')
            continue
        if re.findall('out',activity):
            standardized_activities.append('outdoor')
            continue
        standardized_activities.append(activity)
    return standardized_activities

def categorize_label(activities):
    categorized_activities = []
    for activity in activities:
        if 'walk' in activity:
            categorized_activities.append('Ambulation')
            continue
        elif 'sit' in activity or re.findall('us.*computer',activity):
            categorized_activities.append('Sedentary')
            continue
        elif 'typ' in activity:
            categorized_activities.append('Sedentary')
            continue
        elif 'run' in activity:
            categorized_activities.append('Ambulation')
            continue
        elif re.findall('in\s*door',activity):
            continue
        elif re.findall('out',activity):
            continue
        elif 'pack' in activity:
            categorized_activities.append('Other')
            continue
        elif 'stand' in activity:
            categorized_activities.append('Sedentary')
            continue
        elif 'lay' in activity or  'ly' in activity:
            categorized_activities.append('Sedentary')
            continue
        elif 'stair' in activity:
            categorized_activities.append('Ambulation')
            continue
        elif re.findall('tak.*off', activity):
            categorize_activities.append('nonwear')
            continue
        else:
            while True:
                user_input = input('Categorize '+activity+': [S]edentary, [A]mbulation, [O]ther, [R]emove: ').lower()
                if user_input == 's' or user_input == 'sedentary':
                    categorized_activities.append('Sedentary')
                    break
                elif user_input == 'o' or user_input == 'other':
                    categorized_activities.append('Other')
                    break
                elif user_input == 'a' or user_input == 'ambulation':
                    categorized_activities.append('Ambulation')
                    break
                elif user_input == 'r' or user_input == 'remove':
                    break
                else:
                    print('Wrong input')
    return categorized_activities

def split_by_hour(parsed_recordlist):
    new_recordlist = []
    for record in parsed_recordlist:
        start_time = pd.to_datetime(record['START_TIME'])
        stop_time = pd.to_datetime(record['STOP_TIME'])
        if start_time.hour != stop_time.hour:
            split_time_start = record['START_TIME'][:14]+'59:59'
            new_record_1 = pd.Series([record['START_TIME'], record['START_TIME'], record['LABEL_NAME'], split_time_start],
                                      index=['HEADER_TIME_STAMP','START_TIME','LABEL_NAME','STOP_TIME'])

            one_hour = timedelta(hours=1)
            split_time_stop = pd.to_datetime(split_time_start)
            new_recordlist.append(new_record_1)
            # if the activity is longer than 1 hour, creates multiple lines fills the gap
            while split_time_stop < stop_time - one_hour:
                new_recordlist.append(pd.Series([split_time_stop, split_time_stop, record['LABEL_NAME'], split_time_stop + one_hour],
                                      index=['HEADER_TIME_STAMP','START_TIME','LABEL_NAME','STOP_TIME']))
                split_time_stop = split_time_stop + one_hour

            new_record_2 = pd.Series([split_time_stop, split_time_stop, record['LABEL_NAME'], record['STOP_TIME']],
                                      index=['HEADER_TIME_STAMP','START_TIME','LABEL_NAME','STOP_TIME'])
            new_recordlist.append(new_record_2)

        else:
            new_recordlist.append(record)
    return new_recordlist

def write_to_file(parsed_data, split, path_out, annotatoinset, annotator_set_id):
    if not split:
        parsed_data.to_csv(path_out+'total.annotation.csv', index=False)
    else:
        parsed_data['key'] = pd.to_datetime(parsed_data['STOP_TIME']).dt.strftime('%Y-%m-%d-%H')
        temp_data = parsed_data.groupby('key')
        for key, data in temp_data:
            start_time = pd.to_datetime(data.iloc[0,0])
            time_elements = key.split('-') #'%Y-%m-%d-%H'
            data.drop('key', axis = 1).to_csv('/'.join([path_out,'MasterSynced',str(time_elements[0]),
                        str(time_elements[1]),
                        str(time_elements[2]), str(time_elements[3]), '.'.join([annotatoinset, annotator_set_id,start_time.strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]+'-P0000',
                        'annotation.csv'])]), index=False)


if __name__ == '__main__':
    if (len(sys.argv) < 6):
        print('INSTRUCTION: \n'
              + 'for simple parse: STANDARD/CATEGORIZE [Original File Path] [Formatted Annotation File Path] [AnnotationSet] [ANNOTATORID-ANNOTATIONSETID]\n'
              + 'split by hour: STANDARD/CATEGORIZE  [Original File Path] [Formatted Annotation File Path] [AnnotationSet] [ANNOTATORID-ANNOTATIONSETID] split\n'
              + 'Standard for parse without categorize labels \n'
              + 'This tool automatically add annotation.csv at the end \n'
              + 'For more information, see README.MD')
    else:
        if sys.argv[1].lower() == 'standard':
            categorize = False
        elif sys.argv[1].lower() == 'categorize':
            categorize = True
        else:
            raise ValueError('WRONG COMMAND')
        if len(sys.argv) == 7 and sys.argv[6] == 'split':
            parse(sys.argv[2],sys.argv[3], True, categorize, sys.argv[4], sys.argv[5])
        else:
            parse(sys.argv[2],sys.argv[3], False, categorize, sys.argv[4], sys.argv[5])
