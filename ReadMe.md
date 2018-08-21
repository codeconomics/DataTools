## Sanity Check Tool

 ### SanityCheck.py
 Usage: Python SanityCheck.py [root_path] [config_path]  
 
 **key constant variables:**
 
 Here are some changeable variables in `sanity_check` method
 
 `MISSING_FILE_TAG` = `'missing-file'` The html tag id of missing file report in report template  
 `ANNOTATION_TAG` = `'annotation'` The html tag id of annotation file report in report template  
 `SAMPLING_RATE_TAG` = `'sampling-rate'` The html tag id of sampling rate report in report template  
 `BOKEH_VERSION` = `'0.13.0'` The version of bokeh package  
 
 ### configuration
 The configuration file should be in [yaml syntax](https://learn.getgrav.org/advanced/yaml). You can refer to an example [here](../padar_extra/config.txt). Following are configurable variables:
  
  `pid` : a `list` of pid `string` needed to check within the root folder. 
  
     E.g. pid : ['Aiden', 'SPADES_3']  

  `check_missing_file`: `boolean` if check if there exists any missing file. Default false

  `check_annotation_file_exist`: **(REQUIRED IF `check_missing_file` is true)**`boolean` if need to check if there is any annotation file missed. 

  `num_annotator`: **(REQUIRED IF `check_missing_file` is true)**`int` how many annotators were there, indicating how the number of annotation files should exist

  `check_event`: **(REQUIRED IF `check_missing_file` is true)**`boolean` if check the existence of event file

  `check_EMA`: **(REQUIRED IF `check_missing_file` is true)**`boolean` if check the existence of EMA file

  `check_GPS`: **(REQUIRED IF `check_missing_file` is true)** `boolean` if check the existence of GPS file

  `num_sensors`: **(REQUIRED IF `check_missing_file` is true)** `int` how many sensors were there, indicating the number of sensor files should exist

  `sensor_location`: a list of locations required to check in `[pid]/Derived/location_mapping.csv`, Default None

      e.g.
      sensor_locations:
         - DominantAnkle
         - DominantThigh
         - DominantWaist
         - NonDominantWrist

  `check_sampling_rate`: `dictionary` a dictionary including the properties need to check regarding sampling rate. If do not wish to check sampling rate, do not write this variable or assign it as `false`. Default None. Variables should be included are as follows:

&nbsp;&nbsp;&nbsp; `claimed_rate`: `int` the samples per minute the sensor files should have

&nbsp;&nbsp;&nbsp; `accept_range`: `int` in decimal. the range the actual sampling rate should be within. e.g. `0.2` indicating the sampling rate should not be lower or higher than +- 20% of the claimed rate

  `check_annotation`: `boolean` if wish to check the details of annotation files. Default false
  
  `annotation_lower_bound`: **(REQUIRED IF `check_annotation` is true)** `string` time string indicating the shortest time duration any annotation should be. e.g. '60s', '2 seconds'
  
  `annotation_upper_bound`: **(REQUIRED IF `check_annotation` is true)** `string` time string indicating the longest time duration any annotation should be. e.g. '12 h', '10 hours'
  
  `check_episode_duration`: `dictionary` a dictionary including the duration limits for specific activities in the following format, default None:
  
     activity: ['> or < limit1','> or < limit2' ...] or 'limit' if there is only one limit. This means the given activity should not have duration below or beyond limit1, etc.
     e.g. 
     check_episode_duration:
       sleep: ['>10h', '<60 seconds']
       wait: '>2h'
       ambulation: '>12hours'
   
   `check_episode_time`: `dictionary` a dictionary including the abnormal time range for specific activities in the following foramt, default None:
   
      activity: [starttime, endtime]. This means the given activity should not happend during starttime to endtime
      e.g.
      check_episode_time:
        ambulation:[3am, 6am]
   
   `specification`: `list` a list of dictionary providing special requirement for specific pids, default None.
   
      e.g.
      
      specification:
        -
          pid: Aiden
          check_episode_time:
            ambulation: [22:00, 24:00]

        -
          pid: SPADES_3
          check_sampling_rate: false
          num_sensor : 4
   
   &nbsp;&nbsp;&nbsp;**IMPORTANT NOTICE FOR SPECIFICATION:**
   
   1. `pid` is required for all dictionary within the specification list. The dictionaries can contain all configurable variables mentioned above, but not including specification itself. 
   2. To negate the need to conduct certain checking processes specified by dictionary, including `check_sampling_rate`, `check_episode_duration`, `check_episode_time`, specify them as `false` in specification dictionary, or they will not be in effect.
   3. The specification of the checking processes specified by dictionary, including `check_sampling_rate`, `check_episode_duration`, `check_episode_time`, will **cover** the original requirements, and is not accumulative. e.g. if you set the sleep time should not be more than 10 hours in the general configuration and specified sleep to not be less than 2 hours for SPADES_3. The sanity check tool will only tag those sleep episodes less than 2 hours for SPADES_3.
      
  
 ### BokehScripts.txt
    The scripts for styling for Bokeh package. It must be included in the directory of the python script.

 ### ReportTemplate.html
    The html template for the report. If does not exist in the directory of the python script, a plain report will be generated. The html tag id for each components of the report is specified in `sanity_check` method, as explained in section SanityCheck.py

