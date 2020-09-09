from vconnector.core import VConnector
from datetime import datetime,timedelta
from time import mktime,time,strftime
from getpass import getpass
import pyVmomi, sys, re, os, globals
from SnapUtils import Snapshot,VM
from prettytable import PrettyTable
import csv

def switchFileFormat(format):
	format = {
		1: "txt",
		2: "csv"
	}
	print (format.get(format, "Invalid format"))

def parseVCList():
	""" Parses a multiline string looking for an IP or FQDN and gathers these on a list.

	Returns:
		[list]: [list of detected host IPs or FQDNs to be searched for VMs and its snapshtos]
	"""
	vcList=[]
	print("vCenter/ESXi IP/FQDN (Ctrl+D to escape):")

	# Verify each line and find IP or FQDN, not 100% specific though
	for line in sys.stdin.readlines():
		if re.search(r'\b([0-9]{1,3}\.){3}([0-9]{1,3}){1}\b', line) or re.search(r'\b([a-zA-Z]+\.)+([a-zA-z]+){1}\b', line):
			vcList.append(line.strip())
	
	print('Detected hosts {'+str(len(vcList))+'}: '+','.join(map(str,vcList)))
	
	return vcList

def obtainCreds():
	"""[Collects credentials from the user]

	Returns:
		[str,str]: [Returns the admin user and the password to login to the VC/ESXi]
	"""
	myadmin='administrator@vsphere.local'
	myinput = input("Username[administrator@vsphere.local]:")
	mypwd = ''

	if (myinput): 
		myadmin = myinput
	while (not mypwd):
		mypwd = getpass("Password:")
	if globals.debug:
		print ("Username:%s\tPassword:%s" % (myadmin,mypwd))
	return myadmin,mypwd

def obtainSnapTargetAge():
	"""[Obtains, from the user, the minimum age of snapshot, in days, to be searched for (inclusively)  ]

	Returns:
		[int]: [minimum age of snapshot to be looked for (inclusively)]
	"""
	while True:
		try:
			readValue = input("Snapshot min age (days)[0]:")
			if (re.search(r'[0-9]+',readValue)):
				return int(readValue.strip())
			elif (not readValue):
				return 0
		except ValueError:
			print("Number not recognized. Please insert a whole number:")

def openConnection(myvc,myadmin,mypwd):
	""" Opens a connection to a VC/ESXi 

	Args:
		myvc (str): vCenter/ESXi IP or FQDN 

	Raises:
		exception: [Timeout, Invalid Login, etc]

	Returns:
		[connection,vms]: Returns both the connection open as well as a list of VMs present on the VC/ESXi
	"""
	print ("\n========== %s ==========" % myvc)
	#Open VC Connection
	try:
		client = VConnector(user=myadmin, pwd=mypwd, host=myvc)
		#print("Connecting to %s using account %s" % (myvc,myadmin))
		client.connect()
		vms = client.get_vm_view() 			#Obtain VMs
		globals.hostReport+='-'+myvc+' OK!\n'

		return client,vms

	except Exception as exception:
		print (exception.__class__.__name__)
		print ("Unexpected error:", sys.exc_info()[0])
		print ("Please confirm\n1) The vCenter/ESXi is reachable\n2) If FQDN is used, that it is resolvable\n3) Credentials are correct\n")
		raise exception
		
	print ("Connected to VC %s" % myvc)

def getSnapInfo(currVM,vmSnap,now,targetAge): 
	"""[Obtains snapshot information if its age is longer than the minimum defined snapshot age, in days.
	     Returns the VM object with a list of those snapshots]

	Args:
		currVM ([VM]): [Current VM being analysed]
		vmSnap ([VConnector.vm.snapshottree]): [Snapshot Tree object obtained from vCenter/ESXi]
		now ([mktime]): [Now timestamp in seconds]
		targetAge ([int]): [minimum snapshot age in seconds]

	Returns:
		[VM]: [VM object containing the list of VMs that exceeded the target age]
	"""
	if globals.debug:
		print ("@getSnapInfo"+str(vmSnap))
    
	# If snapshot exists && its age >= target age, extract age in days
	if vmSnap:
		snapAge = ( timedelta(seconds=now).days -  timedelta(seconds=mktime(vmSnap.createTime.timetuple())).days )
		
		if (snapAge >= targetAge): 	
			currSnap = Snapshot(name=vmSnap.name, desc=vmSnap.description,age=snapAge)	# Instantiate snapshot with data
			currVM._snapList.append(currSnap)											# Append to VM 
			
			if globals.debug:
				print ("@getSnapInfo --> Snapshot Age > Target Age. "+currVM.toString())
				print (vmSnap.childSnapshotList)
		
		# Recursively search more snapshots on the VM, if there are any more
		if vmSnap.childSnapshotList:
			getSnapInfo(currVM,vmSnap.childSnapshotList[0],now,targetAge)
	return currVM

def writeToFile(name,text,format):
	"""[Writes to file in the specified format (txt or CSV) a report of VMs with snapshots that exceed the target age]

	Args:
		name ([str]): [VC/ESXi name from where the VMs have been analysed]
		text ([str/List]): [String that contains the report to be written to text file]
		format ([str]): [Format of the file to write to]
	"""
	folderPath = './reports'
	date = strftime("%d%m%y")
	
	#Create folder if does not exist
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
	tofname = name + '_' + date		# Save filename with date
	reportFile = 'reports/snapshotReport_'+tofname+format

	if format.lower() == 'txt' :
		snapReport = open (reportFile,'w')
		snapReport.write(text)
		
	elif format.lower() == 'csv':
		with open(reportFile, 'w', newline='') as snapReport:
			writer = csv.writer(snapReport, delimiter=';')
			writer.writerows(text)
	else:
		print('Unknown file format. No file written nor created.')
		return
	
	snapReport.close()
	print ("File '%s' successfully written" % (reportFile))

def genSnapReport(vcDict):
	"""[Generate the snapshot report in both txt and CSV files. Print the report to the screen as well]

	Args:
		vcDict ([dict]): [Dictionary containing the vCenter/ESXi and its corresponding list of VM objects]
	"""
	reportTable = PrettyTable()
	reportTable.field_names = ["Vm Name", 'Host', 'Datastore', 'Snapshot Name', 'Snapshot Description','Snapshot Age']
	reportList = []
	reportList.append(["Vm Name", 'Host', 'Datastore', 'Snapshot Name', 'Snapshot Description','Snapshot Age'])
	report=''
	
	for vc in vcDict:
		for vm in vcDict[vc]:
			#report+= "%s\n" % (vm.toString())
			for snap in vm._snapList:
				reportTable.add_row([vm._name,vm._host,vm._ds,snap._name,snap._description,snap._age])
				reportList.append([vm._name,vm._host,vm._ds,snap._name,snap._description,snap._age])
				
		report = reportTable.get_string(title=vc)
		writeToFile(vc,report,'txt')
		writeToFile(vc,reportList,'csv')
		
	print(report+'\n')	#Print report to screen