class Block(object):
	PART_WAITING = 0
	PART_DOWNLOADING = 1
	PART_PAUSED = 2
	PART_FINISHED = 3
	PART_WRITTED = 4
	
	def __init__(self, start, end, data):
		self.start = start
		self.end = end
		self.data = data
		self.current = start
		self.state = Block.PART_WAITING
		self.record = []
	
	def __str__(self):
		return "Block(start:{},end:{})".format(self.start, self.end)


class Cache(object):
	def __init__(self, writer, unit, blocks, total):
		self.__block_list = []
		self.end = total
		self.writer = writer
		self.__init_blocks(unit, blocks, total)
	
	def set_finish_at(self, end):
		self.end = end
		self.__init_empty_file()
	
	def reinitialize(self):
		for part in self.__block_list:
			if part.data is not None:
				del part.data
		self.__block_list.clear()
		self.end = 0
	
	def __init_empty_file(self):
		for i in range(self.end):
			self.writer.write(b"0")
	
	def __init_blocks(self, unit, number, total):
		for i in range(0, total, unit):
			if i == unit * (number - 1):
				self.__block_list.append(Block(i, total, None))
			else:
				self.__block_list.append(Block(i, i + unit, None))
	
	def put(self, start, data):
		for block in self.__block_list:
			if block.start == start:
				block.data = data
				break
		self.__flush()
	
	def close(self):
		self.__check()
		self.writer.close()
	
	@property
	def window(self):
		return self.__block_list
	
	def __flush(self):
		for block in self.__block_list:
			if block.end > self.end:
				return
			if block.data is not None:
				self.writer.seek(block.current, 0)
				self.writer.write(block.data)
				block.record.append((block.current, block.current + len(block.data)))
				block.current += len(block.data)
				block.data = None
	
	def __check(self):
		current = 0
		for block in self.__block_list:
			for record in block.record:
				if current == record[0]:
					current = record[1]
				else:
					raise Exception("Block " + str(block) + " not continuous.")
	
	def __str__(self) -> str:
		result = []
		for part in self.__block_list:
			result.append("({}\t{}-{}\tstate:{}\tlength:{})".format(part.hash,
			                                                        part.start,
			                                                        part.end,
			                                                        part.state,
			                                                        len(part.data)))
		return "\n".join(result)
