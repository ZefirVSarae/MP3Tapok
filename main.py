import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, error
import io

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MusicTagEditor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MP3 Tag Editor - Win11 Style")
        self.geometry("1100x700")

        self.current_file_path = None
        self.album_art_data = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=15)
        self.sidebar.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.btn_open_dir = ctk.CTkButton(self.sidebar, text="Открыть папку", command=self.load_directory)
        self.btn_open_dir.pack(pady=20, padx=20, fill="x")

        self.file_list = ctk.CTkTextbox(self.sidebar, width=250)
        self.file_list.pack(pady=10, padx=20, expand=True, fill="both")
        
        self.file_list_view = ctk.CTkScrollableFrame(self.sidebar, label_text="Файлы")
        self.file_list_view.pack(pady=10, padx=20, expand=True, fill="both")
        self.file_buttons = []

        self.main_content = ctk.CTkFrame(self, corner_radius=15)
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.cover_label = ctk.CTkLabel(self.main_content, text="Нет обложки", width=200, height=200, fg_color="gray30", corner_radius=10)
        self.cover_label.pack(pady=20)

        self.btn_frame_art = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.btn_frame_art.pack(pady=5)
        
        self.btn_load_art = ctk.CTkButton(self.btn_frame_art, text="Загрузить аву", width=100, command=self.upload_art)
        self.btn_load_art.grid(row=0, column=0, padx=5)
        
        self.btn_clear_art = ctk.CTkButton(self.btn_frame_art, text="Удалить аву", width=100, fg_color="red", hover_color="darkred", command=self.clear_art)
        self.btn_clear_art.grid(row=0, column=1, padx=5)

        self.tag_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tag_frame.pack(pady=20, padx=40, fill="both")

        self.entry_title = self.create_input("Название трека:")
        self.entry_artist = self.create_input("Исполнитель:")
        self.entry_album = self.create_input("Альбом:")

        self.btn_save = ctk.CTkButton(self.main_content, text="Сохранить изменения", height=50, command=self.save_tags)
        self.btn_save.pack(pady=30, padx=40, fill="x")

    def create_input(self, label_text):
        frame = ctk.CTkFrame(self.tag_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        lbl = ctk.CTkLabel(frame, text=label_text, width=120, anchor="w")
        lbl.pack(side="left")
        entry = ctk.CTkEntry(frame, placeholder_text=label_text)
        entry.pack(side="left", expand=True, fill="x")
        return entry

    def load_directory(self):
        dir_path = filedialog.askdirectory()
        if not dir_path:
            return
        
        for btn in self.file_buttons:
            btn.destroy()
        self.file_buttons = []

        files = [f for f in os.listdir(dir_path) if f.lower().endswith(".mp3")]
        for file in files:
            full_path = os.path.join(dir_path, file)
            btn = ctk.CTkButton(self.file_list_view, text=file, anchor="w", fg_color="transparent", text_color=("black", "white"), hover_color=("gray80", "gray25"), command=lambda p=full_path: self.load_file_tags(p))
            btn.pack(fill="x", pady=2)
            self.file_buttons.append(btn)

    def load_file_tags(self, path):
        self.current_file_path = path
        try:
            audio = MP3(path, ID3=ID3)
            self.entry_title.delete(0, 'end')
            self.entry_artist.delete(0, 'end')
            self.entry_album.delete(0, 'end')

            self.entry_title.insert(0, str(audio.get('TIT2', '')))
            self.entry_artist.insert(0, str(audio.get('TPE1', '')))
            self.entry_album.insert(0, str(audio.get('TALB', '')))

            self.album_art_data = None
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    self.album_art_data = tag.data
                    self.update_cover_image(tag.data)
                    break
            else:
                self.cover_label.configure(image=None, text="Нет обложки")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать теги: {e}")

    def update_cover_image(self, data):
        img = Image.open(io.BytesIO(data))
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))
        self.cover_label.configure(image=ctk_img, text="")

    def upload_art(self):
        file_path = filedialog.askopenfilename(filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
        if file_path:
            with open(file_path, "rb") as f:
                self.album_art_data = f.read()
            self.update_cover_image(self.album_art_data)

    def clear_art(self):
        self.album_art_data = b""
        self.cover_label.configure(image=None, text="Обложка удалена")

    def save_tags(self):
        if not self.current_file_path:
            messagebox.showwarning("Внимание", "Сначала выберите файл")
            return

        try:
            audio = MP3(self.current_file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()

            audio.tags.add(TIT2(encoding=3, text=self.entry_title.get()))
            audio.tags.add(TPE1(encoding=3, text=self.entry_artist.get()))
            audio.tags.add(TALB(encoding=3, text=self.entry_album.get()))

            if self.album_art_data is not None:
                if self.album_art_data == b"":
                    audio.tags.delall("APIC")
                else:
                    audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=self.album_art_data))

            audio.save()
            messagebox.showinfo("Успех", "Теги успешно сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

if __name__ == "__main__":
    app = MusicTagEditor()
    app.mainloop()
      
