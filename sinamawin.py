"""Sinamawin - Simple Network Adapter Manager for Windows"""

import ctypes
import tkinter as tk
import traceback
import webbrowser
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from PIL import Image, ImageTk
from network_adapters import NetworkAdapters
from net_adap_widget import NetAdapWidget


APPNAME = "Sinamawin"
ICON = "./resources/sinamawin.ico"  # App icon
ABOUT_LOGO = ""  # App logo in About window
ADMIN = False  # Privileges
MAIN_FRAME = None  # Frame containing the network adapters and the scrollbar
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
    l_app = ttk.Label(popup, text=APPNAME,
                      font=("Arial", 14, "bold"))
    l_app.grid(row=0, column=0, padx=10, pady=(10, 0))

    l_app_desc = ttk.Label(
        popup, text="Simple Network Adapter Manager for Windows",
        font=("Arial", 12))
    l_app_desc.grid(row=1, column=0, padx=10, pady=5)

    t_lic = tk.Text(popup, wrap="word", height=15,
                    relief="flat", font=("Arial", 11))
    t_lic.grid(row=2, column=0, padx=10, pady=10)

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

    t_lic.configure(state="disabled")

    return


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
                appname=APPNAME,
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
        # Get network adapter info
        net_adapters = NetworkAdapters().get_info()

        # To know if the application has been launched as administrator.
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                ADMIN = True
        except:  # pylint: disable=bare-except # noqa
            pass

        # Assign an ID to display the icon in the taskbar on Windows
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Sinamawin")

        WIDTH, HEIGHT = get_window_size()
        ADJ_HEIGHT = 1.06 if ADMIN else 1.11

        app = ttk.Window(title="Sinamawin" + (" [Admin]" if ADMIN else ""),
                         themename="litera",
                         size=(int(WIDTH*1.025), int(HEIGHT*ADJ_HEIGHT)))
        app.resizable(False, False)

        # App icon in all windows
        app.iconbitmap(ICON)  # Set the bitmap for this window only
        app.iconbitmap(default=ICON)  # Set the default bitmap (.ico)
        app.iconbitmap(default='')  # Remove the default bitmap

        # Menu bar
        menubar = tk.Menu(app)
        app.config(menu=menubar)

        filemenu = tk.Menu(menubar)
        editmenu = tk.Menu(menubar)
        helpmenu = tk.Menu(menubar)

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # File menu
        filemenu.add_command(label="Refresh", command=refresh,
                             accelerator="Ctrl+R")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=app.quit)

        # Help menu
        helpmenu.add_command(label="About", command=about_popup)
        helpmenu.add_command(label="Releases", command=lambda: webbrowser.open(
            "https://github.com/javierorp/Sinamawin/releases"))

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
                  encoding="utf-8") as file:
            traceback.print_exc(file=file)

        ctypes.windll.user32.MessageBoxW(
            0,
            ("Sorry, an error occurred while trying to start the application."
             "\nPlease contact the developer (@javierorp)."),
            f"{APPNAME} - Error", 0x40 | 0x0)