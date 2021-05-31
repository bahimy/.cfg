#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os,sys,shutil
import datetime
import argparse
import time
import threading
import lxml.etree as etree

import logging
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
from jinja2 import Template

ovf_namespaces = {
	'ovf': 'http://schemas.dmtf.org/ovf/envelope/1/',
	'rasd': "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData",
	'vssd': "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData",
	'xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }

rasd_hw_types = {
	"0": {"name": "reserved", "single": False, "numeric": False},
	"1": {"name": "other", "single": False, "numeric": False},
	"2": {"name": "computer_cystem", "single": True, "numeric": False},
	"3": {"name": "processor", "single": True, "numeric": True},
	"4": {"name": "memory", "single": True, "numeric": True},
	"5": {"name": "ide_controller", "single": False, "numeric": False},
	"10": {"name": "ethernet_adapter", "single": False, "numeric": False},
	"11": {"name": "other_network_adapter", "single": False, "numeric": False},
	"14": {"name": "floppy", "single": False, "numeric": False},
	"15": {"name": "cd_drive", "single": False, "numeric": False},
	"16": {"name": "dvd_drive", "single": False, "numeric": False},
	"17": {"name": "disk_drive", "single": False, "numeric": False},
	"20": {"name": "ovirt_graphics_controller", "single": False, "numeric": False},
	"21": {"name": "serial_port", "single": False, "numeric": False},
	"22": {"name": "parallel_port", "single": False, "numeric": False},
	"23": {"name": "usb_controller", "single": False, "numeric": False},
	"24": {"name": "graphics_controller", "single": False, "numeric": False},
	"26": {"name": "graphical_framebuffer", "single": False, "numeric": False}
}

additional_info_fields = {
	"memory" : ["MaxMemorySizeMb", "MinAllocatedMem"],
	"processor" : ["CustomCpuName", "UseHostCpu"]
}

mem_size_map = {
	"KiloBytes" : "KB",
	"KibiBytes" : "KiB",
	"MegaBytes" : "M",
	"MebiBytes" : "MiB",
	"GigaBytes" : "GB",
	"GibiBytes" : "GiB"
}

#0902
storage_paths = {
	"cephfs_ssd": "/rhev/data-center/mnt/192.168.5.7:6789:_engine0902",
	"cephfs_hdd": "/rhev/data-center/mnt/192.168.5.1:6789:_engine0902"
}

def login(url, user, password, ca=None, insecure=True ):
	return sdk.Connection(
		url=url,
        username=user,
        password=password,
        ca_file=ca,
        insecure=insecure,
        debug=True,
        log=logging.getLogger(),
		)

def parse_vm_xml(config):
	data = etree.fromstring(config)

	disks_section = data.xpath('.//Section[@xsi:type="ovf:DiskSection_Type"]', namespaces=ovf_namespaces)[0]
	disk_entrances = disks_section.findall('Disk')
	disks = {}
	for de in disk_entrances:
		disk_id = de.attrib.get("{%s}diskId" % ovf_namespaces["ovf"])
		disks[disk_id] = { k.split("}")[1] : v for k,v in de.items() }
	print(disks)

	nics_section = data.xpath('.//NetworkSection', namespaces=ovf_namespaces)[0]
	nic_entrances = nics_section.findall('Network')
	print("{%s}name" % ovf_namespaces["ovf"])
	nics = [nic.get("{%s}name" % ovf_namespaces["ovf"]) for nic in nic_entrances]
	print(nics)

	vm_data = {item["name"] : [] for _,item in rasd_hw_types.items() }
	vm_data.update({"controller" : [], "channel" : [], "sound" : [], "rng" : [], "balloon" : []})
	parsed_vm_data = []
	vm_data_section = data.xpath('.//Section[@xsi:type="ovf:VirtualHardwareSection_Type"]', namespaces=ovf_namespaces)[0]
	vm_data_entrances = vm_data_section.findall('Item')
	for ve in vm_data_entrances:
		res_type = ve.findall("{%s}ResourceType" % ovf_namespaces["rasd"])
		if res_type:
			res_type = res_type[0]
			res_text = res_type.text
			resource = rasd_hw_types.get(res_text)
			if resource:
				parsed_vm_data.append({item.tag.replace("{%s}" % ovf_namespaces["rasd"],""):item.text for item in ve })
				specparams = ve.find("SpecParams")
				if specparams:
					parsed_vm_data[-1]["SpecParams"] = {item.tag:item.text for item in specparams}
				p_address = parsed_vm_data[-1].get("Address")
				if p_address:
					tmp_address = p_address.strip("}{").replace(" ", "")
					address = " ".join(["%s=\"%s\"" % (elem.split("=")[0],elem.split("=")[1]) for elem in tmp_address.split(",")])
					parsed_vm_data[-1]["Address"] = address
			else:
				print("Unknown resource type of %s" % res_text)
	for de in parsed_vm_data:
		res_type = de["ResourceType"]
		if not res_type == "0":
			vm_data[rasd_hw_types[res_type]["name"]].append(de)
		elif de["Type"] in vm_data.keys():
			vm_data[de["Type"]].append(de)

	# gather some additional data
	for dep,fields in additional_info_fields.items():
		for field in fields:
			result = data.xpath("//%s" % field)
			if result and result[0].text:
				vm_data[dep][0][field] = result[0].text
	print(vm_data)
	return disks,nics,vm_data


def render_xml(templatefile, disks, nics, vm_data, vm_name):
	with open(templatefile, "r") as file:
		tpl = Template(file.read())
		result = tpl.render(disks=disks,nics=nics,vm_data=vm_data,vm_name=vm_name,mem_map=mem_size_map,storage_type="rbd",storage_pool="rbd")
	return result

def create_snapshot(snap_service):
	snap = snap_service.add(types.Snapshot(description='My snapshot',persist_memorystate=False),wait=True)
	sid = snap.id
	print("Waiting for snapshot to complete...")
	while True:
		time.sleep(5)
		if not 'locked' in [s.snapshot_status.value for s in snap_service.list()]:
			break
	return snap

def main(received_args):
	parser = argparse.ArgumentParser(description="Ovirt to KVM migraton tool")
	parser.add_argument('-e', action='store', dest='url', help='Ovirt API Endpoint Url', required=True)
	parser.add_argument('-u', action='store', dest='user', help='Ovirt API login user', required=True)
	parser.add_argument('-p', action='store', dest='password', help='Ovirt API password password', required=True)
	parser.add_argument('-n', action='store', dest='vm_name', help='VM name to migrate', required=True)
	parser.add_argument('-d', action='store', dest='destination_folder', help='Destination folder for migration (temporary storage)', required=True)
	# parser.add_argument('-c', action='store', dest='count', help='mail count', type=int, default=1)
	# parser.add_argument('-f', action='store', dest='filename', help='Email attachment')
	# parser.add_argument('-a', action='store_true', dest='async', help='Run async')
	# parser.add_argument('-R', action='store', dest='recipients_file', help='Recipients_file')
	args = parser.parse_args(received_args)
	args = vars(args)

	connection = login(args["url"], args["user"], args["password"])
	vms_service = connection.system_service().vms_service()
	vm = vms_service.list(search="name=%s" % args["vm_name"], all_content=True)
	if not vm:
		print("VM {} does not exist. Exiting...".format(args["vm_name"]))
		sys.exit(1)
	vm = vm[0]
	vm_service = vms_service.vm_service(vm.id)
	snap_service = vm_service.snapshots_service()
	diskattachment_service = vm_service.disk_attachments_service()



	vm_status = vm.status.value
	if vm_status == "up" and len(snap_service.list()) > 1:
		print("Vm has snapshots, this mode is not supported yet. Exiting...")
		sys.exit(1)
	snaps_map = {snap.id: snap.description for snap in snap_service.list()}
	print(snaps_map)

	templatefile = args["template"] if args.get("template") else "domain.j2"
	disks,nics,vm_data = parse_vm_xml(vm.initialization.configuration.data.encode("utf-8"))
	fin_xml = render_xml(templatefile, disks, nics, vm_data, args["vm_name"])
	print(fin_xml)

	disk_paths_to_copy = []
	disks_from_api = [connection.follow_link(_disk.disk) for _disk in diskattachment_service.list()]
	for disk in disks_from_api:
		disk_storage = connection.follow_link(disk.storage_domains[0])
		storage_base_path = storage_paths.get(disk_storage.name)
		print(storage_base_path, disk_storage.name, disk_storage.id , disk.id)
		for di, dd in disks.items():
			if disk.id == dd["fileRef"].split("/")[0]:
				disk_paths_to_copy.append("%s/%s/images/%s/%s" % (storage_base_path, disk_storage.id, disk.id, dd["fileRef"].split("/")[1]))
	print(disk_paths_to_copy)

	snap = None
	if vm_status == "up":
		print("Vm is running. Creating snapshot now ...")
		snap = create_snapshot(snap_service)
	elif vm_status != "down":
		print("VM is in some transitional state. Either wait until it completely boots/will shut down or shut i down by hand. Exiting now...")
		print("Current VM state is %s" % vm_status)
		sys.exit(1)

	d_folder = "%s/%s" % (args["destination_folder"], args["vm_name"])
	print("Creating destination folder ...")
	os.mkdir(d_folder)
	print("Start copying disks to destination folder...")
	for dfile in disk_paths_to_copy:
		shutil.copy(dfile, d_folder)
	print("Rendering xml templates...")
	with open("%s/%s.xml" % (d_folder, args["vm_name"]), "w") as xmlfile:
		xmlfile.write(fin_xml)
	with open("import_script.j2", "r") as import_sc_file:
		tpl = Template(import_sc_file.read())
		i_content = tpl.render(vm_data=vm_data,disks=disks,vm_name=args["vm_name"],storage_type="rbd",storage_pool="rbd")
		print(i_content)
	with open("%s/import.sh" % d_folder, "w") as scriptfile:
		scriptfile.write(i_content)


	connection.close()
	return 0

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)
