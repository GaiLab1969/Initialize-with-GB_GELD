import tkinter as tk
from tkinter import ttk, messagebox, Canvas
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import json
import os
from collections import defaultdict
import math
import webbrowser

BG_DARK = "#0a1428"
BG_ACCENT = "#1a3a52"
BG_CARD = "#1f2937"
ACCENT_GREEN = "#10b981"
ACCENT_RED = "#ef4444"
TEXT_LIGHT = "#f0f4f8"
TEXT_SECONDARY = "#9ca3af"
BG_INPUT = "#1e293b"
BTN_BLUE = "#3b82f6"
BTN_YELLOW = "#fbbf24"
FONT_TITLE_BIG = ("Calibri", 16, "bold")
FONT_TITLE = ("Calibri", 12, "bold")
FONT_MAIN = ("Calibri", 9)
FONT_SMALL = ("Calibri", 8)
FONT_GRAPH = ("Calibri", 9, "bold")
FONT_GRAPH_TITLE = ("Calibri", 14, "bold")
FONT_BALANCE = ("Calibri", 14, "bold")
DATAFILE = "wallet_data.json"
CATFILE = "categories_data.json"
BG_MAIN_FILE = "bg_main.png"
BG_LINDEN_FILE = "Lindentekh.jpg"
COLOR_INCOME = ACCENT_GREEN
COLOR_EXPENSE = ACCENT_RED
RAINBOW_COLORS = [
    "#ff0000", "#ff7f00", "#ffff00", "#00ff00", "#0000ff",
    "#4b0082", "#9400d3", "#ff1493", "#00ced1", "#32cd32",
    "#ff4500", "#1e90ff"
]

DEFAULT_CATEGORIES = {
    "Доход": [
        ["💼", "Музд (зарплата)"], ["💰", "Бизнес"], ["🎁", "Тӯҳфа"], ["🏦", "Ҳавола/переводы"],
        ["📈", "Сармоягузорӣ"], ["🏆", "Ҷоиза"], ["💵", "Дигар"]
    ],
    "Расход": [
        ["🍎", "Хӯрок"], ["🥦", "Маҳсулот"], ["🍔", "Кафе"], ["🏠", "Хона"], ["🧾", "Хизматҳо"],
        ["🛒", "Мағоза"], ["👕", "Либос"], ["👟", "Пойафзол"], ["🚆", "Транспорт"], ["🚗", "Авто"],
        ["💊", "Дору"], ["🏥", "Тиб"], ["✈️", "Саёҳат"], ["🏖️", "Истироҳат"], ["📚", "Маориф"],
        ["🎁", "Тӯҳфа"], ["🎉", "Фароғат"], ["📱", "Алока"], ["💻", "Интернет"], ["🐾", "Ҳайвонот"],
        ["🧒", "Кӯдакон"], ["🏋️", "Варзиш"], ["🧾", "Дигар"]
    ]
}

def dt(form):
    try:
        return datetime.strptime(form, "%d.%m.%Y").date()
    except:
        return None

def open_lindentech():
    webbrowser.open("https://lindentech.de/ru")

class WalletApp:
    def __init__(self, root):
        self.root = root
        self.root.title('💳 LabGai Premium v3.9')
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        self.root.config(bg=BG_DARK)
        self.transactions = []
        self.categories = self.load_categories()
        self.load_data()
        self.filter_updating = False
        self.show_filter = tk.StringVar(value="Все")
        self.report_show_filter = tk.StringVar(value="Все")
        self.graph_type = tk.StringVar(value="pie")
        self.global_date_from = None
        self.global_date_to = None
        self.bg_images = {}
        self.setup_backgrounds()
        self.build_ui()

    def setup_backgrounds(self):
        if os.path.exists(BG_MAIN_FILE):
            try:
                img = Image.open(BG_MAIN_FILE)
                self.bg_images['main'] = ImageTk.PhotoImage(img)
            except:
                pass
        if os.path.exists(BG_LINDEN_FILE):
            try:
                img = Image.open(BG_LINDEN_FILE)
                img = img.resize((570, 100), Image.Resampling.LANCZOS)
                self.bg_images['linden'] = ImageTk.PhotoImage(img)
            except:
                pass

    def get_total_balance(self):
        return sum(t["amount"] for t in self.transactions)

    def get_period_balance(self):
        total = 0
        if self.global_date_from and self.global_date_to:
            for tr in self.transactions:
                tr_date = dt(tr["date"].split()[0])
                if tr_date and self.global_date_from <= tr_date <= self.global_date_to:
                    total += tr["amount"]
        return total

    def get_filtered_items(self, show_type="Все"):
        items = []
        if not self.global_date_from or not self.global_date_to:
            return items
        for tr in self.transactions:
            tr_date = dt(tr["date"].split()[0])
            if not tr_date:
                continue
            if tr_date < self.global_date_from or tr_date > self.global_date_to:
                continue
            if show_type != "Все" and tr["type"] != show_type:
                continue
            items.append(tr)
        return items

    def update_all_views(self):
        self.apply_filters()
        self.show_report_tab()
        self.show_graph_filtered()

    def set_period(self, mode="day"):
        today = datetime.today().date()
        if mode == "day":
            self.global_date_from = today
            self.global_date_to = today
        elif mode == "week":
            self.global_date_from = today - timedelta(days=today.weekday())
            self.global_date_to = self.global_date_from + timedelta(days=6)
        elif mode == "month":
            self.global_date_from = today.replace(day=1)
            last = today.replace(day=1) + timedelta(days=32)
            self.global_date_to = last.replace(day=1) - timedelta(days=1)
        elif mode == "all":
            if self.transactions:
                dates = [dt(tr["date"].split()[0]) for tr in self.transactions if dt(tr["date"].split()[0])]
                if dates:
                    self.global_date_from = min(dates)
                    self.global_date_to = max(dates)
        self.update_all_views()

    def set_manual_period(self):
        try:
            self.global_date_from = self.manual_date_from.get_date()
            self.global_date_to = self.manual_date_to.get_date()
            self.update_all_views()
        except:
            pass

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG_CARD, height=50)
        header.pack(fill="x", padx=0, pady=0)
        tk.Label(header, text='💳 LabGai Premium v3.9', font=FONT_TITLE_BIG,
                 bg=BG_CARD, fg="#4ade80", pady=8).pack(side="left", padx=16)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill='both', expand=True)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=BG_DARK, borderwidth=0)
        style.configure('TNotebook.Tab', font=("Calibri", 9, "bold"), padding=[16, 6], background=BG_CARD, foreground=TEXT_SECONDARY)
        style.map('TNotebook.Tab', background=[('selected', ACCENT_GREEN)], foreground=[('selected', BG_DARK)])
        style.configure("Treeview", background=BG_CARD, fieldbackground=BG_CARD, foreground=TEXT_LIGHT, rowheight=20)
        style.configure("Treeview.Heading", font=("Calibri", 9, "bold"), background=BG_CARD, foreground=ACCENT_GREEN)

        self.main_fr = tk.Frame(self.tabs, bg=BG_DARK)
        self.tabs.add(self.main_fr, text="📋 Главная")
        self.cat_fr = tk.Frame(self.tabs, bg=BG_DARK)
        self.tabs.add(self.cat_fr, text="🏷️ Категории")
        self.rep_fr = tk.Frame(self.tabs, bg=BG_DARK)
        self.tabs.add(self.rep_fr, text="📊 Отчёт")
        self.graph_fr = tk.Frame(self.tabs, bg=BG_DARK)
        self.tabs.add(self.graph_fr, text="📈 Графики")
        self.admin_fr = tk.Frame(self.tabs, bg=BG_DARK)
        self.tabs.add(self.admin_fr, text="⚙️ Администратор")

        self.build_main()
        self.build_categories()
        self.build_report()
        self.build_graph()
        self.build_admin()
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_switched)
        self.set_period("day")

    def build_main(self):
        f = self.main_fr
        
        # КРАСИВЫЙ ФОНОВЫЙ БАННЕР LINDENTECH
        if self.bg_images.get('linden'):
            ad_frame = tk.Frame(f, bg="#001a4d", relief="raised", bd=3, highlightthickness=2, highlightbackground="#0066ff")
            ad_frame.pack(fill="x", padx=12, pady=(8, 4), ipady=2)
            
            # Фоновое изображение
            bg_label = tk.Label(ad_frame, image=self.bg_images['linden'], bg="#001a4d", bd=0)
            bg_label.image = self.bg_images['linden']
            bg_label.pack(fill="both", expand=True)
            
            # Оверлей с градиентным эффектом (тёмный полупрозрачный слой)
            overlay_frame = tk.Frame(ad_frame, bg="#000000", height=120)
            overlay_frame.place(in_=ad_frame, x=0, y=0, relwidth=1, height=120)
            
            # Левая часть - текст
            left_frame = tk.Frame(overlay_frame, bg="#000000")
            left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=12)
            
            ad_text = tk.Label(left_frame, text="🌐 LINDENTECH", fg="#ff9f43",
                               font=("Calibri", 16, "bold"), bg="#000000")
            ad_text.pack(anchor="w")
            
            ad_desc = tk.Label(left_frame, text="Современные решения для вашего бизнеса", fg="#00d4ff",
                              font=("Calibri", 9), bg="#000000")
            ad_desc.pack(anchor="w", pady=(2, 0))
            
            # Правая часть - кнопка
            right_frame = tk.Frame(overlay_frame, bg="#000000")
            right_frame.pack(side="right", fill="both", padx=20, pady=12)
            
            ad_btn = tk.Button(right_frame, text="🚀 ПОСЕТИТЬ САЙТ", bg="#ff9f43", fg="#000000",
                              font=("Calibri", 10, "bold"), relief="raised", bd=2, cursor="hand2",
                              command=open_lindentech,
                              padx=20, pady=8,
                              activebackground="#ffb366",
                              activeforeground="#000000")
            ad_btn.pack(anchor="e")
        else:
            # Версия без изображения - с градиентом из цветов
            ad_frame = tk.Frame(f, bg="#0066ff", relief="raised", bd=3, highlightthickness=2, highlightbackground="#00d4ff")
            ad_frame.pack(fill="x", padx=12, pady=(8, 4), ipady=2)
            
            ad_inner = tk.Frame(ad_frame, bg="#001a4d", height=120)
            ad_inner.pack(fill="both", expand=True, padx=2, pady=2)
            
            left_part = tk.Frame(ad_inner, bg="#001a4d")
            left_part.pack(side="left", fill="both", expand=True, padx=20, pady=12)
            
            ad_text = tk.Label(left_part, text="🌐 LINDENTECH", fg="#ff9f43",
                              font=("Calibri", 14, "bold"), bg="#001a4d")
            ad_text.pack(anchor="w")
            
            ad_desc = tk.Label(left_part, text="Современные решения для вашего бизнеса", fg="#00d4ff",
                              font=("Calibri", 9), bg="#001a4d")
            ad_desc.pack(anchor="w", pady=(2, 0))
            
            right_part = tk.Frame(ad_inner, bg="#001a4d")
            right_part.pack(side="right", fill="both", padx=20, pady=12)
            
            ad_btn = tk.Button(right_part, text="🚀 ПОСЕТИТЬ САЙТ", bg="#ff9f43", fg="#000000",
                              font=("Calibri", 10, "bold"), relief="raised", bd=2, cursor="hand2",
                              command=open_lindentech,
                              padx=20, pady=8,
                              activebackground="#ffb366",
                              activeforeground="#000000")
            ad_btn.pack(anchor="e")

        balbx = tk.Frame(f, bg=BG_CARD, relief="ridge", bd=2)
        balbx.pack(fill="x", padx=12, pady=(4, 6))

        tk.Label(balbx, text="💰 Общий баланс (ВСЕ ВРЕМЯ):", bg=BG_CARD, fg=ACCENT_GREEN, font=FONT_TITLE).pack(anchor="w", padx=12, pady=(6, 0))
        self.bal_var = tk.StringVar()
        tk.Label(balbx, textvariable=self.bal_var, bg=BG_CARD, fg="#4ade80", font=("Calibri", 18, "bold")).pack(anchor="w", padx=12, pady=(2, 6))

        opbox = tk.Frame(f, bg=BG_DARK)
        opbox.pack(fill="x", padx=12, pady=4)

        self.main_type = tk.StringVar(value="Расход")
        rb_opts = {"bg":BG_DARK, "fg":TEXT_LIGHT, "selectcolor":BG_DARK, "font":FONT_MAIN, "activebackground": BG_DARK}
        tk.Radiobutton(opbox, text="📉 Расход", variable=self.main_type, value="Расход", **rb_opts).pack(side="left", padx=6)
        tk.Radiobutton(opbox, text="📈 Доход", variable=self.main_type, value="Доход", **rb_opts).pack(side="left", padx=6)

        tk.Label(opbox, text="Категория:", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_MAIN).pack(side="left", padx=(12, 4))
        self.main_cat = ttk.Combobox(opbox, state='readonly', font=FONT_MAIN, width=16)
        self.main_cat.pack(side="left", padx=4)

        tk.Label(opbox, text="Сумма:", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_MAIN).pack(side="left", padx=(8, 4))
        self.main_sum = tk.Entry(opbox, font=FONT_MAIN, width=10, bg=BG_INPUT, fg=TEXT_LIGHT, relief="flat", borderwidth=1)
        self.main_sum.pack(side="left", padx=4)

        tk.Button(opbox, text="✓ Добавить", command=self.add_operation, bg=ACCENT_GREEN, fg=BG_DARK,
                 font=(FONT_MAIN[0], 9, "bold"), relief="raised", bd=2, cursor="hand2", padx=12).pack(side="left", padx=4)

        self.main_type.trace_add("write", lambda *_: self.refresh_cat_box())
        self.refresh_cat_box()

        flt_dates = tk.Frame(f, bg=BG_DARK)
        flt_dates.pack(fill="x", padx=12, pady=2)

        tk.Button(flt_dates, text="День", bg=BTN_YELLOW, fg=BG_DARK, font=(FONT_SMALL[0], 8, "bold"),
                 command=lambda: self.set_period("day"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(flt_dates, text="Неделя", bg=BTN_BLUE, fg=TEXT_LIGHT, font=(FONT_SMALL[0], 8, "bold"),
                 command=lambda: self.set_period("week"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(flt_dates, text="Месяц", bg="#10b981", fg=TEXT_LIGHT, font=(FONT_SMALL[0], 8, "bold"),
                 command=lambda: self.set_period("month"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)

        self.manual_date_from = DateEntry(flt_dates, width=10, date_pattern='dd.mm.yyyy', font=FONT_SMALL, background=BG_INPUT, foreground=TEXT_LIGHT, selectbackground=ACCENT_GREEN)
        self.manual_date_from.set_date(datetime.today().date())
        self.manual_date_from.pack(side="left", padx=2)

        self.manual_date_to = DateEntry(flt_dates, width=10, date_pattern='dd.mm.yyyy', font=FONT_SMALL, background=BG_INPUT, foreground=TEXT_LIGHT, selectbackground=ACCENT_GREEN)
        self.manual_date_to.set_date(datetime.today().date())
        self.manual_date_to.pack(side="left", padx=2)

        tk.Button(flt_dates, text="▶ Период", bg=ACCENT_GREEN, fg=BG_DARK, font=(FONT_SMALL[0], 8, "bold"),
                 command=self.set_manual_period, relief="raised", bd=2, cursor="hand2", padx=6).pack(side="left", padx=2)
        tk.Button(flt_dates, text="Всё время", bg="#f59e0b", fg=BG_DARK, font=(FONT_SMALL[0], 8, "bold"),
                 command=lambda: self.set_period("all"), relief="raised", bd=2, cursor="hand2", padx=6).pack(side="left", padx=2)

        flt_type = tk.Frame(f, bg=BG_DARK)
        flt_type.pack(fill="x", padx=12, pady=2)

        tk.Label(flt_type, text="🔍 Показать:", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_MAIN).pack(side="left", padx=4)
        tk.Radiobutton(flt_type, text="Все", variable=self.show_filter, value="Все", bg=BG_DARK, fg=TEXT_LIGHT,
                      selectcolor=BG_DARK, font=FONT_MAIN, command=self.apply_filters, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(flt_type, text="Только расходы", variable=self.show_filter, value="Расход", bg=BG_DARK, fg=COLOR_EXPENSE,
                      selectcolor=BG_DARK, font=FONT_MAIN, command=self.apply_filters, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(flt_type, text="Только доходы", variable=self.show_filter, value="Доход", bg=BG_DARK, fg=COLOR_INCOME,
                      selectcolor=BG_DARK, font=FONT_MAIN, command=self.apply_filters, activebackground=BG_DARK).pack(side="left", padx=4)

        frtbl = tk.Frame(f, bg=BG_DARK)
        frtbl.pack(fill="both", expand=True, padx=12, pady=6)

        self.trtable = ttk.Treeview(frtbl, columns=("Дата","Категория","Тип","Сумма"), show="headings", height=10)
        for col, title, w in (("Дата","Дата",90),("Категория","Категория",220),("Тип","Тип",70),("Сумма","Сумма, сомонӣ",140)):
            self.trtable.heading(col, text=title)
            self.trtable.column(col, width=w, anchor="center" if col!="Категория" else "w")

        self.trtable.tag_configure("income", foreground=COLOR_INCOME, font=(FONT_MAIN[0], 9, "bold"))
        self.trtable.tag_configure("expense", foreground=COLOR_EXPENSE, font=(FONT_MAIN[0], 9, "bold"))
        self.trtable.pack(side="left", fill="both", expand=True)

        scr = tk.Scrollbar(frtbl, orient="vertical", command=self.trtable.yview)
        scr.pack(side="right", fill="y")
        self.trtable.configure(yscrollcommand=scr.set)

        totals_frame = tk.Frame(f, bg=BG_CARD, relief="ridge", bd=2)
        totals_frame.pack(fill="x", padx=12, pady=(0, 6))

        left_frame = tk.Frame(totals_frame, bg=BG_CARD)
        left_frame.pack(side="left", fill="x", expand=True, padx=12, pady=6)

        tk.Label(left_frame, text="📊 Итого расходов:", bg=BG_CARD, fg=ACCENT_RED, font=FONT_MAIN).pack(anchor="w")
        self.totals_expense_var = tk.StringVar(value="0.00 сомонӣ")
        tk.Label(left_frame, textvariable=self.totals_expense_var, bg=BG_CARD, fg=ACCENT_RED, font=FONT_BALANCE).pack(anchor="w")

        right_frame = tk.Frame(totals_frame, bg=BG_CARD)
        right_frame.pack(side="right", fill="x", expand=True, padx=12, pady=6)

        tk.Label(right_frame, text="📈 Итого доходов:", bg=BG_CARD, fg=ACCENT_GREEN, font=FONT_MAIN).pack(anchor="e")
        self.totals_income_var = tk.StringVar(value="0.00 сомонӣ")
        tk.Label(right_frame, textvariable=self.totals_income_var, bg=BG_CARD, fg=ACCENT_GREEN, font=FONT_BALANCE).pack(anchor="e")

        self.update_total_balance()

    def update_total_balance(self):
        total = self.get_total_balance()
        self.bal_var.set(f"{total:.2f} сомонӣ")

    def update_totals(self):
        items = self.get_filtered_items(self.show_filter.get())
        income_total = sum(abs(t["amount"]) for t in items if t["amount"] > 0)
        expense_total = sum(abs(t["amount"]) for t in items if t["amount"] < 0)
        self.totals_income_var.set(f"{income_total:.2f} сомонӣ")
        self.totals_expense_var.set(f"{expense_total:.2f} сомонӣ")

    def build_categories(self):
        f = self.cat_fr
        self.cat_type = tk.StringVar(value="Расход")
        top = tk.Frame(f, bg=BG_DARK)
        top.pack(fill="x", padx=12, pady=6)

        for t in ["Расход","Доход"]:
            tk.Radiobutton(top, text=t, variable=self.cat_type, value=t, bg=BG_DARK, fg=TEXT_LIGHT, selectcolor=BG_DARK, font=FONT_MAIN, activebackground=BG_DARK).pack(side="left", padx=8)

        form = tk.Frame(f, bg=BG_DARK)
        form.pack(fill="x", padx=12, pady=4)

        tk.Label(form, text="Эмодзи:", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_MAIN).pack(side="left")
        self.cat_emoji = tk.Entry(form, width=3, font=FONT_MAIN, justify="center", bg=BG_INPUT, fg=TEXT_LIGHT, relief="flat")
        self.cat_emoji.pack(side="left", padx=4)

        tk.Label(form, text="Название:", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_MAIN).pack(side="left", padx=(8, 4))
        self.cat_name = tk.Entry(form, font=FONT_MAIN, bg=BG_INPUT, fg=TEXT_LIGHT, relief="flat")
        self.cat_name.pack(side="left", fill="x", expand=True, padx=4)

        tk.Button(form, text="✓ Сохранить", bg=ACCENT_GREEN, fg=BG_DARK, font=(FONT_MAIN[0], 9, "bold"),
                 command=self.inline_add_cat, relief="raised", bd=2, cursor="hand2", padx=12).pack(side="left", padx=4)

        list_area = tk.Frame(f, bg=BG_DARK)
        list_area.pack(fill="both", expand=True, padx=12, pady=6)

        self.cat_list = tk.Listbox(list_area, font=FONT_MAIN, bg=BG_CARD, fg=TEXT_LIGHT,
                                   selectbackground=ACCENT_GREEN, relief="flat", borderwidth=0, height=8)
        self.cat_list.pack(side="left", fill="both", expand=True)

        scr = tk.Scrollbar(list_area, command=self.cat_list.yview)
        scr.pack(side="left", fill="y")
        self.cat_list.config(yscrollcommand=scr.set)

        btns = tk.Frame(f, bg=BG_DARK)
        btns.pack(pady=6)

        tk.Button(btns, text="✏️ Редактировать", bg=BTN_YELLOW, fg=BG_DARK, font=(FONT_MAIN[0], 10, "bold"),
                 command=self.edit_cat, relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=4)
        tk.Button(btns, text="🗑️ Удалить", bg=ACCENT_RED, fg=TEXT_LIGHT, font=(FONT_MAIN[0], 10, "bold"),
                 command=self.del_cat, relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=4)

        self.cat_type.trace_add("write", lambda *_: self.update_cat_list())
        self.update_cat_list()

    def update_cat_list(self):
        self.cat_list.delete(0, tk.END)
        for icon, name in self.categories[self.cat_type.get()]:
            self.cat_list.insert(tk.END, f"{icon} {name}")
        self.refresh_cat_box()

    def inline_add_cat(self):
        e = self.cat_emoji.get().strip()
        n = self.cat_name.get().strip()
        if not e or not n:
            messagebox.showwarning("Внимание","Заполните эмодзи и название")
            return
        self.categories[self.cat_type.get()].append([e,n])
        self.save_categories()
        self.update_cat_list()
        self.cat_emoji.delete(0, tk.END)
        self.cat_name.delete(0, tk.END)

    def del_cat(self):
        sel = self.cat_list.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.categories[self.cat_type.get()][idx]
        self.save_categories()
        self.update_cat_list()

    def edit_cat(self):
        sel = self.cat_list.curselection()
        if not sel:
            return
        idx = sel[0]
        icon, name = self.categories[self.cat_type.get()][idx]
        self.cat_emoji.delete(0, tk.END)
        self.cat_name.delete(0, tk.END)
        self.cat_emoji.insert(0, icon)
        self.cat_name.insert(0, name)
        self.del_cat()

    def build_report(self):
        f = self.rep_fr
        bar = tk.Frame(f, bg=BG_DARK)
        bar.pack(fill="x", padx=12, pady=6)

        tk.Button(bar, text="День", bg=BTN_YELLOW, fg=BG_DARK, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("day"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar, text="Неделя", bg=BTN_BLUE, fg=TEXT_LIGHT, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("week"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar, text="Месяц", bg="#10b981", fg=TEXT_LIGHT, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("month"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar, text="Всё время", bg="#f59e0b", fg=BG_DARK, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("all"), relief="raised", bd=2, cursor="hand2", padx=6).pack(side="left", padx=2)

        flt_rep = tk.Frame(f, bg=BG_DARK)
        flt_rep.pack(fill="x", padx=12, pady=2)

        tk.Radiobutton(flt_rep, text="Все", variable=self.report_show_filter, value="Все", bg=BG_DARK, fg=TEXT_LIGHT,
                      selectcolor=BG_DARK, font=FONT_SMALL, command=self.show_report_tab, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(flt_rep, text="Только расходы", variable=self.report_show_filter, value="Расход", bg=BG_DARK, fg=COLOR_EXPENSE,
                      selectcolor=BG_DARK, font=FONT_SMALL, command=self.show_report_tab, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(flt_rep, text="Только доходы", variable=self.report_show_filter, value="Доход", bg=BG_DARK, fg=COLOR_INCOME,
                      selectcolor=BG_DARK, font=FONT_SMALL, command=self.show_report_tab, activebackground=BG_DARK).pack(side="left", padx=4)

        self.rep_text = tk.Text(f, font=("Calibri", 10), bg=BG_CARD, fg=TEXT_LIGHT, relief="flat", wrap="word", borderwidth=1)
        self.rep_text.pack(padx=12, pady=6, fill="both", expand=True)

    def show_report_tab(self):
        items = self.get_filtered_items(self.report_show_filter.get())
        self.rep_text.delete(1.0, tk.END)
        
        # Добавляем теги для цветов
        self.rep_text.tag_configure("header", foreground=TEXT_LIGHT, font=("Calibri", 10, "bold"))
        self.rep_text.tag_configure("income", foreground="#4ade80", font=("Calibri", 11, "bold"))
        self.rep_text.tag_configure("expense", foreground="#ef4444", font=("Calibri", 11, "bold"))
        self.rep_text.tag_configure("balance", foreground="#fbbf24", font=("Calibri", 11, "bold"))
        self.rep_text.tag_configure("section", foreground="#00d4ff", font=("Calibri", 10, "bold"))
        
        if not items:
            self.rep_text.insert(tk.END, "Нет операций для отчета", "header")
            return
        
        income = sum(t["amount"] for t in items if t["amount"]>0)
        out = sum(-t["amount"] for t in items if t["amount"]<0)
        balance = income - out
        total_balance = self.get_total_balance()
        
        # ЗАГОЛОВОК
        self.rep_text.insert(tk.END, "═══════════════════════════════════════\n", "header")
        self.rep_text.insert(tk.END, "📊 ОТЧЁТ\n", "header")
        self.rep_text.insert(tk.END, "═══════════════════════════════════════\n\n", "header")
        
        # ОСНОВНЫЕ СУММЫ
        self.rep_text.insert(tk.END, "💰 ДОХОД:\n", "section")
        self.rep_text.insert(tk.END, f"{income:.2f} сомонӣ\n\n", "income")
        
        self.rep_text.insert(tk.END, "💸 РАСХОД:\n", "section")
        self.rep_text.insert(tk.END, f"{out:.2f} сомонӣ\n\n", "expense")
        
        self.rep_text.insert(tk.END, "────────────────────────────────────────\n", "header")
        
        self.rep_text.insert(tk.END, "📈 БАЛАНС ПЕРИОДА:\n", "section")
        self.rep_text.insert(tk.END, f"{balance:.2f} сомонӣ\n\n", "balance")
        
        self.rep_text.insert(tk.END, "💳 ОБЩИЙ БАЛАНС:\n", "section")
        self.rep_text.insert(tk.END, f"{total_balance:.2f} сомонӣ\n", "balance")
        
        self.rep_text.insert(tk.END, "═══════════════════════════════════════\n\n", "header")
        
        # РАСХОДЫ ПО КАТЕГОРИЯМ
        out_by = defaultdict(float)
        for t in items:
            if t["amount"]<0:
                out_by[f'{t["icon"]} {t["category"]}'] += -t["amount"]
        
        if out_by:
            self.rep_text.insert(tk.END, "📉 РАСХОДЫ ПО КАТЕГОРИЯМ:\n", "section")
            self.rep_text.insert(tk.END, "─────────────────────────────────────\n", "header")
            for k, v in sorted(out_by.items(), key=lambda x:-x[1]):
                self.rep_text.insert(tk.END, f"  {k}\n", "header")
                self.rep_text.insert(tk.END, f"  {v:.2f} сомонӣ\n\n", "expense")
        
        # ДОХОДЫ ПО КАТЕГОРИЯМ
        in_by = defaultdict(float)
        for t in items:
            if t["amount"]>0:
                in_by[f'{t["icon"]} {t["category"]}'] += t["amount"]
        
        if in_by:
            self.rep_text.insert(tk.END, "📈 ДОХОДЫ ПО КАТЕГОРИЯМ:\n", "section")
            self.rep_text.insert(tk.END, "─────────────────────────────────────\n", "header")
            for k, v in sorted(in_by.items(), key=lambda x:-x[1]):
                self.rep_text.insert(tk.END, f"  {k}\n", "header")
                self.rep_text.insert(tk.END, f"  {v:.2f} сомонӣ\n\n", "income")

    def build_graph(self):
        f = self.graph_fr
        bar = tk.Frame(f, bg=BG_DARK)
        bar.pack(fill="x", padx=12, pady=6)

        tk.Label(bar, text="📊 Тип графика:", bg=BG_DARK, fg=ACCENT_GREEN, font=FONT_TITLE).pack(side="left", padx=4)
        tk.Radiobutton(bar, text="◯ Круговая (Pie)", variable=self.graph_type, value="pie",
                      bg=BG_DARK, fg=TEXT_LIGHT, selectcolor=BG_DARK, font=FONT_MAIN,
                      command=self.show_graph_filtered, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(bar, text="📊 Столбцы (Bar)", variable=self.graph_type, value="bar",
                      bg=BG_DARK, fg=TEXT_LIGHT, selectcolor=BG_DARK, font=FONT_MAIN,
                      command=self.show_graph_filtered, activebackground=BG_DARK).pack(side="left", padx=4)
        tk.Radiobutton(bar, text="📈 Линия (Line)", variable=self.graph_type, value="line",
                      bg=BG_DARK, fg=TEXT_LIGHT, selectcolor=BG_DARK, font=FONT_MAIN,
                      command=self.show_graph_filtered, activebackground=BG_DARK).pack(side="left", padx=4)

        bar2 = tk.Frame(f, bg=BG_DARK)
        bar2.pack(fill="x", padx=12, pady=4)

        tk.Button(bar2, text="День", bg=BTN_YELLOW, fg=BG_DARK, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("day"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar2, text="Неделя", bg=BTN_BLUE, fg=TEXT_LIGHT, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("week"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar2, text="Месяц", bg="#10b981", fg=TEXT_LIGHT, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("month"), relief="raised", bd=2, cursor="hand2", padx=8).pack(side="left", padx=2)
        tk.Button(bar2, text="Всё время", bg="#f59e0b", fg=BG_DARK, font=(FONT_SMALL[0], 9, "bold"),
                 command=lambda: self.set_period("all"), relief="raised", bd=2, cursor="hand2", padx=6).pack(side="left", padx=2)

        balance_frame = tk.Frame(f, bg=BG_CARD, relief="ridge", bd=2)
        balance_frame.pack(fill="x", padx=12, pady=4)

        left_bal = tk.Frame(balance_frame, bg=BG_CARD)
        left_bal.pack(side="left", fill="x", expand=True, padx=12, pady=6)

        tk.Label(left_bal, text="💰 Общий баланс:", bg=BG_CARD, fg=ACCENT_GREEN, font=FONT_MAIN).pack(anchor="w")
        self.graph_total_var = tk.StringVar()
        tk.Label(left_bal, textvariable=self.graph_total_var, bg=BG_CARD, fg="#4ade80", font=FONT_BALANCE).pack(anchor="w")

        right_bal = tk.Frame(balance_frame, bg=BG_CARD)
        right_bal.pack(side="right", fill="x", expand=True, padx=12, pady=6)

        tk.Label(right_bal, text="📊 Баланс периода:", bg=BG_CARD, fg=BTN_YELLOW, font=FONT_MAIN).pack(anchor="e")
        self.graph_period_var = tk.StringVar()
        tk.Label(right_bal, textvariable=self.graph_period_var, bg=BG_CARD, fg=BTN_YELLOW, font=FONT_BALANCE).pack(anchor="e")

        canv_frame = tk.Frame(f, bg=BG_DARK)
        canv_frame.pack(fill="both", expand=True, padx=12, pady=6)

        center_frame = tk.Frame(canv_frame, bg=BG_DARK)
        center_frame.pack(expand=True)

        self.c_left = Canvas(center_frame, width=400, height=300, bg=BG_CARD, highlightthickness=1, highlightbackground=BG_ACCENT)
        self.c_left.pack(side="left", padx=6, pady=4)

        self.c_right = Canvas(center_frame, width=400, height=300, bg=BG_CARD, highlightthickness=1, highlightbackground=BG_ACCENT)
        self.c_right.pack(side="left", padx=6, pady=4)

    def show_graph_filtered(self):
        self.c_left.delete("all")
        self.c_right.delete("all")
        items = self.get_filtered_items("Все")
        outs = defaultdict(float)
        ins = defaultdict(float)
        for t in items:
            if t["amount"]<0:
                outs[f'{t["icon"]} {t["category"]}'] += -t["amount"]
            if t["amount"]>0:
                ins[f'{t["icon"]} {t["category"]}'] += t["amount"]

        graph_type = self.graph_type.get()
        if graph_type == "pie":
            self.draw_pie_chart(outs, "РАСХОДЫ", ACCENT_RED, self.c_left)
            self.draw_pie_chart(ins, "ДОХОДЫ", ACCENT_GREEN, self.c_right)
        elif graph_type == "bar":
            self.draw_bar_chart(outs, "РАСХОДЫ", self.c_left)
            self.draw_bar_chart(ins, "ДОХОДЫ", self.c_right)
        elif graph_type == "line":
            self.draw_line_chart(outs, "РАСХОДЫ", self.c_left)
            self.draw_line_chart(ins, "ДОХОДЫ", self.c_right)

        total_balance = self.get_total_balance()
        period_balance = self.get_period_balance()
        self.graph_total_var.set(f"{total_balance:.2f} сомонӣ")
        self.graph_period_var.set(f"{period_balance:.2f} сомонӣ")

    def draw_pie_chart(self, data, title, color, canvas):
        if not data:
            canvas.create_text(200, 150, text=f"Нет данных", fill=TEXT_SECONDARY, font=FONT_GRAPH)
            return
        cx, cy, r = 120, 110, 70
        total = sum(data.values())
        ang = 0
        sorted_data = sorted(data.items(), key=lambda x: -x[1])
        for i, (k, v) in enumerate(sorted_data):
            ext = v / total * 360
            c = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
            canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=ang, extent=ext, fill=c, outline=TEXT_LIGHT, width=2)
            ang += ext

        canvas.create_text(200, 20, text=title, fill=color, font=FONT_GRAPH_TITLE)
        y_offset = 210
        for i, (k, v) in enumerate(sorted_data[:5]):
            c = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
            pct = v / total * 100
            cat_name = k.split(" ", 1)[1][:12] if " " in k else k[:12]
            canvas.create_rectangle(25 + i*75, y_offset-10, 45 + i*75, y_offset+10, fill=c, outline=TEXT_SECONDARY)
            canvas.create_text(50 + i*75, y_offset+25, text=f"{cat_name}\\n{pct:.0f}%", fill=TEXT_LIGHT, font=(FONT_SMALL[0], 7), anchor="n")
        canvas.create_text(200, 280, text=f"Всего: {total:.0f}", fill=TEXT_LIGHT, font=FONT_GRAPH)

    def draw_bar_chart(self, data, title, canvas):
        if not data:
            canvas.create_text(200, 150, text=f"Нет данных", fill=TEXT_SECONDARY, font=FONT_GRAPH)
            return
        sorted_data = sorted(data.items(), key=lambda x: -x[1])[:5]
        if not sorted_data:
            return
        mx = max(v for k, v in sorted_data)
        bar_width = 50
        spacing = 15
        start_x = 30
        base_y = 220
        max_height = 130
        for i, (k, v) in enumerate(sorted_data):
            x = start_x + i * (bar_width + spacing)
            h = (v / mx) * max_height
            y_top = base_y - h
            c = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
            canvas.create_rectangle(x, y_top, x + bar_width, base_y, fill=c, outline=TEXT_LIGHT, width=2)
            canvas.create_text(x + bar_width/2, y_top - 15, text=f"{v:.0f}", fill=c, font=FONT_GRAPH, anchor="s")
            cat_name = k.split(" ", 1)[1][:10] if " " in k else k[:10]
            canvas.create_text(x + bar_width/2, base_y + 20, text=cat_name, fill=TEXT_LIGHT, font=(FONT_SMALL[0], 7), anchor="n")
        canvas.create_text(200, 20, text=title, fill=("#ef4444" if "РАС" in title else ACCENT_GREEN), font=FONT_GRAPH_TITLE)

    def draw_line_chart(self, data, title, canvas):
        if not data:
            canvas.create_text(200, 150, text=f"Нет данных", fill=TEXT_SECONDARY, font=FONT_GRAPH)
            return
        sorted_data = sorted(data.items(), key=lambda x: -x[1])[:5]
        if not sorted_data:
            return
        mx = max(v for k, v in sorted_data)
        point_dist = 70
        start_x = 30
        base_y = 200
        max_height = 120
        line_color = ACCENT_RED if "РАС" in title else ACCENT_GREEN
        points = []
        for i, (k, v) in enumerate(sorted_data):
            x = start_x + i * point_dist
            h = (v / mx) * max_height
            y = base_y - h
            points.append((x, y, k, v))

        for i in range(len(points)-1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=line_color, width=3)

        for i, (x, y, k, v) in enumerate(points):
            c = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
            canvas.create_oval(x-6, y-6, x+6, y+6, fill=c, outline=TEXT_LIGHT, width=2)
            canvas.create_text(x, y-20, text=f"{v:.0f}", fill=c, font=FONT_GRAPH)
            cat_name = k.split(" ", 1)[1][:10] if " " in k else k[:10]
            canvas.create_text(x, base_y + 20, text=cat_name, fill=TEXT_LIGHT, font=(FONT_SMALL[0], 7), anchor="n")
        canvas.create_text(200, 20, text=title, fill=line_color, font=FONT_GRAPH_TITLE)

    def refresh_cat_box(self):
        cats = self.categories[self.main_type.get()]
        formatted = [f"{icon} {name}" for icon, name in cats]
        self.main_cat["values"] = formatted
        if formatted:
            self.main_cat.set(formatted[0])

    def add_operation(self):
        ttype = self.main_type.get()
        cats = self.categories[ttype]
        sel = self.main_cat.current()
        if sel < 0 or not cats:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return
        icon, cname = cats[sel]
        raw = self.main_sum.get().replace(",",".").strip()
        try:
            val = float(raw)
        except:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
            self.main_sum.focus_set()
            return

        amount = val if ttype=="Доход" else -abs(val)
        self.transactions.append({
            "type": ttype,
            "category": cname,
            "icon": icon,
            "amount": amount,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        self.save_data()
        self.main_sum.delete(0, tk.END)
        self.apply_filters()
        self.update_total_balance()

    def apply_filters(self):
        if self.filter_updating:
            return
        self.filter_updating = True
        try:
            show_type = self.show_filter.get()
            items = self.get_filtered_items(show_type)
            self.trtable.delete(*self.trtable.get_children())
            for tr in items:
                tag = "income" if tr["amount"] > 0 else "expense"
                self.trtable.insert("", "end", values=(tr["date"], f'{tr["icon"]} {tr["category"]}', tr["type"], f'{tr["amount"]:.2f}'), tags=(tag,))
            self.update_totals()
        finally:
            self.filter_updating = False

    def build_admin(self):
        f = self.admin_fr
        tk.Label(f, text="⚙️ Администратор", font=FONT_TITLE, bg=BG_DARK, fg=ACCENT_GREEN).pack(pady=8)

        ops_frame = tk.LabelFrame(f, text="📝 Управление операциями", font=FONT_MAIN, bg=BG_CARD, fg=ACCENT_GREEN, padx=12, pady=8)
        ops_frame.pack(fill="both", padx=12, pady=6)

        list_frame = tk.Frame(ops_frame, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True)

        tk.Label(list_frame, text="Список операций:", font=FONT_MAIN, bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        self.admin_ops_list = tk.Listbox(list_frame, font=FONT_SMALL, bg=BG_INPUT, fg=TEXT_LIGHT,
                                         selectbackground=ACCENT_GREEN, relief="flat", height=5)
        self.admin_ops_list.pack(fill="both", expand=True, pady=4)
        self.refresh_admin_ops_list()

        btns_frame = tk.Frame(ops_frame, bg=BG_CARD)
        btns_frame.pack(fill="x")

        tk.Button(btns_frame, text="✏️ Редактировать", bg=BTN_YELLOW, fg=BG_DARK, font=(FONT_MAIN[0], 10, "bold"),
                 command=self.edit_operation, relief="raised", bd=2, cursor="hand2", padx=8, pady=2).pack(side="left", padx=4, pady=4)
        tk.Button(btns_frame, text="🗑️ Удалить", bg=ACCENT_RED, fg=TEXT_LIGHT, font=(FONT_MAIN[0], 10, "bold"),
                 command=self.delete_operation, relief="raised", bd=2, cursor="hand2", padx=8, pady=2).pack(side="left", padx=4, pady=4)

        sys_frame = tk.LabelFrame(f, text="🔧 Система", font=FONT_MAIN, bg=BG_CARD, fg=ACCENT_GREEN, padx=12, pady=8)
        sys_frame.pack(fill="x", padx=12, pady=6)

        tk.Button(sys_frame, text="🗑️ Очистить все операции", bg=ACCENT_RED, fg=TEXT_LIGHT,
                 font=(FONT_MAIN[0], 10, "bold"), command=self.clear_ops, relief="raised", bd=2, cursor="hand2", width=28, pady=2).pack(pady=2)
        tk.Button(sys_frame, text="🔄 Восстановить категории", bg=BTN_YELLOW, fg=BG_DARK,
                 font=(FONT_MAIN[0], 10, "bold"), command=self.restore_categories, relief="raised", bd=2, cursor="hand2", width=28, pady=2).pack(pady=2)

    def refresh_admin_ops_list(self):
        self.admin_ops_list.delete(0, tk.END)
        for i, tr in enumerate(sorted(self.transactions, key=lambda x: x["date"], reverse=True)):
            text = f"{tr['date']} | {tr['icon']} {tr['category'][:10]} | {tr['amount']:.0f}"
            self.admin_ops_list.insert(tk.END, text)

    def edit_operation(self):
        sel = self.admin_ops_list.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите операцию")
            return
        sorted_trans = sorted(self.transactions, key=lambda x: x["date"], reverse=True)
        idx = sel[0]
        tr = sorted_trans[idx]
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование операции")
        dialog.geometry("320x180")
        dialog.config(bg=BG_DARK)

        tk.Label(dialog, text="Редактирование", font=FONT_TITLE, bg=BG_DARK, fg=ACCENT_GREEN).pack(pady=8)
        tk.Label(dialog, text="Сумма:", font=FONT_MAIN, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", padx=16, pady=(4, 0))
        sum_entry = tk.Entry(dialog, font=FONT_MAIN, bg=BG_INPUT, fg=TEXT_LIGHT, relief="flat")
        sum_entry.pack(fill="x", padx=16, pady=(0, 8))
        sum_entry.insert(0, str(abs(tr["amount"])))

        tk.Label(dialog, text="Категория:", font=FONT_MAIN, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", padx=16, pady=(4, 0))
        cat_entry = tk.Entry(dialog, font=FONT_MAIN, bg=BG_INPUT, fg=TEXT_LIGHT, relief="flat")
        cat_entry.pack(fill="x", padx=16, pady=(0, 8))
        cat_entry.insert(0, tr["category"])

        def save_edit():
            try:
                new_amount = float(sum_entry.get())
                if tr["type"] == "Расход":
                    new_amount = -abs(new_amount)
                tr["amount"] = new_amount
                tr["category"] = cat_entry.get()
                self.save_data()
                self.apply_filters()
                self.update_total_balance()
                self.refresh_admin_ops_list()
                self.update_all_views()
                dialog.destroy()
                messagebox.showinfo("Готово", "Операция обновлена!")
            except:
                messagebox.showerror("Ошибка", "Проверьте данные")

        tk.Button(dialog, text="✓ Сохранить", bg=ACCENT_GREEN, fg=BG_DARK, font=(FONT_MAIN[0], 11, "bold"),
                 command=save_edit, relief="raised", bd=2, cursor="hand2", padx=16, pady=3).pack(pady=8)

    def delete_operation(self):
        sel = self.admin_ops_list.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите операцию")
            return
        sorted_trans = sorted(self.transactions, key=lambda x: x["date"], reverse=True)
        idx = sel[0]
        tr = sorted_trans[idx]
        if messagebox.askyesno("Подтвердите", f"Удалить: {tr['icon']} {tr['category']} - {tr['amount']:.2f}?"):
            self.transactions.remove(tr)
            self.save_data()
            self.apply_filters()
            self.update_total_balance()
            self.refresh_admin_ops_list()
            self.update_all_views()
            messagebox.showinfo("Готово", "Операция удалена!")

    def clear_ops(self):
        if not messagebox.askyesno("Подтвердите", "Удалить ВСЕ операции? Категории останутся."):
            return
        self.transactions.clear()
        self.save_data()
        self.apply_filters()
        self.update_total_balance()
        self.refresh_admin_ops_list()
        self.update_all_views()
        messagebox.showinfo("Готово","Все операции удалены.")

    def restore_categories(self):
        self.categories = json.loads(json.dumps(DEFAULT_CATEGORIES, ensure_ascii=False))
        self.save_categories()
        self.update_cat_list()
        self.refresh_cat_box()
        messagebox.showinfo("Готово","Категории восстановлены.")

    def load_data(self):
        if os.path.exists(DATAFILE):
            try:
                with open(DATAFILE, "r", encoding="utf-8") as f:
                    self.transactions = json.load(f)
            except:
                self.transactions = []

    def save_data(self):
        with open(DATAFILE, "w", encoding="utf-8") as f:
            json.dump(self.transactions, f, ensure_ascii=False, indent=2)

    def load_categories(self):
        if os.path.exists(CATFILE):
            try:
                with open(CATFILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return json.loads(json.dumps(DEFAULT_CATEGORIES, ensure_ascii=False))
        return json.loads(json.dumps(DEFAULT_CATEGORIES, ensure_ascii=False))

    def save_categories(self):
        with open(CATFILE, "w", encoding="utf-8") as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)

    def on_tab_switched(self, event=None):
        tab = self.tabs.tab(self.tabs.select(), "text")
        if "Отчёт" in tab:
            self.show_report_tab()
        if "Графики" in tab:
            self.show_graph_filtered()
        if "Администратор" in tab:
            self.refresh_admin_ops_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = WalletApp(root)
    root.mainloop()
