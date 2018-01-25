import os
import hashlib
import pandas as pd
import numpy as np 

##########################
# FUNCTIONS TO PARSE DEMOS
##########################


def md5(fname):
    '''
    helper function used to know what md5 checksum a file has. needed to know unique key in sqlite database for a given demo
    '''
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
def make_dictionary(demos_path):
    '''
    function that makes a dictionary with:
    - key: 1 match folder where the demos are located 
    - value: list with md5 checksum + list with demo names
    '''
    counter = 0
    folders = os.listdir(demos_path)
    demos_dct = {}

    for folder in folders:
        #put all files in a list
        files = os.listdir(os.path.join(demos_path, folder))

        #make empty lists
        demo_names_lst = list()
        md5_names_lst = list()
        last_changed_lst = list()

        #extract all demos from the files
        demos = []
        for file in files:
            if str.upper(file[-5:-2]) == 'DM_':
                demos.append(file)

        #debug if no demos in folder
        if(len(demos)) == 0:
            print folder
            pass

        elif(len(demos)) == 1:
            demo_names_lst = demos
            md5_name = md5(os.path.join(demos_path, folder, demos[0]))
            md5_names_lst.append(md5_name)

        else:
            #fill the lists with demo names and their last changed date
            for demo in demos: 
                #if file is a demo, process it
                changed_date = os.path.getmtime(os.path.join(demos_path, folder, demo))
                md5_name = md5(os.path.join(demos_path, folder, demo))
                last_changed_lst.append(changed_date)
                demo_names_lst.append(demo)
                md5_names_lst.append(md5_name)

            #[x for _,x in sorted(zip(last_changed_lst,demo_names_lst))]

            #make a df with the purpose of sorting on the last changed date of the demos
            df = pd.DataFrame({'demo_name': demo_names_lst,
                               'md5_name' : md5_names_lst,
                               'last_changed_date': last_changed_lst})
            df = df.sort_values('last_changed_date')
            #if length between first demo and last demo is less than 5 minutes, sort on demo name, else on last changed date
            if int(np.subtract(df.iloc[[-1], 1], df.iloc[[0], 1])) < 5 * 60:
                df = df.sort_values('demo_name')

            #fill a list of lists of md5 name and demo name
            md5_names_lst = df.md5_name.tolist()
            demo_names_lst = df.demo_name.tolist()

        output_list = [md5_names_lst,demo_names_lst]

        match_name = folders[counter] #make key name based on match folder
        demos_dct[match_name] = output_list

        counter += 1

        if counter % 100 == 0:
            print 'parsed ' + str(counter) + ' matches'
    print 'finished parsing all matches!'
    
    return demos_dct
    

def indexer_exe_cmd(demo_path, parameters_dct):
    '''
    helper function to create string with demo_path and parameters to input in anders libtech 3 api
    parameters: 
    - demo_path: full path to demo
    - parameters_dct: a dictionary with all the parameters necessary
    '''
    s = 'indexer indexTarget/' + demo_path 
    s += '/exportBulletEvents/' + parameters_dct['exportBulletEvents']
    s += '/exportPlayers/' + parameters_dct['exportPlayers']
    s += '/exportDemo/' + parameters_dct['exportDemo']
    s += '/exportObituaries/' + parameters_dct['exportObituaries']
    s += '/exportChatMessages/' + parameters_dct['exportChatMessages']
    s += '/exportJson/' + parameters_dct['exportJson']
    s += '/exportSQL/' + parameters_dct['exportSQL']
    s += '/exportPaths' + parameters_dct['exportPaths']
    
    if parameters_dct['exportSQL'] == 1:
        s += '/exportSQLFile/' + parameters_dct['exportSQL']
    
    if parameters_dct['exportJson'] == 1:
        s += '/eportJsonFile/' + parameters_dct['exportJson']

    return s

def fill_db(root_path, parameters_dct, demos_dct, demo_folder_name = 'demos', exe_name = 'Anders.Gaming.LibTech3.exe', verbose = True):
    '''
    fill a sqlite database with statistics of all demos
    
    parameters:
    - path: root directory (1 level higher than demos)
    - parameters_dct: a dictionary with all the parameters settings to fill database: 
    - demos_dct: dictionary created with make_dictionary function
    - demo_folder_name: foldername where the demos are located
    - exe_name: anders libtech3 api filename
    - verbose: if you want info while function is running
    '''
    counter = 1
    exe_path = os.path.join(root_path, exe_name)
    for k in demos_dct:
        match_folder = os.path.join(root_path, demo_folder_name, k)
        
        for demo in demos_dct[k][1]:
            demo_path = os.path.join(match_folder, demo)
            
            #insert demo into database
            parameters = indexer_exe_cmd(demo_path, parameters_dct)
            os.system(exe_path + ' ' + parameters)
        if counter % 50 == 0:
            print 'filled ' + str(counter) + ' matches in the database'
        counter += 1
        
    print 'all matches filled in database!'

############################
# FUNCTIONS TO ANALYZE DEMOS
############################

def get_sec(time_str):
    '''function currently not used anywhere but handy for shiny app later'''
    m, s = time_str.split(':')
    return int(m) * 60 + int(s)


def get_kill_sprees(df, maxtime_secs = 30, weapon_filter = None, minspree = 3, verbose = True):
    '''
    Function that outputs kill sprees

    parameters:
    - df: dataframe with obituaries
    - weapons_enum: dictionary with the key as weapon names and values of the weapon numbers in RTCW
    - maxtime_secs: max time in seconds to get a spree
    - weapon_filter: list with weapon_filters, check weapons_enum.py for the correct naming to use
    - minspree: minimum amount of enemy players killed within a certain timeframe (maxtime_secs)
    - verbose: output prints for every 100 demos analyzed

    returns:
    a pandas dataframe with the follow columns:
    - md5: md5 checksum of the demo
    - start: rtcw time when spree begins (exact time of first frag of the spree)
    - end: rtcw time when spree ends (exact time of last frag of the spree)
    - attacker: player number who made the spree
    - spreecount: the amount of kills the attacker made in the spree
    '''

    #import the weapons_enum
    from weapons_enum import weapons_enum

    #empty lists that we will populate and use to make final df_spree 
    pd_md5 = []
    pd_attacker = []
    pd_start_dwtime = []
    pd_end_dwtime = []
    pd_spree_length = []

    #helper variables for verbose
    counter = 0
    total_demos = df.szMd5.nunique()

    #filter the dataframe if we have a weapon filter
    if weapon_filter != None:
        weapon_numbers_filter = []
        for weapon in weapon_filter:
            weapon_numbers_filter.append(weapons_enum[weapon])
        weapon_numbers_filter = [item for sublist in weapon_numbers_filter for item in sublist]
        df = df.loc[df['bWeapon'].isin(weapon_numbers_filter)].copy()

    for demo in df.szMd5.unique():
        df_demo = df.loc[df['szMd5'] == demo]
        counter += 1
        
        for player in df_demo.bAttacker.unique():
            df_cut = df_demo.loc[df['bAttacker'] == player]
            arr = df_cut.as_matrix(columns = ['bAttacker', 'bTarget', 'bIsTeamkill', 'dwTime'])

            timerestriction = maxtime_secs * 1000 #put it in seconds for rtcw time
            spreecounter = 0
            temp_sprees = []
            total_rows = len(arr)

            for row in range(len(arr)):
                frag = arr[row, :]

                #init first_spreetime
                if row == 0:
                    first_spreetime = frag[3]         

                #debug if dzTime is buggy (lower current dzTime vs first spree dzTime): restart counting
                if frag[3] - first_spreetime < 0:
                    if (frag[0] != frag[1]) and (frag[2] != 1):
                        spreecounter = 1
                        first_spreetime = frag[3]   
                        temp_sprees = []
                        temp_sprees.append(first_spreetime)       
                    else:
                        spreecounter = 0
                        first_spreetime = frag[3]   
                        temp_sprees = []

                #if current frag is in the timerestriction, up the spreecount and append temp_sprees
                if frag[3] - first_spreetime <= timerestriction:
                    if (frag[0] != frag[1]) and (frag[2] != 1):
                        spreecounter += 1
                        temp_sprees.append(frag[3])

                #if not, add a value to every list with spree details if minspree is met / reinitilize spreecounter and temp_sprees
                else:
                    if spreecounter >= minspree:
                        pd_md5.append(demo)
                        pd_attacker.append(player)
                        pd_start_dwtime.append(temp_sprees[0])
                        pd_end_dwtime.append(temp_sprees[-1])
                        pd_spree_length.append(spreecounter)

                    if (frag[0] != frag[1]) and (frag[2] != 1):
                        spreecounter = 1
                        first_spreetime = frag[3]   
                        temp_sprees = []
                        temp_sprees.append(first_spreetime)

                    else:
                        spreecounter = 0
                        first_spreetime = frag[3]   
                        temp_sprees = []

                #if last frag in the data, and we have reach the minspree, add entry
                if row == (total_rows - 1):
                    if spreecounter >= minspree:
                        pd_md5.append(demo)
                        pd_attacker.append(player)
                        pd_start_dwtime.append(temp_sprees[0])
                        pd_end_dwtime.append(temp_sprees[-1])
                        pd_spree_length.append(spreecounter)

        if counter % 100 == 0:
            if verbose:
                print 'scanned ' + str(counter) + ' demos of ' + str(total_demos) + ' demos in total'

    'all done!'


    #make final dataframe where 1 row is a spree with all the necessary info
    df_spree = pd.DataFrame(
    {'md5': pd_md5,
     'attacker': pd_attacker,
     'start': pd_start_dwtime,
     'end': pd_end_dwtime,
     'spreecount': pd_spree_length
    })

    return df_spree

def locate_demo_path(demos_dct, spree, root_path):
    '''
    helper function that outputs the path to the demo that we want to cut
    '''
    for k in demos_dct:
        if spree.md5 in demos_dct[k][0]:
            match_folder = k
            demo_loc = [i for i in range(len(demos_dct[k][0])) if demos_dct[k][0][i]==spree.md5]
            demo_name = demos_dct[k][1][demo_loc[0]]
            
            return match_folder, demo_name

def cutter_exe_cmd(root_path, match_folder, demo_name, start_time, end_time, 
                   demo_folder_name = 'demos', output_folder = 'output_spree_demos', cut_type = 1):
    '''
    helper function to create string with demo_path and parameters to input in anders libtech 3 api
    parameters: 
    - demo_path: full path to demo
    - parameters_dct: a dictionary with all the parameters necessary
    '''
    demo_path = os.path.join(root_path, demo_folder_name, match_folder, demo_name)
    output_path = os.path.join(root_path, output_folder, demo_name)
    
    s = 'cut ' + demo_path + ' '
    s += output_path + ' '
    s += str(start_time) + ' '
    s += str(end_time) + ' '
    s += str(cut_type) + ' 0' # plus the zero at the end or the api will crash

    return s

def cut_demos(root_path, demos_dct, df_spree, exe_name, offset_start = 5000, offset_end = 5000):

    for row in range(len(df_spree)):

        spree = df_spree.loc[row]
        match_folder, demo_name = locate_demo_path(demos_dct, spree, root_path)

        start_time = spree.start - offset_start
        end_time = spree.end + offset_end

        parameters = cutter_exe_cmd(root_path, match_folder, demo_name, start_time, end_time, 
                                    demo_folder_name = 'demos', output_folder = 'output_spree_demos', cut_type = 1)

        os.system(exe_path + ' ' + parameters)

