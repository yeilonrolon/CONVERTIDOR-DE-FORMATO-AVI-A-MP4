import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class ConvertidorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Convertidor de video a MP4")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # La carpeta por defecto es donde se guarda/ejecuta este archivo .py
        self.directorio_actual = os.path.dirname(os.path.abspath(__file__))

        self.setup_ui()
        self.verificar_ffmpeg()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Título principal
        lbl_titulo = tk.Label(
            self.root,
            text="Convertidor de video a MP4 (H.264 / AAC)",
            font=("Helvetica", 14, "bold")
        )
        lbl_titulo.pack(pady=15)

        # Marco para la selección de directorio
        frame_dir = tk.LabelFrame(self.root, text=" Carpeta de Trabajo ", padx=10, pady=10)
        frame_dir.pack(fill="x", padx=20, pady=5)

        self.txt_ruta = tk.Entry(frame_dir, font=("Helvetica", 10))
        self.txt_ruta.insert(0, self.directorio_actual)
        self.txt_ruta.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_examinar = tk.Button(
            frame_dir,
            text="Examinar...",
            command=self.seleccionar_carpeta
        )
        btn_examinar.pack(side="right")

        # Botón principal de conversión
        self.btn_convertir = tk.Button(
            self.root,
            text="▶ Convertir todos los videos a .MP4",
            font=("Helvetica", 11, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            pady=8,
            padx=15,
            command=self.iniciar_conversion_thread
        )
        self.btn_convertir.pack(pady=15)

        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=20, pady=5)

        # Consola / Log de estado
        frame_log = tk.LabelFrame(self.root, text=" Estado del proceso ", padx=5, pady=5)
        frame_log.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.txt_log = tk.Text(frame_log, height=8, font=("Consolas", 9), state="disabled")
        self.txt_log.pack(fill="both", expand=True)

    def log(self, mensaje):
        """Agrega texto a la consola integrada."""
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.txt_ruta.get())
        if carpeta:
            self.txt_ruta.delete(0, tk.END)
            self.txt_ruta.insert(0, carpeta)

    def verificar_ffmpeg(self):
        """Comprueba si FFmpeg está instalado en el sistema."""
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, creationflags=creation_flags)
            self.log("✔ Sistema listo. FFmpeg detectado correctamente.")
        except (subprocess.SubprocessError, FileNotFoundError):
            self.log("⚠️ ADVERTENCIA: FFmpeg no está instalado o no se encuentra en el PATH.")
            messagebox.showwarning(
                "FFmpeg no encontrado",
                "Para realizar la conversión necesitas tener FFmpeg instalado o el ejecutable 'ffmpeg.exe' en la misma carpeta."
            )

    def iniciar_conversion_thread(self):
        """Ejecuta la conversión en un hilo secundario."""
        threading.Thread(target=self.convertir_archivos, daemon=True).start()

    def convertir_archivos(self):
        carpeta = self.txt_ruta.get()

        if not os.path.exists(carpeta):
            messagebox.showerror("Error", "La carpeta seleccionada no existe.")
            return

        extensiones_video = {
            ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v",
            ".mpg", ".mpeg", ".3gp", ".ts", ".mts", ".m2ts", ".vob"
        }
        archivos_video = [
            f for f in os.listdir(carpeta)
            if os.path.isfile(os.path.join(carpeta, f))
            and os.path.splitext(f)[1].lower() in extensiones_video
        ]

        if not archivos_video:
            messagebox.showinfo("Información", "No se encontraron videos compatibles en la carpeta.")
            self.log("No se encontraron videos compatibles para procesar.")
            return

        self.btn_convertir.config(state="disabled")
        self.progress["maximum"] = len(archivos_video)
        self.progress["value"] = 0

        self.log(f"Iniciando conversión optimizada de {len(archivos_video)} archivo(s)...")

        exitosos = 0
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        for i, archivo in enumerate(archivos_video, 1):
            ruta_entrada = os.path.join(carpeta, archivo)
            nombre_base = os.path.splitext(archivo)[0]
            ruta_salida = os.path.join(carpeta, f"{nombre_base}.mp4")

            self.log(f"[{i}/{len(archivos_video)}] Convirtiendo: {archivo}...")

            comando = [
                "ffmpeg",
                "-y",
                "-threads", "2",          # Limita a 2 hilos de la CPU
                "-i", ruta_entrada,
                "-c:v", "libx264",
                "-preset", "ultrafast",    # Modode codificación rápido de baja carga
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192000",
                ruta_salida
            ]

            try:
                proceso = subprocess.run(
                    comando,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=creation_flags
                )

                if proceso.returncode == 0:
                    self.log(f"  ✔ Guardado como: {nombre_base}.mp4")
                    exitosos += 1
                else:
                    self.log(f"  ❌ Error al convertir {archivo}")

            except Exception as e:
                self.log(f"  ❌ Error de ejecución: {str(e)}")

            self.progress["value"] = i

        self.log(f"\n¡Proceso finalizado! Se convirtieron {exitosos} de {len(archivos_video)} archivo(s).")
        self.btn_convertir.config(state="normal")
        messagebox.showinfo("Completado", f"Conversión finalizada.\nArchivos procesados: {exitosos}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConvertidorApp(root)
    root.mainloop()