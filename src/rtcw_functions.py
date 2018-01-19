import os
import hashlib
import pandas as pd
import numpy as np 

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
			print 'parsed ' + str(counter) + ' demos'
	print 'finished parsing all demos!'
	
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