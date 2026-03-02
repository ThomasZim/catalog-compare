"""Tkinter interface: 3 screens (selection, mapping, results)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .comparator import ComparisonResult, compare_catalogs
from .csv_parser import auto_detect_columns, parse_csv
from .pdf_report import generate_pdf

# Colors
BG = "#f5f5f7"
BG_CARD = "#ffffff"
ACCENT = "#4a6fa5"
ACCENT_HOVER = "#3d5d8a"
TEXT = "#1d1d1f"
TEXT_LIGHT = "#86868b"
GREEN = "#34c759"
RED = "#ff3b30"
BLUE = "#007aff"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Catalog Compare")
        self.geometry("1000x680")
        self.minsize(950, 620)
        self.configure(bg=BG)

        self.old_path: str | None = None
        self.new_path: str | None = None
        self.old_headers: list[str] = []
        self.new_headers: list[str] = []
        self.old_rows: list[list[str]] = []
        self.new_rows: list[list[str]] = []
        self.result: ComparisonResult | None = None

        # ttk style
        self._setup_styles()

        self._container = tk.Frame(self, bg=BG)
        self._container.pack(fill="both", expand=True, padx=30, pady=25)

        self._show_screen1()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[12, 6], font=("Helvetica", 10), background="#e8e8ed", foreground=TEXT)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT), ("!selected", "#e8e8ed")],
                  foreground=[("selected", "white"), ("!selected", TEXT)])

        style.configure("Treeview", font=("Helvetica", 10), rowheight=26, borderwidth=0,
                        background="white", foreground=TEXT, fieldbackground="white")
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), padding=[4, 4],
                        background="#e8e8ed", foreground=TEXT)
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        style.configure("TCombobox", padding=4, foreground=TEXT, fieldbackground="white")
        style.map("TCombobox", foreground=[("readonly", TEXT)], fieldbackground=[("readonly", "white")])

    # --- Screen 1: File selection ---

    def _show_screen1(self):
        self._clear()

        # Title
        tk.Label(
            self._container, text="Catalog Compare",
            font=("Helvetica", 22, "bold"), bg=BG, fg=TEXT,
        ).pack(pady=(20, 5))
        tk.Label(
            self._container, text="Select the two CSV files to compare",
            font=("Helvetica", 12), bg=BG, fg=TEXT_LIGHT,
        ).pack(pady=(0, 30))

        # Selection card
        card = tk.Frame(self._container, bg=BG_CARD, padx=30, pady=25, relief="flat", highlightbackground="#e0e0e0", highlightthickness=1)
        card.pack(fill="x", padx=60)

        # Old catalog
        self._old_label = self._file_row(card, "Old catalog", self._browse_old)

        # Separator
        tk.Frame(card, bg="#e0e0e0", height=1).pack(fill="x", pady=12)

        # New catalog
        self._new_label = self._file_row(card, "New catalog", self._browse_new)

        # Next button
        self._next_btn = tk.Button(
            self._container, text="Next", state="disabled",
            command=self._go_to_screen2, font=("Helvetica", 12, "bold"),
            bg=ACCENT, fg=TEXT, activebackground=ACCENT_HOVER, activeforeground=TEXT,
            relief="flat", padx=30, pady=8, cursor="hand2",
        )
        self._next_btn.pack(pady=(30, 0))

    def _file_row(self, parent, label_text, command):
        frame = tk.Frame(parent, bg=BG_CARD)
        frame.pack(fill="x", pady=4)

        tk.Label(
            frame, text=label_text, font=("Helvetica", 11, "bold"),
            bg=BG_CARD, fg=TEXT, width=18, anchor="w",
        ).pack(side="left")

        file_label = tk.Label(
            frame, text="No file selected",
            font=("Helvetica", 11), bg=BG_CARD, fg=TEXT_LIGHT, anchor="w",
        )
        file_label.pack(side="left", fill="x", expand=True, padx=(10, 10))

        btn = tk.Button(
            frame, text="Browse...", command=command,
            font=("Helvetica", 10), relief="flat", bg="#e8e8ed", fg=TEXT,
            activebackground="#d1d1d6", activeforeground=TEXT, padx=12, pady=3, cursor="hand2",
        )
        btn.pack(side="right")

        return file_label

    def _browse_old(self):
        path = filedialog.askopenfilename(
            title="Select the old catalog",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.old_path = path
            self._old_label.config(text=path.split("/")[-1], fg=TEXT)
            self._check_ready()

    def _browse_new(self):
        path = filedialog.askopenfilename(
            title="Select the new catalog",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.new_path = path
            self._new_label.config(text=path.split("/")[-1], fg=TEXT)
            self._check_ready()

    def _check_ready(self):
        if self.old_path and self.new_path:
            self._next_btn.config(state="normal")

    # --- Screen 2: Column mapping ---

    def _go_to_screen2(self):
        try:
            self.old_headers, self.old_rows = parse_csv(self.old_path)
            self.new_headers, self.new_rows = parse_csv(self.new_path)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to read CSV files:\n{e}")
            return

        self._show_screen2()

    def _show_screen2(self):
        self._clear()

        tk.Label(
            self._container, text="Column Mapping",
            font=("Helvetica", 18, "bold"), bg=BG, fg=TEXT,
        ).pack(pady=(0, 15))

        # Side-by-side frame
        mapping_frame = tk.Frame(self._container, bg=BG)
        mapping_frame.pack(fill="both", expand=True)
        mapping_frame.columnconfigure(0, weight=1)
        mapping_frame.columnconfigure(1, weight=1)

        # Old catalog
        old_card = tk.Frame(mapping_frame, bg=BG_CARD, padx=15, pady=12, highlightbackground="#e0e0e0", highlightthickness=1)
        old_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(old_card, text=f"Old ({len(self.old_rows)} rows)", font=("Helvetica", 12, "bold"), bg=BG_CARD, fg=TEXT).pack(anchor="w", pady=(0, 8))

        old_detected = auto_detect_columns(self.old_headers)
        self._old_barcode, self._old_cost, self._old_name = self._create_mapping_widgets(
            old_card, self.old_headers, old_detected
        )
        self._create_preview(old_card, self.old_headers, self.old_rows[:3])

        # New catalog
        new_card = tk.Frame(mapping_frame, bg=BG_CARD, padx=15, pady=12, highlightbackground="#e0e0e0", highlightthickness=1)
        new_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        tk.Label(new_card, text=f"New ({len(self.new_rows)} rows)", font=("Helvetica", 12, "bold"), bg=BG_CARD, fg=TEXT).pack(anchor="w", pady=(0, 8))

        new_detected = auto_detect_columns(self.new_headers)
        self._new_barcode, self._new_cost, self._new_name = self._create_mapping_widgets(
            new_card, self.new_headers, new_detected
        )
        self._create_preview(new_card, self.new_headers, self.new_rows[:3])

        # Buttons
        btn_frame = tk.Frame(self._container, bg=BG)
        btn_frame.pack(pady=(15, 0))

        tk.Button(
            btn_frame, text="Back", command=self._show_screen1,
            font=("Helvetica", 11), relief="flat", bg="#e8e8ed", fg=TEXT,
            activebackground="#d1d1d6", activeforeground=TEXT, padx=20, pady=6, cursor="hand2",
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Compare", command=self._run_comparison,
            font=("Helvetica", 12, "bold"), relief="flat",
            bg=ACCENT, fg=TEXT, activebackground=ACCENT_HOVER, activeforeground=TEXT,
            padx=25, pady=6, cursor="hand2",
        ).pack(side="left", padx=8)

    def _create_mapping_widgets(self, parent, headers, detected):
        options = ["-- Select --"] + headers

        frame = tk.Frame(parent, bg=BG_CARD)
        frame.pack(fill="x")

        for label_text, key in [("Barcode", "barcode"), ("Cost", "cost"), ("Product name", "name")]:
            row = tk.Frame(frame, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label_text}:", font=("Helvetica", 10), bg=BG_CARD, fg=TEXT, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=headers[detected[key]] if detected[key] is not None else options[0])
            ttk.Combobox(row, textvariable=var, values=options, state="readonly", width=25).pack(side="left", fill="x", expand=True)
            if key == "barcode":
                barcode_var = var
            elif key == "cost":
                cost_var = var
            else:
                name_var = var

        return barcode_var, cost_var, name_var

    def _create_preview(self, parent, headers, rows):
        tk.Label(parent, text="Preview:", font=("Helvetica", 9, "bold"), bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(10, 3))

        display_cols = min(4, len(headers))
        preview_text = "  |  ".join(headers[:display_cols]) + "\n"
        preview_text += "-" * 50 + "\n"
        for row in rows:
            vals = [str(row[i])[:20] if i < len(row) else "" for i in range(display_cols)]
            preview_text += "  |  ".join(vals) + "\n"

        text_widget = tk.Text(
            parent, height=5, font=("Courier", 9), wrap="none",
            bg="#fafafa", fg=TEXT, relief="flat", highlightbackground="#e0e0e0", highlightthickness=1,
            padx=8, pady=6,
        )
        text_widget.insert("1.0", preview_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="x", pady=(0, 5))

    def _get_col_index(self, var: tk.StringVar, headers: list[str]) -> int | None:
        val = var.get()
        if val == "-- Select --":
            return None
        try:
            return headers.index(val)
        except ValueError:
            return None

    def _run_comparison(self):
        old_barcode = self._get_col_index(self._old_barcode, self.old_headers)
        old_cost = self._get_col_index(self._old_cost, self.old_headers)
        old_name = self._get_col_index(self._old_name, self.old_headers)

        new_barcode = self._get_col_index(self._new_barcode, self.new_headers)
        new_cost = self._get_col_index(self._new_cost, self.new_headers)
        new_name = self._get_col_index(self._new_name, self.new_headers)

        missing = []
        if old_barcode is None:
            missing.append("Barcode (old)")
        if old_cost is None:
            missing.append("Cost (old)")
        if old_name is None:
            missing.append("Name (old)")
        if new_barcode is None:
            missing.append("Barcode (new)")
        if new_cost is None:
            missing.append("Cost (new)")
        if new_name is None:
            missing.append("Name (new)")

        if missing:
            messagebox.showwarning("Missing columns", "Please select:\n- " + "\n- ".join(missing))
            return

        try:
            self.result = compare_catalogs(
                self.old_rows, {"barcode": old_barcode, "cost": old_cost, "name": old_name},
                self.new_rows, {"barcode": new_barcode, "cost": new_cost, "name": new_name},
            )
        except Exception as e:
            messagebox.showerror("Error", f"Comparison error:\n{e}")
            return

        self._show_screen3()

    # --- Screen 3: Results ---

    def _show_screen3(self):
        self._clear()
        r = self.result

        tk.Label(
            self._container, text="Results",
            font=("Helvetica", 18, "bold"), bg=BG, fg=TEXT,
        ).pack(pady=(0, 12))

        # Summary cards
        summary_frame = tk.Frame(self._container, bg=BG)
        summary_frame.pack(fill="x", pady=(0, 10))

        self._summary_card(summary_frame, "Old", f"{r.old_count}", "#e8e8ed", TEXT)
        self._summary_card(summary_frame, "New", f"{r.new_count}", "#e8e8ed", TEXT)
        self._summary_card(summary_frame, "Added", str(len(r.appeared)), "#d1f2d9", "#1b7a2e")
        self._summary_card(summary_frame, "Removed", str(len(r.disappeared)), "#fdd", "#c0392b")
        self._summary_card(summary_frame, "Changes", str(len(r.cost_changes)), "#d6eaf8", "#2471a3")

        # Results tabs
        notebook = ttk.Notebook(self._container)
        notebook.pack(fill="both", expand=True, pady=(5, 10))

        # Added tab
        tab_app = tk.Frame(notebook, bg=BG)
        notebook.add(tab_app, text=f" Added ({len(r.appeared)}) ")
        self._create_result_table(tab_app, ["Barcode", "Name", "Cost"],
                                  [(p.barcode, p.name, f"{p.cost:.2f}" if p.cost else "N/A") for p in r.appeared])

        # Removed tab
        tab_dis = tk.Frame(notebook, bg=BG)
        notebook.add(tab_dis, text=f" Removed ({len(r.disappeared)}) ")
        self._create_result_table(tab_dis, ["Barcode", "Name", "Cost"],
                                  [(p.barcode, p.name, f"{p.cost:.2f}" if p.cost else "N/A") for p in r.disappeared])

        # Changes tab
        tab_chg = tk.Frame(notebook, bg=BG)
        notebook.add(tab_chg, text=f" Changes ({len(r.cost_changes)}) ")
        self._create_result_table(
            tab_chg,
            ["Barcode", "Old name", "New name", "Old", "New", "Change"],
            [(c.barcode, c.old_name,
              c.new_name if c.name_changed else "-",
              f"{c.old_cost:.2f}" if c.old_cost is not None else "N/A",
              f"{c.new_cost:.2f}" if c.new_cost is not None else "N/A",
              f"{c.variation_pct:+.1f}%" if c.variation_pct is not None else "N/A")
             for c in r.cost_changes],
        )

        # Buttons
        btn_frame = tk.Frame(self._container, bg=BG)
        btn_frame.pack(pady=(8, 0))

        tk.Button(
            btn_frame, text="Export PDF", command=self._export_pdf,
            font=("Helvetica", 12, "bold"), relief="flat",
            bg=ACCENT, fg=TEXT, activebackground=ACCENT_HOVER, activeforeground=TEXT,
            padx=20, pady=6, cursor="hand2",
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="New comparison", command=self._reset,
            font=("Helvetica", 11), relief="flat", bg="#e8e8ed", fg=TEXT,
            activebackground="#d1d1d6", activeforeground=TEXT, padx=16, pady=6, cursor="hand2",
        ).pack(side="left", padx=8)

    def _summary_card(self, parent, label, value, bg_color, fg_color):
        card = tk.Frame(parent, bg=bg_color, padx=12, pady=8, highlightbackground="#d0d0d0", highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=3)
        tk.Label(card, text=value, font=("Helvetica", 16, "bold"), bg=bg_color, fg=fg_color).pack()
        tk.Label(card, text=label, font=("Helvetica", 9), bg=bg_color, fg=TEXT_LIGHT).pack()

    def _create_result_table(self, parent, columns, data):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        col_widths = {
            "Barcode": 100,
            "Old name": 220,
            "New name": 200,
            "Cost": 80,
            "Old": 80,
            "New": 80,
            "Change": 80,
        }

        for col in columns:
            tree.heading(col, text=col)
            w = col_widths.get(col, 100)
            tree.column(col, width=w, minwidth=60)

        for row in data:
            tree.insert("", "end", values=row)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(
            title="Save PDF report",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
            initialfile="catalog_comparison.pdf",
        )
        if not path:
            return

        try:
            generate_pdf(self.result, path)
            messagebox.showinfo("Success", f"Report exported:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to generate PDF:\n{e}")

    def _reset(self):
        self.old_path = None
        self.new_path = None
        self.old_headers = []
        self.new_headers = []
        self.old_rows = []
        self.new_rows = []
        self.result = None
        self._show_screen1()

    def _clear(self):
        for widget in self._container.winfo_children():
            widget.destroy()
