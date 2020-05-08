import os
import hashlib
import pandas as pd
import numpy as np 
from lxml import etree
from xml.etree import ElementTree
from goldfinch import validFileName
import shutil
import glob
import re
from scipy import stats


#import lists with info
from chathelper import DocsStolen
from chathelper import DocsReturned
from chathelper import DocsTransmitted
from chathelper import DocsAll
from chathelper import DynamitePlanted
from chathelper import DynamiteDefused
from chathelper import DynamiteExploded
from chathelper import DynamiteAll

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
	
	if parameters_dct['exportSQL'] == '1':
		s += '/exportSQLFile/' + parameters_dct['exportSQLFile']
	
	if parameters_dct['exportJson'] == '1':
		s += '/eportJsonFile/' + parameters_dct['exportJsonFile']

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
			if verbose:
				print demo
			os.system(exe_path + ' ' + parameters)
		if counter % 50 == 0:
			print 'filled ' + str(counter) + ' matches in the database'
		counter += 1
		
	print 'all matches filled in database!'

############################
# FUNCTIONS TO ANALYZE DEMOS
############################

def add_match_data(df, player_df, demos_dct, what_df = 'obituary_df'):
	'''
	Add match information to a db df to possibily filter on later. 
	Important note: only works if you have my rtcw demo folder naming system.
	'''
	pd_md5 = []
	pd_match = []
	pd_demo = []

	for md5 in df.szMd5.unique():
		for k in demos_dct:
			if md5 in demos_dct[k][0]:
				demo_loc = [i for i in range(len(demos_dct[k][0])) if demos_dct[k][0][i]==md5]
				demo_name = demos_dct[k][1][demo_loc[0]]
				pd_md5.append(md5)
				pd_match.append(k)
				pd_demo.append(demo_name)

	md5_match_link = pd.DataFrame(
	{'szMd5': pd_md5,
	 'matchName': pd_match,
	 'demoName': pd_demo
	})

	df = pd.merge(df, md5_match_link, how = 'left', on = 'szMd5')

	player_df = player_df[['szMd5', 'szCleanName', 'bClientNum']].copy()
	player_df.rename(columns = {'bClientNum':'bAttacker'}, inplace=True)

	if what_df == 'obituary_df':
		df = pd.merge(df, player_df, how = 'left', on = ['szMd5', 'bAttacker'])


	return df

def convert_names(x):
	'''helper function to create valid player names for files later'''
	x = str(x)
	x = validFileName(x)
	return x


def get_kill_sprees(obituary_df, demo_df, maxtime_secs = 30, include_weapon_filter = None, exclude_weapon_filter = None, minspree = 3, pov_sprees_only = False, verbose = True):
	'''
	Function that outputs kill sprees

	TO BE ADDED:
	- include / exclude / only teamkill

	parameters:
	- obituary_df: dataframe with obituaries
	- demo_df: dataframe with demo info
	- weapons_enum: dictionary with the key as weapon names and values of the weapon numbers in RTCW
	- maxtime_secs: max time in seconds to get a spree
	- include_weapon_filter: list with allowed weapons for the spree, check weapons_enum.py for the correct naming to use
	- exclude_weapon_filter: list with non-allowed weapons for the spree, check weapons_enum.py for the correct naming to use
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
	pd_weapons = []
	pd_spree_length = []
	pd_demo_name = []
	pd_match_name = []
	pd_player_name = []
	pd_demo_pov = []

	#filter the dataframe if we have include weapon filter
	if exclude_weapon_filter != None:
		weapon_numbers_filter = []
		for weapon in exclude_weapon_filter:
			weapon_numbers_filter.append(weapons_enum[weapon])
		weapon_numbers_filter = [item for sublist in weapon_numbers_filter for item in sublist]
		obituary_df = obituary_df.loc[~obituary_df['bWeapon'].isin(weapon_numbers_filter)].copy()

	#filter the dataframe if we have include weapon filter
	if include_weapon_filter != None:
		weapon_numbers_filter = []
		for weapon in include_weapon_filter:
			weapon_numbers_filter.append(weapons_enum[weapon])
		weapon_numbers_filter = [item for sublist in weapon_numbers_filter for item in sublist]
		obituary_df = obituary_df.loc[obituary_df['bWeapon'].isin(weapon_numbers_filter)].copy()

	#filter on only pov player
	obituary_df = pd.merge(obituary_df, demo_df[['szMd5', 'bPOVId']], how = 'left', on = 'szMd5')
	if pov_sprees_only:
		obituary_df = obituary_df.loc[obituary_df['bAttacker'] == obituary_df['bPOVId']]

	#helper variables for verbose
	counter = 0
	total_demos = obituary_df.szMd5.nunique()

	for demo in obituary_df.szMd5.unique():
		df_demo = obituary_df.loc[obituary_df['szMd5'] == demo]
		demo_name = df_demo.demoName.unique()
		match_name = df_demo.matchName.unique()
		demo_pov = df_demo.bPOVId.unique()
		counter += 1
		
		for player in df_demo.bAttacker.unique():
			df_cut = df_demo.loc[obituary_df['bAttacker'] == player]
			player_name = df_cut.szCleanName.unique()
			arr = df_cut.as_matrix(columns = ['bAttacker', 'bTarget', 'bIsTeamkill', 'dwTime', 'bWeapon'])

			timerestriction = maxtime_secs * 1000 #put it in seconds for rtcw time
			spreecounter = 0
			temp_sprees = []
			weapons_used = ''
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
						weapons_used = ''
						temp_sprees.append(first_spreetime)
						weapons_used += str(frag[4]) + '-'
					else:
						spreecounter = 0
						first_spreetime = frag[3]   
						temp_sprees = []
						weapons_used = ''

				#if current frag is in the timerestriction, up the spreecount and append temp_sprees
				if frag[3] - first_spreetime <= timerestriction:
					if (frag[0] != frag[1]) and (frag[2] != 1):
						spreecounter += 1
						temp_sprees.append(frag[3])
						weapons_used += str(frag[4]) + '-'

				#if not, add a value to every list with spree details if minspree is met / reinitilize spreecounter and temp_sprees
				else:
					if spreecounter >= minspree:
						pd_md5.append(demo)
						pd_attacker.append(player)
						pd_start_dwtime.append(temp_sprees[0])
						pd_end_dwtime.append(temp_sprees[-1])
						pd_weapons.append(weapons_used)
						pd_spree_length.append(spreecounter)
						pd_demo_name.append(demo_name[0])
						pd_match_name.append(match_name[0])
						pd_player_name.append(player_name[0])
						pd_demo_pov.append(demo_pov[0])

					if (frag[0] != frag[1]) and (frag[2] != 1):
						spreecounter = 1
						first_spreetime = frag[3]   
						temp_sprees = []
						weapons_used = ''
						temp_sprees.append(first_spreetime)
						weapons_used += str(frag[4]) + '-'

					else:
						spreecounter = 0
						first_spreetime = frag[3]   
						temp_sprees = []
						weapons_used = ''

				#if last frag in the data, and we have reach the minspree, add entry
				if row == (total_rows - 1):
					if spreecounter >= minspree:
						pd_md5.append(demo)
						pd_attacker.append(player)
						pd_start_dwtime.append(temp_sprees[0])
						pd_end_dwtime.append(temp_sprees[-1])
						pd_weapons.append(weapons_used)
						pd_spree_length.append(spreecounter)
						pd_demo_name.append(demo_name[0])
						pd_match_name.append(match_name[0])
						pd_player_name.append(player_name[0])
						pd_demo_pov.append(demo_pov[0])

		if counter % 100 == 0:
			if verbose:
				print 'scanned ' + str(counter) + ' demos of ' + str(total_demos) + ' demos in total'

	print 'all done!'


	#make final dataframe where 1 row is a spree with all the necessary info
	df_spree = pd.DataFrame(
	{'md5': pd_md5,
	 'attacker': pd_attacker,
	 'start': pd_start_dwtime,
	 'end': pd_end_dwtime,
	 'weapons' : pd_weapons,
	 'spreecount': pd_spree_length,
	 'demo': pd_demo_name,
	 'match': pd_match_name,
	 'player': pd_player_name,
	 'pov_id': pd_demo_pov
	})

	if len(df_spree):

		#convert player names to valid names for windows filenaming
		df_spree['player'] = df_spree.player.apply(lambda x: convert_names(x))

		#make sure a buggy demo is not in there
		df_spree = df_spree.loc[df_spree['match'] != 'rtcw_2003.06.25_qcon03-qual_gmpo_vs_clan-carnage_round2'].copy()
		df_spree.reset_index(drop=True, inplace=True)

	return df_spree

########################
# FUNCTIONS TO CUT DEMOS
########################

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


def generate_output_name(spree, demo_type = 'kill', transform_to_dm_60 = True):
	'''
	Helper function to create a filename for a cut demo
	'''
	#output_name = spree['match'] + '_' +  spree['demo'][:-6] + '_' + spree['player'] + '_' + spree['weapons'] + str(spree['start']) + spree['demo'][-6:]
	if demo_type == 'kill':
		output_name = spree['demo'][:-6] + '_' + spree['player'] + '_' + spree['weapons'] + str(spree['start']) + spree['demo'][-6:]
	if demo_type == 'docs':
		output_name = spree['demo'][:-6] + '_' + str(spree['duration']) + '_' + str(spree['start_secsleft']) + '_' + str(spree['end_secsleft']) + '_' + str(spree['won_round']) + '_' + str(spree['start']) + spree['demo'][-6:] 
	
	if demo_type == 'wtv':
		output_name = spree['demo'][:-6] + '_' + str(spree['start']) + '_' + spree['demo'][-6:]

	if transform_to_dm_60:
		output_name = output_name[:-2] + '60'

	#additional replacement 
	output_name = output_name.replace('^', '')
	
	return output_name

def cutter_exe_cmd(root_path, match_folder, demo_name, spree, start_time, end_time, demo_type = 'kill', transform_to_dm_60 = True, 
				   demo_folder_name = 'demos', output_folder = 'output_spree_demos', cut_type = 1):
	'''
	helper function to create string with demo_path and parameters to input in anders libtech 3 api
	'''
	demo_path = os.path.join(root_path, demo_folder_name, match_folder, demo_name)
	output_demo_name = generate_output_name(spree, demo_type, transform_to_dm_60)

	output_path = os.path.join(root_path, output_folder, output_demo_name)
	
	s = 'cut ' + demo_path + ' '
	s += output_path + ' '
	s += str(start_time) + ' '
	s += str(end_time) + ' '
	s += str(cut_type) + ' 0' # plus the zero at the end or the api will crash

	return s

def cut_demos(root_path, demos_dct, df_spree, demo_type = 'kill', offset_start = 5, offset_end = 5, transform_to_dm_60 = True,
	demo_folder_name = 'demos', output_folder = 'output_spree_demos', exe_name = 'Anders.Gaming.LibTech3.exe', cut_type = 1):
	'''
	Function that cuts demos. Offset variables are used to start cut x seconds before and x seconds after the spree
	'''

	for row in range(len(df_spree)):
		spree = df_spree.iloc[row]
		exe_path = os.path.join(root_path, exe_name)
		match_folder, demo_name = locate_demo_path(demos_dct, spree, root_path)

		start_time = spree.start - (offset_start * 1000)
		end_time = spree.end + (offset_end * 1000)

		parameters = cutter_exe_cmd(root_path, match_folder, demo_name, spree, start_time, end_time, demo_type = demo_type, transform_to_dm_60 = transform_to_dm_60,
									demo_folder_name = demo_folder_name, output_folder = output_folder, cut_type = cut_type)

		os.system(exe_path + ' ' + parameters)


###############
# MISCELLANEOUS
###############

def generate_capture_list(df_spree, folder ='C:\Users\Jelle\Documents', demo_type = 'kill', name = 'capture_list.xml', transform_to_dm_60 = True, follow_mode = True):
	'''
	Function that makes a xml capture list to be imported in crumbs his demoviewer. transform_to_dm_60 is used to either save older protocol demos to .dm_60 extension
	'''
	
	df_spree['output_name'] = df_spree.apply(lambda x: generate_output_name(x, demo_type, transform_to_dm_60), axis=1).values
	
	captureList = etree.Element('CaptureList')

	for row in range(len(df_spree)):
		spree = df_spree.iloc[row]
		if demo_type != 'kill':
			spree.attacker = '-1'

		if not follow_mode:
			spree.attacker = '-1'

		capture = etree.Element('capture')
		id = etree.Element('id')
		demoPath = etree.Element('demoPath')
		startFrame = etree.Element('startFrame')
		stopFrame = etree.Element('stopFrame')
		localOffset = etree.Element('localOffset')
		selected = etree.Element('selected')
		playerPov = etree.Element('playerPov')
		config = etree.Element('config')

		id.text = '-1'
		selected.text = 'Yes'
		localOffset.text = '0'
		demoPath.text = spree.output_name
		startFrame.text = str(spree.start - 50000)
		stopFrame.text = str(spree.end + 50000)
		playerPov.text = str(spree.attacker)
		config.text = 'follow' + str(spree.attacker) + '.cfg'

		capture.append(id)
		capture.append(demoPath)
		capture.append(startFrame)
		capture.append(stopFrame)
		capture.append(localOffset)
		capture.append(selected)
		capture.append(playerPov)
		capture.append(config)

		captureList.append(capture)
		
	tree = etree.ElementTree(captureList)
	tree.write(os.path.join(folder,name), pretty_print=True, xml_declaration=True, encoding="utf-8")

def merge_capture_lists(folder ='C:/Users/Jelle/Documents/GIT/rtcw_demo_analyzer/xml', name = 'capture_list_merged.xml'):
	'''
	Function that merges several capture lists in one big capture list. 
	'''
	captureList = etree.Element('CaptureList')
	xml_files = glob.glob(folder +"/*.xml")

	for xml_file in xml_files:
		for data in ElementTree.parse(xml_file).getroot():
			capture = etree.Element('capture')
			id = etree.Element('id')
			demoPath = etree.Element('demoPath')
			startFrame = etree.Element('startFrame')
			stopFrame = etree.Element('stopFrame')
			localOffset = etree.Element('localOffset')
			selected = etree.Element('selected')
			playerPov = etree.Element('playerPov')
			config = etree.Element('config')

			id.text = data.find('id').text
			selected.text = data.find('selected').text
			localOffset.text = data.find('localOffset').text
			demoPath.text = data.find('demoPath').text
			startFrame.text = data.find('startFrame').text
			stopFrame.text = data.find('stopFrame').text
			playerPov.text = data.find('playerPov').text
			config.text = data.find('config').text

			capture.append(id)
			capture.append(demoPath)
			capture.append(startFrame)
			capture.append(stopFrame)
			capture.append(localOffset)
			capture.append(selected)
			capture.append(playerPov)
			capture.append(config)

			captureList.append(capture)

	tree = etree.ElementTree(captureList)
	tree.write(os.path.join(folder,name), pretty_print=True, xml_declaration=True, encoding="utf-8")

def recordings_to_avi(vdub_folder, screenshots_folder, output_folder, vdub_exe, vdub_configfile, remove_screenshots = True):
	'''
	Function to make all tga screenshot recordings to avi's
	'''
	vdub_path = os.path.join(vdub_folder, vdub_exe)
	vdubconfig_path = os.path.join(vdub_folder, vdub_configfile)
	cmdline = vdub_path + ' /s ' + vdubconfig_path
	recordings = os.listdir(screenshots_folder)

	for rec in recordings:
		tgafolder = os.listdir(os.path.join(screenshots_folder, rec))[0]
		tgastartname = os.listdir(os.path.join(screenshots_folder, rec, tgafolder))[3]
		vdubinputloc = os.path.join(screenshots_folder, rec, tgafolder, tgastartname)
		outputfilename = rec[:-6] + '.avi'
		vduboutputloc = os.path.join(output_folder, outputfilename)
		vdubinputline = 'VirtualDub.Open("' + vdubinputloc + '",0,0);\n'
		vduboutputline = 'VirtualDub.SaveAVI("' + vduboutputloc + '");\n'
		vdubinputline = vdubinputline.replace('\\', '\\\\')
		vduboutputline = vduboutputline.replace('\\', '\\\\')

		
		#replace lines in cfg file for input and output
		with open(vdubconfig_path) as f:
			lines = f.readlines()
		
		lines[0] = vdubinputline
		lines[-2] = vduboutputline

		with open(vdubconfig_path, "w") as f:
			f.writelines(lines)
			
		#make avi
		print 'rendering ' + rec
		os.system(cmdline)
		
		if remove_screenshots:
			shutil.rmtree(os.path.join(screenshots_folder, rec))

	print 'all done!'



def hh_mm_ss2seconds(x):
	'''
	Function that splits szTimeString to seconds left in round
	'''
	if x in ('Warmup', 'Countdown', 'Intermission', ''):
		s = -1
	else:
		s = reduce(lambda acc, x: acc*60 + x, map(int, x.split(':')))

	return s

def map_docrun_events(x):

	if x in DocsStolen:
		d = 1
	elif x in DocsReturned:
		d = 0
	elif x in DocsTransmitted:
		d = 2
	else:
		d = -1

	return d
		
def map_dynamite_events(x):

	if x in DynamitePlanted:
		d = 1
	elif x in DynamiteDefused:
		d = 0
	elif x in DynamiteExploded:
		d = 2
	elif x == 'Arming dynamite...':
		d = 3
	elif x == 'Defusing dynamite...':
		d = 4
	else:
		d = -1

	return d

def feature_extraction_chat(chatmessages_df):
	'''
	Function that adds columns with various information about a chatmessage
	'''

	#create boolean columns
	chatmessages_df['WTV'] = chatmessages_df.szMessage.apply(lambda x: bool(re.search('\([0-9]+\):', x))) #wtv chat is typical a string like: 'playername (wtvclientnumb): message'
	chatmessages_df['WTV'] = chatmessages_df['WTV'].astype(int)
	chatmessages_df['DocsAll'] = chatmessages_df.szMessage.isin(DocsAll).astype(int)
	chatmessages_df['DynamiteAll'] = chatmessages_df.szMessage.isin(DynamiteAll).astype(int)
	chatmessages_df['TimelimitHit'] = chatmessages_df.szMessage == 'Timelimit hit.'
	chatmessages_df['TimelimitHit'] = chatmessages_df.TimelimitHit.astype(int)
	chatmessages_df['InMatch'] = ~chatmessages_df['szTimeString'].isin(['Warmup', 'Countdown', 'Intermission', ''])
	chatmessages_df['InMatch'] = chatmessages_df['InMatch'].astype(int)
	#create seconds left in round integer variable
	chatmessages_df['SecondsLeftInRound'] = chatmessages_df.szTimeString.apply(lambda x: hh_mm_ss2seconds(x))

	#map docrun events
	chatmessages_df['DocsEvents'] = chatmessages_df.szMessage.apply(lambda x: map_docrun_events(x))
	chatmessages_df['DynamiteEvents'] = chatmessages_df.szMessage.apply(lambda x: map_dynamite_events(x))

	return chatmessages_df

def get_docruns(chatmessages_df, min_docrun_length = None, max_timeleft = None, docs_succesful = None, min_docs_lost = None, verbose = True):
	
	#empty lists that we will populate and use to make final df
	pd_md5 = []
	pd_start_docrun_dwtime = []
	pd_end_docrun_dwtime = []
	pd_start_docrun_secsleft = []
	pd_end_docrun_secsleft = []
	pd_docrun_duration = []
	pd_times_docs_lost = []
	pd_won_round = []
	pd_demo_name = []
	pd_match_name = []
	
	#helper variables for verbose
	counter = 0
	total_demos = chatmessages_df.szMd5.nunique()
	
	for demo in chatmessages_df.szMd5.unique():
		#evt hier nog cutten op timelimit hit of docsevents zoals cell hierboven voor speed
		df_demo = chatmessages_df.loc[(chatmessages_df['szMd5'] == demo) & (chatmessages_df['InMatch'])]
		demo_name = df_demo.demoName.unique()
		match_name = df_demo.matchName.unique()
		counter += 1
		
		arr = df_demo.as_matrix(columns = ['DocsEvents', 'TimelimitHit', 'dwTime', 'SecondsLeftInRound'])
		taken_docs_bool = False
		docs_lost_times = 0
		
		for row in range(len(arr)):
			chat = arr[row, :]
			
			#taken docs
			if chat[0] == 1:
				if taken_docs_bool == False: 
					start_dwtime = chat[2]
					start_timeleft = chat[3]
					taken_docs_bool = True
				else:
					docs_lost_times += 1

			#transmitted docs
			if chat[0] == 2:
				end_dwtime = chat[2]
				end_timeleft = chat[3]
				taken_docs_bool = False
				docs_succes = True
				
				pd_md5.append(demo)
				pd_start_docrun_dwtime.append(start_dwtime)
				pd_end_docrun_dwtime.append(end_dwtime)
				pd_start_docrun_secsleft.append(start_timeleft)
				pd_end_docrun_secsleft.append(end_timeleft)
				pd_docrun_duration.append(start_timeleft - end_timeleft)
				pd_times_docs_lost.append(docs_lost_times)
				pd_won_round.append(docs_succes)
				pd_demo_name.append(demo_name[0])
				pd_match_name.append(match_name[0])
			
				docs_lost_times = 0
				
			#returned docs / timelimit hit
			if ((chat[0] == 0 or chat[1] == 1) and (taken_docs_bool == True)):
				end_dwtime = chat[2]
				end_timeleft = chat[3]
				taken_docs_bool = False
				docs_succes = False
				
				pd_md5.append(demo)
				pd_start_docrun_dwtime.append(start_dwtime)
				pd_end_docrun_dwtime.append(end_dwtime)
				pd_start_docrun_secsleft.append(start_timeleft)
				pd_end_docrun_secsleft.append(end_timeleft)
				pd_docrun_duration.append(start_timeleft - end_timeleft)
				pd_times_docs_lost.append(docs_lost_times)
				pd_won_round.append(docs_succes)
				pd_demo_name.append(demo_name[0])
				pd_match_name.append(match_name[0])
				
				docs_lost_times = 0
				
			#if demo stopped before end of docrun
			
			
		#verbose shizzle
		if counter % 100 == 0:
			if verbose:
				print 'scanned ' + str(counter) + ' demos of ' + str(total_demos) + ' demos in total' 
	
	print 'all done!'
	
	
	#make final dataframe where 1 row is a spree with all the necessary info
	df_docs = pd.DataFrame(
	{'md5': pd_md5,
	 'start': pd_start_docrun_dwtime,
	 'end': pd_end_docrun_dwtime,
	 'start_secsleft': pd_start_docrun_secsleft,
	 'end_secsleft': pd_end_docrun_secsleft,
	 'duration': pd_docrun_duration,
	 'times_lost_docs': pd_times_docs_lost,
	 'won_round': pd_won_round,
	 'demo': pd_demo_name,
	 'match': pd_match_name,
	})
	
	if min_docrun_length != None:
		df_docs = df_docs.loc[df_docs['duration'] >= min_docrun_length]
		
	if max_timeleft != None:
		df_docs = df_docs.loc[df_docs['end_secsleft'] <= max_timeleft]
		
	if docs_succesful != None:
		df_docs = df_docs.loc[df_docs['won_round'] == docs_succesful]
		
	if min_docs_lost != None:
		df_docs = df_docs.loc[df_docs['times_lost_docs'] >= min_docs_lost]
		
	return df_docs     

def get_wtvmoments(chatmessages_df, z = 5, window = 10, verbose=True):
    pd_md5 = []
    pd_start_wtv = []
    pd_end_wtv = []
    pd_demo_name = []
    pd_match_name = []
    
    #helper variables for verbose
    counter = 0
    total_demos = chatmessages_df.szMd5.nunique()

    for demo in chatmessages_df.szMd5.unique():
        df_demo = chatmessages_df.loc[(chatmessages_df['szMd5'] == demo) & (chatmessages_df['WTV'] == 1)]
        if len(df_demo) > 0:
            demo_name = df_demo.demoName.unique()
            match_name = df_demo.matchName.unique()
            counter += 1

            df_demo['sec'] = df_demo['dwTime'] / 1000
            df_demo['sec'] = df_demo['sec'].astype(int)
            df_demo.sort_values('sec', inplace=True)
            cnt = df_demo.groupby('sec').count()['szMessage'].reset_index()
            cnt.rename(columns = {'szMessage': 'count'}, inplace=True)

            # extrapolate and put zeros for seconds where there is no wtv chat
            base = pd.DataFrame(range(cnt['sec'].min(), cnt['sec'].max() + 1))
            base.rename(columns = {0:'sec'}, inplace=True)
            base['count'] = 0
            cnt = base.merge(cnt, how = 'left', on = 'sec')
            cnt['count'] = cnt['count_y'].fillna(0)
            cnt = cnt[['sec', 'count']]

            # find z-scores
            cnt['z'] = np.abs(stats.zscore(cnt['count']))

            # subset z-scores above certain threshold
            cnt = cnt[cnt['z']> z]

            # keep observations that fall in certain time window
            prev = 0
            lst = []
            for i in cnt['sec']:
                if i - prev > window:
                    lst.append(i)
                prev = i
                
            for i in lst:     
                pd_md5.append(demo)
                pd_start_wtv.append(i * 1000)
                pd_end_wtv.append(i * 1000)
                pd_demo_name.append(demo_name[0])
                pd_match_name.append(match_name[0])
                
            #verbose shizzle
        if counter % 100 == 0:
            if verbose:
                print 'scanned ' + str(counter) + ' demos of ' + str(total_demos) + ' demos in total' 

    print 'all done!'


    #make final dataframe where 1 row is a spree with all the necessary info
    df_wtv = pd.DataFrame(
    {'md5': pd_md5,
     'start': pd_start_wtv,
     'end': pd_end_wtv,
     'demo': pd_demo_name,
     'match': pd_match_name,
    })     
    
    return df_wtv