import ping3
import win32serviceutil
import wmi
import os
import win32api
import shutil
import win32wnet
import logging
import time
import sqlite3


class Koffing:
	password = ""
	username = ""
	machine_name = None
	ft = None

	def __init__(self, machine_name, username, password):
		self.machine_name = machine_name
		self.username = username
		self.password = password

	def get_ping_response_in_ms(self, ip_address, packet_size=20):
		return ping3.ping(ip_address, unit='ms', size=packet_size)

	def set_password(self, password):
		self.password = password

	def set_user(self, username):
		self.username = username

	def set_machine_name(self, machine_name):
		self.machine_name = machine_name
		logging.debug(f"Setting destination machine name to {machine_name}")

	def get_machine_connection(self):
		if self.machine_name is None:
			return wmi.WMI()
		return wmi.WMI(self.machine_name)

	def get_service(self, service_name):
		logging.debug(f"Attempting to get service: {service_name} from {self.machine_name}")
		return self.get_machine_connection().Win32_Service(Name=service_name)

	def pause_service(self, service_name):
		c = self.get_machine_connection()
		state = 0
		for service in c.Win32_Service(Name=service_name):
			state = service.PauseService()
			logging.debug(f"Pausing service: {service_name} on {self.machine_name}. Status: {state}")
		return state

	def resume_service(self, service_name):
		c = self.get_machine_connection()
		state = 0
		for service in c.Win32_Service(Name=service_name):
			state = service.ResumeService()
			logging.debug(f"resuming service: {service_name} on {self.machine_name}. Status: {state}")
		return state

	def terminate_process(self, process_name):
		client = self.get_machine_connection()
		all_processes = client.Win32_Process(Description=f"{process_name}".format(process_name))
		for process in all_processes:
			try:
				process.Terminate()
			except:
				logging.error(f"Failed to terminate {process_name} with process details: {process}")
		return

	def get_file_paths(self, process_name):
		return [process.ExecutablePath for process in
		        self.get_machine_connection().Win32_Process(Description=f"{process_name}".format(process_name))]

	def reformat_path_to_unc(self, process_file_path):
		return f"\\\\{self.machine_name}\\{process_file_path}".replace(':', '$')

	def replace_file(self, source_path, dest_path):
		try:
			shutil.copy(source_path, dest_path)
		except Exception as err:
			print(f"failed to copy file to {dest_path}. Error {err}")
			logging.error(f"failed to copy file to {dest_path}. Error {err}")
		return

	def update_database(self,database_file_path,script_content):
		db = sqlite3.connect(database_file_path)
		try:
			db.cursor().executescript(script_content)
		except:
			logging.debug("Issue detected when attempt to update the database")

		db.commit()
		db.close()

	def is_service_running(self, service):
		return win32serviceutil.QueryServiceStatus(service, self.machine_name)[1] == 4




def get_list_of_sites_from_file():
	f = open('ZubatUccList.txt', 'r')
	with(f):
		site_list = [site.replace("\n", "") for site in f]
	return site_list


def read_sql_script_content(script_path):
	with open(script_path,'r') as sql_file:
		sql_script = sql_file.read()
	return sql_script

def check_file_exists(file):
	return os.path.exists(file)


def sql_file_exists(sql_file):
	logging.debug(f"Sql file detected. Will be updating database along with Zubat")
	return os.path.exists(sql_file)

def zubat_folders_in_path(path):
	return [files for files in path if 'Zubat' in files]


if __name__ == "__main__":
	logging.basicConfig(filename="koffing.log", level=logging.DEBUG)
	file_list = get_list_of_sites_from_file()
	service = "Watchdog"
	process = "Zubat.exe"
	file = f".//Zubat.exe"
	sql_script_path = r"./Koffing.sql"
	sample_packet_size = 50
	max_acceptable_ping_response = 500
	parse_sql = sql_file_exists(sql_script_path)

	if parse_sql:
		script_content = read_sql_script_content(sql_script_path)

	if not check_file_exists(file):
		logging.error(f"{file} does not exist in the current directory, please make sure it is before running.")
	else:
		#Check if SQL file eixsts
		for hostname in file_list:
			print(hostname)
			## Create new Koffing
			koffing = Koffing(hostname, None, None)
			##check ping
			# ping_responses = koffing.get_ping_response_in_ms(hostname, sample_packet_size)
			# if ping_responses > max_acceptable_ping_response:
			#	logging.error(
			#		f"Ping responses to {hostname} is {ping_responses}, which is kinda high. Going to skip this site.")
			#	continue
			## Stop the watchdogt sevice
			koffing.pause_service(service)

			## Get the path of all the processes
			process_file_path = koffing.get_file_paths(process)
			## Kill all running process
			koffing.terminate_process(process)
			## Replace the Zubat.exe file
			logging.debug(f"process file paths: {process_file_path}")

			for file_path in process_file_path:
				logging.debug(f"attempting to replace {file_path}")
				new_file_path = koffing.reformat_path_to_unc(file_path)
				koffing.replace_file(f".//{file}", new_file_path)
				if parse_sql:
					logging.debug(f"Updating Database for {hostname}")
					database_path = f"{new_file_path}\\Database\\ZubatConfiguration.db"
					logging.debug(f"Updating the database in {database_path}")
					koffing.update_database(database_path,script_content)

			if len(process_file_path) == 0:
				logging.error("No Instance of Zubat Running. Attempting to Get the folders from the directory instead.")
				d_path = fr"\\{hostname}\D$\Program Files\IBERINCO"
				zubat_folders = zubat_folders_in_path(d_path)
				if(len(zubat_folders) == 0):
					logging.error(f"No Zubat folders found in {hostname}'s D drive. Is Zubat deployed to {hostname}?")
				else:
					for zubat in zubat_folders:
						logging.debug(f"Attempting to replace Zubat.exe in {hostname}'s {d_path}")
						new_file_path = d_path+f"\{zubat}"
						koffing.replace_file(f".//{file}", new_file_path)


			## start back up the watchdog server
			koffing.resume_service(service)
