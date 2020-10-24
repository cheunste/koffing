import unittest
import koffing
import wmi
import os
import shutil
import time
import koffing
import sqlite3


class KoffingTestCases(unittest.TestCase):
	process_name = "notepad.exe"
	test_koffing = koffing.Koffing(None, None, None)

	def test_ping_response(self):
		ping_response = self.test_koffing.get_ping_response_in_ms("mehwhatever.duckdns.org")
		self.assertTrue(ping_response < 200, "ping responses is greater than 200")

	def test_get_service(self):
		service_name = self.test_koffing.get_service("Telephony")
		self.assertTrue(service_name is not None)

	def test_pause_service(self):
		some_service = "TapiSrv"
		accepted_status_code = 0
		already_paused_status = 24
		status_code = self.test_koffing.pause_service(some_service)[0]
		self.assertTrue(status_code == already_paused_status or status_code == accepted_status_code,
			f"Status code is {status_code} implies service is not paused")

	def test_resume_service(self):
		some_service = "TapiSrv"
		accepted_status_code = 0
		already_running_status = 10
		status_code = self.test_koffing.resume_service(some_service)[0]
		self.assertTrue(status_code == already_running_status or status_code == accepted_status_code,
			f"Status code is {status_code} implies service is not running")

	def test_get_machine(self):
		connection = self.test_koffing.get_machine_connection()
		self.assertTrue(connection is not None)

	def test_kill_process(self):
		process_id, return_value = wmi.WMI().Win32_Process.Create(CommandLine=self.process_name)
		self.test_koffing.terminate_process(self.process_name)
		self.find_process(self.process_name)

	def test_get_file_path(self):
		self.create_a_test_process()
		self.test_koffing.terminate_process(self.process_name)
		self.find_process(self.process_name)
		file_paths = self.test_koffing.get_file_paths(self.process_name)
		for path in file_paths:
			self.assertTrue(path == "C:\\WINDOWS\\system32\\notepad.exe")
		self.test_koffing.terminate_process(self.process_name)

	def test_no_file_paths(self):
		file_paths = self.test_koffing.get_file_paths(self.process_name)
		self.assertTrue(not file_paths)
		return

	def test_replace_file(self):
		self.test_koffing.replace_file("DummySource\\test.txt", "DummyDest\\test.txt")
		self.verify_copied_file()

	def test_format_returned_file_path(self):
		expected_file_paths = ['D:\\Program Files\\IBERINCO\\ZubatKara1\\Zubat.exe',
		                       'D:\\Program Files\\IBERINCO\\ZubatKara2\\Zubat.exe',
		                       'D:\\Program Files\\IBERINCO\\ZubatKara3\\Zubat.exe']
		for path in expected_file_paths:
			full_unc_path = self.test_koffing.reformat_path_to_unc(path)
			path_slice = path[2:]
			correct_path = f"\\\\None\\D${path_slice}"
			self.assertTrue(full_unc_path == correct_path)

	def test_check_sql_file(self):
		self.assertTrue( koffing.sql_file_exists("./Koffing.sql"))

	def test_read_from_sql_script(self):
		self.assertIsNotNone(koffing.read_sql_script_content("./Koffing.sql"))

	def test_update_database(self):
		database_path = r"./ZubatConfiguration.db"
		script_path = r"./Koffing.sql"

		script_content = koffing.read_sql_script_content(script_path)
		self.test_koffing.update_database(database_path, script_content)
		conn = sqlite3.connect(database_path)
		for row in conn.cursor().execute("SELECT DefaultValue from SystemInputTags where Description='UTCOffset'"):
			utc_value_from_db = row[0]

		for row in conn.cursor().execute("SELECT DefaultValue from SystemInputTags where Description='Timeout'"):
			timeout_from_db = row[0]
		conn.close()

		self.assertTrue(utc_value_from_db == "-9")
		self.assertTrue(timeout_from_db == "10")

	def test_get_zubat_directories(self):
		#Assume this is a list of files in the XXXX directory
		current_directory_listing = os.listdir('.')
		current_directory_listing.append('Zubat-XXXXX')
		current_directory_listing.append('Zubat-YYYYY')
		current_directory_listing.append('Zubat')
		list_of_zubat_folders = koffing.zubat_folders_in_path(current_directory_listing)
		#There can be more Zubat files in the directory mainly because of all the stuf you have in this folder
		self.assertTrue(len(list_of_zubat_folders) >= 3)

	### Private methods here

	def create_a_test_process(self):
		wmi.WMI().Win32_Process.Create(CommandLine=self.process_name)

	def find_process(self, process_name):
		for process in wmi.WMI().Win32_Process(name=process_name):
			self.fail("Test failed. There should be no process here")

	def verify_copied_file(self):
		mtime_dest = os.stat("DummyDest\\test.txt").st_mtime
		mtime_source = os.stat("DummySource\\test.txt").st_mtime
		print("Dest last modified: %s" % time.ctime(mtime_dest))
		print("Source last modified: %s" % time.ctime(mtime_source))
		self.assertTrue(mtime_dest > mtime_source)

class FileHandlerTest(unittest.TestCase):

	def test_read_txt_file(self):
		site_list = koffing.get_list_of_zubat_sites_from_file()
		self.assertTrue(len(site_list)>4)
		print(site_list)




if __name__ == '__main__':
	unittest.main()
