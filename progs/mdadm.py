# --------------------------------------------------------------------
# (C) Copyright 2006-2014 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2019-2020 Red Hat, Inc.
#
# Author: Nitin U. Yewale <nyewale@redhat.com>
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


__version__ = "0.0.1"

from pykdump.API import *

import importlib.util

def get_device_list(mddev):
    devlist = []
    for rd in readSUListFromHead(mddev.disks,
                        'same_set', 'struct md_rdev'):
            dev = rd.kobj.name
            devlist.append(dev)
    return devlist

def get_rdevS(mddev):
    rdevlist = []
    for rdev in readSUListFromHead(mddev.disks, 'same_set', 'struct md_rdev'):
        rdevlist.append(rdev)

    return rdevlist

def get_disk_size(rdev):
    ds = rdev.sectors
    disk_size = ds / 2048
    return disk_size

def get_rdev_dev(mddev):
    dev_rdev = {}
    disknum_rdev = {}
    disksize_rdev = {}
    rdevl =  []
    for rdev in readSUListFromHead(mddev.disks, 'same_set', 'struct md_rdev'):
        rdevp = readSU("struct md_rdev", rdev)
        rdevp = format(rdevp, 'x')
        rdevl.append(rdevp)
        dev_rdev[rdevp] = rdev.kobj.name
        disknum_rdev[rdevp] = rdev.desc_nr
        disksize_rdev[rdevp] = get_disk_size(rdev)
    for r in rdevl :
        disk = dev_rdev[r]
        disk_num = disknum_rdev[r]
        disk_size = disksize_rdev[r]
        print ("disk{} : {}    size: {:.2f}GB    md_rdev {}".format(disk_num, disk, disk_size/1024, r))

def get_md_size(mddev):
    if (mddev.pers):
        sectors = (mddev.array_sectors)
        return ((sectors * 512) / 1024 / 1024 )
    else:
        if (mddev.dev_sectors != 0):
            sectors = (mddev.dev_sectors)
            return ((sectors * 512) / 1024 / 1024)
        else:
            sectors = "-1"
            return sectors

def get_array_state(mddev):
    enum_array_state = EnumInfo("enum mddev_sb_flags")
    enum_array_state = EnumInfo("enum mddev_flags")
    ro = mddev.ro
    if (mddev.pers and not test_bit(MD_NOT_READY, mddev.flags)):
        if (ro == 1):
            st = readonly
        elif (ro == 2):
            st = read_auto
        elif (ro == 0):
            if (test_bit(MD_SB_CHANGE_PENDING, mddev.sb_flags)):
                st = write_pending
            elif (mddev.in_sync):
                st = clean
            elif (mddev.safemode):
                st = active_idle
            else:
                st = active
    else:
        if (mddev.raid_disks == "0") and (mddev.dev_sectors == "0"):
            st = clear
        else:
            st = inactive

    print("Array_state is {}".format(st))

def get_mdlist():
    mdlist = []
    if (symbol_exists('all_mddevs')):
        for md in readSUListFromHead(sym2addr('all_mddevs'),
                        'all_mddevs', 'struct mddev'):
            mdlist.append(md)
    return mdlist

def get_metada_type(mddev):
    if (mddev.metadata_type == "0"):
        metadata_type = ""
        return metadata_type
    else:
        metadata_type = mddev.metadata_type
        return metadata_type

def get_mddev():
    mdlist = get_mdlist()
    for mddev in mdlist:
        disk_name = mddev.gendisk.disk_name
        mddevp = readSU("struct mddev", mddev)
        mddevp = format(mddevp, 'x')
        if (mddev.pers):
            mp = readSU("struct md_personality", mddev.pers)
            mp = format(mp, 'x')
        else:
            mp = "Not Available"
        gd = readSU("struct gendisk", mddev.gendisk)
        gd = format(gd, 'x')
        #is_active = atomic_t(mddev.active)
        size = get_md_size(mddev)
        if (size != "-1"):
            sizeG = float(int(size)/1024)
        #get_array_state
        rdevlist=get_rdevS(mddev)
        print ("\nDevice : /dev/{}".format(disk_name))
        metadata_type = get_metada_type(mddev)
        print("Raid Level : {}      Version : {}.{}   metadata_type : {}".format(mddev.clevel, mddev.major_version,
         mddev.minor_version, metadata_type))
        if (size == "-1"):
            print ("Size : NA")
        else:
            print ("Array Size : {:.2f}MB  ({:.2f}GB)    Total Devices : {}".format(size, sizeG, len(rdevlist)))
        print ("mddev    {}         md_personality  {}".format(mddevp, mp))
        print ("gendisk  {}   \n".format(gd))
        print ("flags :  {}   sb_flags : {}  external : {} \n".format(mddev.flags, mddev.sb_flags, mddev.external))
        get_rdev_dev(mddev)
        print("\n=================================================================================== \n")

def get_chunk_size(mddev):
    if (mddev.chunk_sectors != 0 ):
        return (mddev.chunk_sectors/2)
    else:
        return "-1"

def get_raid_disk(rdev):
    if (rdev.raid_disk < 0 ) :
        return "-1"
    else :
        raid_disk = rdev.raid_disk
        return raid_disk

def get_mddev_details():
    mdlist = get_mdlist()
    for mddev in mdlist:
        print("Device : /dev/{}".format(mddev.gendisk.disk_name))
        print("Version : {}.{}       metadata_type : {}".format(mddev.major_version, mddev.minor_version, get_metada_type(mddev)))
        print("Creation Time : {}".format(time.ctime(mddev.ctime)))
        print("Raid Level : {}".format(mddev.clevel))
        size = get_md_size(mddev)
        if (size != "-1"):
            sizeG = float(int(size)/1024)
            print("Array Size : {:.2f}MB  ({:.2f}GB)".format(size, sizeG))
        else:
            print("Array Size : NA")
        print("RAID Devices : {}".format(get_device_list(mddev)))
        rdevlist = get_rdevS(mddev)
        print("Total Devices : {}".format(len(rdevlist)))
        if (mddev.persistent == 1):
            persistence = "Superblock is persistent"
        else:
            persistence = "NA"
        print("Persistence : {}".format(persistence))

        print("Update Time : {}".format(time.ctime(mddev.utime)))
        #print("State : ")
        #print("Active Devices : ")
        #print("Working Devices : ")
        #print("Failed Devices : ")
        #print("Spare Devices : \n")
        csize = get_chunk_size(mddev)
        if (csize == "-1" ):
            print("Chunk Size : NA")
        else:
            print("Chunk Size : {}K".format(csize))
        #print("Consistency Policy : ")
        print("\nDevice              Number       RaidDevice ")
        rdevS=get_rdevS(mddev)
        for rdev in rdevS:
            Number = rdev.desc_nr
            Name = rdev.kobj.name

            if (get_raid_disk(rdev) == "-1"):
                raid_disk = "Spare/Faulty"
            else :
                raid_disk = get_raid_disk(rdev)

            print("{:}  {:12}  {:14} ".format(Name, Number, raid_disk))
        print ("\n----------------------------------------------------------------------------\n")


if ( __name__ == '__main__'):

    import argparse
    parser =  argparse.ArgumentParser()

    parser.add_argument("-m", "--mddev", dest="mddev", default=0,
        action="store_true",
        help="show mdamd_crash_format")

    parser.add_argument("-d", "--details", dest="details", default=0,
        action="store_true",
        help="show mdadm_-D_format")

    args = parser.parse_args()

    if (args.details):
        get_mddev_details()

    if (args.mddev or not args.details):
        get_mddev()
