import os
import json
import google.generativeai as genai
from supabase import create_client, Client
import time
import requests
from bs4 import BeautifulSoup

# --- 1. CONEXIONES Y CONFIGURACIÓN ---
def inicializar_servicios():
    url_supabase = os.environ.get("SUPABASE_URL")
    key_supabase = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url_supabase, key_supabase)

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=google_api_key)
    model_ia = genai.GenerativeModel('gemini-1.5-flash')

    print("✅ Conexiones a Supabase y Google IA establecidas.")
    return supabase, model_ia

# --- 2. LA FASE DE PSICOLOGÍA DE MERCADO ---
def crear_biblia_de_ventas(supabase, model_ia, campana_id, que_vendes):
    print("\n🧐 Analizando el mercado para la campaña...")
    response = supabase.table('argumentarios_venta').select('id').eq('campana_id', campana_id).execute()
    if response.data:
        print("✅ La 'Biblia de Ventas' para esta campaña ya existe.")
        return

    print("  -> La 'Biblia de Ventas' no existe. Creándola con la IA...")
    
    prompt_objeciones = f"""
    Actúa como un psicólogo de ventas experto. Para un cliente que vende "{que_vendes}", genera un objeto JSON.
    La clave principal debe ser "objeciones".
    El valor debe ser una lista de 5 objeciones o miedos comunes que un prospecto tendría antes de comprar.
    Cada objeción en la lista debe ser un objeto JSON con dos claves: "dolor_clave" (un identificador corto en mayúsculas, ej: 'MIEDO_COSTOS') y "descripcion_dolor" (la preocupación del cliente en una frase).
    Genera únicamente el objeto JSON.
    """
    try:
        response_ia = model_ia.generate_content(prompt_objeciones)
        json_text = response_ia.text.strip().replace('```json', '').replace('```', '')
        objeciones = json.loads(json_text)['objeciones']
        print(f"  -> IA ha identificado {len(objeciones)} dolores principales.")
    except Exception as e:
        print(f"❌ Error al identificar objeciones con la IA: {e}")
        return

    for objecion in objeciones:
        print(f"    -> Creando argumentario para: {objecion['dolor_clave']}")
        prompt_argumentario = f"""
        Actúa como un copywriter de ventas de élite.
        El producto de tu cliente es: "{que_vendes}".
        La objeción o dolor del prospecto es: "{objecion['descripcion_dolor']}".
        Redacta un argumentario de venta poderoso y empático que derribe esta objeción específica, ofreciendo el producto como la solución.
        """
        response_arg = model_ia.generate_content(prompt_argumentario)
        
        supabase.table('argumentarios_venta').insert({
            'campana_id': campana_id, 'dolor_clave': objecion['dolor_clave'],
            'descripcion_dolor': objecion['descripcion_dolor'], 'argumentario_solucion': response_arg.text
        }).execute()
    print("✅ 'Biblia de Ventas' creada y guardada en la base de datos.")

# --- 3. ANÁLISIS INDIVIDUAL (aún no lo usamos, pero lo dejamos listo) ---
def analizar_sitio_web(url_sitio):
    # En el futuro, aquí pondremos la lógica para analizar la web de cada prospecto.
    pass

# --- EL PUNTO DE ENTRADA: main() ---
def main():
    ID_CAMPANA_ACTUAL = 1
    QUE_VENDE_EL_CLIENTE = "Servicios de construcción de lujo para viviendas y hoteles."

    print("--- INICIO DE MISIÓN DEL ANALISTA PSICÓLOGO v2.0 ---")
    supabase, model_ia = inicializar_servicios()
    crear_biblia_de_ventas(supabase, model_ia, ID_CAMPANA_ACTUAL, QUE_VENDE_EL_CLIENTE)

    print("\n🔍 Buscando prospectos 'cazados' para calificar...")
    response = supabase.table('prospectos').select('*').eq('estado_prospecto', 'cazado').limit(10).execute()

    if not response.data:
        print("✅ No hay nuevos prospectos para analizar.")
        return

    prospectos_a_analizar = response.data
    for prospecto in prospectos_a_analizar:
        supabase.table('prospectos').update({
            'estado_prospecto': 'analizado_calificado'
        }).eq('prospecto_id', prospecto['prospecto_id']).execute()
        print(f"  -> ✅ Calificado: {prospecto['nombre_negocio']}")
        time.sleep(0.5)

    print("\n🎉 ¡MISIÓN DEL ANALISTA PSICÓLOGO COMPLETADA!")

if __name__ == "__main__":
    main()
# --- Ejecutamos la función principal en un bucle infinito ---
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ocurrió un error en el ciclo principal: {e}")
        
        # El trabajador se "duerme" por 1 hora antes de volver a buscar trabajo.
        # En el futuro, el Orquestador lo despertará directamente.
        print("\nAnalista en modo de espera por 1 hora...")
        time.sleep(3600)
