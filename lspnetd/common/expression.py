import socket


def ports_to_segments(ports: list[int]):
    "[10,11,12,13,20] -> [(10,13), (20,20)]"
    
    sorted_ports = sorted(set([int(x) for x in ports]))
    segs: list[tuple[int, int]] = []
    
    begin_port = 0
    end_port = 0
    for port in sorted_ports:
        if not begin_port:
            begin_port = port
            end_port = port
            continue
        
        if port - end_port > 1:
            # not-continuous
            segs.append((begin_port, end_port))
            begin_port = port
            end_port = port
            continue

        # continous
        end_port = port

    if begin_port:
        segs.append((begin_port, end_port))

    return segs


def port_segments_to_expression(segments: list[tuple[int, int]]):
    "[(10,13), (20,20)] -> '10-13,20'"
    
    output: list[str] = []
    for seg in segments:
        begin_port, end_port = seg
        if end_port != begin_port:
            output.append('{}-{}'.format(begin_port, end_port))
        else:
            output.append('{}'.format(begin_port))
    
    return ','.join(output)


def parse_ports_expression(port_expr: str):
    "10-13,20 -> [10,11,12,13,20]"
    
    parts = [s for s in port_expr.split(',') if s]
    all_ports: set[int] = set()
    for s in parts:
        if '-' in s:
            begin_port, end_port = s.split('-')
            all_ports.update(range(int(begin_port), int(end_port)+1))
        else:
            all_ports.add(int(s))

    return list(all_ports)


def parse_endpoint_expression(endpoint_expr: str):
    "host:port -> host, real_host, ports"
    
    if "[" in endpoint_expr and "]" in endpoint_expr:
        # [ipv6]:port
        parts = endpoint_expr.split(']')
        if len(parts) < 2:
            return parts[0][1:], '', 0

        assert len(parts) == 2, "Invalid hostport format, detected invalid [ipv6]:<port-expression>"
        return parts[0][1:], parts[0][1:], parse_ports_expression(parts[1])
    
    parts = endpoint_expr.split(':')
    real_host = socket.gethostbyname(parts[0])
    if len(parts) < 2:
        return parts[0], real_host, 0

    assert len(parts) == 2, "Invalid hostport format, detected invalid <host or ipv4>:<port-expression>"
    return parts[0], real_host, parse_ports_expression(parts[1])
