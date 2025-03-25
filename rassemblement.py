import os

def collect_python_files(source_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, source_dir)

                    # Écrire le chemin relatif en haut de chaque section
                    out.write(f"# --- {relative_path} ---\n\n")

                    # Lire et écrire le contenu du fichier
                    with open(file_path, 'r', encoding='utf-8') as f:
                        out.write(f.read() + "\n\n")

    print(f"✅ Tous les fichiers Python ont été regroupés dans : {output_file}")

if __name__ == '__main__':
    dossier_source = input("Entrez le chemin du dossier à explorer : ").strip()
    fichier_sortie = input("Entrez le nom du fichier de sortie (ex: resultat.py) : ").strip()

    collect_python_files(dossier_source, fichier_sortie)