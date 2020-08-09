Extracting network and TCP/IP sockets information (xportshow)
=============================================================

The xportshow program available in PyKdump framework can be used to extract
detailed information about the network connections, sockets, routing table,
TCP retransmissions, various statistics, sysctl network parameters, etc.

Options provided by ‘xportshow’::

    crash> xportshow -h
    usage: xportshow [-h] [-a] [-v] [-r] [--program PROGRAM] [--pid [PID]] [--netfilter] [--softnet] [--summary] [-s] [-i] [--interface IF1] [--decode DECODE [DECODE ...]]
                     [--port PORT] [-l] [-t] [--tcpstate TCPSTATE] [--retransonly] [-u] [-w] [-x] [--sysctl] [--devpack] [--arp] [--rtcache] [--skbuffhead SKBUFFHEAD]
                     [--netns NETNS] [--version] [--everything]
    
    optional arguments:
      -h, --help            show this help message and exit
      -a                    print all sockets
      -v                    verbose output
      -r                    Print routing table. Adding -v prints all routing tables and policies
      --program PROGRAM     print sockets for cmdname
      --pid [PID]           print sockets for PID
      --netfilter           Print Netfilter Hooks
      --softnet             Print Softnet Queues
      --summary             Print A Summary
      -s, --statistics      Print Statistics
      -i                    Print Interface Info
      --interface IF1       Limit output to the specified interface only
      --decode DECODE [DECODE ...]
                            Decode iph/th/uh
      --port PORT           Limit output to the specified port (src or dst)
      -l, --listening       Print LISTEN sockets only
      -t                    Print TCP Info
      --tcpstate TCPSTATE   Limit display for this state only, e.g. SYN_SENT
      --retransonly         Show only TCP retransmissions
      -u, --udp             Print UDP Info
      -w, --raw             Print RAW Info
      -x, --unix            Print UNIX Info
      --sysctl              Print sysctl info for net.
      --devpack             Print dev_pack info
      --arp                 Print ARP & Neighbouring info
      --rtcache             Print the routing cache
      --skbuffhead SKBUFFHEAD
                            Print sk_buff_head
      --netns NETNS         Set net ns address
      --version             Print program version and exit
      --everything          Run all functions available for regression testing
    
     ** Execution took   2.35s (real)   2.24s (CPU)
    crash>

* `Print all sockets (-a)`_
* `Print routing table (-r)`_
* `Print the sockets used by programs (-\\-program, -\\-pid)`_
* `Print Netfilter Hooks (-\\-netfilter)`_
* `Print Softnet Queues (--softnet)`_
* `Print a summary of network connections (-\\-summary)`_
* `Show TCP, UDP, ICMP statistics (-\\-statistics)`_
* `Print network interface details (-i)`_
* `Decode iph/th/uh (-\\-decode)`_
* `Limit output to the specified port (-\\-port)`_
* `Print LISTEN sockets only (-l)`_
* `Print TCP sockets details (-t)`_
* `List the sockets with specific state (-\\-tcpstate)`_
* `Show only TCP retransmissions (-\\-retransonly)`_
* `Print UDP/RAW/UNIX sockets info (-u, -w, -x)`_
* `Print network sysctl parameters (-\\-sysctl)`_
* `Print dev_pack info (-\\-devpack)`_
* `Print ARP & Neighbouring info (-\\-arp)`_
* `Set net ns address (-\\-netns)`_
* `Run all functions in single command (-\\-everything)`_

Print all sockets (-a)
----------------------

The '-a' option lists the TCP, UDP and RAW sockets used on system::

    crash> xportshow -a
    tcp6  :::36590                   :::*                        LISTEN
    tcp   0.0.0.0:36463              0.0.0.0:*                   LISTEN
    tcp6  :::111                     :::*                        LISTEN
    tcp   0.0.0.0:111                0.0.0.0:*                   LISTEN
    tcp   0.0.0.0:42096              0.0.0.0:*                   LISTEN
    tcp   192.168.122.1:53           0.0.0.0:*                   LISTEN
    tcp6  :::22                      :::*                        LISTEN
    tcp   0.0.0.0:22                 0.0.0.0:*                   LISTEN
    tcp   127.0.0.1:631              0.0.0.0:*                   LISTEN
    tcp6  ::1:631                    :::*                        LISTEN
    tcp6  :::43161                   :::*                        LISTEN
    tcp6  ::1:25                     :::*                        LISTEN
    tcp   127.0.0.1:25               0.0.0.0:*                   LISTEN
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58504           ESTABLISHED
    udp6  :::908                     :::*                       st=7
    udp   0.0.0.0:908                0.0.0.0:*                  st=7
    udp6  :::39875                   :::*                       st=7
    udp   192.168.122.1:53           0.0.0.0:*                  st=7
    udp   0.0.0.0:67                 0.0.0.0:*                  st=7
    udp   0.0.0.0:68                 0.0.0.0:*                  st=7
    udp6  :::111                     :::*                       st=7
    udp   0.0.0.0:111                0.0.0.0:*                  st=7
    udp   0.0.0.0:42164              0.0.0.0:*                  st=7
    udp   0.0.0.0:5353               0.0.0.0:*                  st=7
    udp6  ::1:323                    :::*                       st=7
    udp   127.0.0.1:323              0.0.0.0:*                  st=7
    udp   0.0.0.0:39238              0.0.0.0:*                  st=7
    udp   0.0.0.0:59726              0.0.0.0:*                  st=7
    udp6  :::50703                   :::*                       st=7
    udp   127.0.0.1:809              0.0.0.0:*                  st=7
    raw6  :::58                      :::*                       st=7
    
     ** Execution took   0.39s (real)   0.32s (CPU)
    crash>

Using '-v' option provides more verbose information about each of these
sockets::

    crash> xportshow -a -v
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007ba9a200> 		TCP
    tcp6  :::36590                   :::*                        LISTEN
    	 family=PF_INET6
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d4f80> 		TCP
    tcp   0.0.0.0:36463              0.0.0.0:*                   LISTEN
    	 family=PF_INET
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007ba98000> 		TCP
    tcp6  :::111                     :::*                        LISTEN
    	 family=PF_INET6
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885c000> 		TCP
    tcp   0.0.0.0:111                0.0.0.0:*                   LISTEN
    	 family=PF_INET
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    [...]
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d5740> 		TCP
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=1077376  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=815224
    	rcvbuf=367360, sndbuf=1296896
    	rcv_tstamp=17.65 s, lsndtime=4.88 s ago,  RTO=12928 ms
        -- Retransmissions --
           retransmits=6, ca_state=TCP_CA_Loss, 17.43 s since first retransmission
    	   |user_data| 0xffff8800356cc800
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885ee80> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58504           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=13.46 s, lsndtime=13.46 s ago,  RTO=201 ms
    udp6  :::908                     :::*                       st=7
    ------------------------------------------------------------------------------
    [...]

Using '-vv' will provide even more detailed information e.g.  Write Queue,
skbuff, data length, retransmissions, etc.::

    crash> xportshow -a -vv
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007ba9a200> 		TCP
    tcp6  :::36590                   :::*                        LISTEN
    	 family=PF_INET6
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d4f80> 		TCP
    tcp   0.0.0.0:36463              0.0.0.0:*                   LISTEN
    	 family=PF_INET
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    [...]
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885f640> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
            --- Emulating __tcp_select_window ---
              rcv_mss=1376 free_space=184640 allowed_space=184640 full_space=183180
              rcv_ssthresh=45616, so free_space->45616 
              rcv_wscale=7
              window is not changed
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=9.94 s, lsndtime=9.94 s ago,  RTO=201 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d66c0> 		TCP
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=2323072  advmss=1448 rcv_ws=7 snd_ws=7
            --- Emulating __tcp_select_window ---
              rcv_mss=1448 free_space=183680 allowed_space=183680 full_space=182232
              rcv_ssthresh=182232, so free_space->182232 
              rcv_wscale=7
              window is not changed
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=995976
    	rcvbuf=367360, sndbuf=1584128
    	rcv_tstamp=17.64 s, lsndtime=0.76 s ago,  RTO=17088 ms
     **  Write Queue (skbuff, data length)
                     <struct sk_buff 0xffff880058aa6000> 1200
    				 <struct skb_shared_info 0xffff880079d4c6c0>
                     <struct sk_buff 0xffff880058aa6200> 1448
    				 <struct skb_shared_info 0xffff880079d4cec0>
                     <struct sk_buff 0xffff880058aa6400> 1448
    				 <struct skb_shared_info 0xffff880079d4d6c0>
                     <struct sk_buff 0xffff880058aa6600> 1448
    				 <struct skb_shared_info 0xffff880079d4dec0>
                     <struct sk_buff 0xffff880058aa6800> 1448
    				 <struct skb_shared_info 0xffff880079d4e6c0>
                     <struct sk_buff 0xffff880058aa6a00> 1448
    				 <struct skb_shared_info 0xffff880079d4eec0>
                     <struct sk_buff 0xffff880058aa6c00> 1448
    				 <struct skb_shared_info 0xffff880079d4f6c0>
                     <struct sk_buff 0xffff880058aa6e00> 1448
    				 <struct skb_shared_info 0xffff880079d4fec0>
                     <struct sk_buff 0xffff88007be23c00> 1448
    				 <struct skb_shared_info 0xffff880058a53ec0>
                     <struct sk_buff 0xffff88007be23600> 1448
    				 <struct skb_shared_info 0xffff880058a52ec0>
                     <struct sk_buff 0xffff88005a084800> 1448
    				 <struct skb_shared_info 0xffff880058a506c0>
                     <struct sk_buff 0xffff880057089c00> 1448
    				 <struct skb_shared_info 0xffff880079d4b6c0>
                     <struct sk_buff 0xffff880057089e00> 1448
    
                     [...]
                     <struct sk_buff 0xffff880079c8bc00> 1448
    				 <struct skb_shared_info 0xffff880058930ec0>
                     <struct sk_buff 0xffff880079c8be00> 1448
    				 <struct skb_shared_info 0xffff8800589316c0>
                     <struct sk_buff 0xffff880079c8c000> 1448
    				 <struct skb_shared_info 0xffff880058931ec0>
                     <struct sk_buff 0xffff880079c8c200> 1448
    				 <struct skb_shared_info 0xffff8800589326c0>
        -- Retransmissions --
           retransmits=6, ca_state=TCP_CA_Loss, 17.36 s since first retransmission
    	   |user_data| 0xffff8800791be000
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d5740> 		TCP
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=1077376  advmss=1448 rcv_ws=7 snd_ws=7
            --- Emulating __tcp_select_window ---
              rcv_mss=1448 free_space=183680 allowed_space=183680 full_space=182232
              rcv_ssthresh=182232, so free_space->182232 
              rcv_wscale=7
              window is not changed
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=815224
    	rcvbuf=367360, sndbuf=1296896
    	rcv_tstamp=17.65 s, lsndtime=4.88 s ago,  RTO=12928 ms
     **  Write Queue (skbuff, data length)
                     <struct sk_buff 0xffff88007b067400> 1448
    				 <struct skb_shared_info 0xffff880062e406c0>
                     <struct sk_buff 0xffff88007b067e00> 1448
    				 <struct skb_shared_info 0xffff880062e416c0>
                     <struct sk_buff 0xffff880077a7aa00> 1448
    				 <struct skb_shared_info 0xffff880062e436c0>
                     <struct sk_buff 0xffff880077a7a200> 1448
    				 <struct skb_shared_info 0xffff880062e43ec0>
                     <struct sk_buff 0xffff880077a7a800> 1448
    				 <struct skb_shared_info 0xffff880062e40ec0>
                     <struct sk_buff 0xffff88007bfaee00> 1448
    				 <struct skb_shared_info 0xffff880062e41ec0>
                     <struct sk_buff 0xffff88007bfae600> 1448
                     [...]

Print routing table (-r)
------------------------

The '-r' option prints routing table inforation. Users can increase the the
verbosity of these details using '-v'::

    crash> xportshow -r
    
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
    0.0.0.0         172.25.0.2      0.0.0.0         UG    100    0        0 ens3    
    172.25.0.0      0.0.0.0         255.255.0.0     U     100    0        0 ens3    
    192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0  
    
     ** Execution took   0.69s (real)   0.63s (CPU)
    crash> 
    
    crash> xportshow -r -v
    
    ==== <struct fib_table 0xffff88007a0fd540> RT_TABLE_MAIN
    
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
    0.0.0.0         172.25.0.2      0.0.0.0         UG    100    0        0 ens3    
    172.25.0.0      0.0.0.0         255.255.0.0     U     100    0        0 ens3    
    192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0  
    
    ==== <struct fib_table 0xffff880077beae40> RT_TABLE_LOCAL
    
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
    127.0.0.0       0.0.0.0         255.0.0.0       U     0      0        0 lo      
    127.0.0.1       0.0.0.0         255.255.255.255 UH    0      0        0 lo      
    172.25.0.45     0.0.0.0         255.255.255.255 UH    0      0        0 ens3    
    192.168.122.1   0.0.0.0         255.255.255.255 UH    0      0        0 virbr0  
    
    === Policy Rules
    -- <struct net 0xffffffff81ae2d80> <struct fib_rules_ops 0xffff88007c3933c0>
        -- <struct fib4_rule 0xffff88007c393480> RT_TABLE_LOCAL
    	src 0.0.0.0 srcmask 0.0.0.0 src_len 0
    	dst 0.0.0.0 dstmask 0.0.0.0 dst_len 0
    	action 1iifindex 0  oifindex 0 
        -- <struct fib4_rule 0xffff88007c393540> RT_TABLE_MAIN
    	src 0.0.0.0 srcmask 0.0.0.0 src_len 0
    	dst 0.0.0.0 dstmask 0.0.0.0 dst_len 0
    	action 1iifindex 0  oifindex 0 
        -- <struct fib4_rule 0xffff88007c393600> RT_TABLE_DEFAULT
    	src 0.0.0.0 srcmask 0.0.0.0 src_len 0
    	dst 0.0.0.0 dstmask 0.0.0.0 dst_len 0
    	action 1iifindex 0  oifindex 0 
    
     ** Execution took   0.24s (real)   0.17s (CPU)
    crash>

Print the sockets used by programs (-\\-program, -\\-pid)
---------------------------------------------------------

To get the details about sockets used by specific program, use '-\\-program'.

For example, to view the sockets associated with specific process in below list,
use 'xportshow -\\-program <process-name>'::

    crash> ps |less
    [...]
       2003   1700   0  ffff88000013dee0  IN   0.3  472080   5340  pool
       2005      1   0  ffff88005a388000  IN   0.3  419396   6304  gmain
       2009      1   0  ffff88005a38bf40  IN   0.3  419396   6304  gdbus
       2013      1   0  ffff88005a38af70  IN   0.1   54452   1304  spice-vdagentd
       2018   1862   0  ffff88005a3f0fd0  IN   0.2  302056   3560  ibus-engine-sim
       2021   1862   0  ffff88005a3f0000  IN   0.2  302056   3560  gmain
       2022   1862   0  ffff88005a3f3f40  IN   0.2  302056   3560  gdbus
       2085   1082   0  ffff88005a3f5ee0  IN   0.3  161008   5832  sshd
    [...]
    
Checking sockets used by 'spice-vdagentd'::
    
    crash> xportshow --program spice-vdagentd
    
    -----PID=2013  COMM=spice-vdagentd 
     fd     file              socket
     --     ----              ------
      3  0xffff88007af8b900  0xffff88007b64cf00  PF_FILE  SOCK_STREAM  UNIX 
      5  0xffff88005a1e0300  0xffff880061304500  PF_FILE  SOCK_STREAM  UNIX 
      6  0xffff88005c255500  0xffff880061304a00  PF_FILE  SOCK_STREAM  UNIX 
      8  0xffff88005c0a4f00  0xffff880061305400  PF_FILE  SOCK_DGRAM   UNIX 
    
    
     ** Execution took   0.16s (real)   0.09s (CPU)
    crash>
    crash> xportshow --program spice-vdagent
    
    -----PID=1999  COMM=spice-vdagent 
     fd     file              socket
     --     ----              ------
      3  0xffff88005d758200  0xffff8800612f2a00  PF_FILE  SOCK_STREAM  UNIX 
      4  0xffff88005c39c800  0xffff8800612f2c80  PF_FILE  SOCK_STREAM  UNIX 
      5  0xffff88005a1f3b00  0xffff880061293180  PF_FILE  SOCK_DGRAM   UNIX 
    
    
     ** Execution took   0.09s (real)   0.04s (CPU)
    crash>
    crash> xportshow --program ibus-engine-sim
    
    -----PID=2018  COMM=ibus-engine-sim   (3 threads)
     fd     file              socket
     --     ----              ------
      6  0xffff88005a1f3200  0xffff880061304c80  PF_FILE  SOCK_STREAM  UNIX 
    
    
     ** Execution took   0.09s (real)   0.03s (CPU)
    crash>

Similar information about the sockets used by a process can also be obtained
by  using '-\\-pid'::

    crash> xportshow --pid 2013
    
    -----PID=2013  COMM=spice-vdagentd 
     fd     file              socket
     --     ----              ------
      3  0xffff88007af8b900  0xffff88007b64cf00  PF_FILE  SOCK_STREAM  UNIX 
      5  0xffff88005a1e0300  0xffff880061304500  PF_FILE  SOCK_STREAM  UNIX 
      6  0xffff88005c255500  0xffff880061304a00  PF_FILE  SOCK_STREAM  UNIX 
      8  0xffff88005c0a4f00  0xffff880061305400  PF_FILE  SOCK_DGRAM   UNIX 
    
    
     ** Execution took   0.04s (real)   0.05s (CPU)
    crash>

The '-\\-pid' option also supports verbose flag (-v). It prints the
additional information e.g. name of the socket file being used by the process::

    crash> xportshow --pid 2013 -vv
    
    -----PID=2013  COMM=spice-vdagentd 
     fd     file              socket
     --     ----              ------
      3  0xffff88007af8b900  0xffff88007b64cf00  PF_FILE  SOCK_STREAM  UNIX 
         +-----------------------------------------------------------------
         |      state          i_ino   Path
         +-----------------------------------------------------------------
         |sock  LISTEN         16384   /var/run/spice-vdagentd/spice-vdagent-sock
         +-----------------------------------------------------------------
      5  0xffff88005a1e0300  0xffff880061304500  PF_FILE  SOCK_STREAM  UNIX 
         +-----------------------------------------------------------------
         |      state          i_ino   Path
         +-----------------------------------------------------------------
         |sock  ESTABLISHED    30768   
         +-----------------------------------------------------------------
         |peer  ESTABLISHED    30769   /run/dbus/system_bus_socket
         |    <struct file 0xffff88005a1e0600> <struct socket 0xffff880061304780>
         |    PID=741 <struct task_struct 0xffff88007ab54f10> CMD=dbus-daemon
         +-----------------------------------------------------------------
      6  0xffff88005c255500  0xffff880061304a00  PF_FILE  SOCK_STREAM  UNIX 
         +-----------------------------------------------------------------
         |      state          i_ino   Path
         +-----------------------------------------------------------------
         |sock  ESTABLISHED    30775   /var/run/spice-vdagentd/spice-vdagent-sock
         +-----------------------------------------------------------------
         |peer  ESTABLISHED    30523   
         |    <struct file 0xffff88005d758200> <struct socket 0xffff8800612f2a00>
         |    PID=1999 <struct task_struct 0xffff88000013af70> CMD=spice-vdagent
         +-----------------------------------------------------------------
      8  0xffff88005c0a4f00  0xffff880061305400  PF_FILE  SOCK_DGRAM   UNIX 
         +-----------------------------------------------------------------
         |      state          i_ino   Path
         +-----------------------------------------------------------------
         |sock  CLOSE          30847   
         +-----------------------------------------------------------------
         |peer  CLOSE          7160    /dev/log
         |    <struct file 0xffff880035c5fc00> <struct socket 0xffff88007b60e500>
         |    PID=1 <struct task_struct 0xffff88007c0d8000> CMD=systemd
         |    PID=509 <struct task_struct 0xffff880035d98fd0> CMD=systemd-journal
         +-----------------------------------------------------------------
    
    
     ** Execution took   0.22s (real)   0.15s (CPU)
    crash>

Print Netfilter Hooks (-\\-netfilter)
-------------------------------------

To view the netfilter hooks information, use '-\\-netfilter'::

    crash> xportshow --netfilter 
    NPROTO=13, NF_MAX_HOOKS=8
    =====PROTO= PF_INET
        NF_IP_PRE_ROUTING
    	prio=-400,  hook=ipv4_conntrack_defrag
    	prio=-200,  hook=ipv4_conntrack_in
    	prio=-150,  hook=iptable_mangle_hook
    	prio=-100,  hook=iptable_nat_ipv4_in
        NF_IP_LOCAL_IN
    	prio=-150,  hook=iptable_mangle_hook
    	prio=0,  hook=iptable_filter_hook
    	prio=100,  hook=iptable_nat_ipv4_fn
    	prio=300,  hook=ipv4_helper
    	prio=2147483647,  hook=ipv4_confirm
        NF_IP_FORWARD
    	prio=-225,  hook=selinux_ipv4_forward
    	prio=-150,  hook=iptable_mangle_hook
    	prio=0,  hook=iptable_filter_hook
        NF_IP_LOCAL_OUT
    	prio=-400,  hook=ipv4_conntrack_defrag
    	prio=-225,  hook=selinux_ipv4_output
    	prio=-200,  hook=ipv4_conntrack_local
    	prio=-150,  hook=iptable_mangle_hook
    	prio=-100,  hook=iptable_nat_ipv4_local_fn
    	prio=0,  hook=iptable_filter_hook
        NF_IP_POST_ROUTING
    	prio=-150,  hook=iptable_mangle_hook
    	prio=100,  hook=iptable_nat_ipv4_out
    	prio=225,  hook=selinux_ipv4_postroute
    	prio=300,  hook=ipv4_helper
    	prio=2147483647,  hook=ipv4_confirm
    =====PROTO= PF_BRIDGE
        NF_IP_LOCAL_IN
    	prio=-200,  hook=ebt_in_hook
        NF_IP_FORWARD
    	prio=-200,  hook=ebt_in_hook
        NF_IP_LOCAL_OUT
    	prio=200,  hook=ebt_out_hook
    =====PROTO= PF_INET6
        NF_IP_LOCAL_IN
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_FORWARD
    	prio=-225,  hook=selinux_ipv6_forward
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_LOCAL_OUT
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_POST_ROUTING
    	prio=225,  hook=selinux_ipv6_postroute
    
     ** Execution took   0.23s (real)   0.16s (CPU)
    crash>

Print Softnet Queues (--softnet)
--------------------------------

To print the per-cpu softnet data, use '-\\-softnet'::

    crash> xportshow --softnet
     --CPU=0
        ..input_pkt_queue has 0 elements
        ..Completion queue
    
     ** Execution took   0.03s (real)   0.05s (CPU)
    crash>

Print a summary of network connections (-\\-summary)
----------------------------------------------------

Users can get a detailed summary of n/w connections, TCP, UDP, RAW and Unix
sockets using '-\\-summary' option::

    crash> xportshow --summary
    TCP Connection Info
    -------------------
            ESTABLISHED      6
                 LISTEN     13
    			NAGLE disabled (TCP_NODELAY):     6
    			user_data set (NFS etc.):         4
    
      Unusual Situations:
        Doing Retransmission:          2  (run xportshow --retrans for details)
    
    UDP Connection Info
    -------------------
      16 UDP sockets, 0 in ESTABLISHED
    			user_data set (NFS etc.):         2
    
    Unix Connection Info
    ------------------------
            ESTABLISHED    405
                  CLOSE     50
                 LISTEN     59
    
    Raw sockets info
    --------------------
            ESTABLISHED      1
    
    Interfaces Info
    ---------------
      How long ago (in seconds) interfaces transmitted/received?
    	  Name        RX          TX
    	  ----    ----------    ---------
    	      lo       861.9         1161.5
    	    ens3       861.9            0.0
    	  virbr0       861.9          861.9
    	virbr0-nic       861.9         1127.6
    
     ** Execution took   0.20s (real)   0.17s (CPU)
    crash>

Show TCP, UDP, ICMP statistics (-\\-statistics)
-----------------------------------------------
::

    crash> xportshow --statistics
    
    -------------------- ip_statistics -------------------- 
    
                      InReceives               582574
                     InHdrErrors                    0
                    InAddrErrors                    0
                   ForwDatagrams                    0
                 InUnknownProtos                    0
                      InDiscards                    0
                      InDelivers               582572
                     OutRequests              2484936
                     OutDiscards                   84
                     OutNoRoutes                   65
                    ReasmTimeout                    0
                      ReasmReqds                    0
                        ReasmOKs                    0
                      ReasmFails                    0
                         FragOKs                    0
                       FragFails                    0
                     FragCreates                    0
    
    
    -------------------- icmp_statistics -------------------- 
    
      not implemented yet
    
    -------------------- tcp_statistics -------------------- 
    
                    RtoAlgorithm                    1
                          RtoMin                  200
                          RtoMax               120000
                         MaxConn                   -1
                     ActiveOpens                    7
                    PassiveOpens                    4
                    AttemptFails                    0
                     EstabResets                    0
                       CurrEstab                    6
                          InSegs               582175
                         OutSegs              2483329
                     RetransSegs                 1218
                          InErrs                    0
                         OutRsts                    0
                    InCsumErrors                    0
    
    
    -------------------- udp_statistics -------------------- 
    
                     InDatagrams                   42
                         NoPorts                  176
                        InErrors                    0
                    OutDatagrams                  208
                    RcvbufErrors                    0
                    SndbufErrors                    0
                    InCsumErrors                    0
    
    
    -------------------- net_statistics -------------------- 
    
                  SyncookiesSent                    0
                  SyncookiesRecv                    0
                SyncookiesFailed                    0
                   EmbryonicRsts                    0
                     PruneCalled                    0
                           [...]
           TCPACKSkippedTimeWait                    0
          TCPACKSkippedChallenge                    0
    
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash>

Print network interface details (-i)
------------------------------------

This option can be used to view the network interface details e.g. it's IP
address, MAC address, pointer to the 'net_device' structure and
net_device_flags::

    crash> xportshow -i 
    ====================== lo <struct net_device 0xffff88007c2ff000>  ============
    lo             127.0.0.1/8  mtu=65536                        LOOPBACK
      inet6 addr: ::1/128
        flags=<IFF_UP|IFF_LOOPBACK>
        features=<SG|HW_CSUM|HIGHDMA|FRAGLIST|VLAN_CHALLENGED|TSO|LLTX|UFO>
    ====================== ens3 <struct net_device 0xffff880077be5000>  ==========
    ens3        172.25.0.45/16  mtu=1500      52:54:00:c4:05:90  ETHER
      inet6 addr: fe80::a148:5899:c318:e13a/64
        flags=<IFF_UP|IFF_BROADCAST|IFF_MULTICAST>
        features=<HIGHDMA|HW_VLAN_TX|HW_VLAN_RX>
    ====================== virbr0 <struct net_device 0xffff88007afa2000>  ========
    virbr0    192.168.122.1/24  mtu=1500      52:54:00:66:46:70  ETHER
        flags=<IFF_UP|IFF_BROADCAST|IFF_MULTICAST>
        features=<SG|HW_CSUM|FRAGLIST|HW_VLAN_TX|TSO|LLTX|UFO>
    ====================== virbr0-nic <struct net_device 0xffff88007839c000>  ====
    virbr0-nic                      mtu=1500      52:54:00:66:46:70  ETHER
        flags=<IFF_BROADCAST|IFF_PROMISC|IFF_ALLMULTI|IFF_MULTICAST>
        features=<SG|FRAGLIST|HW_VLAN_TX|TSO|LLTX>
    
     ** Execution took   0.03s (real)   0.03s (CPU)
    crash>

Using verbose flag (-v) with '-i' provides even more detailed information
about the interfaces. These details include multicast address, link state,
mtu, network packets sent/received, etc::

    crash> xportshow -i -v
    ====================== lo <struct net_device 0xffff88007c2ff000>  ============
    lo             127.0.0.1/8  mtu=65536                        LOOPBACK
      inet6 addr: ::1/128
        flags=<IFF_UP|IFF_LOOPBACK>
        features=<SG|HW_CSUM|HIGHDMA|FRAGLIST|VLAN_CHALLENGED|TSO|LLTX|UFO>
     --------mcast------------
      inet:  224.0.0.1 users=1
      inet6: ff02::1
      inet6: ff01::1
     -------------------------
        LINK_STATE   3 (XOFF|START)
        open=<None>, stats=<None> mtu=65536 promisc=0
        	last_rx 4295829.24 s ago
        	trans_start 1161.46 s ago
    
                RX                -= Stats =-            TX          
         -----------------------                ------------------------
       --CPU 0                             
        rx_packets           356               tx_packets           356
        rx_bytes             28024             tx_bytes             28024
                                           
        ..................
        | tx queue 0
        ..................
        | rx_queue
    ====================== ens3 <struct net_device 0xffff880077be5000>  ==========
    ens3        172.25.0.45/16  mtu=1500      52:54:00:c4:05:90  ETHER
      inet6 addr: fe80::a148:5899:c318:e13a/64
        flags=<IFF_UP|IFF_BROADCAST|IFF_MULTICAST>
        features=<HIGHDMA|HW_VLAN_TX|HW_VLAN_RX>
     --------mcast------------
      link: 01:00:5e:00:00:01
      link: 33:33:00:00:00:01
      link: 33:33:ff:18:e1:3a
      link: 01:00:5e:00:00:fb
      inet:  224.0.0.251 users=1
      inet:  224.0.0.1 users=1
      inet6: ff02::1:ff18:e13a
      inet6: ff02::1
      inet6: ff01::1
     -------------------------
        LINK_STATE   3 (XOFF|START)
        open=<cp_open>, stats=<cp_get_stats> mtu=1500 promisc=0
        	last_rx 4295829.24 s ago
        	trans_start    0.00 s ago
        ..................
        | tx queue 0
        .............................................................
        <struct Qdisc 0xffff88007a0a8800> qlen=0
    	enqueue=<pfifo_fast_enqueue> dequeue=<pfifo_fast_dequeue>
    	qlen=0 backlog=0 drops=0 requeues=0 overlimits=0
    	== Bands ==
    	  sk_buff_head=0xffff88007a0a8948 len=0
    	  sk_buff_head=0xffff88007a0a8960 len=0
    	  sk_buff_head=0xffff88007a0a8978 len=0
        ..................
        | rx_queue
        .............................................................
        <struct Qdisc 0xffff88007a0a8800> qlen=0
    	enqueue=<pfifo_fast_enqueue> dequeue=<pfifo_fast_dequeue>
    	qlen=0 backlog=0 drops=0 requeues=0 overlimits=0
    	== Bands ==
    	  sk_buff_head=0xffff88007a0a8948 len=0
    	  sk_buff_head=0xffff88007a0a8960 len=0
    	  sk_buff_head=0xffff88007a0a8978 len=0
    ====================== virbr0 <struct net_device 0xffff88007afa2000>  ========
    virbr0    192.168.122.1/24  mtu=1500      52:54:00:66:46:70  ETHER
        flags=<IFF_UP|IFF_BROADCAST|IFF_MULTICAST>
        features=<SG|HW_CSUM|FRAGLIST|HW_VLAN_TX|TSO|LLTX|UFO>
     --------mcast------------
      link: 01:00:5e:00:00:01
      link: 01:00:5e:00:00:fb
      inet:  224.0.0.251 users=1
      inet:  224.0.0.1 users=1
      inet6: ff02::1
      inet6: ff01::1
     -------------------------
        LINK_STATE   7 (XOFF|START|PRESENT)
        open=<br_dev_open>, stats=<None> mtu=1500 promisc=0
        	last_rx 4295829.24 s ago
        ..................
        | tx queue 0
        .............................................................
        <struct Qdisc 0xffffffff81ae6bc0> qlen=0
    	enqueue=<noop_enqueue> dequeue=<noop_dequeue>
    	qlen=0 backlog=0 drops=0 requeues=0 overlimits=0
        ..................
        | rx_queue
    [...]

Decode iph/th/uh (-\\-decode)
-----------------------------

The contents of 'iphdr' structure can be decoded using '-\\-decode' option as
shown below::

    crash> xportshow --decode iph 0xffff882fdb99a810
    IPv4 <struct iphdr 0xffff882fdb99a810>
    tos=0 id=1742 fl=2 frag=0 ttl=1 proto=17 saddr=172.29.23.38 daddr=172.18.101.1

Limit output to the specified port (-\\-port)
---------------------------------------------

TCP socket details printed by xportshow program can also be filtered using the
port numbers.

For example, the following output will only show the TCP sockets used by port
2049::

    crash> xportshow -a --port 2049
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    [...]

Filtering the TCP sockets used by port 22::

    crash> xportshow -a --port 22
    tcp6  :::22                      :::*                        LISTEN
    tcp   0.0.0.0:22                 0.0.0.0:*                   LISTEN
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58504           ESTABLISHED
    udp6  :::908                     :::*                       st=7
    udp   0.0.0.0:908                0.0.0.0:*                  st=7
    udp6  :::39875                   :::*                       st=7
    udp   192.168.122.1:53           0.0.0.0:*                  st=7
    udp   0.0.0.0:67                 0.0.0.0:*                  st=7
    [...]

Print LISTEN sockets only (-l)
------------------------------

The '-l' option with xportshow only lists the sockets in 'LISTEN' state::

    crash> xportshow -l
    tcp6  :::36590                   :::*                        LISTEN
    tcp   0.0.0.0:36463              0.0.0.0:*                   LISTEN
    tcp6  :::111                     :::*                        LISTEN
    tcp   0.0.0.0:111                0.0.0.0:*                   LISTEN
    tcp   0.0.0.0:42096              0.0.0.0:*                   LISTEN
    tcp   192.168.122.1:53           0.0.0.0:*                   LISTEN
    tcp6  :::22                      :::*                        LISTEN
    tcp   0.0.0.0:22                 0.0.0.0:*                   LISTEN
    tcp   127.0.0.1:631              0.0.0.0:*                   LISTEN
    tcp6  ::1:631                    :::*                        LISTEN
    tcp6  :::43161                   :::*                        LISTEN
    tcp6  ::1:25                     :::*                        LISTEN
    tcp   127.0.0.1:25               0.0.0.0:*                   LISTEN
    udp6  :::908                     :::*                       st=7
    udp   0.0.0.0:908                0.0.0.0:*                  st=7
    udp6  :::39875                   :::*                       st=7
    udp   192.168.122.1:53           0.0.0.0:*                  st=7
    udp   0.0.0.0:67                 0.0.0.0:*                  st=7
    udp   0.0.0.0:68                 0.0.0.0:*                  st=7
    udp6  :::111                     :::*                       st=7
    udp   0.0.0.0:111                0.0.0.0:*                  st=7
    udp   0.0.0.0:42164              0.0.0.0:*                  st=7
    udp   0.0.0.0:5353               0.0.0.0:*                  st=7
    udp6  ::1:323                    :::*                       st=7
    udp   127.0.0.1:323              0.0.0.0:*                  st=7
    udp   0.0.0.0:39238              0.0.0.0:*                  st=7
    udp   0.0.0.0:59726              0.0.0.0:*                  st=7
    udp6  :::50703                   :::*                       st=7
    udp   127.0.0.1:809              0.0.0.0:*                  st=7
    raw6  :::58                      :::*                       st=7
    
     ** Execution took   0.07s (real)   0.07s (CPU)
    crash>

To get more verbose information about the sockets in 'LISTEN' state, use '-v'
::

    crash> xportshow -l -v
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007ba9a200> 		TCP
    tcp6  :::36590                   :::*                        LISTEN
    	 family=PF_INET6
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d4f80> 		TCP
    tcp   0.0.0.0:36463              0.0.0.0:*                   LISTEN
    	 family=PF_INET
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007ba98000> 		TCP
    tcp6  :::111                     :::*                        LISTEN
    	 family=PF_INET6
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885c000> 		TCP
    tcp   0.0.0.0:111                0.0.0.0:*                   LISTEN
    	 family=PF_INET
    	 backlog=0(128)
    	 max_qlen_log=8 qlen=0 qlen_young=0
    [...]

Print TCP sockets details (-t)
------------------------------

The '-t' option lists all the TCP sockets::

    crash> xportshow -t
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58504           ESTABLISHED
    [...]

To get more verbose information about the TCP sockets use '-v'::

    crash> xportshow -t -v
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d4000> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=7.12 s, lsndtime=7.12 s ago,  RTO=202 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d47c0> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    	windows: rcv=42880, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=0.00 s, lsndtime=75.70 s ago,  RTO=209 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885f640> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=9.94 s, lsndtime=9.94 s ago,  RTO=201 ms
    [...]

List the sockets with specific state (-\\-tcpstate)
---------------------------------------------------

The '-\\-tcpstate' option can be used to list the TCP sockets with matching
state.

For example, below command will only list the TCP sockets in ESTABLISHED
state::

    crash> xportshow --tcpstate ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    tcp   172.25.0.45:22             172.25.0.47:58504           ESTABLISHED
    
     ** Execution took   0.03s (real)   0.02s (CPU)

Similar to other options, users can use '-v' to get more verbose details of
sockets::

    crash> xportshow --tcpstate ESTABLISHED -v
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d4000> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58532           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=7.12 s, lsndtime=7.12 s ago,  RTO=202 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d47c0> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58538           ESTABLISHED
    	windows: rcv=42880, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=0.00 s, lsndtime=75.70 s ago,  RTO=209 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007885f640> 		TCP
    tcp   172.25.0.45:22             172.25.0.47:58530           ESTABLISHED
    	windows: rcv=45696, snd=64128  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=3 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=0
    	rcvbuf=369280, sndbuf=87040
    	rcv_tstamp=9.94 s, lsndtime=9.94 s ago,  RTO=201 ms
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d66c0> 		TCP
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=2323072  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=995976
    	rcvbuf=367360, sndbuf=1584128
    	rcv_tstamp=17.64 s, lsndtime=0.76 s ago,  RTO=17088 ms
        -- Retransmissions --
           retransmits=6, ca_state=TCP_CA_Loss, 17.36 s since first retransmission
    	   |user_data| 0xffff8800791be000
    [...]

Show only TCP retransmissions (-\\-retransonly)
-----------------------------------------------

To check the TCP retransmissions, use '-\\-retransonly'::

    crash> xportshow --retransonly
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
           retransmits=6, ca_state=TCP_CA_Loss, 17.36 s since first retransmission
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
           retransmits=6, ca_state=TCP_CA_Loss, 17.43 s since first retransmission
    
     ** Execution took   0.05s (real)   0.06s (CPU)
    crash>

Getting more verbose information using '-v' option::

    crash> xportshow --retransonly -v
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d66c0> 		TCP
    tcp   172.25.0.45:726            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=2323072  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=995976
    	rcvbuf=367360, sndbuf=1584128
    	rcv_tstamp=17.64 s, lsndtime=0.76 s ago,  RTO=17088 ms
        -- Retransmissions --
           retransmits=6, ca_state=TCP_CA_Loss, 17.36 s since first retransmission
    	   |user_data| 0xffff8800791be000
    ------------------------------------------------------------------------------
    <struct tcp_sock 0xffff88007a3d5740> 		TCP
    tcp   172.25.0.45:769            172.25.0.43:2049            ESTABLISHED
    	windows: rcv=182272, snd=1077376  advmss=1448 rcv_ws=7 snd_ws=7
    	nonagle=1 sack_ok=7 tstamp_ok=1
    	rmem_alloc=0, wmem_alloc=1
    	rx_queue=0, tx_queue=815224
    	rcvbuf=367360, sndbuf=1296896
    	rcv_tstamp=17.65 s, lsndtime=4.88 s ago,  RTO=12928 ms
        -- Retransmissions --
           retransmits=6, ca_state=TCP_CA_Loss, 17.43 s since first retransmission
    	   |user_data| 0xffff8800356cc800
    
     ** Execution took   0.04s (real)   0.04s (CPU)
    crash>

Print UDP/RAW/UNIX sockets info (-u, -w, -x)
--------------------------------------------

To print the UDP sockets used on system use '-u'::

    crash> xportshow -u
    udp6  ::1:38596                  ::1:38596                  ESTABLISHED
    udp6  ::1:40392                  ::1:40392                  ESTABLISHED
    udp6  ::1:47437                  ::1:47437                  ESTABLISHED
    udp6  ::1:35280                  ::1:35280                  ESTABLISHED
    udp6  ::1:35665                  ::1:35665                  ESTABLISHED
    udp6  ::1:59348                  ::1:59348                  ESTABLISHED
    [...]

To check more verbose information of UDP sockets::

    crash> xportshow -u -v
    udp6  ::1:38596                  ::1:38596                  ESTABLISHED
    ------------------------------------------------------------------------------
    <struct udp_sock 0xffff881bd7e2cc00> 		UDP
    	rx_queue=0, tx_queue=1
    	rcvbuf=21299200, sndbuf=21299200
    	pending=0, corkflag=0, len=0
    udp6  ::1:40392                  ::1:40392                  ESTABLISHED
    ------------------------------------------------------------------------------
    <struct udp_sock 0xffff88402ad9f000> 		UDP
    	rx_queue=0, tx_queue=1
    	rcvbuf=21299200, sndbuf=21299200
    	pending=0, corkflag=0, len=0
    udp6  ::1:47437                  ::1:47437                  ESTABLISHED
    [...]

Getting a list of Unix sockets using '-x' option::

    crash> xportshow -x
    unix   State          i_ino   Path
    ----------------------------------
    unix   CLOSE          12300   /run/systemd/shutdownd
    unix   CLOSE          20002   /var/run/chrony/chronyd.sock
    unix   CLOSE          7138    /run/systemd/notify
    unix   CLOSE          7140    /run/systemd/cgroups-agent
    unix   CLOSE          7158    /run/systemd/journal/socket
    unix   CLOSE          7160    /dev/log
    unix   ESTABLISHED    25890   
    unix   ESTABLISHED    28490   @/tmp/.X11-unix/X0
    unix   ESTABLISHED    20457   
    unix   CLOSE          13956   
    unix   ESTABLISHED    28061   
    unix   ESTABLISHED    30769   /run/dbus/system_bus_socket
    unix   ESTABLISHED    25891   
    unix   ESTABLISHED    24719   /run/systemd/journal/stdout
    unix   ESTABLISHED    20458   /run/dbus/system_bus_socket
    unix   ESTABLISHED    27566   @/tmp/.X11-unix/X0
    unix   ESTABLISHED    30829   @/tmp/dbus-rfPFUuaY
    unix   ESTABLISHED    28013   /run/systemd/journal/stdout
    unix   ESTABLISHED    25888   
    unix   ESTABLISHED    24718   
    unix   ESTABLISHED    28489   @/tmp/dbus-rfPFUuaY
    unix   ESTABLISHED    25942   
    unix   ESTABLISHED    28058   @/tmp/.X11-unix/X0
    unix   ESTABLISHED    30828   
    unix   ESTABLISHED    28488   
    unix   ESTABLISHED    25943   
    unix   ESTABLISHED    20755   /run/dbus/system_bus_socket
    [...]

Similarly, the details for RAW sockets can be obtained by using '-w'.

Print network sysctl parameters (-\\-sysctl)
--------------------------------------------

To get a full list of network related sysctl parameters, use '-\\-sysctl'::

    crash> xportshow --sysctl|head -100
    net.core.core.bpf_jit_enable                  0
    net.core.core.busy_poll                       0
    net.core.core.busy_read                       0
    net.core.core.default_qdisc                   (?)
    net.core.core.dev_weight                      64
    net.core.core.message_burst                   10
    net.core.core.message_cost                    5
    net.core.core.netdev_budget                   300
    net.core.core.netdev_max_backlog              1000
    net.core.core.netdev_rss_key                  0
    net.core.core.netdev_tstamp_prequeue          1
    net.core.core.optmem_max                      20480
    net.core.core.rmem_default                    212992
    net.core.core.rmem_max                        212992
    net.core.core.rps_sock_flow_entries           (?)
    net.core.core.somaxconn                       128
    net.core.core.warnings                        1
    net.core.core.wmem_default                    212992
    net.core.core.wmem_max                        212992
    net.core.core.xfrm_acq_expires                30
    net.core.core.xfrm_aevent_etime               10
    net.core.core.xfrm_aevent_rseqth              2
    net.core.core.xfrm_larval_drop                1
    net.core.ipv4.cipso_cache_bucket_size         10
    net.core.ipv4.cipso_cache_enable              1
    net.core.ipv4.cipso_rbm_optfmt                0
    net.core.ipv4.cipso_rbm_strictvalid           1
    net.core.ipv4.conf.all.accept_local           0
    net.core.ipv4.conf.all.accept_redirects       0
    net.core.ipv4.conf.all.accept_source_route    0
    net.core.ipv4.conf.all.arp_accept             0
    net.core.ipv4.conf.all.arp_announce           0
    net.core.ipv4.conf.all.arp_filter             0
    net.core.ipv4.conf.all.arp_ignore             0
    net.core.ipv4.conf.all.arp_notify             0
    net.core.ipv4.conf.all.bootp_relay            0
    net.core.ipv4.conf.all.disable_policy         0
    net.core.ipv4.conf.all.disable_xfrm           0
    net.core.ipv4.conf.all.force_igmp_version     0
    net.core.ipv4.conf.all.forwarding             1
    net.core.ipv4.conf.all.log_martians           0
    net.core.ipv4.conf.all.mc_forwarding          0
    net.core.ipv4.conf.all.medium_id              0
    net.core.ipv4.conf.all.promote_secondaries    1
    net.core.ipv4.conf.all.proxy_arp              0
    net.core.ipv4.conf.all.proxy_arp_pvlan        0
    net.core.ipv4.conf.all.route_localnet         0
    net.core.ipv4.conf.all.rp_filter              1
    net.core.ipv4.conf.all.secure_redirects       1
    net.core.ipv4.conf.all.send_redirects         1
    net.core.ipv4.conf.all.shared_media           1
    net.core.ipv4.conf.all.src_valid_mark         0
    net.core.ipv4.conf.all.tag                    0
    net.core.ipv4.conf.default.accept_local       0
    net.core.ipv4.conf.default.accept_redirects   1
    net.core.ipv4.conf.default.accept_source_route 0
    net.core.ipv4.conf.default.arp_accept         0
    net.core.ipv4.conf.default.arp_announce       0
    [...]
    net.core.ipv4.conf.default.src_valid_mark     0
    net.core.ipv4.conf.default.tag                0
    net.core.ipv4.conf.ens3.accept_local          0
    net.core.ipv4.conf.ens3.accept_redirects      1
    net.core.ipv4.conf.ens3.accept_source_route   0
    net.core.ipv4.conf.ens3.arp_accept            0
    net.core.ipv4.conf.ens3.arp_announce          0
    net.core.ipv4.conf.ens3.arp_filter            0
    net.core.ipv4.conf.ens3.arp_ignore            0
    net.core.ipv4.conf.ens3.arp_notify            0
    net.core.ipv4.conf.ens3.bootp_relay           0
    [...]

Print dev_pack info (-\\-devpack)
---------------------------------

The '-\\-devpack' option prints network packet details from the lists viz.
ptype_all and ptype_base containing protocol handlers for generic and
specific packet types::

    crash> xportshow --devpack
    --------ptype_all-------------------------------------------
    <struct packet_type 0xffff88007b233d80>
    	type=0x0003 dev=0xffff880077be5000 func=packet_rcv
    	    pid=850, command=dhclient
    
    --------ptype_base-------------------------------------------
    <struct packet_type 0xffffffff81b31240>  (bucket=0)
    	type=0x0800 dev=0x0 func=ip_rcv
    <struct packet_type 0xffffffffc04a8020>  (bucket=1)
    	type=0x0011 dev=0x0 func=llc_rcv
    <struct packet_type 0xffffffffc04a8080>  (bucket=4)
    	type=0x0004 dev=0x0 func=llc_rcv
    <struct packet_type 0xffff880077800d80>  (bucket=6)
    	type=0x0806 dev=0xffff88007afa2000 func=packet_rcv
    <struct packet_type 0xffffffff81b311a0>  (bucket=6)
    	type=0x0806 dev=0x0 func=arp_rcv
    <struct packet_type 0xffffffff81b31580>  (bucket=13)
    	type=0x86dd dev=0x0 func=ipv6_rcv
    
     ** Execution took   0.07s (real)   0.07s (CPU)
    crash>

Print ARP & Neighbouring info (-\\-arp)
---------------------------------------

Users can get the ARP table data using '-\\-arp' option::

    crash> xportshow --arp
    === <struct neigh_table 0xffffffff81aee080> PF_INET6 nd_tbl
    IP ADDRESS        HW TYPE    HW ADDRESS           DEVICE  STATE
    ----------        -------    ----------           ------  -----
    ff02::1:ff18:e13a  ETHER      33:33:ff:18:e1:3a    ens3    NOARP
    ff02::2           ETHER      33:33:00:00:00:02    ens3    NOARP
    ff02::16          ETHER      33:33:00:00:00:16    ens3    NOARP
    
    === <struct neigh_table 0xffffffff81ae97a0> PF_INET arp_tbl
    IP ADDRESS        HW TYPE    HW ADDRESS           DEVICE  STATE
    ----------        -------    ----------           ------  -----
    224.0.0.22        ETHER      01:00:5e:00:00:16    ens3    NOARP
    172.25.0.43       ETHER      52:54:00:81:02:2f    ens3    REACHABLE
    224.0.0.22        ETHER      01:00:5e:00:00:16    virbr0  NOARP
    172.25.0.47       ETHER      e8:6a:64:a3:72:4b    ens3    REACHABLE
    224.0.0.251       ETHER      01:00:5e:00:00:fb    ens3    NOARP
    127.0.0.1         LOOPBACK   00:00:00:00:00:00    lo      NOARP
    224.0.0.251       ETHER      01:00:5e:00:00:fb    virbr0  NOARP
    172.25.0.2        ETHER      40:8d:5c:c4:9e:72    ens3    STALE
    
     ** Execution took   0.20s (real)   0.20s (CPU)
    crash>

Use verbose (-v) flag to view more detailed information e.g. pointer to
struct neighbour, neigh_tableand arp_queue_len::

    crash> xportshow --arp -v
    === <struct neigh_table 0xffffffff81aee080> PF_INET6 nd_tbl
    IP ADDRESS        HW TYPE    HW ADDRESS           DEVICE  STATE
    ----------        -------    ----------           ------  -----
    ff02::1:ff18:e13a  ETHER      33:33:ff:18:e1:3a    ens3    NOARP
       <struct neighbour 0xffff88007a1c1c00>  arp_queue_len=0
    ------------------------------------------------------------------------------
    ff02::2           ETHER      33:33:00:00:00:02    ens3    NOARP
       <struct neighbour 0xffff88007ac01000>  arp_queue_len=0
    ------------------------------------------------------------------------------
    ff02::16          ETHER      33:33:00:00:00:16    ens3    NOARP
       <struct neighbour 0xffff88007a0f1c00>  arp_queue_len=0
    ------------------------------------------------------------------------------
    
    === <struct neigh_table 0xffffffff81ae97a0> PF_INET arp_tbl
    IP ADDRESS        HW TYPE    HW ADDRESS           DEVICE  STATE
    ----------        -------    ----------           ------  -----
    224.0.0.22        ETHER      01:00:5e:00:00:16    ens3    NOARP
       <struct neighbour 0xffff880035737c00>  arp_queue_len=0
    ------------------------------------------------------------------------------
    172.25.0.43       ETHER      52:54:00:81:02:2f    ens3    REACHABLE
       <struct neighbour 0xffff88007a743800>  arp_queue_len=0
    ------------------------------------------------------------------------------
    224.0.0.22        ETHER      01:00:5e:00:00:16    virbr0  NOARP
       <struct neighbour 0xffff88007b236a00>  arp_queue_len=0
    ------------------------------------------------------------------------------
    172.25.0.47       ETHER      e8:6a:64:a3:72:4b    ens3    REACHABLE
       <struct neighbour 0xffff88005a149600>  arp_queue_len=0
    ------------------------------------------------------------------------------
    224.0.0.251       ETHER      01:00:5e:00:00:fb    ens3    NOARP
       <struct neighbour 0xffff88007a114600>  arp_queue_len=0
    ------------------------------------------------------------------------------
    127.0.0.1         LOOPBACK   00:00:00:00:00:00    lo      NOARP
       <struct neighbour 0xffff8800790df800>  arp_queue_len=0
    ------------------------------------------------------------------------------
    224.0.0.251       ETHER      01:00:5e:00:00:fb    virbr0  NOARP
       <struct neighbour 0xffff88007b271400>  arp_queue_len=0
    ------------------------------------------------------------------------------
    172.25.0.2        ETHER      40:8d:5c:c4:9e:72    ens3    STALE
       <struct neighbour 0xffff88007a6a0400>  arp_queue_len=0
    ------------------------------------------------------------------------------
    
     ** Execution took   0.03s (real)   0.05s (CPU)
    crash>

Set net ns address (-\\-netns)
------------------------------

The netns (network namespace) address can be changed using '-\\-netns' option
as shown below::

    crash> xportshow --netns 0xffffffff81ae2d80
     *=*=* Using <struct net 0xffffffff81ae2d80 *=*=*
    
     ** Execution took   0.01s (real)   0.01s (CPU)
    crash>
    crash> xportshow --netns 0xffff88007bbc8000
     *=*=* Using <struct net 0xffff88007bbc8000 *=*=*
    
     ** Execution took   0.01s (real)   0.01s (CPU)
    crash>

The xportshow program also verifies if the mentioned netns address is valid or
not. In case of any invalid address, it will just log an error and refuse to
change the network namespace::

    crash> xportshow --netns 0xffff88007bbc8010
    Invalid net ns 0xffff88007bbc8010
    
     ** Execution took   0.01s (real)   0.01s (CPU)
    crash>

Run all functions in single command (-\\-everything)
----------------------------------------------------

Users can also run all the above options in single command by using
'-\\-everything'::

    crash> xportshow --everything | head -100
    NPROTO=13, NF_MAX_HOOKS=8
    =====PROTO= PF_INET
        NF_IP_PRE_ROUTING
    	prio=-400,  hook=ipv4_conntrack_defrag
    	prio=-200,  hook=ipv4_conntrack_in
    	prio=-150,  hook=iptable_mangle_hook
    	prio=-100,  hook=iptable_nat_ipv4_in
        NF_IP_LOCAL_IN
    	prio=-150,  hook=iptable_mangle_hook
    	prio=0,  hook=iptable_filter_hook
    	prio=100,  hook=iptable_nat_ipv4_fn
    	prio=300,  hook=ipv4_helper
    	prio=2147483647,  hook=ipv4_confirm
        NF_IP_FORWARD
    	prio=-225,  hook=selinux_ipv4_forward
    	prio=-150,  hook=iptable_mangle_hook
    	prio=0,  hook=iptable_filter_hook
        NF_IP_LOCAL_OUT
    	prio=-400,  hook=ipv4_conntrack_defrag
    	prio=-225,  hook=selinux_ipv4_output
    	prio=-200,  hook=ipv4_conntrack_local
    	prio=-150,  hook=iptable_mangle_hook
    	prio=-100,  hook=iptable_nat_ipv4_local_fn
    	prio=0,  hook=iptable_filter_hook
        NF_IP_POST_ROUTING
    	prio=-150,  hook=iptable_mangle_hook
    	prio=100,  hook=iptable_nat_ipv4_out
    	prio=225,  hook=selinux_ipv4_postroute
    	prio=300,  hook=ipv4_helper
    	prio=2147483647,  hook=ipv4_confirm
    =====PROTO= PF_BRIDGE
        NF_IP_LOCAL_IN
    	prio=-200,  hook=ebt_in_hook
        NF_IP_FORWARD
    	prio=-200,  hook=ebt_in_hook
        NF_IP_LOCAL_OUT
    	prio=200,  hook=ebt_out_hook
    =====PROTO= PF_INET6
        NF_IP_LOCAL_IN
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_FORWARD
    	prio=-225,  hook=selinux_ipv6_forward
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_LOCAL_OUT
    	prio=0,  hook=ip6table_filter_hook
        NF_IP_POST_ROUTING
    	prio=225,  hook=selinux_ipv6_postroute
    net.core.core.bpf_jit_enable                  0
    net.core.core.busy_poll                       0
    net.core.core.busy_read                       0
    net.core.core.default_qdisc                   (?)
    net.core.core.dev_weight                      64
    net.core.core.message_burst                   10
    net.core.core.message_cost                    5
    net.core.core.netdev_budget                   300
    net.core.core.netdev_max_backlog              1000
    net.core.core.netdev_rss_key                  0
    net.core.core.netdev_tstamp_prequeue          1
    [...]
