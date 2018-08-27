#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 11:03:13 2018

@author: zhangzhanming
"""

import pandas as pd
import sys
import os.path
import re
import collections

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
            curr_activities.append(time_record[1].lower().strip())
        else:
            if len(curr_activities) > 0 and last_time != curr_time:
                curr_activities.sort()
                new_label = '-'.join(curr_activities)
                splitted_time_list.append(pd.Series([last_time, last_time, curr_time, new_label],
                                                    index=['HEADER_TIME_STAMP','START_TIME','STOP_TIME','LABEL_NAME']))
            if time_record[2] == 'start':
                curr_activities.append(time_record[1].lower().strip())
            else:
                curr_activities.remove(time_record[1].lower().strip())

            last_time = curr_time

    # sort by start time, export to dataframe
    splitted_time_list.sort(key=lambda series: series['START_TIME'])
    splitted_annotation = pd.DataFrame(splitted_time_list)

    return splitted_annotation


def class_mapping(in_annotation):
    '''
    Create a table with more features('label','posture','four_class',
                                      'activity_group','indoor_outdoor',
                                      'activity', 'hand_gesture')
    of the labels of input annotation data

    :param pandas.DataFrame in_annotation: input annotation data

    '''

    labels = in_annotation.iloc[:,3].unique()
    mapped_list = []
    for label in labels:
        activity = __get_activity(label)
        posture = __get_posture(label, activity)
        four_class = __get_four_class(label, activity)
        ambience = __get_indoor_outdoor(label, activity)
        hand_gesture = __get_hand_gesture(label, activity)
        activity_group = __get_activity_group(label, four_class)
        mapped_list.append(pd.Series([label, posture, four_class, activity_group,
                                      ambience, activity,hand_gesture],
                                     index=['label','posture','four_classes',
                                            'activity_group','indoor_outdoor',
                                            'activity', 'hand_gesture']))
    return pd.DataFrame(mapped_list)


def __get_posture(label, activity):
    if label == 'transition':
        return label

    sit_keywords = ['sit','bik','reclin','eat']
    if any(re.findall(word, label) for word in sit_keywords):
        return 'sitting'

    upright_keywords = ['stand', 'run', 'jump', 'walk', 'frisbee', 'escalator'
                        ,'elevator', 'climb.*stair','stair', 'treadmill',
                        'vend.*machine', 'shelf reloading or unloading','sweep','shop','cook']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in upright_keywords):
        return 'upright'

    lying_keywords = ['lying','sleep','nap']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in lying_keywords):
        return 'lying'

    print('unknown posture', activity, label)
    return 'unknown'


def __get_four_class(label, activity):
    if 'transition' in label:
        return 'transition'

    amb_keywords = ['walk','run','stair']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in amb_keywords):
        return 'ambulation'

    cyc_keywords = ['cycl','bik']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in cyc_keywords):
        return 'cycling'

    seden_keywords = ['sit','stand','lying','typ', 'sleep', 'computer', 'still',
                      'elevator','text','wait','eat','watch','gam']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in seden_keywords):
        return 'sedentary'

    other_keywords = ['frisbee', 'sweep', 'paint', 'clean.*room', 'soccer',
                      'basketball', 'tennis', 'jump','packing','shop','cook']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in other_keywords):
        return 'others'

    print('unknown four class:', label)
    return 'unknown'


def __get_indoor_outdoor(label, activity):
    indoor_keywords = ['in\s*door', 'elevator', 'mbta', 'computer', r'brush\s*teeth'
                       ,'sleep','escalator','shop','cook','stairs','bed', 'typ'
                       ,'treadmill', 'arm.*on desk', 'stationary biking', 'lying','sweep','game',
                       'eat','shop','pack','gam']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in indoor_keywords):
        return 'indoor'

    outdoor_keywords = ['out\s*door', 'signal\s*light', 'city','stop.*light']
    if any((re.findall(word, label) or re.findall(word, activity)) for word in outdoor_keywords):
        return 'outdoor'


    print('unknow indoor outdoor: ', label, activity)
    return 'unknown'


def __get_activity_group(label, four_class):
    if re.findall('sleep|lying', label):
        return 'sleep'

    unwear_keywords = [r'take\s*off','not.*wear','unworn','unwear','non.*wear']
    if any(re.findall(word, label) for word in unwear_keywords):
        print('unknown four class', label)
        return 'nonwear'

    return four_class


def __get_activity(label):
    actions = []
    # detect if the special verbs inside the label first
    # for walk and run, detect if the speed or climbing stairs exist
    first_activity = ''
    special_words = {'treadmill running at 5.5 mph 5% grade': ['5.5\s*mph.*5%\s*grade',
                                           '5%\s*grade.*5.5\s*mph'],
                   'treadmill walking at 1 mph':['1\s*mph'],
                   'treadmill walking at 2 mph':['2\s*mph'],
                   'treadmill walking at 3-3.5 mph':['3-3.5\s*mph','3\s*mph','3.5\s*mph'],
                   'treadmill running at 5.5 mph':['5.5\s*mph'],
                   'walking up stairs':['up.*stairs'],
                   'walking down stairs':['down.*stairs']}

    for key, keyword_list in special_words.items():
        if any(re.findall(keyword, label) for keyword in keyword_list):
            first_activity = key
            continue

    if len(first_activity) == 0:
        if 'walk' in label:
            first_activity = 'self-paced walking'
        elif 'run' in label or 'jog' in label:
            first_activity = 'running'

    if len(first_activity) > 0:
        actions.insert(0, first_activity)

    # detect if there are other actions at the same time
    activities_verbs = collections.OrderedDict({'sitting':['sit'],
                  'standing':['stand','signal.*light'],
                  'biking outdoor' : [r'bik.*out\s*door',r'out\s*door.*bik', '300.*kpm.*bik'],
                  'stationary biking':['bik.*stationary',r'bik.*in\s*door|in\s*door.*bik'],
                  'frisbee':['frisbee'],
                  'jumping jacks':['jumping jacks'],
                  'lying on the back':['lying.*back','ly.*bed'],
                  'elevator up':['elevator.*up', 'up.*elevator'],
                  'elevator down':['elevator.*down', 'down.*elevator'],
                  'escalator up':['escalator.*up','up.*escalator'],
                  'escalator down':['escalator.*down','down.*escalator'],
                  'transition':['transition'],
                  'reclining':['reclin.*'],
                  'writing':['writ'],
                  'sweeping':['sweep'],
                  'keyboard typing':['typ'],
                  'folding towel':['fold.*towel'],
                  'shelf loading or unloading':['shelf.*load','unload'],
                  'using vending machine': ['vend.*machine'],
                  'texting':['text'], 'web browsing':['web browsing'], 
                  'gaming':['gam'],
                  'using computer':['us.*computer','watch.*netflix'],
                  'sleeping':['sleep','nap'],
                  'eating':['eat'],
                  'packing':['pack'],
                  'shopping':['shop'],
                  'cooking':['cook','mak.*food']})

    for key, keyword_list in activities_verbs.items():
        if any(re.findall(keyword, label) for keyword in keyword_list):
            actions.append(key)

    # deal with some overlap activities

    if ('bik' in label) and not ('biking outdoor' in actions) and not ('stationary biking' in actions):
        actions.append('biking')

    if ('elevator' in label) and not ('elevator up' in actions) and not ('elevator down' in actions):
        actions.append('elevator')

    if ('escalator' in label) and not ('escalator up' in actions) and not ('escalator down' in actions):
        actions.append('escalator')

    if ('stairs' in label) and not ('walking up stairs' in actions) and not ('walking down stairs' in actions):
        actions.append('escalator')


    # special match for talking
    if any(re.findall(keyword, label) for keyword in ['talk.*phone','call']):
        actions.append('talking with phone')
    else:
        if any(re.findall(keyword, label) for keyword in ['talk','tell.*story']):
            actions.append('talking')
        if 'phone' in label:
            actions.append('using phone')

    activity = ' and '.join(actions)

    activity_adverbs = {'with bag':['bag'],
                        'naturally':['natur'],
                        'carrying a drink':['carry.*drink'],
                        'with arms on desk':['arms.*on.*desk'],
                        'on train':['on train'],
                        'for stop light':['for.*stop.*light']
                        }

    adverbs = []

    for key, keyword_list in activity_adverbs.items():
        if any(re.findall(keyword, label) for keyword in keyword_list):
            adverbs.append(key)

    if len(adverbs) != 0:
        activity = activity + ' '+' '.join(adverbs)

    if activity == 'sitting':
        activity = activity + ' still'

    if activity == 'standing':
        activity = activity + ' naturally'

    if len(activity) == 0:
        print('unknown activity: ', label)
        return 'unknown'

    return activity


def __get_hand_gesture(label, activity):
    handgestures_label = {'writing':['writ'],
                'arms on desk':['on.*desk','computer','gam'],
                'holding cellphone':['phone'],
                'transition':['transition'],
                'biking': ['bik'],
                'carrying a drink': ['drink'],
                'carrying a suitcase': ['carry.*suitcase'],
                'frisbee':['frisbee'],
                'jumping jacks':['jumping.*jacks'],
                'keyboard typing':['typ'],
                'sweeping':['sweep'],
                'shelf loading or unloading':['shelf.*load','unload'],
                'using vending machine':['vend.*machine'],
                'still':['still','lying','sleep'],
                'folding towels':['fold.*towel'],
                'laundry':['laundry'],
                'eating':['eat'],
                'packing':['pack'],
                'holding a bag':['hold.*bag','with.*bag'],
                'shopping':['shop']}
    for key, keyword_list in handgestures_label.items():
        if any((re.findall(word, label) or re.findall(word, activity)) for word in keyword_list):
                return key

    # special match for talking
    if any(re.findall(keyword, label) for keyword in ['talk.*phone','call']):
        return 'phone talking'
    else:
        if any(re.findall(keyword, label) for keyword in ['talk','tell.*story']):
            return 'talking'
        if any(re.findall(keyword, label) for keyword in ['phone','text']):
            return 'using phone'

    if activity == 'unknown':
        print('unknown gesture', activity, label)
        return 'unknown'
    
    print('free hand gesture', activity, label)
    return 'free'


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


        in_annotation = pd.read_csv(path_in)

        if 'SPLIT' in command:
            splitted_annotation = annotation_splitter(in_annotation)
            splitted_annotation.to_csv(os.path.join(path_out, 'splitted.annotation.csv'), index=False)

            if command == 'SPLIT_CLASSMAP':
                class_map = class_mapping(splitted_annotation)
                class_map.to_csv(os.path.join(path_out,'class_mapping.csv'), index=False)

        elif command == 'CLASSMAP':
            class_map = class_mapping(in_annotation)
            class_map.to_csv(os.path.join(path_out,'class_mapping.csv'), index=False)


# def __test():
#     in_annotation=pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Data/MyData/AIDEN.ANKLE.2018-06-20/Aiden/Derived/RealLifeAnkleRawtotal.annotation.csv')
#     splitted = annotation_splitter(in_annotation)
#     classmapping = class_mapping(splitted)
#     test_class = pd.read_csv('/Users/zhangzhanming/Desktop/mHealth/Test/SPADESInLab.class.csv')
#     unique_mapping = test_class.iloc[:,[2,3,4,5,6,8]].drop_duplicates()
#     unique_mapping.to_csv('/Users/zhangzhanming/Desktop/mHealth/Test/unique_mapping.csv')
