import json
import socket
import struct
import time
from scapy.all import DNS, DNSQR, DNSRR, IP, UDP

AD_SERVERS_FILE = 'adservers.txt'
DNS_SERVER_IP = '8.8.8.8'
DNS_SERVER_PORT = 53
STATISTICS_FILE = 'statistics.json'
STATS_FILE = 'stats.txt'

# incarcam statistica din fisierul json
def load_stats_file(filename):
    with open(filename, 'r') as fr:
        return json.load(fr)

# salvam statistica in fisierul json
def update_stats_file(filename, stats):
    print("Updating Statistics!")
    with open(filename, 'w') as fw:
        json.dump(stats, fw)
    with open(filename, 'r') as fr:
        stats = json.load(fr)

    visited = []
    total_visits = 0
    max_visits = 0
    max_visited_site = ""
    visits_google = 0
    visits_facebook = 0
    visits_amazon = 0

    # cream o lista de tupluri (site, numar de vizite)
    for site in stats:
        visits = stats[site]
        if visits > 0:
            visited.append((site, visits))
            total_visits += visits

            if visits > max_visits:
                max_visits = visits
                max_visited_site = site

            if 'google' in site:
                visits_google += visits
            if 'facebook' in site:
                visits_facebook += visits
            if 'amazon' in site:
                visits_amazon += visits

    # sortam lista de tupluri descrescator dupa numarul de vizite
    visited = sorted(visited, key=lambda x: x[1], reverse=True)

    with open(STATS_FILE, 'w') as fw:
        fw.write(f"Total number of visits: {total_visits}\n")
        fw.write(f"Site with the maximum number of visits: {max_visited_site}\n")
        fw.write(f"Number of visits for sites containing 'google': {visits_google}\n")
        fw.write(f"Number of visits for sites containing 'facebook': {visits_facebook}\n")
        fw.write(f"Number of visits for sites containing 'amazon': {visits_amazon}\n")
        fw.write(f"Visited sites sorted by number of visits:\n")
        for site, visits in visited:
            fw.write(f"{site} : {visits}\n")

# incarcam lista de ad servers din fisier
def load_ad_servers(filename):
    with open(filename, 'r') as f:
        return set([line.split()[1] for line in f.readlines()])

# functia care se ocupa de requesturile DNS
def handle_dns_request(request, addr, client_sock, ad_servers, stats):
    # salvam requestul intr-un obiect de tip DNS
    dns_request = DNS(request)


    # dam forward la requestul DNS catre un server google (test)

    # print("Forwarded: " + dns_request.qd.qname[:-1].decode())
    # server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # server_sock.sendto(request, (DNS_SERVER_IP, DNS_SERVER_PORT))
    # response, _ = server_sock.recvfrom(1024)
    # server_sock.close()
    
    # # Send the DNS response back to the client
    # client_sock.sendto(response, addr)


    
    # daca domeniul este in lista de servere cu reclame, trimitem un raspuns cu ip-ul 0.0.0.0 (pentru a bloca reclamele)
    if dns_request.qd.qname[:-1].decode() in ad_servers:
        stats[dns_request.qd.qname[:-1].decode()] += 1
        print("Blocked: " + dns_request.qd.qname[:-1].decode())
        # cream un raspuns de tip DNS cu acelasi id ca requestul
        dns_response = DNS(id=dns_request.id, qr=1, opcode=0, aa=0, tc=0, rd=1, ra=1, z=0, rcode=0, qd=dns_request.qd, an=DNSRR(rrname=dns_request.qd.qname, rdata='0.0.0.0'))
        response = IP()/UDP()/dns_response
        # trimitem raspunsul la client
        client_sock.sendto(bytes(response), addr)
    else:
        # daca domeniul nu este in lista de servere cu reclame, trimitem requestul mai departe la un server DNS real
        print("Forwarded: " + dns_request.qd.qname[:-1].decode())
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_sock.sendto(request, (DNS_SERVER_IP, DNS_SERVER_PORT))
        response, _ = server_sock.recvfrom(1024)
        server_sock.close()
        
        # trimitem raspunsul la client
        client_sock.sendto(response, addr)

def main():
    ad_servers = load_ad_servers(AD_SERVERS_FILE)
    stats = load_stats_file(STATISTICS_FILE)
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.bind(('0.0.0.0', DNS_SERVER_PORT))

    update_time = time.time()
    print("DNS server started")
    while True:
        request, addr = client_sock.recvfrom(1024)
        handle_dns_request(request, addr, client_sock, ad_servers, stats)
        current_time = time.time()
        # actualizam statistica la fiecare 5 minute
        if current_time - update_time >= 300:
            update_stats_file(STATISTICS_FILE, stats)
            update_time = current_time

if __name__ == '__main__':
    main()
