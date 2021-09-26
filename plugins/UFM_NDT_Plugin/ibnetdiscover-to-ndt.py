import re

MS_NET_FILE_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/Director_Switches/ibnetdiscover_director.txt'
#MS_NET_FILE_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/Director_Switches/ms-net.txt'
SWITCH_TO_SWITCH_FILE_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/Director_Switches/switch-to-switch.csv'
SWITCH_TO_HOST_FILE_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/Director_Switches/switch-to-host.csv'

Director_Switch_Flag = False

def main():
    global Director_Switch_Flag
    with open(MS_NET_FILE_PATH, 'r') as f, open(SWITCH_TO_SWITCH_FILE_PATH, 'w') as s, open(SWITCH_TO_HOST_FILE_PATH, 'w') as h:
        s.write('#StartDevice,StartPort,EndDevice,EndPort,LinkType\n')
        h.write('#StartDevice,StartPort,EndDevice,EndPort,LinkType\n')
        lines = f.readlines()
        for line in lines:
            match = re.search(r'^Switch.*MF0;(.*):.*/L(.*)/U(.*)".*', line)
            if match:
                Director_Switch_Flag = False
                switch1 = match.group(1)
                switch1_blade = match.group(2)
                switch1_asic = match.group(3)
            else:
                match = re.search(r'^Switch.*MF0;(.*):.*/S(.*)/U(.*)".*', line)
                if match:
                    Director_Switch_Flag = True
                    continue

                match = re.search(r'^Switch.*MF0;(.*):.*', line)
                if match:
                    Director_Switch_Flag = False
                    switch1 = match.group(1)  # orig
                    switch1_blade = None
                    switch1_asic = None

            if Director_Switch_Flag == True:
                continue

            match = re.search(r'^\[(\d+)\].*\[(\d+)\].*MF0;(.*):.*/L(.*)/U(.*)" lid.*', line) #orig
            #match = re.search(r'^\[(\d+)\].*\[(\d+)\].*MF0;(.*):(.*)/L(.*)/U(.*)" lid.*', line)
            if match:
                    if match.lastindex == 5:
                        port1 = match.group(1)
                        port2 = match.group(2)
                        switch2 = match.group(3)
                        blade = match.group(4)
                        asic = match.group(5)
                        if switch1_blade and switch1_asic:
                            #if switch1.upper() == "SAT11-0101-0903-01IB1-A" and switch1_blade == "06" and switch1_asic == "1" and blade == "13" and asic == "1":
                            #    pass
                            s.write('{},Blade {}_Port {}/{},{},Blade {}_Port {}/{},Data\n'.format(switch1.upper(), switch1_blade, switch1_asic, port1, switch2.upper(), blade, asic, port2))
                        else:
                            s.write('{},Port {},{},Blade {}_Port {}/{},Data\n'.format(switch1.upper(), port1, switch2.upper(), blade, asic, port2))
            else:
                    match = re.search(r'^\[(\d+)\].*\[(\d+)\].*MF0;(.*):.*/S(.*)/U(.*)" lid.*', line)
                    if match:
                        continue

                    match = re.search(r'^\[(\d+)\].*\[(\d+)\].*MF0;(.*):.*', line) #orig
                    if match:
                        port1 = match.group(1)
                        port2 = match.group(2)
                        switch2 = match.group(3)
                        if switch1_blade and switch1_asic:
                            s.write('{},Blade {}_Port {}/{},{},Port {},Data\n'.format(switch1.upper(), switch1_blade, switch1_asic, port1, switch2.upper(), port2))
                        else:
                            s.write('{},Port {},{},Port {}, Data\n'.format(switch1.upper(), port1, switch2.upper(), port2))


            #match = re.search(r'^\[(\d+)\].*\[(\d+)\].*(DSM.*) (.*)\".*', line) #orig
            match = re.search(r'^\[(\d+)\].*\[(\d+)\].*(SAT.*) (.*)\".*', line)
            if match:
                port1 = match.group(1)
                hca = match.group(3)
                port2 = match.group(4)
                h.write('{},{} {},{},Port {}, Data\n'.format(hca.upper(), hca.upper(), port2, switch1.upper(), port1))
            match = re.search(r'^Ca', line)
            if match:
                break

if __name__ == '__main__':
    main()
