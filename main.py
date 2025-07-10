import excel_to_sqlite
import tests



# путь к файлу excel - jobs_cost.xlsx
jobs_cost_file_excel = "jobs_cost.xlsx"

# путь к файлу базы данных - jobs_cost.db
jobs_cost_file_db = "jobs_cost.db"

excel_to_sqlite.create_database_structure(jobs_cost_file_db)
excel_to_sqlite.import_from_excel(jobs_cost_file_excel, jobs_cost_file_db)

print("\nФасадные работы:")
print(tests.get_works_by_category(jobs_cost_file_db, "Фасадные работы").head())

print("\nКровельные работы:")
print(tests.get_works_by_category(jobs_cost_file_db, "Кровельные работы").head())

print("\nЭлектромонтажные работы:")
print(tests.get_works_by_category(jobs_cost_file_db, "Электромонтажные работы").head())
