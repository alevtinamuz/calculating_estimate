import excel_to_sqlite_jobs
import excel_to_sqlite_materials
import getters



jobs_cost_file_excel = "works_cost.xlsx"
jobs_cost_file_db = "works_cost.db"

materials_cost_file_excel = "materials_cost.xlsx"
materials_cost_file_db = "materials_cost.db"

# excel_to_sqlite_jobs.create_database_structure(jobs_cost_file_db)
# excel_to_sqlite_jobs.import_from_excel(jobs_cost_file_excel, jobs_cost_file_db)
#
# excel_to_sqlite_materials.create_database_structue(materials_cost_file_db)
# excel_to_sqlite_materials.import_from_excel(materials_cost_file_excel, materials_cost_file_db)

name = "Огне-био защита древесины (антисептирование)"
price = getters.get_price_by_name(jobs_cost_file_db, name)

print(price)
