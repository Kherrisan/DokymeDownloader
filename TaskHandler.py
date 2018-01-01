from Cache import Cache
import aiohttp
import asyncio
import requests
from multiprocessing import Process
from Hashor import hashor


class TaskHandler(Process):
	WAITING = 0
	PREPARING = 1
	DOWNLOADING = 2
	PAUSED = 3
	FINISHED = 4
	
	def __init__(self, url, part_number):
		Process.__init__(self)
		self.part_number = part_number
		self.url = url
		self.unit = 0
		self.state = TaskHandler.WAITING
		self.file_hash = ""
		self.cache = None
		self.file_name = None
		self.accumulate = 0
		self.content_length = 0
		self.on_start = None
		self.on_prepare = None
		self.on_pause = None
		self.on_continue = None
		self.on_download = None
		self.on_finish = None
	
	def run(self):
		self.__on_start()
		self.__download()
	
	async def __worker(self, start, end):
		if start == end:
			return
		print("Worker {}-{}".format(start, end))
		resped = False
		headers = {"Range": "bytes={}-{}".format(start, end - 1)}
		with aiohttp.ClientSession() as session:
			while not resped:
				async with session.get(self.url, headers=headers) as response:
					while True:
						if response.status == 429:
							asyncio.sleep(10)
							break
						resped = True
						if self.state == TaskHandler.PAUSED:
							asyncio.sleep(1)
							continue
						chunk = await response.content.read(4096)
						if not chunk:
							break
						self.cache.put(start, chunk)
						self.accumulate += len(chunk)
						self.__print_progress()
	
	def __prepare(self):
		self.__on_prepare()
		self.__get_file_name()
		response = requests.head(self.url)
		self.content_length = int(response.headers["Content-Length"])
		self.unit = int(self.content_length / self.part_number)
		file = open(self.file_name, "wb")
		self.cache = Cache(file, self.unit, self.part_number, self.content_length)
	
	def __download(self):
		self.__prepare()
		async_tasks = []
		for i in range(0, self.part_number * self.unit, self.unit):
			if i == self.unit * (self.part_number - 1):
				async_tasks.append(self.__worker(i, self.content_length))
			else:
				async_tasks.append(self.__worker(i, i + self.unit))
		loop = asyncio.get_event_loop()
		loop.run_until_complete(asyncio.wait(async_tasks))
		loop.close()
		self.cache.close()
		self.__finish()
	
	def __print_progress(self):
		print("Progress:{}%".format(self.accumulate * 100.0 / self.content_length))
	
	def __get_file_name(self):
		l = self.url.rindex("/")
		r = self.url.find("?")
		if r == -1:
			self.file_name = self.url[l + 1:]
		else:
			self.file_name = self.url[l + 1:r]
	
	def __finish(self):
		with open(self.file_name, "rb") as file:
			self.file_hash = hashor.hash(file.read())
			print(self.file_hash)
		self.__on_finished()
	
	def pause(self):
		self.__on_pause()
	
	def continue_(self):
		self.__on_continue()
	
	def __on_finished(self):
		self.state = TaskHandler.FINISHED
		pass
	
	def __on_start(self):
		pass
	
	def __on_pause(self):
		self.state = TaskHandler.PAUSED
		pass
	
	def __on_continue(self):
		self.state = TaskHandler.DOWNLOADING
		pass
	
	def __on_prepare(self):
		self.state = TaskHandler.PREPARING
		pass
	
	def __on_download(self):
		self.state = TaskHandler.DOWNLOADING
		pass
	
	def __str__(self):
		return "Task(filename:{},content-length:{},downloaded:{})".format(self.file_name, self.content_length,
		                                                                  self.accumulate)


if __name__ == '__main__':
	test_url = "http://mirrors.ustc.edu.cn/node/v9.3.0/node-v9.3.0-x64.msi"
	test_url_2 = "https://nodejs.org/dist/v8.9.3/node-v8.9.3-x64.msi"
	task = TaskHandler(test_url, 5)
	print("START")
	task.start()
	task.join()
	print("FINISH")
