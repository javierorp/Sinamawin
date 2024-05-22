"""Use Nmap to get information about active hosts"""

from time import sleep
import ipaddress
import subprocess
import threading
import tkinter as tk
import traceback
import webbrowser
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import MessageDialog, Messagebox

from network_adapters import NetworkAdapters


APPNAME = "Sinamawin"


def get_nmap_version() -> str:
    """Get the namp version.

    Returns:
        str: Nmap version.
    """

    version = ""
    p = subprocess.Popen(["powershell.exe", "nmap", "--version"],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)

    na = NetworkAdapters()
    output, _ = p.communicate()
    out_dec = output.decode(na.enconding)

    if out_dec:
        version = out_dec.split(" ")[2]

    return version


def nmap_widget() -> None:
    """Create the Nmap module popup window."""
    try:
        nmap_ver = get_nmap_version()
        header = ("Internet Address     Port          State"
                  "      Service          MAC Address"
                  "           Device\n")
        if not nmap_ver:
            title = f"{APPNAME} - Nmap not installed"
            msg = ("To use this module Nmap (https://nmap.org)"
                   " must be installed.")
            dialog = MessageDialog(message=msg,
                                   title=title,
                                   buttons=["Download", "Cancel"],
                                   padding=(30, 30),
                                   width=100,
                                   alert=True)

            dialog.show()

            if dialog.result == "Download":
                webbrowser.open("https://nmap.org/download.html#windows")

            return

        na = NetworkAdapters()
        style = ttk.Style()
        style.configure("Normal.TLabel", foreground="black",
                        font=("Consolas", 9))
        style.configure("Wrong.TLabel", foreground="red",
                        font=("Consolas", 9, "bold"))

        def on_change_ip_netmask(*_):
            ip = ip_var.get()
            port = port_var.get()
            netmask = cb_netmask.get()
            if na.validate_ipv4(ip):
                net = ipaddress.ip_network(f"{ip}{netmask}", strict=False)
                first_ip = str(net.network_address)
                last_ip = str(net.broadcast_address)

                if int(netmask.replace("/", "")) >= 24:
                    last_segment = last_ip.split(".")[3]
                    if first_ip == last_ip:
                        d_ip_range.configure(text=f"{first_ip}",
                                             style="Normal.TLabel")
                    else:
                        d_ip_range.configure(text=f"{first_ip}-{last_segment}",
                                             style="Normal.TLabel")
                else:
                    d_ip_range.configure(text=f"{first_ip} to\n{last_ip}",
                                         style="Normal.TLabel")

                if port:
                    b_run.configure(state="enabled")
                else:
                    b_run.configure(state="disabled")
            else:
                d_ip_range.configure(text="Invalid IP", style="Wrong.TLabel")
                b_run.configure(state="disabled")

        popup = ttk.Toplevel(
            title=f"{APPNAME} - Nmap (Network Mapper)",
            resizable=(False, False))

        # -- Description --
        l_desc = ttk.Label(
            popup,
            text="🛈 This module allows IP and port scanning.")
        l_desc.grid(row=0, column=0, columnspan=4,
                    padx=15, pady=(15, 10), sticky="w")

        # -- IP address --
        l_ip_addr = ttk.Label(popup, text="IP address:")
        ip_var = tk.StringVar()
        ip_var.trace_add("write", on_change_ip_netmask)
        d_ip_addr = ttk.Entry(
            popup, width=20, justify="center", textvariable=ip_var)

        l_ip_addr.grid(row=1, column=0, padx=(15, 5), pady=5)
        d_ip_addr.grid(row=1, column=1, padx=5, pady=5)

        # -- Netmask --
        l_netmask = ttk.Label(popup, text="Netmask:")
        cb_netmask_val = list(range(1, 33))
        cb_netmask_val = [f"/{elem}" for elem in cb_netmask_val]
        cb_netmask = ttk.Combobox(popup,
                                  state="readonly",
                                  values=cb_netmask_val,
                                  width=18,
                                  justify="center")
        cb_netmask.set("/24")
        cb_netmask.bind("<<ComboboxSelected>>", on_change_ip_netmask)

        l_netmask.grid(row=1, column=2, padx=(15, 5), pady=5)
        cb_netmask.grid(row=1, column=3, padx=(5, 15), pady=5)

        # -- IP range --
        l_ip_range = ttk.Label(popup, text="Range:", justify="center")
        d_ip_range = ttk.Label(popup, text="Invalid IP",
                               style="Wrong.TLabel",
                               justify="center")
        l_ip_range.grid(row=2, column=0, padx=(15, 5), pady=5)
        d_ip_range.grid(row=2, column=1, padx=5, pady=5)

        # -- Port --
        l_port = ttk.Label(popup, text="Ports:")
        port_var = tk.StringVar()
        port_var.trace_add("write", on_change_ip_netmask)
        d_port = ttk.Entry(popup, width=20, justify="center",
                           textvariable=port_var)

        l_port.grid(row=2, column=2, padx=5, pady=5)
        d_port.grid(row=2, column=3, padx=(5, 15), pady=5)

        # -- Protocol --
        def on_change_protocol(*_):
            prot_sel = cb_prot.get()
            if prot_sel == "TCP":
                nb_output.tab(0, state="normal")
                nb_output.tab(1, state="disabled")
                nb_output.select(0)
            elif prot_sel == "UDP":
                nb_output.tab(0, state="disabled")
                nb_output.tab(1, state="normal")
                nb_output.select(1)
            else:
                nb_output.tab(0, state="normal")
                nb_output.tab(1, state="normal")

        l_prot = ttk.Label(popup, text="Protocol:", justify="center")
        cb_prot = ttk.Combobox(popup,
                               state="readonly",
                               values=["TCP", "UDP", "TCP & UDP"],
                               width=18,
                               justify="center")
        cb_prot.set("TCP")

        l_prot.grid(row=3, column=0, padx=(15, 5), pady=5)
        cb_prot.grid(row=3, column=1, padx=5, pady=5)

        cb_prot.bind("<<ComboboxSelected>>", on_change_protocol)

        # -- Run --
        def run_btn():
            d_ip_addr.configure(state="readonly")
            cb_netmask.configure(state="disabled")
            cb_prot.configure(state="disabled")
            d_port.configure(state="readonly")
            b_run.configure(state="disabled")

            t_tcp.configure(state="normal")
            t_tcp.delete(1.0, tk.END)
            t_tcp.insert(tk.END, "Running... (it may take several minutes)")
            t_tcp.configure(state="disabled")

            t_udp.configure(state="normal")
            t_udp.delete(1.0, tk.END)
            t_udp.insert(tk.END, "Running... (it may take several minutes)")
            t_udp.configure(state="disabled")

            def run_nmap():
                try:
                    sleep(5)  # To avoid errors
                    ip_mask = f"{ip_var.get()}{cb_netmask.get()}"
                    prot_sel = cb_prot.get()
                    ports = port_var.get()
                    tcp_op = False
                    udp_op = False

                    if "TCP" in prot_sel:
                        tcp_op = True

                    if "UDP" in prot_sel:
                        udp_op = True

                    ret = nmap(ip=ip_mask, ports=ports, tcp=tcp_op, udp=udp_op)

                    tcp_data = ret["tcp"]
                    udp_data = ret["udp"]

                    t_tcp.configure(state="normal")
                    t_tcp.delete(1.0, tk.END)
                    t_udp.configure(state="normal")
                    t_udp.delete(1.0, tk.END)

                    if tcp_data:
                        t_tcp.insert(tk.END, header, "bold")

                        for ip, ip_data in tcp_data.items():
                            mac = ip_data["mac"]
                            device = ip_data["device"]
                            for serv_data in ip_data["services"]:
                                port = serv_data["port"]
                                state = serv_data["state"]
                                service = serv_data["service"]

                                line = ip[:19].ljust(21)
                                line += port[:12].ljust(14)
                                line += state[:9].ljust(11)
                                if len(service) > 15:
                                    service = service[:-3] + "..."
                                line += service[:15].ljust(17)
                                line += mac.ljust(22) + device
                                line += "\n"
                                t_tcp.insert(tk.END, line)
                    else:
                        t_tcp.insert(tk.END, "No data available.")

                    if udp_data:
                        t_udp.insert(tk.END, header, "bold")

                        for ip, ip_data in udp_data.items():
                            mac = ip_data["mac"]
                            device = ip_data["device"]
                            for serv_data in ip_data["services"]:
                                port = serv_data["port"]
                                state = serv_data["state"]
                                service = serv_data["service"]

                                line = ip[:19].ljust(21)
                                line += port[:12].ljust(14)
                                line += state[:9].ljust(11)
                                if len(service) > 15:
                                    service = service[:-3] + "..."
                                line += service[:15].ljust(17)
                                line += mac.ljust(22) + device
                                line += "\n"
                                t_udp.insert(tk.END, line)
                    else:
                        t_udp.insert(tk.END, "No data available.")

                except (KeyError, ValueError, NotImplementedError) as err:
                    t_tcp.configure(state="normal")
                    t_tcp.delete(1.0, tk.END)
                    t_udp.configure(state="normal")
                    t_udp.delete(1.0, tk.END)

                    t_tcp.insert(tk.END, f"Error: {err}", "error")
                    t_udp.insert(tk.END, f"Error: {err}", "error")

                except:  # pylint: disable=bare-except # noqa
                    traceback.print_exc()
                    t_tcp.configure(state="normal")
                    t_tcp.delete(1.0, tk.END)
                    t_udp.configure(state="normal")
                    t_udp.delete(1.0, tk.END)

                    t_tcp.insert(tk.END, "Error: Failed to run Nmap.", "error")
                    t_udp.insert(tk.END, "Error: Failed to run Nmap.", "error")
                finally:
                    d_ip_addr.configure(state="enabled")
                    cb_netmask.configure(state="readonly")
                    cb_prot.configure(state="readonly")
                    d_port.configure(state="enabled")
                    b_run.configure(state="enabled")
                    t_tcp.configure(state="disabled")
                    t_udp.configure(state="disabled")

            th_run = threading.Thread(target=run_nmap)
            th_run.start()

        b_run = ttk.Button(popup,
                           text="Run", width=10,
                           command=run_btn,
                           state="disabled")
        b_run.grid(row=3, column=3, padx=(5, 15), pady=5)

        # -- Notebook --
        nb_output = ttk.Notebook(popup, bootstyle="light")
        nb_output.grid(row=4, column=0, columnspan=4, padx=15, pady=(10, 15))

        tcp_frame = ttk.Frame(nb_output)
        nb_output.add(tcp_frame, text="TCP")
        udp_frame = ttk.Frame(nb_output)
        nb_output.add(udp_frame, text="UDP")

        nb_output.tab(1, state="disabled")

        # -- TCP Tab --
        t_tcp = tk.Text(tcp_frame, wrap="none", height=12, width=110,
                        relief="flat", font=("Consolas", 10))
        t_tcp.grid(row=0, column=0)
        t_tcp.tag_configure("bold", font=("Consolas", 10, "bold"))
        t_tcp.tag_configure("error", font=(
            "Consolas", 10), foreground="red")
        t_tcp.insert(tk.END, header, "bold")
        t_tcp.configure(state="disabled")

        # -- UDP Tab --
        t_udp = tk.Text(udp_frame, wrap="none", height=12, width=110,
                        relief="flat", font=("Consolas", 10))
        t_udp.grid(row=0, column=0)
        t_udp.tag_configure("bold", font=("Consolas", 10, "bold"))
        t_udp.tag_configure("error", font=(
            "Consolas", 10), foreground="red")
        t_udp.insert(tk.END, header, "bold")
        t_udp.configure(state="disabled")

        # Mouse wheel behavior

        def popup_window_scroll(_):
            """To avoid propagating the event to the main window."""
            return "break"

        popup.bind("<MouseWheel>", popup_window_scroll)

        return

    except:  # pylint: disable=bare-except # noqa
        traceback.print_exc()
        Messagebox.show_error(
            message="The Nmap module has an unexpected error.",
            title=f"{APPNAME} - Error",
            padding=(30, 30),
            width=100)


def nmap(ip: str, ports: str, tcp: bool = True, udp: bool = False) -> dict:
    """Run Nmap and return a dictionary separating TCP and UDP.

    Args:
        ip (str): IP + Netmask (e.g., 192.168.1.10/24)
        ports (str): Ports to scan.
        tcp (bool, optional): Scan TCP ports. Defaults to True.
        udp (bool, optional): Scan UDP ports. Defaults to False.

    Raises:
        KeyError: Ports are not valid.
        NotImplementedError: Nmap error.
        ValueError: No hosts up.
        ValueError: No information.

    Returns:
        dict: Dictionary with port information separated by TCP and UDP.
    """
    protocols = " -sS" if tcp else ""
    protocols += " -sU" if udp else ""

    p = subprocess.Popen(["powershell.exe", "nmap",
                          "-p", str(ports),
                          protocols,
                          str(ip)],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)

    na = NetworkAdapters()
    output, error = p.communicate()
    out_dec = output.decode(na.enconding)
    error_dec = error.decode(na.enconding)

    if "Ports specified must be between" in error_dec:
        err = error_dec.split("\r\n", maxsplit=1)[0]
        raise KeyError(err)

    if error_dec:
        err = error_dec.split("\r\n", maxsplit=1)[0]
        raise NotImplementedError(err)

    if "0 hosts up" in out_dec:
        raise ValueError("0 hosts up")

    if not out_dec:
        raise ValueError("No information")

    data = out_dec.split("Nmap scan report for")[1:]

    tcp_servs = {}
    udp_servs = {}
    for host in data:
        info = host.split("\r\n")
        ip = info[0].strip()
        device_aux = ""
        if "(" in ip:
            ip_inf = ip.split(" ")
            ip = ip_inf[1][1:-1]
            device_aux = ip_inf[0]

        ctrl = False
        for inf in info:
            if not inf:
                continue

            if "PORT" in inf:
                ctrl = True
                continue

            if ctrl and "MAC Address" in inf:
                mac_info = inf.strip().split(" ")

                if ip in tcp_servs:
                    tcp_servs[ip]["mac"] = mac_info[2].replace(":", "-")
                    device = tcp_servs[ip]["device"]
                    tcp_servs[ip]["device"] = " ".join(mac_info[3:])[1:-1] + (
                        f" ({device})" if device else "")

                if ip in udp_servs:
                    udp_servs[ip]["mac"] = mac_info[2].replace(":", "-")
                    udp_servs[ip]["device"] = " ".join(mac_info[3:])[1:-1] + (
                        f" ({device})" if device else "")

                break

            if ctrl:
                serv_data = inf.strip().split(" ")
                serv_data = [elem for elem in serv_data if elem]
                if len(serv_data) < 3:
                    serv_data.append("")
                port = serv_data[0]
                state = serv_data[1]
                service = serv_data[2]

                if "tcp" in port:
                    if ip not in tcp_servs:
                        tcp_servs[ip] = {"services": [],
                                         "mac": "", "device": device_aux}
                    tcp_servs[ip]["services"].append({
                        "port": port,
                        "state": state,
                        "service": service
                    })

                if "udp" in port:
                    if ip not in udp_servs:
                        udp_servs[ip] = {"services": [],
                                         "mac": "", "device": device_aux}
                    udp_servs[ip]["services"].append({
                        "port": port,
                        "state": state,
                        "service": service
                    })

    return {"tcp": tcp_servs, "udp": udp_servs}
