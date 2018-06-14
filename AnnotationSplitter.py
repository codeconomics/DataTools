#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 11:03:13 2018

@author: zhangzhanming
"""

import pandas as pd
import sys
import os.path

def annotation_splitter(in_annotation):
    '''
    Combine overlapped labels and split them according to time
    
    :param pandas.DataFrame in_annotation: the raw annotation to split
    '''
    
    time_list = []
    # iterate through the annotation data, put (start time/end time, label name
    # start/end, index) to a list
    for index, series in in_annotation.iterrows():
        time_list.append((pd.to_datetime(series[1]), 
                          series[3],'start',index))
        time_list.append((pd.to_datetime(series[2]), 
                          series[3],'end',index))
    time_list.sort(key=lambda tup:tup[0])# sort the list according to time
    
    # iterate through the time list, detect overlap. If exist, split and concatenate them
    curr_activities = []
    splitted_time_list = []
    last_time = time_list[0][0]

    for time_record in time_list:
        curr_time = time_record[0]
        if curr_time == last_time and time_record[2] == 'start':
            curr_activities.append(time_record[1].lower())
        else:
            if len(curr_activities) > 0:
                new_label = '-'.join(curr_activities)
                splitted_time_list.append(pd.Series([last_time, last_time, curr_time, new_label],
                                                    index=['HEADER_TIME_STAMP','START_TIME','STOP_TIME','LABEL_NAME']))
            if time_record[2] == 'start':
                curr_activities.append(time_record[1].lower())
            else:
                curr_activities.remove(time_record[1].lower())
            last_time = curr_time
    
    # sort by start time, export to dataframe
    splitted_time_list.sort(key=lambda series: series['START_TIME'])
    splitted_annotation = pd.DataFrame(splitted_time_list)
    
    return splitted_annotation

def class_mapping(in_annotation):
    '''
    Create a table with more features(posture, four class categorization, ambivience)
    of the labels of input annotation data
    
    :param pandas.DataFrame in_annotation: input annotation data
    
    '''
    
    pass
    

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('INSTRUCTION: \n'+
              'For splitting: \n SPLIT [Original File Path] [Formatted Annotation File Path] \n' +
              'For splitting and generating a class mapping file: \n' + 
              'SPLIT_CLASSMAP [Original File Path] [Formatted Annotation File Path]\n' +
              'For generating a class mapping file: \n' +
              'CLASSMAP [Original File Path] [Formatted Annotation File Path]')
    else:
        command = sys.argv[1]
        path_in = sys.argv[2]
        path_out = sys.argv[3]
        if os.path.isdir(path_out):
            path_out = path_out + '/'
        
        in_annotation = pd.read_csv(path_in)

        if 'SPLIT' in command:
            splitted_annotation = annotation_splitter(in_annotation)
            splitted_annotation.to_csv(path_out+'splitted.annotation.csv', index=False)
            
            if command == 'SPLIT_CLASSMAP':
                class_map = class_mapping(splitted_annotation)
                class_map.to_csv(path_out+'splitted.class.csv', index=False)

        elif command == 'CLASSMAP':
            class_map = class_mapping(in_annotation)
            class_map.to_csv(path_out+'splitted.class.csv', index=False)
            
        
        
        
        
        
        
        