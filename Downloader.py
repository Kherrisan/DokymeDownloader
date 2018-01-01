from TaskHandler import TaskHandler


class Downloader(object):
	def __init__(self):
		self.thread_number = 5
		self.task_list = []
	
	def download(self, url, thread_number=None):
		if not thread_number:
			thread_number = self.thread_number
		task = TaskHandler(url, thread_number)
		self.task_list.append(task)
		task.start()
