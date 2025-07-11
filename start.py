import os
import subprocess
import sys
import uvicorn


def install_requirements():
    print("📦 Installation des dépendances depuis requirements.txt...")
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt manquant !")
        sys.exit(1)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_env_file():
    print("🔍 Vérification de la présence du fichier .env...")
    if not os.path.exists(".env"):
        print("⚠️  Fichier .env manquant. Crée un fichier .env avec la variable DATABASE_URL.")
        sys.exit(1)

def start_server():
    print("🚀 Démarrage de l'API avec Uvicorn...")
    uvicorn.run("main:app", reload=True)

if __name__ == "__main__":
    install_requirements()
    check_env_file()
    start_server()
