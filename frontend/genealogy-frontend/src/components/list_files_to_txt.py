import os

# Target folder
folder_path = "/Users/kingal/mapem/frontend/genealogy-frontend/src/components"
output_file = "components_dump.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out.write(f"\n\n===== FILE: {file_path} =====\n\n")
                    out.write(f.read())
            except Exception as e:
                out.write(f"\n\n===== ERROR READING: {file_path} =====\n{e}\n")

print(f"📝 All contents dumped to: {output_file}")
