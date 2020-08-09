Extracting various useful information from crash dump (crashinfo)
=================================================================

The crashinfo tool available in PyKdump framework can be used to quickly
fetch various details e.g. per-cpu tasks, errors and call traces in kernel
ring buffer, reason for panic, status of various workqueues, in-flight IOs,
etc.

Options provided by ‘crashinfo’::

    crash> crashinfo -h
    Usage: crashinfo [options]
    
    Options:
      -h, --help            show this help message and exit
      -v                    verbose output
      -q                    quiet mode - print warnings only
      --fast                Fast mode - do not run potentially slow tests
      --sysctl              Print sysctl info.
      --ext3                Print EXT3 info.
      --blkreq              Print Block I/O requests
      --blkdevs             Print Block Devices Info
      --filelock            Print filelock info.
      --stacksummary        Print stacks (bt) categorized summary.
      --findstacks=FINDSTACKS
                            Print stacks (bt) containing functions that match the provided pattern
      --checkstacks          Check stacks of all threads for corruption
      --decodesyscalls=DECODESYSCALLS
                            Decode Syscalls on the Stack
      --keventd_wq          Decode keventd_wq
      --kblockd_wq          Decode kblockd_workqueue
      --lws                 Print Locks Waitqueues and Semaphores
      --devmapper           Print DeviceMapper Tables
      --runq                Print Runqueus
      --semaphore=SEMA      Print 'struct semaphore' info
      --rwsemaphore=RWSEMA  Print 'struct rw_semaphore' info
      --mutex=MUTEX         Print Mutex info
      --umem                Print User-space Memory Usage
      --ls=LS               Emulate 'ls'. You can specify either dentry address or full pathname
      --workqueues          Print Workqueues - just for some kernels
      --radix_tree_element=root offset
                            Find and print a radix tree element
      --pci                 Print PCI Info
      --version             Print program version and exit
    
     ** Execution took   0.31s (real)   0.31s (CPU)
    crash>

**Note:** While we have tried to explain the usage of each of above options
with example outputs, it was hard to find a meaningful output for each of these
options from a single vmcore dump file. Thus we have used multiple vmcores
collected from different hang/panic scenarios while demonstrating the usage of
these options in below documentation.

* `Getting a summary of crash/panic`_
* `Print sysctl info (-\\-sysctl)`_
* `Print EXT3 info (-\\-ext3)`_
* `Print Block I/O requests (-\\-blkreq)`_
* `Print Block Devices Info (-\\-blkdevs)`_
* `Print stacks (bt) categorized summary (-\\-stacksummary)`_
* `Print stacks (bt) containing required functions (-\\-findstacks)`_
* `Check stacks of all threads for corruption (-\\-checkstacks)`_
* `Decode Syscalls on the Stack (-\\-decodesyscalls)`_
* `Decode keventd_wq (-\\-keventd_wq)`_
* `Decode kblockd_workqueue (-\\-kblockd_wq)`_
* `Print Locks Waitqueues and Semaphores (-\\-lws)`_
* `Decode the semaphores (-\\-semaphore, -\\-rwsemaphore)`_
* `Print DeviceMapper Tables (-\\-devmapper)`_
* `Print Runqueus (-\\-runq)`_
* `Print Mutex info (-\\-mutex)`_
* `Print User-space Memory Usage (-\\-umem)`_
* `Emulate 'ls' (-\\-ls)`_
* `Print Workqueues (-\\-workqueues)`_
* `Find and print a radix tree element (-\\-radix_tree_element)`_
* `Print PCI Info (-\\-pci)`_

Getting a summary of crash/panic
--------------------------------

By default, when crashinfo is invoked without any options, it prints some
vital statistics and runs a number of tests. As a result of running these
tests, it can print WARNING messages. These messages are usually (but not
always) followed by more details.

For example, below is the full output of crashinfo command without using any
of the above options::

    crash> crashinfo 
                             +==========================+
                             | *** Crashinfo v1.3.7 *** |
                             +==========================+
    
    +++WARNING+++ PARTIAL DUMP with size(vmcore) < 25% size(RAM)
          KERNEL: 3.10.0-693.17.1.el7.x86_64/vmlinux
        DUMPFILE: vmcore  [PARTIAL DUMP]
            CPUS: 4
            DATE: Sat Jan 19 23:35:05 2019
          UPTIME: 00:19:32
    LOAD AVERAGE: 20.56, 15.12, 7.54
           TASKS: 466
        NODENAME: system2.mpg.testlab.com
         RELEASE: 3.10.0-693.17.1.el7.x86_64
         VERSION: #1 SMP Sun Jan 14 10:36:03 EST 2018
         MACHINE: x86_64  (3492 Mhz)
          MEMORY: 7.8 GB
           PANIC: "SysRq : Trigger a crash"
    
                             +--------------------------+
    >------------------------| Per-cpu Stacks ('bt -a') |------------------------<
                             +--------------------------+
    
          -- CPU#0 -- 
    PID=0  CPU=0 CMD=swapper/0
      #0   crash_nmi_callback+0x31
      #1   nmi_handle+0x87
      #2   do_nmi+0x15d
      #3   end_repeat_nmi+0x1e
      #-1  intel_idle+0x0, 507 bytes of data
      #4   intel_idle+0xf4
      #5   cpuidle_enter_state+0x40
      #6   cpuidle_idle_call+0xd8
      #7   arch_cpu_idle+0xe
      #8   cpu_startup_entry+0x14a
      #9   rest_init+0x77
      #10  start_kernel+0x43e
      #11  x86_64_start_reservations+0x24
      #12  x86_64_start_kernel+0x14f
    
          -- CPU#1 -- 
    PID=6868  CPU=1 CMD=bash
      #0   machine_kexec+0x1fb
      #1   __crash_kexec+0x72
      #2   crash_kexec+0x30
      #3   oops_end+0xa8
      #4   no_context+0x280
      #5   __bad_area_nosemaphore+0x73
      #6   bad_area+0x43
      #7   __do_page_fault+0x3dc
      #8   do_page_fault+0x35
      #9   page_fault+0x28
      #-1  sysrq_handle_crash+0x0, 477 bytes of data
      #10  __handle_sysrq+0x107
      #11  write_sysrq_trigger+0x2f
      #12  proc_reg_write+0x3d
      #13  vfs_write+0xbd
      #14  sys_write+0x7f
      #15  system_call_fastpath+0x16, 477 bytes of data
    
          -- CPU#2 -- 
    PID=0  CPU=2 CMD=swapper/2
      #0   crash_nmi_callback+0x31
      #1   nmi_handle+0x87
      #2   do_nmi+0x15d
      #3   end_repeat_nmi+0x1e
      #-1  intel_idle+0x0, 507 bytes of data
      #4   intel_idle+0xf4
      #5   cpuidle_enter_state+0x40
      #6   cpuidle_idle_call+0xd8
      #7   arch_cpu_idle+0xe
      #8   cpu_startup_entry+0x14a
      #9   start_secondary+0x1d6
    
          -- CPU#3 -- 
    PID=0  CPU=3 CMD=swapper/3
      #0   crash_nmi_callback+0x31
      #1   nmi_handle+0x87
      #2   do_nmi+0x15d
      #3   end_repeat_nmi+0x1e
      #-1  intel_idle+0x0, 507 bytes of data
      #4   intel_idle+0xf4
      #5   cpuidle_enter_state+0x40
      #6   cpuidle_idle_call+0xd8
      #7   arch_cpu_idle+0xe
      #8   cpu_startup_entry+0x14a
      #9   start_secondary+0x1d6
    
                          +--------------------------------+
    >---------------------| How This Dump Has Been Created |---------------------<
                          +--------------------------------+
    
       *** Dump has been initiated: with sysrq ***
         programmatically (via sysrq-trigger)
    
                                   +---------------+
    >------------------------------| Tasks Summary |------------------------------<
                                   +---------------+
    
    Number of Threads That Ran Recently
    -----------------------------------
       last second      27
       last     5s      59
       last    60s      71
    
     ----- Total Numbers of Threads per State ------
      TASK_INTERRUPTIBLE                         439
      TASK_RUNNING                                 3
      TASK_UNINTERRUPTIBLE                        21
    
    +++WARNING+++ There are 8 threads running in their own namespaces
    	Use 'taskinfo --ns' to get more details
    
                               +-----------------------+
    >--------------------------| 5 Most Recent Threads |--------------------------<
                               +-----------------------+
    
      PID  CMD                Age    ARGS
    -----  --------------   ------  ----------------------------
     6868 bash                0 ms  (no user stack)
     7119 kworker/3:0         0 ms  (no user stack)
     4069 kworker/1:1H        0 ms  (no user stack)
      874 kworker/2:1H        0 ms  (no user stack)
        5 kworker/0:0H        0 ms  (no user stack)
    
                              +------------------------+
    >-------------------------| Memory Usage (kmem -i) |-------------------------<
                              +------------------------+
    
                     PAGES        TOTAL      PERCENTAGE
        TOTAL MEM  1947245       7.4 GB         ----
             FREE  1294938       4.9 GB   66% of TOTAL MEM
             USED   652307       2.5 GB   33% of TOTAL MEM
           SHARED   337257       1.3 GB   17% of TOTAL MEM
          BUFFERS    98331     384.1 MB    5% of TOTAL MEM
           CACHED   306536       1.2 GB   15% of TOTAL MEM
             SLAB   151205     590.6 MB    7% of TOTAL MEM
    
       TOTAL HUGE        0            0         ----
        HUGE FREE        0            0    0% of TOTAL HUGE
    
       TOTAL SWAP  1998847       7.6 GB         ----
        SWAP USED        0            0    0% of TOTAL SWAP
        SWAP FREE  1998847       7.6 GB  100% of TOTAL SWAP
    
     COMMIT LIMIT  2972469      11.3 GB         ----
        COMMITTED   372838       1.4 GB   12% of TOTAL LIMIT
    
     -- Request Queues Analysis:     Count=734, in_flight=540
     -- Requests from SLAB Analysis: Count=202, STARTED=120 WRITE=163
          -- Since started: newest    85.66s,  oldest   172.84s
    +++WARNING+++ there are outstanding blk_dev requests
    +++WARNING+++ 7 processes in UNINTERRUPTIBLE state are committing journal
    +++three oldest UNINTERRUPTIBLE threads
       ... ran 168s ago
    
    PID=11451  CPU=0 CMD=rm
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x239
      #3   io_schedule_timeout+0xad
      #4   io_schedule+0x18
      #5   bit_wait_io+0x11
      #6   __wait_on_bit+0x65
      #7   out_of_line_wait_on_bit+0x81
      #8   do_get_write_access+0x285
      #9   jbd2_journal_get_write_access+0x27
      #10  __ext4_journal_get_write_access+0x3b
      #11  ext4_reserve_inode_write+0x70
      #12  ext4_mark_inode_dirty+0x53
      #13  ext4_evict_inode+0x1f3
      #14  evict+0xa9
      #15  iput+0xf9
      #16  do_unlinkat+0x1ae
      #17  sys_unlinkat+0x1b
      #18  system_call_fastpath+0x16, 477 bytes of data
       ... ran 168s ago
    
    PID=11446  CPU=2 CMD=rm
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x239
      #3   io_schedule_timeout+0xad
      #4   io_schedule+0x18
      #5   bit_wait_io+0x11
      #6   __wait_on_bit+0x65
      #7   wait_on_page_bit+0x81
      #8   truncate_inode_pages_range+0x3bb
      #9   truncate_inode_pages_final+0x4f
      #10  ext4_evict_inode+0x11c
      #11  evict+0xa9
      #12  iput+0xf9
      #13  do_unlinkat+0x1ae
      #14  sys_unlinkat+0x1b
      #15  system_call_fastpath+0x16, 477 bytes of data
       ... ran 172s ago
    
    PID=11452  CPU=3 CMD=rm
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x239
      #3   io_schedule_timeout+0xad
      #4   io_schedule+0x18
      #5   bit_wait_io+0x11
      #6   __wait_on_bit+0x65
      #7   wait_on_page_bit+0x81
      #8   truncate_inode_pages_range+0x3bb
      #9   truncate_inode_pages_final+0x4f
      #10  ext4_evict_inode+0x11c
      #11  evict+0xa9
      #12  iput+0xf9
      #13  do_unlinkat+0x1ae
      #14  sys_unlinkat+0x1b
      #15  system_call_fastpath+0x16, 477 bytes of data
    
                           +-------------------------------+
    >----------------------| Scheduler Runqueues (per CPU) |----------------------<
                           +-------------------------------+
    
      ---+ CPU=0 <struct rq 0xffff88021ea18a00> ----
         | CURRENT TASK <struct task_struct 0xffffffff81a02480>, CMD=swapper/0
      ---+ CPU=1 <struct rq 0xffff88021ea98a00> ----
         | CURRENT TASK <struct task_struct 0xffff8800c5fc2f70>, CMD=bash
        7598 kworker/1:0 0.32910 
      ---+ CPU=2 <struct rq 0xffff88021eb18a00> ----
         | CURRENT TASK <struct task_struct 0xffff88017ce7af70>, CMD=swapper/2
      ---+ CPU=3 <struct rq 0xffff88021eb98a00> ----
         | CURRENT TASK <struct task_struct 0xffff88017ce7bf40>, CMD=swapper/3
    
                              +------------------------+
    >-------------------------| Network Status Summary |-------------------------<
                              +------------------------+
    
    TCP Connection Info
    -------------------
            ESTABLISHED      6
                 LISTEN      9
    			NAGLE disabled (TCP_NODELAY):     6
    			user_data set (NFS etc.):         1
    
    UDP Connection Info
    -------------------
      9 UDP sockets, 0 in ESTABLISHED
    
    Unix Connection Info
    ------------------------
            ESTABLISHED    244
                  CLOSE     48
                 LISTEN     59
    
    Raw sockets info
    --------------------
            ESTABLISHED      1
    
    Interfaces Info
    ---------------
      How long ago (in seconds) interfaces transmitted/received?
    	  Name        RX          TX
    	  ----    ----------    ---------
    	      lo       872.4         1171.8
    	  enp3s0       872.4            0.0
    	  virbr0       872.4          872.4
    	virbr0-nic       872.4         1126.1
    
    
    RSS_TOTAL=520628 pages, %mem=    5.1
    +++WARNING+++ Possible hang
    +++WARNING+++    Run 'hanginfo' to get more details
    
                                    +------------+
    >-------------------------------| Mounted FS |-------------------------------<
                                    +------------+
    
         MOUNT           SUPERBLK     TYPE   DEVNAME   DIRNAME
    ffff88017cd38180 ffff88017cd48800 rootfs rootfs    /         
    ffff88021e5d6300 ffff8802127db000 sysfs  sysfs     /sys      
    ffff88021e5d6480 ffff88017cd4b000 proc   proc      /proc     
    ffff88021e5d6600 ffff88017cfb0800 devtmpfs devtmpfs /dev      
    ffff88021e5d6780 ffff88021276c800 securityfs securityfs /sys/kernel/security
    ffff88021e5d6900 ffff8802127db800 tmpfs  tmpfs     /dev/shm  
    ffff88021e5d6a80 ffff88017cf21800 devpts devpts    /dev/pts  
    ffff88021e5d6c00 ffff8802127dc000 tmpfs  tmpfs     /run      
    ffff88021e5d6d80 ffff8802127dc800 tmpfs  tmpfs     /sys/fs/cgroup
    ffff88021e5d6f00 ffff8802127dd000 cgroup cgroup    /sys/fs/cgroup/systemd
    ffff88021e5d7080 ffff8802127dd800 pstore pstore    /sys/fs/pstore
    ffff88021e5d7200 ffff8802127df800 cgroup cgroup    /sys/fs/cgroup/net_cls,net_prio
    ffff88021e5d7380 ffff8802127df000 cgroup cgroup    /sys/fs/cgroup/devices
    ffff88021e5d7500 ffff8802127de800 cgroup cgroup    /sys/fs/cgroup/pids
    ffff88021e5d7680 ffff8802127de000 cgroup cgroup    /sys/fs/cgroup/perf_event
    ffff88021e5d7800 ffff880211c98000 cgroup cgroup    /sys/fs/cgroup/blkio
    ffff88021e5d7980 ffff880211c98800 cgroup cgroup    /sys/fs/cgroup/freezer
    ffff88021e5d7b00 ffff880211c99000 cgroup cgroup    /sys/fs/cgroup/cpuset
    ffff88021e5d7c80 ffff880211c99800 cgroup cgroup    /sys/fs/cgroup/cpu,cpuacct
    ffff88021e5d7e00 ffff880211c9a000 cgroup cgroup    /sys/fs/cgroup/memory
    ffff880211c54000 ffff880211c9a800 cgroup cgroup    /sys/fs/cgroup/hugetlb
    ffff880211c54180 ffff88017cfb3000 configfs configfs /sys/kernel/config
    ffff88020f79af00 ffff88020ef1c000 xfs    /dev/mapper/rhel00-root /         
    ffff88020f790180 ffff88020ef1c800 autofs systemd-1 /proc/sys/fs/binfmt_misc
    ffff8800355f5c80 ffff88017cd4d800 debugfs debugfs  /sys/kernel/debug
    ffff88020e39ca80 ffff88020f223800 hugetlbfs hugetlbfs /dev/hugepages
    ffff8800355f4d80 ffff88017cf23000 mqueue mqueue    /dev/mqueue
    ffff880211627380 ffff88021276e800 nfsd   nfsd      /proc/fs/nfsd
    ffff8800cd016780 ffff8800ce869800 xfs    /dev/mapper/rhel00-home /home     
    ffff880207a04480 ffff8800cf74f000 xfs    /dev/sda3 /boot     
    ffff880034509800 ffff8800c6fd7000 rpc_pipefs sunrpc /var/lib/nfs/rpc_pipefs
    ffff8801fe774480 ffff8800c5e96800 tmpfs  tmpfs     /run/user/42
    ffff8801fbac0f00 ffff8800c2825800 tmpfs  tmpfs     /run/user/0
    ffff8800c644be00 ffff8800c5fb1800 ext4   /dev/mapper/prodvg1-lvdata0 /prd_data0
    ffff8800c644a780 ffff8800c5fb0800 ext4   /dev/mapper/prodvg1-lvdata1 /prd_data1
    ffff8801fbac1500 ffff880034e97800 ext4   /dev/mapper/prodvg1-lvdata2 /prd_data2
    ffff8801f969b500 ffff8800c2824000 ext4   /dev/mapper/prodvg1-lvdata3 /prd_data3
    ffff8800c644a300 ffff8800c5fb4800 ext4   /dev/mapper/prodvg1-lvdata4 /prd_data4
    ffff8800c644bb00 ffff8800c5fb6800 ext4   /dev/mapper/prodvg2-prdbkplv0 /prd_bkp0 
    ffff8800c644b380 ffff8800cf28a000 ext4   /dev/mapper/prodvg2-prdbkplv1 /prd_bkp1 
    ffff8802002e8a80 ffff8800cf48c000 ext4   /dev/mapper/appvg-oraapps_vol /apps     
    ffff8800c2bb3c80 ffff8800c5fb6000 nfs4   172.25.0.11:/nfs_share1 /NFS-share1
    ffff8801f969be00 ffff8800c5fb6000 nfs4   172.25.0.11:/nfs_share2 /NFS-share2
    ffff88020ca45c80 ffff8800c5fb6000 nfs4   172.25.0.11:/nfs_share3 /NFS-share3
    
                           +-------------------------------+
    >----------------------| Last 40 lines of dmesg buffer |----------------------<
                           +-------------------------------+
    
    [ 1139.788068] qla2xxx [0000:01:00.0]-801c:0: Abort command issued nexus=0:0:2 --  1 2002.
    [ 1140.789026] qla2xxx [0000:01:00.0]-801c:0: Abort command issued nexus=0:0:2 --  1 2002.
    [ 1147.712623] qla2xxx [0000:01:00.1]-801c:7: Abort command issued nexus=7:0:1 --  1 2002.
    [ 1150.788760] qla2xxx [0000:01:00.0]-801c:0: Abort command issued nexus=0:0:10 --  1 2002.
    [ 1158.713019] qla2xxx [0000:01:00.1]-801c:7: Abort command issued nexus=7:0:10 --  1 2002.
    [ 1161.788834] qla2xxx [0000:01:00.0]-801c:0: Abort command issued nexus=0:0:16 --  1 2002.
    [ 1169.713389] qla2xxx [0000:01:00.1]-801c:7: Abort command issued nexus=7:0:11 --  1 2002.
    [ 1172.313862] SysRq : Trigger a crash
    [ 1172.313886] BUG: unable to handle kernel NULL pointer dereference at           (null)
    [ 1172.313923] IP: [<ffffffff81400816>] sysrq_handle_crash+0x16/0x20
    [ 1172.313942] PGD 80000000c2ac1067 PUD c2b49067 PMD 0 
    [ 1172.313958] Oops: 0002 [#1] SMP 
    [ 1172.313968] Modules linked in: rpcsec_gss_krb5 nfsv4 dns_resolver nfs fscache ext4 mbcache jbd2 xt_CHECKSUM ipt_MASQUERADE nf_nat_masquerade_ipv4 tun ip6t_rpfilter ipt_REJECT nf_reject_ipv4 ip6t_REJECT nf_reject_ipv6 xt_conntrack ip_set nfnetlink ebtable_nat ebtable_broute bridge stp llc ip6table_nat nf_conntrack_ipv6 nf_defrag_ipv6 nf_nat_ipv6 ip6table_mangle ip6table_security ip6table_raw iptable_nat nf_conntrack_ipv4 nf_defrag_ipv4 nf_nat_ipv4 nf_nat nf_conntrack iptable_mangle iptable_security iptable_raw ebtable_filter ebtables ip6table_filter ip6_tables iptable_filter ppdev mei_wdt intel_powerclamp coretemp intel_rapl kvm_intel kvm irqbypass dm_service_time crc32_pclmul ghash_clmulni_intel aesni_intel lrw pcspkr gf128mul glue_helper ablk_helper sg joydev snd_soc_rt5640 snd_soc_ssm4567 snd_soc_rl6231
    [ 1172.314228]  cryptd snd_hda_codec_hdmi snd_soc_core snd_compress regmap_i2c parport_pc parport snd_hda_codec_realtek snd_hda_codec_generic snd_hda_intel snd_hda_codec snd_hda_core snd_hwdep snd_seq snd_seq_device snd_pcm i2c_designware_platform i2c_designware_core acpi_pad mei_me mei tpm_infineon snd_soc_sst_acpi snd_soc_sst_match snd_timer shpchp snd soundcore nfsd auth_rpcgss nfs_acl lockd grace sunrpc dm_multipath ip_tables xfs libcrc32c sr_mod sd_mod cdrom i915 lpfc ahci libahci i2c_algo_bit drm_kms_helper qla2xxx crc32c_intel crc_t10dif libata serio_raw syscopyarea sysfillrect sysimgblt fb_sys_fops crct10dif_generic drm crct10dif_pclmul crct10dif_common r8169 scsi_transport_fc mii scsi_tgt sdhci_acpi iosf_mbi sdhci mmc_core video i2c_hid i2c_core dm_mirror dm_region_hash dm_log dm_mod
    [ 1172.314474] CPU: 1 PID: 6868 Comm: bash Not tainted 3.10.0-693.17.1.el7.x86_64 #1
    [ 1172.314492] Hardware name: Gigabyte Technology Co., Ltd. H97M-D3H/H97M-D3H, BIOS F6 04/21/2015
    [ 1172.314512] task: ffff8800c5fc2f70 ti: ffff8800c5db4000 task.ti: ffff8800c5db4000
    [ 1172.314532] RIP: 0010:[<ffffffff81400816>]  [<ffffffff81400816>] sysrq_handle_crash+0x16/0x20
    [ 1172.314568] RSP: 0018:ffff8800c5db7e58  EFLAGS: 00010246
    [ 1172.314581] RAX: 000000000000000f RBX: ffffffff81ac1140 RCX: 0000000000000000
    [ 1172.314598] RDX: 0000000000000000 RSI: ffff88021ea938b8 RDI: 0000000000000063
    [ 1172.314614] RBP: ffff8800c5db7e58 R08: ffffffff81d98dfc R09: ffffffff81ddb1cb
    [ 1172.314631] R10: 0000000000000ac4 R11: 0000000000000ac3 R12: 0000000000000063
    [ 1172.314647] R13: 0000000000000000 R14: 0000000000000004 R15: 0000000000000000
    [ 1172.314664] FS:  00007faf2543a740(0000) GS:ffff88021ea80000(0000) knlGS:0000000000000000
    [ 1172.314683] CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
    [ 1172.314705] CR2: 0000000000000000 CR3: 00000000c2b9e000 CR4: 00000000001607e0
    [ 1172.314732] DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000000000000
    [ 1172.314762] DR3: 0000000000000000 DR6: 00000000ffff0ff0 DR7: 0000000000000400
    [ 1172.314793] Call Trace:
    [ 1172.314808]  [<ffffffff81401037>] __handle_sysrq+0x107/0x170
    [ 1172.314835]  [<ffffffff814014af>] write_sysrq_trigger+0x2f/0x40
    [ 1172.314860]  [<ffffffff8127257d>] proc_reg_write+0x3d/0x80
    [ 1172.314886]  [<ffffffff81202ced>] vfs_write+0xbd/0x1e0
    [ 1172.314909]  [<ffffffff81203aff>] SyS_write+0x7f/0xe0
    [ 1172.314929]  [<ffffffff816b89fd>] system_call_fastpath+0x16/0x1b
    [ 1172.314943] Code: eb 9b 45 01 f4 45 39 65 34 75 e5 4c 89 ef e8 e2 f7 ff ff eb db 0f 1f 44 00 00 55 48 89 e5 c7 05 41 e4 62 00 01 00 00 00 0f ae f8 <c6> 04 25 00 00 00 00 01 5d c3 0f 1f 44 00 00 55 31 c0 c7 05 be 
    [ 1172.315057] RIP  [<ffffffff81400816>] sysrq_handle_crash+0x16/0x20
    [ 1172.315074]  RSP <ffff8800c5db7e58>
    [ 1172.315082] CR2: 0000000000000000
    
    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        PARTIAL DUMP with size(vmcore) < 25% size(RAM)
        There are 8 threads running in their own namespaces
    	Use 'taskinfo --ns' to get more details
        there are outstanding blk_dev requests
        7 processes in UNINTERRUPTIBLE state are committing journal
        Possible hang
           Run 'hanginfo' to get more details
    ------------------------------------------------------------------------------
    
     ** Execution took  12.72s (real)  10.41s (CPU), Child processes:   1.77s
    crash>

You can search for +++WARNING+++ pattern to be sure you did not miss any
warning.

Some tests rely on builtin crash commands that can potentially run for a long
time. For example, to check for fragmentation we do 'kmem -f'. On some of the
of vmcores it took more than 20 minutes to complete, even though the host was
fast. As in many cases we would like to obtain at least partial results fast,
there is a timeout mechanism for such commands. By default it is 2 min/command.
If we timeout, a warning message is printed::

    +++WARNING+++ <foreach bt> failed to complete within the timeout period
    of 120s

In this case you can increase the timeout by using an option
'-\\-timeout=seconds'. If you are in a hurry, you can use '-\\-fast' option.
This sets timeout to 15s and disables some potentially slow tests.

The tests check many conditions that are important when system seems to be
hung: e.g. load averages, memory fragmentation, outstanding block requests,
spinlocks hold, activity on networking cards and so on. Some tests are
heuristic - see below advanced options for more details. New tests are added
all the time, based on practical experience.

You can decrease verbosity by using '-q' (quiet) option, in this case only
warnings are printed. Using '-v' (verbose) makes crashinfo print additional
information.

Print sysctl info (-\\-sysctl)
------------------------------

To review the sysctl parameters and their values, use '-\\-sysctl' option::

    crash> crashinfo --sysctl|head -30
    abi.vsyscall32       1
    crypto.fips_enabled  0
    debug.exception-trace 1
    debug.kprobes-optimization 0
    debug.panic_on_rcu_stall 0
    dev.cdrom.autoclose  1
    dev.cdrom.autoeject  0
    dev.cdrom.check_media 0
    dev.cdrom.debug      0
    dev.cdrom.info       
    dev.cdrom.lock       1
    dev.hpet.max-user-freq 64
    dev.mac_hid.mouse_button2_keycode 97
    dev.mac_hid.mouse_button3_keycode 100
    dev.mac_hid.mouse_button_emulation 0
    dev.parport.default.spintime 500
    dev.parport.default.timeslice [0, 0]
    dev.raid.speed_limit_max 200000
    dev.raid.speed_limit_min 1000
    dev.scsi.logging_level 0
    fs.aio-max-nr        1048576
    fs.aio-nr            104
    fs.dentry-state      [70562, 52352, 45, 0, 0, '... 1 more elements']
    fs.dir-notify-enable 1
    fs.epoll.max_user_watches 1588305
    fs.file-max          767990
    fs.file-nr           [4320, 0, 0, 0, 767990, '... 1 more elements']
    fs.inode-nr          [61959, 415]
    fs.inode-state       [61959, 415, 0, 0, 0, '... 2 more elements']
    fs.inotify.max_queued_events 16384
    crash>

**Note:** Some sysctl settings are really programmatic, so that the get/set
value is computed rather than stored in a variable. We do not print such
values.

Print EXT3 info (-\\-ext3)
--------------------------

The older version of Linux kernels (e.g. the ones shipped with RHEL 5, used to
provide separate modules for ext3 and ext4 filesystem). For vmcore dumps
captured from such kernel, the '-\\-ext3' option can be used to quickly fetch
ext3 fs specific details. For example::

    crash> crashinfo --ext3
    
    0xffff81003fb920c0 0xffff81003f0aa000     ext3   /
       8030648    size of fs in 1KB blocks
          4096    file system block size
       5766864    free blocks
       5352352    free blocks for non-root
       2072576    inodes
       1980382    free inodes
    
    0xffff81003fb92ac0 0xffff81003ee90c00     ext3   /boot
        101086    size of fs in 1KB blocks
          1024    file system block size
         83438    free blocks
         78219    free blocks for non-root
         26104    inodes
         26069    free inodes
    
     ** Execution took   0.07s (real)   0.06s (CPU)
    crash>

**Note:** If the vmcore is generated from systems running more recent kernel
where ext4.ko module manages both ext3 and ext4 modules, then this option
would not be usable for it. We are working on adding the support for ext4
and other filesystems e.g. XFS.

Print Block I/O requests (-\\-blkreq)
-------------------------------------

The '-\\-blkreq' option prints a summary of IO requests from device's request
queue, blk_cpu_done list and SLAB::

    crash> crashinfo --blkreq
     -- Request Queues Analysis:     Count=734, in_flight=540
     -- Requests on blk_cpu_done:    Count=0
     -- Requests from SLAB Analysis: Count=202, STARTED=120 WRITE=163
          -- Since started: newest    85.66s,  oldest   172.84s
    
     ** Execution took   0.12s (real)   0.11s (CPU), Child processes:   0.03s
    crash>

Using verbose '-v' flag will display more detailed information e.g. name of
of the device, pointer to struct request, request age, timeout, etc::

    crash> crashinfo --blkreq -v
     -- Request Queues Analysis:     Count=734, in_flight=540
    dm-10            count=119  in_flight=116 
    dm-11            count=82   in_flight=31  
    dm-13            count=9    in_flight=9   
    dm-16            count=112  in_flight=104 
    dm-24            count=81   in_flight=31  
    dm-3             count=78   in_flight=78  
    dm-5             count=2    in_flight=1   
    dm-7             count=130  in_flight=31  
    dm-8             count=9    in_flight=9   
    dm-9             count=8    in_flight=8   
    sdaa             count=1    in_flight=32  
    sdab             count=1    in_flight=1   
    sdac             count=1    in_flight=0   
    sdad             count=1    in_flight=0   
    [...]
    sdy              count=1    in_flight=0   
    sdz              count=1    in_flight=1   
     -- Requests on blk_cpu_done:    Count=0
     -- Requests from SLAB Analysis: Count=202, STARTED=120 WRITE=163
          -- Since started: newest    85.66s,  oldest   172.84s
        <struct request 0xffff880095896a80>
    	disk_name=sdcu major=70
    	  started 85.66 s ago, times out in 30.00s
    	  <scsi_device 0xffff88020f126800>  <scsi_cmnd 0xffff8800958956c0>
    	  (jiffies - cmnd->jiffies_at_alloc)=85662
        <struct request 0xffff880095896c00>
    	disk_name=sdct major=70
    	  started 85.66 s ago, times out in 30.00s
    	  <scsi_device 0xffff88020f127000>  <scsi_cmnd 0xffff880095895880>
    	  (jiffies - cmnd->jiffies_at_alloc)=85662
        <struct request 0xffff880095896d80>
    	disk_name=sdcs major=70
    	  started 85.66 s ago, times out in 30.00s
    	  <scsi_device 0xffff88020f124800>  <scsi_cmnd 0xffff880095895a40>
    	  (jiffies - cmnd->jiffies_at_alloc)=85662
        <struct request 0xffff880095896000>
    	disk_name=sdcc major=69
    	  started 85.66 s ago, times out in 30.00s
    	  <scsi_device 0xffff88020f068800>  <scsi_cmnd 0xffff880095894a80>
    	  (jiffies - cmnd->jiffies_at_alloc)=85663
    [...]
        <struct request 0xffff880194704f00>
    	disk_name=dm-11 major=253
    	  started 172.84 s ago
        <struct request 0xffff880194705200>
    	disk_name=dm-11 major=253
    	  started 172.84 s ago
        <struct request 0xffff880194705380>
    	disk_name=dm-11 major=253
    	  started 172.84 s ago
      -- Summary of flags combinations
       1 WRITE|FAILFAST_TRANSPORT|META|PRIO|SOFTBARRIER|NOMERGE|STARTED|DONTPREP|IO_STAT
       1 WRITE|FAILFAST_TRANSPORT|SYNC|NOIDLE|FUA|SOFTBARRIER|NOMERGE|STARTED|DONTPREP|IO_STAT
       1 WRITE|SYNC|NOIDLE|SORTED|ELVPRIV|ALLOCED|IO_STAT|HASHED
       2 WRITE|SYNC|NOIDLE|FUA|SOFTBARRIER|STARTED|DONTPREP|ALLOCED|IO_STAT
       5 WRITE|SORTED|ELVPRIV|ALLOCED|IO_STAT|HASHED
       5 WRITE|SYNC|NOIDLE|SORTED|NOMERGE|ELVPRIV|ALLOCED|IO_STAT
      13 SORTED|SOFTBARRIER|DONTPREP|ELVPRIV|ALLOCED|IO_STAT
      18 WRITE|FAILFAST_TRANSPORT|SOFTBARRIER|NOMERGE|STARTED|DONTPREP|IO_STAT
      20 WRITE|SORTED|STARTED|DONTPREP|ELVPRIV|ALLOCED|IO_STAT
      25 WRITE|FAILFAST_TRANSPORT|SOFTBARRIER|NOMERGE|STARTED|DONTPREP|QUEUED|IO_STAT
      26 SORTED|SOFTBARRIER|STARTED|DONTPREP|QUEUED|ELVPRIV|ALLOCED|IO_STAT
      27 WRITE|FAILFAST_TRANSPORT|SOFTBARRIER|NOMERGE|IO_STAT
      27 WRITE|SORTED|NOMERGE|STARTED|DONTPREP|ELVPRIV|ALLOCED|IO_STAT
      31 WRITE|SORTED|NOMERGE|ELVPRIV|ALLOCED|IO_STAT
    
     ** Execution took   0.64s (real)   0.55s (CPU), Child processes:   0.01s
    crash>

Print Block Devices Info (-\\-blkdevs)
--------------------------------------

To get the list of block devices and corresponding gendisk structure pointer,
use '-\\-blkdevs'::

    crash> crashinfo --blkdevs
      8  sd               <struct gendisk 0xffff880211f9c000> fops=sd_fops
      9  md              
     11  sr               <struct gendisk 0xffff8800352a4c00> fops=sr_bdops
     65  sd               <struct gendisk 0xffff88020f738400> fops=sd_fops
     66  sd               <struct gendisk 0xffff8800354c7000> fops=sd_fops
     67  sd               <struct gendisk 0xffff8800351bb400> fops=sd_fops
     68  sd               <struct gendisk 0xffff880035325000> fops=sd_fops
     69  sd               <struct gendisk 0xffff8802107ff000> fops=sd_fops
     70  sd               <struct gendisk 0xffff880034c0dc00> fops=sd_fops
    135  sd              
    253  device-mapper    <struct gendisk 0xffff880035390000> fops=dm_blk_dops
    254  mdp             
    259  blkext          
    
     ** Execution took   0.05s (real)   0.05s (CPU)
    crash>

This option also supports verbose flag, which prints more information e.g.
name of the device partitions, pointer to block_device and request_queue struct,
name of the IO scheduler (elevator)::

    crash> crashinfo --blkdevs -v
      8  sd              
        0 sda   <block_device 0xffff88021633e3c0> <gendisk 0xffff880211f9c000>
           I/O Elevator=None
          2 sda2  <block_device 0xffff88017f82ba80> <gendisk 0xffff880211f9c000>
          3 sda3  <block_device 0xffff88017f829d40> <gendisk 0xffff880211f9c000>
          5 sda5  <block_device 0xffff880035a9e080> <gendisk 0xffff880211f9c000>
       16 sdb   <block_device 0xffff880216354340> <gendisk 0xffff880211f9e400>
           I/O Elevator=None
            <struct request_queue 0xffff8800352891a0> Len=32 in_flight=0 count=1
       32 sdc   <block_device 0xffff8802163489c0> <gendisk 0xffff8800356eb800>
           I/O Elevator=None
            <struct request_queue 0xffff880035289a70> Len=1 in_flight=0 count=1
    
       48 sdd   <block_device 0xffff880216354680> <gendisk 0xffff8802111e1800>
           I/O Elevator=None
            <struct request_queue 0xffff8800354e9a70> Len=1 in_flight=0 count=1
       64 sde   <block_device 0xffff880216348000> <gendisk 0xffff8800352a7000>
           I/O Elevator=None
            <struct request_queue 0xffff8800352808d0> Len=1 in_flight=0 count=1
       80 sdf   <block_device 0xffff880216348680> <gendisk 0xffff8800352a6c00>
           I/O Elevator=None
            <struct request_queue 0xffff88003528a340> Len=1 in_flight=0 count=1
       96 sdg   <block_device 0xffff88021633c000> <gendisk 0xffff88020fb55800>
           I/O Elevator=None
            <struct request_queue 0xffff88003528ac10> Len=1 in_flight=0 count=1
      112 sdh   <block_device 0xffff88021634aa40> <gendisk 0xffff8800356e9c00>
           I/O Elevator=None
            <struct request_queue 0xffff88003528b4e0> Len=10 in_flight=0 count=1
    [...]

Print stacks (bt) categorized summary (-\\-stacksummary)
--------------------------------------------------------

Quite often we need to better understand what kind of load do we have: what
are the name of commands, how many threads are running and what they are
doing. A traditional approach is to use 'foreach bt' and then browse it or
write AWK-scripts to reformat the output. Two options let us somewhat
facilitate the process::

      --stacksummary        Print stacks (bt) categorized summary.
      --findstacks=FINDSTACKS
                            Print stacks (bt) containing functions that
                            match the provided pattern

To programatically analyze the backtrace of processes and list the tasks found
to be in similar code paths use '-\\-stacksummary'.

When deciding whether two stacks look similar, we do not take into account the
offsets, only the names and order of functions. The stacks are reverse-sorted
by how many times they occur, so that those stacks that occur many times are
output first::

    crash> crashinfo --stacksummary
    
    ------- 143 stacks like that: ----------
      #0   __schedule
      #1   schedule
      #2   rescuer_thread
      #3   kthread
      #4   ret_from_fork
        youngest=935s(pid=7042), oldest=1172s(pid=28)
    
       ........................
         ata_sff                        1 times
         bioset                         41 times
         crypto                         1 times
         deferwq                        1 times
         ext4-rsv-conver                8 times
         ipv6_addrconf                  1 times
         kblockd                        1 times
         kdmflush                       39 times
         kintegrityd                    1 times
         kmpath_handlerd                1 times
         kmpath_rdacd                   1 times
         kmpathd                        1 times
         kpsmoused                      1 times
         kthrotld                       1 times
         kvm-irqfd-clean                1 times
         md                             1 times
         netns                          1 times
         nfsiod                         1 times
         rpciod                         1 times
         scsi_tmf_0                     1 times
         scsi_tmf_1                     1 times
         scsi_tmf_2                     1 times
         scsi_tmf_3                     1 times
         scsi_tmf_4                     1 times
         scsi_tmf_5                     1 times
         scsi_tmf_6                     1 times
         scsi_tmf_7                     1 times
         scsi_tmf_8                     1 times
    [...]

Adding '-v' will print the PIDs for each stack.

Print stacks (bt) containing required functions (-\\-findstacks)
----------------------------------------------------------------

To find the tasks with matching function calls on it's stack, use
'-\\-findstacks'.

As seen in the following output, there is one process with
'qla2x00_eh_wait_on_command' function call on it's stack. Similarly there
were two processes found to be having 'jbd2_journal_commit_transaction'
function on it's stack::

    crash> crashinfo --findstacks=qla2x00_eh_wait_on_command
    
    PID=308  CPU=2 CMD=scsi_eh_0
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x174
      #3   msleep+0x2f
      #4   qla2x00_eh_wait_on_command+0x45
      #5   qla2xxx_eh_abort+0x2ee
      #6   scsi_send_eh_cmnd+0x1fe
      #7   scsi_eh_tur+0x37
      #8   scsi_eh_test_devices+0x130
      #9   scsi_error_handler+0x66e
      #10  kthread+0xcf
      #11  ret_from_fork+0x58
    
     ** Execution took   0.02s (real)   0.02s (CPU)
    crash>

    crash> crashinfo --findstacks=jbd2_journal_commit_transaction
    
    PID=7015  CPU=0 CMD=jbd2/dm-30-8
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x239
      #3   io_schedule_timeout+0xad
      #4   io_schedule+0x18
      #5   bit_wait_io+0x11
      #6   __wait_on_bit+0x65
      #7   out_of_line_wait_on_bit+0x81
      #8   __wait_on_buffer+0x2a
      #9   jbd2_journal_commit_transaction+0x176f
      #10  kjournald2+0xc9
      #11  kthread+0xcf
      #12  ret_from_fork+0x58
    
    PID=7018  CPU=2 CMD=jbd2/dm-31-8
      #0   __schedule+0x3dc
      #1   schedule+0x29
      #2   schedule_timeout+0x239
      #3   io_schedule_timeout+0xad
      #4   io_schedule+0x18
      #5   bit_wait_io+0x11
      #6   __wait_on_bit+0x65
      #7   wait_on_page_bit+0x81
      #8   __filemap_fdatawait_range+0x111
      #9   filemap_fdatawait_range+0x14
      #10  filemap_fdatawait+0x27
      #11  jbd2_journal_commit_transaction+0xa81
      #12  kjournald2+0xc9
      #13  kthread+0xcf
      #14  ret_from_fork+0x58
    [...]

As 'foreach bt' command is very expensive, we cache the results for non-live
kernels, so that if you want to do '-\\-find' with several different patterns,
the execution will be slow only the first time.

Check stacks of all threads for corruption (-\\-checkstacks)
------------------------------------------------------------
<WIP>

Decode Syscalls on the Stack (-\\-decodesyscalls)
-------------------------------------------------

The '-\\-decodesyscalls' option lets you decode the arguments passed to system
calls. As arguments originate from userspace, it is not always possible to
decode them (as some pages might not be present in vmcore). You can specify
either PID or system call name. For example::

    crash> bt
    PID: 3060   TASK: ffff88200f118040  CPU: 33  COMMAND: "rsyslogd"
     #0 [ffff881fe4a837b8] schedule at ffffffff81558d6a
     #1 [ffff881fe4a838a0] schedule_hrtimeout_range at ffffffff8155b3a8
     #2 [ffff881fe4a83940] poll_schedule_timeout at ffffffff811b9329
     #3 [ffff881fe4a83960] do_select at ffffffff811b9c45
     #4 [ffff881fe4a83d40] core_sys_select at ffffffff811ba87a
     #5 [ffff881fe4a83ee0] sys_select at ffffffff811bac07
     #6 [ffff881fe4a83f50] system_call_fastpath at ffffffff81564357
        RIP: 00007f5926abb633  RSP: 00007ffe36f7b3c0  RFLAGS: 00010217
        RAX: 0000000000000017  RBX: 000055775aebef54  RCX: 00007f5926abb633
        RDX: 0000000000000000  RSI: 0000000000000000  RDI: 0000000000000001
        RBP: 0000000000015180   R8: 00007ffe36f7b3c0   R9: 0000000000000bf4
        R10: 0000000000000000  R11: 0000000000000293  R12: 000000000000001e
        R13: 0000000000000000  R14: 0000000000000000  R15: 0000000000000001
        ORIG_RAX: 0000000000000017  CS: 0033  SS: 002b

    crash> crashinfo --decodesyscalls 3060
    
    PID=3060  CPU=33 CMD=rsyslogd
      #0   schedule+0x45a
      #1   schedule_hrtimeout_range+0xc8
      #2   poll_schedule_timeout+0x39
      #3   do_select+0x5d5
      #4   core_sys_select+0x18a
      #5   sys_select+0x47
      #6   system_call_fastpath+0x35, 477 bytes of data
        ....... Decoding Syscall Args .......
        sys_select (1
    	(fd_set *) 0x0
    	(fd_set *) 0x0
    	(fd_set *) 0x0
    	(struct timeval *) 0x7ffe36f7b3c0)
       nfds=1
       timeout=86400 s, 0 usec
    
     ** Execution took   0.05s (real)   0.05s (CPU)
    crash>

Decode keventd_wq (-\\-keventd_wq)
----------------------------------

To view the worklist items pending in the work queue of each cpu, use
'-\\-keventd_wq'::

    crash> crashinfo --keventd_wq
     ----- CPU  0 <struct cpu_workqueue_struct 0xffff88009e21ba40>
    	    worklist:
     ----- CPU  1 <struct cpu_workqueue_struct 0xffff88009e25ba40>
    	    worklist:
    	        <struct work_struct 0xffff88009e257a40> func=<cache_reap>
    	        <struct work_struct 0xffff88009e257960> func=<vmstat_update>
     ----- CPU  2 <struct cpu_workqueue_struct 0xffff88009e29ba40>
    	    worklist:
    	        <struct work_struct 0xffff88009e297a40> func=<cache_reap>
    	        <struct work_struct 0xffff88009e297960> func=<vmstat_update>
     ----- CPU  3 <struct cpu_workqueue_struct 0xffff88009e2dba40>
    	    worklist:
    	        <struct work_struct 0xffff887103510108> func=<flush_to_ldisc>
    	        <struct work_struct 0xffff88009e2d7960> func=<vmstat_update>
    	        <struct work_struct 0xffff88009e2d7a40> func=<cache_reap>
     ----- CPU  4 <struct cpu_workqueue_struct 0xffff88009e31ba40>
    	    worklist:
     ----- CPU  5 <struct cpu_workqueue_struct 0xffff88009e35ba40>
    	    worklist:
    [...]

Decode kblockd_workqueue (-\\-kblockd_wq)
-----------------------------------------

To view the worklist items pending in the kblockd_workqueue of each cpu, use
'-\\-kblockd_wq'::

    crash> crashinfo --kblockd_wq
     ----- CPU  0 <struct cpu_workqueue_struct 0xffff88009e21c200>
    	    worklist:
     ----- CPU  1 <struct cpu_workqueue_struct 0xffff88009e25c200>
    	    worklist:
     ----- CPU  2 <struct cpu_workqueue_struct 0xffff88009e29c200>
    	    worklist:
     ----- CPU  3 <struct cpu_workqueue_struct 0xffff88009e2dc200>
    	    worklist:
     ----- CPU  4 <struct cpu_workqueue_struct 0xffff88009e31c200>
    	    worklist:
     ----- CPU  5 <struct cpu_workqueue_struct 0xffff88009e35c200>
    	    worklist:
     ----- CPU  6 <struct cpu_workqueue_struct 0xffff88009e39c200>
    	    worklist:
    	        <struct work_struct 0xffff8820049cbba8> func=<cfq_kick_queue>
    	        <struct work_struct 0xffff8820098a5ba8> func=<cfq_kick_queue>
    	        <struct work_struct 0xffff8820070f73a8> func=<cfq_kick_queue>
    	        <struct work_struct 0xffff882009c0cba8> func=<cfq_kick_queue>
     ----- CPU  7 <struct cpu_workqueue_struct 0xffff88009e3dc200>
    	    worklist:
     ----- CPU  8 <struct cpu_workqueue_struct 0xffff88009e41c200>
    	    worklist:
     ----- CPU  9 <struct cpu_workqueue_struct 0xffff88009e45c200>
    	    worklist:
     ----- CPU  10 <struct cpu_workqueue_struct 0xffff8820b0c1c200>
    	    worklist:
    	        <struct work_struct 0xffff880d91fa6ba8> func=<cfq_kick_queue>
    	        <struct work_struct 0xffff88585d29dba8> func=<cfq_kick_queue>
    [...]

Print Locks Waitqueues and Semaphores (-\\-lws)
-----------------------------------------------

We can print all globally-declared structures that are in use using the
following approach:

- obtain a list of all symbols that have 'data' type
- obtain information for each of them and check whether it has a needed type
- print those structures that are being used at this moment::

    crash> crashinfo --lws
     -- rw_semaphores with count > 0 --
         uts_sem <atomic_long_t 0xffffffff81a383a0>
         umhelper_sem <atomic_long_t 0xffffffff81a3b020>
         all_cpu_access_lock <atomic_long_t 0xffffffff81a73080>
         trace_event_sem <atomic_long_t 0xffffffff81a73480>
         shrinker_rwsem <atomic_long_t 0xffffffff81a78460>
         namespace_sem <atomic_long_t 0xffffffff81a8a300>
         configfs_rename_sem <atomic_long_t 0xffffffff81a945c0>
         key_types_sem <atomic_long_t 0xffffffff81a98160>
         keyring_serialise_link_sem <atomic_long_t 0xffffffff81a981a0>
         crypto_alg_sem <atomic_long_t 0xffffffff81a9f520>
         alg_types_sem <atomic_long_t 0xffffffff81aaf0e0>
         asymmetric_key_parsers_sem <atomic_long_t 0xffffffff81aaf640>
         pci_bus_sem <atomic_long_t 0xffffffff81ab4ba0>
         bus_type_sem <atomic_long_t 0xffffffff81ab9070>
         pcmcia_socket_list_rwsem <atomic_long_t 0xffffffff81ad2560>
         ehci_cf_port_reset_rwsem <atomic_long_t 0xffffffff81ad2900>
         minor_rwsem <atomic_long_t 0xffffffff81ad2be0>
         companions_rwsem <atomic_long_t 0xffffffff81ad3c80>
         cpufreq_rwsem <atomic_long_t 0xffffffff81ad9560>
         leds_list_lock <atomic_long_t 0xffffffff81ada6a0>
         triggers_list_lock <atomic_long_t 0xffffffff81ada760>
         dquirks_rwsem <atomic_long_t 0xffffffff81aded00>
         dmar_global_lock <atomic_long_t 0xffffffff81adfc40>
         cb_lock <atomic_long_t 0xffffffff81ae7580>
         snd_ioctl_rwsem <atomic_long_t 0xffffffffc0470120>
         snd_pcm_link_rwsem <atomic_long_t 0xffffffffc0746140>
         fscache_addremove_sem <atomic_long_t 0xffffffffc0b81040>
     -- rw_semaphores with count <= 0 --
     -- Non-empty wait_queue_head --
         mce_chrdev_wait
    	 PID: 5779   TASK: ffff8800c6f4cf10  CPU: 2   COMMAND: "mcelog"
         kauditd_wait
    	 PID: 112    TASK: ffff8802126e3f40  CPU: 3   COMMAND: "kauditd"
         ksm_thread_wait
    	 PID: 41     TASK: ffff880212658000  CPU: 3   COMMAND: "ksmd"
         khugepaged_wait
    	 PID: 42     TASK: ffff880212658fd0  CPU: 1   COMMAND: "khugepaged"
         random_write_wait
    	 PID: 5702   TASK: ffff88020f0c5ee0  CPU: 3   COMMAND: "rngd"
         random_read_wait
    	 PID: 5702   TASK: ffff88020f0c5ee0  CPU: 3   COMMAND: "rngd"
     -- Non-empty struct work_struct --
    
     ** Execution took 192.23s (real) 191.60s (CPU)
    crash>

Decode the semaphores (-\\-semaphore, -\\-rwsemaphore)
------------------------------------------------------

The semaphores shown in '-\\-lws' output or the ones retrieved through manual
analysis can be decoded further using these options::

    crash> crashinfo --rwsemaphore=0xffffffff81ad2be0
    <struct rw_semaphore 0xffffffff81ad2be0>
        Write owner of this rw_semaphore: pid=0 cmd=
    
     ** Execution took   0.02s (real)   0.02s (CPU)
    crash> crashinfo --rwsemaphore=0xffffffff81ad3c80
    <struct rw_semaphore 0xffffffff81ad3c80>
       Reader is the owner
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash> crashinfo --rwsemaphore=0xffffffff81ad9560
    <struct rw_semaphore 0xffffffff81ad9560>
       Reader is the owner
    
     ** Execution took   0.01s (real)   0.01s (CPU)
    crash> crashinfo --rwsemaphore=0xffffffff81aded00
    <struct rw_semaphore 0xffffffff81aded00>
       Reader is the owner
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash> crashinfo --rwsemaphore=0xffffffffc0470120
    <struct rw_semaphore 0xffffffffc0470120>
       Reader is the owner
    
     ** Execution took   0.04s (real)   0.04s (CPU)
     crash> 
     crash> crashinfo --rwsemaphore=0xffff88256f8d80b0
     <struct rw_semaphore 0xffff88256f8d80b0>
         Owner of this rw_semaphore: pid=13318 cmd=kworker/5:5
     crash> 

Print DeviceMapper Tables (-\\-devmapper)
-----------------------------------------

We can quickly get the list of device-mapper objects (e.g. lvm volumes,
multipath device maps, mpath partitions, etc.) present on the system by
using '-\\-devmapper' option::

    crash> crashinfo --devmapper
     ========== Devicemapper devices ============
    rhel00-root                               minor=0
    rhel-swap                                 minor=1
    rhel00-swap                               minor=2
    mpathi                                    minor=3
    mpathh                                    minor=4
    mpathb                                    minor=5
    mpathg                                    minor=6
    mpathd                                    minor=7
    mpathj                                    minor=8
    mpathf                                    minor=9
    mpathe                                    minor=10
    mpatha                                    minor=11
    mpathr                                    minor=12
    mpathn                                    minor=13
    mpathp                                    minor=14
    mpathk                                    minor=15
    mpathc                                    minor=16
    mpathl                                    minor=17
    mpathy                                    minor=18
    mpathx                                    minor=19
    mpathw                                    minor=20
    mpathv                                    minor=21
    mpathz                                    minor=22
    mpatht                                    minor=23
    mpathm                                    minor=24
    mpathu                                    minor=25
    mpatho                                    minor=26
    mpathq                                    minor=27
    mpaths                                    minor=28
    appvg-oraapps_vol                         minor=29
    prodvg1-lvdata0                           minor=30
    prodvg1-lvdata1                           minor=31
    prodvg1-lvdata2                           minor=32
    prodvg1-lvdata3                           minor=33
    prodvg1-lvdata4                           minor=34
    prodvg2-prdbkplv0                         minor=35
    prodvg2-prdbkplv1                         minor=36
    rhel00-home                               minor=37
    rhel-root                                 minor=38
    
     ** Execution took   0.50s (real)   0.49s (CPU)
    crash>

To get even more detailed information about the dm devices, use the
:doc:`dmshow <dmshow>` program available in PyKdump.

Print Runqueus (-\\-runq)
-------------------------

To review per CPU scheduler runqueues, use '-\\-runq'::

    crash> crashinfo --runq
    
                           +-------------------------------+
    >----------------------| Scheduler Runqueues (per CPU) |----------------------<
                           +-------------------------------+
    
      ---+ CPU=0 <struct rq 0xffff88021ea18a00> ----
         | CURRENT TASK <struct task_struct 0xffffffff81a02480>, CMD=swapper/0
      ---+ CPU=1 <struct rq 0xffff88021ea98a00> ----
         | CURRENT TASK <struct task_struct 0xffff8800c5fc2f70>, CMD=bash
        7598 kworker/1:0 0.32910 
      ---+ CPU=2 <struct rq 0xffff88021eb18a00> ----
         | CURRENT TASK <struct task_struct 0xffff88017ce7af70>, CMD=swapper/2
      ---+ CPU=3 <struct rq 0xffff88021eb98a00> ----
         | CURRENT TASK <struct task_struct 0xffff88017ce7bf40>, CMD=swapper/3
    
     ** Execution took   0.02s (real)   0.02s (CPU)
    crash>

Print Mutex info (-\\-mutex)
----------------------------

For the vmcore dumps collected for system hang issues, it is often observed
that processes are stuck waiting for a mutex lock. In such cases it is
important to find the list of all the processes which stuck waiting on the
exact same lock. This option can be used to quickly process this information.

For example, following output shows a large number of 'sg_inq' tasks stuck
waiting for same mutex lock '0xffff97c3af39e420'::

    crash> crashinfo --mutex=0xffff97c3af39e420
     ---<struct mutex 0xffff97c3af39e420>----
        Waiters on this mutex:
    	   42880  sg_inq
    	   98757  sg_inq
    	  155867  sg_inq
    	  211765  sg_inq
    	  270270  sg_inq
    	  329194  sg_inq
    	  386361  sg_inq
    	  442349  sg_inq
    	  498571  sg_inq
    	  554807  sg_inq
    	  614293  sg_inq
    	  673268  sg_inq
    	  730272  sg_inq
    	  786294  sg_inq
    	  842416  sg_inq
    	  898817  sg_inq
    	  957496  sg_inq
    	 1017341  sg_inq
    	 1073456  sg_inq
    	 1130232  sg_inq
    	 1186270  sg_inq
    	 1242064  sg_inq
    	 1301493  sg_inq
    	 1360452  sg_inq
    	 1416538  sg_inq
    	 1473322  sg_inq
    	 1529109  sg_inq
    	 1584889  sg_inq
    	 1643374  sg_inq
    	 1702954  sg_inq
    	 1759218  sg_inq
    	 1815003  sg_inq
    	 1882704  sg_inq
    	 3029625  sg_inq
    	 3088116  sg_inq
    	 3147976  sg_inq
    	 3204737  sg_inq
    	 3260672  sg_inq
    	 3316550  sg_inq
    	 3372448  sg_inq
    	 3430953  sg_inq
    	 3490727  sg_inq
    	 3547342  sg_inq
    	 3603206  sg_inq
    	 3660184  sg_inq
    	 3716298  sg_inq
    	 3774917  sg_inq
    	 3834835  sg_inq
    	 3891401  sg_inq
    	 3947334  sg_inq
    	 4004083  sg_inq
    	 4060990  sg_inq
    	 4119986  sg_inq
    	 4179095  sg_inq

Print User-space Memory Usage (-\\-umem)
----------------------------------------

To get the User-space Memory Usage ('-\\-umem')::

    crash> crashinfo --umem
    RSS_TOTAL=520628 pages, %mem=    5.1
    
     ** Execution took   0.11s (real)   0.08s (CPU), Child processes:   0.06s
    crash>

Emulate 'ls' (-\\-ls)
---------------------

This option is useful to get a long listing of files, similar to the 'ls -l'
output on shell prompt.

For example, below process is having various files open in it's name-space.
The '-\\-ls' option can be used to get more details of these files::

    crash> files
    PID: 3060   TASK: ffff88200f118040  CPU: 33  COMMAND: "rsyslogd"
    ROOT: /    CWD: /
     FD       FILE            DENTRY           INODE       TYPE PATH
      0 ffff884011fd72c0 ffff883ffe854240 ffff884005a4b6c8 SOCK 
      1 ffff886b0b2b1ec0 ffff884109bb4740 ffff885a5ed87100 REG  /var/log/messages
      2 ffff886ad3f355c0 ffff885ff9ecbbc0 ffff884109bf1100 REG  /var/log/secure
      3 ffff88400b9e6a80 ffff883ffe854300 ffff88401380ad48 REG  /proc/kmsg
      4 ffff886610ae4b80 ffff8866b017d8c0 ffff8840033ea4e8 REG  /var/log/cron
      5 ffff885ffc3516c0 ffff886005add500 ffff88600ee1c148 SOCK 
      6 ffff884b9203cec0 ffff884c7c4e7080 ffff884a8906c8d0 REG  /var/log/errlog
      7 ffff885ef34a4e80 ffff8840139a93c0 ffff88601154bd48 CHR  /dev/ttyS1
      8 ffff886eb1f12cc0 ffff8880043e2500 ffff8861ad09d100 REG  /var/log/maillog
    crash>
    
    crash> crashinfo --ls=/var/log/secure
     -rw-------     0     0   15855596 2020-07-25 07:05 /var/log/secure
    
     ** Execution took   0.01s (real)   0.02s (CPU)
    crash> crashinfo --ls=ffff885ff9ecbbc0
     -rw-------     0     0   15855596 2020-07-25 07:05 secure
    
     ** Execution took   0.01s (real)   0.02s (CPU)
    crash>

Print Workqueues (-\\-workqueues)
---------------------------------

To find the list of active work-queues and it's details e.g. number of associated
kworker threads, their pointers, use '-\\-workqueues'::

    crash> crashinfo --workqueues
     -----------------------WorkQueues - Active only-----------------------
       --------writeback--------   <struct workqueue_struct 0xffff88021e5e4200>
      <struct pool_workqueue 0xffff88021eabea00> active=2 delayed=0
       <struct worker_pool 0xffff88017ce63800> nr_workers=7 nr_idle=5
          <struct worker 0xffff88020f6dd480>  kworker/u8:1 bdi_writeback_workfn
           -- Decoding work for func=bdi_writeback_workfn
              <struct bdi_writeback 0xffff88020bf50bb8>
              <struct backing_dev_info 0xffff88020bf50a60>
          <struct worker 0xffff880206a40680>  kworker/u8:4 bdi_writeback_workfn
           -- Decoding work for func=bdi_writeback_workfn
              <struct bdi_writeback 0xffff88020ca92ef8>
              <struct backing_dev_info 0xffff88020ca92da0>
       ---------events----------   <struct workqueue_struct 0xffff88017fc06c00>
    
     ** Execution took   1.41s (real)   1.32s (CPU)
    crash>

Find and print a radix tree element (-\\-radix_tree_element)
------------------------------------------------------------

When accessing a large file, the page cache may become filled with so many of
the file’s pages that sequentially scanning all of them would be too
time consuming. In order to perform page cache lookup efficiently, Linux kernel
makes use of a large set of search trees, one for each address_space object.

The page_tree field of an address_space object is the root of a radix tree,
which contains pointers to the descriptors of the owner’s pages. Given a page
index denoting the position of the page inside the owner’s disk image, the
kernel can perform a very fast lookup operation in order to determine whether
the required page is already included in the page cache. When looking up the
page, the kernel interprets the index as a path inside the radix tree and
quickly reaches the position where the page descriptor is—or should be—stored.

We can use the '-\\-radix_tree_element' option to view the elements at various
offsets in such radix trees.

For example, in the following output we can first get the pointer for
'radix_tree_root' struct used for file - '/var/log/messages' and then check
the elements at different offsets in the radix tree::

    PID: 5723   TASK: ffff880208a94f10  CPU: 0   COMMAND: "in:imjournal"
    ROOT: /    CWD: /
     FD       FILE            DENTRY           INODE       TYPE PATH
      0 ffff8802116cdb00 ffff88017f827240 ffff88021eaa4850 CHR  /dev/null
      1 ffff880209fbc900 ffff88017f827240 ffff88021eaa4850 CHR  /dev/null
      2 ffff880209fbc900 ffff88017f827240 ffff88021eaa4850 CHR  /dev/null
      3 ffff8800345fab00 ffff880213e3fe40 ffff88020c33f230 SOCK UNIX
      4 ffff880034d93600 ffff880216047840 ffff880034a8f990 REG  /var/log/messages
      5 ffff880207f5fc00 ffff880035843780 ffff880035d3c850 REG  /run/log/journal/cfed3488b827492e8ed80518fe12223a/system.journal
      6 ffff8800cd0d5400 ffff8802160c1180 ffff880034a8ea90 REG  /var/log/secure
      7 ffff88020be44300 ffff8800c8db30c0 ffff88017fbee060 UNKN inotify
    
    crash> p ((struct file *) 0xffff880034d93600)->f_mapping
    $11 = (struct address_space *) 0xffff880034a8fae0
    
    crash> p &((struct address_space *) 0xffff880034a8fae0)->page_tree
    $13 = (struct radix_tree_root *) 0xffff880034a8fae8

The first argument to '-\\-radix_tree_element' option is pointer to the
'radix_tree_root'struct  and second argument is numeric offset::

    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 0
      node=0xffffea0008253980, slot=0xffffea0008253980
    
     ** Execution took   0.10s (real)   0.03s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 1
      node=0xffffea0008253a40, slot=0xffffea0008253a40
    
     ** Execution took   0.04s (real)   0.05s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 2
      node=0xffffea0008253a00, slot=0xffffea0008253a00
    
     ** Execution took   0.04s (real)   0.04s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 3
      node=0xffffea0008251d40, slot=0xffffea0008251d40
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 4
      node=0xffffea0008251d00, slot=0xffffea0008251d00
    
     ** Execution took   0.02s (real)   0.02s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 5
      node=0xffffea000825efc0, slot=0xffffea000825efc0
    
     ** Execution took   0.04s (real)   0.03s (CPU)
    crash>
    crash> crashinfo --radix_tree_element=0xffff880034a8fae8 6
      node=0xffffea0008253bc0, slot=0xffffea0008253bc0
    crash>

Print PCI Info (-\\-pci)
------------------------

We can use the '-\\-pci' option to print the PCI devices information e.g.
PCI ID, iomem_resource and ioport_resource associated with the device::

    crash> crashinfo --pci
    00:00.0 0600: 8086:0c00 (rev 06)
    00:01.0 0604: 8086:0c01 (rev 06)
    00:02.0 0300: 8086:041e (rev 06)
    00:03.0 0403: 8086:0c0c (rev 06)
    00:14.0 0c03: 8086:8cb1 (rev 00)
    00:16.0 0780: 8086:8cba (rev 00)
    00:1a.0 0c03: 8086:8cad (rev 00)
    00:1b.0 0403: 8086:8ca0 (rev 00)
    00:1c.0 0604: 8086:8c90 (rev d0)
    00:1c.2 0604: 8086:8c94 (rev d0)
    00:1c.3 0604: 8086:8c96 (rev d0)
    00:1c.4 0604: 8086:8c98 (rev d0)
    00:1d.0 0c03: 8086:8ca6 (rev 00)
    00:1f.0 0601: 8086:8cc6 (rev 00)
    00:1f.2 0106: 8086:8c82 (rev 00)
    00:1f.3 0c05: 8086:8ca2 (rev 00)
    01:00.0 0c04: 1077:2432 (rev 03)
    01:00.1 0c04: 1077:2432 (rev 03)
    03:00.0 0200: 10ec:8168 (rev 0c)
    04:00.0 0604: 8086:244e (rev 41)
    06:00.0 0c04: 10df:fe00 (rev 02)
    06:00.1 0c04: 10df:fe00 (rev 02)
    
    ============================iomem_resource============================
    00000000-00000fff : reserved
    00001000-0009d7ff : System RAM
    0009d800-0009ffff : reserved
    000a0000-000bffff : PCI Bus 0000:00
    000c0000-000cfdff : Video ROM
    000d0000-000d0fff : Adapter ROM
    000d1000-000d11ff : Adapter ROM
    000d1800-000d1fff : Adapter ROM
    000d4000-000d7fff : PCI Bus 0000:00
    000d8000-000dbfff : PCI Bus 0000:00
    000dc000-000dffff : PCI Bus 0000:00
    000e0000-000fffff : reserved
      000e0000-000e3fff : PCI Bus 0000:00
      000e4000-000e7fff : PCI Bus 0000:00
      000f0000-000fffff : System ROM
    00100000-c0286fff : System RAM
      01000000-016c12fe : Kernel code
      016c12ff-01b3323f : Kernel data
      01cfe000-01ff9fff : Kernel bss
      2a000000-340fffff : Crash kernel
    c0287000-c028dfff : ACPI Non-volatile Storage
    c028e000-c0bfafff : System RAM
    c0bfb000-c0eb2fff : reserved
    c0eb3000-d39f2fff : System RAM
    d39f3000-d3a5cfff : reserved
    d3a5d000-d3ac2fff : System RAM
    d3ac3000-d3c02fff : ACPI Non-volatile Storage
    d3c03000-d5ffefff : reserved
    d5fff000-d5ffffff : System RAM
    d6000000-d6ffffff : RAM buffer
    d7000000-df1fffff : reserved
      d7200000-df1fffff : Graphics Stolen Memory
    df200000-feafffff : PCI Bus 0000:00
      e0000000-efffffff : 0000:00:02.0
      f0000000-f00fffff : PCI Bus 0000:03
        f0000000-f0003fff : 0000:03:00.0
          f0000000-f0003fff : r8169
      f7800000-f7bfffff : 0000:00:02.0
      f7c00000-f7cfffff : PCI Bus 0000:06
        f7c00000-f7c3ffff : 0000:06:00.1
        f7c40000-f7c7ffff : 0000:06:00.0
        f7c80000-f7c800ff : 0000:06:00.1
          f7c80000-f7c800ff : lpfc
        f7c81000-f7c81fff : 0000:06:00.1
          f7c81000-f7c81fff : lpfc
        f7c82000-f7c820ff : 0000:06:00.0
          f7c82000-f7c820ff : lpfc
        f7c83000-f7c83fff : 0000:06:00.0
          f7c83000-f7c83fff : lpfc
      f7d00000-f7dfffff : PCI Bus 0000:03
        f7d00000-f7d00fff : 0000:03:00.0
          f7d00000-f7d00fff : r8169
      f7e00000-f7efffff : PCI Bus 0000:01
        f7e00000-f7e3ffff : 0000:01:00.1
        f7e40000-f7e7ffff : 0000:01:00.0
        f7e80000-f7e83fff : 0000:01:00.1
          f7e80000-f7e83fff : qla2xxx
        f7e84000-f7e87fff : 0000:01:00.0
          f7e84000-f7e87fff : qla2xxx
      f7f00000-f7f0ffff : 0000:00:14.0
        f7f00000-f7f0ffff : xhci-hcd
      f7f10000-f7f13fff : 0000:00:1b.0
        f7f10000-f7f13fff : ICH HD audio
      f7f14000-f7f17fff : 0000:00:03.0
        f7f14000-f7f17fff : ICH HD audio
      f7f18000-f7f180ff : 0000:00:1f.3
      f7f19000-f7f197ff : 0000:00:1f.2
        f7f19000-f7f197ff : ahci
      f7f1a000-f7f1a3ff : 0000:00:1d.0
        f7f1a000-f7f1a3ff : ehci_hcd
      f7f1b000-f7f1b3ff : 0000:00:1a.0
        f7f1b000-f7f1b3ff : ehci_hcd
      f7f1c000-f7f1c00f : 0000:00:16.0
        f7f1c000-f7f1c00f : mei_me
      f7fe0000-f7feffff : pnp 00:07
      f8000000-fbffffff : PCI MMCONFIG 0000 [bus 00-3f]
        f8000000-fbffffff : reserved
          f8000000-fbffffff : pnp 00:07
    fec00000-fec00fff : reserved
      fec00000-fec003ff : IOAPIC 0
    fed00000-fed03fff : reserved
      fed00000-fed003ff : HPET 0
        fed00000-fed003ff : PNP0103:00
    fed10000-fed17fff : pnp 00:07
    fed18000-fed18fff : pnp 00:07
    fed19000-fed19fff : pnp 00:07
    fed1c000-fed1ffff : reserved
      fed1c000-fed1ffff : pnp 00:07
    fed20000-fed3ffff : pnp 00:07
    fed40000-fed44fff : pnp 00:00
    fed45000-fed8ffff : pnp 00:07
    fed90000-fed93fff : pnp 00:07
    fee00000-fee00fff : Local APIC
      fee00000-fee00fff : reserved
    ff000000-ffffffff : reserved
      ff000000-ffffffff : INT0800:00
        ff000000-ffffffff : pnp 00:07
    100000000-21edfffff : System RAM
    21ee00000-21fffffff : RAM buffer
    
    ===========================ioport_resource============================
    0000-0cf7 : PCI Bus 0000:00
      0000-001f : dma1
      0020-0021 : pic1
      0040-0043 : timer0
      0050-0053 : timer1
      0060-0060 : keyboard
      0064-0064 : keyboard
      0070-0077 : rtc0
      0080-008f : dma page reg
      00a0-00a1 : pic2
      00c0-00df : dma2
      00f0-00ff : fpu
        00f0-00f0 : PNP0C04:00
      03c0-03df : vga+
      03f8-03ff : serial
      04d0-04d1 : pnp 00:06
      0800-087f : pnp 00:01
      0a00-0a0f : pnp 00:04
      0a20-0a2f : pnp 00:04
      0a30-0a3f : pnp 00:04
    0cf8-0cff : PCI conf1
    0d00-ffff : PCI Bus 0000:00
      1800-1803 : ACPI PM1a_EVT_BLK
      1804-1805 : ACPI PM1a_CNT_BLK
      1808-180b : ACPI PM_TMR
      1810-1815 : ACPI CPU throttle
      1820-182f : ACPI GPE0_BLK
      1850-1850 : ACPI PM2_CNT_BLK
      1854-1857 : pnp 00:03
      c000-cfff : PCI Bus 0000:06
        c000-c0ff : 0000:06:00.1
        c100-c1ff : 0000:06:00.0
      d000-dfff : PCI Bus 0000:03
        d000-d0ff : 0000:03:00.0
          d000-d0ff : r8169
      e000-efff : PCI Bus 0000:01
        e000-e0ff : 0000:01:00.1
        e100-e1ff : 0000:01:00.0
      f000-f03f : 0000:00:02.0
      f040-f05f : 0000:00:1f.3
      f060-f07f : 0000:00:1f.2
        f060-f07f : ahci
      f080-f083 : 0000:00:1f.2
        f080-f083 : ahci
      f090-f097 : 0000:00:1f.2
        f090-f097 : ahci
      f0a0-f0a3 : 0000:00:1f.2
        f0a0-f0a3 : ahci
      f0b0-f0b7 : 0000:00:1f.2
        f0b0-f0b7 : ahci
    
     ** Execution took   3.41s (real)   3.38s (CPU)
    crash>
