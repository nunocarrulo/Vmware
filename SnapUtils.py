class Snapshot:
	def __init__(self, name='', desc='', age=0):
		self._name = name
		self._description = desc
		self._age = age
        #print('Snapshot object created!')

	@property
	def name():
		return self._name
    
	@property
	def description():
		return self._description
    
	@property
	def age():
		return self._age

	@name.setter
	def setName(name):
		self._name = name 

	@description.setter
	def setDescription(desc):
		self._description = desc 

	@age.setter
	def setAge(age):
		self._age = age

	def toString(self, indent='|-'):
		snapDet = "%sSnap Name:%s\tSnap Desc:%s\tSnap Age:%d\n" % (indent,self._name,self._description,self._age)
		return snapDet

class VM:
    
	def __init__(self, name='', host='', ds='', snapList=[]):
		self._name = name
		self._host = host
		self._ds = ds
		self._snapList = snapList 
		#print('VM object created!')

	@property
	def name():
		return self._name
    
	@property
	def host():
		return self._host
    
	@property
	def ds():
		return self._ds

	@property
	def snapList():
		return self._snapList

	@name.setter
	def setName(name):
		self._name = name 

	@host.setter
	def setHost(host):
		self._host = host

	@ds.setter
	def setDS(ds):
		self._ds = ds

	@snapList.setter
	def setsnapList(snapList):
		self._snapList = snapList

	def toString(self):
		vmDet = "VM Name:%s\nHost:%s\nDS:%s\n" % (self._name,self._host,self._ds)
		for i,snap in enumerate(self._snapList):
			indent='|'+(i+1)*'-'
			vmDet+='|\n'+snap.toString(indent)
		return vmDet