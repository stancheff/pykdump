Processing SCSI subsystem details (scsishow)
============================================

The scsishow program available in mpykdump extension allows users to quickly
fetch detailed information about SCSI HBAs, SCSI targets, devices assigned
from different targets and the in-flight SCSI commands. It also provides
'-\\-check' option which can detect stalled error handling process, stuck
IO requests, SCSI commands and other potential isuses in SCSI error handling.

Use '-h' to view the options provided by this program::

    crash> scsishow -h
    usage: scsishow [-h] [-p] [-d [FIELDS]] [-s [FIELDS]] [-T [FIELDS]] [-c [FIELDS]] [-q [FIELDS]] [-r [FIELDS]] [-x] [--check] [--time] [--relative [RELATIVE]]

    optional arguments:
      -h, --help            show this help message and exit
      -p, --proc            show /proc/scsi/scsi style information
      -d [FIELDS], --devices [FIELDS]
                            show all devices
      -s [FIELDS], --hosts [FIELDS]
                            show all hosts
      -T [FIELDS], --Targets [FIELDS]
                            show all the scsi targets
      -c [FIELDS], --commands [FIELDS]
                            show SCSI commands
      -q [FIELDS], --queue [FIELDS]
                            show the IO requests, SCSI commands from request_queue
      -r [FIELDS], --requests [FIELDS]
                            show requests to SCSI devices (INCOMPLETE)
      -x, --hex             display fields in hex
      --check               check for common SCSI issues
      --time                display time and state information for SCSI commands
      --relative [RELATIVE]
                            show fields relative to the given value/symbol. Uses jiffies without argument

     ** Execution took   0.03s (real)   0.03s (CPU)
    crash>

* `Show /proc/scsi/scsi style information (-p)`_
* `Show all devices (-d)`_
* `Show all host bus adapters (optional -s option)`_
* `Show all SCSI targets (-T)`_
* `Show in-flight SCSI commands (-c)`_
* `Show commands queued in request queue of device (-q)`_
* `Show requests to SCSI devices (-r)`_
* `Check for common SCSI issues (-\\-check)`_
* `Display time and state information for SCSI commands (-\\-time)`_

Show /proc/scsi/scsi style information (-p)
-------------------------------------------

The '-p' option available with scsishow program povides device information
similar to the one shown in /proc/scsi/scsi file. Additionally it prints
information about SCSI HBAs, it's Scsi_Host structure pointer, some of the
important fields of this struct and PCI device path of the adapter::

    crash> scsishow -p

    ============================== Summary ===============================
       -- 106 SCSI Devices, 29 Are Busy --
    ........................... Vendors/Types ............................
      Vendor: LIO-ORG  Model: block9           Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: LIO-ORG  Model: block10          Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: ATA      Model: WDC WD3200AAKS-7 Rev: 3E02
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: LIO-ORG  Model: block11          Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: LIO-ORG  Model: block12          Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: LIO-ORG  Model: block13          Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    
      Vendor: LIO-ORG  Model: block22          Rev: 4.0 
      Type:   Direct-Access                    ANSI  SCSI revision: 05
    [...]

    ============================= Scsi_Hosts==============================
     *scsi0*  <struct Scsi_Host 0xffff880211071000>
         /devices/pci0000:00/0000:00:01.0/0000:01:00.0/host0
          last_reset=0 host_busy=96 host_failed=96 host_eh_scheduled=0
          shost_state=SHOST_RECOVERY
           hostt: qla2xxx   <struct scsi_qla_host 0xffff880211071740>
     *scsi7*  <struct Scsi_Host 0xffff880211076000>
         /devices/pci0000:00/0000:00:01.0/0000:01:00.1/host7
          last_reset=0 host_busy=26 host_failed=26 host_eh_scheduled=0
          shost_state=SHOST_RECOVERY
           hostt: qla2xxx   <struct scsi_qla_host 0xffff880211076740>
     *scsi3*  <struct Scsi_Host 0xffff880211175800>
         /devices/pci0000:00/0000:00:1f.2/ata3/host3
          last_reset=0 host_busy=0 host_failed=0 host_eh_scheduled=0
          shost_state=SHOST_RUNNING
           hostt: ahci   <shost_priv(shost) 0xffff880211175f40>
     *scsi5*  <struct Scsi_Host 0xffff880211176800>
         /devices/pci0000:00/0000:00:1f.2/ata5/host5
          last_reset=0 host_busy=0 host_failed=0 host_eh_scheduled=0
          shost_state=SHOST_RUNNING
           hostt: ahci   <shost_priv(shost) 0xffff880211176f40>

     ** Execution took   0.12s (real)   0.06s (CPU)
    crash>

Show all devices (-d)
---------------------

The '-d' option can be used to get more detailed information about the local
as well as the SAN devices present on system. It also prints information about
number of inflight IO requests on individual SCSI devices::

    crash> scsishow -d

    =============================================================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host3     ahci                               ffff880211175800                        0         ffff880211175f40

    DEV NAME          scsi_device             H:C:T:L          VENDOR/MODEL              DEVICE STATE               IOREQ-CNT  IODONE-CNT               IOERR-CNT
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
    sda               ffff880035789000        3:0:0:0          ATA      WDC WD3200AAKS-7 SDEV_RUNNING                   11676       11537  (139)	         6

    =============================================================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host5     ahci                               ffff880211176800                        0         ffff880211176f40

    DEV NAME          scsi_device             H:C:T:L          VENDOR/MODEL              DEVICE STATE               IOREQ-CNT  IODONE-CNT               IOERR-CNT
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
    sr0               ffff880035f32800        5:0:0:0          ATAPI    iHAS124   F      SDEV_RUNNING                     615         600  ( 15)	         3

    =============================================================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host0     qla2xxx                            ffff880211071000         ffff880035f33800         ffff880211071740

    DEV NAME          scsi_device             H:C:T:L          VENDOR/MODEL              DEVICE STATE               IOREQ-CNT  IODONE-CNT               IOERR-CNT
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
    sdb               ffff880211003000        0:0:0:0          LIO-ORG  block0           SDEV_RUNNING                    1029         997  ( 32)	         2
    sdc               ffff880211007800        0:0:0:25         LIO-ORG  block25          SDEV_RUNNING                     283         282  (  1)	         2
    sdd               ffff880035f35800        0:0:0:24         LIO-ORG  block24          SDEV_RUNNING                     284         283  (  1)	         2
    sde               ffff88003578b800        0:0:0:23         LIO-ORG  block23          SDEV_RUNNING                     283         282  (  1)	         2
    sdf               ffff8802111c9000        0:0:0:22         LIO-ORG  block22          SDEV_RUNNING                     289         288  (  1)	         2
    sdg               ffff8802111c9800        0:0:0:21         LIO-ORG  block21          SDEV_RUNNING                     313         312  (  1)	         2
    sdh               ffff8802111ca000        0:0:0:20         LIO-ORG  block20          SDEV_RUNNING                     364         354  ( 10)	         2
    sdj               ffff880035f36000        0:0:0:19         LIO-ORG  block19          SDEV_RUNNING                     319         318  (  1)	         2
    sdl               ffff880035f37000        0:0:0:18         LIO-ORG  block18          SDEV_RUNNING                     313         312  (  1)	         2
    sdn               ffff880035f37800        0:0:0:17         LIO-ORG  block17          SDEV_RUNNING                     361         351  ( 10)	         2
    sdp               ffff88003578d000        0:0:0:16         LIO-ORG  block16          SDEV_RUNNING                    1053         989  ( 64)	         2
    sdq               ffff880035f35000        0:0:0:15         LIO-ORG  block15          SDEV_RUNNING                     333         332  (  1)	         2
    sds               ffff880035f34800        0:0:0:14         LIO-ORG  block14          SDEV_RUNNING                     308         307  (  1)	         2
    sdu               ffff88003578f000        0:0:0:13         LIO-ORG  block13          SDEV_RUNNING                    1089        1080  (  9)	         2
    [...]
    =============================================================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host7     qla2xxx                            ffff880211076000         ffff88017c80d800         ffff880211076740

    DEV NAME          scsi_device             H:C:T:L          VENDOR/MODEL              DEVICE STATE               IOREQ-CNT  IODONE-CNT               IOERR-CNT
    -------------------------------------------------------------------------------------------------------------------------------------------------------------
    sdi               ffff88003578c000        7:0:0:0          LIO-ORG  block0           SDEV_RUNNING                     270         268  (  2)	         2
    sdk               ffff880035f36800        7:0:0:25         LIO-ORG  block25          SDEV_RUNNING                     268         266  (  2)	         2
    sdm               ffff8802111cc800        7:0:0:24         LIO-ORG  block24          SDEV_RUNNING                     269         267  (  2)	         2
    sdo               ffff88003578c800        7:0:0:23         LIO-ORG  block23          SDEV_RUNNING                     269         267  (  2)	         2
    sdr               ffff88003578e000        7:0:0:22         LIO-ORG  block22          SDEV_RUNNING                     321         319  (  2)	         2
    sdt               ffff88017c80e800        7:0:0:21         LIO-ORG  block21          SDEV_RUNNING                     320         318  (  2)	         2
    sdv               ffff88017c80f800        7:0:0:20         LIO-ORG  block20          SDEV_RUNNING                     294         292  (  2)	         2
    sdx               ffff88003578d800        7:0:0:19         LIO-ORG  block19          SDEV_RUNNING                     296         294  (  2)	         2
    [...]

Show all host bus adapters (optional -s option)
-----------------------------------------------

When scsishow program is executed with '-s' or no options, then it would by
default print details about each SCSI adapter connected to the system::

    crash> scsishow

    =========================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    -------------------------------------------------------------------------------------------------------------------------
    host1     ahci                               ffff880211172800                        0         ffff880211172f40

       DRIVER VERSION      : 3.0
       HOST BUSY           : 0
       HOST BLOCKED        : 0
       HOST FAILED         : 0
       SELF BLOCKED        : 0
       SHOST STATE         : SHOST_RUNNING
       MAX LUN             : 1
       CMD/LUN             : 1
       WORK Q NAME         : 
    [...]
    =========================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    -------------------------------------------------------------------------------------------------------------------------
    host0     qla2xxx                            ffff880211071000         ffff880035f33800         ffff880211071740

       DRIVER VERSION      : 8.07.00.38.07.4-k1
       HOST BUSY           : 96
       HOST BLOCKED        : 0
       HOST FAILED         : 96
       SELF BLOCKED        : 0
       SHOST STATE         : SHOST_RECOVERY
       MAX LUN             : 65535
       CMD/LUN             : 3
       WORK Q NAME         : scsi_wq_0
    =========================================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    -------------------------------------------------------------------------------------------------------------------------
    host7     qla2xxx                            ffff880211076000         ffff88017c80d800         ffff880211076740

       DRIVER VERSION      : 8.07.00.38.07.4-k1
       HOST BUSY           : 26
       HOST BLOCKED        : 0
       HOST FAILED         : 26
       SELF BLOCKED        : 0
       SHOST STATE         : SHOST_RECOVERY
       MAX LUN             : 65535
       CMD/LUN             : 3
       WORK Q NAME         : scsi_wq_7
    =========================================================================================================================
    [...]

Show all SCSI targets (-T)
--------------------------

This option prints the information about SCSI targets through which the
local, SAN devices are connected to system::

    crash> scsishow -T

    ===============================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host3     ahci                               ffff880211175800                        0         ffff880211175f40

    --------------------------------------------------------------------------------------------------------
    TARGET DEVICE   scsi_target          CHANNEL  ID     TARGET STATUS        TARGET_BUSY     TARGET_BLOCKED 
    target3:0:0     ffff880035c85c00         0     0     STARGET_RUNNING                0                  0
    [...]
    ===============================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host0     qla2xxx                            ffff880211071000         ffff880035f33800         ffff880211071740

    --------------------------------------------------------------------------------------------------------
    TARGET DEVICE   scsi_target          CHANNEL  ID     TARGET STATUS        TARGET_BUSY     TARGET_BLOCKED 
    target0:0:0     ffff880035d84400         0     0     STARGET_RUNNING                0                  0
    target0:0:1     ffff88020ee94800         0     1     STARGET_RUNNING                0                  0

    ===============================================================================================================
    HOST      DRIVER
    NAME      NAME                               Scsi_Host                shost_data               &.hostdata[0]           
    ---------------------------------------------------------------------------------------------------------------
    host7     qla2xxx                            ffff880211076000         ffff88017c80d800         ffff880211076740

    --------------------------------------------------------------------------------------------------------
    TARGET DEVICE   scsi_target          CHANNEL  ID     TARGET STATUS        TARGET_BUSY     TARGET_BLOCKED 
    target7:0:0     ffff8802111e0000         0     0     STARGET_RUNNING                0                  0
    target7:0:1     ffff880035632800         0     1     STARGET_RUNNING                0                  0
    [...] 

Show in-flight SCSI commands (-c)
---------------------------------

Users can quickly get the list of all in-flight SCSI commands pending on various
devices by this option. It also prints the timestamps when the command was
allocated (jiffies_at_alloc)::

    crash> scsishow -c
    scsi_cmnd ffff88009d796000 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295667099
    scsi_cmnd ffff8801c7a06fc0 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671515
    scsi_cmnd ffff8801c7a06e00 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671515
    scsi_cmnd ffff8801b970a000 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671516
    scsi_cmnd ffff8801e029f180 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671560
    scsi_cmnd ffff8801e029f500 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671560
    scsi_cmnd ffff8801e029f340 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671560
    scsi_cmnd ffff8801e029fdc0 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671562
    scsi_cmnd ffff8801e029e700 on scsi_device 0xffff880211003000 (0:0:0:0) jiffies_at_alloc: 4295671563
    [...]

Show commands queued in request queue of device (-q)
----------------------------------------------------

This option is similar to '-c' option, but it also prints even more detailed
information e.g. pointer to the associated request, bio structures, SCSI
command opcode, age of the SCSI command, sector number on which this IO was
issued, and the IO scheduler used by device::

    crash> scsishow -q

    =======================================================================================================================
        ### DEVICE : sda

            ---------------------------------------------------------------------------------------
            gendisk        	:  ffff880211f9c000	|	scsi_device 	:  ffff880035789000
            request_queue  	:  ffff880035280000	|	H:C:T:L       	:  3:0:0:0
            elevator_name  	:  cfq    		|	VENDOR/MODEL	:  ATA      WDC WD3200AAKS-7
            ---------------------------------------------------------------------------------------

         NO.       request              bio                  scsi_cmnd          OPCODE     COMMAND AGE          SECTOR
         -------------------------------------------------------------------------------------------------------------
                   <<< NO I/O REQUESTS FOUND ON THE DEVICE! >>>

    [...]
    =======================================================================================================================
        ### DEVICE : sdb

            ---------------------------------------------------------------------------------------
            gendisk        	:  ffff880211f9e400	|	scsi_device 	:  ffff880211003000
            request_queue  	:  ffff8800352891a0	|	H:C:T:L       	:  0:0:0:0
            elevator_name  	:  deadline    		|	VENDOR/MODEL	:  LIO-ORG  block0
            ---------------------------------------------------------------------------------------

         NO.       request              bio                  scsi_cmnd          OPCODE     COMMAND AGE          SECTOR
         -------------------------------------------------------------------------------------------------------------
           1       ffff880199373380     ffff88019ca63b10     ffff8801b37841c0   WRITE(10)    168078 ms          476928
           2       ffff8802007ad800     ffff8801bdf38810     ffff8801b9640e00   WRITE(10)    162804 ms          341960
           3       ffff880199372c00     ffff8801b52c9110     ffff8801b3784000   WRITE(10)    168078 ms         1104888
           4       ffff8800931ad680     ffff88009be3a110     ffff8801b9641dc0   WRITE(10)    162804 ms          342072
           5       ffff8800931ad080     ffff880093f5bb10     ffff8801b96401c0   WRITE(10)    162804 ms          342040
           6       ffff8800931acd80     ffff880093f5be10     ffff8801b9640380   WRITE(10)    162804 ms          342032
           7       ffff8800931ad380     ffff880093f5b810     ffff8801b9640000   WRITE(10)    162804 ms          342048
           8       ffff8800931ad980     ffff8801b56d4e10     ffff8801b9641c00   WRITE(10)    162804 ms          342080
           9       ffff8800931aca80     ffff880093f5b310     ffff8801b9640540   WRITE(10)    162804 ms          342016
          10       ffff8800931ac780     ffff8801ac6cb310     ffff8801b9640700   WRITE(10)    162804 ms          342008
          11       ffff880199373c80     ffff8801f6ae1f10     ffff8800982c9500   WRITE(10)    168097 ms          471888
          12       ffff880199372d80     ffff8801b4f4fc10     ffff8801e029f340   WRITE(10)    168108 ms          465568
          13       ffff880199373e00     ffff8801dfeb8610     ffff8801e029e700   WRITE(10)    168105 ms          467376
          14       ffff880199372000     ffff8801dfeb8510     ffff8801e029fdc0   WRITE(10)    168106 ms          466352
          15       ffff8800cd158000     ffff8801b4f4d510     ffff8801b970a000   WRITE(10)    168152 ms          463344
          16       ffff880095ba7080     ffff8801bc248500     ffff8801b3785880   READ(10)     168074 ms               0
          17       ffff880199373080     ffff8801f6aeab10     ffff8801b3784a80   WRITE(10)    168079 ms          474880
          18       ffff8800931ac180     ffff88019da2df10     ffff8801b9640a80   WRITE(10)    162804 ms          341976
          19       ffff880199373200     ffff8801f6aef210     ffff8801b3785180   WRITE(10)    168078 ms          475904
          20       ffff8801b92fd200     ffff8801b4f4bd10     ffff88009d796000   WRITE(10)    172569 ms          461472
    [...]

Show requests to SCSI devices (-r)
----------------------------------

This option is similar to '-c' and '-q', but also provides an address for
'struct request->special' pointer::

    crash> scsishow -r
    ffff880199373380 (0:0:0:0)     start_time: 4295666968 special: 0xffff8801b37841c0
    ffff8802007ad800 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b9640e00
    ffff880199372c00 (0:0:0:0)     start_time: 4295666968 special: 0xffff8801b3784000
    ffff8800931ad680 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b9641dc0
    ffff8800931ad080 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b96401c0
    ffff8800931acd80 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b9640380
    ffff8800931ad380 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b9640000
    ffff8800931ad980 (0:0:0:0)     start_time: 4295676864 special: 0xffff8801b9641c00
    [...]

Check for common SCSI issues (-\\-check)
----------------------------------------

The '-\\-check' option uses in-built heuristics to automatically review status
of SCSI adapters, devices, targets, and the error handling process
to verify if there are any issues that could contribute to the stalled IO
requests.

It also checks various flags associated with IO requests, SCSI adapters and
devices to verify if any specific error condition is leading the stalled IO
operations::

    crash> scsishow --check
    WARNING: Scsi_Host 0xffff880211071000 (host0) is running error recovery!
    WARNING: Scsi_Host 0xffff880211076000 (host7) is running error recovery!
    Warning: scsi_cmnd 0xffff88009d796000 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801c7a06fc0 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801c7a06e00 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801b970a000 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801e029f180 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801e029f500 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801e029f340 on scsi_device 0xffff880211003000 (0:0:0:0) older than its timeout: EH or stalled queue?
    [...]
    Warning: scsi_cmnd 0xffff8800962fe380 on scsi_device 0xffff88003578d000 (0:0:0:16) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801e029efc0 on scsi_device 0xffff88003578d000 (0:0:0:16) older than its timeout: EH or stalled queue?
    Error: cannot determine timeout!
    Warning: scsi_cmnd 0xffff880034ed6c40 on scsi_device 0xffff880035f35000 (0:0:0:15) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff880034ed7500 on scsi_device 0xffff880035f34800 (0:0:0:14) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff880093f5ea80 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8800982c8a80 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8800982c96c0 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8800982c8fc0 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8800982c88c0 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8800982c9a40 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801b9641180 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    Warning: scsi_cmnd 0xffff8801b9640fc0 on scsi_device 0xffff88003578f000 (0:0:0:13) older than its timeout: EH or stalled queue?
    [...]

Display time and state information for SCSI commands (-\\-time)
---------------------------------------------------------------

The '-\\-time' option provides even more information about the in-flight IO
reqests and SCSI commands. Along with the SCSI command age it also provides
details about when the corresponding 'request' structure  was allocated
(rq-alloc)::

    crash> scsishow --time
    scsi_cmnd ffff88009d796000 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138153 cmnd-alloc: -172569 rq-alloc: -172700
    scsi_cmnd ffff8801c7a06fc0 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138153 cmnd-alloc: -168153 rq-alloc: -172700
    scsi_cmnd ffff8801c7a06e00 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138152 cmnd-alloc: -168153 rq-alloc: -172700
    scsi_cmnd ffff8801b970a000 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138108 cmnd-alloc: -168152 rq-alloc: -172700
    scsi_cmnd ffff8801e029f180 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138108 cmnd-alloc: -168108 rq-alloc: -172700
    scsi_cmnd ffff8801e029f500 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138108 cmnd-alloc: -168108 rq-alloc: -172700
    scsi_cmnd ffff8801e029f340 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138106 cmnd-alloc: -168108 rq-alloc: -172700
    scsi_cmnd ffff8801e029fdc0 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138105 cmnd-alloc: -168106 rq-alloc: -172700
    scsi_cmnd ffff8801e029e700 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138104 cmnd-alloc: -168105 rq-alloc: -172700
    scsi_cmnd ffff8801e029e540 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138102 cmnd-alloc: -168104 rq-alloc: -172700
    scsi_cmnd ffff8801e029e380 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138101 cmnd-alloc: -168102 rq-alloc: -172700
    scsi_cmnd ffff8801e029fa40 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138100 cmnd-alloc: -168101 rq-alloc: -172700
    scsi_cmnd ffff8800982c8540 on scsi_device 0xffff880211003000 (0:0:0:0) is unknown, deadline: -138097 cmnd-alloc: -168100 rq-alloc: -172700
    [...]
    scsi_cmnd ffff8801ca736a80 on scsi_device 0xffff880035f37800 (0:0:0:17) is unknown, deadline: -138115 cmnd-alloc: -168115 rq-alloc: -168115
    scsi_cmnd ffff8801ca7368c0 on scsi_device 0xffff880035f37800 (0:0:0:17) is unknown, deadline: -138115 cmnd-alloc: -168115 rq-alloc: -168115
    scsi_cmnd ffff880034ed6700 on scsi_device 0xffff880035f37800 (0:0:0:17) is unknown, deadline: 29998 cmnd-alloc: -150904 rq-alloc: -150904
    scsi_cmnd ffff880093f5e8c0 on scsi_device 0xffff88003578d000 (0:0:0:16) is timeout, deadline: -87627 cmnd-alloc: -168159 rq-alloc: -168159
    scsi_cmnd ffff880093f5ec40 on scsi_device 0xffff88003578d000 (0:0:0:16) is timeout, deadline: -87627 cmnd-alloc: -168159 rq-alloc: -168159
    scsi_cmnd ffff880093f5ee00 on scsi_device 0xffff88003578d000 (0:0:0:16) is timeout, deadline: -87627 cmnd-alloc: -168159 rq-alloc: -168159
    [...]

The scsishow program by default logs all the values in hex format, so it is
not mandatory to use '--hex/-x' option with above options.
