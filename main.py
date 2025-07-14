import os
from supabase import create_client, Client
from dotenv import load_dotenv
import getters


load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# cat_name = 'Утеплители'
# getters.get_materials_by_category(supabase, cat_name)

# cat_name = 'Барабашка'
# getters.get_materials_by_category(supabase, cat_name)

# cat_name = 'Напольные покрытия'
# getters.get_works_by_category(supabase, cat_name)

# response = supabase.table('works').select('price').eq('name', 'Покраска фасада в два слоя').execute()
# print(response.data[0])

substr = 'утЕплИтеЛь'
getters.get_materials_by_substr(supabase, substr)

substr = 'Покраска'
getters.get_works_by_substr(supabase, substr)

# response = supabase.table('works').select('*').ilike('name', f'%{str}%').execute()
# print(response.data)
