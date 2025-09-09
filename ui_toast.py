# ui_toast.py
import tkinter as tk

def show_answer_toast(answer: str, duration_ms: int = 2000):
    """
    Kenarlıksız, siyah arkaplanlı, otomatik kapanan bir bildirim kutusu gösterir.
    """
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle

    toast = tk.Toplevel(root)
    toast.overrideredirect(True)  # Pencere başlığını ve kenarlıklarını kaldır
    toast.attributes('-topmost', True)  # Her zaman üstte
    toast.configure(background='black')

    # Metni ekle
    label = tk.Label(toast, text=answer, fg='white', bg='black', font=("Consolas", 11, "bold"), padx=15, pady=10)
    label.pack()

    # Pencereyi ekranın sağ üstüne konumlandır
    toast.update_idletasks()
    screen_width = toast.winfo_screenwidth()
    width = toast.winfo_width()
    toast.geometry(f"+{screen_width - width - 40}+60")

    # Belirtilen süre sonra kendini imha et
    toast.after(duration_ms, root.destroy)
    
    root.mainloop()


def show_letter_toast(letter: str, duration_ms: int = 1200, font_size: int = 14):
    """
    Çok küçük, sadece tek harf (A/B/C/D) gösteren bildirim.
    """
    letter = (letter or "").strip().upper()[:1]
    if not letter:
        return

    root = tk.Tk()
    root.withdraw()

    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes('-topmost', True)
    toast.configure(background='black')

    label = tk.Label(
        toast,
        text=letter,
        fg='white',
        bg='black',
        font=("Consolas", font_size, "bold"),
        padx=6,
        pady=2,
    )
    label.pack()

    # Sağ üst köşe, çok küçük ofset
    toast.update_idletasks()
    screen_width = toast.winfo_screenwidth()
    width = toast.winfo_width()
    toast.geometry(f"+{screen_width - width - 24}+40")

    toast.after(duration_ms, root.destroy)
    root.mainloop()

if __name__ == '__main__':
    # Test için
    show_answer_toast("Answer: C", duration_ms=2500)
    show_answer_toast("Paris", duration_ms=2500)
