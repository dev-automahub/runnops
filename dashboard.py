import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import dateutil.parser
import os
import numpy as np
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import altair as alt

# Configuração da Página
st.set_page_config(page_title="L3 Triathlon Team", layout="wide")

# Título
st.title("🏃‍♂️ Painel de Análise do Aluno: Oswaldo Junior")
st.markdown("Visualize suas atividades extraídas do Garmin Connect (Arquivos .TCX)")

# --- FUNÇÃO DE LEITURA DO ARQUIVO TCX ---
def parse_tcx(file_content):
    try:
        tree = ET.parse(file_content)
        root = tree.getroot()
    except Exception as e:
        st.error(f"Erro ao ler XML: {e}")
        return pd.DataFrame()

    # Namespaces EXATOS do Garmin (Obrigatório para funcionar corretamente)
    ns = {
        'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
        'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
    }

    data = []
    
    # Busca todas as atividades
    activities = root.findall('.//ns:Activity', ns)
    if not activities:
        st.warning("Nenhuma tag 'Activity' encontrada. Verifique se o arquivo é um TCX válido.")

    for activity in activities:
        sport = activity.get('Sport')
        # Tenta pegar ID da atividade
        id_node = activity.find('ns:Id', ns)
        activity_id = id_node.text if id_node is not None else "Desconhecido"

        for lap in activity.findall('.//ns:Lap', ns):
            for trackpoint in lap.findall('.//ns:Trackpoint', ns):
                point = {'Sport': sport, 'ActivityId': activity_id}

                # 1. TEMPO
                time_elem = trackpoint.find('ns:Time', ns)
                if time_elem is not None:
                    point['Time'] = dateutil.parser.parse(time_elem.text)

                # 2. HEART RATE
                hr_elem = trackpoint.find('.//ns:HeartRateBpm/ns:Value', ns)
                if hr_elem is not None:
                    point['HeartRate'] = int(hr_elem.text)

                # 3. POSIÇÃO (CRÍTICO PARA O MAPA)
                position = trackpoint.find('ns:Position', ns)
                if position is not None:
                    lat = position.find('ns:LatitudeDegrees', ns)
                    lon = position.find('ns:LongitudeDegrees', ns)
                    if lat is not None and lon is not None:
                        try:
                            point['Latitude'] = float(lat.text)
                            point['Longitude'] = float(lon.text)
                        except ValueError:
                            pass

                # 4. ALTITUDE E DISTÂNCIA
                alt = trackpoint.find('ns:AltitudeMeters', ns)
                dist = trackpoint.find('ns:DistanceMeters', ns)
                if alt is not None: point['Altitude'] = float(alt.text)
                if dist is not None: point['Distance'] = float(dist.text)

                # 5. EXTENSÕES (CADENCIA, WATTS, SPEED)
                extensions = trackpoint.find('ns:Extensions', ns)
                if extensions is not None:
                    tpx = extensions.find('ns3:TPX', ns)
                    if tpx is not None:
                        speed = tpx.find('ns3:Speed', ns)
                        cad = tpx.find('ns3:RunCadence', ns)
                        watts = tpx.find('ns3:Watts', ns)
                        
                        if speed is not None: point['Speed'] = float(speed.text)
                        if cad is not None: point['Cadence'] = int(cad.text)
                        if watts is not None: point['Watts'] = int(watts.text)

                data.append(point)

    return pd.DataFrame(data)

# --- SIDEBAR PARA SELEÇÃO DE ARQUIVOS ---
st.sidebar.header("Carregar Dados")

# 1. Tenta pegar via Upload (mantivemos isso para a variável existir)
uploaded_file = st.sidebar.file_uploader("Arraste seu arquivo .TCX aqui", type=['tcx'])

# 2. Configuração da pasta local
folder_path = './' # O ponto significa a pasta atual onde o script está
files_in_folder = [f for f in os.listdir(folder_path) if f.endswith('.tcx')] if os.path.exists(folder_path) else []


# Cria o seletor apenas se houver arquivos na pasta
selected_local_file = "Nenhum"
if files_in_folder:
    selected_local_file = st.sidebar.selectbox("Ou selecione da pasta local:", ["Nenhum"] + files_in_folder)
else:
    st.sidebar.warning(f"Nenhum arquivo .tcx encontrado na pasta '{folder_path}'")

# --- LÓGICA DE CARREGAMENTO ---
df = pd.DataFrame()

# Prioridade 1: Arquivo carregado via Upload
if uploaded_file is not None:
    df = parse_tcx(uploaded_file)

# Prioridade 2: Arquivo da pasta local (se nenhum upload foi feito)
elif selected_local_file != "Nenhum":
    file_full_path = os.path.join(folder_path, selected_local_file)
    try:
        # Abrimos o arquivo local e passamos para a função
        with open(file_full_path, 'r', encoding='utf-8') as f:
            # O parse_tcx espera um objeto de arquivo ou string, vamos passar o arquivo aberto
            df = parse_tcx(f)
    except Exception as e:
        st.error(f"Erro ao ler arquivo local: {e}")

# --- PROCESSAMENTO E VISUALIZAÇÃO ---
if not df.empty:
    # Prepara dados adicionais
    start_time = df['Time'].iloc[0]
    df['Elapsed_Minutes'] = (df['Time'] - start_time).dt.total_seconds() / 60
    
    # Pace (min/km) - Tratamento de erros de divisão por zero
    df['Pace_decimal'] = df.apply(lambda row: (1000 / row['Speed'] / 60) if (pd.notnull(row.get('Speed')) and row['Speed'] > 0) else np.nan, axis=1)
    df['Pace_decimal'] = df['Pace_decimal'].replace([np.inf, -np.inf], np.nan)
    df['Pace_decimal'] = df['Pace_decimal'].clip(upper=20) # Limita a 20 min/km para gráfico não estourar

    # Métricas de Resumo (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_km = df['Distance'].max() / 1000
        st.metric("Distância Total", f"{total_km:.2f} km")
    with col2:
        duration = df['Elapsed_Minutes'].max()
        st.metric("Duração", f"{duration:.0f} min")
    with col3:
        avg_hr = df['HeartRate'].mean()
        st.metric("Frequência Cardíaca Média", f"{avg_hr:.0f} bpm")
    with col4:
        if 'Watts' in df.columns:
            avg_pwr = df['Watts'].mean()
            st.metric("Potência Média", f"{avg_pwr:.0f} W")
        else:
            st.metric("Potência Média", "N/A")

    st.divider()

# --- ÁREA DE DEBUG (Pode remover depois) ---
    # st.write("### Debug dos Dados")
    # if 'Latitude' in df.columns:
        # gps_count = df['Latitude'].notna().sum()
        # st.write(f"Pontos com GPS encontrados: {gps_count}")
        # if gps_count > 0:
            # st.write("Exemplo de dados:", df[['Time', 'Latitude', 'Longitude']].dropna().head())
        # else:
            # st.error("A coluna Latitude existe, mas está vazia!")
    # else:
        # st.error("A coluna Latitude NÃO foi criada. O parser não encontrou as tags.")
    # st.divider()
# -------------------------------------------


# --- GRÁFICOS (LAYOUT VERTICAL) ---
    
    # 1. MAPA DE CALOR (Full Width)
    st.subheader("🗺️ Mapa de Calor da Rota")
    
    # Verifica GPS
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        # Prepara dataframe limpo e busca métricas disponíveis
        cols_to_check = ['Latitude', 'Longitude']
        if 'HeartRate' in df.columns: cols_to_check.append('HeartRate')
        if 'Speed' in df.columns: cols_to_check.append('Speed')
        
        # Limpa dados nulos apenas nas colunas essenciais
        route_data = df[cols_to_check].dropna(subset=['Latitude', 'Longitude'])
        # Remove pontos (0,0)
        route_data = route_data[(route_data['Latitude'] != 0) & (route_data['Longitude'] != 0)]
        
        if not route_data.empty:
            # Configura Mapa Base
            mid_lat = route_data['Latitude'].mean()
            mid_lon = route_data['Longitude'].mean()
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=14, tiles='OpenStreetMap')

            # Define Métrica para Colorir (Prioridade: FC > Velocidade)
            points = route_data[['Latitude', 'Longitude']].values.tolist()
            metric_values = None
            
            if 'HeartRate' in route_data.columns:
                metric_values = route_data['HeartRate']
                label_legend = "Frequência Cardíaca (bpm)"
                colors_scale = ['lightblue', 'green', 'yellow', 'orange', 'red']
            elif 'Speed' in route_data.columns:
                metric_values = route_data['Speed']
                label_legend = "Velocidade (m/s)"
                colors_scale = ['red', 'yellow', 'green', 'blue'] 
            
            # Desenha a Rota
            if metric_values is not None:
                colormap = cm.LinearColormap(
                    colors=colors_scale,
                    vmin=metric_values.min(),
                    vmax=metric_values.max()
                )
                colormap.caption = label_legend
                
                folium.ColorLine(
                    positions=points,
                    colors=metric_values,
                    colormap=colormap,
                    weight=5, # Linha um pouco mais grossa
                    opacity=0.9
                ).add_to(m)
                
                m.add_child(colormap)
            else:
                folium.PolyLine(points, color="red", weight=5).add_to(m)

            # Marcadores Início/Fim
            folium.Marker(points[0], popup="Início", icon=folium.Icon(color='green', icon='play')).add_to(m)
            folium.Marker(points[-1], popup="Fim", icon=folium.Icon(color='black', icon='stop')).add_to(m)
            
            # Ajusta Zoom
            sw = route_data[['Latitude', 'Longitude']].min().values.tolist()
            ne = route_data[['Latitude', 'Longitude']].max().values.tolist()
            m.fit_bounds([sw, ne])

            # Exibe o mapa usando a largura total do container
            st_folium(m, use_container_width=True, height=500)
        else:
            st.warning("Sem dados de GPS válidos para exibir.")
    else:
        st.error("Colunas de GPS não encontradas.")

    st.divider() # Uma linha divisória elegante

    # 2. PERFIL DE ELEVAÇÃO (Abaixo do Mapa)
    st.subheader("⛰️ Perfil de Elevação")
    
    if 'Altitude' in df.columns and 'Distance' in df.columns:
        # Cria um gráfico de área para ficar mais bonito visualmente
        chart_data = df[['Distance', 'Altitude']].set_index('Distance')
        st.area_chart(chart_data, color="#808080") # Cinza para lembrar montanha/rocha
    else:
        st.info("Dados de elevação não disponíveis.")

# ---

# ... (Código anterior do Mapa e Elevação) ...

    # --- GRÁFICOS DETALHADOS (LAYOUT VERTICAL) ---

# 3. FREQUÊNCIA CARDÍACA & ZONAS
    st.divider()
    st.subheader("❤️ Frequência Cardíaca")
    
    if 'HeartRate' in df.columns:
        # 3.1 Gráfico de Linha (Evolução Temporal)
        st.line_chart(df.set_index('Elapsed_Minutes')['HeartRate'], color="#FF0000")
        
        avg_hr = df['HeartRate'].mean()
        max_hr = df['HeartRate'].max()
        st.caption(f"Média: {avg_hr:.0f} bpm | Máxima: {max_hr} bpm")

        # 3.2 Distribuição em Zonas (Karvonen do atleta)
        st.markdown("#### 📊 Tempo nas Zonas (Karvonen)")

        # Zonas Karvonen do atleta — ajustar conforme perfil:
        # FCalvo = FCrep + (% × FCR), onde FCR = FCmáx − FCrep
        # Recalibrado 16/05/2026 com dados oficiais do Garmin Connect
        FC_MAX = 175   # auto-detected pelo Garmin (era Tanaka 170)
        FC_REP = 49    # medida atual (era 51)
        FCR = FC_MAX - FC_REP  # 126 bpm

        zones = [
            (FC_REP + 0.50 * FCR, FC_REP + 0.60 * FCR, "Z1", "Recuperação",      "#A9A9A9"),
            (FC_REP + 0.60 * FCR, FC_REP + 0.70 * FCR, "Z2", "Aeróbico Base",    "#32CD32"),
            (FC_REP + 0.70 * FCR, FC_REP + 0.80 * FCR, "Z3", "Limiar Aeróbio",   "#FFD700"),
            (FC_REP + 0.80 * FCR, FC_REP + 0.90 * FCR, "Z4", "Limiar Anaeróbio", "#FF8C00"),
            (FC_REP + 0.90 * FCR, FC_MAX,              "Z5", "VO2máx",           "#FF0000"),
        ]
        st.caption(f"FCmáx {FC_MAX} | FCrep {FC_REP} | FCR {FCR} — zonas: " +
                   " | ".join([f"{z[2]} {int(z[0])}-{int(z[1])}" for z in zones]))

        zone_counts = []
        
        # Calcula o tempo em CADA zona (mesmo que seja zero)
        for min_hr, max_hr, label, name, color in zones:
            # Conta quantos pontos (segundos) caem nesta faixa
            count = df[(df['HeartRate'] >= min_hr) & (df['HeartRate'] < max_hr)].shape[0]
            minutes = count / 60 
            
            # Adiciona à lista SEMPRE (para o gráfico mostrar todas as zonas)
            zone_counts.append({
                "Zona": label, 
                "Nome": name, 
                "Minutos": minutes, 
                "Cor": color, 
                "Range": f"{int(min_hr)}-{int(max_hr)}"
            })

        # Cria o gráfico de zonas
        df_zones = pd.DataFrame(zone_counts)
        
        c_zones = alt.Chart(df_zones).mark_bar().encode(
            x=alt.X('Zona', sort=['Z1', 'Z2', 'Z3', 'Z4', 'Z5'], title='Zona de Esforço'),
            y=alt.Y('Minutos', title='Tempo (min)'),
            color=alt.Color('Cor', scale=None), # Usa as cores definidas manualmente
            tooltip=['Zona', 'Nome', 'Range', alt.Tooltip('Minutos', format='.1f')]
        ).properties(height=250)
        
        # Adiciona rótulos de texto (valor em minutos) em cima das barras
        text = c_zones.mark_text(dy=-5, color='black').encode(
            text=alt.Text('Minutos', format='.1f')
        )

        st.altair_chart(c_zones + text, use_container_width=True)

    else:
        st.info("Dados de Frequência Cardíaca não disponíveis.")

    # 4. POTÊNCIA (WATTS)
    if 'Watts' in df.columns:
        st.divider()
        st.subheader("⚡ Potência (Watts)")
        # Gráfico Roxo
        st.line_chart(df.set_index('Elapsed_Minutes')['Watts'], color="#800080")
        st.caption(f"Média: {df['Watts'].mean():.0f} W | Máxima: {df['Watts'].max()} W")

    # 5. CADÊNCIA
    if 'Cadence' in df.columns:
        st.divider()
        st.subheader("👣 Cadência (Passos por minuto)")
        # Gráfico Laranja
        st.line_chart(df.set_index('Elapsed_Minutes')['Cadence'], color="#FFA500")
        st.caption(f"Média: {df['Cadence'].mean():.0f} spm")

# 6. RITMO (PACE) - Com Eixo Invertido
    st.divider()
    st.subheader("⏱️ Ritmo (Pace - min/km)")
    
    if 'Pace_decimal' in df.columns:
        # Prepara os dados para o Altair (remove NaNs para não quebrar o gráfico)
        pace_data = df[['Elapsed_Minutes', 'Pace_decimal']].dropna()
        
        # Cria o gráfico com Altair
        c = alt.Chart(pace_data).mark_line(color='#008000').encode(
            x=alt.X('Elapsed_Minutes', title='Tempo (min)'),
            y=alt.Y('Pace_decimal', 
                    title='Min/Km', 
                    scale=alt.Scale(reverse=True, zero=False) # <--- O SEGREDO: reverse=True inverte o eixo
                   ),
            tooltip=[
                alt.Tooltip('Elapsed_Minutes', title='Tempo (min)', format='.1f'),
                alt.Tooltip('Pace_decimal', title='Pace (decimal)', format='.2f')
            ]
        ).interactive() # Permite zoom e pan
        
        st.altair_chart(c, use_container_width=True)
        
        # Estatísticas (mantidas igual)
        avg_pace_dec = df['Pace_decimal'].mean()
        mins = int(avg_pace_dec)
        secs = int((avg_pace_dec - mins) * 60)
        st.caption(f"Ritmo Médio: {mins}:{secs:02d} /km")
        
    # --- FIM DO DASHBOARD ---
    st.divider()
    st.success("Análise da atividade concluída.")