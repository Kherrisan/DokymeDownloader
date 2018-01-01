import hashlib


class Hashor(object):
	def __init__(self):
		self.hashlib = hashlib.sha256()
	
	def hash(self, obj):
		self.hashlib.update(obj)
		return self.hashlib.hexdigest()
	
	def summary(self, obj):
		return self.hash(obj)[:6]


hashor = Hashor()
