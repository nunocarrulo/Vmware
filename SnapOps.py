from vconnector.core import VConnector
from datetime import datetime,timedelta
from time import mktime,time,strftime
from getpass import getpass
import pyVmomi, sys, re, os, globals
from SnapUtils import Snapshot,VM
from prettytable import PrettyTable

def parseVCList():
	vcList=[]
	print("vCenter/ESXi IP/FQDN (Ctrl+D to escape):")

	# Verify each line and find IP or FQDN, not 100% specific though
	for line in sys.stdin.readlines():

		if re.search(r'\b([0-9]{1,3}\.){3}([0-9]{1,3}){1}\b', line) or re.search(r'\b([a-zA-Z]+\.)+([a-zA-z]+){1}\b', line):
			vcList.append(line.strip())
	
	print('Detected hosts {%d}: ' % len(vcList),end='')
	for vc in vcList:
		print (vc+"; ",end='')
	print()
	if globals.debug:
		print(str(vcList))
	
	return vcList

def obtainCreds():
	global myadmin,mypwd
	myadmin='administrator@vsphere.local'
	mypwd=''
	myinput = input("Username[administrator@vsphere.local]:")

	if (myinput):
		myadmin = myinput
	while (not mypwd):
		mypwd = getpass("Password:")
	if globals.debug:
		print ("Username:%s\tPassword:%s" % (myadmin,mypwd))

def obtainSnapTargetAge():
	while True:
		try:
			readValue = input("Snapshot min age (days)[0]:")
			if (re.search(r'[0-9]+',readValue)):
				return int(readValue.strip())
			elif (not readValue):
				return 0
		except ValueError:
			print("Number not recognized. Please insert a whole number:")

def openConnection(myvc):
	print ("\n========== %s ==========" % myvc)
	#Open VC Connection
	try:
		client = VConnector(user=myadmin, pwd=mypwd, host=myvc)
		#print("Connecting to %s using account %s" % (myvc,myadmin))
		client.connect()
		return client

	except Exception as exception:
		print (exception.__class__.__name__)
		print ("Unexpected error:", sys.exc_info()[0])
		print ("Please confirm\n1) The vCenter/ESXi is reachable\n2) If FQDN is used, that it is resolvable\n3) Credentials are correct\n")
		
		raise exception
		
	print ("Connected to VC %s" % myvc)

def getSnapInfo(currVM,vmSnap,now,targetAge): 
	""" Obtain snapshot details """
	#snap = client.get_object_by_property(property_name='id', property_value=vm.layout.snapshot[0].key, obj_type=pyVmomi.vim.vm.snapshotTree)
	if globals.debug:
		print ("@getSnapInfo"+str(vmSnap))
    
	# If snapshot exists, collect age in days
	if vmSnap:
		snapAge = ( timedelta(seconds=now).days -  timedelta(seconds=mktime(vmSnap.createTime.timetuple())).days )
		#allSnapsFile.write("Desc: "+str(vmSnap.description))
		
		if (snapAge >= targetAge): #If snapshot has targetAge days or more
			currSnap = Snapshot(name=vmSnap.name, desc=vmSnap.description,age=snapAge)	# Instantiate snapshot with data
			currVM._snapList.append(currSnap)											# Append to VM 
			if globals.debug:
				print ("Snapshot %s longer than %d days. Days: %d" % (vmSnap.name,targetAge,snapAge )) 
				#print ("==== Inside after append"+currVM.toString()+"=== INSIDE END")
				print (vmSnap.childSnapshotList)
		
		# Recursively search more snapshots on the VM till there is none
		if vmSnap.childSnapshotList:
			getSnapInfo(currVM,vmSnap.childSnapshotList[0],now,targetAge)
	return currVM

def writeToFile(name,text):
	''' Write to file the snapshot report '''
	folderPath = './reports'
	#Create folder if does not exist
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
	date = strftime("%d%m%y")

	# Save filename with date
	tofname = name + '_' + date
	reportFile = 'reports/snapshotReport_'+tofname+'.txt'
	snapReport = open (reportFile,'w')
	snapReport.write(text)
	snapReport.close()
	print ("File '%s' successfully written" % (reportFile))

def genSnapReport(vcDict):
	"""Print & Write Snapshot Report"""
	reportTable = PrettyTable()
	reportTable.field_names = ["Vm Name", 'Host', 'Datastore', 'Snapshot Name', 'Snapshot Description','Snapshot Age']

	#report = ''
	#report+="\n========== VM Snapshot Report ==========\n"
	for vc in vcDict:
		#report+="========== %s ==========\n" % (vc)
		for vm in vcDict[vc]:
			#report+= "%s\n" % (vm.toString())
			#reportTable.title = "Oh well"
			for snap in vm._snapList:
				reportTable.add_row([vm._name,vm._host,vm._ds,snap._name,snap._description,snap._age])
		
		report = reportTable.get_string(title=vc)
		writeToFile(vc,report)
		
	print(report+"\n")	#Print report to screen