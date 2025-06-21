from scapy.all import *

server_ip = "192.168.1.1"
offered_ip = "192.168.1.123"
subnet_mask = "255.255.255.0"
lease_time = 86400
iface = "eth0"

def handle_dhcp(pkt):
    if DHCP in pkt and pkt[DHCP].options[0][1] == 1:  # DHCP Discover
        print("[*] DHCP Discover received")

        ether = Ether(dst=pkt[Ether].src)
        ip = IP(src=server_ip, dst="255.255.255.255")
        udp = UDP(sport=67, dport=68)
        bootp = BOOTP(op=2, yiaddr=offered_ip, siaddr=server_ip, chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid)
        dhcp = DHCP(options=[
            ("message-type", "offer"),
            ("server_id", server_ip),
            ("subnet_mask", subnet_mask),
            ("lease_time", lease_time),
            "end"
        ])
        offer = ether / ip / udp / bootp / dhcp
        sendp(offer, iface=iface)
        print("[+] Sent DHCP Offer")

    elif DHCP in pkt and pkt[DHCP].options[0][1] == 3:  # DHCP Request
        print("[*] DHCP Request received")

        ether = Ether(dst=pkt[Ether].src)
        ip = IP(src=server_ip, dst="255.255.255.255")
        udp = UDP(sport=67, dport=68)
        bootp = BOOTP(op=2, yiaddr=offered_ip, siaddr=server_ip, chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid)
        dhcp = DHCP(options=[
            ("message-type", "ack"),
            ("server_id", server_ip),
            ("subnet_mask", subnet_mask),
            ("lease_time", lease_time),
            "end"
        ])
        ack = ether / ip / udp / bootp / dhcp
        sendp(ack, iface=iface)
        print("[+] Sent DHCP ACK")

print("[*] DHCP Server running on interface " + iface)
sniff(filter="udp and (port 67 or 68)", prn=handle_dhcp, store=0, iface=iface)
