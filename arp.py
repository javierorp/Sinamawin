"""Find out the MAC address of a network adapter to which it is connected"""

import subprocess
import threading
import traceback
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import Messagebox

from network_adapters import NetworkAdapters


APPNAME = "Sinamawin"


def get_arp_table(ip_netap: str, ip_target: str = ""):
    """Get the ARP table of a network adapter.

    Args:
        ip_netap (str): Network adapter IP.
        ip_target (str, optional): IP to ping. Defaults to "" (disabled).
    """

    def ping():
        p = subprocess.Popen(["powershell.exe", "ping",
                              str(ip_target), "-n 20"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        p.communicate()

    if ip_target:
        t_ping = threading.Thread(target=ping)
        t_ping.start()

    p = subprocess.Popen(["powershell.exe", "arp -a -N", str(ip_netap)],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)

    na = NetworkAdapters()
    output, error = p.communicate()
    out_dec = output.decode(na.enconding)

    data_arp = []

    if out_dec.find("---") == -1 or error:
        return data_arp

    ret = out_dec.split("\r\n")
    ret = [elem.strip() for elem in ret if elem.strip() != ""]

    for line in ret:
        data = [elem.strip() for elem in line.split(" ") if elem.strip() != ""]
        if na.validate_ipv4(data[0]):
            data_arp.append({
                "iaddr": str(data[0]),
                "phyaddr": str((data[1])).upper(),
                "itype": str(data[2])
            })

    return data_arp


def arp_widget(adapters: list) -> None:
    """Create the ARP module popup window.

    Args:
        adapters (list): List of dictionaries with information
            about network adapters.
            [
                {
                'ip': '192.168.1.1',
                'name': 'Ethernet'
                },
                ...
            ]
    """
    try:
        popup = ttk.Toplevel(
            title=f"{APPNAME} - ARP (Address Resolution Protocol)",
            resizable=(False, False))

        # -- Description --
        l_desc = ttk.Label(
            popup,
            text=("🛈 This module allows you to know the MAC address of"
                  " the network adapter to which it is connected."
                  "\n     If a target IP address is specified,"
                  " a ping is performed"
                  " while the ARP table is obtained."))
        l_desc.grid(row=0, column=0, columnspan=4,
                    padx=15, pady=(15, 10), sticky="w")

        # -- IP address --
        l_ip_addr = ttk.Label(popup, text="IP address target:")
        d_ip_addr = ttk.Entry(
            popup, width=20, justify="center")

        l_ip_addr.grid(row=1, column=0, padx=(15, 5), pady=5)
        d_ip_addr.grid(row=1, column=1, padx=5, pady=5)

        # -- Interface --
        cb_iface_val = ["-- Select interface --"] + \
            [f"{elem['ip']} ({elem['name']})" for elem in adapters]
        cb_iface = ttk.Combobox(popup,
                                state="readonly",
                                values=cb_iface_val,
                                width=25)
        cb_iface.set(cb_iface_val[0])

        cb_iface.grid(row=1, column=2, padx=5, pady=5)

        # -- Run button --
        def run_btn():
            """Get the information from the ARP table and
            display it in the text box.
            """
            cb_selec = cb_iface.get()

            if "Select interface" in cb_selec:
                return

            ip_netap = cb_selec.split(" ")[0]
            ip_target = d_ip_addr.get()

            na = NetworkAdapters()

            if ip_target and not na.validate_ipv4(ip_target):
                Messagebox.show_error(
                    message="Invalid IP address.",
                    title=f"{APPNAME} - Invalid data",
                    padding=(30, 30),
                    width=100,
                    parent=popup)
                return

            data = get_arp_table(ip_netap, ip_target)
            t_arp.configure(state="normal")
            t_arp.delete(1.0, tk.END)

            if not data:
                t_arp.insert(tk.END, "No data available")
                return

            t_arp.insert(
                tk.END, "Internet Address     Physical Address      Type\n",
                "bold")

            for rec in data:
                text = rec["iaddr"].ljust(
                    21) + rec["phyaddr"].ljust(22) + rec["itype"] + "\n"

                if ip_target and ip_target == rec["iaddr"]:
                    t_arp.insert(tk.END, text, "emphasis")
                else:
                    t_arp.insert(tk.END, text)

            t_arp.configure(state="disabled")

            return

        b_run = ttk.Button(popup, bootstyle="outline",
                           text="Run", width=10,
                           command=run_btn)
        b_run.grid(row=1, column=3, padx=(5, 15), pady=5)

        # -- Text --
        t_arp = tk.Text(popup, wrap="word", height=12,
                        relief="flat", font=("Consolas", 10))
        t_arp.grid(row=2, column=0, columnspan=4, padx=15, pady=(10, 15))
        t_arp.tag_configure("bold", font=("Consolas", 10, "bold"))
        t_arp.tag_configure("emphasis", font=(
            "Consolas", 10, "bold"), foreground="green")
        t_arp.insert(
            tk.END, "Internet Address     Physical Address      Type\n",
            "bold")
        t_arp.configure(state="disabled")

        # Mouse wheel behavior
        def popup_window_scroll(_):
            """To avoid propagating the event to the main window."""
            return "break"

        popup.bind("<MouseWheel>", popup_window_scroll)

        return

    except:  # pylint: disable=bare-except # noqa
        traceback.print_exc()
        Messagebox.show_error(
            message="The ARP module has an unexpected error.",
            title=f"{APPNAME} - Error",
            padding=(30, 30),
            width=100)
