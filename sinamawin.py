"""Sinamawin - Simple Network Adapter Manager for Windows"""

import ctypes
from datetime import datetime
import json
import os
import re
import threading
import tkinter as tk
import traceback
import webbrowser
import requests
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.dialogs.dialogs import MessageDialog
from PIL import Image, ImageTk
from packaging.version import Version

from network_adapters import NetworkAdapters
from net_adap_widget import NetAdapWidget
from net_adap_profiles import NetAdapProfiles
from arp import arp_widget


APPNAME = "Sinamawin"
APP_INFO = None
ICON = "./resources/sinamawin.ico"  # App icon
ABOUT_LOGO = ""  # App logo in About window
ADMIN = False  # Privileges
MAIN_FRAME = None  # Frame containing the network adapters and the scrollbar
NETADAPTERS = None  # Network adapters
NETADAPTERS_FRAME = None  # Frame containing all the frames
# of the network adapters
NETFRAMES = []  # Frames of all network adapters
NOT_FOUND_TEXT = None  # Label when no adapters are found


def about_popup() -> None:
    """Pop-up window with application information."""

    popup = ttk.Toplevel(title=f"About {APPNAME}",
                         resizable=(False, False))

    # Logo
    i_logo = Image.open("./resources/sinamawin.png")
    i_logo = i_logo.resize((70, 70))

    global ABOUT_LOGO  # pylint: disable=global-statement
    ABOUT_LOGO = ImageTk.PhotoImage(i_logo)
    l_logo = tk.Label(popup, image=ABOUT_LOGO)
    l_logo.grid(row=0, column=0, padx=(50, 10), pady=10, rowspan=2, sticky="w")

    # App name
    appname_txt = APPNAME
    if APP_INFO:
        appname_txt = (f"{APPNAME} (v{APP_INFO['version']}"
                       f"{'*' if not APP_INFO['up_to_date'] else ''}")

        if APP_INFO["version_date"]:
            ver_date = datetime.strptime(
                APP_INFO["version_date"], "%Y-%m-%dT%H:%M:%SZ")
            appname_txt = appname_txt + f" - {ver_date.strftime('%b %Y')}"

        appname_txt = appname_txt + ")"

    l_app = ttk.Label(popup, text=appname_txt,
                      font=("Arial", 14, "bold"))
    l_app.grid(row=0, column=0, padx=10, pady=(10, 0))

    l_app_desc = ttk.Label(
        popup, text="Simple Network Adapter Manager for Windows",
        font=("Arial", 12))
    l_app_desc.grid(row=1, column=0, padx=10, pady=5)

    t_lic = tk.Text(popup, wrap="word", height=16,
                    relief="flat", font=("Arial", 11))
    t_lic.grid(row=2, column=0, padx=10, pady=10)

    t_lic.tag_configure("bold", font=("Arial", 11, "bold"))

    # Dev and GitHub
    t_lic.insert(tk.END, "This application has been developed by ")
    t_lic.tag_configure("dev", foreground="blue")
    t_lic.insert(tk.END, "Javier Orti", "dev")
    t_lic.insert(tk.END, " (April 2024) and the source code can be found on ")
    t_lic.tag_configure("github", foreground="blue")
    t_lic.insert(tk.END, "GitHub", "github")
    t_lic.insert(tk.END, ".\n\n")

    t_lic.tag_bind("dev", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://linktr.ee/javierorp"))
    t_lic.tag_bind("github", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://github.com/javierorp/Sinamawin"))

    # Licenses
    t_lic.tag_configure("header", font=("Arial", 12, "bold"))
    t_lic.insert(tk.END, "Licenses\n", "header")

    t_lic.insert(
        tk.END, ("This application is distributed under"
                 " GNU General Public License version 3 ("))
    t_lic.tag_configure("gplv3", foreground="blue")
    t_lic.insert(tk.END, "GPLv3", "gplv3")
    t_lic.insert(tk.END, ").\n")

    t_lic.tag_bind("gplv3", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://github.com/javierorp/"
                       "Sinamawin/blob/main/LICENSE"))

    # Licenses - resources
    t_lic.insert(tk.END, "\nLicenses of the resources used:\n")
    t_lic.insert(tk.END, "\t● ")
    t_lic.tag_configure("python", foreground="blue")
    t_lic.insert(tk.END, "Python\n", "python")
    t_lic.tag_configure("tkinter", foreground="blue")
    t_lic.insert(tk.END, "\t● ")
    t_lic.insert(tk.END, "Tkinter\n", "tkinter")
    t_lic.tag_configure("tcl", foreground="blue")
    t_lic.insert(tk.END, "\t● ")
    t_lic.insert(tk.END, "Tcl/Tk\n", "tcl")
    t_lic.tag_configure("ttk", foreground="blue")
    t_lic.insert(tk.END, "\t● ")
    t_lic.insert(tk.END, "ttkbootstrap\n", "ttk")

    t_lic.tag_bind("python", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://docs.python.org/3/license.html"))
    t_lic.tag_bind("tkinter", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://docs.python.org/3/library/tkinter.html"))
    t_lic.tag_bind("tcl", "<Button-1>",
                   lambda e: webbrowser.open(
                       "https://www.tcl.tk/software/tcltk/license.html"))
    t_lic.tag_bind("ttk", "<Button-1>", lambda e: webbrowser.open(
        "https://ttkbootstrap.readthedocs.io/en/latest/license/"))

    t_lic.insert(tk.END, "\nSome of the icons used are from ")
    t_lic.tag_configure("freepik", foreground="blue")
    t_lic.insert(tk.END, "Freepik", "freepik")
    t_lic.insert(tk.END, ".\n")

    t_lic.tag_bind("freepik", "<Button-1>", lambda e: webbrowser.open(
        "https://www.freepik.com"))

    if APP_INFO and not APP_INFO["up_to_date"]:
        t_lic.insert(tk.END, "\n *Download the latest version ", "bold")
        t_lic.tag_configure("last_version", foreground="blue",
                            font=("Arial", 11, "bold"))
        last_ver_date = datetime.strptime(
            APP_INFO["last_version_date"], "%Y-%m-%dT%H:%M:%SZ")
        t_lic.insert(
            tk.END,
            f"{APP_INFO['last_version']} ({last_ver_date.strftime('%b %Y')})",
            "last_version")
        t_lic.insert(tk.END, ".\n")

        t_lic.tag_bind("last_version", "<Button-1>", lambda e: webbrowser.open(
            APP_INFO["url"]))

    t_lic.configure(state="disabled")

    # Mouse wheel behavior
    def popup_window_scroll(_):
        """To avoid propagating the event to the main window."""
        return "break"

    popup.bind("<MouseWheel>", popup_window_scroll)

    return


def check_app_folder() -> None:
    """Check if the application folder/file exists and create it if necessary."""
    appdata_path = os.environ.get("APPDATA")

    # Use the application path if there is no user path
    if not appdata_path:
        appdata_path = "."

    appdata_path = f"{appdata_path}\\{APPNAME}"

    if not os.path.exists(appdata_path):
        os.mkdir(appdata_path)

    prefdata_path = appdata_path + "\\preferences"
    if not os.path.exists(prefdata_path):
        preferences = {
            "themename": "litera",
            "skip_vers": []
        }
        with open(prefdata_path, "w", encoding="utf-8") as file:
            json.dump(preferences, file, indent=4)

    # Save the profile path in an environment variable
    os.environ[f"{APPNAME}_PROFILES"] = f"{appdata_path}\\profiles"
    os.environ[f"{APPNAME}_PREFERENCES"] = prefdata_path

    return


def check_app_version() -> None:
    """Check if a new version is available."""
    try:
        version = ""
        last_version = ""
        last_version_date = ""

        # App version
        with open("setup.py", "r", encoding="utf-8") as f:
            content = f.read()
            version_match = re.search(r"version=['\"]([^'\"]*)['\"]", content)
            if version_match:
                version = version_match.group(1)
            else:
                return

        # Last version
        url = ("https://api.github.com/repos/javierorp/"
               "Sinamawin/releases/latest")
        req = requests.get(url, timeout=30)
        if req.status_code == 200:
            data = req.json()
            last_version = data["tag_name"]
            last_version_date = data["published_at"]
        else:
            return

        url_last_ver = ("https://github.com/javierorp/"
                        f"Sinamawin/releases/tag/{last_version}")

        global APP_INFO  # pylint: disable=global-statement
        APP_INFO = {
            "url": url_last_ver,
            "version": version,
            "version_date": "",
            "last_version": last_version,
            "last_version_date": last_version_date,
            "up_to_date": False
        }

        if Version(version) == Version(last_version):
            APP_INFO["up_to_date"] = True
            APP_INFO["version_date"] = last_version_date
            return
        else:
            url = "https://api.github.com/repos/javierorp/Sinamawin/releases"
            req = requests.get(url, timeout=30)

            if req.status_code == 200:
                releases = req.json()

                for release in releases:
                    if release["tag_name"] == version:
                        APP_INFO["version_date"] = release["published_at"]

            if Version(version) >= Version(last_version):
                APP_INFO["up_to_date"] = True
                return

        with open(os.environ[f"{APPNAME}_PREFERENCES"], "r",
                  encoding="utf-8") as fprefers:
            preferences = json.load(fprefers)

        # Skip version
        if last_version in preferences["skip_vers"]:
            return

        # Show "New version" modal
        title = f"{APPNAME} - New version"
        last_ver_datetime = datetime.strptime(
            last_version_date, "%Y-%m-%dT%H:%M:%SZ")
        msg = (f"New version available: {last_version}"
               f" ({last_ver_datetime.strftime('%b %Y')})")
        dialog = MessageDialog(message=msg,
                               title=title,
                               buttons=["Download", "Skip", "Cancel"],
                               padding=(30, 30),
                               width=100,
                               alert=True)

        dialog.show()

        if dialog.result == "Download":
            webbrowser.open(url_last_ver)
        elif dialog.result == "Skip":
            try:
                preferences["skip_vers"].append(last_version)

                with open(os.environ[f"{APPNAME}_PREFERENCES"], "w",
                          encoding="utf-8") as fprefers:
                    json.dump(preferences, fprefers, indent=4)
            except:  # pylint: disable=bare-except # noqa
                pass

    except:  # pylint: disable=bare-except # noqa
        pass


def create_net_wd(adapters: dict) -> None:
    """Create widgets with the information of each network adapter.

    Args:
        adapters (dict): Dictionary with the information
            of the network adapters.
    """
    if adapters:
        global NETADAPTERS_FRAME  # pylint: disable=W0602

        for idx, (a_idx, a_info) in enumerate(adapters.items()):
            netframe = NetAdapWidget(
                idx=a_idx,
                name=a_info["name"],
                desc=a_info["desc"],
                status=a_info["status"],
                mac=a_info["mac"],
                ip=a_info["ip"],
                mask=a_info["mask"],
                gateway=a_info["gateway"],
                prefix_origin=a_info["prefix_origin"],
                suffix_origin=a_info["suffix_origin"],
                pref_dns=a_info["pref_dns"],
                alt_dns=a_info["alt_dns"],
                disabled=not ADMIN
            )
            netframe.create(
                frame=NETADAPTERS_FRAME,
                row=idx
            )

            NETFRAMES.append(netframe)

        return
    else:
        global NOT_FOUND_TEXT  # pylint: disable=global-statement
        NOT_FOUND_TEXT = ttk.Label(
            MAIN_FRAME, text="No network adapter was found on the computer",
            font=("Arial", 12))
        NOT_FOUND_TEXT.grid(row=0, column=0)


def get_window_size() -> list:
    """Get the window size to be set.

    Returns:
        list: Width and height in pixels.
    """
    try:
        widths = {
            "1093x614": [1200, 600],
            "1097x617":  [1570, 800],
            "1280x720": [1400, 800],
            "1360x768": [970, 620],
            "1366x768": [970, 620],
            "1463x914": [1580, 950],
            "1707x1067": [1400, 800],
            "1920x1080": [980, 800],
            "2048x1280": [1200, 760],
            "2560x1440": [1400, 800],
            "2560x1600": [980, 700],
            "2752x1152": [1200, 800],
            "2293x960": [1400, 800],
            "3440x1440": [980, 800]
        }

        # Get the computer screen size
        user32 = ctypes.windll.user32
        w_width = user32.GetSystemMetrics(0)
        w_height = user32.GetSystemMetrics(1)

        return widths[f"{w_width}x{w_height}"]

    except:  # pylint: disable=bare-except # noqa
        return [int(w_width*0.85), int(w_height*0.80)]


def refresh() -> None:
    """Refresh information and widgets for all network adapters."""

    adapters = NetworkAdapters().get_info()

    global NETADAPTERS  # pylint: disable=global-statement
    NETADAPTERS = adapters

    global NETFRAMES  # pylint: disable=global-statement

    if isinstance(NETFRAMES, list):
        for netframe in NETFRAMES:
            netframe.destroy()

        NETFRAMES = []

        global NOT_FOUND_TEXT  # pylint: disable=global-statement
        if NOT_FOUND_TEXT:
            NOT_FOUND_TEXT.destroy()
            NOT_FOUND_TEXT = None

        create_net_wd(adapters)

        toast = ToastNotification(
            title=APPNAME,
            message="Network adapters refreshed.",
            duration=5000,
            icon="\u2714"
        )
        toast.show_toast()

    return


if __name__ == "__main__":
    try:
        # App folder
        check_app_folder()

        # Get network adapter info
        net_adapters = NetworkAdapters().get_info()
        NETADAPTERS = net_adapters

        # To know if the application has been launched as administrator.
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                ADMIN = True
        except:  # pylint: disable=bare-except # noqa
            pass

        # Assign an ID to display the icon in the taskbar on Windows
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APPNAME)

        WIDTH, HEIGHT = get_window_size()
        ADJ_HEIGHT = 1.06 if ADMIN else 1.11

        THEME = "litera"
        try:
            with open(os.environ[f"{APPNAME}_PREFERENCES"], "r",
                      encoding="utf-8") as fpref:
                prefs = json.load(fpref)

            THEME = prefs["themename"]
        except:  # pylint: disable=bare-except # noqa
            pass

        app = ttk.Window(title=APPNAME + (" [Admin]" if ADMIN else ""),
                         themename=THEME,
                         size=(int(WIDTH*1.025), int(HEIGHT*ADJ_HEIGHT)))
        app.resizable(False, False)

        # App icon in all windows
        app.iconbitmap(ICON)  # Set the bitmap for this window only
        app.iconbitmap(default=ICON)  # Set the default bitmap (.ico)
        app.iconbitmap(default='')  # Remove the default bitmap

        # App version
        threading.Thread(target=check_app_version).start()

        # Menu bar
        menubar = tk.Menu(app)
        app.config(menu=menubar)

        filemenu = tk.Menu(menubar)
        editmenu = tk.Menu(menubar)
        toolsmenu = tk.Menu(menubar)
        helpmenu = tk.Menu(menubar)

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Edit", menu=editmenu)
        menubar.add_cascade(label="Tools", menu=toolsmenu)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # File menu
        filemenu.add_command(label="Refresh", command=refresh,
                             accelerator="Ctrl+R")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=app.quit)

        # Edit menu
        editmenu.add_command(
            label="Profiles",
            command=lambda: NetAdapProfiles().manage_profiles())

        # Tools menu
        toolsmenu.add_command(
            label="ARP",
            command=lambda: arp_widget([{
                "ip": data["ip"], "name": data["name"]}
                for data in NETADAPTERS.values()])
        )

        # Help menu
        helpmenu.add_command(label="About", command=about_popup)

        # Config menu
        app.config(menu=menubar)
        app.bind_all("<Control-r>", lambda event: refresh())

        # Main frame
        MAIN_FRAME = ttk.Frame(app, style='Frame.TFrame')
        MAIN_FRAME.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        CANVAS_ROW = 0
        # Warning if not admin
        if not ADMIN:
            f_warning = ttk.Frame(MAIN_FRAME)
            f_warning.grid(row=0, column=0, pady=5)
            warning = Image.open("./resources/warning.png")
            warning = warning.resize((16, 16))
            warning = ImageTk.PhotoImage(warning)
            l_warning = tk.Label(f_warning, image=warning)
            l_warning.grid(row=0, column=0, padx=5)

            l_admin = ttk.Label(
                f_warning,
                text=("To modify the network adapters, the application"
                      " must be run as an administrator"),
                font=("Arial", 8, "bold"))
            l_admin.grid(row=0, column=1)
            f_separator = ttk.Frame(
                f_warning, relief='flat', height=2, bootstyle="warning")
            f_separator.grid(row=1, column=0, columnspan=2,
                             sticky="ew", padx=5, pady=5)

            CANVAS_ROW = 1

        # Canvas to enable the displacement of network adapters
        netadapters_canvas = tk.Canvas(
            MAIN_FRAME, bg='blue', width=WIDTH, height=HEIGHT)
        netadapters_canvas.grid(row=CANVAS_ROW, column=0, sticky="nsew")

        # Scroball for the canvas
        scrollbar = ttk.Scrollbar(
            MAIN_FRAME, orient="vertical",
            bootstyle="primary-round",
            command=netadapters_canvas.yview)
        scrollbar.grid(row=CANVAS_ROW, column=1, sticky="ns")

        # Displacement of network adapters
        netadapters_canvas.configure(yscrollcommand=scrollbar.set)
        netadapters_canvas.bind_all(
            "<MouseWheel>",
            lambda e: netadapters_canvas.yview_scroll(-1*(e.delta//120),
                                                      "units"))

        # Frame with the network adapters
        NETADAPTERS_FRAME = ttk.Frame(
            netadapters_canvas, width=WIDTH, height=HEIGHT)
        netadapters_canvas.create_window(
            (0, 0), window=NETADAPTERS_FRAME, anchor="nw")

        # Network adapters
        create_net_wd(net_adapters)

        # Set the size of the main frame
        app.grid_rowconfigure(0, weight=1)
        app.grid_columnconfigure(0, weight=1)

        app.bind("<Configure>",
                 lambda e: netadapters_canvas.configure(
                     scrollregion=netadapters_canvas.bbox("all"))
                 )

        app.mainloop()

    except Exception as e:  # pylint: disable=broad-exception-caught # noqa
        traceback.print_exc()
        with open(f"{APPNAME.lower()}_error.log", mode="w",
                  encoding="utf-8") as flog:
            traceback.print_exc(file=flog)

        ctypes.windll.user32.MessageBoxW(
            0,
            ("Sorry, an error occurred while trying to start the application."
             "\nPlease contact the developer (@javierorp)."),
            f"{APPNAME} - Error", 0x40 | 0x0)
