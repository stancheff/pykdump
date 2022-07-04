# --------------------------------------------------------------------
# (C) Copyright 2006-2014 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2014-2019 Red Hat, Inc.
#
# Author: John Pittman <jpittman@redhat.com>
#
# Collaboration on this project provided by David Jeffery. Additionally,
# the request_queue discovery code in this script was shamelessly poached
# from his multiqueue-capable request tracking script, rqlist.py.
#
# nvme.py: pykdump script to print information surrounding the
#          NVMe storage driver
#
# [--list] - emulates 'nvme list' command
# [--ctrl] - prints nvme_ctrl struct info
# [--ns]   - prints nvme_ns struct info
# [--dev]  - prints NVMe ops specific device info
#              - PCI:  nvme_pci_ctrl_ops - struct nvme_dev
#              - RDMA: nvme_rdma_ctrl_ops - struct nvme_rdma_ctrl
#              - Loop: nvme_loop_ctrl_ops - struct nvme_loop_ctrl
#              - FC:   nvme_fc_ctrl_ops - struct nvme_fc_ctrl
# [--queue] - prints NVMe ops specific queues
#              - PCI:  nvme_pci_ctrl_ops - struct nvme_queue
#              - RDMA: nvme_rdma_ctrl_ops - struct nvme_rdma_queue
#              - Loop: nvme_loop_ctrl_ops - struct nvme_loop_queue
#              - FC:   nvme_fc_ctrl_ops - struct nvme_fc_queue
# [--qid] - for use with queue argument to limit output
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

__version__ = "1.0.0"

import math, traceback
from collections import defaultdict
from pykdump.API import *
from LinuxDump.kobjects import *
from LinuxDump.trees import *
import importlib.util
if importlib.util.find_spec("pykdump.wrapcrash"):
    from pykdump.wrapcrash import readSUListFromHead

use_linuxdump_idr = 1
try:
    from LinuxDump.idr import *
except:
    use_linuxdump_idr = 0

rq_removed = 0
rq_names = {}
ops_string = {}
hd_struct_exists = struct_exists("struct hd_struct")

def get_gendisk(bdev):

    if(bdev.bd_disk):
        return bdev.bd_disk

    return 0

def get_bdev_inode(inode, i_bdev_exists):

    if i_bdev_exists:
        return inode.i_bdev
    bdev_inode = container_of(inode, "struct bdev_inode", "vfs_inode")
    return bdev_inode.bdev

def part0_to_name(part0):

    if hd_struct_exists:
        return part0.__dev.kobj.name
    else:
        return part0.bd_device.kobj.name

def nvme_rq_to_gendisk(queue):

    nvme_kobject = readSU("struct kobject", queue.kobj.parent)
    if hd_struct_exists:
        device_str = "part0.__dev"
    else:
        device_str = "part0.bd_device"

    if nvme_kobject:
        device = container_of(nvme_kobject, "struct device", "kobj")
        gendisk = container_of(device, "struct gendisk", device_str)
        return gendisk

    return 0

def get_nvme_sysfs_gendisk_queues(rq_list):

    block_depr = readSymbol("block_depr")
    rbroot = block_depr.sd.dir.children

    for kernfs_node in for_all_rbtree(rbroot, "struct kernfs_node", "rb"):
        try:
            target_kn = kernfs_node.symlink.target_kn
            if hd_struct_exists:
                gendisk = container_of(target_kn.priv, "struct gendisk", "part0.__dev.kobj")
            else:
                blockdevice = container_of(target_kn.priv, "struct block_device", "bd_device.kobj")
                gendisk = blockdevice.bd_disk
        except:
            pylog.info("WARNING: get_nvme_sysfs_gendisk_queues() failed for {}. Output maybe "
                "incomplete.".format(kernfs_node))
            continue
        if gendisk and gendisk.queue:
            if gendisk.queue not in rq_list:
                rq_list.append(gendisk.queue)
            rq_names[gendisk.queue] = str(gendisk.disk_name)

    return rq_list

def get_nvme_blockdev_queues(rq_list):

    if symbol_exists("all_bdevs"):
        all_bdevs = readSymbol("all_bdevs")

        for bdev in readSUListFromHead(all_bdevs, "bd_list", "struct block_device"):

            if bdev.bd_queue:

                gendisk = get_gendisk(bdev)
                if (gendisk):
                    rq_names[bdev.bd_queue] = str(gendisk.disk_name)
                elif (not bdev.bd_queue in rq_names or
                      rq_names[bdev.bd_queue] == "Unknown"):
                    rq_names[bdev.bd_queue] = "{}:{}".format(bdev.bd_dev >> 20,
                                                             bdev.bd_dev & 0xfffff)
                if bdev.bd_queue not in rq_list:
                    rq_list.append(bdev.bd_queue)

    return rq_list

def get_nvme_inode_blockdev_queues(rq_list):

    i_bdev_exists = member_size("struct inode", "i_bdev")
    if symbol_exists("blockdev_superblock"):
        blockdev_superblock = readSymbol("blockdev_superblock")
        for inode in readSUListFromHead(blockdev_superblock.s_inodes, "i_sb_list", "struct inode"):

            if i_bdev_exists != -1:
                bdev = get_bdev_inode(inode, 1)
            else:
                bdev = get_bdev_inode(inode, 0)

            if bdev:
                gendisk = get_gendisk(bdev)
                if gendisk and gendisk.queue:
                    if gendisk.queue not in rq_list:
                        rq_list.append(gendisk.queue)
                    rq_names[gendisk.queue] = str(gendisk.disk_name)

    return rq_list

def get_nvme_gendisk_queues(rq_list):

    global use_linuxdump_idr

    if (symbol_exists("block_depr") and struct_exists("struct kernfs_node") and not
        struct_exists("struct sysfs_dirent")):
        return get_nvme_sysfs_gendisk_queues(rq_list)

    for i in range(255):
        for bprobe in readSUListFromHead(readSymbol("bdev_map").probes[i],
                                   "next", "struct probe", inchead= True):
            try:
                if (not bprobe.owner and bprobe.get and bprobe.lock and
                     bprobe.data):

                    gendisk = readSU("struct gendisk", bprobe.data)
                    if gendisk.queue:
                        if gendisk.queue not in rq_list:
                            rq_list.append(gendisk.queue)
                        rq_names[gendisk.queue] = str(gendisk.disk_name)
            except:
                pass

    part = 0

    if use_linuxdump_idr:
        for _id, val in idr_for_each(readSymbol("ext_devt_idr")):
            if _id != 0:
                continue
            part = readSU("struct hd_struct", val)
            break

    else:
        if (member_size("struct idr", "idr_rt") != -1):

            tree_type = ("radix", "xarray")["xarray" in
                         str(getStructInfo("struct idr")["idr_rt"])]
            lines = exec_crash_command("tree -t " + tree_type + " {:x}"
                                       .format(long(readSymbol("ext_devt_idr"))))
            if (len(lines) >= 16):
                try:
                    part = readSU("struct hd_struct", long(lines[0:16], 16))
                except:
                    pass
        else:
            pylog.info("ERROR: cannot understand ext_devt_idr! A device may be missed")

    if (part):

        if part.partno > 0:
            val = part.__dev.parent
        else:
            val = part.__dev

        gendisk = container_of(val, "struct gendisk", "part0.__dev")
        if gendisk.queue:
            if (not (gendisk.queue in rq_list)):
                rq_list.append(gendisk.queue)
            rq_names[gendisk.queue] = str(gendisk.disk_name)

    return rq_list

def get_nvme_mq_queues(rq_list):

    try:
        mq_list = readSymbol("all_q_list")
    except:
        return rq_list

    for queue in readSUListFromHead(mq_list, "all_q_node", "struct request_queue"):

        if (queue.dev):
            rq_names[queue] = str(queue.dev.kobj.name)
        elif (not queue in rq_names):
            rq_names[queue] = "Unknown"

        if queue not in rq_list:
            rq_list.append(queue)

    return rq_list

def get_nvme_subqueues(rq_list):

    head_list = []
    admin_list = []

    admin_list[:] = (queue for queue in rq_list if queue.mq_ops if "admin" in addr2sym(queue.mq_ops))
    rq_list[:] = (queue for queue in rq_list if queue not in admin_list)

    if symbol_exists("nvme_ns_head_make_request"):

        nvme_ns_head_make_request_sym_addr = sym2addr("nvme_ns_head_make_request")
        for queue in rq_list:

            if queue.make_request_fn == nvme_ns_head_make_request_sym_addr:
                ns_head = readSU("struct nvme_ns_head", queue.queuedata)
                head_list.append(queue)

                if ns_head:
                    for ns in readSUListFromHead(ns_head.list, "siblings", "struct nvme_ns"):
                        rq_names[ns.queue] = str(ns.disk.disk_name)
                        if ns.queue not in rq_list:
                            rq_list.append(ns.queue)
                else:
                    ns_head = readSU("struct nvme_ns_head", disk.private_data)
                    if ns_head:
                        for ns in readSUListFromHead(ns_head.list, "siblings", "struct nvme_ns"):
                            rq_names[ns.queue] = str(ns.disk.disk_name)
                            if ns.queue not in rq_list:
                                rq_list.append(ns.queue)
    else:

        nvme_ns_head_ops_sym_addr = sym2addr("nvme_ns_head_ops")
        nvme_fops_sym_addr = sym2addr("nvme_fops")

        for queue in rq_list:
            disk = nvme_rq_to_gendisk(queue)
            if disk:
                if disk.fops == nvme_ns_head_ops_sym_addr:
                    ns_head = readSU("struct nvme_ns_head", disk.private_data)
                    head_list.append(queue)

                    if ns_head:
                        for ns in readSUListFromHead(ns_head.list, "siblings", "struct nvme_ns"):
                            rq_names[ns.queue] = str(ns.disk.disk_name)
                            if ns.queue not in rq_list:
                                rq_list.append(ns.queue)

                elif disk.fops == nvme_fops_sym_addr:
                    rq_names[queue] = disk.disk_name
                    if queue not in rq_list:
                        rq_list.append(queue)

    rq_list[:] = (value for value in rq_list if value not in head_list)

    return rq_list, head_list, admin_list

def special_nvme_queue_name_rules(queue):

    try:

        if queue.mq_ops == sym2addr("nvme_mq_admin_ops"):
            nvmeq = readSU("struct nvme_queue", queue.queue_hw_ctx[0].driver_data)
            rq_names[queue] = str(nvmeq.irqname)

        elif queue.mq_ops == sym2addr("nvme_mq_ops"):
            nvme_ns = readSU("struct nvme_ns", queue.queuedata)
            if nvme_ns.disk:
                rq_names[queue] = str(nvme_ns.disk.disk_name)
    except:
        pass

def trim_queue_list(rq_list, option):

    tlist = []

    for queue in rq_list:

        if "nvme" in rq_names[queue]:
            if (option == "devs" and "q" not in rq_names[queue]):
                tlist.append(queue)
            elif (option == "queues" and "q" in rq_names[queue]):
                tlist.append(queue)

    return tlist

def inc_removed():

    global rq_removed
    rq_removed += 1

def bio_mode_check(rq_list):

    if (member_size("struct request_queue", "make_request_fn") != -1):
        for rq in rq_list[:]:

            make_request_fn = rq.make_request_fn
            if (make_request_fn):
                if ("nvme_make_request" in addr2sym(make_request_fn)):
                    rq_list.remove(rq)
                    inc_removed()
                    pylog.info("WARNING: unsupported NVMe bio-mode detected. Some devices"
                        " not reported. Please check make_request_fn, mod,"
                        " and dev -d for more info.")

    return rq_list

def request_queue_sort_key(queue):

    if (rq_names[queue]):

        if (len(rq_names[queue]) > 7):
            return rq_names[queue]

        return "{}{:>6}".format(rq_names[queue][0:2], rq_names[queue][2:])

    else:
        return "Unknown"

def verify_ctrl_ops(ctrl_list):

    for ctrl in ctrl_list:
        ops_name = addr2sym(ctrl.ops)

        if (ops_name is None):
            pylog.info("WARNING: nvme_ctrl {:16x} with no ops detected. Out-of-box"
                " driver present?".format(ctrl))
            return 0

        elif ("nvme_pci_ctrl_ops" not in ops_name and "nvme_loop_ctrl_ops" not
            in ops_name and "nvme_rdma_ctrl_ops" not in ops_name and
            "nvme_fc_ctrl_ops" not in ops_name and "nvme_tcp_ctrl_ops" not in ops_name):
            pylog.info("WARNING: nvme_ctrl {:16x} detected with no accepted ops string."
                "Out-of-box driver present?".format(ctrl))
            return 0

def verify_queue_count(rq_list):

    dev_count = 0
    for dev in exec_crash_command_bg("dev -d").splitlines():
        if "nvme" in dev:
            dev_count += 1

    if (dev_count > len(rq_list)):
        pylog.info("WARNING: request_queue count ({}) is less than namespace"
          " count ({})! Some devices may not be displayed!".format(len(rq_list), dev_count))

def get_nvme_queues():

    rq_list = []

    rq_list = get_nvme_blockdev_queues(rq_list)
    rq_list = get_nvme_inode_blockdev_queues(rq_list)
    rq_list = get_nvme_mq_queues(rq_list)
    rq_list = get_nvme_gendisk_queues(rq_list)
    rq_list, head_list, admin_list = get_nvme_subqueues(rq_list)

    rq_list += list(set(rq_list))

    for key in rq_names.keys():
        if rq_names[key] == "Unknown":
            special_nvme_queue_name_rules(key)

    rq_list = trim_queue_list(rq_list, "devs")

    verify_queue_count(rq_list + head_list)

    rq_list = bio_mode_check(rq_list)
    rq_list.sort(key=request_queue_sort_key)

    return rq_list

def get_nvme_ctrls():

    ctrl_list = []
    rq_list = get_nvme_queues()

    for rq in rq_list:

        ns = readSU("struct nvme_ns", rq.queuedata)
        if ns != 0:
            if ns.ctrl != 0 and ns.ctrl not in ctrl_list:
                ctrl_list.append(ns.ctrl)

    if (ctrl_list):
        verify_ctrl_ops(ctrl_list)
    else:
        if (rq_removed):
            print("Exiting... no supported NVMe controllers present.")
        else:
            print("Exiting... no NVMe controllers present.")

    return ctrl_list

def build_list(list_base, spec):

    item_list = []

    if (spec == "ns" and struct_exists("struct nvme_ns")):
        for ctrl in list_base:
            for ns in readSUListFromHead(ctrl.namespaces, "list", "struct nvme_ns"):
                item_list.append(ns)

    if (spec == "dev"):
        for ctrl in list_base:
            ops_name = addr2sym(ctrl.ops)
            if ("nvme_pci_ctrl_ops" in ops_name):
                if (struct_exists("struct nvme_dev")):
                    item_list.append(container_of(ctrl, "struct nvme_dev", "ctrl"))
                    ops_string[item_list[-1]] = "pci"
                else:
                    pylog.info("ERROR: struct nvme_dev does not exist.")

            elif ("nvme_loop_ctrl_ops" in ops_name):
                if (struct_exists("struct nvme_loop_ctrl")):
                    item_list.append(container_of(ctrl, "struct nvme_loop_ctrl", "ctrl"))
                    ops_string[item_list[-1]] = "loop"
                else:
                    pylog.info("ERROR: struct nvme_loop_ctrl does not exist.")
            elif ("nvme_rdma_ctrl_ops" in ops_name):
                if (struct_exists("struct nvme_rdma_ctrl")):
                    item_list.append(container_of(ctrl, "struct nvme_rdma_ctrl", "ctrl"))
                    ops_string[item_list[-1]] = "rdma"
                else:
                    pylog.info("ERROR: struct nvme_rdma_ctrl does not exist.")
            elif ("nvme_tcp_ctrl_ops" in ops_name):
                if (struct_exists("struct nvme_tcp_ctrl")):
                    item_list.append(container_of(ctrl, "struct nvme_tcp_ctrl", "ctrl"))
                    ops_string[item_list[-1]] = "tcp"
                else:
                    pylog.info("ERROR: struct nvme_tcp_ctrl does not exist.")
            elif ("nvme_fc_ctrl_ops" in ops_name):
                if (struct_exists("struct nvme_fc_ctrl")):
                    item_list.append(container_of(ctrl, "struct nvme_fc_ctrl", "ctrl"))
                    ops_string[item_list[-1]] = "fc"
                else:
                    pylog.info("ERROR: struct nvme_fc_ctrl does not exist.")

    if (spec == "qid"):
        item_list = list(range(list_base))
        for qid in item_list:
            item_list[qid] = qid

    if (spec == "sub"):
        if struct_exists("struct nvme_subsystem"):
            for ctrl in list_base:
                if (ctrl.subsys not in item_list):
                    item_list.append(ctrl.subsys)
        else:
            pylog.info("ERROR: struct nvme_subsystem does not exist.")

    return item_list

def suffix(size):

    if size == 0:
        return "0 B"

    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)

    return "{:<3.0f} {:>3s}".format(s, size_name[i])

def ns_format(ns):

    lba = suffix(int(1 << ns.lba_shift))
    ms = ns.ms

    return "{} + {:<2d}B".format(lba, ms)

def pr_quirks(ctrl, enum_quirks):

    quirk_list = []

    if (not ctrl.quirks):
        return "None"

    for k, v in enum_quirks.items():
        if (ctrl.quirks & enum_quirks[k]):
            quirk_list.append(k)

    return " | ".join(quirk_list)

def pr_io_queues(origin):

    io_queues = "{{{}, {}, {}}}".format(origin.io_queues[0],
        origin.io_queues[1], origin.io_queues[2])

    return io_queues

def get_nvme_queue_tagset(nvme_queue):

    if (not nvme_queue.qid):
        return nvme_queue.dev.admin_tagset.tags[0]

    return nvme_queue.dev.tagset.tags[nvme_queue.qid - 1]

def pr_cap(ns):

    if hd_struct_exists:
        ns_size = ns.disk.part0.nr_sects * (1 << ns.lba_shift)
    else:
        if (member_size("struct block_device", "bd_nr_sectors") != -1):
            ns_size = ns.disk.part0.bd_nr_sectors * (1 << ns.lba_shift)
        else:
            ns_size = ns.disk.part0.bd_inode.i_size

    return suffix(ns_size)

def pr_ctrl_name(origin, match_name):

    if (match_name == "ctrl"):
        ctrl_name = member_check("nvme_ctrl", "ctrl_device", origin,
            "origin.ctrl_device.kobj.name", "origin.device.kobj.name")
    elif (match_name == "dev"):
        ctrl_name = member_check("nvme_ctrl", "ctrl_device", origin,
            "origin.ctrl.ctrl_device.kobj.name", "origin.ctrl.device.kobj.name")

    return ctrl_name

def pr_ctrl_state(ctrl):

    try:
        enum_nvme_state = EnumInfo("enum nvme_ctrl_state")

    except TypeError:

        _ctrl_states = '''
        #define NVME_CTRL_RESETTING    0
        #define NVME_CTRL_REMOVING     1
        '''
        ctrl_states = CDefine(_ctrl_states)

        dev = container_of(ctrl, "struct nvme_dev", "ctrl")
        if (dev.flags & ctrl_states['NVME_CTRL_RESETTING']):
            return "NVME_CTRL_RESETTING"
        elif (dev.flags & ctrl_states['NVME_CTRL_REMOVING']):
            return "NVME_CTRL_REMOVING"
        else:
            return "None"

    return enum_nvme_state.getnam(ctrl.state)

def match_args(arglist, match_names, match_source):

    keep_list = []

    for arg in arglist:
        if (arg not in match_names):
            print("Error: {}: {} not found.".format(match_args.__name__, arg))
    for name in match_names:
        if (name in arglist):
            keep_list.append(match_source[match_names.index(name)])

    return keep_list

def __arg_prep(args, item_list, match_name):

    item_names = []
    arglist = []

    if (match_name == "ns"):
        for item in item_list:
            item_names.append(part0_to_name(item.disk.part0))

    elif (match_name == "dev" or match_name == "ctrl"):
        for item in item_list:
            item_names.append(pr_ctrl_name(item, match_name))

    elif (match_name == "qid"):
        item_list = item_names = build_list(item_list, match_name)

    elif (match_name == "subs"):
        for item in item_list:
            item_names.append(item.dev.kobj.name)

    if (match_name == "qid"):
        for arg in args.split(","):
            try:
                arglist.append(int(arg))
            except ValueError:
                print("QID Error. Bad argument \"{}\" supplied".format(arg))
    else:
        arglist = args.split(",")

    return match_args(arglist, item_names, item_list)

def arg_prep(args, item_list, match_name):

    if (match_name == "qid" and args == "None" or args == -1):
        return build_list(item_list, "qid")
    elif (args == "None"):
        return item_list

    return __arg_prep(args, item_list, match_name)

def member_check(struct, member, origin, pres, notpres):

    sname = "struct " + struct

    if (member_size(sname, member) != -1):
        return eval(pres)

    elif ("unavail" not in notpres):
        return eval(notpres)

    return "<unavailable>"

def nvme_taint_check():

    modlist = []
    tmods = exec_crash_command_bg('mod -t')

    for t in tmods.splitlines():

        if "nvme" in t:
            mod = t.split()[0] + "(" + t.split()[1] + ")"
            modlist.append(mod)

    if (modlist):
        pylog.info("WARNING: potentially out-of-box or tech-preview modules "
        "loaded: {}. See 'mod -t' for more information.".format(", ".join(modlist)))

def pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats):

    print("\n\t\tTagset:\t\t\tAdminTagset:\n\t\t================\t================\n"
        "Map:\t\t{:<16}\t{:<16}\nNrMaps:\t\t{:<16}\t{:<16}\nNrHWQueues:\t{:<16}\t{:<16}"
        "\nQDepth:\t\t{:<16}\t{:<16}\nCmdSize:\t{:<16}\t{:<16}\nNumaNode:\t{:<16}\t"
        "{:<16}\nTimeout:\t{:<16}\t{:<16}\nFlags:\t\t{:<16}\t{:<16}".format(map,
        admin_map, nr_maps, admin_nr_maps, ts.nr_hw_queues, ats.nr_hw_queues,
        ts.queue_depth, ats.queue_depth, ts.cmd_size, ats.cmd_size, ts.numa_node,
        ats.numa_node, ts.timeout, ats.timeout, hex(ts.flags), hex(ats.flags)))

def show_nvme_subsystems(sub_list, args):

    sub_list = arg_prep(args, sub_list, "subs")
    sub_dict = {}
    sub_trans  = {}

    for sub in sub_list:
        sub_dict[sub] = {}
        ctrls = readSUListFromHead(sub.ctrls, "subsys_entry", "struct nvme_ctrl")
        for ctrl in ctrls:
            trans = ctrl.ops.name
            sub_trans[ctrl] = trans
            for ns in readSUListFromHead(ctrl.namespaces, "list", "struct nvme_ns"):
                if (member_size("struct nvme_ns", "head") != -1):
                    if (ns.head):
                        sub_dict[sub][ns] = ns.head
                    else:
                        sub_dict[sub][ns] = ""
                else:
                    sub_dict[sub][ns] = ""

    heads = defaultdict(list)
    subs = defaultdict(list)

    for sub in sub_dict.keys():
        for ns, ns_head in sub_dict[sub].items():
            if (sub_dict[sub][ns]):
                heads[ns_head].append(ns)
            else:
                subs[sub].append(ns)

    if (heads):
        for ns_head, ns in heads.items():
            spacer = "`-+-"
            print("\n{} [{:#x}] - NQN={}".format(ns_head.subsys.dev.kobj.name, ns_head.subsys,
                ns_head.subsys.subnqn))
            for ns in heads[ns_head]:
                if (member_size("struct nvme_ns", "ana_state") != -1):
                    ana_state = ns.ana_state
                else:
                    ana_state = ""
                print("{}{}:{} [{:#x}] {}: [{:#x}] {}".format(spacer, pr_ctrl_name(ns.ctrl, "ctrl"),sub_trans[ns.ctrl],
                ns.ctrl, part0_to_name(ns.disk.part0), ns, ana_state))
                spacer = "  +-"

    if (subs):
        for sub, ns_list in subs.items():
            spacer = "`-+-"
            print("\n{} [{:#x}] - NQN={}".format(sub.dev.kobj.name, sub, sub.subnqn))
            for ns in ns_list:
                print("{}{}: [{:#x}] {}: [{:#x}]".format(spacer, pr_ctrl_name(ns.ctrl, "ctrl"), ns.ctrl,
                    part0_to_name(ns.disk.part0), ns))
                spacer = "  +-"

def show_nvme_list(ns_list, args):

    ns_list = arg_prep(args, ns_list, "ns")

    if (ns_list):

        print("\n{:<16s} {:<20s} {:40s} {:<9s} {:<18s} {:<16s} {:<8s}".format("Node",
            "SN", "Model", "Namespace", "Capacity(gendisk)", "Format", "FW Rev"))
        print("{:<16s} {:<20s} {:40s} {:<9s} {:<18s} {:<16s} {:<8s}".format("----------------",
            "--------------------", "----------------------------------------", "---------",
            "------------------", "----------------", "--------"))

    for ns in ns_list:

        serial = member_check("nvme_ctrl", "subsys", ns, "origin.ctrl.subsys.serial",
            "origin.ctrl.serial")
        model = member_check("nvme_ctrl", "subsys", ns, "origin.ctrl.subsys.model",
            "origin.ctrl.model")
        firmware_rev = member_check("nvme_ctrl", "subsys", ns,
            "origin.ctrl.subsys.firmware_rev", "origin.ctrl.firmware_rev")

        ns_id = member_check("nvme_ns", "head", ns, "origin.head.ns_id", "origin.ns_id")

        print("/dev/{:<11} {:<20s} {:40s} {:<9d} {:<18s} {:<16s} {:<8s}".
            format(part0_to_name(ns.disk.part0), serial, model, ns_id,
            pr_cap(ns), ns_format(ns), firmware_rev))

def show_nvme_ctrl(nvme_ctrls, args):

    enum_quirks = EnumInfo("enum nvme_quirks")

    nvme_ctrls = arg_prep(args, nvme_ctrls, "ctrl")

    for ctrl in nvme_ctrls:

        print("\n{:<10}  {:<16}  {:<21}  {:<16}  {:<16}  {:<16}  {:<16}".format("Name",
            "Ctrl Addr", "Namespaces(list_head)", "AdminQ", "ConnectQ", "Subsystem",
            "Ctrl Device"))
        print("{:<10}  {:<16}  {:<21}  {:<16}  {:<16}  {:<16}  {:<16}".
            format("----------", "----------------", "---------------------",
            "----------------", "----------------", "----------------", "----------------"))

        subsys = member_check("nvme_ctrl", "subsys", ctrl, "hex(origin.subsys)[2:]", "unavail")
        max_segments = member_check("nvme_ctrl", "max_segments", ctrl, "origin.max_segments",
            "unavail")
        ctrl_device = member_check("nvme_ctrl", "ctrl_device", ctrl, "hex(origin.ctrl_device)[2:]",
            "unavail")
        qcount = member_check("nvme_ctrl", "queue_count", ctrl, "origin.queue_count", "unavail")
        connect_q = member_check("nvme_ctrl", "connect_q", ctrl, "hex(origin.connect_q)[2:]",
            "unavail")
        page_size = member_check("nvme_ctrl", "page_size", ctrl, "origin.page_size", "unavail")

        name = pr_ctrl_name(ctrl, "ctrl")
        namespace_lh = readSU("struct list_head", long(ctrl.namespaces))

        print("{:<10}  {:<16x}  {:<21x}  {:<16x}  {:<16}  {:<16}  {:<16}".
            format(name, ctrl, namespace_lh, ctrl.admin_q, connect_q, subsys, ctrl_device))
        print("\nQuirks:\t\t{}\nNumQueues:\t{}\nCtrlState:\t{}\nMaxHWSectors:\t{}\n"
            "MaxSegments:\t{}\nPageSize:\t{}". format(pr_quirks(ctrl, enum_quirks), qcount,
            pr_ctrl_state(ctrl), ctrl.max_hw_sectors, max_segments, page_size))

def show_nvme_ns(ns_list, args):

    ns_list = arg_prep(args, ns_list, "ns")

    if (ns_list):

        print("\n{:<10}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<5}".format("Name",
            "NS Addr", "NS Head", "RequestQ", "Gendisk", "Siblings", "Flags"))
        print("{:<10}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<5}".format("----------",
            "----------------", "----------------", "----------------", "----------------",
            "----------------", "-----"))

    for ns in ns_list:

        ns_head = member_check("nvme_ns", "head", ns, "hex(origin.head)[2:]", "unavail")
        ns_siblings = member_check("nvme_ns", "siblings", ns, "hex(origin.siblings)[2:]", "unavail")

        print("{:<10}  {:<16x}  {:<16}  {:<16x}  {:<16x}  {:<16}  {:<5}".
            format(part0_to_name(ns.disk.part0), ns, ns_head, ns.queue, ns.disk,
                ns_siblings, hex(ns.flags)))

def show_nvme_rdma_dev(rdma_dev):

    print("\n{:<9}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("rdma:Name", "RDMACtrlAddr", "Queues", "Tagset", "AdminTagset",
        "ErrWork", "Device", "ReconnectWork"))
    print("{:<9}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("---------", "----------------", "----------------", "----------------",
        "----------------", "----------------", "----------------", "----------------"))

    name = pr_ctrl_name(rdma_dev.ctrl, "ctrl")
    ts = rdma_dev.tag_set
    ats = rdma_dev.admin_tag_set

    print("{:<9}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".
        format(name, rdma_dev, rdma_dev.queues, ts, ats, rdma_dev.err_work,
        rdma_dev.device, rdma_dev.reconnect_work))

    map = member_check("blk_mq_tag_set", "map", rdma_dev, 'hex(Addr(origin.tag_set, "map"))[2:]',
        "unavail")
    admin_map = member_check("blk_mq_tag_set", "map", rdma_dev, 'hex(Addr(origin.admin_tag_set,'
        '"map"))[2:]', "unavail")
    nr_maps = member_check("blk_mq_tag_set", "nr_maps", rdma_dev, 'str(origin.tag_set.nr_maps)',
        "unavail")
    admin_nr_maps = member_check("blk_mq_tag_set", "nr_maps", rdma_dev, 'str(origin.admin_tag_set'
        '.nr_maps)', "unavail")

    pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats)

def show_nvme_rdma_queues(rdma_dev, qid):

    queue_count = member_check("nvme_ctrl", "queue_count", rdma_dev, "origin.ctrl.queue_count",
        "origin.queue_count")

    qid_list = arg_prep(qid, queue_count, "qid")

    for queue in qid_list:

        print("\n{:<14}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
            format("rdma:Ctrl[qid]", "Queue Addr", "RSPRing", "RDMACtrl", "RDMADevice", "IB CQ",
            "IB QP", "RDMA CMID"))
        print("{:<14}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".format("--------------",
            "----------------", "----------------", "----------------", "----------------",
            "----------------", "----------------", "----------------"))

        q = rdma_dev.queues[queue]
        name = pr_ctrl_name(rdma_dev.ctrl, "ctrl")
        segs = member_check("nvme_rdma_device", "num_inline_segments", q.device,
            "origin.num_inline_segments", "unavail")

        ctrl_queue_id = name + "[" + str(queue) + "]"

        print("{:<14}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".
            format(ctrl_queue_id, q, q.rsp_ring, q.ctrl, q.device, q.ib_cq, q.qp, q.cm_id))

        print("\nIBDevice:\t{:<14x}\tIBDevName:\t{:<14}\nInlineSegs:\t{:<14x}\t\tCMID:\t\t"
            "{:<14x}\nQSize:\t\t{:<14}\t\tFlags:\t\t{:<14}".format(q.device.dev, q.device.dev.name,
            segs, q.cm_id, q.queue_size, hex(q.flags)))

def show_nvme_loop_dev(loop_dev):

    print("\n{:<9}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("loop:Name", "LoopCtrlAddr", "Queues", "Tagset", "AdminTagset",
        "LoopIOD", "TargetCtrl", "TargetPort"))
    print("{:<9}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("---------", "----------------", "----------------", "----------------",
        "----------------", "----------------", "----------------", "----------------"))

    name = pr_ctrl_name(loop_dev.ctrl, "ctrl")
    ts = loop_dev.tag_set
    ats = loop_dev.admin_tag_set

    if (symbol_exists("nvmet_loop_port")):
        tport = readSymbol("nvmet_loop_port")
    else:
        tport = loop_dev.port

    print("{:<9}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".
        format(name, loop_dev, loop_dev.queues, ts, ats, loop_dev.async_event_iod,
            loop_dev.target_ctrl, tport))

    map = member_check("blk_mq_tag_set", "map", loop_dev, 'hex(Addr(origin.tag_set, "map"))[2:]',
        "unavail")
    admin_map = member_check("blk_mq_tag_set", "map", loop_dev, 'hex(Addr(origin.admin_tag_set,'
        '"map"))[2:]', "unavail")

    nr_maps = member_check("blk_mq_tag_set", "nr_maps", loop_dev, 'str(origin.tag_set.nr_maps)',
        "unavail")
    admin_nr_maps = member_check("blk_mq_tag_set", "nr_maps", loop_dev, 'str(origin.admin_tag_set'
        '.nr_maps)', "unavail")

    pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats)

def show_nvme_loop_queues(loop_dev, qid):

    queue_count = member_check("nvme_ctrl", "queue_count", loop_dev, "origin.ctrl.queue_count",
        "origin.queue_count")

    qid_list = arg_prep(qid, queue_count, "qid")

    for queue in qid_list:

        print("\n{:<14}  {:<16}  {:<16}  {:<16}  {:<16}  {:<8}".format("loop:Ctrl[qid]",
            "Queue Addr", "NVMeCQ", "NVMeSQ", "LoopCtrlAddr", "Flags"))
        print("{:<14}  {:<16}  {:<16}  {:<16}  {:<16}  {:<8}".format("--------------",
            "----------------", "----------------", "----------------", "----------------",
            "--------"))

        q = loop_dev.queues[queue]

        if (q.nvme_cq.qid == q.nvme_sq.qid):
            qid = q.nvme_cq.qid
        else:
            pylog.info("WARNING: SQ and CQ qids do not match!")

        name = pr_ctrl_name(loop_dev.ctrl, "ctrl")
        flags = member_check("nvme_loop_queue", "flags", q, "hex(origin.flags)", "unavail")

        ctrl_queue_id = name + "[" + str(qid) + "]"

        print("{:<14}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<8}".format(ctrl_queue_id, q, q.nvme_cq,
            q.nvme_sq, q.ctrl, flags))

        print("\nCQSize:\t\t{:<14}\t\tSQSize:\t\t{:<14}\nSQNVMeTCtrl:\t{:<14x}\tSQPerCPURef:\t"
            "{:<14x}\nSQFreeDone:\t{:<14x}\tSQConfirmDone:\t{:<14x}".format(q.nvme_cq.size,
            q.nvme_sq.size, q.nvme_sq.ctrl, q.nvme_sq.ref, q.nvme_sq.free_done, q.nvme_sq.confirm_done))

def show_nvme_fc_dev(fc_dev):

    print("\n{:<7}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("fc:Name", "FC CtrlAddr", "Queues", "Tagset", "AdminTagset", "LPort",
        "RPort", "Flags"))
    print("{:<7}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("-------", "----------------", "----------------", "----------------",
        "----------------", "----------------", "----------------", "----------------"))

    name = pr_ctrl_name(fc_dev.ctrl, "ctrl")
    ts = fc_dev.tag_set
    ats = fc_dev.admin_tag_set

    print("{:<7}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16}".
        format(name, fc_dev, fc_dev.queues, ts, ats, fc_dev.lport, fc_dev.rport,
        hex(fc_dev.flags)))

    map = member_check("blk_mq_tag_set", "map", fc_dev, 'hex(Addr(origin.tag_set, "map"))[2:]',
        "unavail")
    admin_map = member_check("blk_mq_tag_set", "map", fc_dev, 'hex(Addr(origin.admin_tag_set,'
        '"map"))[2:]', "unavail")

    nr_maps = member_check("blk_mq_tag_set", "nr_maps", fc_dev, 'str(origin.tag_set.nr_maps)',
        "unavail")
    admin_nr_maps = member_check("blk_mq_tag_set", "nr_maps", fc_dev, 'str(origin.admin_tag_set'
        '.nr_maps)', "unavail")

    pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats)

def show_nvme_fc_queues(fc_dev, qid):

    queue_count = member_check("nvme_ctrl", "queue_count", fc_dev, "origin.ctrl.queue_count",
        "origin.queue_count")

    qid_list = arg_prep(qid, queue_count, "qid")

    for queue in qid_list:

        print("\n{:<12}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".format("fc:Ctrl[qid]",
            "Queue Addr", "FCCtrl", "Device", "HCTX", "LLDDHandle"))
        print("{:<12}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".format("------------",
            "----------------", "----------------", "----------------", "----------------",
            "----------------"))

        q = fc_dev.queues[queue]
        name = pr_ctrl_name(fc_dev.ctrl, "ctrl")
        ctrl_queue_id = name + "[" + str(q.qnum) + "]"

        print("{:<12}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".format(ctrl_queue_id, q, q.ctrl,
            q.dev, q.hctx, q.lldd_handle))

        print("\nQNum:\t\t{:<14}\tRQCnt:\t\t{:<14}\nSeqNo:\t\t{:<14}\tConnID:\t\t"
            "{:<14}\nCSN:\t\t{:<14}\tFlags:\t\t{:<14}".format(q.qnum, q.rqcnt, q.seqno,
            q.connection_id, atomic_t(q.csn), hex(q.flags)))

def show_nvme_tcp_dev(tcp_dev):

    print("\n{:<7}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("tcp:Name", "TCP CtrlAddr", "Queues", "Tagset", "AdminTagset"))
    print("{:<7}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("-------", "----------------", "----------------", "----------------",
        "----------------", "----------------", "----------------", "----------------"))

    name = pr_ctrl_name(tcp_dev.ctrl, "ctrl")
    ts = tcp_dev.tag_set
    ats = tcp_dev.admin_tag_set
    io_queues = member_check("nvme_dev", "io_queues", tcp_dev, "pr_io_queues(origin)", "unavail")

    print("{:<7}  {:<16x}  {:<16x}  {:<16x}  {:<16}".
        format(name, tcp_dev, tcp_dev.queues, ts, hex(ats)))

    print("\nIOQueues:\t{}".format(io_queues))


    map = member_check("blk_mq_tag_set", "map", tcp_dev, 'hex(Addr(origin.tag_set, "map"))[2:]',
        "unavail")
    admin_map = member_check("blk_mq_tag_set", "map", tcp_dev, 'hex(Addr(origin.admin_tag_set,'
        '"map"))[2:]', "unavail")

    nr_maps = member_check("blk_mq_tag_set", "nr_maps", tcp_dev, 'str(origin.tag_set.nr_maps)',
        "unavail")
    admin_nr_maps = member_check("blk_mq_tag_set", "nr_maps", tcp_dev, 'str(origin.admin_tag_set'
        '.nr_maps)', "unavail")

    pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats)

def show_nvme_tcp_queues(tcp_dev, qid):

    queue_count = member_check("nvme_ctrl", "queue_count", tcp_dev, "origin.ctrl.queue_count",
        "origin.queue_count")

    qid_list = arg_prep(qid, queue_count, "qid")

    for queue in qid_list:

        print("\n{:<12}  {:<16}  {:<16}  {:<16}  {:<16}".format("tcp:Ctrl[qid]",
            "Queue Addr", "TCPCtrl", "SOCK", "REQUEST"))
        print("{:<12}  {:<16}  {:<16}  {:<16}  {:<16}".format("------------",
            "----------------", "----------------", "----------------", "----------------"))

        q = tcp_dev.queues[queue]
        name = pr_ctrl_name(tcp_dev.ctrl, "ctrl")
        ctrl_queue_id = name + "[" + str(queue) + "]"

        print("{:<12}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".format(ctrl_queue_id, q, q.ctrl,
            q.sock, q.request))

def show_nvme_pci_dev(pci_dev):

    print("\n{:<8}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("pci:Name", "DevAddr", "Queues", "Tagset", "AdminTagset", "Ctrl Addr",
        "PagePool", "SmallPool"))
    print("{:<8}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".
        format("--------", "----------------", "----------------", "----------------",
        "----------------", "----------------", "----------------", "----------------"))

    io_queues = member_check("nvme_dev", "io_queues", pci_dev, "pr_io_queues(origin)", "unavail")
    name = pr_ctrl_name(pci_dev.ctrl, "ctrl")
    num_vecs = member_check("nvme_dev", "num_vecs", pci_dev, "origin.num_vecs", "unavail")

    ts = pci_dev.tagset
    ats = pci_dev.admin_tagset

    print("{:<8}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".
        format(name, pci_dev, pci_dev.queues, ts, ats, pci_dev.ctrl, pci_dev.prp_page_pool,
        pci_dev.prp_small_pool))

    print("\nOnlineQueues:\t{}\nMaxQID:\t\t{}\nIOQueues:\t{}\nNumVecs:\t{}\nQDepth:\t\t{}\n"
        "DBStride\t{}".format(pci_dev.online_queues, pci_dev.max_qid, io_queues, num_vecs,
        pci_dev.q_depth, pci_dev.db_stride))

    map = member_check("blk_mq_tag_set", "map", pci_dev, 'hex(Addr(origin.tagset, "map"))[2:]',
        "unavail")
    admin_map = member_check("blk_mq_tag_set", "map", pci_dev, 'hex(Addr(origin.admin_tagset,'
        '"map"))[2:]', "unavail")

    nr_maps = member_check("blk_mq_tag_set", "nr_maps", pci_dev, 'str(origin.tagset.nr_maps)',
        "unavail")
    admin_nr_maps = member_check("blk_mq_tag_set", "nr_maps", pci_dev, 'str(origin.admin_tagset'
        '.nr_maps)', "unavail")

    pr_tagset_info(map, admin_map, nr_maps, admin_nr_maps, ts, ats)

def show_nvme_pci_queues(pci_dev, qid):

    queue_count = member_check("nvme_ctrl", "queue_count", pci_dev, "origin.ctrl.queue_count",
        "origin.queue_count")

    qid_list = arg_prep(qid, queue_count, "qid")

    for queue in qid_list:

        print("\n{:<13}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".format("pci:Ctrl[qid]",
            "Queue Addr", "DMA Dev", "NVMe Dev", "SQ Cmds", "Completion", "Tags"))
        print("{:<13}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}  {:<16}".format("-------------",
            "----------------", "----------------", "----------------", "----------------",
            "----------------", "----------------"))

        q = pci_dev.queues[queue]
        name = pr_ctrl_name(pci_dev.ctrl, "ctrl")
        ctrl_queue_id = name + "[" + str(q.qid) + "]"
        q_dmadev = member_check("nvme_queue", "q_dmadev", q, "hex(origin.q_dmadev)[2:]", "unavail")

        tags = member_check("nvme_queue", "tags", q, "origin.tags", "get_nvme_queue_tagset(origin)")

        print("{:<13}  {:<16x}  {:<16}  {:<16x}  {:<16x}  {:<16x}  {:<16x}".format(ctrl_queue_id,
            q, q_dmadev, q.dev, q.sq_cmds, q.cqes, tags))

        last_sq_tail = member_check("nvme_queue", "last_sq_tail", pci_dev, "origin.queues["
            + str(queue) + "].last_sq_tail", "unavail")

        last_cq_head = member_check("nvme_queue", "last_cq_head", pci_dev, "origin.queues["
            + str(queue) + "].last_cq_head", "unavail")

        flags = member_check("nvme_queue", "flags", pci_dev, "hex(origin.queues["
            + str(queue) + "].flags)", "unavail")

        print("\nQDepth:\t\t{:<14}\tCQVector:\t{:<14}\nSQTail:\t\t{:<14}\tLastSQTail:\t"
            "{:<14}\nCQHead:\t\t{:<14}\tLastCQHead:\t{:<14}\nQiD:\t\t{:<14}\tCQPhase:\t{:<14}"
            "\nFlags:\t\t{:<14}\tQCount:\t\t{:<14}".format(q.q_depth, q.cq_vector, q.sq_tail,
            last_sq_tail, q.cq_head, last_cq_head, q.qid, q.cq_phase, flags, queue_count))

def show_nvme_devs(dev_list, args):

    dev_list = arg_prep(args, dev_list, "dev")

    for dev in dev_list:
        if "pci" in ops_string[dev]:
            show_nvme_pci_dev(dev)
        elif "loop" in ops_string[dev]:
            show_nvme_loop_dev(dev)
        elif "rdma" in ops_string[dev]:
            show_nvme_rdma_dev(dev)
        elif "fc" in ops_string[dev]:
            show_nvme_fc_dev(dev)
        elif "tcp" in ops_string[dev]:
            show_nvme_tcp_dev(dev)

def show_nvme_queues(dev_list, args, qid):

    dev_list = arg_prep(args, dev_list, "dev")

    for dev in dev_list:
        if "pci" in ops_string[dev]:
            show_nvme_pci_queues(dev, qid)
        elif "loop" in ops_string[dev]:
            show_nvme_loop_queues(dev, qid)
        elif "rdma" in ops_string[dev]:
            show_nvme_rdma_queues(dev, qid)
        elif "fc" in ops_string[dev]:
            show_nvme_fc_queues(dev, qid)
        elif "tcp" in ops_string[dev]:
            show_nvme_tcp_queues(dev, qid)

def nvme_check_ctrl_states(nvme_ctrls):

    alt_state = 0

    for ctrl in nvme_ctrls:
        ctrl_state = pr_ctrl_state(ctrl)

        if (ctrl_state != "None" and ctrl_state != "NVME_CTRL_LIVE"):
            if (alt_state == 0):
                print("{}".format("\n"), end="")
                alt_state = 1
            name = pr_ctrl_name(ctrl, "ctrl")

            print("WARNING: {} in state {}".format(name, ctrl_state))

def nvme_check(nvme_ctrls):

    nvme_check_ctrl_states(nvme_ctrls)

def main():

    import argparse
    parser =  argparse.ArgumentParser()

    parser.add_argument("-l", "--list", dest="list", default = 0, metavar="NS",
        const="None", nargs="?", help="list nvme namespaces vpd data and capacity")

    parser.add_argument("-c", "--ctrl", dest="ctrl", default = 0,
        const="None", nargs="?", help="show nvme controller information (nvme_ctrl)")

    parser.add_argument("-n", "--ns", dest="ns", default=0,
        const="None", nargs="?", help="show nvme namespace information (nvme_ns)")

    parser.add_argument("-d", "--dev", dest="dev", default=0, metavar="CTRL",
        const="None", nargs="?", help="show nvme device information (nvme_dev, "
        "nvme_loop_ctrl, nvme_rdma_ctrl, nvme_fc_ctrl, nvme_tcp_ctrl)")

    parser.add_argument("-q", "--queue", dest="queue", default=0, metavar="CTRL",
        const="None", nargs="?", help="show nvme queue information (nvme_queue, "
        "nvme_loop_queue, nvme_rdma_queue, nvme_fc_queue)")

    parser.add_argument("-i", "--qid", dest="qid", default=0,
        const="None", nargs="?", help="limit output by QID. for use with -q")

    parser.add_argument("-s", "--subsystem", dest="sub", default=0,
        const="None", nargs="?", help="show nvme subsystem information "
        "(nvme_subsystem)")

    parser.add_argument("-k", "--check", dest="check", default=0,
        action="store_true", help="check for common NVMe issues")

    args = parser.parse_args()

    mods = lsModules()
    if ("nvme" not in mods and "nvme_core" not in mods):
        print("Exiting... nvme not in use.")
        return 1

    if (not struct_exists("struct nvme_ctrl")):
        print("ERROR: struct nvme_ctrl does not exist.")
        return 1

    if (args.qid and not args.queue):
        print("Error: {-i,--qid} options only available with {-q,--queue}")
        return 1

    nvme_taint_check()

    try:

        nvme_ctrls = get_nvme_ctrls()

        if (nvme_ctrls):

            if (len(sys.argv) == 1):
                show_nvme_ctrl(nvme_ctrls, "None")

            else:

                if (args.ctrl):
                    show_nvme_ctrl(nvme_ctrls, args.ctrl)

                if (args.list or args.ns):
                    ns_list = build_list(nvme_ctrls, "ns")

                    if (ns_list):
                        if (args.list):
                            show_nvme_list(ns_list, args.list)
                        if (args.ns):
                            show_nvme_ns(ns_list, args.ns)
                    else:
                        pylog.info("ERROR: No nvme_ns structs found. Required for arguments"
                            "{-l,--list} and {-n,--ns}.")

                if (args.dev or args.queue):
                    dev_list = build_list(nvme_ctrls, "dev")

                    if (dev_list):
                        if (args.dev):
                            show_nvme_devs(dev_list, args.dev)
                        if (args.queue and args.qid):
                            show_nvme_queues(dev_list, args.queue, args.qid)
                        elif (args.queue):
                            show_nvme_queues(dev_list, args.queue, -1)
                    else:
                        pylog.info("ERROR: No nvme_dev structs found. Required for arguments"
                            "{-d,--dev} and {-q,--queue}.")

                if (args.sub):
                    sub_list = build_list(nvme_ctrls, "sub")

                    if (sub_list):
                        show_nvme_subsystems(sub_list, args.sub)

                if (args.check):
                    nvme_check(nvme_ctrls)

    except:

        traceback.print_exc()

        pylog.info("ERROR: For in-box modules, please report full command, full "
            "backtrace output, and core location to https://gitlab.cee.redhat.com/sbr-kernel"
            "/pykdump/issues")

if ( __name__ == '__main__'):
    main()
