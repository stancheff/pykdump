Getting hung task details (hanginfo)
====================================

The hanginfo program available in PyKdump framework provides below options to
retrieve more information about the processes stuck in UN (un-interruptible)
::

    crash> hanginfo -h
    Usage: hanginfo [options]

    Options:
      -h, --help         show this help message and exit
      -v                 verbose output
      --version          Print program version and exit
      --maxpids=MAXPIDS  Maximum number of PIDs to print
      --sortbypid        Sort by pid (the default is by ran_ago)
      --syslogger        Print info about hangs on AF_UNIX sockets (such as used by syslogd
      --tree             Print tree of resources owners  (experimental!)
      --saphana          Print recommendations for SAP HANA specific hangs

     ** Execution took   0.02s (real)   0.02s (CPU)
    crash>

* `Maximum number of PIDs to print (-\\-maxpids=MAXPIDS)`_
* `Sort by pid (-\\-sortbypid)`_
* `Print info about hangs on AF_UNIX sockets (-\\-syslogger)`_
* `Print tree of resources owners (-\\-tree)`_
* `Print recommendations for SAP HANA specific hangs (-\\-saphana)`_

Maximum number of PIDs to print (-\\-maxpids=MAXPIDS)
-----------------------------------------------------

Running hanginfo program without any options prints the information about
all the hung tasks. These details include the last function call after which
the process was stuck, how long it was in UN state etc::

    crash> hanginfo
     *** UNINTERRUPTIBLE threads, classified ***

     ================== Waiting in io_schedule ==================
        ... 19 pids. Youngest,oldest: 11643, 11452  Ran ms ago: 1, 172493
            printing 10 out of 19
            sorted by ran_ago, youngest first
          [11643, 11644, 11646, 7018, 7030, <9 skipped>, 11428, 11450,
           11451, 11446, 11452]

     =============== Waiting in schedule_timeout ================
        ... 2 pids. Youngest,oldest: 308, 355  Ran ms ago: 523, 2598
            sorted by ran_ago, youngest first
          [308, 355]

    *** System activities other threads are waiting for ***
      --- Doing schedule_timeout ---
    {355, 308}
      --- Doing io_schedule ---
    {11459, 7314, 11643, 7317, 11644, 11428, 7033, 7015, 7018, 7021, 7024, 7027, 11446, 7030, 11449, 11450, 11451, 11452, 11646}


    +++WARNING+++ Possible hang

    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        Possible hang
    ------------------------------------------------------------------------------

     ** Execution took   0.19s (real)   0.19s (CPU)
    crash>

Users can choose to limit the number of processes displayed in output by
using '-\\-maxpids=MAXPIDS' option.

For example, use '-\\-maxpids=5' to limit the sorted list of hung tasks to
5 processes only::

    crash> hanginfo --maxpids=5
     *** UNINTERRUPTIBLE threads, classified ***

     ================== Waiting in io_schedule ==================
        ... 19 pids. Youngest,oldest: 11643, 11452  Ran ms ago: 1, 172493
            printing 5 out of 19
            sorted by ran_ago, youngest first
          [11643, 11644, <14 skipped>, 11451, 11446, 11452]		<--- Only 5 PIDs are printed from the sorted list of hung tasks

     =============== Waiting in schedule_timeout ================
        ... 2 pids. Youngest,oldest: 308, 355  Ran ms ago: 523, 2598
            sorted by ran_ago, youngest first
          [308, 355]

    *** System activities other threads are waiting for ***
      --- Doing schedule_timeout ---
    {355, 308}
      --- Doing io_schedule ---
    {11459, 7314, 11643, 7317, 11644, 11428, 7033, 7015, 7018, 7021, 7024, 7027, 11446, 7030, 11449, 11450, 11451, 11452, 11646}


    +++WARNING+++ Possible hang

    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        Possible hang
    ------------------------------------------------------------------------------

     ** Execution took   0.19s (real)   0.19s (CPU)
    crash>

Sort by pid (-\\-sortbypid)
---------------------------

The hanginfo program by default sorts the processes as per the amount of they
were in UN (un-interruptible) state. To sort the process information as per
their PIDs, use '-\\-sortbypid'::

    crash> hanginfo --sortbypid
     *** UNINTERRUPTIBLE threads, classified ***

     ================== Waiting in io_schedule ==================
        ... 19 pids. Youngest,oldest: 11643, 11452  Ran ms ago: 1, 172493
            printing 10 out of 19
            sorted by pid
          [7015, 7018, 7021, 7024, 7027, ..., 11452, 11459, 11643, 11644,   <--- Sorted as per the PIDs
           11646]

     =============== Waiting in schedule_timeout ================
        ... 2 pids. Youngest,oldest: 308, 355  Ran ms ago: 523, 2598
            sorted by pid
          [308, 355]

    *** System activities other threads are waiting for ***
      --- Doing schedule_timeout ---
    {355, 308}
      --- Doing io_schedule ---
    {11459, 7314, 11643, 7317, 11644, 11428, 7033, 7015, 7018, 7021, 7024, 7027, 11446, 7030, 11449, 11450, 11451, 11452, 11646}


    +++WARNING+++ Possible hang

    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        Possible hang
    ------------------------------------------------------------------------------

     ** Execution took   0.20s (real)   0.19s (CPU)
    crash>


Print info about hangs on AF_UNIX sockets (-\\-syslogger)
---------------------------------------------------------

WIP

Print tree of resources owners (-\\-tree)
-----------------------------------------

The '-\\-tree' option with hanginfo program prints graphical representation
of the processes waiting for specific operations::

    crash> hanginfo --tree
     *** UNINTERRUPTIBLE threads, classified ***

    [...]

    +++WARNING+++ Possible hang
    ------------------------------------------------------------------------------
     ┌───────────┐
     │io_schedule│
     └─┬─────────┘
       │ ┌─────────────────────────────┐
       │ │7015,7018,7021,7024,7027     │
       │ │7030,7033,7314,7317,11428    │
       └─┤11446,11449,11450,11451,11452│
         │11459,11643,11644,11646      │
         └─────────────────────────────┘
    ------------------------------------------------------------------------------
     ┌────────────────┐
     │schedule_timeout│
     └─┬──────────────┘
       │ ┌───────┐
       └─┤308,355│
         └───────┘

    ******************************************************************************
    ************************ A Summary Of Problems Found *************************
    ******************************************************************************
    -------------------- A list of all +++WARNING+++ messages --------------------
        Possible hang
    ------------------------------------------------------------------------------

     ** Execution took   0.17s (real)   0.17s (CPU)
    crash>

Print recommendations for SAP HANA specific hangs (-\\-saphana)
---------------------------------------------------------------

WIP
