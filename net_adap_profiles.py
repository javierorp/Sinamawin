"""Manage profiles including the necessary widgets"""

import json
import os
import re
import traceback
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.dialogs.dialogs import MessageDialog, Messagebox

from network_adapters import NetworkAdapters

APPNAME = "Sinamawin"


class NetAdapProfiles:
    """Management of network adapter profiles"""

    def __init__(self, ip: str = "", mask: str = "255.255.255.0",
                 gateway: str = "0.0.0.0", pref_dns: str = "",
                 alt_dns: str = "", name: str = "") -> None:
        self.name = name
        self.ip = ip
        self.mask = mask
        self.gateway = gateway
        self.pref_dns = pref_dns
        self.alt_dns = alt_dns
        self._manage_prof_popup = None  # Manage profile popup
        self._return = None  # Return data

    def delete_profile(self, name: str) -> None:
        """Delete a profile from the profile file.

        Args:
            name (str): Profile name to be deleted.
        """
        profiles = self.get_profiles()
        del profiles[name]

        if self.save_profiles(profiles):
            self.toast_notification(f"Profile '{name}' successfully deleted.")

    def get_profiles(self) -> dict:
        """Get profiles from the profile file.

        Returns:
            dict: All saved profiles.
        """
        profiles = {}
        prof_path = os.environ.get(f"{APPNAME}_PROFILES")
        if os.path.exists(prof_path):
            with open(prof_path, "r", encoding="utf-8") as file:
                profiles = json.load(file)

        return profiles

    def manage_profiles(self, select: bool = False) -> dict:
        """Displays a window for managing profiles.

        Args:
            select (bool, optional): If True displays "Select" and
                "Select & Apply" buttons instead of "New", "Edit" and
                "Delete" buttons. Defaults to False.

        Returns:
            dict: Return the selected profile.
        """

        self._manage_prof_popup = None

        popup = ttk.Toplevel(title=f"{APPNAME} - Manage profiles",
                             resizable=(False, False),
                             size=(760, 250))

        prof_table = ttk.Treeview(popup)
        prof_table["columns"] = (
            "NAME", "IP", "SUBNET_MASK", "GATEWAY", "PREF_DNS", "ALT_DNS")

        # Configure the style of heading in the table
        prof_table_style = ttk.Style()
        prof_table_style.configure('Treeview.Heading',
                                   background="#C4790E",
                                   foreground="white",
                                   font=('Arial', 8, 'bold'))
        prof_table_style.configure('Treeview',
                                   rowheight=25
                                   )

        # Configure columns
        prof_table.column("#0", anchor="center", width=0, stretch=False)

        for column in prof_table["columns"]:
            prof_table.column(column,  stretch=False,
                              anchor="center", width=120)
            prof_table.heading(column, text=column, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            popup, bootstyle="primary-round", orient="vertical",
            command=prof_table.yview)
        scrollbar.grid(row=0, column=4, sticky="ns", padx=(5, 10))

        prof_table.configure(yscrollcommand=scrollbar.set)

        # Add profiles to the table
        profiles = self.get_profiles()

        for index, (name, data) in enumerate(profiles.items()):
            prof_table.insert(parent="", index="end", iid=index, text="",
                              values=(name,
                                      data["ip"],
                                      data["mask"],
                                      data["gateway"],
                                      data["pref_dns"],
                                      data["alt_dns"]
                                      ))

        prof_table.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Functions that provide utility to the buttons
        def get_selected_row(show_error: bool = True) -> str:
            """Gets the row selected by the user.

            Args:
                show_error (bool, optional): If True displays an error message
                    if the user has not selected any rows. Defaults to True.

            Returns:
                str: Name of the selected profile.
            """
            selection = prof_table.selection()
            name = ""

            if selection:
                self._manage_prof_popup = popup
                name = list(profiles.keys())[int(selection[0])]

            elif show_error:
                Messagebox.show_error(
                    message="No row is selected.",
                    title=f"{APPNAME} - Error",
                    padding=(30, 30),
                    width=100)

            return name

        def new_profile() -> None:
            """Open a pop-up window to save a new profile.
            If one is selected, copy the information.
            """
            name = get_selected_row(show_error=False)

            self.name = ""
            self.ip = profiles[name]["ip"] if name else ""
            self.mask = profiles[name]["mask"] if name else "255.255.255.0"
            self.gateway = profiles[name]["gateway"] if name else "0.0.0.0"
            self.pref_dns = profiles[name]["pref_dns"] if name else ""
            self.alt_dns = profiles[name]["alt_dns"] if name else ""

            self._manage_prof_popup = popup
            self.save_profile_popup(remove=self.name)

            return

        def edit_profile() -> None:
            """Open a pop-up window to edit a profile's information."""
            name = get_selected_row()

            if not name:
                return

            self.name = name
            self.ip = profiles[name]["ip"]
            self.mask = profiles[name]["mask"]
            self.gateway = profiles[name]["gateway"]
            self.pref_dns = profiles[name]["pref_dns"]
            self.alt_dns = profiles[name]["alt_dns"]

            self._manage_prof_popup = popup
            self.save_profile_popup(f"Edit profile '{name}'", remove=self.name)

            return

        def delete_profile() -> None:
            """Delete a profile by requesting confirmation from the user."""
            name = get_selected_row()

            if not name:
                return

            msg = f"Do you want to remove the profile '{name}'?"
            dialog_title = f"{APPNAME} - Remove {name}"
            dialog = MessageDialog(message=msg,
                                   title=dialog_title,
                                   buttons=["Accept", "Cancel"],
                                   padding=(30, 30),
                                   width=70)

            dialog.show()

            if dialog.result == "Accept":
                self.delete_profile(name)
                # Refresh the window
                popup.destroy()
                self.manage_profiles()

        def select_apply_profile(apply: bool = False) -> None:
            """'Select' or 'Select & Apply' a profile.

            Args:
                apply (bool, optional): Indicate whether "Select" (False) or
                    "Select and Apply" (True). Defaults to False.
            """
            name = get_selected_row()

            if not name:
                return

            self._return = {
                "name": name,
                "ip": profiles[name]["ip"],
                "mask": profiles[name]["mask"],
                "gateway": profiles[name]["gateway"],
                "pref_dns": profiles[name]["pref_dns"],
                "alt_dns": profiles[name]["alt_dns"],
                "apply": apply
            }

            # Destroy the popup window
            popup.destroy()

        # Buttons
        if select:  # "Select" and "Select & Apply"
            b_select = ttk.Button(popup, text="Select",
                                  command=select_apply_profile)
            b_sel_apply = ttk.Button(
                popup, text="Select & Apply",
                command=lambda: select_apply_profile(True))
            b_select.grid(row=1, column=1, padx=5, pady=10)
            b_sel_apply.grid(row=1, column=2, padx=5, pady=10)

        else:  # "New", "Edit" and "Delete"
            b_new = ttk.Button(popup, text="New",
                               command=new_profile)
            b_edit = ttk.Button(popup, text="Edit",
                                bootstyle="dark", command=edit_profile)
            b_remove = ttk.Button(popup, text="Delete",
                                  bootstyle="danger",
                                  command=delete_profile)
            b_new.grid(row=1, column=0, padx=5, pady=10, sticky="e")
            b_edit.grid(row=1, column=1, padx=5, pady=10)
            b_remove.grid(row=1, column=2, padx=5, pady=10)

        # Adjust size of columns to window size
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        # Mouse wheel behavior
        def popup_window_scroll(_):
            """To avoid propagating the event to the main window."""
            scrollbar.set(*prof_table.yview())
            return "break"

        popup.bind("<MouseWheel>", popup_window_scroll)

        # Wait until the popup window is destroyed
        popup.wait_window()

        return self._return

    def save_profile(self, popup: ttk.Toplevel = None,
                     remove: str = "") -> None:
        """Validate that the profile is valid and save it in the profile file.

        Args:
            popup (ttk.Toplevel, optional): Raise the window in the stack of
                window and destroys the window at the end. Defaults to None.
            remove (str, optional): Name of the profile to be deleted,
                replaced by the new one. Defaults to "".
        """
        try:
            # Remove characters not allowed
            self.name = re.sub(r"[^\w\s\-]", "", self.name)

            ni = NetworkAdapters()

            def show_error(msg):
                Messagebox.show_error(
                    message=msg,
                    title=f"{APPNAME} - Invalid data",
                    padding=(30, 30),
                    width=100)

                if popup:
                    # Raise the window in the stack of windows
                    popup.lift()

            if not self.name or not self.name.isascii():
                show_error("Invalid profile name.")
                return

            if not ni.validate_ipv4(self.ip):
                show_error("Invalid IP address.")
                return

            if not ni.validate_subnet_mask(self.mask):
                show_error("Invalid subnet mask.")
                return

            if self.gateway == "":
                self.gateway = "0.0.0.0"
            elif not ni.validate_ipv4(self.gateway):
                show_error("Invalid default gateway.")
                return

            if self.pref_dns and not ni.validate_ipv4(self.pref_dns):
                show_error("Invalid preferred DNS server.")
                return

            if self.alt_dns and not ni.validate_ipv4(self.alt_dns):
                show_error("Invalid alternate DNS server.")
                return

            if self.pref_dns and self.pref_dns == self.alt_dns:
                show_error(
                    "The preferred and alternate"
                    " DNS servers can not be the same.")
                return

            if not self.pref_dns and self.alt_dns:
                self.pref_dns = self.alt_dns
                self.alt_dns = ""

            profiles = self.get_profiles()

            new_profile = {
                "ip": self.ip,
                "mask": self.mask,
                "gateway": self.gateway,
                "pref_dns": self.pref_dns,
                "alt_dns": self.alt_dns
            }

            if profiles and self.name in list(profiles.keys()):
                msg = (f"The profile '{self.name}' already exists."
                       " Do you want to replace it with the new one?")

                dialog_title = f"{APPNAME} - Duplicate profile name"
                dialog = MessageDialog(message=msg,
                                       title=dialog_title,
                                       buttons=["Accept", "Cancel"],
                                       padding=(30, 30),
                                       width=70)

                dialog.show()

                if dialog.result == "Accept":
                    profiles[self.name] = new_profile

                    # Remove the old profile
                    if remove and remove != self.name:
                        del profiles[remove]
                else:
                    return

            else:
                profiles[self.name] = new_profile

                # Remove the old profile
                if remove:
                    del profiles[remove]

            if self.save_profiles(profiles):
                self.toast_notification("Profile saved successfully.")

            if popup:
                popup.destroy()

            # Refresh the window
            if self._manage_prof_popup:
                self._manage_prof_popup.destroy()
                self.manage_profiles()

            return

        except:  # pylint: disable=bare-except # noqa
            traceback.print_exc()
            Messagebox.show_error(
                message="The profile could not be saved.",
                title=f"{APPNAME} - Error",
                padding=(30, 30),
                width=100)

    def save_profile_popup(self, title: str = "New profile",
                           remove: str = "") -> None:
        """Window to save/edit the profile information.

        Args:
            title (str, optional): Title of the window.Defaults to
                "New profile".
            remove (str, optional): Profile name to be deleted. Defaults to "".
        """

        popup = ttk.Toplevel(title=f"{APPNAME} - {title}",
                             resizable=(False, False))

        # ---------
        # | ROW 0 |
        # ---------
        l_name = ttk.Label(popup, text="Profile name:",
                           font=("Arial", 9, "bold"))
        d_name = ttk.Entry(
            popup, width=30, justify="left")
        if self.name:
            d_name.insert(0, self.name)

        l_name.grid(row=0, column=0, padx=(25, 5), pady=(15, 5))
        d_name.grid(row=0, column=1, padx=5, pady=(15, 5))

        # ---------
        # | ROW 1 |
        # ---------

        # -- IP address --
        l_ip_addr = ttk.Label(popup, text="IP address:")
        d_ip_addr = ttk.Entry(
            popup, width=15, justify="center")
        d_ip_addr.insert(0, self.ip)

        l_ip_addr.grid(row=1, column=0, padx=(25, 5), pady=5)
        d_ip_addr.grid(row=1, column=1, padx=5, pady=5)

        # -- Subnet mask --
        l_subnet = ttk.Label(popup, text="Subnet mask:")
        d_subnet = ttk.Entry(
            popup, width=15, justify="center")
        d_subnet.insert(0, self.mask)

        l_subnet.grid(row=1, column=2, padx=(15, 5), pady=5)
        d_subnet.grid(row=1, column=3, padx=5, pady=5)

        # -- Default gateway --
        l_gateway = ttk.Label(popup, text="Default gateway:")
        d_gateway = ttk.Entry(
            popup, width=15, justify="center")
        d_gateway.insert(0, self.gateway)

        l_gateway.grid(row=1, column=4, padx=(15, 5), pady=5)
        d_gateway.grid(row=1, column=5, padx=(5, 25), pady=5)

        # ---------
        # | ROW 2 |
        # ---------

        # -- Preferred DNS Server --
        l_pref_dns_server = ttk.Label(
            popup, text="Preferred DNS Server:")
        d_pref_dns_server = ttk.Entry(
            popup, width=15, justify="center")
        d_pref_dns_server.insert(0, self.pref_dns)

        l_pref_dns_server.grid(row=2, column=0, padx=(25, 5), pady=5)
        d_pref_dns_server.grid(row=2, column=1, padx=5, pady=5)

        # -- Alternate DNS Server --
        l_alt_dns_server = ttk.Label(
            popup, text="Alternate DNS Server:")
        d_alt_dns_server = ttk.Entry(
            popup, width=15, justify="center")
        d_alt_dns_server.insert(0, self.alt_dns)

        l_alt_dns_server.grid(row=2, column=2, padx=(15, 5), pady=5)
        d_alt_dns_server.grid(row=2, column=3, padx=5, pady=5)

        # ---------
        # | ROW 3 |
        # ---------
        def clear_entries():
            d_name.delete(0, tk.END)
            d_ip_addr.delete(0, tk.END)
            d_subnet.delete(0, tk.END)
            d_subnet.insert(0, "255.255.255.0")
            d_gateway.delete(0, tk.END)
            d_gateway.insert(0, "0.0.0.0")
            d_pref_dns_server.delete(0, tk.END)
            d_alt_dns_server.delete(0, tk.END)

        def save_profile_data():
            self.name = d_name.get().strip()
            self.ip = d_ip_addr.get()
            self.mask = d_subnet.get()
            self.gateway = d_gateway.get()
            self.pref_dns = d_pref_dns_server.get()
            self.alt_dns = d_alt_dns_server.get()
            self.save_profile(popup, remove)

        b_clear = ttk.Button(popup, bootstyle="warning", text="Clear",
                             width=10, command=clear_entries)
        b_save = ttk.Button(popup,  text="Save", width=10,
                            command=save_profile_data)
        b_cancel = ttk.Button(popup, bootstyle="dark",
                              text="Cancel", command=popup.destroy, width=10)

        b_clear.grid(row=3, column=0, padx=5, pady=(5, 25))
        b_save.grid(row=3, column=4, padx=5, pady=(5, 25), sticky="e")
        b_cancel.grid(row=3, column=5, padx=5, pady=(5, 25))

    def save_profiles(self, profiles: dict) -> bool:
        """Save the profiles in the profile file.

        Args:
            profiles (dict): Profiles to be saved.

        Returns:
            bool: True if saved.
        """
        with open(os.environ.get(f"{APPNAME}_PROFILES"), "w",
                  encoding="utf-8") as file:
            json.dump(dict(sorted(profiles.items())), file, indent=4)

        return True

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
