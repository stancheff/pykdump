Analyzing process/task details from vmcore (taskinfo)
=====================================================

The taskinfo program available in PyKdump framework can be used to quickly
analyze the process/task details. It allows users to list the processes as
per their memory usage, last execution time, run specific crash commands on
processes in Running/Un-interruptible state, retrieve process namespace
details, etc.

Options provided by 'taskinfo'::

    crash> taskinfo -h
    Usage: taskinfo [options]
    
    Options:
      -h, --help            show this help message and exit
      -v                    verbose output
      --summary             Summary
      --hang                Equivalent to '-r --task=UN' and prints just several newest and several oldest threads
      --maxpids=MAXPIDS     Maximum number of PIDs to print for --hang and --mem
      --pidinfo=PIDINFO     Display details for a given PID. You can specify PID or addr of task_struct
      --taskfilter=TASKFILTER
                            A list of 2-letter task states to print, e.g. UN
      --pstree              Emulate user-space 'pstree' output
      -r, --recent          Reverse order while sorting by ran_ago
      --cmd=CMD             For each listed task, display output of specified command, e.g. '--cmd files'
      --memory              Print a summary of memory usage by tasks
      --ns                  Print info about namespaces
      --version             Print program version and exit
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash>

* `Summary (-\\-Summary)`_
* `Print the hung task information (-\\-hang)`_
* `Maximum number of PIDs to print for -\\-hang and -\\-mem (-\\-maxpids)`_
* `Display the details for a given PID (-\\-pidinfo)`_
* `Filter the list of processes as per their state (-\\-taskfilter)`_
* `Emulate a user-space 'pstree' output (-\\-pstree)`_
* `Use reverse order while sorting and printing task details (-r)`_
* `Run specific command for each task (-\\-cmd)`_
* `Print a summary of memory usage by tasks (-\\-memory)`_
* `Print info about namespaces (-\\-ns)`_

Summary (-\\-Summary)
---------------------
The '-\\-summary' option prints a small summary about recently executed
tasks, number of processes in different states, and the threads running
in their own namespaces::

    crash> taskinfo --summary
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
    
    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        There are 8 threads running in their own namespaces
    	Use 'taskinfo --ns' to get more details
    ------------------------------------------------------------------------------
    
     ** Execution took   0.04s (real)   0.03s (CPU)
    crash>

Print the hung task information (-\\-hang)
------------------------------------------
To view the summary of hung tasks, use '-\\-hang' option::

    crash> taskinfo --hang
    === Tasks in reverse order, scheduled recently first (5 tasks skipped) ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
      11643             dd   0              1  UN               UID=0
      11644             dd   0             10  UN               UID=0
      11646             dd   1             28  UN               UID=0
        308      scsi_eh_0   2            523  UN               UID=0
        355      scsi_eh_7   2           2598  UN               UID=0
       7018   jbd2/dm-31-8   2         162648  UN               UID=0
       7030   jbd2/dm-35-8   1         162649  UN               UID=0
       7033   jbd2/dm-36-8   3         162650  UN               UID=0
               <snip>
       7314   kworker/u8:1   1         167673  UN               UID=0
      11459             rm   2         167950  UN               UID=0
      11449             rm   0         168080  UN               UID=0
      11428             rm   0         168084  UN               UID=0
      11450             rm   2         168106  UN               UID=0
      11451             rm   0         168140  UN               UID=0
      11446             rm   2         168172  UN               UID=0
      11452             rm   3         172493  UN               UID=0
    
      ** Execution took   0.07s (real)   0.06s (CPU)
    crash>

Users can get more verbose information about the hung tasks using '-v'
(verbose) flag::

    crash> taskinfo --hang -v
    === Tasks in reverse order, scheduled recently first (5 tasks skipped) ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
      11643             dd   0              1  UN               UID=0
    
    PID=11643  CPU=0 CMD=dd
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
      #10  filemap_write_and_wait_range+0x56
      #11  nfs4_file_fsync+0x81
      #12  vfs_fsync+0x2b
      #13  nfs4_file_flush+0x5e
      #14  filp_close+0x34
      #15  __close_fd+0x78
      #16  sys_close+0x23
      #17  system_call_fastpath+0x16, 477 bytes of data
    
    ------------------------------------------------------------------------------
    
      11644             dd   0             10  UN               UID=0
    
    PID=11644  CPU=0 CMD=dd
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
      #10  filemap_write_and_wait_range+0x56
      #11  nfs4_file_fsync+0x81
      #12  vfs_fsync+0x2b
      #13  nfs4_file_flush+0x5e
      #14  filp_close+0x34
      #15  __close_fd+0x78
      #16  sys_close+0x23
      #17  system_call_fastpath+0x16, 477 bytes of data
    
    ------------------------------------------------------------------------------
    
      11646             dd   1             28  UN               UID=0
    
    PID=11646  CPU=1 CMD=dd
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
      #10  filemap_write_and_wait_range+0x56
      #11  nfs4_file_fsync+0x81
      #12  vfs_fsync+0x2b
      #13  nfs4_file_flush+0x5e
      #14  filp_close+0x34
      #15  __close_fd+0x78
      #16  sys_close+0x23
      #17  system_call_fastpath+0x16, 477 bytes of data
    [...]

Maximum number of PIDs to print for -\\-hang and -\\-mem (-\\-maxpids)
----------------------------------------------------------------------
The '-\\-hang' option by default prints the details for every process.
But users can restrict the output to a specific number of processes by using
'-\\-maxpids' option.

For example, using '-\\-maxpids=5' option will print the details of first and
last 5 processes sorted as per their last execution time::

    crash> taskinfo --hang --maxpids=5
    === Tasks in reverse order, scheduled recently first (11 tasks skipped) ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
      11643             dd   0              1  UN               UID=0
      11644             dd   0             10  UN               UID=0
      11646             dd   1             28  UN               UID=0
        308      scsi_eh_0   2            523  UN               UID=0
        355      scsi_eh_7   2           2598  UN               UID=0
               <snip>
      11428             rm   0         168084  UN               UID=0
      11450             rm   2         168106  UN               UID=0
      11451             rm   0         168140  UN               UID=0
      11446             rm   2         168172  UN               UID=0
      11452             rm   3         172493  UN               UID=0
    
     ** Execution took   0.07s (real)   0.07s (CPU)
    crash>

Similarly, when the '-\\-maxpids=N' option is used with '-\\-mem', it will
restrict the output only to the specified number of process.::

    crash> taskinfo --mem --maxpids=5
     ==== First 5 Tasks reverse-sorted by RSS+SHM ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
       PID=  6581 CMD=X               RSS=0.023 Gb
       PID=  6685 CMD=gnome-settings- RSS=0.021 Gb
       PID=  4624 CMD=multipathd      RSS=0.019 Gb
    
     ==== First 5 Tasks Reverse-sorted by RSS only ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
       PID=  6581 CMD=X               RSS=0.023 Gb
       PID=  6685 CMD=gnome-settings- RSS=0.021 Gb
       PID=  4624 CMD=multipathd      RSS=0.019 Gb
    
     === Total Memory in RSS  0.497 Gb
     === Total Memory in SHM  0.000 Gb
    
     ** Execution took   0.21s (real)   0.10s (CPU), Child processes:   0.10s
    crash>

Display the details for a given PID (-\\-pidinfo)
-------------------------------------------------
To view more detailed information about particular process, use '-\\-pidinfo'.
It prints the address of 'task_struct' associated with given PID, 'uid' and
'gid' credentials with which the process was executed, and 'RLIMITs'::


    crash> taskinfo --pidinfo=355
    ----    355(UN) <struct task_struct 0xffff880211d16eb0> scsi_eh_7
       cpu 2
       -- Parent: 2 kthreadd
       -- Credentials
    	  uid=18446612133217246980   gid=18446612133217246984
    	  suid=18446612133217246988  sgid=18446612133217246992
    	  euid=18446612133217246996  egid=18446612133217247000
    	  fsuid=18446612133217247004 fsgid=18446612133217247008
         --user_struct <struct user_struct 0xffffffff81a345a0>
    	  processes=401 files=0 sigpending=0
         --group_info <struct group_info 0xffffffff81a3dd80>
          []
       -- Rlimits:
    	00 (RLIMIT_CPU) cur=INFINITY max=INFINITY
    	01 (RLIMIT_FSIZE) cur=INFINITY max=INFINITY
    	02 (RLIMIT_DATA) cur=INFINITY max=INFINITY
    	03 (RLIMIT_STACK) cur=8388608 max=INFINITY
    	04 (RLIMIT_CORE) cur=0 max=INFINITY
    	05 (RLIMIT_RSS) cur=INFINITY max=INFINITY
    	06 (RLIMIT_NPROC) cur=30294 max=30294
    	07 (RLIMIT_NOFILE) cur=1024 max=4096
    	08 (RLIMIT_MEMLOCK) cur=65536 max=65536
    	09 (RLIMIT_AS) cur=INFINITY max=INFINITY
    	10 (RLIMIT_LOCKS) cur=INFINITY max=INFINITY
    	11 (RLIMIT_SIGPENDING) cur=30294 max=30294
    	12 (RLIMIT_MSGQUEUE) cur=819200 max=819200
    	13 (RLIMIT_NICE) cur=0 max=0
    	14 (RLIMIT_RTPRIO) cur=0 max=0
    	15 (RLIMIT_RTTIME) cur=INFINITY max=INFINITY
       --- thread_info <struct thread_info 0xffff880035200000>
    
      ** Execution took   0.12s (real)   0.12s (CPU)
    crash>

Filter the list of processes as per their state (-\\-taskfilter)
----------------------------------------------------------------
To get a list of processes filtered as per their state, use '-\\-taskfilter'.

For example, below command will only list the processes in running (RU)
state::

    crash> taskinfo --taskfilter=RU
    === Tasks in PID order, grouped by Thread Group leader ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
    >     0      swapper/0   0        1172313  RU               UID=0
    >  6868           bash   1              0  RU               UID=0
       7598    kworker/1:0   1            340  RU               UID=0
    
     ** Execution took   0.05s (real)   0.05s (CPU)
    crash>

To get a filtered list of processes stuck un Un-interruptible (UN) state::

    crash> taskinfo --taskfilter=UN
    === Tasks in PID order, grouped by Thread Group leader ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
        308      scsi_eh_0   2            523  UN               UID=0
        355      scsi_eh_7   2           2598  UN               UID=0
       7015   jbd2/dm-30-8   0         167657  UN               UID=0
       7018   jbd2/dm-31-8   2         162648  UN               UID=0
       7021   jbd2/dm-32-8   1         167641  UN               UID=0
       7024   jbd2/dm-33-8   0         167641  UN               UID=0
       7027   jbd2/dm-34-8   1         167641  UN               UID=0
       7030   jbd2/dm-35-8   1         162649  UN               UID=0
       7033   jbd2/dm-36-8   3         162650  UN               UID=0
       7314   kworker/u8:1   1         167673  UN               UID=0
       7317   kworker/u8:4   3         167642  UN               UID=0
      11428             rm   0         168084  UN               UID=0
      11446             rm   2         168172  UN               UID=0
      11449             rm   0         168080  UN               UID=0
      11450             rm   2         168106  UN               UID=0
      11451             rm   0         168140  UN               UID=0
      11452             rm   3         172493  UN               UID=0
      11459             rm   2         167950  UN               UID=0
      11643             dd   0              1  UN               UID=0
      11644             dd   0             10  UN               UID=0
      11646             dd   1             28  UN               UID=0
    
     ** Execution took   0.07s (real)   0.07s (CPU)
    crash>

Emulate a user-space 'pstree' output (-\\-pstree)
-------------------------------------------------
The '-\\-pstree' option will print the parent child relationship between the
processes.

This output is similar to the Linux 'pstree' command::

    crash> taskinfo --pstree
    systemd(1)-+-ModemManager(5709)---2*[{ModemManager}]
               |-NetworkManager(5788)-+-dhclient(5912)
               |                      `-2*[{NetworkManager}]
               |-abrt-watch-log(5718)
               |-abrt-watch-log(5720)
               |-abrtd(5714)
               |-accounts-daemon(5706)---2*[{accounts-daemon}]
               |-alsactl(5695)
               |-at-spi-bus-laun(6607)-+-dbus-daemon(6612)
               |                       `-3*[{at-spi-bus-laun}]
               |-at-spi2-registr(6614)---2*[{at-spi2-registr}]
               |-atd(6131)
               |-auditd(5670)-+-audispd(5672)-+-sedispatch(5674)
               |              |               `-{audispd}
               |              `-{auditd}
               |-avahi-daemon(5699)---avahi-daemon(5703)
               |-chronyd(5781)
               |-colord(6713)---2*[{colord}]
               |-crond(6130)
               |-cupsd(6107)
               |-dbus-daemon(5728)
               |-dbus-daemon(6604)
               |-dbus-launch(6603)
               |-dnsmasq(6443)---dnsmasq(6444)
               |-firewalld(5770)---{firewalld}
               |-gdm(6129)-+-X(6581)---{X}
               |           |-gdm-session-wor(6593)-+-gnome-session-b(6597)-+-gnome-settings-(6685)---4*[{gnome-settings-}]
               |           |                       |                       |-gnome-shell(6622)-+-ibus-daemon(6666)-+-ibus-dconf(6692)---3*[{ibus-dconf}]
               |           |                       |                       |                   |                   |-ibus-engine-sim(6729)---2*[{ibus-engine-sim}]
               |           |                       |                       |                   |                   `-2*[{ibus-daemon}]
               |           |                       |                       |                   `-6*[{gnome-shell}]
               |           |                       |                       `-3*[{gnome-session-b}]
               |           |                       `-2*[{gdm-session-wor}]
               |           `-3*[{gdm}]
               |-gssproxy(5738)---5*[{gssproxy}]
               |-ibus-x11(6695)---2*[{ibus-x11}]
               |-iobkp0.sh(7235)---rm(11450)
               |-iobkp1.sh(7236)---rm(11451)
               |-iodata0.sh(7237)---rm(11449)
               |-iodata1.sh(7238)---rm(11446)
               |-iodata2.sh(7239)---rm(11459)
               |-iodata3.sh(7240)---rm(11452)
               |-iodata4.sh(7241)---rm(11428)
               |-ionfs1.sh(7242)---dd(11646)
               |-ionfs2.sh(7243)---dd(11643)
               |-ionfs3.sh(7244)---dd(11644)
               |-irqbalance(5725)
               |-ksmtuned(5773)---sleep(11584)
               |-libvirtd(6119)---15*[{libvirtd}]
               |-lsmd(5698)
               |-lvmetad(4614)
               |-master(6506)-+-pickup(6507)
               |              `-qmgr(6508)
               |-mcelog(5779)
               |-multipathd(4624)---31*[{multipathd}]
               |-packagekitd(6678)---2*[{packagekitd}]
               |-polkitd(5710)---5*[{polkitd}]
               |-pulseaudio(6650)---2*[{pulseaudio}]
               |-rhnsd(6204)
               |-rhsmcertd(6117)
               |-rngd(5702)
               |-rsyslogd(5707)---2*[{rsyslogd}]
               |-rtkit-daemon(5700)---2*[{rtkit-daemon}]
               |-smartd(5696)
               |-sshd(6106)-+-sshd(6777)---bash(6792)
               |            |-sshd(6824)---bash(6830)---journalctl(11478)
               |            |-sshd(6862)---bash(6868)
               |            |-sshd(6900)---bash(6906)
               |            `-sshd(6938)---bash(6952)
               |-systemd-journal(4578)
               |-systemd-logind(5711)
               |-systemd-udevd(4618)
               |-tuned(6108)---4*[{tuned}]
               |-upowerd(6627)---2*[{upowerd}]
               |-wpa_supplicant(6677)
               `-xdg-permission-(6670)---2*[{xdg-permission-}]
    
     ** Execution took   0.05s (real)   0.04s (CPU)
    crash>

Use reverse order while sorting and printing task details (-r)
--------------------------------------------------------------
The 'taskinfo' program by default lists the process details sorted as per their
PID. The '-r' option allows users to sort process details as per their last
execution time::

    crash> taskinfo |head -10
    === Tasks in PID order, grouped by Thread Group leader ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
    >     0      swapper/0   0        1172313  RU               UID=0
          1        systemd   0           4303  IN               UID=0
          2       kthreadd   2         176550  IN               UID=0
          3    ksoftirqd/0   0            113  IN               UID=0
          5   kworker/0:0H   0              0  IN               UID=0
          7    migration/0   0           3044  IN               UID=0
          8         rcu_bh   0        1172282  IN               UID=0
    crash>
    
    crash> taskinfo -r|head -10
    === Tasks in reverse order, scheduled recently first ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
    >  6868           bash   1              0  RU               UID=0
       7119    kworker/3:0   3              0  IN               UID=0
       4069   kworker/1:1H   1              0  IN               UID=0
        874   kworker/2:1H   2              0  IN               UID=0
          5   kworker/0:0H   0              0  IN               UID=0
         23    ksoftirqd/3   3              0  IN               UID=0
       5702           rngd   3              0  IN               UID=0
    crash>

Run specific command for each task (-\\-cmd)
--------------------------------------------
While analyzing a vmcore, it is often required to run specific crash commands
e.g. 'bt', 'bt -f' on a list of processes. The '-\\-cmd' option can be used to
run the crash commands on list of processes.

For example, using 'taskinfo -\\-cmd bt' will run the 'bt' command on each
process in the list::

    crash> taskinfo --cmd bt
    === Tasks in PID order, grouped by Thread Group leader ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
    >     0      swapper/0   0        1172313  RU               UID=0
    
    crash> bt 0
    PID: 0      TASK: ffffffff81a02480  CPU: 0   COMMAND: "swapper/0"
     #0 [ffff88021ea08e48] crash_nmi_callback at ffffffff8104fd11
     #1 [ffff88021ea08e58] nmi_handle at ffffffff816b0c57
     #2 [ffff88021ea08eb0] do_nmi at ffffffff816b0e8d
     #3 [ffff88021ea08ef0] end_repeat_nmi at ffffffff816b00b9
        [exception RIP: intel_idle+244]
        RIP: ffffffff816adb04  RSP: ffffffff819efe28  RFLAGS: 00000046
        RAX: 0000000000000001  RBX: 0000000000000002  RCX: 0000000000000001
        RDX: 0000000000000000  RSI: ffffffff819effd8  RDI: 0000000000000000
        RBP: ffffffff819efe58   R8: 00000000000003e3   R9: 0000000000000018
        R10: 00000000000003e2  R11: 0000014a0e39c880  R12: ffffffff819effd8
        R13: 0000000000000002  R14: 0000000000000001  R15: ffffffff81ab8a28
        ORIG_RAX: ffffffffffffffff  CS: 0010  SS: 0018
    --- <NMI exception stack> ---
     #4 [ffffffff819efe28] intel_idle at ffffffff816adb04
     #5 [ffffffff819efe60] cpuidle_enter_state at ffffffff81529e30
     #6 [ffffffff819efe98] cpuidle_idle_call at ffffffff81529f88
     #7 [ffffffff819efed8] arch_cpu_idle at ffffffff81034eee
     #8 [ffffffff819efee8] cpu_startup_entry at ffffffff810e9aba
     #9 [ffffffff819eff30] rest_init at ffffffff81694f17
    #10 [ffffffff819eff40] start_kernel at ffffffff81b500e1
    #11 [ffffffff819eff88] x86_64_start_reservations at ffffffff81b4f66b
    #12 [ffffffff819eff98] x86_64_start_kernel at ffffffff81b4f7bc
    
    PID: 0      TASK: ffff88017ce79fa0  CPU: 1   COMMAND: "swapper/1"
     #0 [ffff88017ceafe48] __schedule at ffffffff816ab2ac
     #1 [ffff88017ceafed0] schedule_preempt_disabled at ffffffff816ac7c9
     #2 [ffff88017ceafee0] cpu_startup_entry at ffffffff810e9afa
     #3 [ffff88017ceaff28] start_secondary at ffffffff81051b96
    
    PID: 0      TASK: ffff88017ce7af70  CPU: 2   COMMAND: "swapper/2"
     #0 [ffff88021eb08e48] crash_nmi_callback at ffffffff8104fd11
     #1 [ffff88021eb08e58] nmi_handle at ffffffff816b0c57
     #2 [ffff88021eb08eb0] do_nmi at ffffffff816b0e8d
     #3 [ffff88021eb08ef0] end_repeat_nmi at ffffffff816b00b9
        [exception RIP: intel_idle+244]
        RIP: ffffffff816adb04  RSP: ffff88017ceb3e20  RFLAGS: 00000046
        RAX: 0000000000000001  RBX: 0000000000000002  RCX: 0000000000000001
        RDX: 0000000000000000  RSI: ffff88017ceb3fd8  RDI: 0000000000000002
        RBP: ffff88017ceb3e50   R8: 00000000000003d4   R9: 0000000000000020
        R10: 00000000000007cd  R11: 0000014a0e2a8640  R12: ffff88017ceb3fd8
        R13: 0000000000000002  R14: 0000000000000001  R15: ffffffff81ab8a28
        ORIG_RAX: ffffffffffffffff  CS: 0010  SS: 0018
    --- <NMI exception stack> ---
     #4 [ffff88017ceb3e20] intel_idle at ffffffff816adb04
     #5 [ffff88017ceb3e58] cpuidle_enter_state at ffffffff81529e30
     #6 [ffff88017ceb3e90] cpuidle_idle_call at ffffffff81529f88
     #7 [ffff88017ceb3ed0] arch_cpu_idle at ffffffff81034eee
     #8 [ffff88017ceb3ee0] cpu_startup_entry at ffffffff810e9aba
     #9 [ffff88017ceb3f28] start_secondary at ffffffff81051b96
    
    PID: 0      TASK: ffff88017ce7bf40  CPU: 3   COMMAND: "swapper/3"
     #0 [ffff88021eb88e48] crash_nmi_callback at ffffffff8104fd11
     #1 [ffff88021eb88e58] nmi_handle at ffffffff816b0c57
     #2 [ffff88021eb88eb0] do_nmi at ffffffff816b0e8d
     #3 [ffff88021eb88ef0] end_repeat_nmi at ffffffff816b00b9
        [exception RIP: intel_idle+244]
        RIP: ffffffff816adb04  RSP: ffff88017ceb7e20  RFLAGS: 00000046
        RAX: 0000000000000000  RBX: 0000000000000002  RCX: 0000000000000001
        RDX: 0000000000000000  RSI: ffff88017ceb7fd8  RDI: 0000000000000003
        RBP: ffff88017ceb7e50   R8: 0000000000000137   R9: ffff88021eb97a80
        R10: 7fffffffffffffff  R11: 7fffffffffffffff  R12: ffff88017ceb7fd8
        R13: 0000000000000001  R14: 0000000000000000  R15: ffffffff81ab89d0
        ORIG_RAX: ffffffffffffffff  CS: 0010  SS: 0018
    --- <NMI exception stack> ---
     #4 [ffff88017ceb7e20] intel_idle at ffffffff816adb04
     #5 [ffff88017ceb7e58] cpuidle_enter_state at ffffffff81529e30
     #6 [ffff88017ceb7e90] cpuidle_idle_call at ffffffff81529f88
     #7 [ffff88017ceb7ed0] arch_cpu_idle at ffffffff81034eee
     #8 [ffff88017ceb7ee0] cpu_startup_entry at ffffffff810e9aba
     #9 [ffff88017ceb7f28] start_secondary at ffffffff81051b96
    ------------------------------------------------------------------------------
    [...]

This option can also be combinted with '-\\-taskfilter' to run the specific
crash command on the list of processes in Running or Un-interruptible state::

    crash> taskinfo --cmd "bt -f" --taskfilter=RU
    === Tasks in PID order, grouped by Thread Group leader ===
     PID          CMD       CPU   Ran ms ago   STATE
    --------   ------------  --  ------------- -----
    >     0      swapper/0   0        1172313  RU               UID=0
    
    crash> bt -f 0
    PID: 0      TASK: ffffffff81a02480  CPU: 0   COMMAND: "swapper/0"
     #0 [ffff88021ea08e48] crash_nmi_callback at ffffffff8104fd11
        ffff88021ea08e50: ffff88021ea08ea8 ffffffff816b0c57 
     #1 [ffff88021ea08e58] nmi_handle at ffffffff816b0c57
        ffff88021ea08e60: 0000000000000000 ffff88021ea08ef8 
        ffff88021ea08e70: ffffffff81a1a700 a89424830a090e96 
        ffff88021ea08e80: ffff88021ea08ef8 ffffffff819effd8 
        ffff88021ea08e90: 0000000000000000 ffffffff819effd8 
        ffff88021ea08ea0: 00000000ffffffff ffff88021ea08ee8 
        ffff88021ea08eb0: ffffffff816b0e8d 
     #2 [ffff88021ea08eb0] do_nmi at ffffffff816b0e8d
        ffff88021ea08eb8: 0000000000000000 0000000000000001 
        ffff88021ea08ec8: 00007f451748c000 0000000000000001 
        ffff88021ea08ed8: 000000009845a000 ffffffff81ab8a28 
        ffff88021ea08ee8: ffffffff819efe58 ffffffff816b00b9 
     #3 [ffff88021ea08ef0] end_repeat_nmi at ffffffff816b00b9
        [exception RIP: intel_idle+244]
        RIP: ffffffff816adb04  RSP: ffffffff819efe28  RFLAGS: 00000046
        RAX: 0000000000000001  RBX: 0000000000000002  RCX: 0000000000000001
        RDX: 0000000000000000  RSI: ffffffff819effd8  RDI: 0000000000000000
    [...]

Print a summary of memory usage by tasks (-\\-memory)
-----------------------------------------------------
To view the memory usage by processes, use '-\\-memory'::

    crash> taskinfo --memory
     ==== First 8 Tasks reverse-sorted by RSS+SHM ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
       PID=  6581 CMD=X               RSS=0.023 Gb
       PID=  6685 CMD=gnome-settings- RSS=0.021 Gb
       PID=  4624 CMD=multipathd      RSS=0.019 Gb
       PID=  6108 CMD=tuned           RSS=0.016 Gb
       PID=  5912 CMD=dhclient        RSS=0.015 Gb
       PID=  6119 CMD=libvirtd        RSS=0.014 Gb
    
     ==== First 8 Tasks Reverse-sorted by RSS only ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
       PID=  6581 CMD=X               RSS=0.023 Gb
       PID=  6685 CMD=gnome-settings- RSS=0.021 Gb
       PID=  4624 CMD=multipathd      RSS=0.019 Gb
       PID=  6108 CMD=tuned           RSS=0.016 Gb
       PID=  5912 CMD=dhclient        RSS=0.015 Gb
       PID=  6119 CMD=libvirtd        RSS=0.014 Gb
    
     === Total Memory in RSS  0.497 Gb
     === Total Memory in SHM  0.000 Gb
    
     ** Execution took   0.50s (real)   0.29s (CPU), Child processes:   0.09s
    crash>

This option can be combined with '-\\-maxpids=2' to restrict the output to
a specified number of processes::

    crash> taskinfo --memory --maxpids=2
     ==== First 2 Tasks reverse-sorted by RSS+SHM ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
    
     ==== First 2 Tasks Reverse-sorted by RSS only ====
       PID=  6622 CMD=gnome-shell     RSS=0.089 Gb
       PID=  5770 CMD=firewalld       RSS=0.027 Gb
    
     === Total Memory in RSS  0.497 Gb
     === Total Memory in SHM  0.000 Gb
    
     ** Execution took   0.19s (real)   0.10s (CPU), Child processes:   0.10s
    crash>

Print info about namespaces (-\\-ns)
------------------------------------
To view more details about the namespaces associated with processes, use
'-\\-ns'::

    crash> taskinfo --ns
      ******************Non-standard Namespaces*******************
        ~~~~~~~~~~~~~~Namespaces Associated with PID~~~~~~~~~~~~~~
          .......<struct nsproxy 0xffff88021ed1f000>........
          ['mnt_ns']
    	 PID=27 <struct task_struct 0xffff88017c860fd0> CMD=kdevtmpfs
          .......<struct nsproxy 0xffff88020fc45000>........
          ['mnt_ns']
    	 PID=4618 <struct task_struct 0xffff8802126e0fd0> CMD=systemd-udevd
          .......<struct nsproxy 0xffff88021508d4b0>........
          ['mnt_ns', 'net_ns']
    	 PID=5700 <struct task_struct 0xffff880207e91fa0> CMD=rtkit-daemon
          .......<struct nsproxy 0xffff88020d2c9000>........
          ['mnt_ns']
    	 PID=5781 <struct task_struct 0xffff8800c6f2bf40> CMD=chronyd
          .......<struct nsproxy 0xffff88020d2c9060>........
          ['mnt_ns']
    	 PID=5788 <struct task_struct 0xffff8800cac50000> CMD=NetworkManager
    	 PID=5912 <struct task_struct 0xffff880034cf2f70> CMD=dhclient
          .......<struct nsproxy 0xffff88020d325450>........
          ['mnt_ns']
    	 PID=6107 <struct task_struct 0xffff8800cd092f70> CMD=cupsd
          .......<struct nsproxy 0xffff88021508d4e0>........
          ['mnt_ns']
    	 PID=6713 <struct task_struct 0xffff8800cd20eeb0> CMD=colord
    
     ** Execution took   0.22s (real)   0.15s (CPU)
    crash>

