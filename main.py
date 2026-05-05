import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import os

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("750x600")
        
        # Загрузка избранного
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Создание интерфейса
        self.create_ui()
    
    def create_ui(self):
        # Рамка для поиска
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10)
        
        tk.Label(search_frame, text="Введите логин GitHub:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search())
        
        tk.Button(search_frame, text="🔍 Поиск", command=self.search, bg="#2ea44f", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        
        # Таблица результатов
        tk.Label(self.root, text="📊 Результаты поиска:", font=("Arial", 10, "bold")).pack(pady=(10,0))
        
        # Создаём фрейм для таблицы и скролла
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Таблица
        self.tree = ttk.Treeview(tree_frame, columns=("login", "id", "url"), show="headings", yscrollcommand=scrollbar.set)
        self.tree.heading("login", text="👤 Логин")
        self.tree.heading("id", text="🆔 ID")
        self.tree.heading("url", text="🔗 URL профиля")
        self.tree.column("login", width=150)
        self.tree.column("id", width=80)
        self.tree.column("url", width=400)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Кнопки управления
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="⭐ Добавить в избранное", command=self.add_favorite, bg="#ffc107", padx=10, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="📋 Показать избранное", command=self.show_favorites, bg="#17a2b8", fg="white", padx=10, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Удалить из избранного", command=self.remove_favorite, bg="#dc3545", fg="white", padx=10, width=20).pack(side=tk.LEFT, padx=5)
        
        # Список избранного
        tk.Label(self.root, text="⭐ Избранные пользователи:", font=("Arial", 10, "bold")).pack(pady=(10,0))
        
        fav_frame = tk.Frame(self.root)
        fav_frame.pack(pady=5, padx=10, fill=tk.X)
        
        fav_scrollbar = tk.Scrollbar(fav_frame)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.fav_listbox = tk.Listbox(fav_frame, height=4, yscrollcommand=fav_scrollbar.set)
        self.fav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.config(command=self.fav_listbox.yview)
        
        # Обновляем отображение избранного
        self.update_fav_listbox()
    
    def search(self):
        username = self.search_entry.get().strip()
        
        # Валидация
        if not username:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не может быть пустым!")
            return
        
        # Показываем статус загрузки
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # Запрос к API GitHub
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Очистка таблицы
                for item in self.tree.get_children():
                    self.tree.delete(item)
                # Добавление результата
                self.tree.insert("", 0, values=(data["login"], data["id"], data["html_url"]))
                messagebox.showinfo("Успех", f"Пользователь {data['login']} найден!")
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", f"Пользователь '{username}' не найден на GitHub!")
            else:
                messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
                
        except requests.exceptions.Timeout:
            messagebox.showerror("Ошибка", "Превышено время ожидания ответа от сервера!")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к интернету!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        finally:
            self.root.config(cursor="")
    
    def add_favorite(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Сначала найдите и выберите пользователя в таблице!")
            return
        
        # Получаем данные выбранного пользователя
        values = self.tree.item(selected[0])["values"]
        if not values:
            return
        
        login, user_id, url = values
        
        # Проверка на дубликат
        for fav in self.favorites:
            if fav["login"] == login:
                messagebox.showinfo("Информация", f"Пользователь '{login}' уже есть в избранном!")
                return
        
        # Добавление в избранное
        self.favorites.append({"login": login, "id": user_id, "url": url})
        self.save_favorites()
        self.update_fav_listbox()
        messagebox.showinfo("Успех", f"Пользователь '{login}' добавлен в избранное!")
    
    def remove_favorite(self):
        selected = self.fav_listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя в списке избранного!")
            return
        
        login = self.fav_listbox.get(selected[0])
        
        # Удаление
        self.favorites = [fav for fav in self.favorites if fav["login"] != login]
        self.save_favorites()
        self.update_fav_listbox()
        messagebox.showinfo("Успех", f"Пользователь '{login}' удалён из избранного!")
    
    def show_favorites(self):
        if not self.favorites:
            messagebox.showinfo("Информация", "Список избранного пуст. Добавьте пользователей через кнопку 'Добавить в избранное'")
            return
        
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Показ всех избранных
        for fav in self.favorites:
            self.tree.insert("", 0, values=(fav["login"], fav["id"], fav["url"]))
        
        messagebox.showinfo("Информация", f"Показано {len(self.favorites)} избранных пользователей")
    
    def update_fav_listbox(self):
        self.fav_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_listbox.insert(tk.END, fav["login"])
    
    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_favorites(self):
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
        except:
            messagebox.showerror("Ошибка", "Не удалось сохранить избранное!")

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
