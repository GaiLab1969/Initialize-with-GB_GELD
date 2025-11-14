# УПРАВЛЕНИЕ РАСХОДАМИ ПОДЪЕЗДА
# Версия: GaiLab v15.2
# Дата: 2025-11-14
# ФУНКЦИОНАЛ:
# 1. ✅ Система администратора: admin/admin (полный доступ)
# 2. ✅ Обычные пользователи: только вкладка Квартиры
# 3. ✅ Транзакции
# 4. ✅ Администрирование: только для admin


import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import csv

APP_VERSION = "GaiLab v15.2"
APP_BUILD_DATE = "2025-11-14"

MONTHS_RU = {
    1: "январь", 2: "февраль", 3: "март", 4: "апрель",
    5: "май", 6: "июнь", 7: "июль", 8: "август",
    9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"
}


class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._files = {
            'users': self.data_dir / "users.json",
            'categories': self.data_dir / "categories.json",
            'transactions': self.data_dir / "transactions.json",
            'apartments': self.data_dir / "apartments.json"
        }
        self._init_files()

    def _init_files(self):
        for key, filepath in self._files.items():
            if not filepath.exists():
                if key == 'apartments':
                    data = [{"id": i, "number": i + 1, "full_name": "", "phone": ""} for i in range(10)]
                elif key == 'users':
                    #  Создаём администратора с правильной ролью
                    data = [{'id': 1, 'username': 'admin', 'password': 'admin', 'role': 'admin', 'created_at': datetime.now().isoformat()}]
                else:
                    data = []
                self._save(key, data)

    def _load(self, key: str) -> Any:
        try:
            with open(self._files[key], 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save(self, key: str, data: Any) -> bool:
        try:
            with open(self._files[key], 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def get_apartment(self, apt_id: int) -> Optional[Dict]:
        apartments = self._load('apartments')
        for apt in apartments:
            if apt['id'] == apt_id:
                return apt
        return None

    def update_apartment(self, apt_id: int, full_name: str, phone: str) -> bool:
        apartments = self._load('apartments')
        for apt in apartments:
            if apt['id'] == apt_id:
                apt['full_name'] = full_name
                apt['phone'] = phone
                return self._save('apartments', apartments)
        return False

    def get_all_apartments(self) -> List[Dict]:
        return self._load('apartments')

    def add_user(self, username: str, password: str) -> bool:
        users = self._load('users')
        if any(u['username'] == username for u in users):
            return False
        users.append({'id': len(users) + 1, 'username': username, 'password': password, 'role': 'user', 'created_at': datetime.now().isoformat()})
        return self._save('users', users)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        users = self._load('users')
        return next((u for u in users if u['username'] == username and u['password'] == password), None)

    def add_category(self, name: str, amount: float) -> bool:
        categories = self._load('categories')
        now = datetime.now()
        month_name = MONTHS_RU[now.month]
        year = now.year
        full_name = f"{name} {month_name} {year}"
        if any(c['name'] == full_name for c in categories):
            return False
        categories.append({'id': len(categories) + 1, 'name': full_name, 'amount': amount, 'created_at': datetime.now().isoformat()})
        return self._save('categories', categories)

    def get_categories(self) -> List[Dict]:
        return self._load('categories')

    def delete_category(self, cat_id: int) -> bool:
        categories = self._load('categories')
        self._save('categories', [c for c in categories if c['id'] != cat_id])
        self.delete_transactions_by_category(cat_id)
        return True

    def delete_transactions_by_category(self, cat_id: int):
        transactions = self._load('transactions')
        self._save('transactions', [t for t in transactions if t['category_id'] != cat_id])

    def update_category(self, cat_id: int, name: str, amount: float) -> bool:
        categories = self._load('categories')
        for cat in categories:
            if cat['id'] == cat_id:
                cat['amount'] = amount
                return self._save('categories', categories)
        return False

    def add_transaction(self, apartment_id: int, category_id: int, amount: float, trans_type: str, user_id: int, notes: str = "") -> bool:
        transactions = self._load('transactions')
        transactions.append({'id': len(transactions) + 1, 'apartment_id': apartment_id, 'category_id': category_id, 'amount': amount, 'type': trans_type, 'user_id': user_id, 'notes': notes, 'created_at': datetime.now().isoformat()})
        return self._save('transactions', transactions)

    def get_transactions(self, apartment_id: Optional[int] = None, category_id: Optional[int] = None) -> List[Dict]:
        transactions = self._load('transactions')
        if apartment_id is not None:
            transactions = [t for t in transactions if t['apartment_id'] == apartment_id]
        if category_id is not None:
            transactions = [t for t in transactions if t['category_id'] == category_id]
        return transactions

    def delete_transaction(self, trans_id: int) -> bool:
        transactions = self._load('transactions')
        original_count = len(transactions)
        new_transactions = [t for t in transactions if t['id'] != trans_id]
        if len(new_transactions) < original_count:
            return self._save('transactions', new_transactions)
        return False

    def update_transaction(self, trans_id: int, amount: float, notes: str) -> bool:
        transactions = self._load('transactions')
        found = False
        for trans in transactions:
            if trans['id'] == trans_id:
                trans['amount'] = amount
                trans['notes'] = notes
                trans['updated_at'] = datetime.now().isoformat()
                found = True
                break
        if found:
            return self._save('transactions', transactions)
        return False

    def get_apartment_balance(self, apartment_id: int) -> Dict:
        transactions = self.get_transactions(apartment_id=apartment_id)
        valid_categories = {c['id'] for c in self.get_categories()}
        transactions = [t for t in transactions if t['category_id'] in valid_categories]
        total_paid = sum(t['amount'] for t in transactions if t['type'] == 'payment')
        total_debts = sum(t['amount'] for t in transactions if t['type'] == 'debt')
        balance = total_paid - total_debts
        return {'apartment_id': apartment_id, 'paid': total_paid, 'debts': total_debts, 'balance': balance}

    def get_categories_with_distribution(self, apartment_id: int) -> List[Dict]:
        transactions = self.get_transactions(apartment_id=apartment_id)
        valid_categories = {c['id'] for c in self.get_categories()}
        transactions = [t for t in transactions if t['category_id'] in valid_categories]
        categories = self.get_categories()
        by_category = {}
        for trans in transactions:
            cat_id = trans['category_id']
            if cat_id not in by_category:
                by_category[cat_id] = []
            by_category[cat_id].append(trans)
        categories_info = []
        for cat in categories:
            cat_id = cat['id']
            cat_transactions = by_category.get(cat_id, [])
            cat_paid = sum(t['amount'] for t in cat_transactions if t['type'] == 'payment')
            cat_debts = sum(t['amount'] for t in cat_transactions if t['type'] == 'debt')
            cat_balance_before = cat_paid - cat_debts
            categories_info.append({'id': cat_id, 'name': cat['name'], 'paid': cat_paid, 'debts': cat_debts, 'balance_before': cat_balance_before, 'balance_after': cat_balance_before})
        total_surplus = sum(cat['balance_before'] for cat in categories_info if cat['balance_before'] > 0)
        if total_surplus > 0:
            for i in range(len(categories_info) - 1, -1, -1):
                if total_surplus <= 0:
                    break
                cat_info = categories_info[i]
                if cat_info['balance_before'] < 0:
                    debt_amount = abs(cat_info['balance_before'])
                    to_use = min(debt_amount, total_surplus)
                    cat_info['balance_after'] = cat_info['balance_before'] + to_use
                    total_surplus -= to_use
        return categories_info

    def get_all_balances(self) -> List[Dict]:
        apartments = self._load('apartments')
        return [self.get_apartment_balance(apt['id']) for apt in apartments]


class LoginWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user = None
        self.title("Управление расходами подъезда - Вход")
        
        width, height = 500, 450
        self.geometry(f"{width}x{height}")
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.resizable(False, False)

        title_frame = tk.Frame(self, bg='#0078D4', height=80)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text=f"💼 Вход в систему", font=("Arial", 16, "bold"), bg='#0078D4', fg='white')
        title_label.pack(pady=15)
        
        version_label = tk.Label(title_frame, text=f"Версия: {APP_VERSION}", font=("Arial", 8), bg='#0078D4', fg='#FFD700')
        version_label.pack()

        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)

        tk.Label(main_frame, text="Имя пользователя:", bg='white', font=("Arial", 11, "bold"), fg='#333').pack(anchor='w', pady=(0, 8))
        self.username_entry = tk.Entry(main_frame, font=("Arial", 11), width=35, relief=tk.SOLID, bd=1)
        self.username_entry.pack(fill=tk.X, ipady=8, pady=(0, 15))

        tk.Label(main_frame, text="Пароль:", bg='white', font=("Arial", 11, "bold"), fg='#333').pack(anchor='w', pady=(0, 8))
        self.password_entry = tk.Entry(main_frame, font=("Arial", 11), width=35, relief=tk.SOLID, bd=1, show='•')
        self.password_entry.pack(fill=tk.X, ipady=8, pady=(0, 20))

        info_frame = tk.Frame(main_frame, bg='#FFF9E6', relief=tk.SOLID, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_label = tk.Label(info_frame, text="💡 Демо доступ\n👑 Admin: admin / admin\n👤 Или создайте новый аккаунт", bg='#FFF9E6', font=("Arial", 9), fg='#666', justify=tk.LEFT)
        info_label.pack(padx=12, pady=10)

        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        login_btn = tk.Button(button_frame, text="🔓 ВХОД", command=self.login, bg='#0078D4', fg='white', font=("Arial", 11, "bold"), height=2, cursor="hand2", activebackground='#005A9E', activeforeground='white', relief=tk.RAISED, bd=2)
        login_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.BOTH, expand=True)

        register_btn = tk.Button(button_frame, text="✏️ РЕГИСТРАЦИЯ", command=self.register, bg='#107C10', fg='white', font=("Arial", 11, "bold"), height=2, cursor="hand2", activebackground='#055C0E', activeforeground='white', relief=tk.RAISED, bd=2)
        register_btn.pack(side=tk.LEFT, padx=(5, 0), fill=tk.BOTH, expand=True)

        self.username_entry.focus()
        
        self.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        user = self.db.authenticate(username, password)
        if user:
            self.user = user
            self.destroy()
        else:
            messagebox.showerror("Ошибка входа", "Неверные учетные данные!")
            self.password_entry.delete(0, tk.END)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
        if len(username) < 3:
            messagebox.showwarning("Ошибка", "Имя пользователя должно быть минимум 3 символа!")
            return
        if len(password) < 3:
            messagebox.showwarning("Ошибка", "Пароль должен быть минимум 3 символа!")
            return
        if self.db.add_user(username, password):
            messagebox.showinfo("✅ Успех", f"Пользователь '{username}' создан!\n\nТеперь вы можете войти с новыми учетными данными.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Ошибка", f"Пользователь '{username}' уже существует!\n\nВыберите другое имя.")


class MainWindow(tk.Tk):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        # Правильная проверка роли
        self.is_admin = user.get('role') == 'admin'
        
        self.selected_category = None
        self.selected_item_id = None
        self.transaction_mapping = {}
        self.selected_apartment_id = None
        self.title(f"Управление расходами подъезда v{APP_VERSION} - {user['username']}")
        self.geometry("1400x750")
        self.resizable(True, True)
        self.state('normal')
        
        self.create_top_panel()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        self.apartments_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.apartments_tab, text="🏠 Квартиры")
        self.create_apartments_tab()
        
        # Проверяем is_admin правильно
        if self.is_admin:
            self.transactions_tab = tk.Frame(self.notebook, bg='white')
            self.notebook.add(self.transactions_tab, text="💰 Транзакции")
            self.create_transactions_tab()
            
            self.admin_tab = tk.Frame(self.notebook, bg='white')
            self.notebook.add(self.admin_tab, text="⚙️ Администрирование")
            self.create_admin_tab()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.fix_existing_categories()
        self.update_category_combo()
        self.after(100, self.refresh_apartments)

    def fix_existing_categories(self):
        categories = self.db.get_categories()
        now = datetime.now()
        month_name = MONTHS_RU[now.month]
        year = now.year
        needs_update = False
        for cat in categories:
            if not any(month in cat['name'] for month in MONTHS_RU.values()):
                cat['name'] = f"{cat['name']} {month_name} {year}"
                needs_update = True
        if needs_update:
            self.db._save('categories', categories)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        if "Квартиры" in tab_text:
            self.refresh_apartments()
        elif self.is_admin and "Администрирование" in tab_text:
            self.refresh_categories()
            self.refresh_apartments_list()
        elif self.is_admin and "Транзакции" in tab_text:
            self.update_category_combo()
            self.refresh_transactions_tree()

    def create_top_panel(self):
        top_frame = tk.Frame(self, bg='#0078D4', height=50)
        top_frame.pack(fill=tk.X)
        title = tk.Label(top_frame, text="💼 Управление расходами подъезда", font=("Arial", 14, "bold"), bg='#0078D4', fg='white')
        title.pack(side=tk.LEFT, padx=15, pady=10)
        version_label = tk.Label(top_frame, text=f"Версия: {APP_VERSION}", font=("Arial", 8), bg='#0078D4', fg='#FFD700')
        version_label.pack(side=tk.LEFT, padx=10, pady=10)
        role_text = "👑 АДМИНИСТРАТОР" if self.is_admin else "👤 Обычный пользователь"
        user_label = tk.Label(top_frame, text=f"{role_text} - {self.user['username']}", font=("Arial", 10, "bold"), bg='#0078D4', fg='white')
        user_label.pack(side=tk.RIGHT, padx=15, pady=10)

    def create_apartments_tab(self):
        btn_frame = tk.Frame(self.apartments_tab, bg='white')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        export_btn = tk.Button(btn_frame, text="💾 Экспорт CSV", command=self.export_report, bg='#107C10', fg='white', font=("Arial", 10, "bold"))
        export_btn.pack(side=tk.LEFT, padx=5)
        refresh_btn = tk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_apartments, bg='#0078D4', fg='white', font=("Arial", 10, "bold"))
        refresh_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(self.apartments_tab, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.apartments_tree = ttk.Treeview(tree_frame, columns=('Баланс', 'Платежи', 'Долги', 'Статус', 'ФИО', 'Телефон'), height=20, yscrollcommand=scrollbar.set, xscrollcommand=hsb.set)
        scrollbar.config(command=self.apartments_tree.yview)
        hsb.config(command=self.apartments_tree.xview)

        self.apartments_tree.column('#0', width=200)
        self.apartments_tree.column('Баланс', anchor=tk.CENTER, width=100)
        self.apartments_tree.column('Платежи', anchor=tk.CENTER, width=100)
        self.apartments_tree.column('Долги', anchor=tk.CENTER, width=100)
        self.apartments_tree.column('Статус', anchor=tk.CENTER, width=100)
        self.apartments_tree.column('ФИО', anchor=tk.W, width=150)
        self.apartments_tree.column('Телефон', anchor=tk.CENTER, width=100)

        self.apartments_tree.heading('#0', text='Квартира', anchor=tk.W)
        self.apartments_tree.heading('Баланс', text='Баланс', anchor=tk.CENTER)
        self.apartments_tree.heading('Платежи', text='Платежи', anchor=tk.CENTER)
        self.apartments_tree.heading('Долги', text='Долги', anchor=tk.CENTER)
        self.apartments_tree.heading('Статус', text='Статус', anchor=tk.CENTER)
        self.apartments_tree.heading('ФИО', text='👤 ФИО', anchor=tk.W)
        self.apartments_tree.heading('Телефон', text='📱 Тел', anchor=tk.CENTER)

        self.apartments_tree.pack(fill=tk.BOTH, expand=True)
        
        self.apartments_tree.tag_configure('apartment_ok', font=("Arial", 9, "bold"), foreground='#107C10', background='#e8f5e9')
        self.apartments_tree.tag_configure('apartment_debt', font=("Arial", 9, "bold"), foreground='#C91130', background='#ffebee')
        self.apartments_tree.tag_configure('category', font=("Arial", 9), foreground='#0078D4', background='#f5f5f5')
        self.apartments_tree.tag_configure('payment', foreground='#107C10', font=("Arial", 8))
        self.apartments_tree.tag_configure('debt', foreground='#C91130', font=("Arial", 8))
        self.apartments_tree.tag_configure('paid', foreground='#107C10', font=("Arial", 8, "bold"))
        self.apartments_tree.tag_configure('unpaid', foreground='#FFB900', font=("Arial", 8, "bold"))
        self.apartments_tree.tag_configure('separator', background='#d0d0d0', foreground='#999999')

    def refresh_apartments(self):
        for item in self.apartments_tree.get_children():
            self.apartments_tree.delete(item)
        
        apartments = self.db.get_all_apartments()
        
        for apt_index, apt in enumerate(apartments):
            apt_id = apt['id']
            balance = self.db.get_apartment_balance(apt_id)
            apt_num = apt_id + 1
            
            if apt_index > 0:
                separator_line = "─" * 100
                self.apartments_tree.insert('', 'end',
                    text=separator_line,
                    values=('─' * 15, '─' * 15, '─' * 15, '─' * 15, '─' * 25, '─' * 15),
                    tags=('separator',))
            
            if balance['debts'] == 0 or balance['balance'] >= 0:
                apartment_tag = 'apartment_ok'
                status_text = "✅ ОК"
            else:
                apartment_tag = 'apartment_debt'
                status_text = "❌ ДОЛЖНА"
            
            balance_text = f"+{balance['balance']:.2f}" if balance['balance'] > 0 else f"{balance['balance']:.2f}"
            full_name = apt.get('full_name', '')[:30]
            phone = apt.get('phone', '')[:20]
            
            apt_parent = self.apartments_tree.insert('', 'end',
                text=f"Кв. {apt_num}",
                values=(balance_text, f"{balance['paid']:.2f}", f"{balance['debts']:.2f}", status_text, full_name, phone),
                tags=(apartment_tag,))
            
            self.apartments_tree.item(apt_parent, open=True)
            
            transactions = self.db.get_transactions(apartment_id=apt_id)
            valid_categories = {c['id'] for c in self.db.get_categories()}
            transactions = [t for t in transactions if t['category_id'] in valid_categories]
            
            if transactions:
                by_category = {}
                for trans in transactions:
                    cat_id = trans['category_id']
                    if cat_id not in by_category:
                        by_category[cat_id] = []
                    by_category[cat_id].append(trans)
                
                categories_info = self.db.get_categories_with_distribution(apt_id)
                
                for cat_info in categories_info:
                    cat_id = cat_info['id']
                    cat_name = cat_info['name']
                    balance_after = cat_info['balance_after']
                    
                    if balance_after >= 0:
                        status_text = "✅ Оплачено"
                        cat_tag = 'paid'
                    else:
                        status_text = "⚠️ Имеется долг"
                        cat_tag = 'unpaid'
                    
                    cat_display_name = f"{cat_name} | {status_text}"
                    
                    cat_parent = self.apartments_tree.insert(apt_parent, 'end',
                        text=cat_display_name,
                        values=(f"{balance_after:.2f}", "", "", "", "", ""),
                        tags=(cat_tag, 'category'))
                    
                    self.apartments_tree.item(cat_parent, open=True)
                    
                    if cat_id in by_category:
                        for trans in by_category[cat_id]:
                            trans_type = "💰 Платеж" if trans['type'] == 'payment' else "💸 Долг"
                            tag = 'payment' if trans['type'] == 'payment' else 'debt'
                            date = trans['created_at'].split('T')[0]
                            
                            self.apartments_tree.insert(cat_parent, 'end',
                                text=f" {trans_type} ({date})",
                                values=(f"{trans['amount']:.2f}", "", "", "", "", ""),
                                tags=(tag,))
        
        self.apartments_tree.update()

    def export_report(self):
        try:
            filename = f"отчет_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            balances = self.db.get_all_balances()
            apartments = self.db.get_all_apartments()
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['Квартира', 'ФИО', 'Телефон', 'Платежи (руб.)', 'Долги (руб.)', 'Остаток (руб.)', 'Статус'])
                for bal in balances:
                    apt_num = bal['apartment_id'] + 1
                    apt = self.db.get_apartment(bal['apartment_id'])
                    status = 'ОК' if bal['balance'] >= 0 else 'ДОЛЖНА'
                    writer.writerow([f'Кв. {apt_num}', apt.get('full_name', '') if apt else '', apt.get('phone', '') if apt else '', f'{bal["paid"]:.2f}', f'{bal["debts"]:.2f}', f'{bal["balance"]:.2f}', status])
            messagebox.showinfo("✅ Успех", f"Отчет успешно сохранен!\n📁 Файл: {filename}")
        except Exception as e:
            messagebox.showerror("❌ Ошибка", f"Ошибка при сохранении: {e}")

    def create_admin_tab(self):
        main_container = tk.Frame(self.admin_tab, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = tk.LabelFrame(main_container, text="📦 Управление категориями", font=("Arial", 11, "bold"), bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        form_title = tk.Label(left_frame, text="Добавить категорию", font=("Arial", 10, "bold"), bg='white')
        form_title.pack(anchor='w', pady=10, padx=10)
        
        tk.Label(left_frame, text="Название:", bg='white', font=("Arial", 9)).pack(anchor='w', padx=10)
        self.cat_name_entry = tk.Entry(left_frame, font=("Arial", 9), width=25)
        self.cat_name_entry.pack(pady=3, padx=10)
        
        now = datetime.now()
        month_name = MONTHS_RU[now.month]
        year = now.year
        hint_label = tk.Label(left_frame, text=f"💡 Автоматически добавится: {month_name} {year}", bg='white', font=("Arial", 8, "italic"), fg='#666')
        hint_label.pack(anchor='w', padx=10, pady=2)
        
        tk.Label(left_frame, text="Сумма (руб.) на все квартиры:", bg='white', font=("Arial", 9)).pack(anchor='w', pady=(5, 0), padx=10)
        self.cat_amount_entry = tk.Entry(left_frame, font=("Arial", 9), width=25)
        self.cat_amount_entry.pack(pady=3, padx=10)
        
        btn_frame = tk.Frame(left_frame, bg='white')
        btn_frame.pack(pady=10, padx=10)
        add_btn = tk.Button(btn_frame, text="➕ Добавить", command=self.add_category, bg='#107C10', fg='white', font=("Arial", 10, "bold"), width=15, height=2, padx=5, pady=5)
        add_btn.pack(pady=3)
        
        table_title = tk.Label(left_frame, text="Список категорий", font=("Arial", 10, "bold"), bg='white')
        table_title.pack(anchor='w', pady=5, padx=10)
        
        control_frame = tk.Frame(left_frame, bg='white')
        control_frame.pack(fill=tk.X, pady=5, padx=10)
        edit_btn = tk.Button(control_frame, text="✏️ Редактировать", command=self.edit_category_window, bg='#FFB900', fg='black', font=("Arial", 10, "bold"), width=15, height=2, padx=5, pady=5)
        edit_btn.pack(side=tk.LEFT, padx=3, pady=3, fill=tk.BOTH, expand=True)
        delete_btn = tk.Button(control_frame, text="🗑️ Удалить", command=self.delete_category, bg='#C91130', fg='white', font=("Arial", 10, "bold"), width=15, height=2, padx=5, pady=5)
        delete_btn.pack(side=tk.LEFT, padx=3, pady=3, fill=tk.BOTH, expand=True)
        
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.categories_tree = ttk.Treeview(tree_frame, columns=('ID', 'Название', 'Сумма'), height=12, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.categories_tree.yview)
        
        self.categories_tree.column('#0', width=0, stretch=tk.NO)
        self.categories_tree.column('ID', anchor=tk.CENTER, width=35)
        self.categories_tree.column('Название', anchor=tk.W, width=120)
        self.categories_tree.column('Сумма', anchor=tk.CENTER, width=80)
        
        self.categories_tree.heading('#0', text='', anchor=tk.W)
        self.categories_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.categories_tree.heading('Название', text='Название', anchor=tk.W)
        self.categories_tree.heading('Сумма', text='Сумма', anchor=tk.CENTER)
        
        self.categories_tree.pack(fill=tk.BOTH, expand=True)
        self.categories_tree.bind('<<TreeviewSelect>>', self.on_category_select)
        
        right_frame = tk.LabelFrame(main_container, text="🏠 Управление квартирами", font=("Arial", 11, "bold"), bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        form_title2 = tk.Label(right_frame, text="Данные квартиры", font=("Arial", 10, "bold"), bg='white')
        form_title2.pack(anchor='w', pady=10, padx=10)
        
        tk.Label(right_frame, text="Выберите квартиру:", bg='white', font=("Arial", 9)).pack(anchor='w', padx=10)
        self.apt_select_var = tk.StringVar()
        self.apt_select_combo = ttk.Combobox(right_frame, textvariable=self.apt_select_var, values=[f"Кв. {i}" for i in range(1, 11)], width=15, state='readonly')
        self.apt_select_combo.pack(pady=3, padx=10)
        self.apt_select_combo.bind('<<ComboboxSelected>>', self.on_apartment_select)
        
        tk.Label(right_frame, text="ФИО владельца:", bg='white', font=("Arial", 9)).pack(anchor='w', pady=(10, 0), padx=10)
        self.apt_full_name_entry = tk.Entry(right_frame, font=("Arial", 9), width=25)
        self.apt_full_name_entry.pack(pady=3, padx=10)
        
        tk.Label(right_frame, text="Номер телефона:", bg='white', font=("Arial", 9)).pack(anchor='w', pady=(5, 0), padx=10)
        self.apt_phone_entry = tk.Entry(right_frame, font=("Arial", 9), width=25)
        self.apt_phone_entry.pack(pady=3, padx=10)
        
        btn_frame2 = tk.Frame(right_frame, bg='white')
        btn_frame2.pack(pady=10, padx=10)
        save_apt_btn = tk.Button(btn_frame2, text="💾 Сохранить", command=self.save_apartment_data, bg='#107C10', fg='white', font=("Arial", 9, "bold"), width=15)
        save_apt_btn.pack(pady=3)
        
        table_title2 = tk.Label(right_frame, text="Список квартир", font=("Arial", 10, "bold"), bg='white')
        table_title2.pack(anchor='w', pady=5, padx=10)
        
        tree_frame2 = tk.Frame(right_frame)
        tree_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar2 = ttk.Scrollbar(tree_frame2)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.apartments_info_tree = ttk.Treeview(tree_frame2, columns=('№', 'ФИО', 'Телефон'), height=12, yscrollcommand=scrollbar2.set)
        scrollbar2.config(command=self.apartments_info_tree.yview)
        
        self.apartments_info_tree.column('#0', width=0, stretch=tk.NO)
        self.apartments_info_tree.column('№', anchor=tk.CENTER, width=35)
        self.apartments_info_tree.column('ФИО', anchor=tk.W, width=120)
        self.apartments_info_tree.column('Телефон', anchor=tk.CENTER, width=100)
        
        self.apartments_info_tree.heading('#0', text='', anchor=tk.W)
        self.apartments_info_tree.heading('№', text='№', anchor=tk.CENTER)
        self.apartments_info_tree.heading('ФИО', text='ФИО владельца', anchor=tk.W)
        self.apartments_info_tree.heading('Телефон', text='Телефон', anchor=tk.CENTER)
        
        self.apartments_info_tree.pack(fill=tk.BOTH, expand=True)
        self.apartments_info_tree.bind('<<TreeviewSelect>>', self.on_apartment_info_select)

    def on_category_select(self, event):
        selected = self.categories_tree.selection()
        if selected:
            item = selected[0]
            values = self.categories_tree.item(item)['values']
            self.selected_category = {'id': int(values[0]), 'name': values[1], 'amount': float(values[2])}

    def edit_category_window(self):
        if not self.selected_category:
            messagebox.showwarning("Ошибка", "Выберите категорию для редактирования!")
            return
        
        edit_window = tk.Toplevel(self)
        edit_window.title("Редактировать категорию")
        edit_window.geometry("650x500")
        edit_window.resizable(False, False)
        edit_window.grab_set()
        
        header = tk.Frame(edit_window, bg='#0078D4', height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title_label = tk.Label(header, text=f"Редактирование: {self.selected_category['name']}", font=("Arial", 14, "bold"), bg='#0078D4', fg='white')
        title_label.pack(pady=20)
        
        content_frame = tk.Frame(edit_window, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Название категории (не редактируется):", bg='white', font=("Arial", 11, "bold"), fg='#333').pack(anchor='w', pady=(0, 8))
        
        name_entry = tk.Entry(content_frame, font=("Arial", 11), width=60, relief=tk.SOLID, bd=1, bg="#E8E8E8", fg="#666666")
        name_entry.insert(0, self.selected_category['name'])
        name_entry.config(state="readonly")
        name_entry.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        tk.Label(content_frame, text="Новая сумма на все квартиры (руб.):", bg='white', font=("Arial", 11, "bold"), fg='#333').pack(anchor='w', pady=(0, 8))
        
        amount_entry = tk.Entry(content_frame, font=("Arial", 11), width=60, relief=tk.SOLID, bd=1)
        amount_entry.insert(0, str(self.selected_category['amount']))
        amount_entry.pack(fill=tk.X, pady=(0, 20), ipady=10)
        amount_entry.focus()
        
        info_frame = tk.Frame(content_frame, bg='#FFF9E6', relief=tk.SOLID, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 25))
        
        info_text = tk.Label(info_frame, text=f"💡 На каждую квартиру: {float(self.selected_category['amount']) / 10:.2f} руб.\n\n⚠️ ВАЖНО: При изменении суммы категории,\nрассчёты обновятся для ВСЕХ квартир!\nВкладки 'Квартиры' и 'Транзакции' обновятся автоматически.", bg='#FFF9E6', font=("Arial", 9, "italic"), fg='#333', justify=tk.LEFT, wraplength=500)
        info_text.pack(padx=10, pady=10)
        
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_changes():
            try:
                new_amount_str = amount_entry.get().strip()
                if not new_amount_str:
                    messagebox.showwarning("❌ Ошибка", "Введите сумму категории!")
                    return
                
                try:
                    new_amount = float(new_amount_str)
                except ValueError:
                    messagebox.showerror("❌ Ошибка", "Сумма должна быть числом!")
                    return
                
                if new_amount <= 0:
                    messagebox.showwarning("❌ Ошибка", "Сумма должна быть больше 0!")
                    return
                
                cat_id = self.selected_category['id']
                
                if self.db.update_category(cat_id, self.selected_category['name'], new_amount):
                    transactions = self.db.get_transactions(category_id=cat_id)
                    
                    for trans in transactions:
                        if trans['type'] == 'debt' and 'Начисление:' in trans.get('notes', ''):
                            new_trans_amount = new_amount / 10
                            self.db.update_transaction(trans['id'], new_trans_amount, trans.get('notes', ''))
                    
                    messagebox.showinfo("✅ УСПЕШНО!",
                        f"Категория обновлена!\n\nНазвание: {self.selected_category['name']}\nСумма: {new_amount:.2f} руб.\nНа кв-ру: {new_amount/10:.2f} руб.\n\n✓ Платежи сохранены!\n✓ Долги пересчитаны!")
                    
                    self.refresh_categories()
                    self.refresh_apartments()
                    self.refresh_transactions_tree()
                    self.update_category_combo()
                    self.selected_category = None
                    
                    edit_window.destroy()
                else:
                    messagebox.showerror("❌ Ошибка", "Не удалось обновить категорию!")
            except Exception as e:
                messagebox.showerror("❌ ОШИБКА", f"Ошибка при сохранении:\n{str(e)}")
        
        save_btn = tk.Button(button_frame, text="💾 СОХРАНИТЬ ИЗМЕНЕНИЯ", command=save_changes, bg='#107C10', fg='white', font=("Arial", 12, "bold"), padx=20, pady=12, cursor="hand2", activebackground='#0B6107', activeforeground='white', relief=tk.RAISED, bd=2)
        save_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        cancel_btn = tk.Button(button_frame, text="❌ ОТМЕНА", command=edit_window.destroy, bg='#C91130', fg='white', font=("Arial", 12, "bold"), padx=20, pady=12, cursor="hand2", activebackground='#A00A25', activeforeground='white', relief=tk.RAISED, bd=2)
        cancel_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def refresh_categories(self):
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        categories = self.db.get_categories()
        for cat in categories:
            self.categories_tree.insert('', 'end', values=(cat['id'], cat['name'], f"{cat['amount']:.2f}"))

    def delete_category(self):
        if not self.selected_category:
            messagebox.showwarning("Ошибка", "Выберите категорию для удаления!")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить категорию '{self.selected_category['name']}' и все её транзакции?"):
            self.db.delete_category(self.selected_category['id'])
            self.refresh_categories()
            self.refresh_apartments()
            self.refresh_transactions_tree()
            self.update_category_combo()
            self.selected_category = None
            messagebox.showinfo("✅ Успех", "Категория и все её данные удалены!")

    def on_apartment_select(self, event=None):
        apt_num_str = self.apt_select_var.get()
        if apt_num_str:
            apt_num = int(apt_num_str.replace("Кв. ", ""))
            apt = self.db.get_apartment(apt_num - 1)
            if apt:
                self.apt_full_name_entry.delete(0, tk.END)
                self.apt_full_name_entry.insert(0, apt.get('full_name', ''))
                self.apt_phone_entry.delete(0, tk.END)
                self.apt_phone_entry.insert(0, apt.get('phone', ''))
                self.selected_apartment_id = apt_num - 1

    def on_apartment_info_select(self, event):
        selected = self.apartments_info_tree.selection()
        if selected:
            item = selected[0]
            values = self.apartments_info_tree.item(item)['values']
            apt_num = int(values[0])
            self.apt_select_combo.set(f"Кв. {apt_num}")
            self.on_apartment_select()

    def save_apartment_data(self):
        if self.selected_apartment_id is None:
            messagebox.showwarning("Ошибка", "Выберите квартиру!")
            return
        full_name = self.apt_full_name_entry.get()
        phone = self.apt_phone_entry.get()
        if self.db.update_apartment(self.selected_apartment_id, full_name, phone):
            messagebox.showinfo("✅ Успех", "Данные квартиры сохранены!")
            self.refresh_apartments_list()
            self.refresh_apartments()
        else:
            messagebox.showerror("❌ Ошибка", "Не удалось сохранить данные!")

    def refresh_apartments_list(self):
        for item in self.apartments_info_tree.get_children():
            self.apartments_info_tree.delete(item)
        apartments = self.db.get_all_apartments()
        for apt in apartments:
            apt_num = apt['number']
            full_name = apt.get('full_name', '')
            phone = apt.get('phone', '')
            self.apartments_info_tree.insert('', 'end', values=(apt_num, full_name, phone))

    def add_category(self):
        name = self.cat_name_entry.get()
        try:
            amount = float(self.cat_amount_entry.get())
            if not name:
                messagebox.showwarning("Ошибка", "Введите название!")
                return
            if self.db.add_category(name, amount):
                amount_per_apt = amount / 10
                new_category = self.db.get_categories()[-1]
                for apt_id in range(10):
                    self.db.add_transaction(apartment_id=apt_id, category_id=new_category['id'], amount=amount_per_apt, trans_type='debt', user_id=self.user['id'], notes=f"Начисление: {new_category['name']}")
                messagebox.showinfo("✅ Успех", f"Категория '{new_category['name']}' добавлена!\n\nОбщая сумма: {amount:.2f} руб.\nНа каждую квартиру: {amount_per_apt:.2f} руб.")
                self.cat_name_entry.delete(0, tk.END)
                self.cat_amount_entry.delete(0, tk.END)
                self.refresh_categories()
                self.refresh_apartments()
                self.refresh_transactions_tree()
                self.update_category_combo()
            else:
                messagebox.showerror("❌ Ошибка", "Категория уже существует!")
        except ValueError:
            messagebox.showerror("❌ Ошибка", "Сумма должна быть числом!")

    def update_category_combo(self):
        categories = self.db.get_categories()
        cat_list = [f"{c['id']}: {c['name']}" for c in categories]
        if hasattr(self, 'cat_combo'):
            self.cat_combo['values'] = cat_list

    def create_transactions_tab(self):
        btn_frame = tk.Frame(self.transactions_tab, bg='white')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        left_btn_frame = tk.Frame(btn_frame, bg='white')
        left_btn_frame.pack(side=tk.LEFT, fill=tk.X)
        
        edit_btn = tk.Button(left_btn_frame, text="✏️ Редактировать платеж", command=self.edit_transaction, bg='#FFB900', fg='black', font=("Arial", 10))
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(left_btn_frame, text="🗑️ Удалить платеж", command=self.delete_transaction_btn, bg='#C91130', fg='white', font=("Arial", 10))
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        form_frame = tk.Frame(self.transactions_tab, bg='#f0f0f0')
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        form_title = tk.Label(form_frame, text="Добавить новую транзакцию", font=("Arial", 11, "bold"), bg='#f0f0f0')
        form_title.pack(anchor='w', pady=5)
        
        input_frame = tk.Frame(form_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(input_frame, text="Кв:", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.trans_apt_var = tk.StringVar()
        apt_combo = ttk.Combobox(input_frame, textvariable=self.trans_apt_var, values=[str(i) for i in range(1, 11)], width=5, state='readonly')
        apt_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(input_frame, text="Категория:", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.trans_cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(input_frame, textvariable=self.trans_cat_var, width=50, state='readonly')
        self.cat_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(input_frame, text="Сумма:", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.trans_amount_entry = tk.Entry(input_frame, font=("Arial", 9), width=10)
        self.trans_amount_entry.pack(side=tk.LEFT, padx=5)
        
        payment_btn = tk.Button(input_frame, text="💰 Платеж", command=lambda: self.save_transaction('payment'), bg='#107C10', fg='white', font=("Arial", 9))
        payment_btn.pack(side=tk.LEFT, padx=3)
        
        tree_frame = tk.Frame(self.transactions_tab, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.transactions_tree = ttk.Treeview(tree_frame, columns=('Категория', 'Тип', 'Сумма', 'Дата', 'Баланс'), height=18, yscrollcommand=scrollbar.set, xscrollcommand=hsb.set)
        scrollbar.config(command=self.transactions_tree.yview)
        hsb.config(command=self.transactions_tree.xview)
        
        self.transactions_tree.column('#0', width=200)
        self.transactions_tree.column('Категория', anchor=tk.W, width=250)
        self.transactions_tree.column('Тип', anchor=tk.CENTER, width=120)
        self.transactions_tree.column('Сумма', anchor=tk.CENTER, width=120)
        self.transactions_tree.column('Дата', anchor=tk.CENTER, width=120)
        self.transactions_tree.column('Баланс', anchor=tk.CENTER, width=120)
        
        self.transactions_tree.heading('#0', text='Квартира', anchor=tk.W)
        self.transactions_tree.heading('Категория', text='Категория', anchor=tk.W)
        self.transactions_tree.heading('Тип', text='Тип', anchor=tk.CENTER)
        self.transactions_tree.heading('Сумма', text='Сумма', anchor=tk.CENTER)
        self.transactions_tree.heading('Дата', text='Дата', anchor=tk.CENTER)
        self.transactions_tree.heading('Баланс', text='Баланс', anchor=tk.CENTER)
        
        self.transactions_tree.pack(fill=tk.BOTH, expand=True)
        self.transactions_tree.bind('<<TreeviewSelect>>', self.on_transaction_select)
        
        self.transactions_tree.tag_configure('payment', foreground='#107C10', font=("Arial", 9, "bold"))
        self.transactions_tree.tag_configure('debt', foreground='#C91130', font=("Arial", 9, "bold"))
        self.transactions_tree.tag_configure('apartment_ok', font=("Arial", 10, "bold"), foreground='#107C10', background='#e8f5e9')
        self.transactions_tree.tag_configure('apartment_debt', foreground='#C91130', font=("Arial", 10, "bold"), background='#ffebee')
        self.transactions_tree.tag_configure('paid', foreground='#107C10', font=("Arial", 9, "bold"))
        self.transactions_tree.tag_configure('unpaid', foreground='#FFB900', font=("Arial", 9, "bold"))
        self.transactions_tree.tag_configure('separator', background='#d0d0d0', foreground='#999999')

    def refresh_transactions_tree(self):
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
        self.transaction_mapping.clear()
        self.selected_item_id = None
        
        for apt_index, apt_id in enumerate(range(10)):
            all_transactions = self.db.get_transactions(apartment_id=apt_id)
            balance = self.db.get_apartment_balance(apt_id)
            apt_num = apt_id + 1
            
            if apt_index > 0:
                separator_line = "─" * 80
                self.transactions_tree.insert('', 'end',
                    text=separator_line,
                    values=('─' * 20, '─' * 15, '─' * 15, '─' * 15, '─' * 15),
                    tags=('separator',))
            
            if balance['debts'] == 0 or balance['balance'] >= 0:
                apartment_tag = 'apartment_ok'
            else:
                apartment_tag = 'apartment_debt'
            
            balance_text = f"+{balance['balance']:.2f}" if balance['balance'] > 0 else f"{balance['balance']:.2f}"
            
            apt_parent = self.transactions_tree.insert('', 'end',
                text=f"Кв. {apt_num}",
                values=("", "", "", "", balance_text),
                tags=(apartment_tag,))
            
            self.transactions_tree.item(apt_parent, open=True)
            
            if all_transactions:
                by_category = {}
                for trans in all_transactions:
                    cat_id = trans['category_id']
                    if cat_id not in by_category:
                        by_category[cat_id] = []
                    by_category[cat_id].append(trans)
                
                categories = self.db.get_categories()
                for cat in categories:
                    cat_id = cat['id']
                    cat_name = cat['name']
                    if cat_id in by_category:
                        cat_transactions = by_category[cat_id]
                        cat_paid = sum(t['amount'] for t in cat_transactions if t['type'] == 'payment')
                        cat_debts = sum(t['amount'] for t in cat_transactions if t['type'] == 'debt')
                        balance_after = cat_paid - cat_debts
                        
                        if balance_after >= 0:
                            status_text = "✅ Оплачено"
                            cat_tag = 'paid'
                        else:
                            status_text = "⚠️ Имеется долг"
                            cat_tag = 'unpaid'
                        
                        cat_parent = self.transactions_tree.insert(apt_parent, 'end',
                            text="",
                            values=(f"{cat_name} | {status_text}", "", "", "", ""),
                            tags=(cat_tag,))
                        
                        self.transactions_tree.item(cat_parent, open=True)
                        
                        for trans in cat_transactions:
                            trans_type = "💰 Платеж" if trans['type'] == 'payment' else "💸 Долг"
                            tag = 'payment' if trans['type'] == 'payment' else 'debt'
                            date = trans.get('created_at', '???').split('T')[0] if 'created_at' in trans else '???'
                            
                            item = self.transactions_tree.insert(cat_parent, 'end',
                                text="",
                                values=(f"{cat_name}",
                                        trans_type,
                                        f"{trans['amount']:.2f}",
                                        date,
                                        ""),
                                tags=(tag,))
                            
                            self.transaction_mapping[item] = {
                                'type': 'transaction',
                                'trans_id': trans['id'],
                                'trans_type': trans['type'],
                                'amount': trans['amount']
                            }
        
        self.transactions_tree.update()

    def on_transaction_select(self, event):
        selected = self.transactions_tree.selection()
        if selected:
            self.selected_item_id = selected[0]

    def edit_transaction(self):
        if not self.selected_item_id or self.selected_item_id not in self.transaction_mapping:
            messagebox.showwarning("Ошибка", "Выберите транзакцию!")
            return
        
        item_data = self.transaction_mapping[self.selected_item_id]
        
        if item_data['type'] != 'transaction':
            messagebox.showwarning("Ошибка", "Выберите конкретную транзакцию!")
            return
        
        if item_data['trans_type'] != 'payment':
            messagebox.showwarning("⚠️ Ошибка", "❌ НЕЛЬЗЯ РЕДАКТИРОВАТЬ ДОЛГИ!\n\nЭтот функционал доступен только в вкладке 'Администрирование'.\n\nДля изменения сумм долгов используйте опцию\n'Редактировать' в разделе 'Управление категориями'.")
            return
        
        transactions = self.db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == item_data['trans_id']), None)
        
        if not transaction:
            messagebox.showerror("❌ Ошибка", "Транзакция не найдена в БД!")
            return
        
        edit_window = tk.Toplevel(self)
        edit_window.title("Редактировать платеж")
        edit_window.geometry("400x250")
        edit_window.resizable(False, False)
        edit_window.grab_set()
        
        header = tk.Frame(edit_window, bg='#0078D4', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title_label = tk.Label(header, text="💰 Редактировать платеж",
            font=("Arial", 14, "bold"), bg='#0078D4', fg='white')
        title_label.pack(pady=15)
        
        content_frame = tk.Frame(edit_window, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Новая сумма платежа (руб.):", font=("Arial", 11, "bold"),
            bg='white', fg='#333').pack(anchor='w', pady=(0, 8))
        
        amount_entry = tk.Entry(content_frame, font=("Arial", 11), width=40, relief=tk.SOLID, bd=1)
        amount_entry.insert(0, str(transaction['amount']))
        amount_entry.pack(fill=tk.X, ipady=10, pady=(0, 20))
        amount_entry.focus()
        amount_entry.select_range(0, tk.END)
        
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_changes():
            try:
                new_amount_str = amount_entry.get().strip()
                if not new_amount_str:
                    messagebox.showwarning("❌ Ошибка", "Введите сумму!")
                    return
                
                try:
                    new_amount = float(new_amount_str)
                except ValueError:
                    messagebox.showerror("❌ Ошибка", "Сумма должна быть числом!")
                    return
                
                if new_amount <= 0:
                    messagebox.showwarning("❌ Ошибка", "Сумма должна быть больше 0!")
                    return
                
                old_amount = transaction['amount']
                trans_id = transaction['id']
                
                if self.db.update_transaction(trans_id, new_amount, transaction.get('notes', '')):
                    updated_trans = next((t for t in self.db.get_transactions() if t['id'] == trans_id), None)
                    
                    if updated_trans and updated_trans['amount'] == new_amount:
                        self.refresh_transactions_tree()
                        self.refresh_apartments()
                        self.notebook.select(self.transactions_tab)
                        self.update()
                        self.transactions_tree.update()
                        
                        messagebox.showinfo("✅ Успех",
                            f"✓ Платеж обновлен!\n\n💰 Старая сумма: {old_amount:.2f} руб.\n💰 Новая сумма: {new_amount:.2f} руб.\n✓ Все вкладки обновлены!")
                        
                        edit_window.destroy()
                    else:
                        messagebox.showerror("❌ ОШИБКА",
                            f"Платеж не сохранился правильно!")
                else:
                    messagebox.showerror("❌ Ошибка", "Не удалось обновить платеж в БД!")
            except Exception as e:
                messagebox.showerror("❌ ОШИБКА", f"Ошибка:\n{str(e)}")
        
        save_btn = tk.Button(button_frame, text="💾 СОХРАНИТЬ", command=save_changes,
            bg='#107C10', fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
            cursor="hand2", activebackground='#0B6107', activeforeground='white',
            relief=tk.RAISED, bd=2)
        save_btn.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        
        cancel_btn = tk.Button(button_frame, text="❌ ОТМЕНА", command=edit_window.destroy,
            bg='#C91130', fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
            cursor="hand2", activebackground='#A00A25', activeforeground='white',
            relief=tk.RAISED, bd=2)
        cancel_btn.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

    def delete_transaction_btn(self):
        if not self.selected_item_id or self.selected_item_id not in self.transaction_mapping:
            messagebox.showwarning("Ошибка", "Выберите транзакцию для удаления!")
            return
        
        item_data = self.transaction_mapping[self.selected_item_id]
        
        if item_data['type'] == 'transaction':
            if item_data['trans_type'] != 'payment':
                messagebox.showwarning("⚠️ ОШИБКА", "❌ НЕЛЬЗЯ УДАЛЯТЬ ДОЛГИ!\n\nЭтот функционал доступен только в вкладке 'Администрирование' для администратора.\n\nМожно удалять только транзакции ПЛАТЕЖЕЙ 💰")
                return
            
            if messagebox.askyesno("Подтверждение", "Удалить эту транзакцию платежа?"):
                if self.db.delete_transaction(item_data['trans_id']):
                    messagebox.showinfo("✅ Успех", "Платеж удален!")
                    self.refresh_transactions_tree()
                    self.refresh_apartments()

    def save_transaction(self, trans_type):
        try:
            apt_id = int(self.trans_apt_var.get()) - 1
            cat_id = int(self.trans_cat_var.get().split(':')[0])
            amount = float(self.trans_amount_entry.get())
            
            if not self.trans_apt_var.get() or not self.trans_cat_var.get():
                messagebox.showwarning("Ошибка", "Выберите квартиру и категорию!")
                return
            
            if trans_type != 'payment':
                messagebox.showwarning("Ошибка", "Только администратор может добавлять долги!")
                return
            
            self.db.add_transaction(apt_id, cat_id, amount, trans_type, self.user['id'], "")
            
            messagebox.showinfo("✅ Успех", "Платеж записан!")
            
            self.trans_apt_var.set('')
            self.trans_cat_var.set('')
            self.trans_amount_entry.delete(0, tk.END)
            
            self.refresh_transactions_tree()
            self.refresh_apartments()
        except ValueError:
            messagebox.showerror("❌ Ошибка", "Проверьте введенные данные!")


def main():
    db = Database()
    login_window = LoginWindow(db)
    login_window.mainloop()
    
    if login_window.user:
        main_window = MainWindow(db, login_window.user)
        main_window.mainloop()


if __name__ == "__main__":
    main()
