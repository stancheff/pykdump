Analysing device-mapper and LVM information (dmshow)
====================================================

The dmshow program can be used to quickly extract dm-multipath and LVM
volume information from vmcore. It also provides '-\\-check' option to
check for potential LVM, multipath issues and report the same.

Use '-h' to view the options provided by this program::

    crash> dmshow -h
    usage: dmshow [-h] [-x] [--check] [-m [FIELDS]] [-ll [FIELDS]] [-d [FIELDS]] [--table] [--lvs] [--lvuuid] [--pvs]

    optional arguments:
      -h, --help            show this help message and exit
      -x, --hex             display fields in hex
      --check               check for common DM issues (WIP)
      -m [FIELDS], --multipath [FIELDS]
                            show multipath devices and fields
      -ll [FIELDS], --list [FIELDS]
                            show multipath device listing similar to "multipath -ll"
      -d [FIELDS], --mapdev [FIELDS]
                            show mapped_devices and fields
      --table               show "dmsetup table" like output
      --lvs                 show lvm volume information similar to "lvs" command
      --lvuuid              show lvm volume and volume group's UUID
      --pvs                 show physical volume information similar to "pvs" command

     ** Execution took   1.27s (real)   1.27s (CPU)
    crash>

* `Show mapped_devices and fields (-d)`_
* `Show multipath devices and fields (-m)`_
* `Show multipath devices similar to 'multipath -ll' output (-ll)`_
* `Show 'dmsetup table' like output (-\\-table)`_
* `Show lvm volume information similar to 'lvs' command (-\\-lvs)`_
* `Show lvm volume and volume group's UUID (-\\-lvuuid)`_
* `Show physical volume information similar to 'pvs' command (-\\-pvs)`_
* `Check for common DM issues (-\\-check)`_

Show mapped_devices and fields (-d)
-----------------------------------

Executing dmshow program with '-d' option lists the pointer to mapped_device
structure associated with multipath devices and lvm volumes. It also prints
the mapped_device->flags for each device::

    crash> dmshow -d
    NUMBER  NAME                                       MAPPED_DEVICE         FLAGS
    dm-0    rhel00-root                                0xffff88020f221800    flags: 64        
    dm-1    rhel-swap                                  0xffff88020f227800    flags: 64        
    dm-2    rhel00-swap                                0xffff88020f226800    flags: 64        
    dm-3    mpathi                                     0xffff880210213000    flags: 64        
    dm-4    mpathh                                     0xffff880210216800    flags: 64        
    dm-5    mpathb                                     0xffff8800cf748800    flags: 64        
    dm-6    mpathg                                     0xffff8800cf74b800    flags: 64        
    dm-7    mpathd                                     0xffff8800cf74e800    flags: 64        
    dm-8    mpathj                                     0xffff8802159d2000    flags: 64        
    dm-9    mpathf                                     0xffff8802159d7000    flags: 64        
    dm-10   mpathe                                     0xffff8800cf289800    flags: 64        
    [...]
    dm-29   appvg-oraapps_vol                          0xffff8800ce86b800    flags: 64        
    dm-30   prodvg1-lvdata0                            0xffff8800cde73800    flags: 64        
    dm-31   prodvg1-lvdata1                            0xffff8800cde70800    flags: 64        
    dm-32   prodvg1-lvdata2                            0xffff8800cde77800    flags: 64        
    dm-33   prodvg1-lvdata3                            0xffff8800cde77000    flags: 64        
    dm-34   prodvg1-lvdata4                            0xffff88021130d800    flags: 64        
    dm-35   prodvg2-prdbkplv0                          0xffff8800cf749000    flags: 64        
    dm-36   prodvg2-prdbkplv1                          0xffff8800ce86b000    flags: 64        
    dm-37   rhel00-home                                0xffff8800cf74c000    flags: 64        
    dm-38   rhel-root                                  0xffff880210217000    flags: 64        
     ** Execution took   0.04s (real)   0.05s (CPU)
    crash>

Show multipath devices and fields (-m)
--------------------------------------

The '-m' option prints basic information for the multipath devices e.g.
pointer to struct multipath, nr_valid_paths and queue_if_no_path::

    crash> dmshow -m
    NUMBER  NAME                   MULTIPATH                      nr_valid_paths            queue_if_no_path
    dm-3    mpathi                 0xffff880207b70800                          4		Enabled
    dm-4    mpathh                 0xffff880214945600                          4		Enabled
    dm-5    mpathb                 0xffff880214dbb200                          4		Enabled
    dm-6    mpathg                 0xffff880214945e00                          4		Enabled
    dm-7    mpathd                 0xffff880214dbbe00                          4		Enabled
    dm-8    mpathj                 0xffff8800b1593200                          4		Enabled
    dm-9    mpathf                 0xffff8801d76b7600                          4		Enabled
    dm-10   mpathe                 0xffff880214dbb400                          4		Enabled
    dm-11   mpatha                 0xffff880214dbaa00                          4		Enabled
    dm-12   mpathr                 0xffff8800cd3bd000                          4		Enabled
    dm-13   mpathn                 0xffff880214dbc800                          4		Enabled
    dm-14   mpathp                 0xffff8801dda08800                          4		Enabled
    [...]


Show multipath devices similar to 'multipath -ll' output (-ll)
--------------------------------------------------------------

'-ll' option prints the detailed multipath device information similar to
the 'multipath -ll' command output::

    crash> dmshow -ll
    ------------------------------------------------------------------------------------------
    mpathi  (3600140530e36ebf3d744e94952d7b048)  dm-3     LIO-ORG   block16         
    size=1024.00M  (queue_if_no_path enabled)  hwhandler=None  
    +- policy='service-time' 
      `- 0:0:0:16 sdp 8:240             [scsi_device: 0xffff88003578d000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 0:0:1:16 sdbl 67:240           [scsi_device: 0xffff88020f06d000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
       `- 7:0:0:16 sdae 65:224          [scsi_device: 0xffff88017c80b000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:1:16 sdcl 69:144           [scsi_device: 0xffff88020f121000 sdev_state: SDEV_RUNNING]
    ------------------------------------------------------------------------------------------
    mpathh  (3600140590f29d48c0e445ee92666ce3b)  dm-4     LIO-ORG   block15         
    size=1024.00M  (queue_if_no_path enabled)  hwhandler=None  
    +- policy='service-time' 
      `- 0:0:0:15 sdq 65:0              [scsi_device: 0xffff880035f35000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 0:0:1:15 sdbm 68:0             [scsi_device: 0xffff8800352cb000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:0:15 sdaf 65:240           [scsi_device: 0xffff88020ee3a800 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:1:15 sdcm 69:160           [scsi_device: 0xffff88020f120800 sdev_state: SDEV_RUNNING]
    ------------------------------------------------------------------------------------------
    mpathb  (360014058aaaf65146b3415cbdd7dcb8a)  dm-5     LIO-ORG   block1          
    size=1024.00M  (queue_if_no_path enabled)  hwhandler=None  
    +- policy='service-time' 
      `- 0:0:0:1 sdar 66:176            [scsi_device: 0xffff88020ee3d000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 0:0:1:1 sdcf 69:48             [scsi_device: 0xffff88020f125000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:0:1 sdbh 67:176            [scsi_device: 0xffff88003578e800 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:1:1 sdda 70:128            [scsi_device: 0xffff8802107f2000 sdev_state: SDEV_RUNNING]
    ------------------------------------------------------------------------------------------
    mpathg  (36001405eefdc858a57842c3bec1855b4)  dm-6     LIO-ORG   block14         
    size=1024.00M  (queue_if_no_path enabled)  hwhandler=None  
    +- policy='service-time' 
      `- 0:0:0:14 sds 65:32             [scsi_device: 0xffff880035f34800 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 0:0:1:14 sdbn 68:16            [scsi_device: 0xffff880035f30000 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:0:14 sdai 66:32            [scsi_device: 0xffff8802111cd800 sdev_state: SDEV_RUNNING]
    +- policy='service-time' 
      `- 7:0:1:14 sdcn 69:176           [scsi_device: 0xffff88020f120000 sdev_state: SDEV_RUNNING]
    ------------------------------------------------------------------------------------------
    [...]

Show 'dmsetup table' like output (-\\-table)
--------------------------------------------

The '-\\-table' option prints device-mapper internal table similar to the
'dmsetup -\\-table' command output::

    crash> dmshow --table
    rhel00-root: 0 104857600 linear 8:5 [sda] 395208704
    rhel-swap: 0 15990784 linear 8:2 [sda] 104859648
    rhel00-swap: 0 15990784 linear 8:5 [sda] 2048
    mpathi: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 8:240 [sdp] 1 service-time 0 1 1 67:240 [sdbl] 1 service-time 0 1 1 65:224 [sdae] 1 service-time 0 1 1 69:144 [sdcl] 1
    mpathh: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 65:0 [sdq] 1 service-time 0 1 1 68:0 [sdbm] 1 service-time 0 1 1 65:240 [sdaf] 1 service-time 0 1 1 69:160 [sdcm] 1
    mpathb: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 66:176 [sdar] 1 service-time 0 1 1 69:48 [sdcf] 1 service-time 0 1 1 67:176 [sdbh] 1 service-time 0 1 1 70:128 [sdda] 1
    mpathg: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 65:32 [sds] 1 service-time 0 1 1 68:16 [sdbn] 1 service-time 0 1 1 66:32 [sdai] 1 service-time 0 1 1 69:176 [sdcn] 1
    [...]
    mpathq: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 8:64 [sde] 1 service-time 0 1 1 67:64 [sdba] 1 service-time 0 1 1 8:224 [sdo] 1 service-time 0 1 1 69:0 [sdcc] 1
    mpaths: 0 2097152 multipath 1 queue_if_no_path 0 4 1 service-time 0 1 1 8:32 [sdc] 1 service-time 0 1 1 67:0 [sdaw] 1 service-time 0 1 1 8:160 [sdk] 1 service-time 0 1 1 68:176 [sdbx] 1
    appvg-oraapps_vol: 0 2088960 linear 253:27 [dm-27] 2048
    appvg-oraapps_vol: 2088960 2088960 linear 253:12 [dm-12] 2048
    appvg-oraapps_vol: 4177920 2088960 linear 253:28 [dm-28] 2048
    appvg-oraapps_vol: 6266880 2088960 linear 253:23 [dm-23] 2048
    appvg-oraapps_vol: 8355840 2088960 linear 253:25 [dm-25] 2048
    [...]
    prodvg1-lvdata1: 2088960 8192 linear 253:5 [dm-5] 10240
    prodvg1-lvdata2: 0 2088960 linear 253:7 [dm-7] 2048
    prodvg1-lvdata2: 2088960 8192 linear 253:5 [dm-5] 18432
    prodvg1-lvdata3: 0 2088960 linear 253:10 [dm-10] 2048
    prodvg1-lvdata3: 2088960 8192 linear 253:5 [dm-5] 26624
    prodvg1-lvdata4: 0 2088960 linear 253:9 [dm-9] 2048
    [...]

Show lvm volume information similar to 'lvs' command (-\\-lvs)
--------------------------------------------------------------

Users can get lvm volume information similar to the 'lvs' command output
by using '-\\-lvs' option::

    crash> dmshow --lvs
    LV DM-X DEV   LV NAME                      VG NAME                 OPEN COUNT       LV SIZE (MB)     PV NAME
    dm-0          root                         rhel00                           1           51200.00     sda
    dm-1          swap                         rhel                             0            7808.00     sda
    dm-2          swap                         rhel00                           2            7808.00     sda
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathq	(dm-27)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathr	(dm-12)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpaths	(dm-28)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpatht	(dm-23)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathu	(dm-25)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathv	(dm-21)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathw	(dm-20)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathx	(dm-19)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathy	(dm-18)
    dm-29         oraapps_vol                  appvg                            1            9216.00     mpathz	(dm-22)
    dm-30         lvdata0                      prodvg1                          1            1024.00     mpatha	(dm-11)
    dm-30         lvdata0                      prodvg1                          1            1024.00     mpathb	(dm-5)
    dm-31         lvdata1                      prodvg1                          1            1024.00     mpathc	(dm-16)
    dm-31         lvdata1                      prodvg1                          1            1024.00     mpathb	(dm-5)
    dm-32         lvdata2                      prodvg1                          1            1024.00     mpathd	(dm-7)
    dm-32         lvdata2                      prodvg1                          1            1024.00     mpathb	(dm-5)
    dm-33         lvdata3                      prodvg1                          1            1024.00     mpathe	(dm-10)

Show lvm volume and volume group's UUID (-\\-lvuuid)
----------------------------------------------------

The output of '-\\-lvuuid' option is similar to '-\\-lvs', but is also
provides the UUID of lvm volume and volume groups::

    crash> dmshow --lvuuid
    LV DM-X DEV   LV NAME                   VG NAME                LV SIZE (MB)      LV UUID                           VG UUID
    dm-0          root                      rhel00                     51200.00      tnqhh4lxlhQqNuKP4V8WgnE5c6RY46oC  YwZPcP2fdN5KlZn52mve8FxANMtkVD0f
    dm-1          swap                      rhel                        7808.00      5mkMJYaeYUKsNgQpZbhUhEcPIizO5hfW  G9ckFgUu9Ta5370Drr3o1HSEC5cKOq8d
    dm-2          swap                      rhel00                      7808.00      yRYd9VCCakcSQHdxBLrT80RFZP2WPuYV  YwZPcP2fdN5KlZn52mve8FxANMtkVD0f
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-29         oraapps_vol               appvg                       9216.00      Es4gcJ1berhRRjtQcpeUspPl5eT9oHVf  eOL5OQSw1ECpqQMOSyBnd5zboTGjnd7Y
    dm-30         lvdata0                   prodvg1                     1024.00      NGCX1qOmDeJ7XT77LeKp4WFw1an124Wc  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-30         lvdata0                   prodvg1                     1024.00      NGCX1qOmDeJ7XT77LeKp4WFw1an124Wc  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-31         lvdata1                   prodvg1                     1024.00      wBcHLGf1c63K5Ki2sWuuu7fVj4OQagT9  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-31         lvdata1                   prodvg1                     1024.00      wBcHLGf1c63K5Ki2sWuuu7fVj4OQagT9  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-32         lvdata2                   prodvg1                     1024.00      qdctN8EuI1EDVRJZPISc34P0dQBDqXG8  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-32         lvdata2                   prodvg1                     1024.00      qdctN8EuI1EDVRJZPISc34P0dQBDqXG8  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-33         lvdata3                   prodvg1                     1024.00      G8osg99x1eKGP2OnI29s0S53Hn79gIm3  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    dm-33         lvdata3                   prodvg1                     1024.00      G8osg99x1eKGP2OnI29s0S53Hn79gIm3  7JS0jiSW2v53RpDzeV2GFJqmspyVS4bY
    [...]

Show physical volume information similar to 'pvs' command (-\\-pvs)
-------------------------------------------------------------------

To view the information about Physical Volumes, use '-\\-pvs' option::

    crash> dmshow --pvs
    PV NAME                        PV's MAPPED_DEVICE                    DEVICE SIZE (MB)	VG NAME              LV NAME
    sda                            [PV not on dm dev, skipping!]	        305245.34	rhel00               root
    sda                            [PV not on dm dev, skipping!]	        305245.34	rhel                 swap
    sda                            [PV not on dm dev, skipping!]	        305245.34	rhel00               swap
    mpathq (dm-27)                   ffff880211309000	                          1024.00	appvg                oraapps_vol
    mpathr (dm-12)                   ffff8800cf28f800	                          1024.00	appvg                oraapps_vol
    mpaths (dm-28)                   ffff88021e4eb000	                          1024.00	appvg                oraapps_vol
    mpatht (dm-23)	             ffff88021065d000	                          1024.00	appvg                oraapps_vol
    mpathu (dm-25)	             ffff88021130a000	                          1024.00	appvg                oraapps_vol
    mpathv (dm-21)	             ffff8800cde73000	                          1024.00	appvg                oraapps_vol
    mpathw (dm-20)	             ffff8800cde70000	                          1024.00	appvg                oraapps_vol
    mpathx (dm-19)	             ffff8800ceaf5800	                          1024.00	appvg                oraapps_vol
    mpathy (dm-18)	             ffff8800ceaf1800	                          1024.00	appvg                oraapps_vol
    mpathz (dm-22)	             ffff88021065a000	                          1024.00	appvg                oraapps_vol
    mpatha (dm-11)	             ffff8800cf28c800	                          1024.00	prodvg1              lvdata0
    mpathb (dm-5)	             ffff8800cf748800	                          1024.00	prodvg1              lvdata0
    mpathc (dm-16)	             ffff8802112e4800	                          1024.00	prodvg1              lvdata1
    mpathb (dm-5)	             ffff8800cf748800	                          1024.00	prodvg1              lvdata1
    mpathd (dm-7)	             ffff8800cf74e800	                          1024.00	prodvg1              lvdata2
    mpathb (dm-5)	             ffff8800cf748800	                          1024.00	prodvg1              lvdata2
    [...]

Check for common DM issues (-\\-check)
--------------------------------------

The '-\\-check' option checks for potential lvm, multipath issues and
reports the same.

For example, following output shows that system is having multipath devices
but the 'multipathd' process is not running. This will lead to no path checks
and IO failover will not work::

    crash> dmshow --check
    NUMBER  NAME                                       MAPPED_DEVICE         FLAGS
    dm-0    rhel00-root                                0xffff88020f221800    flags: 0x40      
    dm-1    rhel-swap                                  0xffff88020f227800    flags: 0x40      
    dm-2    rhel00-swap                                0xffff88020f226800    flags: 0x40      
    dm-3    mpathi                                     0xffff880210213000    flags: 0x40      
    dm-4    mpathh                                     0xffff880210216800    flags: 0x40     
    [...]
    dm-36   prodvg2-prdbkplv1                          0xffff8800ce86b000    flags: 0x40      
    dm-37   rhel00-home                                0xffff8800cf74c000    flags: 0x40      
    dm-38   rhel-root                                  0xffff880210217000    flags: 0x40      

    Checking for device-mapper issues...

    Getting a list of processes in UN state...			[Done] (Count: 21)

    Processing the back trace of hung tasks...			[Done]

    ** multipath device(s) are present, but multipathd service is
       not running. IO failover/failback may not work.

    Found 21 processes in UN state.

    Run 'hanginfo' for more information on processes in UN state.

     ** Execution took   2.40s (real)   2.31s (CPU)
    crash>
