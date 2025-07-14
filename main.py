import os
from supabase import create_client, Client
from dotenv import load_dotenv



load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

cat_name = 'Утеплители'
getters.get_materials_by_category(supabase, cat_name)

# response = supabase.table('works').select('price').eq('name', 'Покраска фасада в два слоя').execute()
# print(response.data[0])
#
str = 'Покраска'
response = supabase.table('works').select('*').ilike('name', f'%{str}%').execute()
print(response.data)
