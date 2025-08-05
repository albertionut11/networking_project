import socket
import struct
import sys
import requests
import geoplot as gplt
import geopandas as gpd
import matplotlib.pyplot as plt

ip_list = []

def traceroute(ip, port, TTL=30, timeout=5):
    # socket de UDP
    udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
    # socket RAW de citire a răspunsurilor ICMP
    icmp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    # setam timout in cazul in care socketul ICMP la apelul recvfrom nu primeste nimic in buffer
    udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', 1))

    for ttl in range(1, TTL + 1):
        # setam TTL in headerul de IP pentru socketul de UDP
        udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))

        # trimite un mesaj UDP catre un tuplu (IP, port)
        udp_send_sock.sendto(b'', (ip, port))
        
        icmp_recv_socket.settimeout(timeout)
        addr = "done!"
        try:
            data, addr = icmp_recv_socket.recvfrom(512)
        except socket.timeout:
            print(ttl, "*")
            continue


        print (ttl, addr[0])
        ip_list.append(addr[0])
        if addr[0] == ip:
            break
        # last_addr = addr[0]


'''
 Exercitiu hackney carriage (optional)!
    e posibil ca ipinfo sa raspunda cu status code 429 Too Many Requests
    cititi despre campul X-Forwarded-For din antetul HTTP
        https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/
    si setati-l o valoare in asa fel incat
    sa puteti trece peste sistemul care limiteaza numarul de cereri/zi

    Alternativ, puteti folosi ip-api (documentatie: https://ip-api.com/docs/api:json).
    Acesta permite trimiterea a 45 de query-uri de geolocare pe minut.
'''

# traceroute("170.171.1.10", 33434)
traceroute(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))

if len(ip_list) >= 2 and ip_list[-1] == ip_list[-2]:
    ip_list.pop()

# res = requests.get('http://ip-api.com/json/193.226.51.6')
endpoint = "http://ip-api.com/batch"
res = requests.post(endpoint, json=ip_list)
# res.raise_for_status()
res = res.json()

coords = []
for i in res:
    if i["status"] == "success":
        print(i["query"], i["country"], i["city"])
        coords.append((i["lon"], i["lat"]))
    else:
        print(i["query"], "error")


print("Geoplot")

from shapely.geometry import LineString

# creeaza un GeoDataFrame dintr-o lista de coordonate
print(gpd.GeoDataFrame({'geometry': gpd.points_from_xy([coord[0] for coord in coords], [coord[1] for coord in coords])}))
df = gpd.GeoDataFrame({'geometry': gpd.points_from_xy([coord[0] for coord in coords], [coord[1] for coord in coords])})


# adauga un index pentru fiecare punct (necesar pentru a crea linii intre puncte)
df['order'] = range(len(df))

# creeaza o lista de LineString-uri intre puncte consecutive
lines = [LineString([df.iloc[i]['geometry'], df.iloc[i+1]['geometry']]) for i in range(len(df)-1)]

# creeaza un GeoDataFrame din lista de linii
lines_df = gpd.GeoDataFrame({'geometry': lines})

# plotuim punctele si liniile
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
ax = world.plot(color='white', edgecolor='black')
df.plot(ax=ax, color='red')
lines_df.plot(ax=ax, color='blue')

# plt.savefig('../assets/' + 'test.png')
plt.show()