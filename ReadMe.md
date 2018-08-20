## Sanity Check Tool

 ### SanityCheck.py
    Usage: Python SanityCheck.py [root_path] [config_path]  

 ### configuration
 The configuration file should be in ymal format. Following are configurable variables:
  
  `pid` : a list of pids need to check within the root folder. 
  
     E.g. pid : ['Aiden', 'SPADES_3']  

  `check_missing_file`: `boolean` if check if there exists any missing file

  `check_annotation_file_exist`: **REQUIRED IF check_missing_file is true**`boolean` if need to check if there is any annotation file missed. 

  `num_annotator`: **REQUIRED IF check_missing_file is true**`int` how many annotators were there, indicating how the number of annotation files should exist

  `check_event`: **REQUIRED IF check_missing_file is true**`boolean` if check the existence of event file

  `check_EMA`: **REQUIRED IF check_missing_file is true**`boolean` if check the existence of EMA file

  `check_GPS`: `boolean` if check the existence of GPS file

  `num_sensors`: `int` how many sensors were there, indicating the number of sensor files should exist

  `sensor_location`: a list of locations required to check in `[pid]/Derived/location_mapping.csv`

      e.g.
      sensor_locations:
         - DominantAnkle
         - DominantThigh
         - DominantWaist
         - NonDominantWrist

  `check_sampling_rate`: `dictionary` a dictionary including the properties need to check regarding sampling rate. If do not wish to check sampling rate, do not write this variable or assign it as `false`. Default None. Variables should be included are as follows:

&nbsp;&nbsp;&nbsp; `claimed_rate`: `int` the samples per minute the sensor files should have

&nbsp;&nbsp;&nbsp; `accept_range`: `int` in decimal. the range the actual sampling rate should be within. e.g. `0.2` indicating the sampling rate should not be lower or higher than +- 20% of the claimed rate

  `check_annotation`: `boolean` if wish to check the details of annotation files
  
  `annotation_lower_bound`: `string` time string indicating the shortest time duration any annotation should be. e.g. '60s', '2 seconds'
  
  `annotation_upper_bound`: `string` time string indicating the longest time duration any annotation should be. e.g. '12 h', '10 hours'
  
  `check_episode_duration`: 
  
 ### BokehScripts.txt

 ### ReportTemplate.html

