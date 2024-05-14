"""Get information about and configure network adapters in Windows"""

import re
import subprocess


class NetworkAdapters:
    """Network Adapters"""

    def __init__(self) -> None:
        self.enconding = self.get_enconding()

    def _get_dns_client_server_address(self) -> dict:
        """Get network adapter information from Get-DnsClientServerAddress.

        Returns:
            dict: Dictionary of dictionaries with the data of network adapters
                    whose key is the index of the adapter.
            {
            1: {
                "pref_dns": "1.1.1.1",
                "alt_dns": "8.8.8.8"
            },
            ...
            }
        """
        p = subprocess.Popen(["powershell.exe", "Get-DnsClientServerAddress",
                              "-AddressFamily IPv4",
                              "| Format-List -Property",
                              "InterfaceIndex",
                              ",ServerAddresses"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        output, _ = p.communicate()

        out_dec = output.decode(self.enconding).split("InterfaceIndex")

        adapters = {}
        for adapter in out_dec:
            if "ServerAddresses" not in adapter:
                continue

            list_prop = adapter.split("\r\n")
            while "" in list_prop:
                list_prop.remove("")

            list_prop[0] = "InterfaceIndex" + list_prop[0]

            properties = {}
            pref_dns = ""
            alt_dns = ""
            for prop in list_prop:
                if "ServerAddresses" in prop:
                    dns = prop.split(":")[1].strip()[1:-1].split(",")
                    pref_dns = dns[0]
                    if len(dns) == 2:
                        alt_dns = dns[1]
                    properties["PreferredDNSServer"] = pref_dns
                    properties["AlternateDNSServer"] = alt_dns
                else:
                    desc, value = prop.split(":")
                    properties[desc.strip()] = value.strip()

            adapters[int(properties["InterfaceIndex"])] = {
                "pref_dns": properties["PreferredDNSServer"].strip(),
                "alt_dns": properties["AlternateDNSServer"].strip()
            }

        return adapters

    def get_enconding(self) -> str:
        """Get terminal enconding.

        Returns:
            str: Terminal enconding.
        """
        try:
            p = subprocess.Popen(["powershell.exe", "Get-ItemPropertyValue",
                                  "HKLM:\\SYSTEM\\CurrentControlSet" +
                                  "\\Control\\Nls\\CodePage OEMCP"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.DEVNULL,
                                 creationflags=subprocess.CREATE_NO_WINDOW)

            oemcp, _ = p.communicate()
            oemcp = oemcp.decode('utf-8').replace("\n", "")
            return f"cp{oemcp}"

        except (OSError, TypeError, ValueError):
            return "utf-8"

    def _get_net_adapter(self) -> dict:
        """Get network adapter information from Get-NetAdapter.

        Returns:
            dict: Dictionary of dictionaries with the data of network adapters
                    whose key is the index of the adapter.
            {
            1: {
                "name": "Ethernet",
                "desc": "Ethernet Adapter",
                "status": "Up",
                "mac": "00-00-00-00-00-00"
            },
            ...
            }
        """
        p = subprocess.Popen(["powershell.exe", "Get-NetAdapter",
                              "| Format-List -Property",
                              "ifIndex",
                              ",Name",
                              ",InterfaceDescription",
                              ",Status",
                              ",MacAddress"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        output, _ = p.communicate()

        out_dec = output.decode(self.enconding).split("ifIndex")

        adapters = {}
        for adapter in out_dec:
            if "Name" not in adapter:
                continue

            list_prop = adapter.split("\r\n")
            while "" in list_prop:
                list_prop.remove("")

            list_prop[0] = "ifIndex" + list_prop[0]

            properties = {}
            for prop in list_prop:
                desc, value = prop.split(":")
                properties[desc.strip()] = value.strip()

            adapters[int(properties["ifIndex"])] = {
                "name": properties["Name"].strip(),
                "desc": properties["InterfaceDescription"].strip(),
                "status": properties["Status"].strip(),
                "mac": properties["MacAddress"].strip()
            }

        return adapters

    def _get_net_ip_address(self) -> dict:
        """Get network adapter information from Get-NetIPAddress.

        Returns:
            dict: Dictionary of dictionaries with the data of network adapters
                    whose key is the index of the adapter.
            {
            1: {
                "ip": "192.168.1.10",
                "prefix_length": 24,
                "mask": "255.255.255.0",
                "prefix_origin": "Dhcp",
                "suffix_origin": "Dhcp"
            },
            ...
            }
        """
        p = subprocess.Popen(["powershell.exe", "Get-NetIPAddress",
                              "-AddressFamily IPv4",
                              "| Format-List -Property",
                              "InterfaceIndex",
                              ",IPAddress",
                              ",PrefixLength",
                              ",PrefixOrigin",
                              ",SuffixOrigin"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        output, _ = p.communicate()

        out_dec = output.decode(self.enconding).split("InterfaceIndex")

        adapters = {}
        for adapter in out_dec:
            if "IPAddress" not in adapter:
                continue

            list_prop = adapter.split("\r\n")
            while "" in list_prop:
                list_prop.remove("")

            list_prop[0] = "InterfaceIndex" + list_prop[0]

            properties = {}
            for prop in list_prop:
                desc, value = prop.split(":")
                properties[desc.strip()] = value.strip()

            adapters[int(properties["InterfaceIndex"])] = {
                "ip": properties["IPAddress"].strip(),
                "prefix_length": int(properties["PrefixLength"]) if
                properties["PrefixLength"] else "",
                "mask": self.prefix_length_2_subnet_mask(
                    int(properties["PrefixLength"])) if
                properties["PrefixLength"] else "",
                "prefix_origin": properties["PrefixOrigin"].strip(),
                "suffix_origin": properties["SuffixOrigin"].strip()
            }

        return adapters

    def _get_net_route(self) -> dict:
        """Get network adapter information from Get-NetRoute.

        Returns:
            dict: Dictionary of dictionaries with the data of network adapters
                    whose key is the index of the adapter.
            {
            1: {
                "gateway": "192.168.1.1"
            },
            ...
            }
        """
        p = subprocess.Popen(["powershell.exe", "Get-NetRoute",
                              "-AddressFamily IPv4",
                              "| Format-List -Property",
                              "ifIndex",
                              ",NextHop"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        output, _ = p.communicate()

        out_dec = output.decode(self.enconding).split("ifIndex")

        adapters = {}
        for adapter in out_dec:
            if "NextHop" not in adapter:
                continue

            list_prop = adapter.split("\r\n")
            while "" in list_prop:
                list_prop.remove("")

            list_prop[0] = "ifIndex" + list_prop[0]

            properties = {}
            for prop in list_prop:
                desc, value = prop.split(":")
                properties[desc.strip()] = value.strip()

            adapters[int(properties["ifIndex"])] = {
                "gateway": properties["NextHop"].strip()
            }

        return adapters

    def _merge_dicts(self, d1: dict, d2: dict) -> dict:
        """Merge two dictionaries while preserving the properties of both.
        If a property is found in both, the value of d1 prevails.

        Args:
            d1 (dict): First dictionary to be merged.
            d2 (dict): Second dictionary to be merged.

        Returns:
            dict: Dictionary with the properties of both.
        """
        merged = {}
        for key in d1.keys() | d2.keys():
            if key in d1 and key in d2:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    merged[key] = self._merge_dicts(d1[key], d2[key])
                else:
                    merged[key] = d1[key]
            elif key in d1:
                merged[key] = d1[key]
            else:
                merged[key] = d2[key]
        return merged

    def disable_adapter(self, alias: str) -> None:
        """Disable the given network adapter.

        Args:
            alias (str): Network adapter alias.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given alias.
            NotImplementedError: Unidentified error.
        """
        p = subprocess.Popen(["powershell.exe", "Disable-NetAdapter",
                              "-Name",
                              f"'{str(alias)}'",
                              "-Confirm:$false"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while enabling DHCP on the network adapter")

        return

    def enable_adapter(self, alias: str) -> None:
        """Enable the given network adapter.

        Args:
            alias (str): Network adapter alias.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given alias.
            NotImplementedError: Unidentified error.
        """
        p = subprocess.Popen(["powershell.exe", "Enable-NetAdapter",
                              "-Name",
                              f"'{str(alias)}'"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while enabling DHCP on the network adapter")

        return

    def get_info(self) -> dict:
        """Get the information about the network adapters.

        Returns:
            dict: Dictionary of dictionaries with all network adapters whose
                    key is the index of the adapter and sorted by index.
            {
            1: {
                "prefix_origin": "Dhcp",
                "pref_dns": "1.1.1.1",
                "alt_dns": "8.8.8.8",
                "gateway": "192.168.1.1",
                "status": "Up",
                "mac": "00-00-00-00-00-00",
                "ip": "192.168.1.10",
                "suffix_origin": "Dhcp",
                "name": "Ethernet",
                "desc": "Ethernet Adapter",
                "mask": "255.255.255.0",
                "prefix_length": 24
                },
            ...
            }
        """
        properties = ["prefix_origin", "pref_dns", "alt_dns", "gateway",
                      "status", "mac", "ip", "suffix_origin", "name",
                      "desc", "mask", "prefix_length"]

        # Get the network adapters information
        net_adapters = self._get_net_adapter()
        net_ip = self._get_net_ip_address()
        net_dns = self._get_dns_client_server_address()
        net_gateway = self._get_net_route()

        # Merge data
        net_info = self._merge_dicts(net_gateway, self._merge_dicts(
            self._merge_dicts(net_adapters, net_ip), net_dns))

        # Sort by network adapter index
        net_info_sorted = {}
        keys_sorted = sorted(net_info.keys())
        for key in keys_sorted:
            # Save only visible adapters
            if "name" in net_info[key].keys():
                set_prop = set(properties)
                set_adap = set(net_info[key].keys())

                # Complete the dictionary with the missing properties
                if not set_prop.issubset(set_adap):
                    for prop in (set_prop - set_adap):
                        net_info[key][prop] = ""

                net_info_sorted[key] = net_info[key]

        return net_info_sorted

    def prefix_length_2_subnet_mask(self, bits: int) -> str:
        """Convert the size of the local subnet into a subnet mask.

        Args:
            bits (int): Number of bits of the local subnet size.

        Raises:
            ValueError: Invalid number of bits. Must be between 0 and 32.

        Returns:
            str: The subnet mask corresponding to the number of
                bits (255.255.255.255).
        """
        if not 0 <= bits <= 32:
            raise ValueError(
                "Invalid number of bits. Must be between 0 and 32.")

        subnet_mask_int = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
        subnet_mask = (
            (subnet_mask_int >> 24),
            ((subnet_mask_int >> 16) & 0xFF),
            ((subnet_mask_int >> 8) & 0xFF),
            (subnet_mask_int & 0xFF),
        )

        return ".".join(map(str, subnet_mask))

    def reset_def_gateway(self, index: int) -> None:
        """Remove the default gateway for a given network adapter.

        Args:
            index (int): Network adapter index.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        p = subprocess.Popen(["powershell.exe", "Remove-NetRoute",
                              " -ifIndex",
                              str(index),
                              "-DestinationPrefix",
                              "0.0.0.0/0",
                              "-Confirm:$false"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while removing default gateway"
                " on the network adapter")

        return

    def reset_dns_servers(self, index: int) -> None:
        """Remove the DNS servers set for a given network adapter.

        Args:
            index (int): Network adapter index.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        p = subprocess.Popen(["powershell.exe", "Set-DnsClientServerAddress",
                              "-InterfaceIndex",
                              str(index),
                              "-ResetServerAddresses"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise IndexError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while resetting the DNS")

        return

    def reset_ip(self, index: int) -> None:
        """Remove the ip address for a given network adapter.

        Args:
            index (int): Network adapter index.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        p = subprocess.Popen(["powershell.exe", "Remove-NetIPAddress",
                              " -InterfaceIndex",
                              str(index),
                              "-Confirm:$false"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while removing default gateway"
                " on the network adapter")

        return

    def set_def_gateway(self, index: int, ip: str) -> None:
        """Set the default gateway for a given network adapter.

        Args:
            index (int): Network adapter index.
            ip (str): Address to be set.

        Raises:
            ValueError: Invalid address.
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        if not ip or ip == "0.0.0.0":
            raise ValueError("Invalid configuration")

        p = subprocess.Popen(["powershell.exe", "New-NetRoute",
                              "-InterfaceIndex",
                              str(index),
                              "-DestinationPrefix",
                              "0.0.0.0/0",
                              "-NextHop",
                              str(ip)],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while setting the default gateway")
        return

    def set_dns_servers(self, index: int, pref_dns: str, alt_dns: str) -> None:
        """Set the DNS servers for a given network adapter.

        Args:
            index (int): Network adapter index.
            pref_dns (str): Address for the preferred DNS server.
            alt_dns (str): Address for the alternate DNS server.

        Raises:
            ValueError: Invalid address.
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        if (pref_dns == "0.0.0.0" or alt_dns == "0.0.0.0"):
            raise ValueError("Invalid configuration")

        p = subprocess.Popen(["powershell.exe", "Set-DnsClientServerAddress",
                              "-InterfaceIndex",
                              str(index),
                              "-ServerAddresses",
                              ",".join(list(
                                  filter(None,
                                         [str(pref_dns), str(alt_dns)])))],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            print(err_dec)
            raise NotImplementedError(
                "An error occurred while setting the DNS")

        return

    def set_ip_mask(self, index: int, ip: str, mask: str) -> None:
        """Set the address and subnet mask for a given network adapter.

        Args:
            index (int): Network adapter index.
            ip (str): Address to be set.
            mask (str): Subnet mask to be set.

        Raises:
            ValueError: Invalid address or subnet mask.
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        if not ip or not mask or ip == "0.0.0.0" or mask == "0.0.0.0":
            raise ValueError("Invalid configuration")

        p = subprocess.Popen(["powershell.exe", "New-NetIPAddress",
                              "-InterfaceIndex",
                              str(index),
                              "-IPAddress",
                              str(ip),
                              "-PrefixLength",
                              str(self.subnet_mask_2_prefix_length(mask)),
                              "-PolicyStore",
                              "ActiveStore"
                              ],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif "MSFT_NetIPAddress already exists" in err_dec:
            self.reset_ip(index)
            self.set_ip_mask(index, ip, mask)
        elif err_dec:
            err = ("An error occurred while setting the IP: "
                   + err_dec.split("\n", maxsplit=1)[0].split(":")[1].strip())
            raise NotImplementedError(err)
        return

    def set_net_dhcp(self, index: int) -> None:
        """Remove the default gateway and set DHCP for a given network adapter.

        Args:
            index (int): Network adapter index.

        Raises:
            PermissionError: No permissions to execute the command.
            KeyError: There is no network adapter for the given index.
            NotImplementedError: Unidentified error.
        """
        # Remove default gateway
        try:
            self.reset_def_gateway(index)
        except KeyError:
            pass

        # Set DHCP
        p = subprocess.Popen(["powershell.exe", "Set-NetIPInterface",
                              "-InterfaceIndex",
                              str(index),
                              "-DHCP",
                              "Enabled"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)

        _, error = p.communicate()
        err_dec = error.decode(self.enconding)

        if "PermissionDenied" in err_dec:
            raise PermissionError("No administrator permissions")
        elif "ObjectNotFound" in err_dec:
            raise KeyError("Invalid network adapter index")
        elif err_dec:
            raise NotImplementedError(
                "An error occurred while enabling DHCP on the network adapter")

        return

    def subnet_mask_2_prefix_length(self, mask: str) -> int:
        """Calculate the size of the local subnet corresponding
        to a subnet mask.

        Args:
            mask (str): Subnet mask (255.255.255.255).

        Raises:
            ValueError: Invalid subnet mask octet(s). Must be between 0
                and 255.

        Returns:
            int: The number of bits corresponding to the subnet mask.
        """
        octets = list(map(int, mask.split(".")))

        if any(octet < 0 or octet > 255 for octet in octets):
            raise ValueError(
                "Invalid subnet mask octet(s). Must be between 0 and 255.")

        bits_count = sum(bin(octet).count('1') for octet in octets)

        return int(bits_count)

    def validate_ipv4(self, ip: str) -> bool:
        """Check if the IP is in IPv4 format.

        Args:
            ip (str): IP to check.

        Returns:
            bool: True if it has the correct format, False otherwise.
        """
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
        if match:
            for group in match.groups():
                if int(group) > 255:
                    return False
            return True
        return False

    def validate_subnet_mask(self, mask: str) -> bool:
        """Check if the subnet mask is in the correct format (255.255.255.255).

        Args:
            mask (str): Subnet mask to check.

        Returns:
            bool: True if it has the correct format, False otherwise.
        """
        octects = mask.split('.')
        if len(octects) != 4:
            return False

        for octect in octects:
            try:
                value = int(octect)
                if value < 0 or value > 255:
                    return False
            except ValueError:
                return False

        binary = ''.join(format(int(octet), '08b') for octet in octects)

        if '0' in binary.rstrip('0'):
            return False

        return True
