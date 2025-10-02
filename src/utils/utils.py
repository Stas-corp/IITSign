from pathlib import Path

def remove_signed_files(
    root_path_dir
):
    """
    Удаление всех подписей в папке.
    
    # Важно! 
    Схема папок должна быть следующей:
    
    root_path_dir/
    
    ├── dir/
    
    ----├── doc.pdf
    
    ----└──doc.pdf.p7s
    """
    root_path_dir = Path(root_path_dir)
    directories = [item for item in root_path_dir.iterdir() if item.is_dir()]
    for dir in directories:
        files = [item for item in dir.iterdir() 
                 if item.is_file() and item.suffix.lower() == ".p7s"]
        print(f"In dir {dir} files with sign {len(files)}")
        if files:
            for f in files:
                f.unlink()

if __name__ == "__main__":
    remove_signed_files(r"C:\Users\ssamo\Documents\Projects\Ace_11_09_2025_part1")