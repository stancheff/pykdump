# -*- coding: utf-8 -*-
# module LinuxDump.dm
#
# --------------------------------------------------------------------
# (C) Copyright 2006-2014 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2014-2022 Red Hat, Inc.
#
# Author: David Jeffery <djeffery@redhat.com>
#
# Contributors:
#- Milan P. Gandhi <mgandhi@redhat.com>
#- John Pittman <jpittman@redhat.com>
#- Nitin U. Yewale <nyewale@redhat.com>
#
# This package is created for reusability of functions used to process
# the dm device information. Most of the code in this package is based
# on existing code in progs/dmshow.py, which was authored by
# David Jeffery.
#
# The generic code for processing basic dm device details is placed
# in this file. In future, separate module files will be added for
# processing the linear, raid LVM volumes, multipath devices, etc.
# --------------------------------------------------------------------
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import print_function

__doc__ = '''
This is a package providing generic access to dm device stuff
'''

from pykdump.API import *
from collections import (namedtuple, defaultdict, OrderedDict)
from LinuxDump.sysfs import *
from LinuxDump.kobjects import *
from LinuxDump.Time import j_delay


# Get a list of dm devices
def get_dm_devices():
    sn = "struct hash_cell"
    out = []
    if (symbol_exists("_name_buckets")):
        nameb = readSymbol("_name_buckets")
        off = member_offset(sn, "name_list")
        for b in nameb:
            for a in readListByHead(b):
                hc = readSU(sn, a - off)
                if (hc.md.disk):
                    out.append((hc.md, hc.name))
                else:
                    print("ERROR: skipping {}. No gendisk "
                          "present.".format(hc.md))
    else:
        name_tree = readSymbol("name_rb_tree")
        for hc in for_all_rbtree(name_tree, sn, "name_node"):
            if (hc.md.disk):
                out.append((hc.md, hc.name))
            else:
                print("ERROR: skipping {}. No gendisk "
                      "present.".format(hc.md))

    return out

# Get the block device name
def bdev_name(bdev):
    if struct_exists("struct hd_struct"):
        partno = bdev.bd_part.partno
    else:
        partno = bdev.bd_partno

    if (partno == 0):
        return bdev.bd_disk.disk_name
    if (bdev.bd_disk.disk_name[len(bdev.bd_disk.disk_name)-1].isdigit() is True):
        return bdev.bd_disk.disk_name + "p" + str(partno)
    return bdev.bd_disk.disk_name + str(partno)

# Get the device size
def get_size(gendisk):
    try:
        if (member_size("struct gendisk", "capacity") != -1):
            return (gendisk.capacity * 512 / 1048576)
        if struct_exists("struct hd_struct"):
            tmp_hd_struct = readSU("struct hd_struct", long(gendisk.part0))
            return (tmp_hd_struct.nr_sects * 512 / 1048576)
        inode = readSU("struct inode", gendisk.part0.bd_inode)
        return inode.i_size / 1048576
    except:
        pylog.warning("Error in processing 'struct gendisk'", gendisk)
        pylog.warning("To debug this issue, you could manually examine "
                      "the contents of gendisk struct")
        return

# Verify if the device-mapper table exists
def dm_table_exists(table):
    if (table == 0x0):
        return False
    else:
        return True

def context_struct_exists(s_name, name, message=1):
    struct_name = "struct " + s_name
    if (struct_exists(struct_name)):
        return True
    else:
        if (message):
            pylog.info("{}: error: {} does not exist".format(name, struct_name))
        return False

# Get device-mapper target name
def get_dm_target_name(dm_table_map, name):
    if (dm_table_exists(dm_table_map) is False):
        pylog.info("{}: table not found".format(name))
        return 0
    try:
        target_name = dm_table_map.targets.type.name
    except:
        pylog.info("{}: get_dm_target_name() failed".format(name))
        return 0
    return target_name

# Extract the VG and LV name from string
def get_vg_lv_names(string):
    temp = ["", ""]
    i = flag = 0

    while i < len(string):
        if (string[i-1].isalnum() and string[i+1].isalnum() and string[i] == '-'):
            flag = 1
            if (string[i:len(string)] != "-tpool"):
                i += 1

        if (flag == 0):
            temp[0] = temp[0] + string[i]
        elif (flag == 1):
            temp[1] = temp[1] + string[i]
        i += 1

    return temp

# Retrieve the mapped_device pointer for specific device
def get_md_mpath_from_gendisk(pv_gendisk, devlist):
    tmp_mapped_device = readSU("struct mapped_device", pv_gendisk.queue.queuedata)
    for temp_dev in devlist:
        if (tmp_mapped_device == temp_dev[0]):
            return temp_dev
    return (0,0)

# Get the LVM PV size
def get_pvsize(blockdev):
    try:
        bd_inode = (blockdev.bd_inode)
        size = (bd_inode.i_size / 1048576)
        return size
    except:
        pylog.warning("Error in processing {}", blockdev)
        pylog.warning("To debug this issue, you could manually examine "
                      "the contents of block_device struct")
        return

# Check the disk's sysfs state
def get_sysfs_state(gendisk):
    state = gendisk.part0.__dev.kobj.state_in_sysfs
    if state == 1:
        return "online"
    else:
        return "missing"
