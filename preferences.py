"""User preferences"""
import json
import os
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification
from ttkbootstrap.dialogs.dialogs import MessageDialog, Messagebox


APPNAME = "Sinamawin"


def get_preferences() -> dict:
    """Get user preferences.

    Returns:
        dict: User preferences.
            {"themename": "litera","skip_vers": []}
    """
    with open(os.environ.get(f"{APPNAME}_PREFERENCES"), "r",
              encoding="utf-8") as fprefers:
        preferences = json.load(fprefers)

    return preferences


def preferences_widget() -> None:
    """Create the user preferences popup window."""

    themes_vals = ["default (ligth)", "cosmo (ligth)", "flatly (ligth)",
                   "journal (ligth)", "litera (ligth)", "lumen (ligth)",
                   "minty (ligth)", "pulse (ligth)", "sandstone (ligth)",
                   "united (ligth)", "yeti (ligth)", "morph (ligth)",
                   "simplex (ligth)", "cerculean (ligth)", "solar (dark)",
                   "superhero (dark)", "darkly (dark)", "cyborg (dark)",
                   "vapor (dark)"]

    preferences = get_preferences()

    popup = ttk.Toplevel(title=f"{APPNAME} - Preferences",
                         resizable=(False, False))

    # Theme
    l_theme = ttk.Label(popup, text="Theme:")
    cb_theme = ttk.Combobox(popup,
                            state="readonly",
                            values=themes_vals,
                            width=25)

    theme_set = "default (ligth)"
    for theme in themes_vals:
        if preferences["themename"] in theme:
            theme_set = theme

    cb_theme.set(theme_set)

    l_theme.grid(row=0, column=0, padx=(15, 5), pady=15)
    cb_theme.grid(row=0, column=1, padx=(5, 15), pady=15)

    # Save button
    def save_btn():
        msg = "Do you want to save the changes?"
        dialog_title = f"{APPNAME} - Save preferences"
        dialog = MessageDialog(message=msg,
                               title=dialog_title,
                               buttons=["Accept", "Cancel"],
                               padding=(30, 30),
                               width=70)
        dialog.show()

        if dialog.result == "Accept":
            theme_sel = cb_theme.get()
            if theme_sel == "default (ligth)":
                theme_sel = "litera (ligth)"

            preferences["themename"] = theme_sel.split(" ")[0]
            save_preferences(preferences)

            toast = ToastNotification(
                title=APPNAME,
                message="The preferences have been saved.",
                duration=5000,
                icon="\u2714"
            )
            toast.show_toast()

            Messagebox.show_info(
                message=("The changes will be applied when"
                         " the application is restarted."),
                title=f"{APPNAME} - Information",
                padding=(30, 30),
                width=100)

    b_save = ttk.Button(popup,
                        text="Save", width=8,
                        command=save_btn)

    b_save.grid(row=1, column=1, padx=(5, 15), pady=(5, 15), sticky="e")

    # Mouse wheel behavior
    def popup_window_scroll(_):
        """To avoid propagating the event to the main window."""
        return "break"

    popup.bind("<MouseWheel>", popup_window_scroll)

    return


def save_preferences(preferences: dict) -> bool:
    """Save user preferences.

    Args:
        preferences (dict): User preferences.

    Returns:
        bool: True if user preferences has been stored.
    """
    with open(os.environ.get(f"{APPNAME}_PREFERENCES"),
              "w", encoding="utf-8") as file:
        json.dump(preferences, file, indent=4)

    return True
