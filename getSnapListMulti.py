from __future__ import print_function
from vconnector.core import VConnector
from datetime import datetime,timedelta
from time import mktime,time,strftime
from getpass import getpass
import pyVmomi, sys, re
from SnapUtils import Snapshot,VM
#from prettytable import prettytable

def initVars():
	"""Var initialization"""
	global mypwd, myadmin, snapList,now, allSnapsFile,oldSnapsFile
	mypwd=hostReport=''
	myadmin='administrator@vsphere.local'
	debug= False
	snapList = hostList = [] # (vmName, VMHost, VMDatastore, SnapshotName, Snapshot Description, SnapshotAgeinDays)
	
	now = mktime(datetime.utcnow().timetuple())	#Obtain today's date and time
	
	# Obtain credentials
	myinput = input("Username[administrator@vsphere.local]:")
	if (myinput):
		myadmin = myinput
	while (not mypwd):
		mypwd = getpass("Password:")
	#print ("Username:%s\tPassword:%s" % (myadmin,mypwd))

def parseVCList():
	vcList=hostList=''
	while (not vcList):
		vcList = input("vCenter/ESXi (IP/FQDN):")
	
	print("LOL>")
	hostList = vcList.strip().splitlines()
	print (len(hostList))
	#print(hostList[0],hostList[1],hostList[2])
	sys.exit()
	if (',' in vcList or ';' in vcList or '\n' in vcList):
		hostList = re.split(',|;|\n',myvc)
		print('%d hosts detected' % len(hostList))
		for host in hostList:
			print(host)
	
	#return hostList

def openConnection():
	print ("========== %s ==========" % myvc)
	#Open VC Connection
	try:
		client = VConnector(user=myadmin, pwd=mypwd, host=myvc)
		client.connect()
		return client.get_vm_view() #Obtain VMs

	except Exception as exception:
		print (exception.__class__.__name__)
		print ("Unexpected error:", sys.exc_info()[0])
		print ("Please confirm\n1) The vCenter/ESXi is reachable\n2) If FQDN is used, that it is resolvable\n3) Credentials are correct\n")
		hostReport+=myvc+' NOT OK!\n'
		raise exception
		
	print ("Connected to VC %s" % myvc)

def writeSnapFile():
    oldSnapsFile.write("========== VM Snapshot Report ==========\n")
    oldSnapsFile.write("(VM Name, ESXi Host, Datastore, Snapshot Name, Snapshot Description, Snapshot Age)\n") 
    for snap in snapList:
        oldSnapsFile.write(str(snap)+'\n')
    oldSnapsFile.close()
    allSnapsFile.close()
    print ("Files %s and %s successfully written" % (allSnapFilename,oldSnapFilename))

def printSnapReport():
    """Print report"""
    print ("\n========== VM Snapshot Report ==========")
    print ("(VM Name, ESXi Host, Datastore, Snapshot Name, Snapshot Description, Snapshot Age)")
    for snap in snapList:
        print (str(snap))

def getSnapInfo(currVMInfo,vmSnap): 
    """ Obtain snapshot details """
    if debug:
        print ("@getSnapInfo"+str(vmSnap))
    
    if vmSnap:
        snapAge = ( timedelta(seconds=now) -  timedelta(seconds=mktime(vmSnap.createTime.timetuple())) ).days
        
        allSnapsFile.write("Desc: "+str(vmSnap.description))
        if (snapAge >= 4): #If snapshot has 4 days or more
            if debug:
                print ("Snapshot %s longer than 4 days. Days: %d" % (vmSnap.name,snapAge )) 
            snapList.append((currVMInfo[0], currVMInfo[1], currVMInfo[2],vmSnap.name,vmSnap.description,snapAge))
         
        allSnapsFile.write("Snapshot Name: %s\nSnapshot Creation Time: %s\nSnapshot Age (days): %s\n" % (vmSnap.name, vmSnap.createTime,snapAge))
        if debug:
            print (vmSnap.childSnapshotList)
        if vmSnap.childSnapshotList:
            getSnapInfo(currVMInfo,vmSnap.childSnapshotList[0])

def main():
	hostList = parseVCList();
	sys.exit()
	initVars();

	for myvc in hostList:
		#Create the files with date and VC/ESXi
		date = strftime("%d%m%y")
		tofname = myvc + '_' + date
		allSnapFilename = 'allSnapsReport_'+tofname+'.txt'
		oldSnapFilename = 'oldSnapsReport_'+tofname+'.txt'
		oldSnapsFile = open (oldSnapFilename,'w')
		allSnapsFile = open (allSnapFilename,'w')

		#Open VC Connection
		try:
			vms = openConnection(myvc, myadmin, mypwd)
		except:
			continue
		hostReport+=myvc+' OK!\n'

		try:
		# Verify snapshot presence for each VM and print report of those exceeding 4 days
			for currVM in vms.view:
				allSnapsFile.write("===== VM '%s' ===== \n" % (currVM.name))
				if not currVM.snapshot:   #If no snaphots move on
					allSnapsFile.write("No snapshots found!\n")
					continue

				currVMInfo=(currVM.name, str(currVM.runtime.host.name), str(currVM.datastore[0].name) )
				allSnapsFile.write("ESXi Host: %s\nDatastore: %s\n" % (currVMInfo[1], currVMInfo[2]) )
				getSnapInfo(currVMInfo,currVM.snapshot.rootSnapshotList[0]);
			
			printSnapReport(); #Print report to screen with oldVMs only
			writeSnapFile();   #Write all and old VMs to files
		#snap = client.get_object_by_property(property_name='id', property_value=vm.layout.snapshot[0].key, obj_type=pyVmomi.vim.vm.snapshotTree)
		except Exception as exception:
			print("Exception found: "+exception.__class__.__name__)
			print ("Unexpected error:", sys.exc_info()[0])
		client.disconnect()   #close VC connection
		print("\nConnection to VC/ESXi %s closed" % myvc)
	print ("\nAll the following devices have been processed\n"+hostReport)

if __name__ == "__main__":
	main()