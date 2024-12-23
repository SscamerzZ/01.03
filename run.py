import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
import mysql.connector
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
import time

kivy.require('2.0.0')

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="time_tracker"
    )

class LoginScreen(Screen):
    def login_user(self):
        username = self.ids.username.text
        password = self.ids.password.text

        self.logo = Image(source='D:\\12345\\pythonProjectProect\\avatars\\auto.png', size_hint=(None, None), size=(70, 70))
        self.logo.pos_hint = {'right': 1, 'top': 1}

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            if user[3] == 'admin':
                app.root.current = "admin_screen"
            else:
                app.root.current = "user_screen"
                user_screen = self.manager.get_screen('user_screen')
                user_screen.load_tasks(user[0])
                user_screen.user_id = user[0]
            self.show_popup("Вход выполнен успешно!")
        else:
            self.show_popup("Недействительные учетные данные!")

        cursor.close()
        db.close()

    def forgot_password(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        email_input = TextInput(hint_text="Введите ваш Email", multiline=False)

        reset_button = Button(text="Сбросить пароль", on_release=lambda btn: self.reset_password(email_input.text))

        layout.add_widget(email_input)
        layout.add_widget(reset_button)

        popup = Popup(title="Восстановление пароля", content=layout, size_hint=(None, None), size=(400, 200))
        popup.open()

    def reset_password(self, email):
        if not email:
            self.show_popup("Пожалуйста, введите адрес электронной почты.")
            return

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            self.show_popup("Пользователь с таким email не найден.")
            return

        new_password = self.generate_random_password()

        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
        db.commit()

        cursor.close()
        db.close()

        self.send_reset_email(email, new_password)

        self.show_popup(f"Новый пароль был отправлен на вашу почту: {email}")

    def generate_random_password(self):
        import random
        import string
        password_length = 8
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(password_length))

    def send_reset_email(self, email, new_password):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender_email = ""
        receiver_email = email
        sender_password = ""

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = 'Восстановление пароля'

        body = f"Ваш новый пароль: {new_password}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
        except Exception as e:
            self.show_popup(f"Ошибка при отправке письма: {e}")

    def show_popup(self, message):
        popup = Popup(title='Уведомление',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_popup(self, message):
        popup = Popup(title='Уведомление',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

class RegisterScreen(Screen):
    def register_user(self):
        username = self.ids.username.text
        password = self.ids.password.text
        email = self.ids.email.text

        self.logo = Image(source='D:\\12345\\pythonProjectProect\\avatars\\auto.png', size_hint=(None, None),
                          size=(70, 70))
        self.logo.pos_hint = {'right': 1, 'top': 1}

        if not username or not password or not email:
            self.show_popup("Пожалуйста, заполните все поля.")
            return

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, 'user')",
                       (username, password, email))
        db.commit()
        cursor.close()
        db.close()

        self.ids.username.text = ''
        self.ids.password.text = ''
        self.ids.email.text = ''
        self.show_popup("Пользователь успешно зарегистрирован!")
        self.manager.current = "login_screen"

    def show_popup(self, message):
        popup = Popup(title='Уведомление',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

class UserScreen(Screen):
    user_id = None

    avatar_path = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = None
        self.end_time = None
        self.tasks_completed = 0

    def start_work(self):
        self.start_time = time.time()
        self.ids.statistics_label.text = "Статус: В процессе работы"
        self.ids.start_work_button.disabled = True
        self.ids.end_work_button.disabled = False

    def end_work(self):
        if self.start_time is None:
            self.show_popup("Вы не начали работу!")
            return

        self.end_time = time.time()
        work_duration = self.end_time - self.start_time
        work_duration_minutes = work_duration // 60
        work_duration_seconds = work_duration % 60

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND status = 'Завершено'", (self.user_id,))
        tasks_completed = cursor.fetchone()[0]
        cursor.close()
        db.close()

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO reports (user_id, report_text) VALUES (%s, %s)",
                       (self.user_id,
                        f"Время работы: {int(work_duration_minutes)} минут {int(work_duration_seconds)} секунд"))
        db.commit()
        cursor.close()
        db.close()

        self.ids.statistics_label.text = f"     Статус: Работа завершена. Время работы: {int(work_duration_minutes)} мин {int(work_duration_seconds)} сек"
        self.ids.start_work_button.disabled = False
        self.ids.end_work_button.disabled = True

    def task_completed(self):
        self.tasks_completed += 1
        self.update_statistics(self.user_id)

    def show_report_form(self):
        pass

    def show_popup(self, message):
        popup = Popup(title="Уведомление", content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.avatar_image = Image(
            size_hint=(None, None),
            size=(100, 100),
            pos_hint={'right': 1, 'top': 1}
        )
        self.add_widget(self.avatar_image)
        self.avatar_path = self.get_avatar_from_db()

    def load_tasks(self, user_id):
        self.user_id = user_id
        self.update_statistics(user_id)
        self.display_avatar()

    def display_avatar(self):
        if self.avatar_path:
            self.avatar_image.source = self.avatar_path
        else:
            self.avatar_image.source = "default_avatar.png"

    def show_popup(self, message):
        popup = Popup(title='Уведомление',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def get_avatar_from_db(self):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT avatar_path FROM users WHERE id = %s", (self.user_id,))
        avatar_path = cursor.fetchone()
        cursor.close()
        db.close()

        if avatar_path and avatar_path[0]:
            return avatar_path[0]
        return ""

    def update_avatar(self, avatar_path):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET avatar_path = %s WHERE id = %s", (avatar_path, self.user_id))
        db.commit()
        cursor.close()
        db.close()

    def change_avatar(self):
        layout = BoxLayout(orientation='vertical')
        filechooser = FileChooserIconView()
        filechooser.filters = ['*.png', '*.jpg', '*.jpeg']

        button = Button(text="Выбрать", size_hint_y=None, height=50)
        button.bind(on_release=lambda btn: self.set_avatar(filechooser.path, filechooser.selection))

        layout.add_widget(filechooser)
        layout.add_widget(button)

        popup = Popup(title="Выберите аватарку", content=layout, size_hint=(None, None), size=(600, 400))
        popup.open()

    def set_avatar(self, path, selection):
        if selection:
            selected_file = selection[0]
            self.avatar_path = selected_file
            self.update_avatar(selected_file)
            self.display_avatar()
        else:
            self.show_popup("Пожалуйста, выберите файл изображения.")

    def show_profile_form(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # Inputs for the profile form
        birth_date_input = TextInput(hint_text="Дата рождения (YYYY-MM-DD)", multiline=False)
        gender_spinner = Spinner(text="Выберите пол", values=("Male", "Female", "Other"))
        phone_input = TextInput(hint_text="Номер телефона", multiline=False)
        address_input = TextInput(hint_text="Адрес", multiline=True)

        # Save button
        save_button = Button(text="Сохранить", on_release=lambda btn: self.save_profile_data(
            birth_date_input.text, gender_spinner.text, phone_input.text, address_input.text))

        layout.add_widget(birth_date_input)
        layout.add_widget(gender_spinner)
        layout.add_widget(phone_input)
        layout.add_widget(address_input)
        layout.add_widget(save_button)

        popup = Popup(title="Заполните профиль", content=layout, size_hint=(None, None), size=(400, 400))
        popup.open()

    def save_profile_data(self, birth_date, gender, phone_number, address):
        if not birth_date or not gender or not phone_number or not address:
            self.show_popup("Пожалуйста, заполните все поля!")
            return

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO employees (user_id, birth_date, gender, phone_number, address) 
            VALUES (%s, %s, %s, %s, %s)
        """, (self.user_id, birth_date, gender, phone_number, address))

        db.commit()
        cursor.close()
        db.close()

        self.show_popup("Профиль успешно обновлен!")

    def show_tasks(self):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, task_description, status FROM tasks WHERE user_id = %s", (self.user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        db.close()

        task_list_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        task_list_layout.bind(minimum_height=task_list_layout.setter('height'))

        for idx, task in enumerate(tasks, start=1):
            task_label = Label(
                text=f"{idx}. {task[1]} - Статус: {task[2]}",
                font_size="20sp",
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=40
            )
            complete_button = Button(
                text="Завершить задачу",
                size_hint_y=None,
                height=40,
                on_release=lambda btn, task_id=task[0]: self.complete_task(task_id)
            )
            task_list_layout.add_widget(task_label)
            task_list_layout.add_widget(complete_button)

        scroll_view = ScrollView(size_hint=(1, None), size=(400, 400))
        scroll_view.add_widget(task_list_layout)

        popup = Popup(title="Ваши Задания", content=scroll_view, size_hint=(None, None), size=(500, 500))
        popup.open()

    def complete_task(self, task_id):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE tasks SET status = 'Выполнено' WHERE id = %s", (task_id,))
        db.commit()
        cursor.close()
        db.close()
        self.show_popup("Задача завершена!")
        self.update_statistics(self.user_id)

    def update_statistics(self, user_id):
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND status = 'Выполнено'", (user_id,))
        completed_tasks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s", (user_id,))
        total_tasks = cursor.fetchone()[0]

        cursor.close()
        db.close()

        if completed_tasks < 10:
            self.ids.statistics_label.text = f"Статус: Новичок ({completed_tasks}/{total_tasks} задач)"
        elif completed_tasks < 20:
            self.ids.statistics_label.text = f"Статус: Разработчик ({completed_tasks}/{total_tasks} задач)"
        else:
            self.ids.statistics_label.text = f"Статус: Эксперт ({completed_tasks}/{total_tasks} задач)"

    def load_tasks(self, user_id):
        self.user_id = user_id
        self.update_statistics(user_id)

    def show_report_form(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        report_input = TextInput(hint_text="Введите отчет о проделанной работе", multiline=True, size_hint_y=None,
                                 height=200)

        send_button = Button(text="Отправить отчет", on_release=lambda btn: self.send_report(report_input.text))

        layout.add_widget(report_input)
        layout.add_widget(send_button)

        popup = Popup(title="Отправьте отчет", content=layout, size_hint=(None, None), size=(400, 400))
        popup.open()

    def send_report(self, report_text):
        if not report_text:
            self.show_popup("Пожалуйста, введите текст отчета.")
            return

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO message (user_id, report_text) VALUES (%s, %s)", (self.user_id, report_text))
        db.commit()
        cursor.close()
        db.close()

        self.show_popup("Ваш отчет был успешно отправлен!")

class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_list = []

    def on_enter(self):
        self.load_users()

    def load_users(self):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, username FROM users WHERE role = 'user'")
        users = cursor.fetchall()

        self.user_list = [f"{user[1]} (ID: {user[0]})" for user in users]
        self.ids.user_spinner.values = self.user_list

        cursor.close()
        db.close()

    def add_task(self):
        selected_user = self.ids.user_spinner.text
        if not selected_user:
            self.show_popup("Пожалуйста, выберите пользователя.")
            return

        user_id = int(selected_user.split(":")[1].strip(")"))
        task_description = self.ids.task_description.text

        if not task_description:
            self.show_popup("Пожалуйста, заполните все поля.")
            return

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO tasks (user_id, task_description, status) VALUES (%s, %s, 'В процессе')",
                       (user_id, task_description))
        db.commit()
        cursor.close()
        db.close()

        self.ids.task_description.text = ''
        self.show_popup("Задача успешно добавлена!")

    def show_all_tasks(self):
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT t.id, u.username, t.task_description, t.status FROM tasks t JOIN users u ON t.user_id = u.id")
        tasks = cursor.fetchall()
        cursor.close()
        db.close()

        task_list_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        task_list_layout.bind(minimum_height=task_list_layout.setter('height'))

        for idx, task in enumerate(tasks, start=1):
            task_label = Label(
                text=f"{idx}. {task[1]} - {task[2]} - Статус: {task[3]}",
                font_size="20sp",
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=40
            )
            task_list_layout.add_widget(task_label)

        scroll_view = ScrollView(size_hint=(1, None), size=(600, 400))
        scroll_view.add_widget(task_list_layout)

        popup = Popup(title="Все Задания", content=scroll_view, size_hint=(None, None), size=(700, 500))
        popup.open()

    def logout(self):
        app.root.current = "login_screen"

    def show_popup(self, message):
        popup = Popup(title='Уведомление',
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def show_reports(self):
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                SELECT u.username, r.report_text, r.created_at, u.id
                FROM reports r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.created_at DESC
            """)
            reports = cursor.fetchall()

            cursor.close()
            db.close()

            if not reports:
                self.show_popup("Нет отчетов для отображения.")
                return

            report_list_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
            report_list_layout.bind(minimum_height=report_list_layout.setter('height'))

            for idx, report in enumerate(reports, start=1):
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = %s AND status = 'Выполнено'", (report[3],))
                tasks_completed = cursor.fetchone()[0]
                cursor.close()
                db.close()

                report_label = Label(
                    text=f"{idx}.  Пользователь:{report[0]}\n {report[1]}\n Дата: {report[2]}\n Завершено задач: {tasks_completed}",
                    font_size="16sp",
                    color=(0, 0, 0, 1),
                    size_hint_y=None,
                    height=100
                )
                report_list_layout.add_widget(report_label)

            scroll_view = ScrollView(size_hint=(1, None), size=(600, 400))
            scroll_view.add_widget(report_list_layout)

            popup = Popup(title="Все отчеты", content=scroll_view, size_hint=(None, None), size=(700, 500))
            popup.open()

        except Exception as e:
            self.show_popup(f"Ошибка при получении отчетов: {str(e)}")

    def show_message(self):
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                SELECT u.username, m.report_text, m.created_at 
                FROM message m 
                JOIN users u ON m.user_id = u.id
            """)
            messages = cursor.fetchall()

            cursor.close()
            db.close()

            if not messages:
                self.show_popup("Нет сообщений для отображения.")
                return

            message_list_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
            message_list_layout.bind(minimum_height=message_list_layout.setter('height'))

            for idx, message in enumerate(messages, start=1):
                message_label = Label(
                    text=f"{idx}. Пользователь: {message[0]}\nСообщение: {message[1]}\nДата: {message[2]}",
                    font_size="16sp",
                    color=(0, 0, 0, 1),
                    size_hint_y=None,
                    height=100
                )
                message_list_layout.add_widget(message_label)

            scroll_view = ScrollView(size_hint=(1, None), size=(600, 400))
            scroll_view.add_widget(message_list_layout)

            popup = Popup(title="Все сообщения", content=scroll_view, size_hint=(None, None), size=(700, 500))
            popup.open()

        except Exception as e:
            self.show_popup(f"Ошибка: {str(e)}")
            print(f"Ошибка: {str(e)}")

class WorkTimeApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(LoginScreen(name="login_screen"))
        self.screen_manager.add_widget(RegisterScreen(name="register_screen"))
        self.screen_manager.add_widget(UserScreen(name="user_screen"))
        self.screen_manager.add_widget(AdminScreen(name="admin_screen"))
        return self.screen_manager

kv = """
<LoginScreen>:
    name: "login_screen"
    BoxLayout:
        orientation: "vertical"
        padding: 50, 50
        spacing: 20
        canvas.before:
            Color:
                rgba: 0.9, 0.9, 0.9, 1
            Rectangle:
                size: self.size
                pos: self.pos
        Image:
            source: "D:\\12345\\pythonProjectProect\\avatars\\auto.png"
            size_hint: None, None
            size: "70dp", "70dp"
            pos_hint: {"right": 1, "top": 1}
        Label:
            text: "Добро пожаловать в Time Tracker"
            font_size: "28sp"
            color: 0, 0, 0, 1
        TextInput:
            id: username
            hint_text: "Username"
            multiline: False
            size_hint_y: None
            height: "40dp"
            background_normal: ''
            background_color: 0.95, 0.95, 0.95, 1
        TextInput:
            id: password
            hint_text: "Password"
            multiline: False
            password: True
            size_hint_y: None
            height: "40dp"
            background_normal: ''
            background_color: 0.95, 0.95, 0.95, 1
        Button:
            text: "Войти"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.login_user()
        Button:
            text: "Создать аккаунт"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: app.root.current = "register_screen"
        Button:
            text: "Забыл пароль?"
            size_hint_y: None
            height: "50dp"
            background_normal: ''
            background_color: 0, 0, 0, 0
            color: 0, 0, 1, 1
            on_release: root.forgot_password()
<RegisterScreen>:
    name: "register_screen"
    BoxLayout:
        orientation: "vertical"
        padding: 50, 50
        spacing: 20
        canvas.before:
            Color:
                rgba: 0.9, 0.9, 0.9, 1
            Rectangle:
                size: self.size
                pos: self.pos
        Image:
            source: "D:\\12345\\pythonProjectProect\\avatars\\auto.png"
            size_hint: None, None
            size: "70dp", "70dp"
            pos_hint: {"right": 1, "top": 1}
        Label:
            text: "Регистрация"
            font_size: "28sp"
            color: 0, 0, 0, 1
        TextInput:
            id: username
            hint_text: "Username"
            multiline: False
            size_hint_y: None
            height: "40dp"
            background_normal: ''
            background_color: 0.95, 0.95, 0.95, 1
        TextInput:
            id: password
            hint_text: "Password"
            multiline: False
            password: True
            size_hint_y: None
            height: "40dp"
            background_normal: ''
            background_color: 0.95, 0.95, 0.95, 1
        TextInput:
            id: email
            hint_text: "Email"
            multiline: False
            size_hint_y: None
            height: "40dp"
            background_normal: ''
            background_color: 0.95, 0.95, 0.95, 1
        Button:
            text: "Зарегистрироваться"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.register_user()
        Button:
            text: "У вас уже есть аккаунт? Войти"
            size_hint_y: None
            height: "50dp"
            background_color: 0.9, 0.9, 0.9, 1
            on_release: app.root.current = "login_screen"
<UserScreen>:
    name: "user_screen"
    BoxLayout:
        orientation: "vertical"
        padding: 50, 50
        spacing: 20
        canvas.before:
            Color:
                rgba: 0.9, 0.9, 0.9, 1
            Rectangle:
                size: self.size
                pos: self.pos
        Label:
            id: statistics_label
            text: "Статус: Новичок"
            font_size: "20sp"
            color: 0, 0, 0, 1
            size_hint: None, None
            size: 250, 40
            pos_hint: {"x": 0, "top": 1}
        Button:
            id: start_work_button
            text: "Начать работу"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.start_work()
        Button:
            id: end_work_button
            text: "Завершить работу"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.end_work()
            disabled: True
        Button:
            text: "Отправить сообщение админу"
            size_hint_y: None
            height: "50dp"
            background_color: 0.9, 0.9, 0.9, 1
            on_release: root.show_report_form()
        Button:
            text: "Задания"
            size_hint_y: None
            height: "50dp"
            background_color: 0.9, 0.9, 0.9, 1
            on_release: root.show_tasks()
        Button:
            text: "Изменить аватар"
            size_hint_y: None
            height: "50dp"
            background_color: 0.9, 0.9, 0.9, 1
            on_release: root.change_avatar()
        Button:
            text: "Заполнить профиль"
            size_hint_y: None
            height: "50dp"
            background_color: 0.9, 0.9, 0.9, 1
            on_release: root.show_profile_form()
        Button:
            text: "Выйти"
            size_hint: None, None
            size: 150, 50
            pos_hint: {"x": 0.4, "y": 0.05}
            background_color: 0.2, 0.6, 1, 1
            on_release: app.root.current = "login_screen"
<AdminScreen>:
    name: "admin_screen"
    BoxLayout:
        orientation: "vertical"
        padding: 50, 50
        spacing: 20
        canvas.before:
            Color:
                rgba: 0.9, 0.9, 0.9, 1
            Rectangle:
                size: self.size
                pos: self.pos
        Label:
            text: "Admin Panel"
            font_size: "28sp"
            color: 0, 0, 0, 1
        BoxLayout:
            orientation: "vertical"
            padding: 50, 50
            spacing: 20
        Button:
            text: "Просмотр отчётов"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.show_reports()
        Button:
            text: "Просмотр сообщений пользователей"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.show_message()
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "50dp"
            spacing: 10
            Spinner:
                id: user_spinner
                text: "Выберите пользователя"
                size_hint_x: 0.4
            TextInput:
                id: task_description
                hint_text: "Описание задачи"
                multiline: False
                size_hint_x: 0.4
                background_normal: ''
                background_color: 0.95, 0.95, 0.95, 1
            Button:
                text: "Добавить задачу"
                size_hint_x: 0.2
                background_color: 0.2, 0.6, 1, 1
                on_release: root.add_task()
        Button:
            text: "Просмотреть все задачи"
            size_hint_y: None
            height: "50dp"
            background_color: 0.2, 0.6, 1, 1
            on_release: root.show_all_tasks()
        Button:
            text: "Выйти"
            size_hint: None, None
            size: 150, 50
            pos_hint: {"x": 0.4, "y": 0.05}
            background_color: 0.2, 0.6, 1, 1
            on_release: root.logout()
"""

Builder.load_file('ui.kv')

if __name__ == "__main__":
    app = WorkTimeApp()
    app.run()