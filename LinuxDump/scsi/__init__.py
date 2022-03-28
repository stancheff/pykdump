# -*- coding: utf-8 -*-
# module LinuxDump.scsi
#
# --------------------------------------------------------------------
# (C) Copyright 2013-2020 Hewlett Packard Enterprise Development LP
#
# Author: Alex Sidorenko <asid@hpe.com>
#
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
This is a package providing generic access to SCSI stuff
'''

from pykdump.API import *
from collections import (namedtuple, defaultdict, OrderedDict)
from LinuxDump.sysfs import *
from LinuxDump.kobjects import *
from LinuxDump.Time import j_delay


'''
Attached devices:
Host: scsi2 Channel: 03 Id: 00 Lun: 00
  Vendor: HP       Model: P420i            Rev: 3.54
  Type:   RAID                             ANSI  SCSI revision: 05
Host: scsi2 Channel: 00 Id: 00 Lun: 00
  Vendor: HP       Model: LOGICAL VOLUME   Rev: 3.54
  Type:   Direct-Access                    ANSI  SCSI revision: 05
'''

scmd_status_byte = {
    0x0:  "SAM_STAT_GOOD",
    0x2:  "SAM_STAT_CHECK_CONDITION",
    0x4:  "SAM_STAT_CONDITION_MET",
    0x8:  "SAM_STAT_BUSY",
    0x10: "SAM_STAT_INTERMEDIATE",
    0x14: "SAM_STAT_INTERMEDIATE_CONDITION_MET",
    0x18: "SAM_STAT_RESERVATION_CONFLICT",
    0x22: "SAM_STAT_COMMAND_TERMINATED",
    0x28: "SAM_STAT_TASK_SET_FULL",
    0x30: "SAM_STAT_ACA_ACTIVE",
    0x40: "SAM_STAT_TASK_ABORTED"
}

scmd_host_byte = {
    0x0:  "DID_OK",
    0x1:  "DID_NO_CONNECT",
    0x2:  "DID_BUS_BUSY",
    0x3:  "DID_TIME_OUT",
    0x4:  "DID_BAD_TARGET",
    0x5:  "DID_ABORT",
    0x6:  "DID_PARITY",
    0x7:  "DID_ERROR",
    0x8:  "DID_RESET",
    0x9:  "DID_BAD_INTR",
    0x0a: "DID_PASSTHROUGH",
    0x0b: "DID_SOFT_ERROR",
    0x0c: "DID_IMM_RETRY",
    0x0d: "DID_REQUEUE",
    0x0e: "DID_TRANSPORT_DISRUPTED",
    0x0f: "DID_TRANSPORT_FAILFAST",
    0x10: "DID_TARGET_FAILURE",
    0x11: "DID_NEXUS_FAILURE",
    0x12: "DID_ALLOC_FAILURE",
    0x13: "DID_MEDIUM_ERROR",
    0x14: "DID_TRANSPORT_MARGINAL"
}

opcode_table = {'0x0':'TUR', '0x03':'REQ-SENSE', '0x08':'READ(6)',\
                '0x0a':'WRITE(6)', '0x12':'INQUIRY', '0x16':'RESERVE(6)',\
                '0x17':'RELEASE(6)', '0x25':'READ-CAP(10)', '0x28':'READ(10)',\
                '0x2a':'WRITE(10)', '0x35':'SYNC CACHE', '0x41':'WR SAME',\
                '0x56':'RESERVE(10)', '0x57':'RELEASE(10)', '0x88':'READ(16)',\
                '0x8a':'WRITE(16)','0xa0':'REPORT LUNS', '0xa8':'READ(12)',\
                '0xaa':'WRITE(12)'}

scsi_device_types = None
enum_shost_state = None

try:
    scsi_device_types = readSymbol("scsi_device_types")
    enum_shost_state = EnumInfo("enum scsi_host_state")
except TypeError:
    loadModule("scsi_mod")
    loadModule("scsi_transport_fc")
    try:
        scsi_device_types = readSymbol("scsi_device_types")
        enum_shost_state = EnumInfo("enum scsi_host_state")
    except TypeError:
        pass

# A pathological case on some SLES kernel - something is built
# in a way that even after loading debuginfo we cannot find
# the type of scsi_device_types:
# <data variable, no debug info> scsi_device_types;


def scsi_debuginfo_OK(printwarn=True):
    if (scsi_device_types is None or enum_shost_state is None):
        if (printwarn):
            print("+++Cannot find symbolic info for <scsi_device_types>"
                " or <enum scsi_host_state>\n"
                "   Put 'scsi_mod' debuginfo file into current directory\n"
                "   and then re-run the command adding --reload option")
        return False
    elif (isinstance(scsi_device_types, int)):
        if (printwarn):
            print("+++Debuginfo for this kernel is built in a way\n"
                "  that does not let us analyse SCSI devices, even\n"
                "  after loading debuginfo for SCSI")
        return False
    return True

# The following enums exists on all kernels we support
if (scsi_debuginfo_OK(printwarn=False)):
    enum_st_state = EnumInfo("enum scsi_target_state")

try:
    _rq_atomic_flags = EnumInfo("enum rq_atomic_flags")
except TypeError:
    # RHEL5
    _rq_atomic_flags = {}

if ("REQ_ATOM_COMPLETE" in _rq_atomic_flags):
    _REQ_ATOM_COMPLETE = 1<< _rq_atomic_flags.REQ_ATOM_COMPLETE
else:
    _REQ_ATOM_COMPLETE = None
    
if ("REQ_ATOM_START" in _rq_atomic_flags):
    _REQ_ATOM_START = 1<< _rq_atomic_flags.REQ_ATOM_START
else:
    _REQ_ATOM_START = None

def scsi_device_type(t):
    if (t == 0x1e):
        return "Well-known LUN   "
    elif (t == 0x1f):
        return "No Device        "
    elif (t >= len(scsi_device_types)):
        return "Unknown          "
    return scsi_device_types[t]

if (symbol_exists("fc_rport_dev_release")):
    fc_rport_dev_release = sym2addr("fc_rport_dev_release")
else:
    fc_rport_dev_release = -1
# int scsi_is_fc_rport(const struct device *dev)
#{
#       return dev->release == fc_rport_dev_release;
# }
def scsi_is_fc_rport(dev):
    return (dev.release == fc_rport_dev_release)

#define dev_to_rport(d)                         \
#        container_of(d, struct fc_rport, dev)
def dev_to_rport(d):
    return container_of(d, "struct fc_rport", "dev")

# to_scsi_target(d): (d, struct scsi_target, dev)
def to_scsi_target(d):
    return container_of(d, "struct scsi_target", "dev")

# struct scsi_target *scsi_target(struct scsi_device *sdev) {
# return to_scsi_target(sdev->sdev_gendev.parent);
def scsi_target(sdev):
    return to_scsi_target(sdev.sdev_gendev.parent)

#define starget_to_rport(s)                     \
#        scsi_is_fc_rport(s->dev.parent) ? dev_to_rport(s->dev.parent) : NULL
def starget_to_rport(s):
    parent = s.dev.parent
    return dev_to_rport(parent) if scsi_is_fc_rport(parent) else None


# Generic walk for all devices registered in 'struct class'
def class_for_each_device(_class):
    if (_class.hasField("p")):
        p = _class.p
        if (p.hasField("klist_devices")):
            klist_devices = p.klist_devices
        else:
            klist_devices = p.class_devices

    elif(_class.hasField("klist_devices")):
        klist_devices = _class.klist_devices
    else:
        # RHEL5
        for dev in ListHead(_class.children, "struct class_device").node:
            yield dev
        return

    for knode in klistAll(klist_devices):
        dev = container_of(knode, "struct device", "knode_class")
        yield dev

# ...........................................................................
#
# There are several ways to get lists of shosts/devices. We can get just
# Scsi_Host from 'shost_class', or we can get everything (hosts, devices,
# etc.) from 'scsi_bus_type'
#
# ...........................................................................

#
# get all Scsi_Host from 'shost_class'
#

def get_scsi_hosts():
    shost_class = readSymbol("shost_class")
    klist_devices = 0

    try:
        klist_devices = shost_class.p.class_devices
    except KeyError:
        pass
    if (not klist_devices):
        try:
            klist_devices = shost_class.p.klist_devices
        except KeyError:
            pass

    out = []
    if (klist_devices):
        for knode in klistAll(klist_devices):
            if (member_size("struct device", "knode_class") != -1):
                dev = container_of(knode, "struct device", "knode_class")
            else:
                devp = container_of(knode, "struct device_private", "knode_class")
                dev = devp.device
            out.append(container_of(dev, "struct Scsi_Host", "shost_dev"))
        return out
    else:
        for hostclass in readSUListFromHead(shost_class.children, "node", "struct class_device"):
            out.append(container_of(hostclass, "struct Scsi_Host", "shost_classdev"))
        return out

def scsi_device_lookup(shost):
    for a in ListHead(shost.__devices, "struct scsi_device").siblings:
        yield a

#
# Get all SCSI structures from 'scsi_bus_type"
#

scsi_types = ("scsi_host_type", "scsi_target_type", "scsi_dev_type")

def get_all_SCSI():
    _scsi_types_addrs = {sym2addr(n) : n for n in scsi_types}

    # Structures are different on different kernels
    scsi_bus_type = readSymbol("scsi_bus_type")
    try:
        klist_devices = scsi_bus_type.p.klist_devices
    except KeyError:
        klist_devices = scsi_bus_type.klist_devices

    out = defaultdict(list)
    for knode in klistAll(klist_devices):
        if (struct_exists("struct device_private")):
            dev = container_of(knode, "struct device_private", "knode_bus").device
            dev_type = _scsi_types_addrs.get(dev.type, None)
            if (dev.type is not None):
                #print(dev, dev_type)
                if (dev_type == "scsi_host_type"):
                    scsi_host = container_of(dev, "struct Scsi_Host", "shost_gendev")
                    out[dev_type].append(scsi_host)
                elif (dev_type == "scsi_dev_type"):
                    sdev = container_of(dev, "struct scsi_device", "sdev_gendev")
                    out[dev_type].append(sdev)
                    #print("      ---", sdev)
            else:
                out[dev_type].append(dev)
        else:
            # This is old code, is this correct for new kernels?
            dev = container_of(knode, "struct device", "knode_bus")
            sdev = container_of(dev, "struct scsi_device", "sdev_gendev")
            out["scsi_dev_type"].append(sdev)
            
    return out

# Get all SCSI devices. There are several ways of doing it, here we 
# loop on shosts and for each shost get its sdevices

@memoize_cond(CU_LIVE|CU_LOAD)
def get_scsi_devices(shost=0):
    out = []

    if (shost):
        out = readSUListFromHead(shost.__devices, "siblings", "struct scsi_device")
    else:
        for host in get_scsi_hosts():
            out += readSUListFromHead(host.__devices, "siblings", "struct scsi_device")

    return out

# Return an ordered dict with some state info for Scsi_Host
def get_shost_states(shost):
    d = OrderedDict()
    for _a in ("last_reset", "host_busy", "host_failed", "host_eh_scheduled"):
        d[_a] = atomic_t(getattr(shost, _a))
    return d

def print_Scsi_Host(shost, v=0):
    hostt = shost.hostt
    print(" *scsi{}*  {}".format(shost.host_no, shost))
    print("     ", end='')
    sd = gendev2sd(shost.shost_gendev)
    print(sysfs_fullpath(sd))
    
    print("     ", end='')  
    for _a in ("last_reset", "host_busy", "host_failed", "host_eh_scheduled"):
        print(" {:s}={}".format(_a, atomic_t(getattr(shost, _a))), end='')
    print()
    
    # Print shost_state
    shost_state = enum_shost_state.getnam(shost.shost_state)
    print("      shost_state={}".format(shost_state))
    priv = shost.hostdata
    hname = shost.hostt.name

    # Do we know the struct name for this host?
    if (hname.startswith("qla")):
        sname = 'struct scsi_qla_host'
    elif (hname == 'hpsa'):
        sname = 'struct ctlr_info'
    elif (hname == 'lpfc'):
        sname = 'struct lpfc_vport'
    elif (hname == 'bfa'):
        sname = 'struct bfad_im_port_s'
    elif ('pvscsi' in hname.lower()):
        sname = 'struct pvscsi_adapter'
    else:
        # We do not know the struct name
        sname = 'shost_priv(shost)'
    print("       hostt: {}   <{} {:#x}>".format(hname, sname, priv))
    
    do_driver_specific(shost)

# Print time info about request. This is duplicated in Dev, we should
# use the same subroutine
def request_timeinfo(req, jiffies = None):
    if (jiffies is None):
        jiffies = readSymbol("jiffies")
    ran_ago = j_delay(req.start_time, jiffies)
    # On RHEL5, 'struct request' does not have 'deadline' field
    try:
        if (req.deadline):
            deadline = float(req.deadline - jiffies)/HZ
            if (deadline > 0):
                fmt = "started {} ago, times out in {:5.2f}s"
            else:
                fmt = "started {} ago, timed out {:5.2f}s ago"
            return(fmt.format(ran_ago, abs(deadline)))
        else:
            return("started {} ago".format(ran_ago))
    except KeyError:
        return("{}started {} ago".format(ran_ago))


# get scsi_cmnd list from scsi_dev
def print_scsi_dev_cmnds(sdev, v=1):
    # Tghis subroutine does not work for old kernels (RHEL5)
    if (_REQ_ATOM_COMPLETE is None):
        return 0
    l = ListHead(sdev.request_queue.tag_busy_list)
    tagged_set = set(l)
    l_t = ListHead(sdev.request_queue.timeout_list)
    active_set = set(l_t)
    classified = 0
    jiffies = readSymbol("jiffies")

    for cmd in ListHead(sdev.cmd_list, "struct scsi_cmnd").list:
        flags = []
        request = cmd.request
        atomic_flags = request.atomic_flags
        if (_REQ_ATOM_COMPLETE is not None and (atomic_flags & _REQ_ATOM_COMPLETE)):
            flags.append('C')
        if (_REQ_ATOM_START is not None and (atomic_flags & _REQ_ATOM_START)):
            flags.append('S')

        if (long(cmd.request.timeout_list) in active_set):
            flags.append('T')
        if (long(cmd.request.queuelist) in tagged_set):
            flags.append('G')
        status = ''.join(flags)
        if (flags):
            classified += 1
        if (v < 2 and not flags):
            return classified

        print("    {:4} {} {}".format(status, cmd, request))
        print(" "*11,request_timeinfo(request, jiffies))
        print("\t     (jiffies - cmnd->jiffies_at_alloc)={}".format(
                        jiffies-cmd.jiffies_at_alloc))

        #print("           {:#x}  {}".format(cmd.serial_number, cmd.request.atomic_flags))
        
    return classified

# map "struct request" -> ("struct scsi_device", "struct scsi_cmnd")
def req2scsi_info():
    d = {}
    for sdev in get_scsi_devices():
        for cmd in ListHead(sdev.cmd_list, "struct scsi_cmnd").list:
            d[cmd.request] = (sdev, cmd)
    return d


# Decode the scsi_device's sdev_state enum
def get_sdev_state(enum_state):
    if not isinstance(enum_state, long):
        return enum_state
    return {
        1: "SDEV_CREATED",
        2: "SDEV_RUNNING",
        3: "SDEV_CANCEL",
        4: "SDEV_DEL",
        5: "SDEV_QUIESCE",
        6: "SDEV_OFFLINE",
        7: "SDEV_TRANSPORT_OFFLINE",
        8: "SDEV_BLOCK",
        9: "SDEV_CREATED_BLOCK",
    }[enum_state]

# Return the name of module used by specific Scsi_Host (shost)
def get_hostt_module_name(shost):
    try:
        name = shost.hostt.module.name
    except:
        name = "unknown"
    return name

# Returns the number of SCSI commands pending on specific Scsi_Host
SCMD_STATE_COMPLETE = 0
SCMD_STATE_INFLIGHT = 1

def test_bit(nbit, val):
    return ((val >> nbit) == 1)

def get_host_busy(shost):
    cmds_in_flight = 0
    cmds = []

    sdevs = get_scsi_devices(shost)
    for sdev in sdevs:
        cmds += get_scsi_commands(sdev)

    for cmd in cmds:
        if (test_bit(SCMD_STATE_INFLIGHT, cmd.state)):
            cmds_in_flight += 1
    return cmds_in_flight

# Check for the scsi_device busy counter
def get_scsi_device_busy(sdev):
    busy = cleared = 0
    sb = sdev.budget_map

    for map_nr in range(sb.map_nr):
        bitmap = sb.map[map_nr].word
        if (not int(bitmap)):
            continue
        for i in range(sb.map[map_nr].depth):
            if int(bitmap) & 1:
                busy += 1
            bitmap = bitmap >> 1

    for map_nr in range(sb.map_nr):
        bitmap = sb.map[map_nr].cleared
        if (not int(bitmap)):
            continue
        for i in range(sb.map[map_nr].depth):
            if int(bitmap) & 1:
                cleared += 1
            bitmap = bitmap >> 1

    return busy - cleared

# Return the scsi device information in Host(H):Channel(C):Target(T):LunID(L)
# format
def get_scsi_device_id(sdev):
    return "{:d}:{:d}:{:d}:{:d}".format(sdev.host.host_no,
                                        sdev.channel, sdev.id, sdev.lun)

# Print the most common information from Scsi_Host structure, this includes:
# Host name, (e.g. host1, host2, etc.)
# Driver used by scsi host
# Pointer to Scsi_Host, shost_data and hostdata
def print_shost_header(shost):
    print("HOST      DRIVER")
    print("{:10s}{:22s} {:24s} {:24s} {:24s}".format("NAME", "NAME", "Scsi_Host",
          "shost_data", "hostdata"))
    print("--------------------------------------------------"
          "-------------------------------------------------")
    print("{:9s} {:22s} {:12x} {:24x} {:24x}\n".format(shost.shost_gendev.kobj.name,
        get_hostt_module_name(shost), shost, shost.shost_data, shost.hostdata))

# Retrieve the mapping between request_queue and gendisk struct
def get_gendev():
    gendev_dict = {}
    klist_devices = 0

    if ((member_size("struct device", "knode_class") != -1) or
        (member_size("struct device_private", "knode_class") != -1)):
        block_class = readSymbol("block_class")

        try:
            klist_devices = block_class.p.class_devices
        except KeyError:
            pass

        if (not klist_devices):
            try:
                klist_devices = block_class.p.klist_devices
            except KeyError:
                pass

        if (klist_devices):
            for knode in klistAll(klist_devices):
                if (member_size("struct device", "knode_class") != -1):
                    dev = container_of(knode, "struct device", "knode_class")
                else:
                    devp = container_of(knode, "struct device_private", "knode_class")
                    dev = devp.device
                if struct_exists("struct hd_struct"):
                    hd_temp = container_of(dev, "struct hd_struct", "__dev")
                    gendev = container_of(hd_temp, "struct gendisk", "part0")
                else:
                    blockdev = container_of(dev, "struct block_device", "bd_device")
                    gendev = blockdev.bd_disk
                gendev_q = format(gendev.queue, 'x')
                gendev_dict[gendev_q] = format(gendev, 'x')

    elif (member_size("struct gendisk", "kobj") != -1):
        block_subsys = readSymbol("block_subsys")
        try:
            kset_list = block_subsys.kset.list
        except KeyError:
            pass

        if (kset_list):
            for kobject in readSUListFromHead(kset_list, "entry", "struct kobject"):
                gendev = container_of(kobject, "struct gendisk", "kobj")
                gendev_q = format(gendev.queue, 'x')
                gendev_dict[gendev_q] = format(gendev, 'x')

    else:
        print("Unable to process the vmcore, cant find 'struct class' or 'struct subsystem'.")
        return

    return gendev_dict

# Get the FC/FCoE HBA attributes viz. address of fc_host_attrs struct,
# node_name and port_name
def get_fc_hba_port_attr(shost):
    port_attr = []
    if (struct_exists("struct fc_host_attrs")):
        try:
            fc_host_attrs = readSU("struct fc_host_attrs", shost.shost_data)
            if (fc_host_attrs and ('fc_wq_' in fc_host_attrs.work_q_name[:8])):
                port_attr.append(fc_host_attrs)
                port_attr.append(fc_host_attrs.node_name)
                port_attr.append(fc_host_attrs.port_name)
        except:
            pass

    return port_attr

# Return the elevator or IO scheduler used by the device
def get_sdev_elevator(sdev):
    if (sdev.request_queue.elevator):
        try:
            if (member_size("struct elevator_queue", "elevator_type") != -1):
                elevator_name = sdev.request_queue.elevator.elevator_type.elevator_name
            elif(member_size("struct elevator_queue", "type") != -1):
                elevator_name = sdev.request_queue.elevator.type.elevator_name
            else:
                elevator_name = "<Unknown>"
        except Exception as e:
            elevator_name = "<Unknown>"
            pylog.info("Error getting elevator name for {} {}".format(sdev, e))
    else:
        elevator_name = "<none>"

    return elevator_name

import importlib
# Check whether there is an mportable submodule for this driver 
# and if yes, do extra processing
def do_driver_specific(shost):
    hostt = shost.hostt
    modname = hostt.name
    try:
        mod = importlib.import_module('.'+modname, package=__name__)
    except ImportError:
        return
    print("   -- Driver-specific Info {} --".format(hostt))
    mod.print_extra(shost)


# *************************************************************************
#
#          Obsolete subroutines - used by old 'crashinfo --scsi' only
#
# *************************************************************************
# For v=0 list only different model/vendor combinations, how many a busy
# and different Scsi_Host
# For v=1 we additionally print all scsi devices that are busy/active
# For v=2 we print all scsi devices
def print_SCSI_devices(v=0):
    shosts = set()
    n_busy = 0
    tot_devices = 0
    different_types = set()
    for sdev in get_scsi_devices():
        tot_devices += 1
        shost = sdev.host
        shosts.add(shost)
        busy = atomic_t(sdev.device_busy)
        if (busy):
            n_busy += 1
        _a = []
        _a.append("  Vendor: {:8} Model: {:16} Rev: {:4}".\
            format(sdev.vendor[:8], sdev.model[:16], sdev.rev[:4]))
        _a.append("  Type:   {}                ANSI  SCSI revision: {:02x}".\
            format(scsi_device_type(sdev.type),
                   sdev.scsi_level - (sdev.scsi_level > 1)))
        s_descr = "\n".join(_a)
        different_types.add(s_descr)
        
        # iorequest_cnt-iodone_cnt
        iorequest_cnt = atomic_t(sdev.iorequest_cnt)
        iodone_cnt = atomic_t(sdev.iodone_cnt)
        cntdiff = sdev.iorequest_cnt.counter - sdev.iodone_cnt.counter
        if (v > 1 or (v > 0 and (busy))):
            print('{:-^39}{:-^39}'.format(str(sdev)[8:-1], str(shost)[8:-1]))
            print("Host: scsi{} Channel: {:02} Id: {:02} Lun: {:02}".format(
                shost.host_no, sdev.channel, sdev.id, sdev.lun))
            print(s_descr)

            gendev = sdev.sdev_gendev
            # SD is either 'sysfs_dirent' or 'kernfs_node'
            sd = gendev2sd(gendev)
            print(sysfs_fullpath(sd))
            devname = blockdev_name(sd)
            if (busy == 0):
                sbusy = ''
            else:
                sbusy = " busy={}".format(busy)
            if (devname or busy):
                print("devname={}{}".format(devname, sbusy))
            starget = scsi_target(sdev)
            is_fc = scsi_is_fc_rport(starget.dev.parent)
            st_state = enum_st_state.getnam(starget.state)
            #if (is_fc):
            print("  {} state = {}".format(starget, st_state))
            print("  {}".format(sdev.request_queue))
            
            print("  iorequest_cnt={}, iodone_cnt={}, diff={}".\
                  format(iorequest_cnt, iodone_cnt, cntdiff))
            classified = print_scsi_dev_cmnds(sdev, v)
            if (False and classified != busy):
                print("Mismatch", classified, busy)
            continue
            rport = starget_to_rport(starget)
            print("    ", shost.hostt)
            if (rport):
                print("   ", rport)
            #print(scsi_target(sdev).dev.parent)
    if (different_types):
        print("\n{:=^70}".format(" Summary "))
        print("   -- {} SCSI Devices, {} Are Busy --".\
            format(tot_devices, n_busy))
        print("{:.^70}".format(" Vendors/Types "))
        for _a in different_types:
            print(_a)
            print()

    # Now print info about Shosts
    if (not shosts):
        return
    print("\n{:=^70}".format(" Scsi_Hosts"))
    for shost in sorted(shosts):
        print_Scsi_Host(shost)

    #print ("  ", scsi_dev.host.hostt.name)
