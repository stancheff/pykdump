Getting module specific information (modinfo)
=============================================

The modinfo program provides several options to quickly extract module specific
information from the vmcores.

Options provided by 'modinfo'::

    crash> modinfo -h
    Usage: modinfo [options]

    Options:
      -h, --help            show this help message and exit
      --disasm=DISASM_MODULE
                            Disassemble a module functions
      --details=MODULE_DETAIL
                            Show details
      -t                    Shows tainted modules only
      -g                    Shows gaps between modules as well as phyiscally allocated sizes
      -a                    Shows address range for the module
      -u                    Shows unloaded module data if possible

     ** Execution took   0.01s (real)   0.01s (CPU)
    crash>

* `Disassemble module functions (-\\-disasm=MODULE)`_
* `Show module details (-\\-details=MODULE)`_
* `Show tainted modules (-t)`_
* `Show address range for the module (-a)`_
* `Show gaps between modules as well as physically allocated sizes (-g)`_
* `Show unloaded module data if possible (-u)`_

Disassemble module functions (-\\-disasm=MODULE)
------------------------------------------------

Using the '-\\-disasm' option, users can review the dis-assembly of each
function provided by module. For example, to review the dis-assembly of
functions in ext4 module::

    crash> modinfo --disasm=ext4
    ---------- BEGIN disassemble ext4_unlock_group() ----------
    0xffffffffc0879000 <ext4_unlock_group>:	push   %rbp
    0xffffffffc0879001 <ext4_unlock_group+0x1>:	mov    0x350(%rdi),%rax
    0xffffffffc0879008 <ext4_unlock_group+0x8>:	mov    %esi,%edi
    0xffffffffc087900a <ext4_unlock_group+0xa>:	and    $0x7f,%edi
    0xffffffffc087900d <ext4_unlock_group+0xd>:	shl    $0x6,%rdi
    0xffffffffc0879011 <ext4_unlock_group+0x11>:	mov    %rsp,%rbp
    0xffffffffc0879014 <ext4_unlock_group+0x14>:	add    0x180(%rax),%rdi
    0xffffffffc087901b <ext4_unlock_group+0x1b>:	movb   $0x0,(%rdi)
    0xffffffffc087901e <ext4_unlock_group+0x1e>:	nopl   0x0(%rax)
    0xffffffffc0879022 <ext4_unlock_group+0x22>:	pop    %rbp
    0xffffffffc0879023 <ext4_unlock_group+0x23>:	retq
    ========== END   disassemble ext4_unlock_group() ==========

    ---------- BEGIN disassemble num_clusters_in_group() ----------
    0xffffffffc0879030 <num_clusters_in_group>:	nopl   0x0(%rax,%rax,1) [FTRACE NOP]
    0xffffffffc0879035 <num_clusters_in_group+0x5>:	push   %rbp
    0xffffffffc0879036 <num_clusters_in_group+0x6>:	mov    0x350(%rdi),%rax
    0xffffffffc087903d <num_clusters_in_group+0xd>:	mov    %rsp,%rbp
    0xffffffffc0879040 <num_clusters_in_group+0x10>:	mov    0x40(%rax),%ecx
    0xffffffffc0879043 <num_clusters_in_group+0x13>:	sub    $0x1,%ecx
    0xffffffffc0879046 <num_clusters_in_group+0x16>:	mov    0x350(%rdi),%rdx
    0xffffffffc087904d <num_clusters_in_group+0x1d>:	cmp    %esi,%ecx
    0xffffffffc087904f <num_clusters_in_group+0x1f>:	je     0xffffffffc0879068 <num_clusters_in_group+0x38>
    0xffffffffc0879051 <num_clusters_in_group+0x21>:	mov    0x50(%rdx),%ecx
    0xffffffffc0879054 <num_clusters_in_group+0x24>:	mov    0x10(%rdx),%eax
    0xffffffffc0879057 <num_clusters_in_group+0x27>:	pop    %rbp
    0xffffffffc0879058 <num_clusters_in_group+0x28>:	lea    -0x1(%rax,%rcx,1),%eax
    0xffffffffc087905c <num_clusters_in_group+0x2c>:	mov    0x54(%rdx),%ecx
    0xffffffffc087905f <num_clusters_in_group+0x2f>:	shr    %cl,%eax
    [...]

Show module details (-\\-details=MODULE)
----------------------------------------

Use '-\\-details' to get more details about the module version, and functions
available in it::


    crash> modinfo --details=ext4|head -20
    struct module   : 0xffffffffc08ee6c0
    name            : ext4
    version         : None
    source ver      : 3FC0F2CFC3F9938AE9C8339
    init            : None (0xffffffffc090dbbd)
    exit            : cleanup_module (0xffffffffc08cffc2)

    .text section
    0xffffffffc08cffc2 (t) ext4_exit_fs
    0xffffffffc08cffc2 (T) cleanup_module
    0xffffffffc08cffbc (t) ext4_chksum
    0xffffffffc08cfca7 (t) ext4_mb_discard_group_preallocations
    0xffffffffc08cfca1 (t) ext4_get_group_info
    0xffffffffc08cfc96 (t) get_groupinfo_cache
    0xffffffffc08cfc27 (t) ext4_access_path
    0xffffffffc08cfbcf (t) trace_ext4_ext_convert_to_initialized_fastpath
    0xffffffffc08cf4c6 (t) ext4_load_journal
    0xffffffffc08cf4c0 (t) ext4_chksum
    0xffffffffc08cf48d (t) ext4_exit_feat_adverts
    0xffffffffc08cf487 (t) ext4_chksum
    crash>

The same command can be used for in-built or third party modules.
e.g. checking the details about 'involflt' module::

    crash> modinfo --details=involflt|head -20
    struct module   : 0xffffffffc033c340
    name            : involflt
    version         : Mar 25 2019 [ 01:23:58 ]
    source ver      : A3554E5E155D078A71E0183
    init            : crc_t10dif_pcl (0xffffffffc0350000)
    exit            : cleanup_module (0xffffffffc031abcd)

    .text section
    0xffffffffc031abcd (t) involflt_exit
    0xffffffffc031abcd (t) cleanup_module
    0xffffffffc031aba1 (t) init_latency_stats
    0xffffffffc031ab70 (t) end_cp_timer
    0xffffffffc031ab60 (t) emd_unregister_virtual_device
    0xffffffffc031ab50 (t) process_at_lun_delete
    0xffffffffc031ab40 (t) process_at_lun_query
    0xffffffffc031ab30 (t) process_at_lun_last_host_io_timestamp
    0xffffffffc031ab20 (t) process_at_lun_last_write_vi
    0xffffffffc031ab10 (t) process_at_lun_create
    0xffffffffc031ab00 (t) inm_validate_fabric_vol
    0xffffffffc031aaf0 (t) copy_iovec_data_to_data_pages
    crash>

Show tainted modules (-t)
-------------------------

The '-u' option lists the third party or customised kernel modules loaded
on system::

    crash> modinfo -t
    struct module *    MODULE_NAME                     SIZE
    0xffffffffc033c340 involflt                      677188
    ===========================================================================
    There are 1 tainted modules

     ** Execution took   0.01s (real)   0.01s (CPU)
    crash>

Show address range for the module (-a)
--------------------------------------

To view the memory address range allocated for the module, use '-a' option::

    crash> modinfo -a
    struct module *    MODULE_NAME                     SIZE
    0xffffffffc033c340 involflt                      677188
       addr range : 0xffffffffc02a9000 - 0xffffffffc0350000
    0xffffffffc0352280 crct10dif_pclmul               14307
       addr range : 0xffffffffc0350000 - 0xffffffffc0355000
    0xffffffffc0358080 scsi_tgt                       20027
       addr range : 0xffffffffc0355000 - 0xffffffffc035b000
    0xffffffffc035d180 serio_raw                      13434
       addr range : 0xffffffffc035b000 - 0xffffffffc0360000
    0xffffffffc03620e0 hyperv_keyboard                12787
       addr range : 0xffffffffc0360000 - 0xffffffffc0365000
    0xffffffffc0370b00 floppy                         69432
       addr range : 0xffffffffc0365000 - 0xffffffffc0377000
    0xffffffffc0379000 libcrc32c                      12644
       addr range : 0xffffffffc0377000 - 0xffffffffc037c000
    0xffffffffc038dda0 hv_vmbus                       96657
       addr range : 0xffffffffc037e000 - 0xffffffffc0397000
    0xffffffffc039a1a0 crc32c_intel                   22094
       addr range : 0xffffffffc0397000 - 0xffffffffc039e000
    0xffffffffc03a9240 ata_piix                       35052
       addr range : 0xffffffffc03a2000 - 0xffffffffc03ac000
    0xffffffffc03ae640 ata_generic                    12923
       addr range : 0xffffffffc03ac000 - 0xffffffffc03b1000
    0xffffffffc03b7000 crct10dif_common               12595
    [...]

Show gaps between modules as well as physically allocated sizes (-g)
--------------------------------------------------------------------

The '-g' option displays module size, allocated size and gap size.

The gap size is basically the difference between module start address and
the previous module's end address. For example, in below output, the end
address of libcrc32c module is 0xffffffffc037c000, and start address of
next module - hv_vmbus is 0xffffffffc037e000. The difference between these
addresses is the gap size::

    crash> modinfo -a
    struct module *    MODULE_NAME                     SIZE
    [...]
    0xffffffffc0379000 libcrc32c                      12644
       addr range : 0xffffffffc0377000 - 0xffffffffc037c000
    0xffffffffc038dda0 hv_vmbus                       96657
       addr range : 0xffffffffc037e000 - 0xffffffffc0397000
    [...]

    crash> pd 0xffffffffc037e000-0xffffffffc037c000
    $3 = 8192

    crash> modinfo -g
    struct module *    MODULE_NAME                     SIZE ALLOC_SIZE    GAPSIZE
    0xffffffffc033c340 involflt                      677188     684032          0
    0xffffffffc0352280 crct10dif_pclmul               14307      20480          0
    0xffffffffc0358080 scsi_tgt                       20027      24576          0
    0xffffffffc035d180 serio_raw                      13434      20480          0
    0xffffffffc03620e0 hyperv_keyboard                12787      20480          0
    0xffffffffc0370b00 floppy                         69432      73728          0
    0xffffffffc0379000 libcrc32c                      12644      20480          0
    0xffffffffc038dda0 hv_vmbus                       96657     102400       8192       <--- GAPSIZE as calculated above
    0xffffffffc039a1a0 crc32c_intel                   22094      28672          0
    0xffffffffc03a9240 ata_piix                       35052      40960      16384
    0xffffffffc03ae640 ata_generic                    12923      20480          0
    0xffffffffc03b7000 crct10dif_common               12595      20480      16384
    [...]

Show unloaded module data if possible (-u)
------------------------------------------

To view unloaded module data, use '-u'::

    crash> modinfo -u
    struct module *    MODULE_NAME                     SIZE
    0xffffffffc033c340 involflt                      677188
    0xffffffffc0352280 crct10dif_pclmul               14307
    0xffffffffc0358080 scsi_tgt                       20027
    0xffffffffc035d180 serio_raw                      13434
    0xffffffffc03620e0 hyperv_keyboard                12787
    0xffffffffc0370b00 floppy                         69432
    [...]
