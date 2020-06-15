# Latex document generation using a .tex template and .csv inputs

This python script including the .tex template were created as part of the conference organization for the [Interspeech 2019](https://interspeech2019.org/), that was mainly organized by my lab, the [Signal Processing and Speech Communication Laboratory](https://www.spsc.tugraz.at/) at TU Graz. My task was to generate session overview posters containing all the information for each session and room - so I quickly decided to write a python script and use it to automatically generate these posters from a csv input file and a Latex template. I think this code might be useful for every kind of automatic document generation using templates and input files.

## Run example
1. Run 'run_session_poster_generation.py'
2. Session posters are created in session_program_files folder
    - Each room has a folder <ROOM> containing all the separate session posters for this room
    - Each session has a '<SESSIONID>.pdf' containing the session posters located in the corresponding room folder.
    - This file structure was chosen to ease printing and the distribution of posters to the corresponding rooms.
