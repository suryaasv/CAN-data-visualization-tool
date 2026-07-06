import tkinter as tk
from tkinter import filedialog, ttk, colorchooser, messagebox
import json
import os
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MaxNLocator
from byte import decode_signals
import numpy as np
import pandas as pd

class DynamicCombobox(tk.Frame):
    """Entry widget with dynamic search dropdown (Google-style autocomplete)."""

    def __init__(self, parent, values=None, width=20, **kwargs):
        super().__init__(parent, **kwargs)
        self.values = values or []
        self.width = width
        self.selected_value = tk.StringVar()
        self.filtered_values = []
        
        self._clicking_listbox = False

       
        self.entry = tk.Entry(self, width=width, font=("Segoe UI", 9))
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Down>",       self._on_down_key)
        self.entry.bind("<Up>",         self._on_up_key)
        self.entry.bind("<Return>",     self._on_return_key)
        self.entry.bind("<FocusIn>",    self._on_focus_in)   # NEW – show all on click
        self.entry.bind("<FocusOut>",   self._on_focus_out)  # FIXED – delayed hide

        self.dropdown_window = tk.Toplevel(self.winfo_toplevel())
        self.dropdown_window.withdraw()
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.attributes("-topmost", True)
        self.dropdown_window.transient(self.winfo_toplevel())

        self.dropdown_frame = tk.Frame(self.dropdown_window, bg="white", relief="sunken", bd=1)
        self.dropdown_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(self.dropdown_frame, font=("Segoe UI", 9), height=8,
                                  selectbackground="#007bff", selectforeground="white")
        self.listbox.pack(fill="both", expand=True)

        
        self.listbox.bind("<ButtonPress-1>",  self._on_listbox_press)  
        self.listbox.bind("<ButtonRelease-1>", self._on_listbox_click) 
        self.listbox.bind("<Return>",         self._on_listbox_return)
        self.listbox.bind("<MouseWheel>",     self._on_listbox_mousewheel)  

        self.listbox_showing = False
        self.listbox_index = -1

    

    def set_values(self, values):
        """Update the available values and refresh the dropdown if open."""
        self.values = values
        if self.listbox_showing:
            self._filter_values()

    def get(self):
        """Return the current text in the entry."""
        return self.entry.get()

    def set(self, value):
        """Set the entry text programmatically."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.selected_value.set(value)

   

    def _show_dropdown(self, items):
        """Populate and display the dropdown with *items*."""
        self.listbox.delete(0, tk.END)
        for item in items[:20]:          
            self.listbox.insert(tk.END, item)
        if not self.listbox_showing:
            self.update_idletasks()
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            width = max(self.entry.winfo_width(), 120)
            self.dropdown_window.geometry(f"{width}x150+{x}+{y}")
            self.dropdown_window.deiconify()
            self.dropdown_window.lift()
            self.listbox_showing = True
        self.listbox_index = -1

    def _hide_dropdown_now(self):
        """Immediately hide the dropdown."""
        if self.listbox_showing:
            self.dropdown_window.withdraw()
            self.listbox_showing = False
            self.listbox_index = -1

    def _filter_values(self):
        """Rebuild the dropdown based on the current entry text."""
        search_text = self.entry.get().strip().lower()
        if search_text:
            self.filtered_values = [v for v in self.values if search_text in v.lower()]
        else:
            # Empty search → show everything
            self.filtered_values = list(self.values)

        if self.filtered_values:
            self._show_dropdown(self.filtered_values)
        else:
            self._hide_dropdown_now()

    def _select_value(self, value):
        """Write *value* into the entry and close the dropdown."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.selected_value.set(value)
        self._hide_dropdown_now()

   

    def _on_focus_in(self, event):
        """Show all signals when the user clicks into the entry."""
        self.filtered_values = list(self.values)
        if self.filtered_values:
            self._show_dropdown(self.filtered_values)

    def _on_focus_out(self, event):
        """
        Hide the dropdown when focus leaves the entry.
        Use after() so a Listbox <ButtonPress> fires first and sets
        _clicking_listbox = True, preventing the hide.
        """
        def delayed_hide():
            if not self._clicking_listbox:
                self._hide_dropdown_now()
            self._clicking_listbox = False
        self.after(150, delayed_hide)

    def _on_key_release(self, event):
        """Filter values on every keystroke (except navigation keys)."""
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self._filter_values()

    def _on_down_key(self, event):
        """Move selection down in the listbox."""
        if self.listbox_showing and self.listbox_index < len(self.filtered_values) - 1:
            self.listbox_index += 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.listbox_index)
            self.listbox.see(self.listbox_index)
        return "break"

    def _on_up_key(self, event):
        """Move selection up in the listbox."""
        if self.listbox_showing and self.listbox_index > 0:
            self.listbox_index -= 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.listbox_index)
            self.listbox.see(self.listbox_index)
        return "break"

    def _on_return_key(self, event):
        """Confirm the highlighted listbox item with Enter."""
        if self.listbox_showing and self.listbox_index >= 0:
            self._select_value(self.filtered_values[self.listbox_index])
            return "break"

    

    def _on_listbox_press(self, event):
        """
        Mark that a listbox click is in progress.
        This prevents _on_focus_out from hiding the dropdown before the
        release event can complete the selection.
        """
        self._clicking_listbox = True

    def _on_listbox_click(self, event):
        """Complete selection on mouse button release."""
        selection = self.listbox.curselection()
        if selection:
            self._select_value(self.filtered_values[selection[0]])
        self._clicking_listbox = False

    def _on_listbox_return(self, event):
        """Confirm selection when Enter is pressed while listbox has focus."""
        selection = self.listbox.curselection()
        if selection:
            self._select_value(self.filtered_values[selection[0]])

    def _on_listbox_mousewheel(self, event):
        """Handle mousewheel on listbox to prevent parent scroll."""
        if len(self.filtered_values) > 8:
            self.listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def hide_dropdown(self, event=None):
        self._hide_dropdown_now()

BG_COLOR      = "#f0f0f0"
FG_COLOR      = "#333333"
BUTTON_COLOR  = "#007bff"
BUTTON_HOVER  = "#0056b3"
SUCCESS_COLOR = "#28a745"
WARNING_COLOR = "#ffc107"
DANGER_COLOR  = "#dc3545"
DEFAULT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
    "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#aec7e8", "#ffbb78",
    "#98df8a", "#ff9896", "#c5b0d5", "#c49c94", "#f7b6d2", "#dbdb8d"
]

APP_ICON = "app_icon.ico"

decoded_df = None
all_signals = []

class SyncedGraphWindow(tk.Toplevel):
    """Custom graph window with synchronized zoom across all subplots."""
    pass


class GraphWindow:
    """Separate window for displaying graphs with synchronized zoom across all subplots."""

    def __init__(self, parent_title, figure):
        self.window = tk.Toplevel()
        self.window.title(f"Graph Viewer - {parent_title}")
        self.window.geometry("1200x800")
        self.window.minsize(1000, 600)
        try:
            self.window.state("zoomed")
        except tk.TclError:
            self.window.geometry(f"{self.window.winfo_screenwidth()}x{self.window.winfo_screenheight()}+0+0")

        # Top area: Toolbar controls
        toolbar_wrapper = tk.Frame(self.window, bg="#f8f9fa", relief="raised", bd=1)
        toolbar_wrapper.pack(side="top", fill="x", padx=5, pady=5)

        # Main plotting area
        main_frame = tk.Frame(self.window, bg="white")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.plot_frame = tk.Frame(main_frame, bg="white")
        self.plot_frame.pack(fill="both", expand=True)

        self.canvas = FigureCanvasTkAgg(figure, master=self.plot_frame)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        try:
            self._nav_toolbar = NavigationToolbar2Tk(self.canvas, toolbar_wrapper)
            self._nav_toolbar.update()
            self._nav_toolbar.pack(side="left", fill="x", expand=True)
        except Exception:
            self._nav_toolbar = None

        self.figure = figure
        self._store_original_limits()
        self._syncing = False

        for ax in self.figure.axes:
            ax.callbacks.connect('xlim_changed', self._on_xlim_changed)
        
        self.window.update_idletasks()
        self.window.bind("<Configure>", self._schedule_resize)
        self.window.after_idle(self._fit_figure_to_window)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _store_original_limits(self):
        self._original_limits = [
            (ax, ax.get_xlim(), ax.get_ylim())
            for ax in self.figure.axes
        ]

    def _on_xlim_changed(self, ax):
        """Synchronize X limits when any subplot X range changes."""
        if self._syncing or len(self.figure.axes) <= 1:
            return
        self._synchronize_x_limits(ax)

    def _synchronize_x_limits(self, source_ax=None):
        """Apply the X-limits from the source axis to all other axes."""
        if not self.figure.axes:
            return
        target_xlim = source_ax.get_xlim() if source_ax is not None else self.figure.axes[0].get_xlim()
        self._syncing = True
        for ax in self.figure.axes:
            if ax is source_ax:
                continue
            try:
                ax.set_xlim(target_xlim)
            except Exception:
                pass
        self._syncing = False
        self.canvas.draw_idle()

    def _reset_view(self):
        for ax, xlim, ylim in getattr(self, "_original_limits", []):
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
        self.canvas.draw_idle()

    def _apply_zoom(self, factor):
        for ax in self.figure.axes:
            x_left, x_right = ax.get_xlim()
            y_bottom, y_top = ax.get_ylim()

            x_center = (x_left + x_right) / 2.0
            y_center = (y_bottom + y_top) / 2.0
            x_half = (x_right - x_left) * factor / 2.0
            y_half = (y_top - y_bottom) * factor / 2.0

            ax.set_xlim(x_center - x_half, x_center + x_half)
            ax.set_ylim(y_center - y_half, y_center + y_half)

        self.canvas.draw_idle()

    def _schedule_resize(self, event=None):
        if event is not None and event.widget is not self.window:
            return
        self.window.after_idle(self._fit_figure_to_window)

    def _fit_figure_to_window(self):
        try:
            width = max(1, self.plot_frame.winfo_width())
            height = max(1, self.plot_frame.winfo_height())
            dpi = self.figure.get_dpi()
            self.figure.set_size_inches(width / dpi, height / dpi, forward=True)
            self.canvas.draw_idle()
        except Exception:
            pass

    def _on_close(self):
        """Cleanup graph window resources before destroying it."""
        try:
            self.canvas.get_tk_widget().destroy()
        except Exception:
            pass
        try:
            plt.close(self.figure)
        except Exception:
            pass
        self.window.destroy()

    def save_graph(self):
        try:
            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                defaultextension=".png",
                filetypes=[
                    ("PNG Files", "*.png"),
                    ("JPG Files", "*.jpg;*.jpeg"),
                    ("PDF Files", "*.pdf"),
                    ("All Files", "*.*")
                ],
                initialfile=f"plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Graph saved to\n{file_path}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self.window)

    def export_graph(self):
        """Export the graph using the same figure in image or document formats."""
        try:
            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                defaultextension=".png",
                filetypes=[
                    ("PNG Files", "*.png"),
                    ("PDF Files", "*.pdf"),
                    ("SVG Files", "*.svg"),
                    ("All Files", "*.*")
                ],
                initialfile=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Graph exported to\n{file_path}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self.window)


class SubplotConfigFrame(tk.LabelFrame):
    """Frame for individual subplot configuration."""
 
    def __init__(self, parent, subplot_num, all_signals_list, **kwargs):
        super().__init__(parent, text=f"Subplot {subplot_num} Configuration", **kwargs)
        self.subplot_num = subplot_num
        self.all_signals = all_signals_list
        self.lhs_entries = []
        self.rhs_entries = []
 
        self.configure(font=("Segoe UI", 10, "bold"), fg=FG_COLOR, relief="solid", borderwidth=1)
 
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=8, pady=8)
 
        lhs_frame = tk.LabelFrame(main_paned, text="LHS (Left Axis)",
                                  font=("Segoe UI", 9, "bold"), fg=FG_COLOR, relief="solid", borderwidth=1)
        main_paned.add(lhs_frame, weight=1)
        self.lhs_ymin_var = tk.StringVar(value="")
        self.lhs_ymax_var = tk.StringVar(value="")
        self._create_axis_config(lhs_frame, "lhs", self.lhs_entries, self.lhs_ymin_var, self.lhs_ymax_var)
 
        rhs_frame = tk.LabelFrame(main_paned, text="RHS (Right Axis)",
                                  font=("Segoe UI", 9, "bold"), fg=FG_COLOR, relief="solid", borderwidth=1)
        main_paned.add(rhs_frame, weight=1)
        self.rhs_ymin_var = tk.StringVar(value="")
        self.rhs_ymax_var = tk.StringVar(value="")
        self._create_axis_config(rhs_frame, "rhs", self.rhs_entries, self.rhs_ymin_var, self.rhs_ymax_var)
 
 
    def _create_axis_config(self, parent, axis_type, entries_list, ymin_var, ymax_var):
        """Create configuration controls for LHS or RHS axis."""
        # Header row
        header_frame = tk.Frame(parent, bg="#e9ecef")
        header_frame.pack(fill="x", padx=6, pady=4)
 
        headers = ["Column", "Type", "Marker", "LineStyle", "Size", "Color"]
        for col_index, header in enumerate(headers):
            tk.Label(
                header_frame,
                text=header,
                font=("Segoe UI", 8, "bold"),
                bg="#e9ecef",
                fg=FG_COLOR,
                anchor="w"
            ).grid(row=0, column=col_index, padx=2, pady=3, sticky="ew")
 
        for i in range(6):
            header_frame.grid_columnconfigure(i, weight=1)
 
        rows_frame = tk.Frame(parent, bg="white")
        rows_frame.pack(fill="both", expand=True, padx=6, pady=4)
 
        for i in range(3):
            row_data = self._create_axis_row(rows_frame, axis_type, i)
            entries_list.append(row_data)

        limit_frame = tk.Frame(parent, bg="#f8f9fa", relief="groove", bd=1)
        limit_frame.pack(fill="x", padx=6, pady=(4, 4))
        tk.Label(limit_frame, text="Y-Limits (e.g., 0-100)", font=("Segoe UI", 8, "bold"), bg="#f8f9fa", fg=FG_COLOR).pack(side="left", padx=(4, 4))
        tk.Label(limit_frame, text="Min", font=("Segoe UI", 8), bg="#f8f9fa", fg=FG_COLOR).pack(side="left", padx=(4, 2))
        tk.Entry(limit_frame, textvariable=ymin_var, width=8, font=("Segoe UI", 8)).pack(side="left", padx=(0, 6))
        tk.Label(limit_frame, text="Max", font=("Segoe UI", 8), bg="#f8f9fa", fg=FG_COLOR).pack(side="left", padx=(4, 2))
        tk.Entry(limit_frame, textvariable=ymax_var, width=8, font=("Segoe UI", 8)).pack(side="left")
 
    def _create_axis_row(self, parent, axis_type, row_num):
        """Create a single configuration row."""
 
        row_frame = tk.Frame(parent, bg="white", relief="flat")
        row_frame.pack(fill="x", pady=2, padx=2)
 
        for col_index in range(6):
            row_frame.grid_columnconfigure(col_index, weight=1)

        
        col_combo = DynamicCombobox(row_frame, values=self.all_signals, width=13, bg="white")
        col_combo.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        
        type_combo = ttk.Combobox(row_frame, values=["Line", "Scatter", "None"],
                                  width=10, state="readonly")
        type_combo.set("Line")
        type_combo.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

       
        marker_combo = ttk.Combobox(
            row_frame,
            values=[".", ",", "o", "x", "X", "+", "P", "*",
                    "H", "h", "v", "^", "<", ">", "s", "D", "d"],
            width=10, state="readonly"
        )
        marker_combo.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

       
        linestyle_combo = ttk.Combobox(row_frame,
                                       values=["-", "--", "-.", ":", "None"],
                                       width=10, state="readonly")
        linestyle_combo.set("-")
        linestyle_combo.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        size_spinbox = ttk.Spinbox(row_frame, from_=0.5, to=12, increment=0.5, width=8)
        size_spinbox.set("2.0")
        size_spinbox.grid(row=0, column=4, padx=2, pady=2, sticky="ew")

        
        color_frame = tk.Frame(row_frame, bg="white")
        color_frame.grid(row=0, column=5, padx=2, pady=2, sticky="ew")

        default_color_index = (((self.subplot_num - 1) * 6) + (0 if axis_type == "lhs" else 3) + row_num) % len(DEFAULT_COLORS)
        default_color = DEFAULT_COLORS[default_color_index]

        color_label = tk.Label(color_frame, bg=default_color, width=5, height=1, relief="sunken")
        color_label.pack(side="left")

        def pick_color(color_label=color_label):
            color = colorchooser.askcolor(title="Choose Color")
            if color[1]:
                color_label.config(bg=color[1])

        tk.Button(color_frame, text="Pick", width=4, command=pick_color,
                  bg=BUTTON_COLOR, fg="white",
                  activebackground=BUTTON_HOVER).pack(side="left", padx=2)

        return {
            "frame":     row_frame,
            "column":    col_combo,
            "type":      type_combo,
            "marker":    marker_combo,
            "size":      size_spinbox,
            "linestyle": linestyle_combo,
            "color":     color_label,
        }


    def update_signal_dropdowns(self):
        """Push the current signal list into every DynamicCombobox in this subplot."""
        for entry in self.lhs_entries + self.rhs_entries:
            entry["column"].set_values(self.all_signals)

    def get_config(self):
        """Return the current configuration dict for this subplot."""
        config = {
            "subplot_num": self.subplot_num,
            "lhs":         [],
            "rhs":         [],
            "lhs_y_limits": [self._parse_limit(self.lhs_ymin_var.get()), self._parse_limit(self.lhs_ymax_var.get())],
            "rhs_y_limits": [self._parse_limit(self.rhs_ymin_var.get()), self._parse_limit(self.rhs_ymax_var.get())],
            "y_limits":    (0, 100),
        }

        for axis_type, entries in [("lhs", self.lhs_entries), ("rhs", self.rhs_entries)]:
            for entry in entries:
                if entry["column"].get():
                    try:
                        size_value = float(entry["size"].get())
                    except (TypeError, ValueError):
                        size_value = 2.0
                    config[axis_type].append({
                        "column":    entry["column"].get(),
                        "type":      entry["type"].get(),
                        "marker":    entry["marker"].get(),
                        "size":      size_value,
                        "ms":        size_value,
                        "linestyle": entry["linestyle"].get(),
                        "color":     entry["color"].cget("bg"),
                    })

        return config

    def _parse_limit(self, value):
        if value is None:
            return None
        value = str(value).strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None


class EnhancedGUI:
    """Enhanced CAN Data Visualizer GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title("CAN Data Visualization Tool")
        self.root.minsize(1100, 850)
        
        self.root.configure(bg=BG_COLOR)
        style = ttk.Style()
        style.theme_use('clam')

        self.decoded_df = None
        self.all_signals = []
        self.input_file = ""
        self.extra_signals_file = ""
        self.input_type = tk.StringVar(value="trc")
        self.subplot_frames = {}
        self.current_num_subplots = 2

        self._setup_ui()

   
    def _setup_ui(self):
        # Main container with improved grid layout
        main_container = tk.Frame(self.root, bg=BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=6, pady=6)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=1)
 
        toolbar_container = tk.Frame(main_container, bg=BG_COLOR)
        toolbar_container.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._setup_toolbar(toolbar_container)
 
        bottom_container = tk.Frame(main_container, bg=BG_COLOR)
        bottom_container.grid(row=1, column=0, sticky="nsew")
        self._setup_bottom_panel(bottom_container)

    def _setup_toolbar(self, parent):
        toolbar_frame = tk.Frame(parent, bg=BG_COLOR, relief="groove", bd=1, padx=6, pady=6)
        toolbar_frame.pack(fill="x", expand=True)

        left_tools = tk.Frame(toolbar_frame, bg=BG_COLOR)
        left_tools.pack(side="left", fill="x", expand=True)

        tk.Button(left_tools, text="Browse CAN Data",
                  command=self.browse_input_file, bg=BUTTON_COLOR, fg="white",
                  font=("Segoe UI", 9), padx=6, pady=6,
                  activebackground=BUTTON_HOVER).pack(side="left", padx=(0, 4))

        tk.Button(left_tools, text="Browse Extra Signals",
                  command=self.browse_extra_signals, bg="#17a2b8", fg="white",
                  font=("Segoe UI", 9), padx=6, pady=6,
                  activebackground="#117a8b").pack(side="left", padx=(0, 4))

        tk.Button(left_tools, text="Decode Signals",
                  bg=SUCCESS_COLOR, fg="white", font=("Segoe UI", 9, "bold"),
                  padx=6, pady=6, command=self.run_decode,
                  activebackground="#218838").pack(side="left", padx=(0, 12))

        self.file_label = tk.Label(left_tools, text="Signals Found: 0",
                       fg=FG_COLOR, font=("Segoe UI", 9), bg=BG_COLOR)
        self.file_label.pack(side="left", padx=(0, 10))

        self.extra_file_label = tk.Label(left_tools, text="Extra Signals: None",
                                         fg=FG_COLOR, font=("Segoe UI", 9), bg=BG_COLOR)
        self.extra_file_label.pack(side="left", padx=(0, 10))

        self.status_label = tk.Label(left_tools, text="Waiting",
                                     fg=FG_COLOR, font=("Segoe UI", 9), bg=BG_COLOR)
        self.status_label.pack(side="left")

        right_tools = tk.Frame(toolbar_frame, bg=BG_COLOR)
        right_tools.pack(side="right", fill="x", expand=True)

        tk.Label(right_tools, text="Plot Title:", font=("Segoe UI", 9, "bold"),
                 bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=(0, 4))

        self.title_entry = tk.Entry(right_tools, width=18, font=("Segoe UI", 9))
        self.title_entry.pack(side="left", padx=(0, 10))
        self.title_entry.insert(0, "CAN Data Plot")

        tk.Label(right_tools, text="X-Axis:", font=("Segoe UI", 9, "bold"),
             bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=(6, 4))

        self.xaxis_combo = ttk.Combobox(right_tools, values=["time"], width=13, state="readonly")
        self.xaxis_combo.set("time")
        self.xaxis_combo.pack(side="left", padx=(0, 8))

        tk.Label(right_tools, text="Subplots:", font=("Segoe UI", 9, "bold"),
                 bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=(0, 4))

        self.subplot_spinbox = tk.Spinbox(right_tools, from_=1, to=5, width=5,
                                          font=("Segoe UI", 9))
        self.subplot_spinbox.delete(0, tk.END)
        self.subplot_spinbox.insert(0, 2)
        self.subplot_spinbox.pack(side="left", padx=(0, 8))

        tk.Label(right_tools, text="(max 5)", font=("Segoe UI", 8),
                 bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=(0, 10))

        tk.Button(right_tools, text="Update",
                  command=self.update_subplots, bg=WARNING_COLOR, fg="white",
                  font=("Segoe UI", 9), padx=10, pady=6,
                  activebackground="#000000").pack(side="left")

    def _setup_bottom_panel(self, parent):
        action_frame = tk.Frame(parent, bg=BG_COLOR)
        action_frame.pack(fill="x", padx=8, pady=(0, 8))

        tk.Button(action_frame, text="📈 Plot",
                  bg=BUTTON_COLOR, fg="white", font=("Segoe UI", 9, "bold"),
                  padx=10, pady=12, command=self.plot_data,
                  activebackground=BUTTON_HOVER).pack(side="left", padx=5, expand=True, fill="x")

        tk.Button(action_frame, text="💾 Export Template",
                  bg=SUCCESS_COLOR, fg="white", font=("Segoe UI", 9),
                  padx=10, pady=12, command=self.export_template,
                  activebackground="#218838").pack(side="left", padx=5, expand=True, fill="x")

        tk.Button(action_frame, text="📂 Import Template",
                  bg=SUCCESS_COLOR, fg="white", font=("Segoe UI", 9),
                  padx=10, pady=12, command=self.import_template,
                  activebackground="#218838").pack(side="left", padx=5, expand=True, fill="x")

        # Scrollable area with better layout
        canvas_frame = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas_frame.yview)
        scrollable_frame = tk.Frame(canvas_frame, bg=BG_COLOR)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )
        canvas_frame.create_window((0, 0), window=scrollable_frame, anchor="nw", width=parent.winfo_width() or 1)
        canvas_frame.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            # Check if the event originated from inside a Listbox or Entry widget (dropdown)
            widget = event.widget
            current = widget
            # Walk up the widget tree to see if we're inside a Listbox or Entry
            while current:
                if isinstance(current, (tk.Listbox, tk.Entry)):
                    return "break"  # Don't scroll canvas if mouse is over dropdown widgets
                current = current.master
            canvas_frame.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_frame.bind_all("<MouseWheel>", _on_mousewheel)

        # Bind canvas resize to update window width
        def _on_canvas_configure(event):
            canvas_items = canvas_frame.find_all()
            if canvas_items:
                canvas_frame.itemconfig(canvas_items[0], width=event.width)
        canvas_frame.bind("<Configure>", _on_canvas_configure)

        canvas_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Subplot configuration section
        self.config_frame = tk.LabelFrame(
            scrollable_frame, text="📊 Subplot Configuration",
            font=("Segoe UI", 11, "bold"), fg=FG_COLOR,
            padx=8, pady=8, bg=BG_COLOR, relief="solid", borderwidth=1
        )
        self.config_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.subplot_container = tk.Frame(self.config_frame, bg=BG_COLOR)
        self.subplot_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.update_subplots()

        tk.Frame(scrollable_frame, height=10, bg=BG_COLOR).pack()


    def browse_input_file(self):
        # Allow selecting TRC, CSV, LOG, or ASC files
        filetypes = [
            ("CAN Data Files", "*.trc *.csv *.log *.asc *.txt"),
            ("TXT Files", "*.txt"),
            ("TRC Files", "*.trc"),
            ("CSV Files", "*.csv"),
            ("LOG Files", "*.log"),
            ("ASC Files", "*.asc"),
            ("All Files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            title="Select CAN Data File(.trc, .csv, .log, .asc, or .txt)",
            filetypes=filetypes
        )
        if file_path:
            self.input_file = file_path
            self.status_label.config(
                text=f"File Selected", fg=WARNING_COLOR
            )

    def browse_extra_signals(self):
        file_path = filedialog.askopenfilename(
            title="Select Extra Signals CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            self.extra_signals_file = file_path
            self.extra_file_label.config(text=f"Extra Signals: {os.path.basename(file_path)}", fg=SUCCESS_COLOR)
            self.status_label.config(
                text=f"Extra signals loaded: {os.path.basename(file_path)}", fg=FG_COLOR
            )

    def run_decode(self):
        """Decode signals from TRC file using the built-in signal database."""

        if not self.input_file:
            self.status_label.config(text="Please select an input file!", fg=DANGER_COLOR)
            return

        try:
            self.status_label.config(text="Decoding...", fg=WARNING_COLOR)
            self.root.update()

            decoded_df = decode_signals(
                self.input_file,
                custom_signal_csv=self.extra_signals_file if self.extra_signals_file else None
            )
            self.decoded_df = decoded_df

            self.all_signals = sorted(
                decoded_df["signal"].dropna().unique().tolist()
            )

            
            # Push updated signal list into every subplot frame
            for frame in self.subplot_frames.values():
                frame.all_signals = self.all_signals
                frame.update_signal_dropdowns()

            # Update x-axis selector to include decoded signals (keep 'time' first)
            try:
                current = self.xaxis_combo.get()
            except Exception:
                current = "time"
            x_options = ["time"] + self.all_signals
            self.xaxis_combo.config(values=x_options)
            if current in x_options:
                self.xaxis_combo.set(current)
            else:
                self.xaxis_combo.set("time")

            # Update the top label to show only how many signals were found.
            self.file_label.config(text=f"Signals Found: {len(self.all_signals)}", fg=SUCCESS_COLOR)
            # Do not display any status words after decoding — keep the status area blank.
            self.status_label.config(text="", fg=SUCCESS_COLOR)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", fg=DANGER_COLOR)

    def update_subplots(self):
        """Rebuild subplot configuration panels from the spinbox value."""
        try:
            num_subplots = int(self.subplot_spinbox.get())
        except ValueError:
            num_subplots = 2

        for frame in self.subplot_frames.values():
            frame.destroy()
        self.subplot_frames.clear()

        for i in range(1, num_subplots + 1):
            subplot_frame = SubplotConfigFrame(
                self.subplot_container, i, self.all_signals,
                padx=5, pady=5, relief="groove", bd=2
            )
            subplot_frame.pack(fill="x", expand=True, pady=5, padx=10)
            self.subplot_frames[i] = subplot_frame

        self.subplot_container.update_idletasks()

    def plot_data(self):
        """Plot the data in a new GraphWindow."""

        if self.decoded_df is None:
            messagebox.showerror("Error", "Please decode signals first")
            return

        try:
            num_subplots = int(self.subplot_spinbox.get())
            fig = plt.figure(figsize=(16, max(7, 1.7 * num_subplots)), constrained_layout=False)
            fig.patch.set_facecolor('white')
            grid = fig.add_gridspec(
                num_subplots, 1,
                left=0.04,
                right=0.98,
                top=0.96,
                bottom=0.12,
                hspace=0.14
            )

            axes = []
            for row_index in range(num_subplots):
                if row_index == 0:
                    ax = fig.add_subplot(grid[row_index, 0])
                else:
                    ax = fig.add_subplot(grid[row_index, 0], sharex=axes[0])
                axes.append(ax)

            for idx, ax in zip(range(1, num_subplots + 1), axes):
                if idx not in self.subplot_frames:
                    continue

                config = self.subplot_frames[idx].get_config()
                has_lhs_data = False
                has_rhs_data = False

                x_field = (self.xaxis_combo.get() if hasattr(self, "xaxis_combo") else "time")

                def format_time_axis_value(value):
                    if value is None:
                        return ""

                    if isinstance(value, str):
                        return value.strip()
                     
                    if isinstance(value, (datetime, pd.Timestamp)):
                        return value.strftime("%H:%M:%S:%f")[:-2]

                    if hasattr(value, "strftime"):
                        try:
                            return value.strftime("%H:%M:%S:%f")[:-3]
                        except Exception:
                            return str(value)

                    return str(value)

                subplot_time_values = []
                time_to_pos = None
                if x_field == "time":
                    use_index_labels = False
                    for item in config["lhs"] + config["rhs"]:
                        signal_data = self.decoded_df[
                            self.decoded_df["signal"] == item["column"]
                        ].sort_values("time")
                        if not signal_data.empty:
                            time_series = signal_data["time"]
                            first_time_value = time_series.iat[0] if len(time_series) > 0 else None
                            if (time_series.dtype == object or isinstance(first_time_value, str)
                                    or hasattr(first_time_value, "strftime")):
                                use_index_labels = True
                            subplot_time_values.extend([format_time_axis_value(v) for v in time_series.tolist()])

                    if use_index_labels and subplot_time_values:
                        unique_times = list(dict.fromkeys(subplot_time_values))
                        time_to_pos = {time: pos for pos, time in enumerate(unique_times)}

                def get_axis_x_limits(axis):
                    x_values = []
                    for line in axis.get_lines():
                        line_x = line.get_xdata()
                        if line_x is not None:
                            x_values.extend(np.asarray(line_x).ravel().tolist())

                    for collection in axis.collections:
                        offsets = collection.get_offsets()
                        if offsets is not None and len(offsets) > 0:
                            x_values.extend(np.asarray(offsets[:, 0]).ravel().tolist())

                    numeric_x_values = [x for x in x_values if x is not None and not pd.isna(x)]
                    if numeric_x_values:
                        return min(numeric_x_values), max(numeric_x_values)
                    return None

                def plot_series(axis, signal_data, item, label):
                    plot_type = item["type"]
                    if plot_type == "None":
                        return False

                    marker = item["marker"] if item["marker"] and item["marker"] != "None" else None
                    try:
                        size_value = float(item.get("size", item.get("ms", 2.0)))
                    except (TypeError, ValueError):
                        size_value = 2.0
                    marker_size = max(size_value, 1.0)
                    line_width = max(size_value, 0.5)

                    # Determine x/y values depending on selected x-axis
                    if x_field == "time":
                        x_values = signal_data["time"].tolist()
                        if time_to_pos is not None:
                            x_values = [time_to_pos[format_time_axis_value(t)] for t in x_values]
                        y_values = signal_data["decoded_value"].tolist()
                    else:
                        x_signal_data = self.decoded_df[self.decoded_df["signal"] == x_field].sort_values("time")
                        if signal_data.empty or x_signal_data.empty:
                            return False
                        y_df = signal_data[["time", "decoded_value"]].rename(columns={"decoded_value": "y_val"})
                        x_df = x_signal_data[["time", "decoded_value"]].rename(columns={"decoded_value": "x_val"})
                        merged = pd.merge(y_df, x_df, on="time", how="inner")
                        if merged.empty:
                            x_values = list(range(len(signal_data)))
                            y_values = signal_data["decoded_value"].tolist()
                        else:
                            x_values = merged["x_val"].tolist()
                            y_values = merged["y_val"].tolist()

                    if plot_type == "Scatter":
                        axis.scatter(x_values, y_values,
                                     label=label, color=item["color"], marker=marker or "o",
                                     s=marker_size * 8, alpha=0.8)
                    else:
                        axis.plot(x_values, y_values,
                                  label=label, color=item["color"],
                                  linestyle=item["linestyle"], marker=marker,
                                  markersize=marker_size, linewidth=line_width, alpha=0.8,
                                  markevery=max(1, max(1, len(y_values)//10)))
                    return True

                for item in config["lhs"]:
                    signal_data = self.decoded_df[
                        self.decoded_df["signal"] == item["column"]
                    ].sort_values("time")
                    if not signal_data.empty and plot_series(ax, signal_data, item, item["column"]):
                        has_lhs_data = True

                ax2 = ax.twinx()

                for item in config["rhs"]:
                    signal_data = self.decoded_df[
                        self.decoded_df["signal"] == item["column"]
                    ].sort_values("time")
                    if not signal_data.empty and plot_series(ax2, signal_data, item, item["column"] + " (RHS)"):
                        has_rhs_data = True

                if time_to_pos is not None:
                    tick_positions = list(time_to_pos.values())
                    tick_labels = list(time_to_pos.keys())
                    max_labels = 10
                    if len(tick_positions) > max_labels:
                        step = max(1, len(tick_positions) // max_labels)
                        tick_positions = tick_positions[::step]
                        tick_labels = tick_labels[::step]
                        if tick_positions[-1] != list(time_to_pos.values())[-1]:
                            tick_positions.append(list(time_to_pos.values())[-1])
                            tick_labels.append(list(time_to_pos.keys())[-1])
                    ax.set_xticks(tick_positions)
                    ax.set_xticklabels(
                    tick_labels,
                    rotation=45,
                    ha="right",
                    fontsize=8
                    )

                else:
                    unique_times = np.sort(self.decoded_df["time"].unique())

                    if len(unique_times) > 10:
                        step = max(1, len(unique_times) // 10)
                        tick_times = unique_times[::step]

                        if tick_times[-1] != unique_times[-1]:
                            tick_times = np.append(tick_times, unique_times[-1])
                    else:
                        tick_times = unique_times

                    ax.set_xticks(tick_times)
                    ax.set_xticklabels(
                        [f"{t:.1f}" for t in tick_times],
                        rotation=45,
                        ha="right",
                        fontsize=8
                    )
                x_limits = get_axis_x_limits(ax)
                if x_limits is not None:
                    ax.set_xlim(x_limits[0], x_limits[1])

                lhs_y_limits = config.get("lhs_y_limits", [None, None])
                rhs_y_limits = config.get("rhs_y_limits", [None, None])

                def apply_axis_limits(axis, limits):
                    if not limits or len(limits) != 2:
                        return
                    ymin, ymax = limits
                    if ymin is not None and ymax is not None and ymin < ymax:
                        axis.set_ylim(ymin, ymax)
                    elif ymin is not None:
                        axis.set_ylim(ymin, axis.get_ylim()[1])
                    elif ymax is not None:
                        axis.set_ylim(axis.get_ylim()[0], ymax)

                if has_lhs_data and lhs_y_limits and len(lhs_y_limits) == 2:
                    apply_axis_limits(ax, lhs_y_limits)

                if has_rhs_data and rhs_y_limits and len(rhs_y_limits) == 2:
                    apply_axis_limits(ax2, rhs_y_limits)

                for label in ax.get_xticklabels():
                    label.set_visible(True)
                    label.set_ha('right')
                    label.set_rotation(45)

                ax.set_ylabel("LHS Value", fontsize=10, fontweight='bold')
                ax2.set_ylabel("RHS Value", fontsize=10, fontweight='bold')
                ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
                ax.tick_params(labelsize=9)
                ax2.tick_params(labelsize=9)

                if idx != num_subplots:
                    ax.tick_params(labelbottom=False)
                    ax.set_xlabel("")

                if has_lhs_data:
                    lines1, labels1 = ax.get_legend_handles_labels()
                    if lines1:
                        ax.legend(
                            lines1,
                            labels1,
                            loc="upper left",
                            fontsize=8,
                            framealpha=0.8,
                            edgecolor='black',
                            fancybox=True,
                            handlelength=1.8,
                            handletextpad=0.5,
                        )

                if has_rhs_data:
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    if lines2:
                        ax2.legend(
                            lines2,
                            labels2,
                            loc="upper right",
                            fontsize=8,
                            framealpha=0.8,
                            edgecolor='black',
                            fancybox=True,
                            handlelength=1.8,
                            handletextpad=0.5,
                        )

            if axes:
                x_label = (self.xaxis_combo.get() if hasattr(self, "xaxis_combo") else "time")
                axes[-1].set_xlabel(x_label, fontsize=10, fontweight='bold')

            fig.tight_layout()
            GraphWindow(self.title_entry.get(), fig)

        except Exception as e:
            messagebox.showerror("Plot Error", str(e))

    def export_template(self):
        """Export current configuration as a JSON template."""
        try:
            template = {
                "title":        self.title_entry.get(),
                "num_subplots": int(self.subplot_spinbox.get()),
                "subplots":     [],
            }
            for idx in sorted(self.subplot_frames.keys()):
                template["subplots"].append(self.subplot_frames[idx].get_config())

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                initialfile=f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            if file_path:
                with open(file_path, "w") as f:
                    json.dump(template, f, indent=4)
                messagebox.showinfo("Success", f"Template exported successfully!\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_template(self):
        """Import configuration from a JSON template."""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            if not file_path:
                return

            with open(file_path, "r") as f:
                template = json.load(f)

            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, template.get("title", ""))

            num_subplots = max(1, min(5, int(template.get("num_subplots", 2))))
            self.subplot_spinbox.delete(0, tk.END)
            self.subplot_spinbox.insert(0, num_subplots)
            self.update_subplots()

            for subplot_idx, subplot_config in enumerate(template.get("subplots", [])):
                subplot_num = subplot_config.get("subplot_num", subplot_idx + 1)
                if subplot_num in self.subplot_frames:
                    self._restore_subplot_config(
                        self.subplot_frames[subplot_num], subplot_config
                    )

            messagebox.showinfo("Success",
                                "Template imported successfully!\nAll settings have been restored.")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    

    def _restore_subplot_config(self, subplot_frame, config):
        """Restore subplot configuration from saved data."""

        lhs_y_limits = config.get("lhs_y_limits", [None, None])
        rhs_y_limits = config.get("rhs_y_limits", [None, None])
        if len(lhs_y_limits) == 2:
            lhs_ymin, lhs_ymax = lhs_y_limits
            subplot_frame.lhs_ymin_var.set("" if lhs_ymin is None else str(lhs_ymin))
            subplot_frame.lhs_ymax_var.set("" if lhs_ymax is None else str(lhs_ymax))
        if len(rhs_y_limits) == 2:
            rhs_ymin, rhs_ymax = rhs_y_limits
            subplot_frame.rhs_ymin_var.set("" if rhs_ymin is None else str(rhs_ymin))
            subplot_frame.rhs_ymax_var.set("" if rhs_ymax is None else str(rhs_ymax))

        for axis_key, entries in [("lhs", subplot_frame.lhs_entries),
                                   ("rhs", subplot_frame.rhs_entries)]:
            for idx, item in enumerate(config.get(axis_key, [])):
                if idx < len(entries):
                    entry = entries[idx]
                    entry["column"].set(item.get("column", ""))
                    entry["type"].set(item.get("type", "Line"))
                    entry["marker"].set(item.get("marker", ""))
                    entry["linestyle"].set(item.get("linestyle", "-"))
                    size_value = item.get("size", item.get("ms", 2.0))
                    try:
                        size_value = float(size_value)
                    except (TypeError, ValueError):
                        size_value = 2.0
                    entry["size"].delete(0, tk.END)
                    entry["size"].insert(0, str(size_value))
                    entry["color"].config(bg=item.get("color", "blue"))

if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    try:
        root.iconbitmap(APP_ICON)
    except Exception:
        pass
    app = EnhancedGUI(root)
    root.mainloop()