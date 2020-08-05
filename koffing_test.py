import unittest
import koffing
import wmi
import os
import shutil
import time
import koffing


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
		some_service = "telephony"
		accepted_status_code = 0
		already_paused_status = 24
		status_code = self.test_koffing.pause_service(some_service)[0]
		self.assertTrue(status_code == already_paused_status or status_code == accepted_status_code,
			f"Status code is {status_code} implies service is not paused")

	def test_resume_service(self):
		some_service = "telephony"
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
		site_list = koffing.get_list_of_sites_from_file()
		self.assertTrue(len(site_list)>4)
		print(site_list)




if __name__ == '__main__':
	unittest.main()
