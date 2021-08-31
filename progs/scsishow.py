# --------------------------------------------------------------------
# (C) Copyright 2006-2014 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2014-2015 Red Hat, Inc.
#
# Author: David Jeffery
#
# Contributor:
# - Milan P. Gandhi
#      Added/updated following options:
#       -d     show the scsi devices on system
#              this option is similar to 'shost -d'
#       -s     show Scsi_Host info
#       -T     show scsi targets through which 
#              scsi devices are connected
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

__version__ = "0.0.3"

from pykdump.API import *

from LinuxDump.scsi import *

def test_bit(nbit, val):
    return ((val >> nbit) == 1)

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

def print_request_header(request, devid):
    print("{:x} {:<13}".format(int(request), "({})".format(devid)), end='')

def get_hostt_module_name(shost):
    try:
        name = shost.hostt.module.name
    except:
        name = "unknown"
    return name

SCMD_STATE_COMPLETE = 0
SCMD_STATE_INFLIGHT = 1

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

def get_queue_requests(rqueue):
    out = []
    for request in readSUListFromHead(rqueue.queue_head, "queuelist",
                                      "struct request"):
        out.append(request)
    return out

def display_requests(fields, usehex):
    num_requests = 0
    for sdev in get_scsi_devices():
        cmnd_requests = []
        cmnds = get_scsi_commands(sdev)

        if (member_size("struct request_queue", "queue_head") != -1):
            for cmnd in cmnds:
                cmnd_requests.append(cmnd.request)

            requests = get_queue_requests(sdev.request_queue)
            requests = list(set(requests + cmnd_requests))

            if (requests):
                if (member_size("struct request", "start_time") == -1):
                    fields = fields.replace("start_time", "deadline")
                if (member_size("struct request", "special") == -1):
                    fields = fields.replace("special", "timeout")
                for req in requests:
                    print_request_header(req, get_scsi_device_id(sdev))
                    display_fields(req, fields, usehex=usehex)
                    num_requests += 1
        else:
            if (cmnds):
                for cmnd in cmnds:
                    print_request_header(cmnd.request, get_scsi_device_id(sdev))
                    if (cmnd.request):
                        display_fields(cmnd.request, "timeout,deadline", usehex=usehex)
                        num_requests += 1
                    else:
                        print("request member of scsi_cmnd {:#x} is null".format(cmnd))

    print("\nRequests found in SCSI layer: {}".format(num_requests))

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

def get_scsi_devices(shost=0):
    out = []

    if (shost):
        out = readSUListFromHead(shost.__devices, "siblings", "struct scsi_device")
    else:
        for host in get_scsi_hosts():
            out += readSUListFromHead(host.__devices, "siblings", "struct scsi_device")

    return out

def is_scsi_queue(queue):
    if (member_size("struct request_queue", "mq_ops") == -1 or not queue.mq_ops):
        if (member_size("struct request_queue", "request_fn") != -1):
            if queue.request_fn == sym2addr("scsi_request_fn"):
                return 1
    elif (member_size("struct request_queue", "mq_ops") != -1 and queue.mq_ops == sym2addr("scsi_mq_ops")):
        return 1

    return 0

check_for_sbitmap_word_cleared = 1
def find_used_tags(queue, tags, offset, rqs):
    global check_for_sbitmap_word_cleared
    out = []
    if tags.isNamed("struct sbitmap_queue"):
        tags = tags.sb

    for i in range(tags.map_nr):
        bitmap = tags.map[i].word

        if check_for_sbitmap_word_cleared:
            try:
                mask = ~tags.map[i].cleared
                bitmap = bitmap & mask
            except:
                check_for_sbitmap_word_cleared = 0

        if (not int(bitmap)):
            next

        for j in range(tags.map[i].depth):
            if int(bitmap) & 1:
                rq = rqs[offset]
                if (member_size("struct request", "ref") != -1):
                    if (rq and rq.ref.refs.counter != 0 and rq.q == queue):
                        out.append(rq)
                    elif (rq == 0):
                        print("WARNING: no rq? tag {} map {} offset {}".format(tags, i, offset))
                elif rq:
                    if rq.q == queue:
                        out.append(rq)
                else:
                    print("WARNING: bit set but no request? {} {} map {} rqs {} offset {}".format(queue, tags, i, rqs, offset))
            offset += 1
            bitmap = bitmap >> 1

    return out

def get_scsi_commands_mq(queue):
    out = []
    cmds = []
    if not queue.mq_ops:
        return out

    #find requests which are tagged and in the various hw queues
    for i in range(queue.nr_hw_queues):
        if queue.queue_hw_ctx[i].tags:
            out += find_used_tags(queue,
                                  queue.queue_hw_ctx[i].tags.breserved_tags,
                                  0, queue.queue_hw_ctx[i].tags.rqs)
            out += find_used_tags(queue, queue.queue_hw_ctx[i].tags.bitmap_tags,
                                  queue.queue_hw_ctx[i].tags.nr_reserved_tags,
                                  queue.queue_hw_ctx[i].tags.rqs)

        if ((member_size("struct blk_mq_hw_ctx", "sched_tags") != -1) and
          queue.queue_hw_ctx[i].sched_tags):
            out += find_used_tags(queue,
                             queue.queue_hw_ctx[i].sched_tags.breserved_tags,
                             0, queue.queue_hw_ctx[i].sched_tags.static_rqs)
            out += find_used_tags(queue,
                             queue.queue_hw_ctx[i].sched_tags.bitmap_tags,
                             queue.queue_hw_ctx[i].sched_tags.nr_reserved_tags,
                             queue.queue_hw_ctx[i].sched_tags.static_rqs)

    for rq in out:
        cmd = readSU("struct scsi_cmnd",
            long(Addr(rq) + struct_size("struct request")))
        cmds.append(cmd)

    # I/O scheduler requests can show up in both sched_tags and hw ctx tags,
    # abuse set to remove any duplicates
    cmds = list(set(cmds))

    return cmds

def get_scsi_commands_sq(sdev):
    out = []
    if is_scsi_queue(sdev.request_queue):
        for cmnd in readSUListFromHead(sdev.cmd_list, "list", "struct scsi_cmnd"):
            out.append(cmnd)
    return out

def get_scsi_commands(sdev):
    out = []
    if (member_size("struct request_queue", "mq_ops") == -1):
        out += get_scsi_commands_sq(sdev)
    elif sdev.request_queue.mq_ops:
        out += get_scsi_commands_mq(sdev.request_queue)
    else:
        out += get_scsi_commands_sq(sdev)
    return out

def get_scsi_device_id(sdev):
    return "{:d}:{:d}:{:d}:{:d}".format(sdev.host.host_no,
                                        sdev.channel, sdev.id, sdev.lun)

def print_cmnd_header(cmnd):
    if (cmnd.device):
        print("scsi_cmnd {:x} {:<13}".format(int(cmnd),
              "on scsi_device {:#x} ({})".format(cmnd.device, get_scsi_device_id(cmnd.device))), end='')
    else:
        print("Warning: device member for scsi_cmnd {:x} is null".format(int(cmnd)), end='')

def print_sdev_header(sdev):
    print("{:x}  {:<12}".format(int(sdev),
              get_scsi_device_id(sdev)), end='')

def print_shost_header(shost):
    print("HOST      DRIVER")
    print("{:10s}{:22s} {:24s} {:24s} {:24s}".format("NAME", "NAME", "Scsi_Host",
          "shost_data", "hostdata"))
    print("--------------------------------------------------"
          "-------------------------------------------------")
    print("{:9s} {:22s} {:12x} {:24x} {:24x}\n".format(shost.shost_gendev.kobj.name,
        get_hostt_module_name(shost), shost, shost.shost_data, shost.hostdata))

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

def print_sdev_shost():
    enum_sdev_state = EnumInfo("enum scsi_device_state")

    gendev_dict = get_gendev()

    for shost in get_scsi_hosts():
        if (shost.__devices.next != shost.__devices.next.next):
            print("\n===================================================================="
                  "====================================================================")

            print_shost_header(shost)

            print("{:12s} {:19s} {:12s} {:26s} {:22s} {}  {}    {}".format("DEV NAME",
                  "scsi_device", "H:C:T:L", "VENDOR/MODEL", "DEVICE STATE",
                  "IOREQ-CNT", "IODONE-CNT", "      IOERR-CNT"))
            print("--------------------------------------------------------------------"
                  "--------------------------------------------------------------------")

            for sdev in readSUListFromHead(shost.__devices, "siblings", "struct scsi_device"):
                name = scsi_device_type(sdev.type)

                if (name):
                    if (name in 'Sequential-Access'):
                        name = "Tape"
                    elif (name in 'Medium Changer   '):
                        name = "Chngr"
                    elif (name in 'RAID             '):
                        name = "CTRL"
                    elif ((name in 'Direct-Access    ') or
                          (name in 'CD-ROM           ')):
                         sdev_q = readSU("struct request_queue", sdev.request_queue)
                         sdev_q = format(sdev_q, 'x')
                         try:
                             gendev = gendev_dict[sdev_q]
                             gendev = readSU("struct gendisk", long (gendev, 16))
                             name = gendev.disk_name
                         except:
                             name = "Disk"
                else:
                    name = "null"

                try:
                    sdev_state = get_sdev_state(enum_sdev_state.getnam(sdev.sdev_state))
                except:
                    if (sdev.sdev_state == 9):
                        sdev_state = "SDEV_TRANSPORT_OFFLINE"
                    else:
                        sdev_state = "<Error in processing sdev_state>"
                vendor_str = sdev.vendor[:8].strip() + " " + sdev.model[:16].strip()
                print("{:12s} {:x}    {:12} {:26s} {:20s}"
                      "{:12d} {:11d}  ({:3d}){:12d}".format(name.strip(),
                      sdev, get_scsi_device_id(sdev), vendor_str, sdev_state,
                      sdev.iorequest_cnt.counter, sdev.iodone_cnt.counter,
                      sdev.iorequest_cnt.counter-sdev.iodone_cnt.counter,
                      sdev.ioerr_cnt.counter))

def print_starget_shost():
    enum_starget_state = EnumInfo("enum scsi_target_state")
    stgt_busy_block_cnt = -1

    for shost in get_scsi_hosts():
        if (shost.__targets.next != shost.__targets.next.next):
            print("\n======================================================="
                  "========================================================")

            print_shost_header(shost)

            print("{:15s} {:20s} {:8s} {:6s} {:20s} {:15s} {:15s}".format("TARGET DEVICE",
                  "scsi_target", "CHANNEL", "ID", "TARGET STATUS", 
                  "TARGET_BUSY", "TARGET_BLOCKED"))
            print("----------------------------------------------------"
                  "----------------------------------------------------")

            for starget in readSUListFromHead(shost.__targets, "siblings", "struct scsi_target"):

                if (member_size("struct scsi_target", "target_busy") != -1):
                    try:
                        stgt_busy_block_cnt = readSU("struct scsi_target", long(starget.target_busy.counter))
                    except:
                        stgt_busy_block_cnt = -1

                    try:
                        print("{:15s} {:x} {:3s} {:5d} {:5d} {:4s}"
                              "{:20s}".format(starget.dev.kobj.name,
                              int(starget), "", starget.channel, starget.id, "",
                              enum_starget_state.getnam(starget.state)), end='')

                        if (stgt_busy_block_cnt != -1):
                            print("{:12d} {:18d}".format(starget.target_busy.counter,
                                  starget.target_blocked.counter))

                        elif (stgt_busy_block_cnt == -1 and
                              member_size("struct scsi_target", "target_busy") == -1):
                            print(" <Not defined in scsi_target>")

                        else:
                            print("{:12d} {:18d}".format(starget.target_busy,
                                  starget.target_blocked))

                    except KeyError:
                        pylog.warning("Error in processing scsi_target {:x},"
                                      "please check manually".format(int(starget)))

def print_fcrports():
    supported_modules = ["lpfc", "qla2xxx", "fnic", "qedf"]
    for shost in get_scsi_hosts():
        if (shost.__targets.next != shost.__targets.next.next and
            get_hostt_module_name(shost) in supported_modules):
            print("\n==================================================="
                  "====================================================="
                  "==================================================")

            print_shost_header(shost)

            print("{:15s} {:16s} {:16s} {:16s} {:16s} {:11s} {:24s} {:20s} {:16s}".format("TARGET DEVICE",
                  "scsi_target", "fc_rport", "node_name", "port_name", "port_id",
                  "port_state", "fast_io_fail_tmo", "dev_loss_tmo"))
            print("----------------------------------------------------"
                  "----------------------------------------------------"
                  "--------------------------------------------------")

            enum_fcrport_state = EnumInfo("enum fc_port_state")

            for starget in readSUListFromHead(shost.__targets, "siblings", "struct scsi_target"):
                try:
                    dev_parent = readSU("struct device", starget.dev.parent)
                    fc_rport = container_of(dev_parent, "struct fc_rport", "dev")
                    print("{:15s} {:x} {:x} {:x} {:x} {:#x}\t{:24s}{:16d}s {:15d}s".format(starget.dev.kobj.name,
                          starget, fc_rport, fc_rport.node_name, fc_rport.port_name, fc_rport.port_id,
                          enum_fcrport_state.getnam(fc_rport.port_state), fc_rport.fast_io_fail_tmo,
                          fc_rport. dev_loss_tmo))
                except KeyError:
                    pylog.warning("Error in processing FC rports connnected to scsi_target {:x},"
                                  "please check manually".format(int(starget)))

def print_qla2xxx_shost_info(shost):
    scsi_qla_host = readSU("struct scsi_qla_host", shost.hostdata)
    qla_hw_data = readSU("struct qla_hw_data", scsi_qla_host.hw)
    print("\n\n   Qlogic HBA specific details")
    print("   ---------------------------")
    print("   scsi_qla_host       : {:x}".format(scsi_qla_host))
    print("   qla_hw_data         : {:x}".format(qla_hw_data))
    print("   pci_dev             : {:x}".format(qla_hw_data.pdev))
    print("   pci_dev slot        : {}".format(qla_hw_data.pdev.dev.kobj.name))
    print("   operating_mode      : {}".format(qla_hw_data.operating_mode))
    print("   model_desc          : {}".format(qla_hw_data.model_desc))
    print("   optrom_state        : {}".format(qla_hw_data.optrom_state))
    print("   fw_major_version    : {}".format(qla_hw_data.fw_major_version))
    print("   fw_minor_version    : {}".format(qla_hw_data.fw_minor_version))
    print("   fw_subminor_version : {}".format(qla_hw_data.fw_subminor_version))
    print("   fw_dumped           : {}".format(qla_hw_data.fw_dumped))
    print("   ql2xmaxqdepth       : {}".format(readSymbol("ql2xmaxqdepth")))

def print_lpfc_shost_info(shost):
    lpfc_vport = readSU("struct lpfc_vport", shost.hostdata)
    lpfc_hba = readSU("struct lpfc_hba", lpfc_vport.phba)
    print("\n\n   Emulex HBA specific details")
    print("   ---------------------------")
    print("   lpfc_vport          : {:x}".format(lpfc_vport))
    print("   lpfc_hba            : {:x}".format(lpfc_hba))
    print("   sli_rev             : {}".format(lpfc_hba.sli_rev))
    print("   pci_dev             : {:x}".format(lpfc_hba.pcidev))
    print("   pci_dev slot        : {}".format(lpfc_hba.pcidev.dev.kobj.name))
    print("   brd_no              : {}".format(lpfc_hba.brd_no))
    print("   SerialNumber        : {}".format(lpfc_hba.SerialNumber))
    print("   OptionROMVersion    : {}".format(lpfc_hba.OptionROMVersion))
    print("   ModelDesc           : {}".format(lpfc_hba.ModelDesc))
    print("   ModelName           : {}".format(lpfc_hba.ModelName))
    print("   cfg_hba_queue_depth : {}".format(lpfc_hba.cfg_hba_queue_depth))
    print("   cfg_lun_queue_depth : {}".format(lpfc_vport.cfg_lun_queue_depth))
    if (member_size("struct lpfc_vport", "cfg_tgt_queue_depth") != -1):
        print("   cfg_tgt_queue_depth : {}".format(lpfc_vport.cfg_tgt_queue_depth))

def print_hpsa_shost_info(shost):
    ctlr_info = readSU("struct ctlr_info", shost.hostdata[0])
    print("\n\n   HPSA HBA specific details")
    print("   ---------------------------")
    print("   ctlr_info           : {:x}".format(ctlr_info))
    print("   pci_dev             : {:x}".format(ctlr_info.pdev))
    print("   pci_dev slot        : {}".format(ctlr_info.pdev.dev.kobj.name))
    print("   devname             : {}".format(ctlr_info.devname))
    print("   product_name        : {}".format(ctlr_info.product_name))
    print("   board_id            : {:#x}".format(ctlr_info.board_id))
    print("   fwrev               : {:c}{:c}{:c}{:c}{:c}".format(ctlr_info.hba_inquiry_data[32],
        ctlr_info.hba_inquiry_data[33], ctlr_info.hba_inquiry_data[34],
        ctlr_info.hba_inquiry_data[35], ctlr_info.hba_inquiry_data[36]))
    print("   CommandList         : {:x}".format(ctlr_info.cmd_pool))
    print("   nr_cmds             : {}".format(ctlr_info.nr_cmds))
    print("   max_commands        : {}".format(ctlr_info.max_commands))
    print("   commands_outstanding: {}".format(ctlr_info.commands_outstanding.counter))
    print("   interrupts_enabled  : {}".format(ctlr_info.interrupts_enabled))
    print("   intr_mode           : {}".format(ctlr_info.intr_mode))
    print("   remove_in_progress  : {}".format(ctlr_info.remove_in_progress))
    print("   reset_in_progress   : {}".format(ctlr_info.reset_in_progress))

def print_vmw_pvscsi_shost_info(shost):
    pvscsi_adapter = readSU("struct pvscsi_adapter", shost.hostdata)
    pci_dev = readSU("struct pci_dev", pvscsi_adapter.dev)
    print("\n\n   PVSCSI HBA specific details")
    print("   ---------------------------")
    print("   pvscsi_adapter      : {:x}".format(pvscsi_adapter))
    print("   pci_dev             : {:x}".format(pci_dev))
    print("   pci_dev slot        : {}".format(pci_dev.dev.kobj.name))
    print("   req_pages           : {}".format(pvscsi_adapter.req_pages))
    print("   req_depth           : {}".format(pvscsi_adapter.req_depth))
    print("   use_req_threshold   : {}".format(pvscsi_adapter.use_req_threshold))
    print("   PVSCSIRingReqDesc   : {:x}".format(pvscsi_adapter.req_ring))
    print("   PVSCSIRingCmpDesc   : {:x}".format(pvscsi_adapter.cmp_ring))
    print("   PVSCSIRingMsgDesc   : {:x}".format(pvscsi_adapter.msg_ring))
    print("   PVSCSIRingsState    : {:x}".format(pvscsi_adapter.rings_state))
    print("   cmd_pool            : {:x}".format(pvscsi_adapter.cmd_pool))

def print_shost_info():
    enum_shost_state = EnumInfo("enum scsi_host_state")

    hosts = get_scsi_hosts()
    mod_with_verbose_info = ["lpfc", "qla2xxx", "fnic", "hpsa", "vmw_pvscsi"]
    verbose_info_logged = 0
    verbose_info_available = 0

    for shost in hosts:
        print("\n============================================================="
              "============================================================")

        print_shost_header(shost)

        try:
            print("   Driver version      : {}".format(shost.hostt.module.version))
        except:
            print("   Driver version      : {}".format("Error in checking "
                                                             "'Scsi_Host->hostt->module->version'"))

        if (member_size("struct Scsi_Host", "host_busy") != -1):
            print("\n   host_busy           : {}".format(atomic_t(shost.host_busy)), end="")
        else:
            print("\n   host_busy           : {}".format(get_host_busy(shost)), end="")
        print("\n   host_blocked        : {}".format(atomic_t(shost.host_blocked)))

        print("   host_failed         : {}".format(shost.host_failed))
        print("   host_self_blocked   : {}".format(shost.host_self_blocked))
        print("   shost_state         : {}".format(enum_shost_state.getnam(shost.shost_state)))

        if (member_size("struct Scsi_Host", "eh_deadline") != -1):
            if (shost.eh_deadline == -1 and shost.hostt.eh_host_reset_handler != 0):
                print("   eh_deadline         : {} (off)".format(shost.eh_deadline))
            elif (shost.eh_deadline == -1 and shost.hostt.eh_host_reset_handler == 0):
                print("   eh_deadline         : {} (off, not supported by driver)".format(
                      shost.eh_deadline))
            elif (shost.eh_deadline != -1 and shost.hostt.eh_host_reset_handler != 0):
                print("   eh_deadline         : {}".format(shost.eh_deadline))

        print("   max_lun             : {}".format(shost.max_lun))
        print("   cmd_per_lun         : {}".format(shost.cmd_per_lun))
        print("   work_q_name         : {}".format(shost.work_q_name))

        if (struct_exists("struct fc_host_attrs") and verbose == 1):
            try:
                fc_host_attrs = readSU("struct fc_host_attrs", shost.shost_data)
                if (fc_host_attrs and ('fc_wq_' in fc_host_attrs.work_q_name[:8])):
                    print("\n\n   FC/FCoE HBA attributes")
                    print("   ----------------------")
                    print("   fc_host_attrs       : {:x}".format(fc_host_attrs))
                    print("   node_name (wwnn)    : {:x}".format(fc_host_attrs.node_name))
                    print("   port_name (wwpn)    : {:x}".format(fc_host_attrs.port_name))
                    verbose_info_logged += 1
            except:
                pylog.warning("Error in processing verbose details from shost.shost_data: "
                              "{:x} for Scsi_Host: {} ({:x})".format(shost.shost_data,
                              shost.shost_gendev.kobj.name, shost))

        if (verbose):
            try:
                if (('lpfc' in get_hostt_module_name(shost)) and struct_exists("struct lpfc_hba")):
                    print_lpfc_shost_info(shost)
                    verbose_info_logged += 1
                elif (('qla2xxx' in get_hostt_module_name(shost)) and struct_exists("struct qla_hw_data")):
                    print_qla2xxx_shost_info(shost)
                    verbose_info_logged += 1
                elif (('hpsa' in get_hostt_module_name(shost)) and struct_exists("struct ctlr_info")):
                    print_hpsa_shost_info(shost)
                    verbose_info_logged += 1
                elif (('vmw_pvscsi' in get_hostt_module_name(shost)) and
                       struct_exists("struct pvscsi_adapter")):
                    print_vmw_pvscsi_shost_info(shost)
                    verbose_info_logged += 1
            except:
                pylog.warning("Error in processing verbose details for Scsi_Host: "
                              "{} ({:x})".format(shost.shost_gendev.kobj.name, shost))

        if (get_hostt_module_name(shost) in mod_with_verbose_info):
            verbose_info_available += 1

    if (verbose_info_available !=0 and verbose_info_logged == 0):
        print("\n\n   *** NOTE: More detailed HBA information available, use '-v'"
              " or '--verbose' to view.")

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

def print_queue(sdev):
    jiffies = readSymbol("jiffies")

    opcode_table = {'0x00':'TUR', '0x03':'REQ-SENSE', '0x08':'READ(6)',\
                    '0x0a':'WRITE(6)', '0x12':'INQUIRY', '0x16':'RESERVE(6)',\
                    '0x17':'RELEASE(6)', '0x25':'READ-CAP(10)', '0x28':'READ(10)',\
                    '0x2a':'WRITE(10)', '0x35':'SYNC CACHE', '0x41':'WR SAME',\
                    '0x56':'RESERVE(10)', '0x57':'RELEASE(10)', '0x88':'READ(16)',\
                    '0x8a':'WRITE(16)','0xa0':'REPORT LUNS', '0xa8':'READ(12)',\
                    '0xaa':'WRITE(12)'}

    cmnd_requests = []
    cmnds = get_scsi_commands(sdev)
    for cmnd in cmnds:
        cmnd_requests.append(cmnd.request)

    if (member_size("struct request_queue", "queue_head") != -1):
        requests = get_queue_requests(sdev.request_queue)
        requests = list(set(requests + cmnd_requests))
    else:
        requests = cmnd_requests

    print("\n     {:10s}{:20s} {:20s} {:18s} {:14s} {:20s} {:10s}".format("NO.", "request",
          "bio", "scsi_cmnd", "OPCODE", "COMMAND AGE", "SECTOR"))
    print("     ---------------------------------------------------------"
          "--------------------------------------------------------")

    counter = 0
    for req in requests:
        counter = counter + 1
        try:
            if ((member_size("struct request_queue", "mq_ops") != -1) and req.q.mq_ops):
                cmnd = readSU("struct scsi_cmnd",
                    long(Addr(req) + struct_size("struct request")))
            else:
                cmnd = readSU("struct scsi_cmnd", long(req.special))
        except:
            cmnd = 0

        if (cmnd):
            time = (long(jiffies) - long(cmnd.jiffies_at_alloc))
            opcode = readSU("struct scsi_cmnd", long(cmnd.cmnd[0]))
            opcode = hex(opcode)
            try:
                opcode = opcode_table[opcode]
            except:
                pass
            print("     {:3d} {:3s} {:18x} {:20x} {:20x}   {:14} {:8d} ms ".format(counter, "",
                  req, req.bio, cmnd, opcode, long(time)), end="")
        else:
            print("     {:3d} {:3s} {:18x} {:20x} {:20x}   {:14} {:12}".format(counter, "",
                  req, req.bio, cmnd, "-NA-", "-NA-"), end="")

        if (req.bio):
            if (member_size("struct bio", "bi_sector") != -1):
                print("{:15d}".format(req.bio.bi_sector))
            else:
                print("{:15d}".format(req.bio.bi_iter.bi_sector))
        else:
                print("       ---NA---")
    if (counter == 0):
        print("\t\t<<< NO I/O REQUESTS FOUND ON THE DEVICE! >>>")

def print_request_queue():
    gendev_dict = get_gendev()

    for sdev in get_scsi_devices():
        gendev_present = 1
        elevator_name = get_sdev_elevator(sdev)
        vendor_str = sdev.vendor[:8].strip() + " " + sdev.model[:16].strip()
        sdev_q = readSU("struct request_queue", sdev.request_queue)
        sdev_q = format(sdev_q, 'x')
        try:
            gendev = gendev_dict[sdev_q]
            gendev = readSU("struct gendisk", long (gendev, 16))
            name = gendev.disk_name
        except:
            gendev_present = 0
            name = scsi_device_type(sdev.type)
            if (not name):
                name = "null"
            elif (name in 'Sequential-Access'):
                name = "Tape"
            elif (name in 'Medium Changer   '):
                name = "Chngr"
            elif (name in 'RAID             '):
                name = "CTRL"

        print("\n==========================================================="
              "============================================================")
        print("    ### DEVICE : {}\n".format(name))

        print("        ----------------------------------------------------"
              "-----------------------------------")

        if (not (gendev_present)):
            print("\tgendisk        \t:  {} |"
                  "\tscsi_device \t:  {:x}".format("<Can't find gendisk>", int(sdev)))
        else:
            print("\tgendisk        \t:  {:x}\t|\tscsi_device \t:  {:x}".format(int(gendev), int(sdev)))
        print("\trequest_queue  \t:  {}\t|\tH:C:T:L       \t:  {}".format(sdev_q,
              sdev.sdev_gendev.kobj.name))
        print("\televator_name  \t:  {}    \t\t|\tVENDOR/MODEL\t:  {}".format(elevator_name,
              vendor_str))
        print("        ----------------------------------------------------"
              "-----------------------------------")

        print_queue(sdev)

def lookup_field(obj, fieldname):
    segments = fieldname.split("[")
    while (len(segments) > 0):
        obj = obj.Eval(segments[0])
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


def display_fields(display, fieldstr, evaldict={}, usehex=0, relative=0):
    evaldict['display'] = display
    for fieldname in fieldstr.split(","):
        try:
            field = lookup_field(display, fieldname)
#        field = eval("display.{}".format(fieldname),{}, evaldict)
            if (relative):
                try:
                    field = long(field) - long(relative)
                except ValueError:
                    field = long(field) - long(readSymbol(relative))
        except (IndexError, crash.error) as e:
            field = "\"ERROR {}\"".format(e)

        if (usehex or isinstance(field, StructResult) or
                      isinstance(field, tPtr)):
            try:
                print(" {}: {:<#10x}".format(fieldname, field), end='')
            except ValueError:
                print(" {}: {:<10}".format(fieldname, field), end='')
        else:
            print(" {}: {:<10}".format(fieldname, field), end='')
    del evaldict['display']
    print("")

#x86_64 only!
def is_kernel_address(addr):
    if ((addr & 0xffff000000000000) != 0xffff000000000000):
        return 0
    if (addr > -65536):
        return 0
    if ((addr & 0xfffff00000000000) == 0xffff800000000000):
        return 1
    if ((addr & 0xffffff0000000000) == 0xffffea0000000000):
        return 1
    if ((addr & 0xffffffff00000000) == 0xffffffff00000000):
        return 1
    return 0

def display_command_time(cmnd, use_start_time_ns):
    rq_start_time = 0
    start_time = 0
    deadline = 0
    jiffies = readSymbol("jiffies")
    state = "unknown"
    HZ = sys_info.HZ

    # get time scsi_cmnd allocated/started
    try:
        start_time = cmnd.jiffies_at_alloc
    except KeyError:
        pass

    if (start_time):
        start_time -= jiffies
    else:
        start_time = "Err"

    try:
        if use_start_time_ns:
            rq_start_time = cmnd.request.start_time_ns
        else:
            rq_start_time = cmnd.request.start_time

    except KeyError:
        pass

    # get time request allocated/started
    if (rq_start_time):
        if use_start_time_ns:
            jiffies_ns = (jiffies - ((-300 * HZ) & 0xffffffff)) * 1000000000 / HZ
            rq_start_time = int((rq_start_time - jiffies_ns) * HZ / 1000000000)
        else:
            rq_start_time -= jiffies
    else:
        rq_start_time = "Err"

    try:
        deadline = cmnd.request.deadline

        if (long(cmnd.request.timeout_list.next)
               != long(cmnd.request.timeout_list)):
            state = "active"
        elif (cmnd.eh_entry.next and
              (long(cmnd.eh_entry.next) != long(cmnd.eh_entry))):
            state = "timeout"
        #csd.list next/prev pointers  may be uninitiallized, so check for sanity
        elif (cmnd.request.csd.list.next and cmnd.request.csd.list.prev and
              (long(cmnd.request.csd.list.next) != long(cmnd.request.csd.list))
              and is_kernel_address(long(cmnd.request.csd.list.next)) and
              is_kernel_address(long(cmnd.request.csd.list.prev))):
            state = "softirq"
        elif (long(cmnd.request.queuelist) != long(cmnd.request.queuelist.next)):
            state = "queued"

    except KeyError:
        pass

    try:
        deadline = cmnd.eh_timeout.expires
        if (cmnd.eh_timeout.entry.next):
            state = "active"
        elif (cmnd.eh_entry.next and
              (long(cmnd.eh_entry.next) != long(cmnd.eh_entry))):
            state = "timeout"
        elif (long(cmnd.request.queuelist) != long(cmnd.request.queuelist.next)):
            state = "queued"
        elif (long(cmnd.request.donelist) != long(cmnd.request.donelist.next)):
            state = "softirq"
    except KeyError:
        pass

    # get time to timeout or state
    if (deadline):
        deadline -= jiffies
    else:
        deadline = "N/A"

    print(" is {}, deadline: {} cmnd-alloc: {} rq-alloc: {}".format(state, deadline, start_time, rq_start_time), end='')

def run_host_checks():
    host_warnings = 0

    for host in get_scsi_hosts():
        if (host.host_failed):
            host_warnings += 1
            if (member_size("struct Scsi_Host", "host_busy") != 1):
                if (host.host_failed == atomic_t(host.host_busy)):
                    print("WARNING: Scsi_Host {:#x} ({}) is running error recovery!".format(host,
                        host.shost_gendev.kobj.name))
                else:
                    print("WARNING: Scsi_Host {:#x} ({}) has timed out commands, but has not started error recovery!".format(host,
                        host.shost_gendev.kobj.name))
            else:
                print("WARNING: Scsi_Host {:#x} ({}) has timed out commands!".format(host, host.shost_gendev.kobj.name))

            if (atomic_t(host.host_blocked)):
                host_warnings += 1
                print("WARNING: Scsi_Host {:#x} ({}) is blocked! HBA driver refusing all commands with SCSI_MLQUEUE_HOST_BUSY?".format(host,
                    host.shost_gendev.kobj.name))
    return host_warnings

def run_cmd_checks(sdev):
    cmd_warnings = 0
    jiffies = readSymbol("jiffies")

    scmd_results = {
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

    for cmnd in get_scsi_commands(sdev):
        timeout = 0
        if (cmnd.request):
            try:
                timeout = cmnd.request.timeout
            except KeyError:
                timeout = -1
        else:
            print("WARNING: cmnd.request is null for scsi_cmnd {:#x}".format(cmnd))

        if (timeout == -1):
            try:
                timeout = cmnd.timeout_per_command
            except KeyError:
                print("Error: cannot determine timeout!")
                timeout = 0

        # Check for large timeout values
        if (timeout >= 300000):
            cmd_warnings += 1
            print("WARNING: scsi_cmnd {:#x} on scsi_device {:#x} ({}) has a huge timeout of {}ms!".format(cmnd,
                   cmnd.device, get_scsi_device_id(cmnd.device), timeout))
        elif (timeout > 60000):
            cmd_warnings += 1
            print("WARNING: scsi_cmnd {:#x} on scsi_device {:#x} ({}) has a large timeout of {}ms.".format(cmnd,
                   cmnd.device, get_scsi_device_id(cmnd.device), timeout))

        # check for old command
        if (timeout and jiffies > (timeout + cmnd.jiffies_at_alloc)):
            cmd_warnings += 1
            print("WARNING: scsi_cmnd {:#x} on scsi_device {:#x} ({}) older than its timeout: "
                  "EH or stalled queue?".format(cmnd, cmnd.device, get_scsi_device_id(cmnd.device)))

        # check for commands that have been retried, indicating potential prior failure
        if (cmnd.retries > 0):
            cmd_warnings += 1
            print("WARNING: scsi_cmnd {:#x} on scsi_device {:#x} ({}) has a retries value of {}!".format(cmnd,
                   cmnd.device, get_scsi_device_id(cmnd.device), cmnd.retries))

        # check for non-zero result values
        if (cmnd.result > 0):
            print("WARNING: scsi_cmnd {:#x} on scsi_device {:#x} ({}) has a result value of {}!".format(cmnd,
                   cmnd.device, get_scsi_device_id(cmnd.device), scmd_results[cmnd.result]))

    return cmd_warnings

def run_sdev_cmd_checks():
    dev_warnings = 0
    cmd_warnings = 0
    retry_delay_bug = 0
    qla_cmd_abort_bug = 0
    gendev_q_sdev_q_mismatch = 0
    jiffies = readSymbol("jiffies")

    gendev_dict = get_gendev()

    for sdev in get_scsi_devices():
        if (atomic_t(sdev.device_blocked)):
            dev_warnings += 1
            print("WARNING: scsi_device {:#x} ({}) is blocked! HBA driver returning "
                    "SCSI_MLQUEUE_DEVICE_BUSY or device returning SAM_STAT_BUSY?".format(sdev,
                    get_scsi_device_id(sdev)))
        if (member_size("struct scsi_device", "device_busy") != -1):
            device_busy = atomic_t(sdev.device_busy)
        else:
            device_busy = get_scsi_device_busy(sdev)
        if (device_busy < 0):
            dev_warnings += 1
            print("ERROR:   scsi_device {:#x} ({}) device_busy count is: {}".format(sdev,
                get_scsi_device_id(sdev), device_busy))
            if (sdev.host.hostt.name in "qla2xxx"):
                qla_cmd_abort_bug += 1

        # Check if scsi_device->request_queue is same as corresponding gendisk->queue.
        name = scsi_device_type(sdev.type)
        if (name):
            if (name in 'Direct-Access    '):
                sdev_q = readSU("struct request_queue", sdev.request_queue)
                sdev_q = format(sdev_q, 'x')
                try:
                    gendev = gendev_dict[sdev_q]
                except:
                    gendev_q_sdev_q_mismatch += 1

        # Checks for qla2xxx bug for retry_delay RH BZ#1588133
        if (sdev.host.hostt.name in "qla2xxx" and 
            struct_exists("struct fc_port") and 
            (member_size("struct fc_port", "retry_delay_timestamp") != -1)):

            fc_port = readSU("struct fc_port", long(sdev.hostdata))

            if (fc_port):
                retry_delay_timestamp = readSU("struct fc_port", long(fc_port.retry_delay_timestamp))
            else:
                # If fc_port is NULL, then fetching the retry_delay_timestamp would result in crash,
                # so just mark retry_delay_timestamp to 0 and process next sdev and fc_port
                retry_delay_timestamp = 0

            if (retry_delay_timestamp != 0):
                retry_delay = (retry_delay_timestamp - jiffies)/1000/60
                if (retry_delay > 2):
                    dev_warnings += 1
                    print("ERROR:   scsi_device {:#x} ({}) has retry_delay_timestamp: {:d}, "
                          "IOs delayed for {:f} more minutes".format(sdev, get_scsi_device_id(sdev),
                          retry_delay_timestamp, retry_delay))
                    retry_delay_bug += 1

        # command checks
        cmd_warnings += run_cmd_checks(sdev)

    if (retry_delay_bug):
        print("\nERROR:   HBA driver returning 'SCSI_MLQUEUE_TARGET_BUSY' due to a large retry_delay.\n"
              "\t See https://patchwork.kernel.org/patch/10450567/")

    if (qla_cmd_abort_bug):
        print("\nERROR:   scsi_device.device_busy count is negative, this could be caused due to"
              "\t double completion of scsi_cmnd from qla2xxx_eh_abort.\n"
              "\t See https://patchwork.kernel.org/patch/10587997/")

    if (gendev_q_sdev_q_mismatch):
        print("\nNOTE:    The scsi_device->request_queue is not same as gendisk->request_queue\n"
              "\t for {} scsi device(s). \n\n"
              "\t It is likely that custom multipathing solutions have created 'gendisk',\n"
              "\t 'request_queue' structures which are not registered with kernel.\n"
              "\t *Although this may or may not be a reason for issue, but it could make\n"
              "\t the analysis of scsi_device, request_queue and gendisk struct confusing!\n"
              .format(gendev_q_sdev_q_mismatch))

    dev_warnings += cmd_warnings

    return (dev_warnings)

def run_target_checks():
    target_warnings = 0
    fc_rport_warnings = 0
    enum_starget_state = EnumInfo("enum scsi_target_state")
    supported_modules = ["lpfc", "qla2xxx", "fnic", "qedf"]

    for shost in get_scsi_hosts():
        if (shost.__targets.next != shost.__targets.next.next):
            for starget in readSUListFromHead(shost.__targets, "siblings", "struct scsi_target"):
                if (member_size("struct scsi_target", "target_busy") != -1):
                    try:
                        if (atomic_t(starget.target_busy) > 0):
                            target_warnings += 1
                            print("WARNING: scsi_target {:10s} {:x} is having non-zero "
                                "target_busy count: {:d}".format(starget.dev.kobj.name,
                                int(starget), atomic_t(starget.target_busy)))
                        if (atomic_t(starget.target_blocked) > 0):
                            target_warnings += 1
                            print("WARNING: scsi_target {:10s} {:x} is blocked "
                                "(target_blocked count: {:d})".format(starget.dev.kobj.name,
                                starget, atomic_t(starget.target_blocked)))
                        if (enum_starget_state.getnam(starget.state) != 'STARGET_RUNNING'):
                            target_warnings += 1
                            print("WARNING: scsi_target {:10s} {:x} not in RUNNING "
                                  "state".format(starget.dev.kobj.name, starget))
                            if (get_hostt_module_name(shost) in supported_modules):
                                enum_fcrport_state = EnumInfo("enum fc_port_state")
                                dev_parent = readSU("struct device", starget.dev.parent)
                                fc_rport = container_of(dev_parent, "struct fc_rport", "dev")
                                if (enum_fcrport_state.getnam(fc_rport.port_state) != 'FC_PORTSTATE_ONLINE'):
                                    print("         FC rport (WWPN: {:x}) on {:10s} is not "
                                          "online".format(fc_rport.port_name, starget.dev.kobj.name))
                                    fc_rport_warnings += 1

                    except KeyError:
                        pylog.warning("Error in processing scsi_target {:x},"
                                      "please check manually".format(int(starget)))

    if (fc_rport_warnings):
        print("\nERROR:   Couple of FC remote port(s) are NOT in ONLINE state, use '-f' to check detailed information.\n")

    return target_warnings

def run_scsi_checks():
    host_warnings = 0
    dev_cmd_warnings = 0
    target_warnings = 0

    # scsi host checks
    host_warnings = run_host_checks()

    # scsi device and scsi command  checks
    dev_cmd_warnings = run_sdev_cmd_checks()

    # scsi_target checks
    target_warnings = run_target_checks()

    print ("\n### Summary:\n")
    print ("    Task                             Errors/Warnings")
    print ("    ------------------------------------------------")
    print ("    SCSI host checks:                {}". format(host_warnings))
    print ("    SCSI device, command checks:     {}". format(dev_cmd_warnings))
    print ("    SCSI target checks:              {}". format(target_warnings))

verbose = 0

if ( __name__ == '__main__'):

    import argparse
    parser =  argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", dest="Verbose", default = 0,
        action="count",
        help="verbose output")

    parser.add_argument("-p", "--proc", dest="proc_info", default = 0,
        action="store_true",
        help="show /proc/scsi/scsi style information")

    parser.add_argument("-d", "--devices", dest="devs", nargs='?',
                const="device_busy,sdev_state", default=0, metavar="FIELDS",
        help="show all devices")

    parser.add_argument("-s", "--hosts", dest="hosts", nargs='?',
                const="host_busy,host_failed", default=0, metavar="FIELDS",
        help="show all hosts")

    parser.add_argument("-T", "--Targets", dest="targets", nargs='?',
                const="target_busy", default=0, metavar="FIELDS",
        help="show all the scsi targets")

    parser.add_argument("-f", "--fcrports", dest="fcrports", nargs='?',
                const="port_state", default=0, metavar="FIELDS",
        help="show all the FC rports")

    parser.add_argument("-c", "--commands", dest="commands", nargs='?',
        const="jiffies_at_alloc", default=0, metavar="FIELDS",
        help="show SCSI commands")

    parser.add_argument("-q", "--queue", dest="queue", nargs='?',
        const="jiffies_at_alloc", default=0, metavar="FIELDS",
        help="show the IO requests, SCSI commands from request_queue")

    parser.add_argument("-r", "--requests", dest="requests", nargs='?',
        const="start_time,special", default=0, metavar="FIELDS",
        help="show requests to SCSI devices (INCOMPLETE)")

    parser.add_argument("-x", "--hex", dest="usehex", default = 0,
        action="store_true",
        help="display fields in hex")

    parser.add_argument("--check", dest="runcheck", default = 0,
        action="store_true",
        help="check for common SCSI issues")

    parser.add_argument("--time", dest="time", default = 0,
        action="store_true",
        help="display time and state information for  SCSI commands")

    parser.add_argument("--relative", dest="relative", nargs='?',
        const="jiffies", default=0,
        help="show fields relative to the given value/symbol.  Uses jiffies without argument")

    args = parser.parse_args()

    verbose = args.Verbose

    # Before doing anything else, check whether debuginfo is available!
    if (not scsi_debuginfo_OK()):
        sys.exit(0)

    if (args.runcheck):
        run_scsi_checks()

    if (args.proc_info):
        if (member_size("struct Scsi_Host", "host_busy") != -1):
            try:
                print_SCSI_devices()
            except crash.error as errval:
                print("print_SCSI_devices() failed: {}".format(errval))
        else:
            print("ERROR: command not supported without Scsi_Host->host_busy")

    if (args.commands or args.time):
        cmndcount = 0
        use_start_time_ns = member_size("struct request", "start_time") == -1
        for sdev in get_scsi_devices():
            cmndlist = get_scsi_commands(sdev)
            for cmnd in cmndlist:
                print_cmnd_header(cmnd)
                if (args.time):
                    if (cmnd.request):
                        display_command_time(cmnd, use_start_time_ns)
                    else:
                        print("\nWarning: cmnd.request is null for scsi_cmnd {:#x}. Skipping...".format(cmnd))

                if (args.commands):
                    display_fields(cmnd, args.commands, 
                               usehex=args.usehex,
                               relative=args.relative)
                else:
                    print("")
            cmndcount += len(cmndlist)
        if (not cmndcount):
            print("No SCSI commands found")

    if (args.devs):
        print_sdev_shost()

    if (args.targets):
        print_starget_shost()

    if (args.requests):
        display_requests(args.requests, args.usehex)

    if (args.queue):
        print_request_queue()

    if (args.fcrports):
        print_fcrports()

    if(args.hosts or not (args.runcheck or args.proc_info or args.devs or
       args.commands or args.requests or args.time or args.targets or
       args.queue or args.fcrports)):
        print_shost_info()
