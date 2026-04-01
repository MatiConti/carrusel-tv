import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Cargar configuración y secretos ocultos
load_dotenv()

# ==========================================
# CONFIGURACIÓN DE REPORTES Y CREDENCIALES
# ==========================================
REPORTES = [
    {
        # URL 1: DevExpress Dashboard
        "url": os.getenv("REPORT_1_URL"),
        "usuario": os.getenv("REPORT_1_USER"),
        "clave": os.getenv("REPORT_1_PASS"),
        "ir_a_post_login": os.getenv("REPORT_1_POST") or None, 
        "es_reporte_griba": True # Bandera para aplicar lógica de maximización especializada
    },
    {
        # URL 2: SGS Pharmacenter
        "url": os.getenv("REPORT_2_URL"),
        "usuario": os.getenv("REPORT_2_USER"),
        "clave": os.getenv("REPORT_2_PASS"),
        "ir_a_post_login": os.getenv("REPORT_2_POST") or None,
        "es_reporte_griba": False
    }
]

INTERVALO_SEGUNDOS = int(os.getenv("INTERVALO_SEGUNDOS", 60))
# ==========================================

from selenium.webdriver.common.action_chains import ActionChains

def maximizar_reporte_dt_griba(driver):
    """ Función agresiva que simula el ratón para revelar y hacer un CLICK FÍSICO REAL en el botón Ampliar.
        (DevExtreme suele bloquear los clicks inyectados por JS porque busca el evento de PointerDown del sistema). """
    print(" -> Empezando proceso simulado de ratón para AMPLIAR el reporte...")
    tiempo_maximo = 25 
    inicio = time.time()
    
    while time.time() - inicio < tiempo_maximo:
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            marcos = [driver.current_window_handle] + iframes

            for marco in marcos:
                if marco != driver.current_window_handle:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(marco)
                
                # 1. Engañar a DevExpress inyectando un "Falso Ratón" directamente al DOM
                # A diferencia de Windows, Xvfb a veces ignora el mouse nativo, así que 
                # obligamos al sistema a creer que pasamos el mouse por los recuadros
                script_hover = """
                    var tarjetas = document.querySelectorAll('.dx-dashboard-item, .dx-dashboard-group-item');
                    for (var i = 0; i < tarjetas.length; i++) {
                        tarjetas[i].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
                        tarjetas[i].dispatchEvent(new MouseEvent('mouseenter', {bubbles: true}));
                        tarjetas[i].dispatchEvent(new PointerEvent('pointerover', {bubbles: true}));
                        tarjetas[i].dispatchEvent(new PointerEvent('pointerenter', {bubbles: true}));
                    }
                """
                driver.execute_script(script_hover)
                time.sleep(1) # Le damos a DevExpress 1 segundo para la animación de dibujar el botón

                # 2. PLAN A (y mejor plan para Linux Xvfb): Inyección Javascript directa y brutal 
                # Ahora que DevExpress fue engañado y dibujó los botones, hacemos el click
                script_JS = """
                    // 1. Estrategia Estrella: Buscar por el Tooltip exacto que DevExpress genera (Inglés y Español)
                    var elementos_por_titulo = document.querySelectorAll('[title*="full screen" i], [title*="Full screen" i], [aria-label*="full screen" i], [title*="pantalla completa" i], [title*="maximizar" i], [aria-label*="maximizar" i], [title*="ampliar" i]');
                    if(elementos_por_titulo.length > 0) {
                        elementos_por_titulo[0].style.display = 'block';
                        elementos_por_titulo[0].style.visibility = 'visible';
                        elementos_por_titulo[0].click();
                        return true;
                    }
                    
                    // 2. Si falla el titulo, buscar los SVG que tienen los diagramas
                    var svgs = document.querySelectorAll('svg');
                    for (var j = 0; j < svgs.length; j++) {
                        var html = (svgs[j].innerHTML || '').toLowerCase();
                        if (html.indexOf('fullscreen') !== -1 || html.indexOf('full screen') !== -1 || html.indexOf('maximize') !== -1 || html.indexOf('pantalla completa') !== -1 || html.indexOf('maximizar') !== -1 || html.indexOf('ampliar') !== -1) {
                            var botonPadre = svgs[j].closest('.dx-dashboard-item-action-button') || svgs[j].parentNode;
                            botonPadre.style.display = 'block';
                            botonPadre.style.visibility = 'visible';
                            botonPadre.click();
                            return true;
                        }
                    }
                    // 3. Si fallan los SVG, buscamos a secas las clases que usa DevExpress
                    var btns = document.querySelectorAll('.dx-dashboard-maximize-button, .dx-dashboard-fullscreen-button, .dx-dashboard-item-maximize-button');
                    if(btns.length > 0) {
                        btns[0].style.display = 'block';
                        btns[0].style.visibility = 'visible';
                        btns[0].click();
                        return true;
                    }
                    return false;
                """
                if driver.execute_script(script_JS):
                    print(f" -> ¡Reporte de Griba AMPLIADO agresivamente con JS! (tardó {round(time.time() - inicio)}s)")
                    driver.switch_to.default_content()
                    return

                # PLAN B: (Fallback) Usamos Selenium normal nativo
                btns = driver.find_elements(By.CSS_SELECTOR, ".dx-dashboard-maximize-button, .dx-dashboard-fullscreen-button, .dx-dashboard-item-maximize-button")
                if btns:
                    try:
                        driver.execute_script("arguments[0].style.display='block'; arguments[0].style.visibility='visible';", btns[0])
                        btns[0].click()
                        print(f" -> ¡Reporte de Griba AMPLIADO (Nativo)! (tardó {round(time.time() - inicio)}s)")
                        driver.switch_to.default_content()
                        return
                    except: pass
                    
        except Exception as e:
            pass # Ignorar errores
        finally:
            driver.switch_to.default_content()
            
        time.sleep(1)
        
    print(f" -> Aviso: Han pasado {tiempo_maximo}s y no se pudo auto-clickear el botón de las flechas.")


def auto_login(driver, reporte):
    print(f"Abriendo: {reporte['url'][:50]}...")
    driver.get(reporte['url'])
    time.sleep(5) 
    
    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
        input_usuario = None
        input_clave = None
        
        for inp in inputs:
            tipo = inp.get_attribute("type")
            if tipo in ["text", "email", "", None] and inp.is_displayed():
                if not input_usuario:
                    input_usuario = inp
            elif tipo == "password" and inp.is_displayed():
                input_clave = inp
                
        if input_usuario and input_clave:
            input_usuario.send_keys(reporte["usuario"])
            time.sleep(1)
            input_clave.send_keys(reporte["clave"])
            time.sleep(1)
            input_clave.send_keys(Keys.RETURN)
            print(" -> Login enviado.")
        else:
            print(" -> Aviso: No se detectaron campos de login en esta pantalla.")
            
    except Exception as e:
        print(f" -> Error en login: {e}")
    
    time.sleep(8)
    
    if reporte.get("ir_a_post_login"):
        print(f" -> Forzando redirección directa a la URL deseada...")
        driver.get(reporte['ir_a_post_login'])
        time.sleep(8)
    
    # Si es el reporte de GRIBA buscar incansablemente las cuatro flechas de ampliar
    if reporte.get("es_reporte_griba"):
        maximizar_reporte_dt_griba(driver)


def main():
    print("Iniciando Modo TV Inquebrantable...")
    
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # IMPORTANTE: Desactivar los popups de Chrome de manera agresiva.
    # El modo incógnito es la ÚNICA manera 100% garantizada de que Google Chrome 
    # no muestre el cartel de "Contraseña Vulnerada" o "Guardar Contraseña".
    chrome_options.add_argument("--incognito")
    
    # Mantenemos las prefs extras por redundancia
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "safebrowsing.enabled": False
    })
    chrome_options.add_argument("--disable-features=PasswordLeakDetection")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--window-size=1920,1080") # Fuerza interna full-HD
    chrome_options.add_argument("--kiosk") # Esto garantiza el FullScreen 100%
    chrome_options.add_argument("--lang=es-AR") # Fuerza fechas en 24h y en Español de Argentina
    
    print("Conectando al contenedor 'chrome' centralizado en Docker...")
    max_reintentos = 15
    driver = None
    for i in range(max_reintentos):
        try:
            driver = webdriver.Remote(command_executor="http://chrome:4444", options=chrome_options)
            print("¡Conectado al Chrome Virtual de Docker exitosamente!")
            break
        except Exception as e:
            if i == max_reintentos - 1:
                print("Error crítico al conectar con Chrome en Docker:", e)
                return
            print(f"Esperando a que el contenedor de Chrome inicie... ({i+1}/{max_reintentos})")
            time.sleep(2)
            
    if not driver:
        return

    # 1. Hacer login en la primera pestaña
    auto_login(driver, REPORTES[0])
    
    # 2. Abrir la segunda pestaña
    for reporte in REPORTES[1:]:
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        auto_login(driver, reporte)

    print("\n\nComenzando la rotación Infinita cada 60s...")
    
    tabs = driver.window_handles
    tab_index = 0
    driver.switch_to.window(tabs[0])

    while True:
        try:
            driver.switch_to.window(tabs[tab_index])
            time.sleep(INTERVALO_SEGUNDOS)
            tab_index = (tab_index + 1) % len(tabs)
            
        except Exception as e:
            print(f"La rotación se detuvo o el navegador fue cerrado manualmete.")
            break

if __name__ == "__main__":
    main()
