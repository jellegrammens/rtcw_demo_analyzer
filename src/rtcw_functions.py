def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
	
def make_dictionary(demos_path):
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

        #debug
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
            print 'parsed ' + str(counter) + ' demos'
    print 'finished parsing all demos!'
    
    return demos_dct

def indexer_exe_cmd(demo_path,
    exportPaths = None,
    exportBulletEvents = 1,
    exportPlayers = 1,
    exportDemo = 0,
    exportObituaries = 1,
    exportChatMessages = 0,
    exportJson = 0,
    exportSQL = 1,
    eportJsonFile = 'out.json',
    exportSQLFile = 'out.db'):
    
    s = 'indexer indexTarget/' + demo_path 
    s += '/exportBulletEvents/' + str(exportBulletEvents)
    s += '/exportPlayers/' + str(exportPlayers)
    s += '/exportDemo/' + str(exportDemo)
    s += '/exportObituaries/' + str(exportObituaries)
    s += '/exportChatMessages/' + str(exportChatMessages)
    s += '/exportJson/' + str(exportJson)
    s += '/exportSQL/' + str(exportSQL)
    
    if exportSQL == 1:
        s += '/exportSQLFile/' + exportSQLFile
        
    if exportJson == 1:
        s += '/eportJsonFile/' + eportJsonFile
   
    return s

def fill_db(path, demos_dct, demos_path = 'clean', exe_name = 'Anders.Gaming.LibTech3.exe', verbose = True):
    counter = 1
    exe_path = os.path.join(path, exe_name)
    for k in demos_dct:
        match_folder = os.path.join(path, demos_path, k)
        
        for demo in demos_dct[k][1]:
            demo_path = os.path.join(match_folder, demo)
            
            #insert demo into database
            parameters = indexer_exe_cmd(demo_path)
            os.system(exe_path + ' ' + parameters)
        if counter % 50 == 0:
            print 'filled ' + str(counter) + ' matches in the database'
        counter += 1
		
	print 'all matches filled in database!'