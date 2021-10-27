# --------------------------------------------------------------------
# (C) Copyright 2006-2014 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2014-2015 Red Hat, Inc.
#
# Author: David Jeffery
#
# Contributor:
# - Milan P. Gandhi
#      Added following options:
#       -ll, --list  list multipath devices similar to 'multipath -ll'
#       --lvs        show lvm volume information similar to 'lvs' command
#       --lvuuid     show lvm volume and volume group's UUID
#       --pvs        show physical volume information similar to 'pvs' command
#      Added a check in '--check' option to verify if 'multipathd' is
#        blocked, along with scsi_wq, fc_wq
# - John Pittman - various enhancements
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

__version__ = "0.0.2"

from pykdump.API import *
from LinuxDump.trees import *
required_modules = ('dm_mod', 'dm_multipath', 'dm_log', 'dm_mirror',
                    'dm_queue_length', 'dm_round_robin', 'dm_service_time',
                    'dm_region_hash', 'dm_snapshot', 'dm_thin_pool', 'dm_raid')

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

from LinuxDump.Tasks import (TaskTable, Task, tasksSummary, ms2uptime,
     decode_tflags, print_namespaces_info, print_memory_stats, TASK_STATE)

from LinuxDump.BTstack import exec_bt, bt_summarize

lv_list = []

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

def lookup_field(obj, fieldname):
    segments = fieldname.split("[")
    while (len(segments) > 0):
        obj = getattr(obj, segments[0])
        if (len(segments) > 1):
            offset = segments[1].split("]")
            if (isinstance(obj, SmartString)):
                obj = obj[long(offset[0])]
            else:
                obj = obj.__getitem__(long(offset[0]))

            if ((len(offset) > 1) and offset[1]):
                # We've consumed one segment, toss it and replace the next
                # segment with a string witout the "]."
                segments = segments[1:]
                #FIXME: we need to drop a leading ".", but should check first
                segments[0] = offset[1][1:]
            else:
                return obj
        else:
            return obj
    return obj

#copied from scsishow.  This needs to go into a common module
def display_fields(display, fieldstr, usehex=0):
    for fieldname in fieldstr.split(","):
        field = lookup_field(display, fieldname)
#        field = display.Eval(fieldname)
        if (usehex or isinstance(field, StructResult) or
                      isinstance(field, tPtr)):
            try:
                print("   {}: {:<#10x}".format(fieldname, field), end='')
            except ValueError:
                print("   {}: {:<10}".format(fieldname, field), end='')
        else:
            print("   {}: {:<10}".format(fieldname, field), end='')

        if (fieldname == "flags"):
            if ((display.flags & (1 << 0)) or (display.flags & (1 << 1))
                or (display.flags & (1 << 5))):
                print("[Device suspended]", end='')

            if (display.flags & (1 << 2)):
                print("[Device frozen]", end='')

            if (display.flags & (1 << 4)):
                print("[Device is being deleted]", end='')

            if (symbol_exists("dm_queue_merge_is_compulsory")
                and (display.flags & (1 << 8))):
                print("[Device suspended internally]", end='')
            elif (not symbol_exists("dm_queue_merge_is_compulsory")
                and (display.flags & (1 << 7))):
                print("[Device suspended internally]", end='')

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

def get_size(gendisk):
    try:
        if (member_size("struct gendisk", "capacity") != -1):
            return (gendisk.capacity * 512 / 1048576)
        if struct_exists("struct hd_struct"):
            tmp_hd_struct = readSU("struct hd_struct", long(gendisk.part0))
            return (tmp_hd_struct.nr_sects * 512 / 1048576)
        inode = readSU("struct inode", gendisk.part0.bd_inode)
        return inode.i_size >> 9
    except:
        pylog.warning("Error in processing 'struct gendisk'", gendisk)
        pylog.warning("To debug this issue, you could manually examine "
                      "the contents of gendisk struct")
        return

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

def __set_multipath_scope(symbol):
    command = "set scope " + symbol
    with SuppressCrashErrors():
        exec_crash_command(command)

def set_multipath_scope():
    try:
        if ("dm_round_robin" in lsModules()):
            if (symbol_exists(".rr_create")):
                __set_multipath_scope(".rr_create")
            else:
                __set_multipath_scope("rr_create")
        elif ("dm_service_time" in lsModules()):
            if (symbol_exists(".st_create")):
                __set_multipath_scope(".st_create")
            else:
                __set_multipath_scope("st_create")
        elif ("dm_queue_length" in lsModules()):
            if (symbol_exists(".ql_create")):
                __set_multipath_scope(".ql_create")
            else:
                __set_multipath_scope("ql_create")
        return 1
    except:
        pylog.info("Error setting multipath scope")
        return 0

def unset_multipath_scope(is_set):
    if (is_set):
        try:
            if (symbol_exists(".dm_table_create")):
                exec_crash_command("set scope .dm_table_create")
            else:
                exec_crash_command("set scope dm_table_create")
        except:
            pylog.info("Error un-setting multipath scope")

def show_table_mpath_priogroup(prio):
    print(" {} 0 {} 1".format(prio.ps.type.name, prio.nr_pgpaths), end="")

    for path in readSUListFromHead(prio.pgpaths, "list", "struct pgpath"):
        path_info = readSU("struct path_info", path.path.pscontext)

        print(" {}:{} [{}] {}".format(path.path.dev.bdev.bd_dev >> 20,
            path.path.dev.bdev.bd_dev & 0xfffff,
            path.path.dev.bdev.bd_disk.disk_name, path_info.repeat_count), end="")

def show_mpath_info(prio, path_ops):
    for path in readSUListFromHead(prio.pgpaths, "list", "struct pgpath"):
        block_device = readSU("struct block_device", path.path.dev.bdev)
        if "sd_fops" in path_ops:
            path_dev = readSU("struct scsi_device", long(block_device.bd_disk.queue.queuedata))
            kobj_name = path_dev.sdev_gendev.kobj.name
        elif "nvme" in path_ops:
            path_dev = readSU("struct nvme_ns", long(block_device.bd_disk.queue.queuedata))
            path_ctrl = path_dev.ctrl
            if (member_size("struct nvme_ctrl", "subsys") != -1):
                path_subsys = "nvme_subsystem: {:#x} ".format(path_dev.ctrl.subsys)
            else:
                path_subsys = ""
            kobj_name = "{}:{}:{}:{}".format(path_dev.ctrl.instance, path_dev.instance,
                path_dev.ctrl.cntlid, path_dev.ns_id)
        else:
            kobj_name = "<unknown>"
            pylog.info("{}: {} ops not recognized".format(path.path.dev.bdev.bd_disk, path_ops))

        print("\n  `- {} {} {}:{}    ".format(kobj_name,
            block_device.bd_disk.disk_name,
            block_device.bd_dev >> 20,
            block_device.bd_dev & 0xfffff), end="")

        if ("sd_fops" in path_ops):
            try:
                enum_sdev_state = EnumInfo("enum scsi_device_state")
            except TypeError:
                enum_sdev_state = False
                pylog.info("{}: EnumInfo for enum_sdev_state failed"
                    .format(block_device.bd_disk.disk_name))

            if (enum_sdev_state is False):
                print("\t[scsi_device: {:#x} sdev_state: {}]".format(path_dev,
                    "--------"), end="")
            elif ('cciss' in block_device.bd_disk.disk_name):
                print("\t[Not a scsi device, skipping scsi_device struct!]", end="")
            else:
                try:
                    sdev_state = get_sdev_state(enum_sdev_state.getnam(path_dev.sdev_state))
                except:
                    if (path_dev.sdev_state == 9):
                        sdev_state = "SDEV_TRANSPORT_OFFLINE"
                    else:
                        sdev_state = "<Error in processing sdev_state>"
                print("\t[scsi_device: {:#x} sdev_state: {}]".format(path_dev, sdev_state), end="")

        elif "nvme" in path_ops:
            print("\t[{}nvme_ctrl: {:#x} nvme_ns: {:#x} state: {}]".format(path_subsys, path_ctrl,
                path_dev, pr_ctrl_state(path_dev.ctrl)), end="")

def show_multipath_list(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", md.map)

    target_name = get_dm_target_name(dm_table_map, name)
    if (not target_name or target_name != "multipath" ):
        return 0

    print("------------------------------------------------------------------------------------------")

    mpath = readSU("struct multipath", dm_table_map.targets.private)
    prio_groups = readSUListFromHead(mpath.priority_groups, "list", "struct priority_group")

    temp_prio_groups_list = readSU("struct list_head", mpath.priority_groups)
    temp_priority_group = readSU("struct priority_group", temp_prio_groups_list.next)
    temp_pgpath_list = readSU("struct list_head", temp_priority_group.pgpaths)
    temp_pgpath = readSU("struct pgpath", temp_pgpath_list.next)

    scope_set = set_multipath_scope()
    path_ops = addr2sym(temp_pgpath.path.dev.bdev.bd_disk.fops)

    try:
        if "sd_fops" in path_ops:
            temp_path = readSU("struct scsi_device", temp_pgpath.path.dev.bdev.bd_disk.queue.queuedata)
            vendor_str = temp_path.vendor[:8].strip() + " " + temp_path.model[:16].strip()
        elif "nvme" in path_ops:
            temp_path = readSU("struct nvme_ns", temp_pgpath.path.dev.bdev.bd_disk.queue.queuedata)
            vendor_str = "NVME " + temp_path.ctrl.model.strip()
        else:
            vendor_str = "<unknown>"
            pylog.info("{}: {} ops not recognized".format(temp_pgpath.path.dev.bdev.bd_disk, path_ops))
    except:
        pylog.warning("Error in processing sub paths for multipath device:", name)
        pylog.warning("Use 'dmshow --table|grep <mpath-device-name>' to manually verify sub paths.")
        return

    hash_cell = readSU("struct hash_cell", md.interface_ptr)
    scsi_id = hash_cell.uuid
    scsi_id = scsi_id.partition("-")

    if ('cciss' in temp_pgpath.path.dev.bdev.bd_disk.disk_name):
        print("{}  ({})  dm-{:<4d}  HP Smart Array RAID Device (cciss)".format(name, scsi_id[2],
            md.disk.first_minor), end="")
    else:
        print("{}  ({})  dm-{:<4d}  {}".format(name, scsi_id[2], md.disk.first_minor,
            vendor_str), end="")

    print("\nsize={:.2f}M  ".format(get_size(temp_pgpath.path.dev.bdev.bd_disk)), end="")

    unset_multipath_scope(scope_set)

    if (member_size("struct multipath", "flags") != -1):
        if ((mpath.flags & (1 << 0)) or (mpath.flags & (1 << 1)) or
            (mpath.flags & (1 << 2))):
            print("(queue_if_no_path enabled)  ".format(), end="")
        else:
            print("(queue_if_no_path disabled)  ".format(), end="")

    else:
        if (mpath.queue_if_no_path):
            print("features='1 queue_if_no_path'  ".format(), end="")
        else:
            print("features='0' (queue_if_no_path disabled)  ".format(), end="")

    if (mpath.hw_handler_name):
        print("hwhandler={} hwhandler params={}  ".format(mpath.hw_handler_name,
            mpath.hw_handler_params), end="")
    else:
        print("hwhandler={}  ".format(mpath.hw_handler_name), end="")

    for prio in prio_groups:
        print("\n+- policy='{}' ".format(prio.ps.type.name), end="")
        show_mpath_info(prio, path_ops)

    print("")
    return 1

def show_dmsetup_table_multipath(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", md.map)
    print("{}: {} {} multipath".format(name, dm_table_map.targets.begin,
        dm_table_map.targets.len),end="")
    if (not context_struct_exists("multipath", name)):
            return
    mpath = readSU("struct multipath", dm_table_map.targets.private)

    # general parameters
    params = []

    if (member_size("struct multipath", "flags") != -1):
        if ((mpath.flags & (1 << 0)) or (mpath.flags & (1 << 1)) or
            (mpath.flags & (1 << 2))):
            params.append("queue_if_no_path")

    else:
        if (mpath.queue_if_no_path):
            params.append("queue_if_no_path")

    print(" {}".format(len(params)), end="")
    for param in params:
        print(" {}".format(param), end="")

    #hw handler parameters
    params = []
    if (mpath.hw_handler_name):
        params.append(mpath.hw_handler_name)
        if (mpath.hw_handler_params):
            for param in mpath.hw_handler_params.split(" "):
                params.append(param)

    print(" {}".format(len(params)), end="")
    for param in params:
        print(" {}".format(param), end="")

    #number of path groups
    print(" {}".format(mpath.nr_priority_groups), end="")

    prio_groups = readSUListFromHead(mpath.priority_groups, "list", "struct priority_group")

    #next pathgroup to try
    if (mpath.current_pg):
        print(" {}".format(mpath.current_pg.pg_num), end="")
    elif (prio_groups):
        print(" {}".format(prio_groups[0].pg_num), end="")
    else:
        print(" 1", end="")

    set_scope = set_multipath_scope()

    for prio in prio_groups:
        show_table_mpath_priogroup(prio)

    unset_multipath_scope(set_scope)

    print("")

def show_basic_mpath_info(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", md.map)

    target_name = get_dm_target_name(dm_table_map, name)
    if (not target_name or target_name != "multipath"):
        return 0

    mpath = readSU("struct multipath", dm_table_map.targets.private)

    print("dm-{:<4d}  {:<38} {:#x} ".format(md.disk.first_minor, name, mpath), end="")

    use_nr_paths_counter = -1

    try:
        use_nr_paths_counter = readSU("struct multipath", long(mpath.nr_valid_paths.counter))
    except:
        use_nr_paths_counter = -1

    if (use_nr_paths_counter != -1):
        print("{:15d}".format(mpath.nr_valid_paths.counter), end="")
    else:
        print("{:15d}".format(mpath.nr_valid_paths), end="")

    if (member_size("struct multipath", "flags") != -1):
        if ((mpath.flags & (1 << 0)) or (mpath.flags & (1 << 1)) or
            (mpath.flags & (1 << 2))):
            print("{:>19s}".format("Enabled"))
        else:
            print("{:>19s}".format("Disabled"))

    else:
        if (mpath.queue_if_no_path):
            print("{:>19s}".format("Enabled"))
        else:
            print("{:>19s}".format("Disabled"))
    return 1

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

def get_md_mpath_from_gendisk(pv_gendisk, devlist):
    tmp_mapped_device = readSU("struct mapped_device", pv_gendisk.queue.queuedata)
    for temp_dev in devlist:
        if (tmp_mapped_device == temp_dev[0]):
            return temp_dev
    return (0,0)

def get_lvm_function(spec):

    if spec == "lvs":
        return "show_lvm_lvs"
    elif spec == "lvuuid":
        return "show_lvm_uuid"
    elif spec == "pvs":
        return "show_lvm_pvs"

def get_lvm_context(target, name):

    type_context = {
            "linear": "struct linear_c", "thin-pool": "struct pool_c",
            "thin": "struct thin_c", "snapshot": "struct dm_snapshot",
            "mirror": "struct mirror_set", "striped": "struct stripe_c",
            "raid": "struct raid_set", "crypt": "struct crypt_config",
            "snapshot-origin": "struct dm_origin", "cache": "struct cache"
    }

    context_string = type_context.get(target.type.name)
    if (not context_struct_exists(context_string.replace("struct ", ""), name)):
        return None
    context = readSU(context_string, long(target.private))
    return context

def get_origin_context(context_dev, name):

    origin_md = readSU("struct mapped_device",
            long(context_dev.bdev.bd_disk.queue.queuedata))
    origin_table = readSU("struct dm_table", long(origin_md.map))
    origin_context = get_lvm_context(origin_table.targets, name)

    return origin_context

def get_pv_blockdev_from_lvm_context(target, context, leg_index, name):

    if target.type.name == "linear":
        bdev = readSU("struct block_device", long(context.dev.bdev))
    elif target.type.name == "thin-pool":
        bdev = readSU("struct block_device", long(context.data_dev.bdev))
    elif target.type.name == "thin":
        bdev = readSU("struct block_device", long(context.pool_dev.bdev))
    elif target.type.name == "cache":
        bdev = readSU("struct block_device", long(context.origin_dev.bdev))
    elif target.type.name == "mirror":
        bdev = readSU("struct block_device", long(context.mirror[leg_index].dev.bdev))
    elif target.type.name == "striped":
        bdev = readSU("struct block_device", long(context.stripe[leg_index].dev.bdev))
    elif target.type.name == "raid":
        bdev = readSU("struct block_device", long(context.dev[leg_index].rdev.bdev))
    elif target.type.name == "crypt":
        bdev = readSU("struct block_device", long(context.dev.bdev))
    elif target.type.name == "snapshot-origin":
        real_context = get_origin_context(context.dev, name)
        if (real_context is None):
            return None
        bdev = readSU("struct block_device", long(real_context.dev.bdev))
    elif target.type.name == "snapshot":
        origin_context = get_origin_context(context.origin, name)
        if (origin_context is None):
            return None
        bdev = readSU("struct block_device", long(origin_context.dev.bdev))
    return bdev

def get_leg_count(target, context):

    leg_count = 1
    if target.type.name == "mirror":
        leg_count = context.nr_mirrors
    elif target.type.name == "striped":
        leg_count = context.stripes
    elif target.type.name == "raid":
        leg_count = context.raid_disks

    return leg_count

def build_pv_list(target, context, devlist, leg_count, pool_string, name):

    pv_names = []
    pv_md = "[PV not DM dev]"

    for leg in range(leg_count):
        pv_blockdev = get_pv_blockdev_from_lvm_context(target, context, leg, name)
        if (pv_blockdev is None):
            pv_names.append("<error>", "", "")
            continue
        pv_gendisk = pv_blockdev.bd_disk
        size = get_size(pv_gendisk)
        if ('dm-' in pv_gendisk.disk_name[:3]):
            pv_md, pv_md_name = get_md_mpath_from_gendisk(pv_gendisk, devlist)
            if (not pv_md and not pv_md_name):
                pylog.warning("No PV found for pv_gendisk".format(pv_gendisk))
                continue
            pv_names.append((pool_string + pv_md_name + " (" + pv_gendisk.disk_name + ")", format(pv_md, 'x'), size))
        else:
            pv_names.append((bdev_name(pv_blockdev), pv_md, size))

    return pv_names

def show_lvm_lvs(dev, devlist, name, md, dm_table_map):

    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        context = get_lvm_context(target, name)
        if (context is None):
            return
        gendisk = readSU("struct gendisk", md.disk)
        hash_cell = readSU("struct hash_cell", md.interface_ptr)

        try:
            if ('LVM-' not in hash_cell.uuid):
                return
        except:
            pylog.warning("Invalid UUID for mapped_device:", hex(md),
                          "| hash_cell.uuid (UUID) is:", hash_cell.uuid)
            return

        vg_lv_names = get_vg_lv_names(name)

        if ((vg_lv_names[0]) and (vg_lv_names[1])):

            lv_capacity = get_size(gendisk)
            pool_string = "Pool: " if target.type.name == "thin" else ""
            leg_count = get_leg_count(target, context)
            pv_names = build_pv_list(target, context, devlist, leg_count, pool_string, name)
            pv_names_only = [x[0] for x in pv_names]
            pv_names_string = ','.join(pv_names_only)

            print("dm-{:<10d} {:<40s}  {:<40s} "
                    "{:>10d} {:>18.2f}     {}\n".format(md.disk.first_minor,
                    vg_lv_names[1], vg_lv_names[0], md.open_count.counter,
                    lv_capacity, pv_names_string), end="")

def show_lvm_uuid(dev, devlist, name, md, dm_table_map):

    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        gendisk = readSU("struct gendisk", md.disk)
        hash_cell = readSU("struct hash_cell", md.interface_ptr)
        try:
            if ('LVM-' not in hash_cell.uuid):
                return
        except:
            pylog.warning("Invalid UUID for mapped_device:", hex(md),
                          "| hash_cell.uuid (UUID) is:", hash_cell.uuid)
            return

        lv_uuid = hash_cell.uuid.partition("-")
        lv_uuid = lv_uuid[2]

        vg_lv_names =  get_vg_lv_names(name)
        if (vg_lv_names in lv_list):
            continue
        else:
            lv_list.append(vg_lv_names)

        if ((vg_lv_names[0]) and (vg_lv_names[1])):

             lv_capacity = get_size(gendisk)

             print("dm-{:<10d} {:40s}  {:40s} {:18.2f}  {:10s}  {:10s}\n".format(md.disk.first_minor,
                 vg_lv_names[1], vg_lv_names[0],
                 lv_capacity,
                 lv_uuid[-32:], lv_uuid[:32]), end="")

def show_lvm_pvs(dev, devlist, name, md, dm_table_map):

    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        context = get_lvm_context(target, name)
        if (context is None):
            return
        gendisk = readSU("struct gendisk", md.disk)
        hash_cell = readSU("struct hash_cell", md.interface_ptr)
        try:
            if ('LVM-' not in hash_cell.uuid):
                return
        except:
            pylog.warning("Invalid UUID for mapped_device:", hex(md),
                          "| hash_cell.uuid (UUID) is:", hash_cell.uuid)
            return

        vg_lv_names =  get_vg_lv_names(name)

        if ((vg_lv_names[0]) and (vg_lv_names[1])):

            leg_count = get_leg_count(target, context)
            pv_names = build_pv_list(target, context, devlist, leg_count, "", name)

            for pv in pv_names:
                pv_name, pv_md, pv_size = pv
                print("{:<48s}{:<16}{:>20.2f}  {:<40s}  {}\n".format(pv_name,
                    pv_md, pv_size, vg_lv_names[0], vg_lv_names[1]), end="")

def show_lvm(dev, devlist, spec):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))

    type_name = get_dm_target_name(dm_table_map, name)
    if (not type_name):
        return

    lvm_func = get_lvm_function(spec)

    if type_name == "multipath":
        return
    elif (type_name == "linear" or type_name == "thin-pool" or
          type_name == "thin" or type_name == "cache" or
          type_name == "mirror" or type_name == "striped" or
          type_name == "raid" or type_name == "crypt" or
          type_name == "snapshot-origin" or type_name == "snapshot"):
        eval(lvm_func)(dev, devlist, name, md, dm_table_map)
    else:
        print("{}: {} not yet supported by this command".format(name,
            dm_table_map.targets.type.name))
        return

def show_dmsetup_table_striped(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("stripe_c", name)):
                return
        stripe_c = readSU("struct stripe_c", long(target.private))
        if (member_size("struct stripe_c", "chunk_shift") != -1):
            c_size = stripe_c.chunk_shift + 1
        else:
            c_size = stripe_c.chunk_size
        print("{}: {} {} striped {} {}".format(name, target.begin, target.len,
            stripe_c.stripes, c_size), end='')

        for stripe_num in range(stripe_c.stripes):
            dm_dev = readSU("struct dm_dev", long(stripe_c.stripe[stripe_num].dev))
            start = stripe_c.stripe[stripe_num].physical_start
            if stripe_num == (stripe_c.stripes - 1):
                print(" {} [{}] {}".format(dm_dev.name,
                    bdev_name(stripe_c.stripe[stripe_num].dev.bdev), start))
            else:
                print(" {} [{}] {}".format(dm_dev.name,
                    bdev_name(stripe_c.stripe[stripe_num].dev.bdev), start), end='')

def show_dmsetup_table_thinpool(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("pool_c", name)):
            return
        pool_c = readSU("struct pool_c", long(target.private))
        print("{}: {} {} thin-pool {} [{}] {} [{}] {} {}".format(name, target.begin, target.len,
            pool_c.metadata_dev.name, bdev_name(pool_c.metadata_dev.bdev), pool_c.data_dev.name,
            bdev_name(pool_c.data_dev.bdev), pool_c.pool.sectors_per_block,
            pool_c.pool.low_water_blocks), end='')

        if (member_size("struct pool_c", "requested_pf") != -1):
            feature_loc = readSU("struct pool_features", pool_c.requested_pf)
        else:
            feature_loc = readSU("struct pool_features", pool_c.pf)
        member_names = ["mode", "zero_new_blocks", "discard_enabled", "discard_passdown", "error_if_no_space"]
        feature_names = ["read_only", "skip_block_zeroing", "ignore_discard", "no_discard_passdown", "error_if_no_space"]
        feature_string = []
        arg_counter = 0
        index = 0
        for features in member_names:
            result = exec_crash_command("struct pool_features.{} {:#x}".format(features, feature_loc))
            if "mode = PM_READ_ONLY" in result:
                feature_string.append(' {}'.format(feature_names[index]))
                arg_counter +=1
            if "zero_new_blocks = false" in result:
                feature_string.append(' {}'.format(feature_names[index]))
                arg_counter +=1
            if "discard_enabled = false" in result:
                feature_string.append(' {}'.format(feature_names[index]))
                arg_counter +=1
            if "discard_passdown = false" in result:
                feature_string.append(' {}'.format(feature_names[index]))
                arg_counter +=1
            if "error_if_no_space = true" in result:
                feature_string.append(' {}'.format(feature_names[index]))
                arg_counter +=1
            index += 1
        features = ''.join(feature_string)
        print(" {}{}".format(arg_counter, features))

def show_dmsetup_table_thin(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("thin_c", name)):
            return
        thin_c = readSU("struct thin_c", long(target.private))

        print("{}: {} {} thin {} [{}] {}".format(name, target.begin, target.len,
            thin_c.pool_dev.name, bdev_name(thin_c.pool_dev.bdev), thin_c.dev_id))

def show_dmsetup_table_snap_origin(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (struct_exists("struct dm_origin")):
            origin = readSU("struct dm_origin", long(target.private))
            origin_dev = origin.dev
        elif ("dm_snapshot" not in lsModules()):
            print("{}: error: dm_origin does not exist. dm_snapshot not loaded".format(name))
            return
        else:
            origin_dev = readSU("struct dm_dev", long(target.private))

        print("{}: {} {} snapshot-origin {} [{}]".format(name, target.begin,
            target.len, origin_dev.name, bdev_name(origin_dev.bdev)))

def show_dmsetup_table_snap(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("dm_snapshot", name)):
            return
        dm_snapshot = readSU("struct dm_snapshot", long(target.private))

        if (member_size("struct dm_snapshot", "type") != -1):
            type = chr(dm_snapshot.type)
        else:
            if (member_size("struct dm_exception_store", "userspace_supports_overflow") != -1):
                support = exec_crash_command("struct dm_exception_store.userspace_supports_overflow \
                    {:#x}".format(dm_snapshot.store))
                if "userspace_supports_overflow = true" in support:
                    type = "PO"
                else:
                    type = dm_snapshot.store.type.name
            else:
                type = dm_snapshot.store.type.name

        if (member_size("struct dm_snapshot", "chunk_size") != -1):
            chunk_size = dm_snapshot.chunk_size
        else:
            chunk_size = dm_snapshot.store.chunk_size

        ttype = dm_table_map.targets.type.name

        print("{}: {} {} {} {} [{}] {} [{}] {} {}".format(name, target.begin, target.len,
            ttype, dm_snapshot.origin.name, bdev_name(dm_snapshot.origin.bdev),
            dm_snapshot.cow.name, bdev_name(dm_snapshot.cow.bdev), type, chunk_size))

def show_dmsetup_table_cache(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("cache", name)):
            return
        cache = readSU("struct cache", long(target.private))

        print("{}: {} {} cache {} [{}] {} [{}] {} [{}]".format(name, target.begin, target.len,
            cache.metadata_dev.name, bdev_name(cache.metadata_dev.bdev), cache.cache_dev.name,
            bdev_name(cache.cache_dev.bdev), cache.origin_dev.name,
            bdev_name(cache.origin_dev.bdev)), end='')

        for arg in range(cache.nr_ctr_args):
            print(" {}".format(SmartString(readmem(cache.ctr_args[arg], 40),
                cache.ctr_args[arg], None)), end='')
        print("{}".format(""))

def show_raid_ctr_table(raid_set, raid_disks, rebuild_disks, write_mostly_params, srdev_flags_bits):
    __raid_defs = '''
    #define __CTR_FLAG_SYNC                 0
    #define __CTR_FLAG_NOSYNC               1
    #define __CTR_FLAG_REBUILD              2
    #define __CTR_FLAG_DAEMON_SLEEP         3
    #define __CTR_FLAG_MIN_RECOVERY_RATE    4
    #define __CTR_FLAG_MAX_RECOVERY_RATE    5
    #define __CTR_FLAG_MAX_WRITE_BEHIND     6
    #define __CTR_FLAG_WRITE_MOSTLY         7
    #define __CTR_FLAG_STRIPE_CACHE         8
    #define __CTR_FLAG_REGION_SIZE          9
    #define __CTR_FLAG_RAID10_COPIES        10
    #define __CTR_FLAG_RAID10_FORMAT        11
    #define __CTR_FLAG_DELTA_DISKS          12
    #define __CTR_FLAG_DATA_OFFSET          13
    #define __CTR_FLAG_RAID10_USE_NEAR_SETS 14
    #define __CTR_FLAG_JOURNAL_DEV          15
    #define __CTR_FLAG_JOURNAL_MODE         16
    '''

    flags = CDefine(__raid_defs)
    real_flags = {k[2:]: 1<<v for k,v in flags.items()}

    CTR_FLAGS_ANY_SYNC = real_flags['CTR_FLAG_SYNC'] | real_flags['CTR_FLAG_NOSYNC']
    CTR_FLAG_OPTIONS_NO_ARGS = CTR_FLAGS_ANY_SYNC | real_flags['CTR_FLAG_RAID10_USE_NEAR_SETS']
    CTR_FLAG_OPTIONS_ONE_ARG = real_flags['CTR_FLAG_REBUILD'] | real_flags['CTR_FLAG_WRITE_MOSTLY'] | \
                               real_flags['CTR_FLAG_DAEMON_SLEEP'] | real_flags['CTR_FLAG_MIN_RECOVERY_RATE'] | \
                               real_flags['CTR_FLAG_MAX_RECOVERY_RATE'] | real_flags['CTR_FLAG_MAX_WRITE_BEHIND'] | \
                               real_flags['CTR_FLAG_STRIPE_CACHE'] | real_flags['CTR_FLAG_REGION_SIZE'] | \
                               real_flags['CTR_FLAG_RAID10_COPIES'] | real_flags['CTR_FLAG_RAID10_FORMAT'] | \
                               real_flags['CTR_FLAG_DELTA_DISKS'] | real_flags['CTR_FLAG_DATA_OFFSET']

    no_arg_val = raid_set.ctr_flags & CTR_FLAG_OPTIONS_NO_ARGS
    one_arg_val = raid_set.ctr_flags & CTR_FLAG_OPTIONS_ONE_ARG

    bits_set_no_arg = bin(no_arg_val).count('1')
    bits_set_one_arg = bin(one_arg_val).count('1') * 2

    journal_dev_val,journal_dev_mode = (0,0)
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_JOURNAL_DEV'])):
        journal_dev_val = 2
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_JOURNAL_MODE'])):
        journal_dev_mode = 2

    raid_param_cnt = 1
    raid_param_cnt += (rebuild_disks * 2) + write_mostly_params + bits_set_no_arg + \
                      bits_set_one_arg + journal_dev_val + journal_dev_mode
    print(" {} {} {}".format(raid_set.raid_type.name, raid_param_cnt, raid_set.md.new_chunk_sectors), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_SYNC'])):
        print(" {}".format("sync"), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_NOSYNC'])):
        print(" {}".format("nosync"), end='')
    if (rebuild_disks != 0):
        bin_string = ""
        for disks in range(len(raid_set.rebuild_disks)):
            bin_string += "{0:{fill}64b}".format(raid_set.rebuild_disks[disks], fill='0')[::-1]
        for dev in range(raid_disks):
            if (bin_string[dev] == '1'):
                print(" {} {}".format("rebuild", raid_set.dev[dev].rdev.raid_disk), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_DAEMON_SLEEP'])):
        print(" {} {}".format("daemon_sleep", raid_set.md.bitmap_info.daemon_sleep), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_MIN_RECOVERY_RATE'])):
        print(" {} {}".format("min_recovery_rate", raid_set.md.sync_speed_min), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_MAX_RECOVERY_RATE'])):
        print(" {} {}".format("max_recovery_rate", raid_set.md.sync_speed_max), end='')
    if (write_mostly_params != 0):
        for dev in range(raid_disks):
            if ("WriteMostly" in srdev_flags_bits):
                if (raid_set.dev[dev].rdev.flags & srdev_flags_bits['WriteMostly']):
                    print(" {} {}".format("write_mostly", raid_set.dev[dev].rdev.raid_disk), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_MAX_WRITE_BEHIND'])):
        print(" {} {}".format("max_write_behind", raid_set.md.bitmap_info.max_write_behind), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_STRIPE_CACHE'])):
        max_nr_stripes = 0
        if (raid_set.md.private != 0):
            r5conf = readSU("struct r5conf", long(raid_set.md.private))
            max_nr_stripes = r5conf.max_nr_stripes
        print(" {} {}".format("stripe_cache", max_nr_stripes), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_REGION_SIZE'])):
        print(" {} {}".format("region_size", (raid_set.md.bitmap_info.chunksize >> 9)), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_RAID10_COPIES'])):
        print(" {} {}".format("raid10_copies", max((raid_set.md.layout & 0xff),
            ((raid_set.md.layout >> 8) & 0xff))), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_RAID10_FORMAT'])):
        print(" {}".format("raid10_format"), end='')
        if ((raid_set.md.layout & (1 << 16)) != 0):
            print(" {}".format("offset"), end='')
        elif ((raid_set.md.layout & 0xff) > 1):
            print(" {}".format("near"), end='')
        elif (((raid_set.md.layout >> 8) & 0xff) > 1):
            print(" {}".format("far"), end='')
        else:
            print(" {}".format("unknown"), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_DELTA_DISKS'])):
        print(" {} {}".format("delta_disks", max(raid_set.delta_disks, raid.md.delta_disks)), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_DATA_OFFSET'])):
        print(" {} {}".format("data_offset", raid_set.data_offset), end='')
    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_JOURNAL_DEV'])):
        print(" {}".format("journal_dev"), end='')
        if (raid_set.journal_dev.dev != 0):
            print(" {}".format(raid_set.journal_dev.dev.name), end='')
        else:
            print(" {}".format("-"), end='')

    if (raid_set.ctr_flags & (1 << flags['__CTR_FLAG_JOURNAL_MODE'])):
        print(" {}".format("journal_mode"), end='')
        mode = readSymbol("_raid456_journal_mode")
        for x in range(len(readSymbol("_raid456_journal_mode"))):
            if (raid_set.journal_dev.mode == mode[x].mode):
                print(" {}".format(mode[x].param), end='')
            else:
                print(" {}".format("unknown"), end='')

def show_raid_dmpf_table(raid_set, raid_disks, srdev_flags_bits):
    __raid_print_flags = '''
    #define DMPF_SYNC              0x1
    #define DMPF_NOSYNC            0x2
    #define DMPF_REBUILD           0x4
    #define DMPF_DAEMON_SLEEP      0x8
    #define DMPF_MIN_RECOVERY_RATE 0x10
    #define DMPF_MAX_RECOVERY_RATE 0x20
    #define DMPF_MAX_WRITE_BEHIND  0x40
    #define DMPF_STRIPE_CACHE      0x80
    #define DMPF_REGION_SIZE       0x100
    #define DMPF_RAID10_COPIES     0x200
    #define DMPF_RAID10_FORMAT     0x400
    '''
    dmpf_flags = CDefine(__raid_print_flags)

    raid_param_cnt = 1
    for i in range(raid_disks):
        if ("In_sync" in srdev_flags_bits):
            if ((raid_set.print_flags & dmpf_flags['DMPF_REBUILD']) and (raid_set.dev[i].data_dev != 0) and not \
                (raid_set.dev[i].rdev.flags & srdev_flags_str['In_sync'])):
                raid_param_cnt += 2
        if ("WriteMostly" in srdev_flags_bits):
            if ((raid_set.dev[i].data_dev != 0) and (raid_set.dev[i].rdev.flags & srdev_flags_bits['WriteMostly'])):
                raid_param_cnt += 2

    raid_param_cnt += bin(raid_set.print_flags & ~dmpf_flags['DMPF_REBUILD']).count('1') * 2
    if ((raid_set.print_flags & (dmpf_flags['DMPF_SYNC'] | dmpf_flags['DMPF_NOSYNC']))):
        raid_param_cnt -= 1
    print(" {} {} {}".format(raid_set.raid_type.name, raid_param_cnt, raid_set.md.chunk_sectors), end='')

    if ((raid_set.print_flags & dmpf_flags['DMPF_SYNC']) and (raid_set.md.recovery_cp == 0xffffffffffffffff)):
        print(" {}".format("sync"), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_NOSYNC']):
        print(" {}".format("nosync"), end='')
    for i in range(raid_disks):
        if ("In_sync" in srdev_flags_bits):
            if ((raid_set.print_flags & dmpf_flags['DMPF_REBUILD']) and (raid_set.dev[i].data_dev != 0) and not \
                (raid_set.dev[i].rdev.flags & srdev_flags_str['In_sync'])):
                print(" rebuild {}".format(i), end='')

    if (raid_set.print_flags & dmpf_flags['DMPF_DAEMON_SLEEP']):
        print(" daemon_sleep {}".format(raid_set.bitmap_info.daemon_sleep), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_MIN_RECOVERY_RATE']):
        print(" min_recovery_rate {}".format(raid_set.md.sync_speed_min), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_MAX_RECOVERY_RATE']):
        print(" max_recovery_rate {}".format(raid_set.md.sync_speed_max), end='')
    for i in range(raid_disks):
        if ("WriteMostly" in srdev_flags_bits):
            if ((raid_set.dev[i].data_dev != 0) and (raid_set.dev[i].rdev.flags & srdev_flags_bits['WriteMostly'])):
                print(" write_mostly {}".format(i), end='')

    if (raid_set.print_flags & dmpf_flags['DMPF_MAX_WRITE_BEHIND']):
        print(" max_write_behind {}".format(raid_set.md.bitmap_info.max_write_behind), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_STRIPE_CACHE']):
        max_nr_stripes = 0
        if (raid_set.md.private != 0):
            r5conf = readSU("struct r5conf", long(raid_set.md.private))
            max_nr_stripes = r5conf.max_nr_stripes
        print(" stripe_cache {}".format(max_nr_stripes * 2), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_REGION_SIZE']):
        print(" region_size {}".format(raid_set.md.bitmap_info.chunksize >> 9), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_RAID10_COPIES']):
        print(" raid10_copies {}".format(raid_set.md.layout & 0xff), end='')
    if (raid_set.print_flags & dmpf_flags['DMPF_RAID10_FORMAT']):
        print(" {}".format("raid10_format near"), end='')

def show_dmsetup_table_raid(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("raid_set", name)):
            return
        raid_set = readSU("struct raid_set", long(target.private))
        print("{}: {} {} raid".format(name, target.begin, target.len), end='')

        if (member_size("struct raid_set", "raid_disks") != -1):
            raid_disks = raid_set.raid_disks
        else:
            raid_disks = raid_set.md.raid_disks

        write_mostly_params = 0
        try:
            rdev_flags_bits = EnumInfo("enum flag_bits")
        except TypeError:
            rdev_flags_bits = False
            pylog.info("{} EnumInfo for rdev_flags_bits failed".format(name))

        if (rdev_flags_bits is not False):
            srdev_flags_bits = {k: 1<<v for k,v in rdev_flags_bits.items()}
            for dev in range(raid_disks):
                if ("WriteMostly" in srdev_flags_bits):
                    if (raid_set.dev[dev].rdev.flags & srdev_flags_bits['WriteMostly']):
                        write_mostly_params += 2

        if (member_size("struct raid_set", "rebuild_disks") != -1):
            rebuild_disks = 0
            for index in range(len(raid_set.rebuild_disks)):
                rebuild_disks += bin(raid_set.rebuild_disks[index]).count('1')

        if (rdev_flags_bits is not False):
            if (member_size("struct raid_set", "ctr_flags") != -1):
                show_raid_ctr_table(raid_set, raid_disks, rebuild_disks, write_mostly_params, srdev_flags_bits)
            elif (member_size("struct raid_set", "print_flags") != -1):
                show_raid_dmpf_table(raid_set, raid_disks, srdev_flags_bits)

        print(" {}".format(raid_disks), end='')

        for x in range(raid_disks):
            if (raid_set.dev[x].meta_dev != 0):
                print(" {} [{}]".format(raid_set.dev[x].meta_dev.name,
                    bdev_name(raid_set.dev[x].meta_dev.bdev)), end='')
            else:
                print(" {}".format("-"), end='')
            if (raid_set.dev[x].data_dev != 0):
                print(" {} [{}]".format(raid_set.dev[x].data_dev.name,
                    bdev_name(raid_set.dev[x].data_dev.bdev)), end='')
            else:
                print(" {}".format("-"), end='')
        print("{}".format(""))

def show_dirty_log_sync(log_c, enum_sync_state):
    if ("DEFAULTSYNC" in enum_sync_state):
        if (log_c.sync != enum_sync_state['DEFAULTSYNC']):
            if ("NOSYNC" in enum_sync_state and "SYNC" in enum_sync_state):
                if (log_c.sync == enum_sync_state['NOSYNC']):
                    print(" {}".format("nosync"), end='')
                elif (log_c.sync == enum_sync_state['SYNC']):
                    print(" {}".format("sync"), end='')
                else:
                    print("{}".format("----"))
                    pylog.info("{} sync status retrieval failed"
                        .format(log_c.ti.table.md.name))
            else:
                pylog.info("{} unknown sync status".format(log_c.ti.table.md.name))

def show_dirty_log_status(status_fn, dirty_log):
    log_c = readSU("struct log_c", long(dirty_log.context))
    dmlog_ioerr_const = '''
    #define DMLOG_IOERR_IGNORE 0
    #define DMLOG_IOERR_BLOCK  1
    '''
    dmlog_ioerr_const_flags = CDefine(dmlog_ioerr_const)

    try:
        enum_sync_state = EnumInfo("enum sync")
    except TypeError:
        enum_sync_state = False
        pylog.info("{}: EnumInfo for enum_sync_state failed"
            .format(log_c.ti.table.md.disk.disk_name))

    if (enum_sync_state is not False):
        if (status_fn == "core_status"):
            if ("DEFAULTSYNC" in enum_sync_state):
                if (log_c.sync == enum_sync_state['DEFAULTSYNC']):
                    params = 1
                else:
                    params = 2
            if (member_size("struct log_c", "failure_response") != -1):
                if (log_c.failure_response == dmlog_ioerr_const_flags['DMLOG_IOERR_BLOCK']):
                    params += 1
            print(" {} {} {}".format(dirty_log.type.name, params, log_c.region_size), end='')
            show_dirty_log_sync(log_c, enum_sync_state)
            if (member_size("struct log_c", "failure_response") != -1):
                if (log_c.failure_response == dmlog_ioerr_const_flags['DMLOG_IOERR_BLOCK']):
                    print(" {}".format("block_on_error"), end='')

        if (status_fn == "disk_status"):
            if ("DEFAULTSYNC" in enum_sync_state):
                if (log_c.sync == enum_sync_state['DEFAULTSYNC']):
                    params = 2
                else:
                    params = 3
            if (member_size("struct log_c", "failure_response") != -1):
                if (log_c.failure_response == dmlog_ioerr_const_flags['DMLOG_IOERR_BLOCK']):
                    params += 1
            print(" {} {} {} [{}] {}".format(dirty_log.type.name, params, log_c.log_dev.name,
                bdev_name(log_c.log_dev.bdev), log_c.region_size), end='')
            show_dirty_log_sync(log_c, enum_sync_state)
            if (member_size("struct log_c", "failure_response") != -1):
                if (log_c.failure_response == dmlog_ioerr_const_flags['DMLOG_IOERR_BLOCK']):
                    print(" {}".format("block_on_error"), end='')

def show_dmsetup_table_raid45(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("raid_set", name)):
            return
        raid_set = readSU("struct raid_set", long(target.private))

        print("{}: {} {} raid45".format(name, target.begin, target.len), end='')

        status_fn = addr2sym(raid_set.recover.dl.type.status)
        show_dirty_log_status(status_fn, raid_set.recover.dl)

        print(" {} {}".format(raid_set.set.raid_type.name, raid_set.set.raid_parms), end='')

        raid_parms = [raid_set.set.chunk_size_parm, raid_set.sc.stripes_parm,
            raid_set.set.io_size_parm, raid_set.recover.io_size_parm,
            raid_set.recover.bandwidth_parm, -2, raid_set.recover.recovery_stripes]

        for p in range(raid_set.set.raid_parms):
            if (raid_parms[p] > -2):
                print(" {}".format(raid_parms[p]), end='')
            else:
                if (raid_set.recover.recovery != 0):
                    print(" {}".format("sync"), end='')
                else:
                    print(" {}".format("nosync"), end='')
        print(" {} {}".format(raid_set.set.raid_devs, raid_set.set.dev_to_init), end='')

        for p in range(raid_set.set.raid_devs):
            print(" {}-{} [{}] {}".format((raid_set.dev[p].dev.bdev.bd_dev >> 20),
                (raid_set.dev[p].dev.bdev.bd_dev & ((1 << 20) - 1)),
                bdev_name(raid_set.dev[p].dev.bdev), raid_set.dev[p].start), end='')
        print("{}".format(""))

def show_dmsetup_table_mirror(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    _handle_err = '''
    #define DM_RAID1_HANDLE_ERRORS 0x01
    '''
    handle_err = CDefine(_handle_err)

    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("mirror_set", name)):
            return
        mirror_set = readSU("struct mirror_set", long(target.private))

        print("{}: {} {} mirror".format(name, target.begin, target.len), end='')
        status_fn = addr2sym(mirror_set.rh.log.type.status)
        show_dirty_log_status(status_fn, mirror_set.rh.log)

        print(" {}".format(mirror_set.nr_mirrors), end='')
        for m in range(mirror_set.nr_mirrors):
            print(" {} [{}] {}".format(mirror_set.mirror[m].dev.name,
                bdev_name(mirror_set.mirror[m].dev.bdev),
                mirror_set.mirror[m].offset), end='')
        if (member_size("struct mirror_set", "features") != -1):
            if (mirror_set.features & handle_err['DM_RAID1_HANDLE_ERRORS'] != 0):
                print(" {}".format("1 handle_errors"), end='')
        print("{}".format(""))

def show_dmsetup_table_crypt(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("crypt_config", name)):
            return
        crypt_c = readSU("struct crypt_config", long(target.private))
        print("{}: {} {} crypt".format(name, target.begin, target.len), end='')

        if (member_size("struct crypt_config", "tfm") != -1):
            _mode_defs = '''
            #define CRYPTO_TFM_MODE_ECB  0x00000001
            #define CRYPTO_TFM_MODE_CBC  0x00000002
            '''
            mode_defs = CDefine(_mode_defs)
            if (member_size("struct crypto_blkcipher", "__crt_alg") != -1):
                cipher = crypt_c.tfm.__crt_alg.cra_name
            else:
                cipher = crypt_c.cipher
            if (member_size("struct crypto_blkcipher", "crt_cipher") != -1):
                if (crypt_c.tfm.crt_cipher.cit_mode == mode_defs['CRYPTO_TFM_MODE_CBC']):
                    chainmode = "cbc"
                elif (crypt_c.tfm.crt_cipher.cit_mode == mode_defs['CRYPTO_TFM_MODE_ECB']):
                    chainmode = "ebc"
            else:
                chainmode = crypt_c.chainmode

            if (crypt_c.iv_mode != 0):
                print(" {}-{}-{}".format(cipher, chainmode, crypt_c.iv_mode), end='')
            else:
                print(" {}-{}".format(cipher, chainmode), end='')
        else:
            print(" {}".format(crypt_c.cipher_string), end='')

        if (crypt_c.key_size > 0):
            print("{}".format(" "), end='')
            for i in range(crypt_c.key_size):
                print("{}".format("00"), end='')
        else:
            print("{}".format(" -"), end='')

        print(" {} {} [{}] {}".format(crypt_c.iv_offset, crypt_c.dev.name,
            bdev_name(crypt_c.dev.bdev), crypt_c.start), end='')

        if (member_size("struct crypt_config", "flags") != -1):
            try:
                flag_bits = EnumInfo("enum flags")
            except TypeError:
                flag_bits = False
                pylog.info("{}: EnumInfo for flag_bits failed".format(name))

            if (flag_bits is not False):
                sflag_bits = {k: 1<<v for k,v in flag_bits.items()}
                num_feature_args = 0

                if (member_size("struct dm_target", "num_discard_bios") != -1):
                    if (target.num_discard_bios > 0):
                        num_feature_args += 1
                if ("DM_CRYPT_SAME_CPU" in sflag_bits):
                    if (crypt_c.flags & sflag_bits['DM_CRYPT_SAME_CPU']):
                        num_feature_args += 1
                if ("DM_CRYPT_NO_OFFLOAD" in sflag_bits):
                    if (crypt_c.flags & sflag_bits['DM_CRYPT_NO_OFFLOAD']):
                        num_feature_args += 1

                if (num_feature_args > 0):
                    print(" {}".format(num_feature_args), end='')
                    if (member_size("struct dm_target", "num_discard_bios") != -1):
                        if (target.num_discard_bios > 0):
                            print(" {}".format("allow discards"), end='')
                    if ("DM_CRYPT_SAME_CPU" in sflag_bits):
                        if (crypt_c.flags & sflag_bits['DM_CRYPT_SAME_CPU']):
                            print(" {}".format("same_cpu_crypt"), end='')
                    if ("DM_CRYPT_NO_OFFLOAD" in sflag_bits):
                        if (crypt_c.flags & sflag_bits['DM_CRYPT_NO_OFFLOAD']):
                            print(" {}".format("submit_from_crypt_cpus"), end='')
        print("{}".format(""))

def show_dmsetup_table_delay(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("delay_c", name)):
            return
        delay_c = readSU("struct delay_c", long(target.private))

        print("{}: {} {} delay".format(name, target.begin, target.len), end='')
        print(" {} [{}] {} {}".format(delay_c.dev_read.name, bdev_name(delay_c.dev_read.bdev),
            delay_c.start_read, delay_c.read_delay), end='')
        if (delay_c.dev_write != 0):
            print(" {} [{}] {} {}".format(delay_c.dev_write.name, bdev_name(delay_c.dev_write.bdev),
                delay_c.start_write, delay_c.write_delay))
        else:
            print("{}".format(""))

def show_dmsetup_table_generic(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        print("{}: {} {} {}".format(name, target.begin, target.len,
            dm_table_map.targets.type.name))

def show_dmsetup_table_switch(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("switch_ctx", name)):
            return
        switch_ctx = readSU("struct switch_ctx", long(target.private))
        print("{}: {} {} switch".format(name, target.begin, target.len), end='')
        print(" {} {} 0".format(switch_ctx.nr_paths, switch_ctx.region_size), end='')

        for path in range(switch_ctx.nr_paths):
            print(" {} [{}] {}".format(switch_ctx.path_list[path].dmdev.name,
                bdev_name(switch_ctx.path_list[path].dmdev.bdev),
                switch_ctx.path_list[path].start), end='')
        print("{}".format(""))

def show_dmsetup_table_flakey(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("flakey_c", name)):
            return
        flakey_c = readSU("struct flakey_c", long(target.private))
        print("{}: {} {} flakey".format(name, target.begin, target.len), end='')
        print(" {} [{}] {} {} {}".format(flakey_c.dev.name,
            bdev_name(flakey_c.dev.bdev), flakey_c.start,
            flakey_c.up_interval, flakey_c.down_interval), end='')

        try:
            enum_flakey_state = EnumInfo("enum feature_flag_bits")
        except TypeError:
            enum_flakey_state = False
            pylog.info("{}: EnumInfo for feature_flag_bits failed"
                .format(bdev_name(flakey_c.dev.bdev)))

        if (enum_flakey_state is not False):
            flakey_state = {k: 1<<v for k,v in enum_flakey_state.items()}
            drop_writes, error_writes, corrupt_byte = (0, 0, 0)
            if ("DROP_WRITES" in flakey_state):
                if (flakey_c.flags & flakey_state['DROP_WRITES']):
                    drop_writes = 1
            if ("ERROR_WRITES" in flakey_state):
                if (flakey_c.flags & flakey_state['ERROR_WRITES']):
                    error_writes = 1
            if (flakey_c.corrupt_bio_byte > 0):
                corrupt_byte = 1
            arg_count = drop_writes + error_writes + (corrupt_byte * 5)
            print(" {}".format(arg_count), end='')

            if (drop_writes > 0):
                print(" {}".format("drop_writes"), end='')
            if (error_writes > 0):
                print(" {}".format("error_writes"), end='')
            if (flakey_c.corrupt_bio_byte != 0):
                if (flakey_c.corrupt_bio_rw == 0):
                    bio_rw = "r"
                else:
                    bio_rw = "w"
                print(" corrupt_bio_byte {} {} {} {}".format(flakey_c.corrupt_bio_byte,
                    bio_rw, flakey_c.corrupt_bio_value, flakey_c.corrupt_bio_flags), end='')
        print("{}".format(""))

def show_dmsetup_table_era(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("era", name)):
            return
        era = readSU("struct era", long(target.private))
        print("{}: {} {} era".format(name, target.begin, target.len), end='')

        print(" {}:{} [{}] {}:{} [{}] {}".format(era.metadata_dev.bdev.bd_dev >> 20,
        era.metadata_dev.bdev.bd_dev & 0xfffff, bdev_name(era.metadata_dev.bdev),
        era.origin_dev.bdev.bd_dev >> 20, era.origin_dev.bdev.bd_dev & 0xfffff,
        bdev_name(era.origin_dev.bdev), era.sectors_per_block))

def show_dmsetup_table_verity(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("dm_verity", name)):
            return
        verity = readSU("struct dm_verity", long(target.private))
        print("{}: {} {} verity".format(name, target.begin, target.len), end='')

        data_bits = 1 << verity.data_dev_block_bits
        hash_bits = 1 << verity.hash_dev_block_bits
        print(" {} {} [{}] {} [{}] {} {} {} {} {} ".format(verity.version, verity.data_dev.name,
            bdev_name(verity.data_dev.bdev), verity.hash_dev.name, bdev_name(verity.hash_dev.bdev),
            data_bits, hash_bits, verity.data_blocks, verity.hash_start, verity.alg_name), end='')

        for digest in range(verity.digest_size):
            print("{:02x}".format(verity.root_digest[digest]), end='')
        print("{}".format(" "), end='')

        if (verity.salt_size == 0):
            print("{}".format("-"), end='')
        else:
            for salt in range(verity.salt_size):
                print("{:02x}".format(verity.salt[salt]), end='')

        try:
            verity_modes = EnumInfo("enum verity_mode")
        except TypeError:
            verity_modes = False
            pylog.info("{}: EnumInfo for verity_modes failed".format(name))

        if (verity_modes is not False):
            if ("DM_VERITY_MODE_EIO" in verity_modes):
                if (verity.mode != verity_modes['DM_VERITY_MODE_EIO']):
                    print(" {} ".format("1"), end='')
                    if ("DM_VERITY_OPT_LOGGING" in verity_modes):
                        if (verity.mode == verity_modes['DM_VERITY_OPT_LOGGING']):
                            print("{}".format(verity_modes['DM_VERITY_OPT_LOGGING']), end='')
                    if ("DM_VERITY_OPT_RESTART" in verity_modes):
                        if (verity.mode == verity_modes[DM_VERITY_OPT_RESTART]):
                            print("{}".format(verity_modes[DM_VERITY_OPT_RESTART]), end='')
        print("{}".format(""))

def show_dmsetup_table_linear(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", md.map)
    for target_id in range(dm_table_map.num_targets):
        target = dm_table_map.targets.__getitem__(target_id)
        if (not context_struct_exists("linear_c", name)):
                return
        linear_c = readSU("struct linear_c", target.private)

        print("{}: {} {} linear {}:{} [{}] {}".format(name, target.begin,
            target.len, linear_c.dev.bdev.bd_dev >> 20,
            linear_c.dev.bdev.bd_dev & 0xfffff,
            bdev_name(linear_c.dev.bdev), linear_c.start))

def show_dmsetup_table(dev):
    md, name = dev
    dm_table_map = readSU("struct dm_table", long(md.map))
    target_name = get_dm_target_name(dm_table_map, name)
    if (not target_name):
        pass
    elif (dm_table_map.num_targets == 0):
        print("{}: ".format(name))
    elif (target_name == "linear"):
        show_dmsetup_table_linear(dev)
    elif (target_name == "multipath"):
        show_dmsetup_table_multipath(dev)
    elif (target_name == "striped"):
        show_dmsetup_table_striped(dev)
    elif (target_name == "thin-pool"):
        show_dmsetup_table_thinpool(dev)
    elif (target_name == "thin"):
        show_dmsetup_table_thin(dev)
    elif (target_name == "snapshot-origin"):
        show_dmsetup_table_snap_origin(dev)
    elif (target_name == "snapshot" or
            target_name == "snapshot-merge"):
        show_dmsetup_table_snap(dev)
    elif (target_name == "cache"):
        show_dmsetup_table_cache(dev)
    elif (target_name == "raid"):
        show_dmsetup_table_raid(dev)
    elif (target_name == "raid45"):
        show_dmsetup_table_raid45(dev)
    elif (target_name == "mirror"):
        show_dmsetup_table_mirror(dev)
    elif (target_name == "crypt"):
        show_dmsetup_table_crypt(dev)
    elif (target_name == "delay"):
        show_dmsetup_table_delay(dev)
    elif (target_name == "error" or
            target_name == "zero"):
        show_dmsetup_table_generic(dev)
    elif (target_name == "switch"):
        show_dmsetup_table_switch(dev)
    elif (target_name == "flakey"):
        show_dmsetup_table_flakey(dev)
    elif (target_name == "era"):
        show_dmsetup_table_era(dev)
    elif (target_name == "verity"):
        show_dmsetup_table_verity(dev)
    else:
        print("{}: {} not yet supported by this command".format(name,
              target_name))

def run_check_on_multipath(devlist):
    bts = []
    errors = 0
    task_cnt = 0
    multipathd_daemon = 0   # To verify if multipathd daemon is running
    multipath_blocked = 0   # To verify if multipathd daemon or command is blocked
    mpath_present = 0       # To verify if multipath device exists with or without
                            # multipathd daemon running
    wq_blocked = 0          # To verify if scsi_wq or fc_wq is blocked
    kworker_md_blocked = 0  # Counter for hung worker threads which are waiting for
                            # IO requests on mdraid devices

    print("\n\nChecking for device-mapper issues...\n")

    # No need to continue if we can't pull the TaskTable
    try:
        tt = TaskTable()
    except:
        print("ERROR: Could not gather TaskTable.  Aborting multipath check.")
        return

    for t in tt.allThreads():
        if ('multipathd' in t.comm):
            multipathd_daemon = 1
        if (t.ts.state & TASK_STATE.TASK_UNINTERRUPTIBLE):
            task_cnt += 1
            errors += 1
            # crash can miss some threads when there are pages missing
            # and it will not do 'bt' in that case.
            try:
                bts.append(exec_bt("bt %d" % t.pid)[0])
            except:
                pass

    print("Getting a list of processes in UN state...\t\t\t[Done] "
        "(Count: {:d})".format(task_cnt))

    if (task_cnt):
        print("\nProcessing the back trace of hung tasks...\t\t\t", end='')
        for bt in bts:
            if ('kworker' in bt.cmd):
                if (bt.hasfunc('md_flush_request') and bt.hasfunc('dio_aio_complete_work')):
                    kworker_md_blocked += 1

            if ('multipath' in bt.cmd):
                multipath_blocked = 1

            if (('scsi_wq' in bt.cmd) or ('fc_wq' in bt.cmd)):
                wq_blocked = 1
        print("[Done]")

    # Checks for dm devices
    for dev in devlist:
        md, name = dev
        dm_table_map = readSU("struct dm_table", md.map)
        # Check if there is any multipath device present in device-mapper table
        target_name = get_dm_target_name(dm_table_map, name)
        if (not target_name):
            continue
        elif (target_name == "multipath"):
            mpath_present += 1

    # Check if kworker threads are stuck waiting to flush IO on mdraid devices
    if (kworker_md_blocked >= 5):
        print("\n ** {} kworker threads are stuck in UN state waiting to flush the IO"
              "\n    requests on mdraid devices. This could be a result of thundering"
              "\n    herd problem. See reference: "
              "\n    https://marc.info/?l=linux-raid&m=155364683109115&w=2".format(kworker_md_blocked))
        errors += 1

    # multipath devices are present but multipathd is not running
    if (mpath_present != 0 and multipathd_daemon == 0):
        print("\n ** multipath device(s) are present, but multipathd service is"
              "\n    not running. IO failover/failback may not work.")
        errors += 1

    # scsi or fc work queue and multipathd are blocked
    if (multipath_blocked == 1 and wq_blocked == 1):
        print("\n ** multipathd and scsi/fc work_queue processes are stuck in UN state,"
              "\n    this could block IO failover on multipath devices")
        errors += 1
    # only multipathd process is stuck in UN state
    elif (multipath_blocked == 1):
        print("\n ** multipathd processes stuck in UN state,"
              "\n    this could block IO failover on multipath devices")
        errors += 1

    # check underlying devs for different block sizes (dm-linear only)
    for dev in devlist:
        sizes=[]
        md, name = dev
        dm_table_map = readSU("struct dm_table", md.map)
        for target_id in range(dm_table_map.num_targets):
            target = dm_table_map.targets.__getitem__(target_id)
            target_name = get_dm_target_name(target.table, name)
            if (target_name == "linear"):
                linear_c = readSU("struct linear_c", target.private)
                queue = linear_c.dev.bdev.bd_disk.queue
                sizes.append(queue.limits.logical_block_size)
        if (sizes.count(sizes[0]) != len(sizes)):
            print("\n ** {} underlying device logical_block_size values "
                "are not the same!".format(name))
            errors += 1

    if (errors > 0 and task_cnt != 0):
        print("\n    Found {} processes in UN state.".format(task_cnt))
        print("\n    Run 'hanginfo' for more information on processes in UN state.")
    elif (errors == 0 and task_cnt == 0):
       print ("No issues detected by utility.")

def main():

    import argparse
    parser =  argparse.ArgumentParser()

    parser.add_argument("-x", "--hex", dest="usehex", default = 0,
        action="store_true",
        help="display fields in hex")

    parser.add_argument("--check", dest="runcheck", default = 0,
        action="store_true",
        help="check for common DM issues (WIP)")

    parser.add_argument("-m", "--multipath", dest="multipath", nargs='?',
        const="nr_valid_paths,queue_io", default=0, metavar="FIELDS",
        help="show multipath devices and fields")

    parser.add_argument("-ll", "--list", dest="multipathlist", nargs='?',
        const="nr_valid_paths,queue_io", default=0, metavar="FIELDS",
        help="show multipath device listing similar to \"multipath -ll\"")

    parser.add_argument("-d", "--mapdev", dest="mapdev", nargs='?',
        const="flags", default=0, metavar="FIELDS",
        help="show mapped_devices and fields")

    parser.add_argument("--table", dest="table", default=0,
        action="store_true",
        help="show \"dmsetup table\" like output")

    parser.add_argument("--lvs", dest="lvs", default=0,
        action="store_true",
        help="show lvm volume information similar to \"lvs\" command")

    parser.add_argument("--lvuuid", dest="lvuuid", default=0,
        action="store_true",
        help="show lvm volume and volume group's UUID")

    parser.add_argument("--pvs", dest="pvs", default=0,
        action="store_true",
        help="show physical volume information similar to \"pvs\" command")

    args = parser.parse_args()

    # Try to load all modules from the required list.
    nodlkms = []
    for m in required_modules:
        if (m in lsModules() and not loadModule(m)):
            nodlkms.append(m)

    # If the required modules could not be loaded, then flag a warning 
    # message about the same
    if (nodlkms):
        s = ", ".join(nodlkms)
        print("\n+++Cannot find debuginfo for DLKMs: {}".format(s))
        sys.exit(0)

    if "dm_mod" not in lsModules():
        print("Exiting...device-mapper not in use.")
        return 1

    for m in exec_crash_command_bg('mod').splitlines()[1:]:
        if (('not loaded' in m) and (('dm_mod' in m) or ('dm_multipath' in m))):
            print ("\n ** Unable to process dm device information since dm_mod/dm_multipath "
                   "modules are not loaded")
            print ("    Please try to verify, load the above modules manually and try again.")
            print ("\n    You can use 'help mod' command for more information on how to load "
                   "the modules manually")
            return 1

    try:
        if (symbol_exists(".dm_table_create")):
            exec_crash_command("sym .dm_table_get_devices")
            exec_crash_command("set scope .dm_table_create")
        else:
            exec_crash_command("sym dm_table_get_devices")
            exec_crash_command("set scope dm_table_create")
        setscope = 1
    except:
        setscope = 0

    devlist = get_dm_devices()
    devlist = sorted(devlist, key=lambda dev: dev[0].disk.first_minor)

    if (args.multipath):
        print("{:7}  {:38s} {:19s} {:15s}  {}\n".format("NUMBER", "NAME", "MULTIPATH",
              "nr_valid_paths", "queue_if_no_path"), end="")
    elif (args.multipathlist):
        pass
    elif (args.lvs):
        print("{:11s}   {:40s}  {:40s} {:10s} {:18s}     {}\n".format("LV DM-X DEV",
            "LV NAME", "VG NAME", "OPEN COUNT", "      LV SIZE (MB)", "PV NAME"), end="")
    elif (args.lvuuid):
        print("{:14s}{:40s}  {:40s} {:>18s}  {:32s}  {}".format("LV DM-X DEV",
            "LV NAME", "VG NAME", "LV SIZE (MB)", "LV UUID", "VG UUID"))
    elif (args.pvs):
        print("{:48s}{:16s}{:20s}{:40s}  {}\n".format("PV NAME",
            "PV's MAPPED_DEVICE", "  DEVICE SIZE (MB)", "VG NAME", "LV NAME"), end="")
    elif (args.table):
        pass
    else:
        print("{:6}  {:50} {:20}  {}".format("NUMBER", "NAME", "MAPPED_DEVICE",
              "FLAGS"), end='')

    mpathfound = 0

    for dev in devlist:
        md, name = dev
        try:
            if (args.multipath):
                ret = show_basic_mpath_info(dev)
                if (ret == 0 or ret == 1):
                    mpathfound += ret

            elif (args.multipathlist):
                ret = show_multipath_list(dev)
                if (ret == 0 or ret == 1):
                    mpathfound += ret

            elif (args.lvs):
                show_lvm(dev, devlist, "lvs")

            elif (args.lvuuid):
                show_lvm(dev, devlist, "lvuuid")

            elif (args.pvs):
                show_lvm(dev, devlist, "pvs")

            elif (args.table):
                show_dmsetup_table(dev)

            else:
                print("\ndm-{:<4d} {:<50} {:#x} ".format(md.disk.first_minor, name, md), end='')
                if (args.mapdev):
                    display_fields(md, args.mapdev, usehex=args.usehex)
                else:
                    display_fields(md, "flags", usehex=1)
        except crash.error as errval:
            print("\nERROR: {}: map skipped: {}".format(name, errval))

    if ((args.multipath or args.multipathlist) and (mpathfound == 0)):
        print("\nNo dm-multipath devices found!")

    if (args.pvs):
        print("\n\n   Note: 'DEVICE SIZE' column shows the size of device used for PV, it is\n"
                 "         not the actual PV size. Depending upon the number of Physical\n"
                 "         Extents and Extent size, actual PV size could be slightly less.")

    if (args.runcheck):
        run_check_on_multipath(devlist)

    if (setscope):
        if (symbol_exists(".schedule")):
            exec_crash_command("set scope .schedule")
        else:
            exec_crash_command("set scope schedule")

if ( __name__ == '__main__'):
    main()
