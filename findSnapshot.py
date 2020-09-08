from __future__ import print_function
from vconnector.core import VConnector
from datetime import datetime,timedelta
from time import mktime,time,strftime
from getpass import getpass
from SnapUtils import Snapshot,VM
from globals import debug
from SnapOps import *
import pyVmomi, sys, re, os


def initVars():
	"""Var initialization"""
	global now, targetAge, vcDict
	now = mktime(datetime.utcnow().timetuple())	#Obtain today's date and time
	targetAge = 0
	vcDict = {}

def main():
	initVars(); 						# Global Vars
	vcList = parseVCList();				# Parse VC/ESXi List
	obtainCreds();						# Obtain Credentials
	targetAge = obtainSnapTargetAge()	#Obtain min snapshot age to collect
	
	# For each VC/Host find VMs and its snapshots
	for myvc in vcList:
		vmList = []			#new VM List per VC/ESXi
		try:
			client = openConnection(myvc)	#Open VC Connection
			vms = client.get_vm_view() 			#Obtain VMs
			globals.hostReport+='-'+myvc+' OK!\n'

			print("Connected to VC/ESXi: %s" % (myvc))
			# Verify snapshot presence for each VM and print report of those exceeding 4 days
			for currVM in vms.view:
				print("-%s" % (currVM.name))
				if not currVM.snapshot:   #If no snaphots move on
					#print("%s - No snapshots found!\n", currVM.name)
					continue
				
				myVM = VM(name=currVM.name,host=str(currVM.runtime.host.name),ds=str(currVM.datastore[0].name), snapList=[])	# Create VM object
				myVM = getSnapInfo(myVM,currVM.snapshot.rootSnapshotList[0],now,targetAge)										# Obtain  snapshots from VM
				vmList.append(myVM);

		#snap = client.get_object_by_property(property_name='id', property_value=vm.layout.snapshot[0].key, obj_type=pyVmomi.vim.vm.snapshotTree)
		except Exception as exception:
			print("Exception found: "+exception.__class__.__name__+" : "+str(exception))
			#print("Unexpected error:", sys.exc_info()[0])
			globals.hostReport+='-'+myvc+' NOT OK!\n'
			continue
		
		vcDict [myvc] = vmList	#  Create dictionary entry for new vCenter
		client.disconnect()   	# Close VC connection
		print("\nConnection to VC/ESXi %s closed" % myvc)
	
	#print("Dictionary size %d" % (len(vcDict)))
	genSnapReport(vcDict); #Print report to screen with oldVMs only
	print ("\nAll the following devices have been processed\n"+globals.hostReport)

if __name__ == "__main__":
	main()