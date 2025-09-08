import os, json, time, requests
from bs4 import BeautifulSoup
from supabase import create_client
import google.generativeai as genai

def inicializar_servicios():
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model_ia = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Conexiones a Supabase y Google IA establecidas.")
    return supabase, model_ia

def crear_biblia_de_ventas(supabase, model_ia, campana):
    print("\n🧐 Analizando el mercado para la campaña...")
    response = supabase.table('argumentarios_venta').select('id').eq('campana_id', campana['id']).execute()
    if response.data:
        print("✅ La 'Biblia de Ventas' para esta campaña ya existe.")
        return

    print("  -> Creando 'Biblia de Ventas' con la IA...")
    criterios = json.loads(campana['criterio_busqueda'])
    prompt_objeciones = f'Actúa como un psicólogo de ventas. Para un cliente que vende "{criterios["que_vendes"]}", genera un JSON con una lista de 5 objeciones comunes. Cada objeción debe tener "dolor_clave" y "descripcion_dolor". Genera solo el JSON.'
    try:
        response_ia = model_ia.generate_content(prompt_objeciones)
        json_text = response_ia.text.strip().replace('```json', '').replace('```', '')
        objeciones = json.loads(json_text)['objeciones']
    except Exception as e:
        print(f"❌ Error al identificar objeciones: {e}")
        return

    for objecion in objeciones:
        prompt_argumentario = f'Actúa como un copywriter de élite. El producto es "{criterios["que_vendes"]}". La objeción es "{objecion["descripcion_dolor"]}". Redacta un argumentario que derribe esta objeción.'
        response_arg = model_ia.generate_content(prompt_argumentario)
        supabase.table('argumentarios_venta').insert({'campana_id': campana['id'], 'dolor_clave': objecion['dolor_clave'], 'descripcion_dolor': objecion['descripcion_dolor'], 'argumentario_solucion': response_arg.text}).execute()
    print("✅ 'Biblia de Ventas' creada.")

def main():
    print("--- INICIO DE MISIÓN DEL ANALISTA PSICÓLOGO ---")
    supabase, model_ia = inicializar_servicios()

    # Buscamos una campaña en estado 'analizando'
    response_campana = supabase.table('campanas').select('*').eq('estado_campana', 'analizando').limit(1).execute()
    if not response_campana.data:
        print("No hay campañas activas para analizar.")
        return

    campana_actual = response_campana.data[0]
    crear_biblia_de_ventas(supabase, model_ia, campana_actual)

    print("\n🔍 Buscando prospectos 'cazados' para calificar...")
    response_prospectos = supabase.table('prospectos').select('*').eq('estado_prospecto', 'cazado').eq('campana_id', campana_actual['id']).limit(10).execute()
    if not response_prospectos.data:
        print("✅ No hay nuevos prospectos para analizar en esta campaña.")
        # Si no hay más prospectos, marcamos la campaña como lista para persuadir
        supabase.table('campanas').update({'estado_campana': 'persuadiendo'}).eq('id', campana_actual['id']).execute()
        return

    for prospecto in response_prospectos.data:
        # Aquí iría la lógica de análisis individual (web, etc.)
        supabase.table('prospectos').update({'estado_prospecto': 'analizado_calificado'}).eq('prospecto_id', prospecto['prospecto_id']).execute()
        print(f"  -> ✅ Calificado: {prospecto['nombre_negocio']}")
    
    print("\n🎉 ¡MISIÓN DEL ANALISTA COMPLETADA!")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ocurrió un error en el ciclo principal del Analista: {e}")
        
        print(f"\nAnalista en modo de espera por 1 hora...")
        time.sleep(3600)
