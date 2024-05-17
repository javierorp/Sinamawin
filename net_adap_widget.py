"""Create and manipulate the ttk widget for a network adapter"""

import threading
from time import sleep
import tkinter as tk
import traceback
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.dialogs.dialogs import MessageDialog, Messagebox
from ttkbootstrap.tooltip import ToolTip
import pyperclip

from network_adapters import NetworkAdapters
from net_adap_profiles import NetAdapProfiles

APPNAME = "Sinamawin"
LOADING_TIME = 10  # Waiting time to obtain the information
ICON = "./resources/sinamawin.ico"  # App icon


class NetAdapWidget:
    """Network adapter widget (ttkbootstrap.Labelframe)"""

    def __init__(self, idx: int, name: str, desc: str,
                 status: str, mac: str, ip: str, mask: str, gateway: str,
                 prefix_origin: str, suffix_origin: str, pref_dns: str,
                 alt_dns: str, disabled: bool) -> None:
        self.index = idx
        self.name = name
        self.desc = desc
        self.status = status
        self.mac = mac
        self.ip = ip
        self.mask = mask
        self.gateway = gateway
        self.prefix_origin = prefix_origin.upper(
        ) if prefix_origin == "Dhcp" else prefix_origin
        self.suffix_origin = suffix_origin.upper(
        ) if suffix_origin == "Dhcp" else suffix_origin
        self.pref_dns = pref_dns
        self.alt_dns = alt_dns

        self.disabled = disabled  # Disable widget completely or not
        self._labelframe = None  # Main widget
        # Other widgets
        self._d_status = None
        self._d_mac_addr = None
        self._b_manual = None
        self._d_ip_addr = None
        self._d_subnet = None
        self._d_gateway = None
        self._d_prefix_origin = None
        self._d_suffix_origin = None
        self._d_pref_dns_server = None
        self._d_alt_dns_server = None
        self._m_action = None

        self._entries_bck = None  # Copy of all Entry widgets

    def _change_wd_state(self) -> None:
        """Change the state of the widgets."""

        state = "readonly"
        m_state = "disabled"

        if "selected" in self._b_manual.state():
            state = "enabled"
            m_state = "active"

        self._d_ip_addr.configure(state=state)
        self._d_subnet.configure(state=state)
        self._d_gateway.configure(state=state)
        self._d_pref_dns_server.configure(state=state)
        self._d_alt_dns_server.configure(state=state)
        self._m_action.menu.entryconfigure(
            "Apply changes", state=m_state)
        self._m_action.menu.entryconfigure(
            "Apply profile", state=m_state)

        if self._d_status.cget('text') in ["Disabled", "Not Present"]:
            self._m_action.menu.entryconfigure("Save profile", state=m_state)

        return

    def _disable_all_wd(self) -> None:
        """Disable all widgets."""

        state = "readonly"
        m_state = "disabled"

        self._d_ip_addr.configure(state=state)
        self._d_subnet.configure(state=state)
        self._d_gateway.configure(state=state)
        self._d_pref_dns_server.configure(state=state)
        self._d_alt_dns_server.configure(state=state)
        self._m_action.menu.entryconfigure(
            "Apply changes", state=m_state)
        self._m_action.menu.entryconfigure(
            "Apply profile", state=m_state)
        try:
            self._m_action.menu.entryconfigure(
                "Enable network adapter", state=m_state)
        except:  # pylint: disable=bare-except # noqa
            pass
        try:
            self._m_action.menu.entryconfigure(
                "Disable network adapter", state=m_state)
        except:  # pylint: disable=bare-except # noqa
            pass
        self._b_manual.state([m_state])

        return

    def _enabled_all_wd(self) -> None:
        """Enable all widgets."""

        state = "enabled"
        m_state = "active"

        self._d_mac_addr.configure(state=state)
        self._d_ip_addr.configure(state=state)
        self._d_subnet.configure(state=state)
        self._d_gateway.configure(state=state)
        self._d_pref_dns_server.configure(state=state)
        self._d_alt_dns_server.configure(state=state)
        self._m_action.menu.entryconfigure(
            "Apply changes", state=m_state)
        self._m_action.menu.entryconfigure(
            "Apply profile", state=m_state)
        try:
            self._m_action.menu.entryconfigure(
                "Enable network adapter", state=m_state)
        except:  # pylint: disable=bare-except # noqa
            pass
        try:
            self._m_action.menu.entryconfigure(
                "Disable network adapter", state=m_state)
        except:  # pylint: disable=bare-except # noqa
            pass
        self._b_manual.configure(state=state)
        self._b_manual.state([m_state])

        return

    def _enable_dhcp(self):
        """Enable DHCP and get DNS servers automatically."""

        try:
            if ("selected" in self._b_manual.state()
                    or self._d_prefix_origin.cget('text') != "Manual"):
                self._entries_wd_bck_restore()
                self._change_wd_state()
                return

            msg = (f"Enable DHCP for '{self.name}' adapter and get DNS server"
                   " addresses automatically?")

            dialog_title = "Enable DHCP and get DNS server automatically"

            dialog = MessageDialog(message=msg,
                                   title=dialog_title,
                                   buttons=["Accept", "Cancel"],
                                   padding=(30, 30),
                                   width=70)

            dialog.show()

            if dialog.result == "Accept":
                # Enable/Disabled adapter
                ni = NetworkAdapters()
                ni.set_net_dhcp(self.index)
                ni.reset_dns_servers(self.index)

                self.toast_notification(
                    f"DHCP has been enabled for '{self.name}' adapter.")

                # Regenerate widgets in a thread so as not to crash the app
                def regenerate_wd():
                    sleep(5)
                    self.update_widgets()

                th = threading.Thread(target=regenerate_wd)
                th.start()

                # Show popup info windows
                self._popup_refresh_changes(
                    title=self.name, seconds=LOADING_TIME)

            else:
                self._b_manual.state(["selected"])
                self._change_wd_state()

            return
        except:  # pylint: disable=bare-except # noqa
            traceback.print_exc()
            with open(f"{APPNAME.lower()}_error.log", mode="w",
                      encoding="utf-8") as file:
                traceback.print_exc(file=file)
            Messagebox.show_error(
                message="The configuration could not be applied.",
                title=f"{APPNAME} - Error",
                padding=(30, 30),
                width=100)

            self._b_manual.state(["selected"])
            self._change_wd_state()

    def _entries_wd_bck(self) -> None:
        """Save a copy of the Entry widgets."""

        entries = {
            "_d_ip_addr": self._d_ip_addr.get(),
            "_d_subnet": self._d_subnet.get(),
            "_d_gateway": self._d_gateway.get(),
            "_d_pref_dns_server": self._d_pref_dns_server.get(),
            "_d_alt_dns_server": self._d_alt_dns_server.get()
        }

        self._entries_bck = entries

        return

    def _entries_wd_bck_restore(self) -> None:
        """Restore Entry widgets from the copy."""

        # -- IP address --
        self._d_ip_addr.delete(0, tk.END)
        self._d_ip_addr.insert(0, self._entries_bck["_d_ip_addr"])

        # -- Subnet mask --
        self._d_subnet.delete(0, tk.END)
        self._d_subnet.insert(0, self._entries_bck["_d_subnet"])

        # -- Default gateway --
        self._d_gateway.delete(0, tk.END)
        self._d_gateway.insert(0, self._entries_bck["_d_gateway"])

        # -- Preferred DNS Server --
        self._d_pref_dns_server.delete(0, tk.END)
        self._d_pref_dns_server.insert(
            0, self._entries_bck["_d_pref_dns_server"])

        # -- Alternate DNS Server --
        self._d_alt_dns_server.delete(0, tk.END)
        self._d_alt_dns_server.insert(
            0, self._entries_bck["_d_alt_dns_server"])

        return

    def _get_prefix_tooltip(self, origin: str) -> str:
        """Get the information about what the prefix origin means.

        Args:
            origin (str): Prefix origin.

        Returns:
            str: Meaning of the prefix origin.
        """
        prefix_origin = {
            "MANUAL": "The IP address prefix was manually specified.",
            "WELLKNOWN": "The IP address prefix is from a well-known source.",
            "DHCP": "The IP address prefix was provided by DHCP settings.",
            "ROUTERADVERTISEMENT": "The IP address prefix was obtained through"
            " a router advertisement (RA).",
            "OTHER": "The IP address prefix was obtained from another source,"
            " such as a VPN."
        }

        return prefix_origin[origin.upper()]

    def _get_suffix_tooltip(self, origin: str) -> str:
        """Get the information about what the suffix origin means.

        Args:
            origin (str): Suffix origin.

        Returns:
            str: Meaning of the suffix origin.
        """
        suffix_origin = {
            "MANUAL": "The IP address suffix was manually specified.",
            "WELLKNOWN": "The IP address suffix is from a"
            " well-known source.",
            "DHCP": "The IP address suffix was provided by DHCP settings.",
            "LINK": "The IP address suffix was obtained from the"
            " link-layer address.",
            "RANDOM": "The IP address suffix was obtained from"
            " a random source.",
            "OTHER": "The IP address suffix was obtained from another source,"
            " such as a VPN."
        }

        return suffix_origin[origin.upper()]

    def _popup_refresh_changes(self, title: str = "",
                               seconds: int = 5) -> None:
        """Displays a pop-up window.

        Args:
            title (str, optional): Window title. Defaults to "" (app name).
            seconds (int, optional): Seconds that the window will be displayed.
                Defaults to 5.
        """
        popup = ttk.Toplevel(title=APPNAME if not title else title,
                             resizable=(False, False),
                             minsize=(400, 70),
                             topmost=True)

        # Lock the main window
        popup.grab_set()

        # Center the popup window on the screen
        w_win = popup.winfo_screenwidth()
        h_win = popup.winfo_screenheight()

        x = (w_win - popup.winfo_reqwidth()) / 2
        y = (h_win - popup.winfo_reqheight()) / 2
        popup.geometry(f"+{int(x)}+{int(y)}")

        # Disable close button
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        pbar = ttk.Progressbar(popup)
        pbar.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        text = ttk.Label(popup, text="Refreshing changes...", wraplength=350)
        text.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        popup.columnconfigure(0, weight=1)
        popup.columnconfigure(1, weight=1)

        # Update the progress bar
        def update_pbar(prog):
            try:
                iters = 101
                waiting_time = seconds / iters

                for i in range(iters):
                    prog.configure(value=i)
                    sleep(waiting_time)
            except:  # pylint: disable=bare-except # noqa
                pass

        th = threading.Thread(target=update_pbar, args=(pbar,))
        th.start()

        mseconds = seconds * 1000 + 500
        popup.after(mseconds, popup.destroy)

        return

    def _save_profile(self) -> None:
        """Save profile into the user folder."""

        nap = NetAdapProfiles(
            ip=self._d_ip_addr.get().strip(),
            mask=self._d_subnet.get().strip(),
            gateway=self._d_gateway.get().strip(),
            pref_dns=self._d_pref_dns_server.get().strip(),
            alt_dns=self._d_alt_dns_server.get().strip(),
        )

        nap.save_profile_popup()

        return

    def _update_info(self) -> None:
        """Update the network adapter data."""

        ni = NetworkAdapters()
        info = ni.get_info()

        info = info[self.index]

        self.name = info["name"]
        self.desc = info["desc"]
        self.status = info["status"]
        self.mac = info["mac"]
        self.ip = info["ip"]
        self.mask = info["mask"]
        self.gateway = info["gateway"]
        prefix_origin = info["prefix_origin"]
        self.prefix_origin = prefix_origin.upper(
        ) if prefix_origin == "Dhcp" else prefix_origin
        suffix_origin = info["suffix_origin"]
        self.suffix_origin = suffix_origin.upper(
        ) if suffix_origin == "Dhcp" else suffix_origin
        self.pref_dns = info["pref_dns"]
        self.alt_dns = info["alt_dns"]

        return

    def apply_changes(self) -> None:
        """Set the configuration specified in the widgets for
        the network adapter.
        """
        try:

            ni = NetworkAdapters()

            ip = self._d_ip_addr.get().strip()
            mask = self._d_subnet.get().strip()
            gateway = self._d_gateway.get().strip()
            pref_dns = self._d_pref_dns_server.get().strip()
            alt_dns = self._d_alt_dns_server.get().strip()

            def show_error(msg):
                Messagebox.show_error(
                    message=msg,
                    title=f"{APPNAME} - Invalid data",
                    padding=(30, 30),
                    width=100)

            if not ni.validate_ipv4(ip):
                show_error("Invalid IP address.")
                return

            if not ni.validate_subnet_mask(mask):
                show_error("Invalid subnet mask.")
                return

            if gateway == "":
                gateway = "0.0.0.0"
            elif not ni.validate_ipv4(gateway):
                show_error("Invalid default gateway.")
                return

            if pref_dns and not ni.validate_ipv4(pref_dns):
                show_error("Invalid preferred DNS server.")
                return

            if alt_dns and not ni.validate_ipv4(alt_dns):
                show_error("Invalid alternate DNS server.")
                return

            if pref_dns and pref_dns == alt_dns:
                show_error(
                    "The preferred and alternate"
                    " DNS servers can not be the same.")
                return

            if not pref_dns and alt_dns:
                pref_dns = alt_dns
                alt_dns = ""

            msg = ("Do you want to apply this configuration to"
                   f" '{self.name}' adapter?\n"
                   f"\tIP address: {ip}\n"
                   f"\tSubnet mask: {mask}\n"
                   f"\tDefault gateway: {gateway}\n"
                   "\tPreferred DNS Server:"
                   f" {'(none)'if not pref_dns else pref_dns}\n"
                   "\tAlternate DNS Server:"
                   f" {'(none)' if not alt_dns else alt_dns}\n")

            dialog_title = "Change the network adapter properties"

            dialog = MessageDialog(message=msg,
                                   title=dialog_title,
                                   buttons=["Apply", "Cancel"],
                                   padding=(30, 30),
                                   width=100)

            dialog.show()

            if dialog.result == "Apply":

                if self._entries_bck["_d_ip_addr"] == ip:
                    ni.reset_ip(self.index)

                ni.set_ip_mask(self.index, ip, mask)

                if gateway != "0.0.0.0":
                    try:
                        ni.reset_def_gateway(self.index)
                    except KeyError:
                        pass
                    ni.set_def_gateway(self.index, gateway)

                if not pref_dns and not alt_dns:
                    ni.reset_dns_servers(self.index)
                else:
                    ni.set_dns_servers(self.index, pref_dns, alt_dns)

                self.toast_notification(
                    f"Configuration applied for '{self.name}' adapter.")

                # Regenerate widgets in a thread so as not to crash the app
                def regenerate_wd():
                    sleep(5)
                    self.update_widgets()

                th = threading.Thread(target=regenerate_wd)
                th.start()

                # Show popup info windows
                self._popup_refresh_changes(
                    title=self.name, seconds=LOADING_TIME)

                return
        except:  # pylint: disable=bare-except # noqa
            traceback.print_exc()
            with open(f"{APPNAME.lower()}_error.log", mode="w",
                      encoding="utf-8") as file:
                traceback.print_exc(file=file)

            Messagebox.show_error(
                message="The configuration could not be applied.",
                title=f"{APPNAME} - Error",
                padding=(30, 30),
                width=100)

    def apply_profile(self) -> None:
        """Apply a saved profile."""
        selection = NetAdapProfiles().manage_profiles(select=True)

        if not selection:
            return

        # -- IP address --
        self._d_ip_addr.delete(0, tk.END)
        self._d_ip_addr.insert(0, selection["ip"])

        # -- Subnet mask --
        self._d_subnet.delete(0, tk.END)
        self._d_subnet.insert(0, selection["mask"])

        # -- Default gateway --
        self._d_gateway.delete(0, tk.END)
        self._d_gateway.insert(0, selection["gateway"])

        # -- Preferred DNS Server --
        self._d_pref_dns_server.delete(0, tk.END)
        self._d_pref_dns_server.insert(0, selection["pref_dns"])

        # -- Alternate DNS Server --
        self._d_alt_dns_server.delete(0, tk.END)
        self._d_alt_dns_server.insert(0, selection["alt_dns"])

        if selection["apply"]:
            self.apply_changes()

        return

    def copy_clipboard(self) -> None:
        """Copy all network adapter information to the clipboard."""

        info = (
            f"Index: {self.index}"
            f"\nName: {self.name}"
            f"\nDescription: {self.desc}"
            f"\nStatus: {self._d_status.cget('text')}"
            f"\nMAC address: {self._d_mac_addr.get()}"
            f"\nIP address: {self._d_ip_addr.get()}"
            f"\nSubnet mask: {self._d_subnet.get()}"
            f"\nDefault gateway: {self._d_gateway.get()}"
            f"\nPrefix Origin: {self._d_prefix_origin.cget('text')}"
            f"\nSuffix Origin: {self._d_suffix_origin.cget('text')}"
            f"\nPreferred DNS Server: {self._d_pref_dns_server.get()}"
            f"\nAlternate DNS Server: {self._d_alt_dns_server.get()}\n"
        )

        self.toast_notification(
            f"'{self.name}' network adapter information copied"
            " to theclipboard.")

        pyperclip.copy(info)

        return

    def create(self, frame: ttk.Frame, row: int,
               bootstyle: str = "default") -> None:
        """Create the main widget that will contain all
        the network adapter information.

        Args:
            frame (ttk.Frame): Master frame where the Labelframe
                will be hosted.
            row (int): Row where the Labelframe will be placed
                in the master frame.
            bootstyle (str): ttk.Labelframe border style.
        """
        self._labelframe = ttk.Labelframe(
            frame,
            text=f"{self.name} - {self.desc}",
            relief="solid",
            borderwidth=10,
            bootstyle=bootstyle)

        self._labelframe.grid(row=row, column=0, padx=10,
                              pady=10, sticky="nsew")

        self.generate_widgets()

        self._entries_wd_bck()

        return

    def destroy(self) -> None:
        """Destroy the Labelframe where all the network adapter
        information is hosted.
        """
        self._labelframe.destroy()

    def endis_adapter(self, disable=False) -> None:
        """Enable or disable the network adapter. It displays a dialog box
        requesting confirmation from the user.

        Args:
            disable (bool, optional): If True, the adapter is disabled.
                Defaults to False (enabled).
        """
        msg = f"'{self.name}' will be " + \
            ("disabled" if disable else "enabled") + \
            ", do you want to continue?"

        dialog_title = ("Disable" if disable else "Enable") + \
            " network adapter"

        dialog = MessageDialog(message=msg,
                               title=dialog_title,
                               buttons=["Accept", "Cancel"],
                               padding=(30, 30))

        dialog.show()

        if dialog.result == "Accept":
            # Enable/Disabled adapter
            ni = NetworkAdapters()

            if disable:
                ni.disable_adapter(self.name)
            else:
                ni.enable_adapter(self.name)

            th_toast = threading.Thread(target=self.toast_notification, args=(
                f"'{self.name}' has been " +
                ("disabled." if disable else "enabled."),))
            th_toast.start()

            # Regenerate widgets in a thread so as not to crash the app
            def regenerate_wd():
                sleep(5)
                self.update_widgets()

            th = threading.Thread(target=regenerate_wd)
            th.start()

            # Show popup info windows
            self._popup_refresh_changes(
                title=self.name, seconds=LOADING_TIME)

        return

    def generate_widgets(self) -> None:
        """Create all widgets where the network adapter
        information is hosted
        """
        # ---------
        # | ROW 0 |
        # ---------

        # -- Status --
        status_style = "dark"
        if self.status == "Up":
            status_style = "success"
        elif self.status == "Disconnected":
            status_style = "info"
        elif self.status == "Disabled":
            status_style = "danger"
        l_status = ttk.Label(self._labelframe, text="Status:")
        self._d_status = ttk.Label(
            self._labelframe, bootstyle=f"{status_style}",
            text=self.status, font=("Helvetica", 8, "bold"))

        self._d_status.grid(row=0, column=1, padx=5, pady=5)
        l_status.grid(row=0, column=0, padx=(15, 5), pady=5)

        # -- MAC address --
        l_mac_addr = ttk.Label(self._labelframe, text="MAC address:")
        self._d_mac_addr = ttk.Entry(self._labelframe, width=20,
                                     justify="center", bootstyle="light")
        self._d_mac_addr.insert(0, self.mac if self.mac else "-")
        self._d_mac_addr.config(state="readonly")

        l_mac_addr.grid(row=0, column=2, padx=(15, 5), pady=5)
        self._d_mac_addr.grid(row=0, column=3, padx=5, pady=5)

        # -- Manual checkbutton --
        self._b_manual = ttk.Checkbutton(
            self._labelframe, bootstyle="round-toggle",
            command=self._enable_dhcp)
        l_manual = ttk.Label(self._labelframe, text="Manual")

        self._b_manual.grid(row=0, column=4, padx=(15, 5), pady=5, sticky="e")
        l_manual.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # -- Select action button --
        self._m_action = ttk.Menubutton(
            self._labelframe, bootstyle="outline", text="Select action")
        self._m_action.menu = ttk.Menu(self._m_action)
        self._m_action["menu"] = self._m_action.menu
        self._m_action.menu.add_command(
            label="Apply changes", command=self.apply_changes)
        self._m_action.menu.add_command(label="Apply profile",
                                        command=self.apply_profile)
        self._m_action.menu.add_command(
            label="Copy information",
            command=self.copy_clipboard)
        if self.status == "Disabled" or self.status == "Not Present":
            self._b_manual.state(['disabled'])
            self._m_action.menu.add_command(
                label="Enable network adapter", command=self.endis_adapter)
        else:
            self._m_action.menu.add_command(
                label="Disable network adapter",
                command=lambda: self.endis_adapter(disable=True))
        self._m_action.menu.add_command(
            label="Save profile", command=self._save_profile)

        self._m_action.grid(row=0, column=6, columnspan=2,
                            padx=(15, 5), pady=5, sticky="w")

        # ---------
        # | ROW 1 |
        # ---------

        # -- IP address --
        l_ip_addr = ttk.Label(self._labelframe, text="IP address:")
        self._d_ip_addr = ttk.Entry(
            self._labelframe, width=15, justify="center")
        self._d_ip_addr.insert(0, self.ip)

        l_ip_addr.grid(row=1, column=0, padx=(15, 5), pady=5)
        self._d_ip_addr.grid(row=1, column=1, padx=5, pady=5)

        # -- Subnet mask --
        l_subnet = ttk.Label(self._labelframe, text="Subnet mask:")
        self._d_subnet = ttk.Entry(
            self._labelframe, width=15, justify="center")
        self._d_subnet.insert(0, self.mask)

        l_subnet.grid(row=1, column=2, padx=(15, 5), pady=5)
        self._d_subnet.grid(row=1, column=3, padx=5, pady=5)

        # -- Default gateway --
        l_gateway = ttk.Label(self._labelframe, text="Default gateway:")
        self._d_gateway = ttk.Entry(
            self._labelframe, width=15, justify="center")
        self._d_gateway.insert(0, self.gateway)

        l_gateway.grid(row=1, column=4, padx=(15, 5), pady=5)
        self._d_gateway.grid(row=1, column=5, padx=5, pady=5)

        # -- Prefix Origin --
        l_prefix_origin = ttk.Label(self._labelframe, text="Prefix Origin:")
        self._d_prefix_origin = ttk.Label(
            self._labelframe, text=self.prefix_origin)

        l_prefix_origin.grid(row=1, column=6, padx=(15, 5), pady=5)
        self._d_prefix_origin.grid(row=1, column=7, padx=5, pady=5)

        if self.prefix_origin:
            ToolTip(
                self._d_prefix_origin, text=self._get_prefix_tooltip(
                    self.prefix_origin), delay=500)

        # -- Suffix Origin --
        l_suffix_origin = ttk.Label(self._labelframe, text="Suffix Origin:")
        self._d_suffix_origin = ttk.Label(
            self._labelframe, text=self.suffix_origin)

        l_suffix_origin.grid(row=2, column=6, padx=(15, 5), pady=5)
        self._d_suffix_origin.grid(row=2, column=7, padx=5, pady=5)

        if self.suffix_origin:
            ToolTip(
                self._d_suffix_origin, text=self._get_suffix_tooltip(
                    self.suffix_origin), delay=500)

        # ---------
        # | ROW 2 |
        # ---------

        # -- Preferred DNS Server --
        l_pref_dns_server = ttk.Label(
            self._labelframe, text="Preferred DNS Server:")
        self._d_pref_dns_server = ttk.Entry(
            self._labelframe, width=15, justify="center")
        self._d_pref_dns_server.insert(0, self.pref_dns)

        l_pref_dns_server.grid(row=2, column=0, padx=(15, 5), pady=5)
        self._d_pref_dns_server.grid(row=2, column=1, padx=5, pady=5)

        # -- Alternate DNS Server --
        l_alt_dns_server = ttk.Label(
            self._labelframe, text="Alternate DNS Server:")
        self._d_alt_dns_server = ttk.Entry(
            self._labelframe, width=15, justify="center")
        self._d_alt_dns_server.insert(0, self.alt_dns)

        l_alt_dns_server.grid(row=2, column=2, padx=(15, 5), pady=5)
        self._d_alt_dns_server.grid(row=2, column=3, padx=5, pady=5)

        if self.prefix_origin == "Manual":
            self._b_manual.state(["selected"])

        if self.disabled:
            self._disable_all_wd()
        else:
            self._change_wd_state()

        return

    def toast_notification(self, toast_msg: str) -> None:
        """Display a notification toast with a message.

        Args:
            toast_msg (str): Message to be displayed.
        """
        toast = ToastNotification(
            title=APPNAME,
            message=toast_msg,
            duration=5000,
            icon="\u2714"
        )
        toast.show_toast()

        return

    def update_widgets(self) -> None:
        """Update widgets with network adapter information."""

        self._update_info()

        self._enabled_all_wd()

        # ---------
        # | ROW 0 |
        # ---------

        # -- Status --
        status_style = "dark"
        if self.status == "Up":
            status_style = "success"
        elif self.status == "Disconnected":
            status_style = "info"
        elif self.status == "Disabled":
            status_style = "danger"

        self._d_status.configure(
            text=self.status, bootstyle=f"{status_style}")

        # -- MAC address --
        self._d_mac_addr.delete(0, tk.END)
        self._d_mac_addr.insert(0, self.mac if self.mac else "-")

        # -- Select action button --
        for _ in range(self._m_action.menu.index("end")+1):
            self._m_action.menu.delete(0)

        self._m_action.menu.add_command(
            label="Apply changes", command=self.apply_changes)
        self._m_action.menu.add_command(
            label="Apply profile", command=self.apply_profile)
        self._m_action.menu.add_command(
            label="Copy information",
            command=self.copy_clipboard)
        if self.status == "Disabled" or self.status == "Not Present":
            self._b_manual.state(['disabled'])
            self._m_action.menu.add_command(
                label="Enable network adapter", command=self.endis_adapter)
        else:
            self._m_action.menu.add_command(
                label="Disable network adapter",
                command=lambda: self.endis_adapter(disable=True))
        self._m_action.menu.add_command(
            label="Save profile", command=self._save_profile)

        # ---------
        # | ROW 1 |
        # ---------

        # -- IP address --
        self._d_ip_addr.delete(0, tk.END)
        self._d_ip_addr.insert(0, self.ip)

        # -- Subnet mask --
        self._d_subnet.delete(0, tk.END)
        self._d_subnet.insert(0, self.mask)

        # -- Default gateway --
        self._d_gateway.delete(0, tk.END)
        self._d_gateway.insert(0, self.gateway)

        # -- Prefix Origin --
        self._d_prefix_origin.configure(text=self.prefix_origin)

        if self.prefix_origin:
            ToolTip(
                self._d_prefix_origin, text=self._get_prefix_tooltip(
                    self.prefix_origin), delay=500)

        # -- Suffix Origin --
        self._d_suffix_origin.configure(text=self.suffix_origin)

        if self.suffix_origin:
            ToolTip(
                self._d_suffix_origin, text=self._get_suffix_tooltip(
                    self.suffix_origin), delay=500)

        # ---------
        # | ROW 2 |
        # ---------

        # -- Preferred DNS Server --
        self._d_pref_dns_server.delete(0, tk.END)
        self._d_pref_dns_server.insert(0, self.pref_dns)

        # -- Alternate DNS Server --
        self._d_alt_dns_server.delete(0, tk.END)
        self._d_alt_dns_server.insert(0, self.alt_dns)

        if self.prefix_origin == "Manual":
            self._b_manual.state(["selected"])
        else:
            self._b_manual.state(["!selected"])

        if self.disabled:
            self._disable_all_wd()
        else:
            self._change_wd_state()

        self._entries_wd_bck()

        return
