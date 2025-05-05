import tkinter as tk
from tkinter import ttk, messagebox
from logic import hitung_produksi, rekomendasi_kain
from data import DATASET_KAIN
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from functools import partial


class OptimasiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikasi Optimasi Produksi Pakaian")
        self.geometry("1200x1000")
        self.resizable(True, True)
        self.configure(bg="#f0f0f0")

        # Load daftar produk dari JSON
        jenispakaian_path = os.path.join(os.path.dirname(__file__), 'data', 'jenispakaian.json')
        try:
            with open(jenispakaian_path, 'r', encoding='utf-8') as f:
                self.daftar_produk = json.load(f)
        except Exception:
            self.daftar_produk = ["Kemeja", "Celana panjang", "Seragam", "Dress", "Blus", "Jas", "Legging", "Gaun", "Jeans"]
            messagebox.showwarning("Peringatan", "Gagal memuat daftar produk, menggunakan default.")

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        # Dataset
        self.dataset = DATASET_KAIN
        self.jenis_kain = list(self.dataset.keys())[0]
        self.ukuran_fokus = None
        self.optimasi_sisa = False
        self.produk_target = "Kemeja"  # Default
        self.updating_percentages = False  # Flag to prevent recursive updates

        # UI
        self.buat_antarmuka()

    def configure_styles(self):
        """Configure custom styles for widgets"""
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 11), foreground="#7f8c8d")
        self.style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"), foreground="#2c3e50")
        self.style.configure("TCombobox", padding=5)
        self.style.configure("TEntry", padding=5)
        self.style.configure("TCheckbutton", background="#f0f0f0")
        self.style.map("TButton",
                       foreground=[('pressed', 'white'), ('active', 'white')],
                       background=[('pressed', '#2980b9'), ('active', '#3498db')])
        self.style.configure("Treeview",
                           font=("Segoe UI", 9),
                           rowheight=25,
                           background="#ffffff",
                           fieldbackground="#ffffff")
        self.style.configure("Treeview.Heading",
                           font=("Segoe UI", 10, "bold"),
                           background="#3498db",
                           foreground="white")
        self.style.map("Treeview.Heading",
                     background=[('active', '#2980b9')])
        self.style.map("TCheckbutton",
                     background=[('selected', '#f0f0f0')])

    def buat_antarmuka(self):
        # Canvas untuk scrolling
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main frame untuk UI
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(header_frame, text="OPTIMASI PRODUKSI PAKAIAN", style="Header.TLabel").pack()
        ttk.Label(header_frame,
                text="Aplikasi untuk menghitung produksi optimal berdasarkan bahan yang tersedia",
                style="Subheader.TLabel").pack()

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab Input
        self.tab_input = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.tab_input, text="Input Data")

        input_frame = ttk.Frame(self.tab_input)
        input_frame.pack(pady=10, fill="x")
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Jenis Produk:", style="TLabel").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.combo_produk = ttk.Combobox(
            input_frame,
            values=self.daftar_produk,
            state="readonly"
        )
        self.combo_produk.current(0)
        self.combo_produk.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.combo_produk.bind("<<ComboboxSelected>>", self.update_rekomendasi_kain)

        ttk.Label(input_frame, text="Jenis Kain:", style="TLabel").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.combo_kain = ttk.Combobox(input_frame, values=list(self.dataset.keys()), state="readonly")
        self.combo_kain.current(0)
        self.combo_kain.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.combo_kain.bind("<<ComboboxSelected>>", lambda e: self.update_ukuran_controls())

        self.label_rekomendasi = ttk.Label(input_frame, text="", style="TLabel", foreground="#27ae60")
        self.label_rekomendasi.grid(row=1, column=2, padx=10, pady=5, sticky="w")

        ttk.Label(input_frame, text="Total Kain (meter):", style="TLabel").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entri_kain = ttk.Entry(input_frame)
        self.entri_kain.insert(0, "100")
        self.entri_kain.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.entri_kain.bind("<Return>", lambda event: self.jalankan_optimasi())

        self.ukuran_frame = ttk.LabelFrame(self.tab_input, text="Fokus Ukuran Produksi", padding=10)
        self.ukuran_frame.pack(fill="x", pady=10)

        self.persentase_frame = ttk.LabelFrame(self.tab_input, text="Persentase Produksi", padding=10)
        self.persentase_frame.pack(fill="x", pady=10)

        self.ukuran_vars = {}
        self.persentase_vars = {}

        # Add a label for remaining percentage
        self.label_sisa_persen = ttk.Label(
            self.persentase_frame,
            text="Sisa Persentase: 100%",
            style="TLabel"
        )
        self.label_sisa_persen.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Add an "Auto Fill" button
        self.btn_auto_fill = ttk.Button(
            self.persentase_frame,
            text="Isi Otomatis",
            command=self.auto_fill_percentages,
            style="TButton"
        )
        self.btn_auto_fill.grid(row=0, column=3, padx=10, pady=5, sticky="e")

        self.update_ukuran_controls()

        opsi_frame = ttk.LabelFrame(self.tab_input, text="Opsi Tambahan", padding=10)
        opsi_frame.pack(fill="x", pady=10)
        self.optimasi_sisa_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opsi_frame,
            text="Optimasi untuk Minimasi Sisa Kain",
            variable=self.optimasi_sisa_var
        ).pack(anchor="w")

        button_frame = ttk.Frame(self.tab_input)
        button_frame.pack(pady=20)
        self.tombol_hitung = ttk.Button(
            button_frame,
            text="HITUNG PRODUKSI OPTIMAL",
            command=self.jalankan_optimasi,
            style="TButton"
        )
        self.tombol_hitung.pack(pady=10, ipadx=20, ipady=5)

        # Tab Hasil
        self.tab_hasil = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hasil, text="Hasil Optimasi")
        results_container = ttk.Frame(self.tab_hasil)
        results_container.pack(fill="both", expand=True, padx=20, pady=20)
        top_frame = ttk.Frame(results_container)
        top_frame.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        self.tabel_hasil = ttk.Treeview(
            tree_frame,
            columns=("size", "count", "meter_per", "total_meter", "profit_each", "profit_total"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        scrollbar.config(command=self.tabel_hasil.yview)

        column_defs = [
            ("size", 100, "Ukuran"),
            ("count", 80, "Jumlah"),
            ("meter_per", 120, "Meter/Pakaian"),
            ("total_meter", 120, "Total Meter"),
            ("profit_each", 150, "Keuntungan/Pakaian"),
            ("profit_total", 150, "Total Keuntungan"),
        ]

        for ident, width, heading in column_defs:
            self.tabel_hasil.heading(ident, text=heading, anchor="center")
            self.tabel_hasil.column(ident, width=width, anchor="center")

        self.tabel_hasil.pack(fill="both", expand=True)

        graph_frame = ttk.Frame(top_frame)
        graph_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.graph_container = ttk.Frame(graph_frame)
        self.graph_container.pack(fill="both", expand=True)

        summary_frame = ttk.Frame(results_container)
        summary_frame.pack(fill="x", pady=(20, 10))
        self.label_total = ttk.Label(
            summary_frame,
            text="Masukkan data dan klik 'Hitung Produksi Optimal' untuk melihat hasil",
            style="Result.TLabel"
        )
        self.label_total.pack()

        self.update_rekomendasi_kain()

    def update_rekomendasi_kain(self, event=None):
        self.produk_target = self.combo_produk.get()
        rekomendasi = rekomendasi_kain(self.dataset, self.produk_target)
        self.label_rekomendasi.config(text=f"Rekomendasi: {', '.join(rekomendasi)}")
        if self.combo_kain.get() not in rekomendasi:
            self.combo_kain.set(rekomendasi[0] if rekomendasi else "")

    def update_ukuran_controls(self):
        jenis_kain = self.combo_kain.get()
        ukuran_tersedia = list(self.dataset[jenis_kain]["meter_per_ukuran"].keys())

        # Hapus kontrol lama
        for widget in self.ukuran_frame.winfo_children():
            widget.destroy()
        for widget in self.persentase_frame.winfo_children():
            widget.destroy()

        # Reset variabel kontrol
        self.ukuran_vars = {}
        self.persentase_vars = {}

        # Buat kontrol baru
        for i, ukuran in enumerate(ukuran_tersedia):
            self.ukuran_vars[ukuran] = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(
                self.ukuran_frame,
                text=ukuran.upper(),
                variable=self.ukuran_vars[ukuran],
                command=partial(self.on_checkbox_change, ukuran)
            )
            cb.grid(row=0, column=i, padx=5, pady=2, sticky="w")

            ttk.Label(self.persentase_frame, text=f"{ukuran.upper()} (%)").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            self.persentase_vars[ukuran] = tk.StringVar(value="25.0" if len(ukuran_tersedia) == 4 else "0")
            entry = ttk.Entry(self.persentase_frame, textvariable=self.persentase_vars[ukuran], width=10)
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            entry.bind("<FocusOut>", partial(self.on_percentage_change, ukuran))
            entry.bind("<KeyRelease>", partial(self.on_percentage_change, ukuran))

        # Buat ulang label sisa persentase
        self.label_sisa_persen = ttk.Label(
            self.persentase_frame,
            text="Sisa Persentase: 100%",
            style="TLabel"
        )
        self.label_sisa_persen.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Tambahkan tombol "Isi Otomatis"
        self.btn_auto_fill = ttk.Button(
            self.persentase_frame,
            text="Isi Otomatis",
            command=self.auto_fill_percentages,
            style="TButton"
        )
        self.btn_auto_fill.grid(row=0, column=3, padx=10, pady=5, sticky="e")

    def on_checkbox_change(self, ukuran):
        if self.updating_percentages:
            return
        if not self.ukuran_vars[ukuran].get():
            self.persentase_vars[ukuran].set("0")
        self.redistribute_percentages()

    def on_percentage_change(self, ukuran, *args):
        if self.updating_percentages:
            return
        try:
            value = self.persentase_vars[ukuran].get()
            if not value:
                return
            persen = float(value)
            if persen < 0 or persen > 100:
                raise ValueError("Persentase harus antara 0-100")
            if persen > 0 and not self.ukuran_vars[ukuran].get():
                self.ukuran_vars[ukuran].set(True)
            self.redistribute_percentages()
        except ValueError:
            pass

    def redistribute_percentages(self):
        if self.updating_percentages:
            return
        self.updating_percentages = True
        try:
            active_sizes = [uk for uk in self.persentase_vars if self.ukuran_vars[uk].get()]
            if not active_sizes:
                return

            total = sum(float(self.persentase_vars[uk].get() or 0) for uk in active_sizes)
            self.label_sisa_persen.config(text=f"Sisa Persentase: {100 - total:.1f}%")  # Update label sisa persentase

            if total == 0:
                equal_share = 100 / len(active_sizes)
                for uk in active_sizes:
                    self.persentase_vars[uk].set(str(round(equal_share, 2)))
            elif total > 100:
                factor = 100 / total
                for uk in active_sizes:
                    val = float(self.persentase_vars[uk].get())
                    self.persentase_vars[uk].set(str(round(val * factor, 2)))
        finally:
            self.updating_percentages = False

    def auto_fill_percentages(self):
        """Automatically distribute percentages evenly among selected sizes."""
        active_sizes = [uk for uk in self.persentase_vars if self.ukuran_vars[uk].get()]
        if not active_sizes:
            return

        equal_share = 100 / len(active_sizes)
        for uk in active_sizes:
            self.persentase_vars[uk].set(str(round(equal_share, 2)))
        self.redistribute_percentages()

    def get_persentase_dict(self):
        return {
            uk: float(self.persentase_vars[uk].get() or 0)
            for uk in self.persentase_vars
            if self.ukuran_vars[uk].get()
        }

    def jalankan_optimasi(self):
        try:
            total_kain = float(self.entri_kain.get())
            if total_kain <= 0:
                raise ValueError("Total kain harus lebih besar dari 0")
            jenis_kain = self.combo_kain.get()
            self.ukuran_fokus = [uk for uk, var in self.ukuran_vars.items() if var.get()]
            if not self.ukuran_fokus:
                raise ValueError("Pilih minimal satu ukuran untuk difokuskan")
            persentase = self.get_persentase_dict()
            total_persen = sum(persentase.values())
            if total_persen > 100:
                raise ValueError("Total persentase tidak boleh melebihi 100%")
            self.optimasi_sisa = self.optimasi_sisa_var.get()
            hasil, keuntungan_total, sisa_kain, fig = hitung_produksi(
                total_kain,
                jenis_kain,
                self.dataset,
                self.ukuran_fokus,
                self.optimasi_sisa,
                persentase
            )

            for item in self.tabel_hasil.get_children():
                self.tabel_hasil.delete(item)

            for ukuran, jumlah in hasil.items():
                meter = self.dataset[jenis_kain]["meter_per_ukuran"][ukuran]
                keuntungan = self.dataset[jenis_kain]["keuntungan_per_pakaian"][ukuran]
                total_meter_ukuran = meter * jumlah
                total_keuntungan_ukuran = keuntungan * jumlah
                self.tabel_hasil.insert(
                    "", "end",
                    values=(
                        ukuran.upper(),
                        jumlah,
                        f"{meter:.2f} m",
                        f"{total_meter_ukuran:.2f} m",
                        f"Rp{int(keuntungan):,}".replace(",", "."),
                        f"Rp{int(total_keuntungan_ukuran):,}".replace(",", ".")
                    )
                )

            for widget in self.graph_container.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

            efisiensi = (total_kain - sisa_kain) / total_kain * 100
            self.label_total.config(
                text=f"Total Keuntungan: Rp{int(keuntungan_total):,} | "
                     f"Sisa Kain: {sisa_kain:.2f} m | Efisiensi: {efisiensi:.1f}%",
                foreground="#27ae60"
            )
            self.notebook.select(self.tab_hasil)

        except ValueError as e:
            messagebox.showerror("Input Tidak Valid", str(e))
            self.entri_kain.focus_set()
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")