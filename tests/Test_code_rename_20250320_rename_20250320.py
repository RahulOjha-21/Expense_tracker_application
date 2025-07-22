import os
import datetime
file_list = os.listdir("tests")
print(file_list)
rename_date = datetime.datetime.now().strftime("%Y%m%d")

# Ensure the export folder exists
export_folder = os.path.join("outputs", "export")
os.makedirs(export_folder, exist_ok=True)

# Move renamed files to the export folder
for file_name in file_list:
    name, ext = os.path.splitext(file_name)
    new_name = f"{name}_rename_{rename_date}{ext}"
    old_path = os.path.join("tests", file_name)
    new_path = os.path.join("tests", new_name)
    os.rename(old_path, new_path)
    os.replace(new_path, os.path.join(export_folder, new_name))