Reviewing NFS server and client details (nfsshow)
=================================================

The nfsshow program available in PyKdump can be used to quickly
process NFS server and client information from the vmcores.

Options provided by nfsshow::

    crash> nfsshow -h
    usage: nfsshow [-h] [-a] [--server] [--client] [--rpctasks] [--decoderpctask DECODERPCTASK] [--nfsclient NFSCLIENT] [--maxrpctasks MAXRPCTASKS] [--locks] [--deferred]
                   [--pid [PID]] [--version] [-v]

    optional arguments:
      -h, --help            show this help message and exit
      -a, --all             print all
      --server              print info about this host as an NFS-server
      --client              print info about this host as an NFS-client
      --rpctasks            print RPC tasks
      --decoderpctask DECODERPCTASK
                            Decode RPC task at address
      --nfsclient NFSCLIENT
                            Print info about nfs_client at address
      --maxrpctasks MAXRPCTASKS
                            Maximum number of RPC tasks to print
      --locks               print NLM locks
      --deferred            Print Deferred Requests
      --pid [PID]           Try to find everything NFS-related for this pid
      --version             Print program version and exit
      -v                    verbose output

     ** Execution took   0.10s (real)   0.10s (CPU)
    crash>

* `Print all the NFS server/client information (-a)`_
* `Print NFS server specific information (-\\-server)`_
* `Print NFS client specific information (-\\-client)`_
* `Print RPC tasks (-\\-rpctasks)`_
* `Decode RPC task at specified address (-\\-decoderpctask)`_
* `Print info from nfs_client struct at specified address (-\\-nfsclient)`_
* `Maximum number of RPC tasks to print (-\\-maxrpctasks)`_
* `Print NLM locks (-\\-locks)`_
* `Print Deferred Requests (-\\-deferred)`_
* `Find NFS related information for pid (-\\-pid)`_

Print all the NFS server/client information (-a)
------------------------------------------------

Users can collect all the NFS server/client information from vmcore by
using a single option '-a'. It combines the output from all the
individual options and displays the summary.

For example, below is the output of using '-a' option on a vmcore
collected from NFS client. It shows NFS shares mounted on system, pointer
to nfs_client structure, NML locks, RPC tasks etc.::

    crash> nfsshow -a
    ********************  Host As A NFS-client  ********************
     -- 3 mounted shares, by flags/caps:
        1 shares with flags=<TCP|VER3>
        2 shares with flags=<>
        3 shares with caps=<READDIRPLUS>
       ---<struct nfs_server 0xffff88005c140800> 172.25.0.43:/fileshare1
           flags=<TCP|VER3>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 3.0
        --- <struct nfs_client 0xffff880077dafc00> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800356cc800> ... <sock_xprt 0xffff8800356cc800>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
     .... Stats for program  nfs
                    program  <struct rpc_program 0xffffffffc05a4120>
                     netcnt  0
                  netudpcnt  0
                  nettcpcnt  0
                 nettcpconn  0
                  netreconn  0
                     rpccnt  15996
                 rpcretrans  0
             rpcauthrefresh  15967
                 rpcgarbage  0
      ----Printing first 20 out of total 48 RPC Tasks ---------
          --- 8 RPC Clients ----
        --- <struct rpc_task 0xffff880079da4798>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
        --- <struct rpc_task 0xffff880079da4e98>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
        --- <struct rpc_task 0xffff880079da4b18>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
        --- <struct rpc_task 0xffff880079da5218>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
    [...]
    --- XPRT Info ---
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

    ********************  NLM(lockd) Info ********************
      -- Sockets Used by NLM
         -- Permanent Sockets
    	     <struct svc_sock 0xffff880077a13000> 
       tcp6  :::43161                   :::*                        LISTEN
    	     <struct svc_sock 0xffff880062daf000> 
       udp6  :::50703                   :::*                       st=7
    	     <struct svc_sock 0xffff880062dae000> 
       tcp   0.0.0.0:42096              0.0.0.0:*                   LISTEN
    	     <struct svc_sock 0xffff880062dad000> 
       udp   0.0.0.0:59726              0.0.0.0:*                  st=7

     ** Execution took   4.17s (real)   4.01s (CPU)
    crash>

Similar information from vmcore of NFS server::

    crash> nfsshow -a
    ********************  Host As A NFS-server  ********************
    -----IP Map (/proc/net/rpc/auth.unix.ip)------------
        #class              IP         domain

    ----- NFS Exports (/proc/net/rpc/nfsd.export)------------

    ----- NFS FH (/proc/net/rpc/nfsd.fh)------------
    #domain fsidtype fsid [path]

    -----GID Map (/proc/net/rpc/auth.unix.gid)------------
    #uid cnt: gids...

     ============ SVC Transports/Sockets ============

     *** sv_permsocks ***
    -------<struct svc_xprt 0xffff88005f364000>--------------svc_udp_class--------
      Local: ('::', 2049) Remote: (None, None)
            flags=
    -------<struct svc_xprt 0xffff88005f363000>--------------svc_tcp_class--------
      Local: ('::', 2049) Remote: (None, None)
            flags=XPT_CHNGBUF|XPT_DETACHED|XPT_LISTENER
    -------<struct svc_xprt 0xffff88005f367000>--------------svc_udp_class--------
      Local: ('0.0.0.0', 2049) Remote: (None, None)
            flags=
    -------<struct svc_xprt 0xffff88005f362000>--------------svc_tcp_class--------
      Local: ('0.0.0.0', 2049) Remote: (None, None)
            flags=XPT_CHNGBUF|XPT_DETACHED|XPT_LISTENER

     *** sv_tempsocks ***
    -------<struct svc_xprt 0xffff88007a7a1000>--------------svc_tcp_class--------
      Local: ('172.25.0.43', 2049) Remote: ('172.25.0.45', 769)
            flags=XPT_BUSY|XPT_DATA|XPT_TEMP|XPT_LISTENER
    -------<struct svc_xprt 0xffff880077806000>--------------svc_tcp_class--------
      Local: ('172.25.0.43', 2049) Remote: ('172.25.0.45', 726)
            flags=XPT_BUSY|XPT_DATA|XPT_TEMP|XPT_LISTENER
      ------- 0 RPC Tasks ---------
          --- 4 RPC Clients ----
     --- XPRT Info ---
    ********************  NLM(lockd) Info ********************
      -- Sockets Used by NLM
         -- Permanent Sockets
    	     <struct svc_sock 0xffff880034bb7000> 
       tcp6  :::34175                   :::*                        LISTEN
    	     <struct svc_sock 0xffff88005f365000> 
       udp6  :::53993                   :::*                       st=7
    	     <struct svc_sock 0xffff88005f361000> 
       tcp   0.0.0.0:42783              0.0.0.0:*                   LISTEN
    	     <struct svc_sock 0xffff880077802000> 
       udp   0.0.0.0:57925              0.0.0.0:*                  st=7

     ** Execution took   0.23s (real)   0.21s (CPU)
    crash>

Print NFS server specific information (-\\-server)
--------------------------------------------------

To retrieve NFS server specific information, use '-\\-server' option::

    crash> nfsshow --server
    ********************  Host As A NFS-server  ********************
    -----IP Map (/proc/net/rpc/auth.unix.ip)------------
        #class              IP         domain

    ----- NFS Exports (/proc/net/rpc/nfsd.export)------------

    ----- NFS FH (/proc/net/rpc/nfsd.fh)------------
    #domain fsidtype fsid [path]

    -----GID Map (/proc/net/rpc/auth.unix.gid)------------
    #uid cnt: gids...

     ============ SVC Transports/Sockets ============

     *** sv_permsocks ***
    -------<struct svc_xprt 0xffff88005f364000>--------------svc_udp_class--------
      Local: ('::', 2049) Remote: (None, None)
            flags=
    -------<struct svc_xprt 0xffff88005f363000>--------------svc_tcp_class--------
      Local: ('::', 2049) Remote: (None, None)
            flags=XPT_CHNGBUF|XPT_DETACHED|XPT_LISTENER
    -------<struct svc_xprt 0xffff88005f367000>--------------svc_udp_class--------
      Local: ('0.0.0.0', 2049) Remote: (None, None)
            flags=
    -------<struct svc_xprt 0xffff88005f362000>--------------svc_tcp_class--------
      Local: ('0.0.0.0', 2049) Remote: (None, None)
            flags=XPT_CHNGBUF|XPT_DETACHED|XPT_LISTENER

     *** sv_tempsocks ***
    -------<struct svc_xprt 0xffff88007a7a1000>--------------svc_tcp_class--------
      Local: ('172.25.0.43', 2049) Remote: ('172.25.0.45', 769)
            flags=XPT_BUSY|XPT_DATA|XPT_TEMP|XPT_LISTENER
    -------<struct svc_xprt 0xffff880077806000>--------------svc_tcp_class--------
      Local: ('172.25.0.43', 2049) Remote: ('172.25.0.45', 726)
            flags=XPT_BUSY|XPT_DATA|XPT_TEMP|XPT_LISTENER

     ** Execution took   3.39s (real)   3.38s (CPU)
    crash>

Print NFS client specific information (-\\-client)
--------------------------------------------------

To display a summary of information from a vmcore of NFS client system,
use '-\\-client'. It displays NFS shares mounted on system, NFS version
used to mount these shares, corresponding nfs_client struct pointer,
RPC tasks, NLM locks, etc.::

    crash> nfsshow --client
    ********************  Host As A NFS-client  ********************
     -- 3 mounted shares, by flags/caps:
        1 shares with flags=<TCP|VER3>
        2 shares with flags=<>
        3 shares with caps=<READDIRPLUS>
       ---<struct nfs_server 0xffff88005c140800> 172.25.0.43:/fileshare1
           flags=<TCP|VER3>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 3.0
        --- <struct nfs_client 0xffff880077dafc00> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800356cc800> ... <sock_xprt 0xffff8800356cc800>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
       --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
      .... Stats for program  nfs
                    program  <struct rpc_program 0xffffffffc05a4120>
                     netcnt  0
                  netudpcnt  0
                  nettcpcnt  0
                 nettcpconn  0
                  netreconn  0
                     rpccnt  15996
                 rpcretrans  0
             rpcauthrefresh  15967
                 rpcgarbage  0

     ** Execution took   0.11s (real)   0.10s (CPU)
    crash>

Use '-v' option to get more detailed information about each NFS mount.

The verbosity of output can be increased even further by using '-vv'::

    crash> nfsshow --client -v
    ********************  Host As A NFS-client  ********************
     -- 3 mounted shares, by flags/caps:
        1 shares with flags=<TCP|VER3>
        2 shares with flags=<>
        3 shares with caps=<READDIRPLUS>
       ---<struct nfs_server 0xffff88005c140800> 172.25.0.43:/fileshare1
           flags=<TCP|VER3>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 3.0
        --- <struct nfs_client 0xffff880077dafc00> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800356cc800> ... <sock_xprt 0xffff8800356cc800>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:769 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 4
            len(pending) queue is 4
            len(backlog) queue is 0
                 bind_count  1
              connect_count  2
              connect_start  4295462926
               connect_time  0
                      sends  5097
                      recvs  5094
                   bad_xids  0
                  max_slots  80
                      req_u  10170
                    bklog_u  0
                  sending_u  50833
                  pending_u  5073

       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
           Linux NFSv4.1 nfsclient1
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          Linux NFSv4.1 nfsclient1
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

      .... Stats for program  nfs
                    program  <struct rpc_program 0xffffffffc05a4120>
                     netcnt  0
                  netudpcnt  0
                  nettcpcnt  0
                 nettcpconn  0
                  netreconn  0
                     rpccnt  15996
                 rpcretrans  0
             rpcauthrefresh  15967
                 rpcgarbage  0
       --- <struct sunrpc_net 0xffff880035db5600> ---
      ip_map_cache/auth.unix.ip      <struct cache_detail 0xffff880035db5b00>
      unix_gid_cache/auth.unix.gid   <struct cache_detail 0xffff880079f8fe00>

     ** Execution took   0.24s (real)   0.24s (CPU)
    crash>

Output using 'nfsshow --client -vv'::

    crash> nfsshow --client -vv
    ********************  Host As A NFS-client  ********************
     -- 3 mounted shares, by flags/caps:
        1 shares with flags=<TCP|VER3>
        2 shares with flags=<>
        3 shares with caps=<READDIRPLUS>
       ---<struct nfs_server 0xffff88005c140800> 172.25.0.43:/fileshare1
           flags=<TCP|VER3>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 3.0
        --- <struct nfs_client 0xffff880077dafc00> 172.25.0.43 172.25.0.43
            ... <struct rpc_clnt 0xffff88007899f000>
          ... <rpc_xprt 0xffff8800356cc800> ... <sock_xprt 0xffff8800356cc800>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:769 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 4
            len(pending) queue is 4
            len(backlog) queue is 0
                 bind_count  1
              connect_count  2
              connect_start  4295462926
               connect_time  0
                      sends  5097
                      recvs  5094
                   bad_xids  0
                  max_slots  80
                      req_u  10170
                    bklog_u  0
                  sending_u  50833
                  pending_u  5073

       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          Linux NFSv4.1 nfsclient1
            ... <struct rpc_clnt 0xffff88007a131600>
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

    (struct nfs_client *)0xffff88005c3fe000
    NFS4 state information:
    - cl_state=0x0  
    NFS4 lease information:
    - cl_lease_time = 90000 (90 seconds), cl_last_renewal = 4295811067 (18 seconds ago), 
    - NFS4 lease is _NOT_ expired
    (struct nfs_server *)0xffff88005c141000
    - rsize = 262144, rpages = 64
    - wsize = 262144, wpages = 64
    - wtmult (server disk block size) = 512, bsize (server block size) = 0
    - dtsize (readdir size) = 32768
    - acregmin = 3000, acregmax = 60000, acdirmin = 30000, acdirmax = 60000
    - caps (capabilities) = 0x3ffdf NFS_CAP_READDIRPLUS NFS_CAP_HARDLINKS
           NFS_CAP_SYMLINKS NFS_CAP_ACLS NFS_CAP_ATOMIC_OPEN
           NFS_CAP_FILEID NFS_CAP_MODE NFS_CAP_NLINK NFS_CAP_OWNER
           NFS_CAP_OWNER_GROUP NFS_CAP_ATIME NFS_CAP_CTIME NFS_CAP_MTIME
           NFS_CAP_POSIX_LOCK NFS_CAP_UIDGID_NOMAP NFS_CAP_STATEID_NFSV41
           NFS_CAP_ATOMIC_OPEN_V1
    nfs_server.state_owners list:
    (struct nfs4_state_owner *)0xffff88007bfa1e00
    - so_flags = 0x0  
    nfs4_state_owner.so_states list:
    (struct nfs4_state *)0xffff880062de3c00
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 1 n_rdwr: 0
    (struct nfs4_state *)0xffff8800600323c0
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 2 n_rdwr: 0
    (struct nfs4_state *)0xffff880062de36c0
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 4 n_rdwr: 0
    (struct nfs4_state *)0xffff88005a2400c0
    - flags=0x0  
    - n_rdonly: 0 n_wronly: 0 n_rdwr: 0
    nfs_server.delegations list:
    (struct nfs_delegation *)0xffff88007beb1480
    - inode = 0xffff8800612daed0
    - type=0x1 FMODE_READ  
    - flags=0x0  
       ---<struct nfs_server 0xffff88005c141000> 172.25.0.43:/fileshare3
           flags=<>, caps=<READDIRPLUS> rsize=262144, wsize=262144
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          Linux NFSv4.1 nfsclient1
            ... <struct rpc_clnt 0xffff88007a131600>
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

    (struct nfs_client *)0xffff88005c3fe000
    NFS4 state information:
    - cl_state=0x0  
    NFS4 lease information:
    - cl_lease_time = 90000 (90 seconds), cl_last_renewal = 4295811067 (18 seconds ago), 
    - NFS4 lease is _NOT_ expired
    (struct nfs_server *)0xffff88005c141000
    - rsize = 262144, rpages = 64
    - wsize = 262144, wpages = 64
    - wtmult (server disk block size) = 512, bsize (server block size) = 0
    - dtsize (readdir size) = 32768
    - acregmin = 3000, acregmax = 60000, acdirmin = 30000, acdirmax = 60000
    - caps (capabilities) = 0x3ffdf NFS_CAP_READDIRPLUS NFS_CAP_HARDLINKS
           NFS_CAP_SYMLINKS NFS_CAP_ACLS NFS_CAP_ATOMIC_OPEN
           NFS_CAP_FILEID NFS_CAP_MODE NFS_CAP_NLINK NFS_CAP_OWNER
           NFS_CAP_OWNER_GROUP NFS_CAP_ATIME NFS_CAP_CTIME NFS_CAP_MTIME
           NFS_CAP_POSIX_LOCK NFS_CAP_UIDGID_NOMAP NFS_CAP_STATEID_NFSV41
           NFS_CAP_ATOMIC_OPEN_V1
    nfs_server.state_owners list:
    (struct nfs4_state_owner *)0xffff88007bfa1e00
    - so_flags = 0x0  
    nfs4_state_owner.so_states list:
    (struct nfs4_state *)0xffff880062de3c00
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 1 n_rdwr: 0
    (struct nfs4_state *)0xffff8800600323c0
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 2 n_rdwr: 0
    (struct nfs4_state *)0xffff880062de36c0
    - flags=0x514 NFS_OPEN_STATE NFS_O_WRONLY_STATE NFS_STATE_POSIX_LOCKS NFS_STATE_MAY_NOTIFY_LOCK  
    - n_rdonly: 0 n_wronly: 4 n_rdwr: 0
    (struct nfs4_state *)0xffff88005a2400c0
    - flags=0x0  
    - n_rdonly: 0 n_wronly: 0 n_rdwr: 0
    nfs_server.delegations list:
    (struct nfs_delegation *)0xffff88007beb1480
    - inode = 0xffff8800612daed0
    - type=0x1 FMODE_READ  
    - flags=0x0  
      .... Stats for program  nfs
                    program  <struct rpc_program 0xffffffffc05a4120>
                     netcnt  0
                  netudpcnt  0
                  nettcpcnt  0
                 nettcpconn  0
                  netreconn  0
                     rpccnt  15996
                 rpcretrans  0
             rpcauthrefresh  15967
                 rpcgarbage  0
       --- <struct sunrpc_net 0xffff880035db5600> ---
      ip_map_cache/auth.unix.ip      <struct cache_detail 0xffff880035db5b00>
      unix_gid_cache/auth.unix.gid   <struct cache_detail 0xffff880079f8fe00>

     ** Execution took   0.26s (real)   0.26s (CPU)
    crash>

Print RPC tasks (-\\-rpctasks)
------------------------------

To display the details about each RPC task, use '-\\-rpctasks'
option::

    crash> nfsshow --rpctasks
      ----Printing first 20 out of total 48 RPC Tasks ---------
          --- 8 RPC Clients ----
        --- <struct rpc_task 0xffff880079da4798>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
        --- <struct rpc_task 0xffff880079da4e98>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
        --- <struct rpc_task 0xffff880079da4b18>
    	    Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	    Owner pid=3556
    	      rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	      pmap_prog= 100003 , pmap_vers= 4
    	      started 18488 ms ago
              [...]
     --- XPRT Info ---
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago
            tcp 172.25.0.45:726 172.25.0.43:2049 ESTABLISHED
            len(binding) queue is 0
            len(sending) queue is 26
            len(pending) queue is 5
            len(backlog) queue is 0
                 bind_count  0
              connect_count  1
              connect_start  4295001290
               connect_time  0
                      sends  10869
                      recvs  10865
                   bad_xids  0
                  max_slots  31
                      req_u  28016
                    bklog_u  0
                  sending_u  76218
                  pending_u  17147

     ** Execution took   0.17s (real)   0.17s (CPU)
    crash>

Decode RPC task at specified address (-\\-decoderpctask)
--------------------------------------------------------

The '-\\-decoderpctask' option allows to retrieve information about
specific RPC task using a pointer for struct rpc_task.

For example, in above output there is a RPC task (pid=3556), with
rpc_task poiner 0xffff880079da4798. This pointer can be used as an
argument to '-\\-decoderpctask' to get more details about it::

    crash> nfsshow --decoderpctask 0xffff880079da4798
    	Protocol= 6  Server= 172.25.0.43 172.25.0.43
    	Owner pid=3556
    	  rpc_proc=1(NFSPROC4_COMPOUND) WRITE  tk_status=-11
    	  pmap_prog= 100003 , pmap_vers= 4
    	  started 18488 ms ago

     ** Execution took   0.10s (real)   0.10s (CPU)
    crash>

Print info from nfs_client struct at specified address (-\\-nfsclient)
----------------------------------------------------------------------

Similar to the above option to process information for specific RCP task,
the '-\\-nfsclient' option allows to process details about individual
NFS client. It takes nfs_client pointer as an argument::

    crash> nfsshow --nfsclient 0xffff88005c3fe000
           NFS version: 4.1
        --- <struct nfs_client 0xffff88005c3fe000> 172.25.0.43 172.25.0.43
          ... <rpc_xprt 0xffff8800791be000> ... <sock_xprt 0xffff8800791be000>
            state=XPRT_LOCKED|XPRT_CONNECTED|XPRT_BOUND
            last_used     17.6 s ago

     ** Execution took   0.11s (real)   0.11s (CPU)
    crash> 

Users can use '-v' option with both the above options to display
more verbose information about RPC task and NFS client.

Maximum number of RPC tasks to print (-\\-maxrpctasks)
------------------------------------------------------
<WIP>

Print NLM locks (-\\-locks)
---------------------------

To display the NLM lock information, use '-\\-locks'::

    crash> nfsshow --locks
    ********************  NLM(lockd) Info ********************
      -- Sockets Used by NLM
         -- Permanent Sockets
    	     <struct svc_sock 0xffff880077a13000> 
       tcp6  :::43161                   :::*                        LISTEN
    	     <struct svc_sock 0xffff880062daf000> 
       udp6  :::50703                   :::*                       st=7
    	     <struct svc_sock 0xffff880062dae000> 
       tcp   0.0.0.0:42096              0.0.0.0:*                   LISTEN
    	     <struct svc_sock 0xffff880062dad000> 
       udp   0.0.0.0:59726              0.0.0.0:*                  st=7

     ** Execution took   0.14s (real)   0.14s (CPU)
    crash>

Print Deferred Requests (-\\-deferred)
--------------------------------------
<WIP>

Find NFS related information for pid (-\\-pid)
----------------------------------------------

To process the NFS server or client specific information from a particular
process, use '-\\-pid'.

For example, the backtrace of following 'dd' task shows presence of NFS
specific function calls. We can use '-\\-pid' option with this process ID
to retrieve NFS related information from this process::

   crash> bt 3572
    PID: 3572   TASK: ffff88007c0daf70  CPU: 0   COMMAND: "dd"
     #0 [ffff8800571038e8] __schedule at ffffffff816ab2ac
     #1 [ffff880057103970] schedule at ffffffff816ab8a9
     #2 [ffff880057103980] rpc_wait_bit_killable at ffffffffc04378e4 [sunrpc]
     #3 [ffff8800571039a0] __wait_on_bit at ffffffff816a9405
     #4 [ffff8800571039e0] out_of_line_wait_on_bit at ffffffff816a94b1
     #5 [ffff880057103a58] __rpc_execute at ffffffffc04390d4 [sunrpc]
     #6 [ffff880057103ac0] rpc_execute at ffffffffc043a7b8 [sunrpc]
     #7 [ffff880057103af0] rpc_run_task at ffffffffc042a776 [sunrpc]
     #8 [ffff880057103b20] rpc_call_sync at ffffffffc042a8e0 [sunrpc]
     #9 [ffff880057103b80] nfs3_rpc_wrapper.constprop.11 at ffffffffc05c45eb [nfsv3]
    #10 [ffff880057103bb0] nfs3_proc_getattr at ffffffffc05c52c6 [nfsv3]
    #11 [ffff880057103bf8] __nfs_revalidate_inode at ffffffffc058e43f [nfs]
    #12 [ffff880057103c30] nfs_lookup_revalidate at ffffffffc0588879 [nfs]
    #13 [ffff880057103ca0] lookup_dcache at ffffffff8120dd6c
    #14 [ffff880057103ce0] do_last at ffffffff81211a29
    #15 [ffff880057103d80] path_openat at ffffffff81212af2
    #16 [ffff880057103e18] do_filp_open at ffffffff8121508b
    #17 [ffff880057103ee8] do_sys_open at ffffffff81201bc3
    #18 [ffff880057103f40] sys_open at ffffffff81201cde
    #19 [ffff880057103f50] system_call_fastpath at ffffffff816b89fd
        RIP: 00007f516ce2d750  RSP: 00007fffb8e14788  RFLAGS: 00010206
        RAX: 0000000000000002  RBX: 0000000000611640  RCX: ffffffff816b889d
        RDX: 00000000000001b6  RSI: 0000000000000241  RDI: 00007fffb8e1667c
        RBP: 0000000000000001   R8: 00007f516d3156b0   R9: 00007fffb8e16690
        R10: 00007fffb8e14380  R11: 0000000000000246  R12: 00007fffb8e1668e
        R13: 0000000000000000  R14: 00007fffb8e16688  R15: 00007fffb8e14a10
        ORIG_RAX: 0000000000000002  CS: 0033  SS: 002b
    crash>

    crash> nfsshow --pid 3572
    --- PID=3572 ---
     --- __rpc_execute
       <struct rpc_task 0xffff88007a2b4500>         
     --- rpc_execute
       <struct rpc_task 0xffff88007a2b4500>         
     --- nfs3_proc_getattr
       <struct nfs4_label 0x0>                      

     ** Execution took   5.08s (real)   5.07s (CPU)

    crash>

For another PID::

    crash> bt 3565
    PID: 3565   TASK: ffff880062d7eeb0  CPU: 0   COMMAND: "rm"
     #0 [ffff880058a1b798] __schedule at ffffffff816ab2ac
     #1 [ffff880058a1b820] schedule at ffffffff816ab8a9
     #2 [ffff880058a1b830] rpc_wait_bit_killable at ffffffffc04378e4 [sunrpc]
     #3 [ffff880058a1b850] __wait_on_bit at ffffffff816a9405
     #4 [ffff880058a1b890] out_of_line_wait_on_bit at ffffffff816a94b1
     #5 [ffff880058a1b908] __rpc_execute at ffffffffc04390d4 [sunrpc]
     #6 [ffff880058a1b970] rpc_execute at ffffffffc043a7b8 [sunrpc]
     #7 [ffff880058a1b9a0] rpc_run_task at ffffffffc042a776 [sunrpc]
     #8 [ffff880058a1b9d0] nfs4_call_sync_sequence at ffffffffc05d98c3 [nfsv4]
     #9 [ffff880058a1ba48] _nfs4_proc_lookup at ffffffffc05da55b [nfsv4]
    #10 [ffff880058a1bb10] nfs4_proc_lookup_common at ffffffffc05e8cb0 [nfsv4]
    #11 [ffff880058a1bb98] nfs4_proc_lookup at ffffffffc05e91b2 [nfsv4]
    #12 [ffff880058a1bbd0] nfs_lookup at ffffffffc0588de3 [nfs]
    #13 [ffff880058a1bc30] lookup_real at ffffffff8120d52d
    #14 [ffff880058a1bc50] __lookup_hash at ffffffff8120de02
    [...]

    crash> nfsshow --pid 3565
    --- PID=3565 ---
     --- __rpc_execute
       <struct rpc_task 0xffff880034755f00>         
     --- rpc_execute
       <struct rpc_task 0xffff880034755f00>         
     --- rpc_run_task
       <struct rpc_task_setup 0xffff880058a1b9f0>   
     --- nfs4_call_sync_sequence
       <struct nfs_server 0xffff88005c141000>       
     --- _nfs4_proc_lookup
       <struct rpc_clnt 0xffff880079721600> 

    ** Execution took   5.08s (real)   5.00 (CPU)
    crash>
