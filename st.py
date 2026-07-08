import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from streamlit import session_state as state
from datetime import datetime
import streamlit.components.v1 as components

# =====================================================
# PROCESSAMENTO DO ARQUIVO - DADOS DE VENTOS
# =====================================================

def processar_arquivo(arquivo):
    """
    Processa o arquivo de dados
    Formato: timestamp|dados
    Extrai pacotes de vento (node=3, type=2) e ondas (node=1, type=1)
    """
    linhas = arquivo.decode('utf-8').split('\n')
    
    dados_vento = []
    dados_onda = []
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            continue
        
        # Separar timestamp do resto (usando | como separador)
        if '|' in linha:
            partes = linha.split('|')
            timestamp = partes[0]
            resto = partes[1] if len(partes) > 1 else ''
        else:
            partes = linha.split(',')
            timestamp = partes[0] if len(partes) > 0 else ''
            resto = ','.join(partes[1:]) if len(partes) > 1 else ''
        
        # Separar os dados por vírgula
        valores = resto.split(',')
        
        if len(valores) < 5:
            continue
        
        try:
            node_val = valores[1].strip() if len(valores) > 1 else ""
            type_val = valores[2].strip() if len(valores) > 2 else ""
            
            try:
                node_int = int(node_val)
                type_int = int(type_val)
            except:
                continue
            
            # Pacote de VENTO (node=3, type=2)
            if node_int == 3 and type_int == 2 and len(valores) >= 9:
                try:
                    velocidade = float(valores[5]) if len(valores) > 5 and valores[5].strip() else None
                    direcao = float(valores[6]) if len(valores) > 6 and valores[6].strip() else None
                    
                    if velocidade is not None:
                        dados_vento.append({
                            'timestamp': timestamp,
                            'velocidade_vento': velocidade,
                            'direcao_vento': direcao if direcao is not None else 0,
                        })
                except Exception as e:
                    continue
            
            # Pacote de ONDA (node=1, type=1)
            elif node_int == 1 and type_int == 1 and len(valores) >= 50:
                try:
                    leituras_A = []
                    for i in range(8, 28):
                        if i < len(valores) and valores[i].strip():
                            try:
                                val = float(valores[i])
                                if 1000 < val < 3000:
                                    leituras_A.append(val)
                            except:
                                pass
                    
                    leituras_B = []
                    for i in range(28, 48):
                        if i < len(valores) and valores[i].strip():
                            try:
                                val = float(valores[i])
                                if 1000 < val < 3000:
                                    leituras_B.append(val)
                            except:
                                pass
                    
                    if leituras_A and leituras_B:
                        amplitude_A = max(leituras_A) - min(leituras_A)
                        amplitude_B = max(leituras_B) - min(leituras_B)
                        amplitude_media_ondas = (amplitude_A + amplitude_B) / 2
                        valor_bruto = amplitude_media_ondas
                    else:
                        valor_bruto = None
                    
                    if valor_bruto is not None:
                        dados_onda.append({
                            'timestamp': timestamp,
                            'valor_bruto': valor_bruto,  # Valor em mm
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            continue
    
    return dados_vento, dados_onda

def criar_dataframes(dados_vento, dados_onda):
    """Cria DataFrames com os dados"""
    df_vento = pd.DataFrame(dados_vento) if dados_vento else pd.DataFrame()
    df_onda = pd.DataFrame(dados_onda) if dados_onda else pd.DataFrame()
    
    if not df_vento.empty:
        df_vento.insert(0, 'indice', range(1, len(df_vento) + 1))
        try:
            df_vento['datetime'] = pd.to_datetime(df_vento['timestamp'])
        except:
            df_vento['datetime'] = None
    
    if not df_onda.empty:
        df_onda.insert(0, 'indice', range(1, len(df_onda) + 1))
        # Converter mm para metros (dividir por 1000)
        df_onda['valor_bruto'] = df_onda['valor_bruto'] / 1000
        try:
            df_onda['datetime'] = pd.to_datetime(df_onda['timestamp'])
        except:
            df_onda['datetime'] = None
    
    return df_vento, df_onda

def formatar_duracao(segundos):
    """Formata a duração em segundos para um formato legível"""
    if segundos < 60:
        return f"{segundos:.1f} segundos"
    elif segundos < 3600:
        minutos = segundos / 60
        return f"{minutos:.1f} minutos"
    else:
        horas = segundos / 3600
        return f"{horas:.2f} horas"

# =====================================================
# FUNÇÕES DE PLOTAGEM
# =====================================================

def plotar_grafico_velocidade_vento(df_vento, inicio, fim, cor="#2ca02c", tema_escuro=False):
    """Plota gráfico de velocidade do vento"""
    if df_vento.empty:
        return None
    
    ordem_normal = inicio <= fim
    
    if ordem_normal:
        df_filtrado = df_vento.iloc[inicio:fim+1].dropna(subset=['velocidade_vento']).copy()
    else:
        df_filtrado = df_vento.iloc[fim:inicio+1].dropna(subset=['velocidade_vento']).copy()
        df_filtrado = df_filtrado.sort_values('indice', ascending=False)
    
    if df_filtrado.empty:
        return None
    
    x_valores = df_filtrado['indice'].values
    y_valores = df_filtrado['velocidade_vento'].values
    
    min_val = float(y_valores.min())
    max_val = float(y_valores.max())
    media_geral = float(y_valores.mean())
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if tema_escuro:
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1c1f26')
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(colors='white')
    
    ax.plot(x_valores, y_valores, color=cor, marker='o', markersize=4, linewidth=2)
    
    ax.set_xlabel("Número da Leitura", fontsize=12)
    ax.set_ylabel("Velocidade do Vento (m/s)", fontsize=12)
    
    if len(x_valores) > 20:
        step = max(1, len(x_valores) // 10)
        ticks = x_valores[::step]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(int(t)) for t in ticks], rotation=45, ha='right')
    
    ax.axhline(media_geral, color='red', linestyle='--', linewidth=1, label=f'Média: {media_geral:.2f} m/s')
    ax.legend(loc='upper right')
    
    ax.text(0.02, 0.98, "Unidade: m/s", transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
    
    ax.text(0.98, 0.05, f"Máx: {max_val:.2f} m/s | Mín: {min_val:.2f} m/s", transform=ax.transAxes,
            fontsize=9, horizontalalignment='right', verticalalignment='bottom',
            bbox=dict(facecolor='white', alpha=0.8))
    
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlim(x_valores[0], x_valores[-1])
    
    return fig

def plotar_grafico_onda(df_onda, inicio, fim, cor="#1f77b4", tema_escuro=False):
    """Plota gráfico da altura da onda (já em metros)"""
    if df_onda.empty:
        return None
    
    ordem_normal = inicio <= fim
    
    if ordem_normal:
        df_filtrado = df_onda.iloc[inicio:fim+1].dropna(subset=['valor_bruto']).copy()
    else:
        df_filtrado = df_onda.iloc[fim:inicio+1].dropna(subset=['valor_bruto']).copy()
        df_filtrado = df_filtrado.sort_values('indice', ascending=False)
    
    if df_filtrado.empty:
        return None
    
    x_valores = df_filtrado['indice'].values
    y_valores = df_filtrado['valor_bruto'].values  # Já está em metros
    
    min_val = float(y_valores.min())
    max_val = float(y_valores.max())
    media_geral = float(y_valores.mean())
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if tema_escuro:
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1c1f26')
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(colors='white')
    
    ax.plot(x_valores, y_valores, color=cor, marker='o', markersize=4, linewidth=2)
    ax.fill_between(x_valores, y_valores, alpha=0.2, color=cor)
    
    ax.set_xlabel("Número da Leitura", fontsize=12)
    ax.set_ylabel("Altura da Onda (m)", fontsize=12)
    
    if len(x_valores) > 20:
        step = max(1, len(x_valores) // 10)
        ticks = x_valores[::step]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(int(t)) for t in ticks], rotation=45, ha='right')
    
    ax.axhline(media_geral, color='red', linestyle='--', linewidth=1, label=f'Média: {media_geral:.3f} m')
    ax.legend(loc='upper right')
    
    ax.text(0.02, 0.98, "Unidade: metros (m)", 
            transform=ax.transAxes, fontsize=9, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
    
    ax.text(0.98, 0.05, f"Máx: {max_val:.3f} m | Mín: {min_val:.3f} m", transform=ax.transAxes,
            fontsize=9, horizontalalignment='right', verticalalignment='bottom',
            bbox=dict(facecolor='white', alpha=0.8))
    
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlim(x_valores[0], x_valores[-1])
    
    return fig

def plotar_grafico_radar(df_vento, inicio, fim, cor="#d62728", tema_escuro=False):
    """Plota gráfico radar para direção do vento"""
    if df_vento.empty:
        return None
    
    pontos_cardinais = {
        'N': 'Norte', 'NNE': 'Norte-Nordeste', 'NE': 'Nordeste', 'ENE': 'Leste-Nordeste',
        'E': 'Leste', 'ESE': 'Leste-Sudeste', 'SE': 'Sudeste', 'SSE': 'Sul-Sudeste',
        'S': 'Sul', 'SSW': 'Sul-Sudoeste', 'SW': 'Sudoeste', 'WSW': 'Oeste-Sudoeste',
        'W': 'Oeste', 'WNW': 'Oeste-Noroeste', 'NW': 'Noroeste', 'NNW': 'Norte-Noroeste'
    }
    
    def converter_direcao(grau):
        try:
            grau = float(grau) % 360
            pontos = list(pontos_cardinais.keys())
            return pontos[int((grau / 22.5) + 0.5) % 16]
        except:
            return None
    
    idx_min = min(inicio, fim)
    idx_max = max(inicio, fim)
    
    df_filtrado = df_vento.iloc[idx_min:idx_max+1].copy()
    df_filtrado['Direcao'] = df_filtrado['direcao_vento'].apply(converter_direcao)
    df_filtrado = df_filtrado.dropna(subset=['Direcao'])
    
    if df_filtrado.empty:
        return None
    
    contagem = df_filtrado['Direcao'].value_counts()
    direcoes = list(pontos_cardinais.keys())
    valores = [contagem.get(d, 0) for d in direcoes]
    rotulos = [pontos_cardinais[d] for d in direcoes]
    
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    
    if tema_escuro:
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1c1f26')
        ax.spines['polar'].set_color('white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(colors='white')
    
    theta = np.linspace(0, 2*np.pi, len(direcoes), endpoint=False)
    theta = np.concatenate((theta, [theta[0]]))
    valores = np.concatenate((valores, [valores[0]]))
    
    max_val = max(valores) if len(valores) > 0 else 1
    ax.set_ylim(0, max_val * 1.2)
    for r in np.linspace(0, max_val, 5):
        ax.plot(theta, [r] * len(theta), color='gray', linestyle=':', alpha=0.5)
    
    ax.plot(theta, valores, color=cor, linestyle='-', linewidth=2)
    ax.fill(theta, valores, color=cor, alpha=0.2)
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_xticks(theta[:-1])
    ax.set_xticklabels(rotulos, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    ax.text(0.5, -0.1, "Unidade: graus", transform=ax.transAxes, fontsize=9,
            horizontalalignment='center', bbox=dict(facecolor='white', alpha=0.7))
    
    return fig

# =====================================================
# CONFIGURACAO DO ESTADO
# =====================================================

if 'page' not in state:
    state.page = 'upload'
    state.df_vento = None
    state.df_onda = None
    state.popup_fechado = False
    state.popup_pagina = 1  # 1 = primeira página, 2 = segunda página
    
    # Cores padrão
    state.cor_velocidade = "#2ca02c"
    state.cor_onda = "#1f77b4"
    state.cor_radar = "#d62728"

def go_to_upload():
    state.page = 'upload'

def go_to_visualization():
    state.page = 'visualization'

def fechar_popup():
    state.popup_fechado = True

def proxima_pagina_popup():
    state.popup_pagina = 2

def voltar_pagina_popup():
    state.popup_pagina = 1

# =====================================================
# FUNÇÃO PARA SCROLL AO TOPO
# =====================================================

def scroll_to_top():
    """Função para rolar a página para o topo"""
    components.html(
        """
        <script>
            window.scrollTo(0, 0);
        </script>
        """,
        height=0
    )

# =====================================================
# PAGINAS DO APLICATIVO
# =====================================================

def upload_page():
    st.set_page_config(page_title="Monitoramento", layout="wide")
    
    # Pop-up que bloqueia o conteúdo principal
    if not state.popup_fechado:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Página 1 do pop-up
                if state.popup_pagina == 1:
                    st.markdown("""
                    <div style="background-color: #1e1e2e; padding: 35px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); text-align: center; border: 1px solid #4a4a5a; margin-top: 50px;">
                        <h2 style="margin-top: 0; color: white; font-size: 24px;">Sobre este Trabalho</h2>
                        <p style="margin: 20px 0; color: #e0e0e0; font-size: 15px; line-height: 1.6; text-align: justify;">
                            Este sistema foi desenvolvido para o monitoramento e análise de dados de ventos, 
                            com foco na medição de velocidade e direção. A plataforma permite o carregamento de 
                            arquivos contendo dados coletados por equipamentos como anemômetros, processando e 
                            apresentando as informações de forma visual e interativa.
                        </p>
                        <p style="margin: 15px 0; color: #cccccc; font-size: 14px; line-height: 1.6; text-align: justify;">
                            Os dados são exibidos em gráficos dinâmicos que facilitam a interpretação das condições 
                            de vento, auxiliando na tomada de decisões em atividades como navegação, aviação, 
                            monitoramento ambiental e estudos meteorológicos.
                        </p>
                        <p style="margin: 15px 0; color: #cccccc; font-size: 14px; line-height: 1.6; text-align: justify;">
                            Para utilizar o sistema, basta carregar um arquivo no formato correto. O sistema processará 
                            os dados e disponibilizará as visualizações para análise. Certifique-se de que o arquivo 
                            está no formato adequado para garantir a correta interpretação dos dados de vento.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão "Próximo →"
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("Próximo →", type="primary", use_container_width=True):
                            proxima_pagina_popup()
                            st.rerun()
                
                # Página 2 do pop-up
                elif state.popup_pagina == 2:
                    st.markdown("""
                    <div style="background-color: #1e1e2e; padding: 35px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); text-align: center; border: 1px solid #4a4a5a; margin-top: 50px;">
                        <h2 style="margin-top: 0; color: white; font-size: 24px;">Instituição de Realização</h2>
                        <p style="margin: 20px 0; color: #e0e0e0; font-size: 15px; line-height: 1.6; text-align: justify;">
                            O presente trabalho foi realizado na Universidade Estadual Paulista Júlio de Mesquita Filho - UNESP, 
                            Campus de Ilha Solteira, no Laboratório ProfÁgua - Laboratório de Hidrologia e Hidrometria - LH2.
                        </p>
                        <p style="margin: 15px 0; color: #cccccc; font-size: 14px; line-height: 1.6; text-align: justify;">
                            O LH2 é um laboratório dedicado à pesquisa e ao desenvolvimento de tecnologias nas áreas de hidrologia, 
                            hidrometria e monitoramento ambiental, contribuindo para o avanço do conhecimento científico e 
                            para a formação de profissionais qualificados.
                        </p>
                        <hr style="border-color: #4a4a5a; margin: 20px 0;">
                        <h3 style="color: white; font-size: 18px; margin-bottom: 15px;">Equipe Responsável</h3>
                        <div style="text-align: left; color: #cccccc; font-size: 14px; line-height: 1.8;">
                            <p style="margin: 5px 0;"><strong style="color: #e0e0e0;">Orientadores:</strong></p>
                            <p style="margin: 3px 0; padding-left: 15px;">
                                Prof. Dr. Evandro Fernandes da Cunha<br>
                                <span style="color: #8888aa;">evandro.cunha@unesp.br</span>
                            </p>
                            <p style="margin: 3px 0; padding-left: 15px;">
                                Prof. Dr. Geraldo de Freitas Maciel<br>
                                <span style="color: #8888aa;">geraldo.f.maciel@unesp.br</span>
                            </p>
                            <p style="margin: 10px 0 5px 0;"><strong style="color: #e0e0e0;">Aluno:</strong></p>
                            <p style="margin: 3px 0; padding-left: 15px;">
                                Luiz Eduardo Landin Rodrigues<br>
                                <span style="color: #8888aa;">luiz.landin@unesp.br</span>
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botões "← Voltar" e "OK, entendi"
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("← Voltar", use_container_width=True):
                            voltar_pagina_popup()
                            st.rerun()
                    with col3:
                        if st.button("OK, entendi", type="primary", use_container_width=True):
                            fechar_popup()
                            state.popup_pagina = 1  # Resetar para página 1
                            st.rerun()
    
    if state.popup_fechado:
        st.title("Monitoramento - Carregar Dados")
        
        arquivo_carregado = st.file_uploader("Selecione o arquivo de dados", 
                                           type=["csv", "txt", "log"])
        
        if arquivo_carregado is not None:
            try:
                conteudo = arquivo_carregado.read()
                dados_vento, dados_onda = processar_arquivo(conteudo)
                
                if dados_vento or dados_onda:
                    state.df_vento, state.df_onda = criar_dataframes(dados_vento, dados_onda)
                    st.success("Arquivo carregado com sucesso!")
                    st.info(f"Registros de vento encontrados: {len(dados_vento)}")
                    st.info(f"Registros de onda do vento encontrados: {len(dados_onda)}")
                    
                    if dados_vento:
                        with st.expander("Preview dos dados de VENTO", expanded=False):
                            st.dataframe(state.df_vento[['indice', 'timestamp', 'velocidade_vento', 'direcao_vento']].head(10))
                    
                    if dados_onda:
                        with st.expander("Preview dos dados de ONDA DO VENTO", expanded=False):
                            st.dataframe(state.df_onda[['indice', 'timestamp', 'valor_bruto']].head(10))
                            
                            st.write("Estatísticas das ondas (em metros):")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Mínimo", f"{state.df_onda['valor_bruto'].min():.3f} m")
                            with col2:
                                st.metric("Máximo", f"{state.df_onda['valor_bruto'].max():.3f} m")
                            with col3:
                                st.metric("Média", f"{state.df_onda['valor_bruto'].mean():.3f} m")
                    
                    if st.button("Visualizar Dashboard", type="primary", use_container_width=True):
                        go_to_visualization()
                        st.rerun()
                else:
                    st.error("Não foi possível extrair dados do arquivo.")
                    
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
    else:
        st.empty()

def visualization_page():
    st.set_page_config(page_title="Dashboard", layout="wide")
    
    # Scroll para o topo da página
    scroll_to_top()
    
    st.title("Dashboard de Monitoramento")
    
    if (state.df_vento is None or state.df_vento.empty) and (state.df_onda is None or state.df_onda.empty):
        st.warning("Nenhum dado carregado.")
        if st.button("Voltar para Upload"):
            state.popup_fechado = False
            go_to_upload()
            st.rerun()
        return
    
    max_linhas_vento = len(state.df_vento) - 1 if state.df_vento is not None and not state.df_vento.empty else 0
    max_linhas_onda = len(state.df_onda) - 1 if state.df_onda is not None and not state.df_onda.empty else 0
    
    # =====================================================
    # CORES DOS GRÁFICOS (usando session_state)
    # =====================================================
    
    # Inicializar cores no session_state se não existirem
    if 'cor_velocidade' not in state:
        state.cor_velocidade = "#2ca02c"
    if 'cor_onda' not in state:
        state.cor_onda = "#1f77b4"
    if 'cor_radar' not in state:
        state.cor_radar = "#d62728"
    
    # =====================================================
    # SIDEBAR - Configurações com expanders (sem emojis)
    # =====================================================
    
    with st.sidebar:
        st.header("Configurações")
        
        # ===== 1. VELOCIDADE DO VENTO =====
        with st.expander("1. Velocidade do Vento", expanded=False):
            if not state.df_vento.empty:
                tema_escuro_vel = st.checkbox("Tema escuro", value=False, key="tema_escuro_vel")
                nova_cor_vel = st.color_picker("Cor", state.cor_velocidade, key="cor_velocidade_picker")
                if nova_cor_vel != state.cor_velocidade:
                    state.cor_velocidade = nova_cor_vel
                    st.rerun()
                
                col1, col2 = st.columns(2)
                with col1:
                    inicio_vel = st.number_input("Leitura inicial", 1, max_linhas_vento + 1, 1, key="inicio_vel")
                with col2:
                    fim_vel = st.number_input("Leitura final", 1, max_linhas_vento + 1, min(200, max_linhas_vento + 1), key="fim_vel", help=f"Total de registros: {max_linhas_vento + 1}")
        
        # ===== 2. ALTURA DA ONDA =====
        with st.expander("2. Altura da Onda do Vento", expanded=False):
            if not state.df_onda.empty:
                tema_escuro_onda = st.checkbox("Tema escuro", value=False, key="tema_escuro_onda")
                nova_cor_onda = st.color_picker("Cor", state.cor_onda, key="cor_onda_picker")
                if nova_cor_onda != state.cor_onda:
                    state.cor_onda = nova_cor_onda
                    st.rerun()
                
                col1, col2 = st.columns(2)
                with col1:
                    inicio_onda = st.number_input("Leitura inicial", 1, max_linhas_onda + 1, 1, key="inicio_onda")
                with col2:
                    fim_onda = st.number_input("Leitura final", 1, max_linhas_onda + 1, min(200, max_linhas_onda + 1), key="fim_onda", help=f"Total de registros: {max_linhas_onda + 1}")
        
        # ===== 3. ROSA DOS VENTOS =====
        with st.expander("3. Rosa dos Ventos", expanded=False):
            if not state.df_vento.empty:
                tema_escuro_dir = st.checkbox("Tema escuro", value=False, key="tema_escuro_dir")
                nova_cor_radar = st.color_picker("Cor", state.cor_radar, key="cor_radar_picker")
                if nova_cor_radar != state.cor_radar:
                    state.cor_radar = nova_cor_radar
                    st.rerun()
                
                col1, col2 = st.columns(2)
                with col1:
                    inicio_dir = st.number_input("Leitura inicial", 1, max_linhas_vento + 1, 1, key="inicio_dir")
                with col2:
                    fim_dir = st.number_input("Leitura final", 1, max_linhas_vento + 1, min(200, max_linhas_vento + 1), key="fim_dir", help=f"Total de registros: {max_linhas_vento + 1}")
    
    # =====================================================
    # ABAS (TABS) - Navegação entre os gráficos
    # =====================================================
    
    # Definir os nomes das abas
    abas_disponiveis = ["Velocidade do Vento", "Altura da Onda do Vento", "Rosa dos Ventos"]
    
    # Criar as abas
    tabs = st.tabs(abas_disponiveis)
    
    # =====================================================
    # CONTEUDO DAS ABAS
    # =====================================================
    
    # Aba 1: Velocidade do Vento
    with tabs[0]:
        st.header("Velocidade do Vento")
        
        if not state.df_vento.empty:
            # Garantir que os valores estão dentro do intervalo
            inicio_vel = max(1, min(inicio_vel, max_linhas_vento + 1))
            fim_vel = max(1, min(fim_vel, max_linhas_vento + 1))
            
            leitura_inicio = min(inicio_vel, fim_vel)
            leitura_fim = max(inicio_vel, fim_vel)
            
            if 'datetime' in state.df_vento.columns and state.df_vento['datetime'].notna().any():
                idx_min = leitura_inicio - 1
                idx_max = leitura_fim - 1
                df_periodo = state.df_vento.iloc[idx_min:idx_max+1]
                
                if not df_periodo.empty and df_periodo['datetime'].notna().any():
                    data_inicio_periodo = df_periodo['datetime'].iloc[0]
                    data_fim_periodo = df_periodo['datetime'].iloc[-1]
                    duracao_periodo = (data_fim_periodo - data_inicio_periodo).total_seconds()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"Início do período: {data_inicio_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col2:
                        st.info(f"Fim do período: {data_fim_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col3:
                        st.info(f"Duração do período: {formatar_duracao(duracao_periodo)}")
                    
                    st.caption(f"Leituras analisadas: {leitura_inicio} até {leitura_fim}")
            
            inicio_idx = inicio_vel - 1
            fim_idx = fim_vel - 1
            
            fig = plotar_grafico_velocidade_vento(
                state.df_vento, inicio_idx, fim_idx,
                state.cor_velocidade, tema_escuro_vel
            )
            if fig:
                st.pyplot(fig)
        else:
            st.info("Sem dados de velocidade do vento disponíveis.")
    
    # Aba 2: Altura da Onda do Vento
    with tabs[1]:
        st.header("Altura da Onda do Vento")
        
        if not state.df_onda.empty:
            # Garantir que os valores estão dentro do intervalo
            inicio_onda = max(1, min(inicio_onda, max_linhas_onda + 1))
            fim_onda = max(1, min(fim_onda, max_linhas_onda + 1))
            
            leitura_inicio = min(inicio_onda, fim_onda)
            leitura_fim = max(inicio_onda, fim_onda)
            
            if 'datetime' in state.df_onda.columns and state.df_onda['datetime'].notna().any():
                idx_min = leitura_inicio - 1
                idx_max = leitura_fim - 1
                df_periodo = state.df_onda.iloc[idx_min:idx_max+1]
                
                if not df_periodo.empty and df_periodo['datetime'].notna().any():
                    data_inicio_periodo = df_periodo['datetime'].iloc[0]
                    data_fim_periodo = df_periodo['datetime'].iloc[-1]
                    duracao_periodo = (data_fim_periodo - data_inicio_periodo).total_seconds()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"Início do período: {data_inicio_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col2:
                        st.info(f"Fim do período: {data_fim_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col3:
                        st.info(f"Duração do período: {formatar_duracao(duracao_periodo)}")
                    
                    st.caption(f"Leituras analisadas: {leitura_inicio} até {leitura_fim}")
            
            inicio_idx = inicio_onda - 1
            fim_idx = fim_onda - 1
            
            fig = plotar_grafico_onda(
                state.df_onda, inicio_idx, fim_idx,
                state.cor_onda, tema_escuro_onda
            )
            if fig:
                st.pyplot(fig)
        else:
            st.info("Sem dados de onda do vento disponíveis.")
    
    # Aba 3: Rosa dos Ventos
    with tabs[2]:
        st.header("Rosa dos Ventos")
        
        if not state.df_vento.empty:
            # Garantir que os valores estão dentro do intervalo
            inicio_dir = max(1, min(inicio_dir, max_linhas_vento + 1))
            fim_dir = max(1, min(fim_dir, max_linhas_vento + 1))
            
            leitura_inicio = min(inicio_dir, fim_dir)
            leitura_fim = max(inicio_dir, fim_dir)
            
            if 'datetime' in state.df_vento.columns and state.df_vento['datetime'].notna().any():
                idx_min = leitura_inicio - 1
                idx_max = leitura_fim - 1
                df_periodo = state.df_vento.iloc[idx_min:idx_max+1]
                
                if not df_periodo.empty and df_periodo['datetime'].notna().any():
                    data_inicio_periodo = df_periodo['datetime'].iloc[0]
                    data_fim_periodo = df_periodo['datetime'].iloc[-1]
                    duracao_periodo = (data_fim_periodo - data_inicio_periodo).total_seconds()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"Início do período: {data_inicio_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col2:
                        st.info(f"Fim do período: {data_fim_periodo.strftime('%d/%m/%Y %H:%M:%S')}")
                    with col3:
                        st.info(f"Duração do período: {formatar_duracao(duracao_periodo)}")
                    
                    st.caption(f"Leituras analisadas: {leitura_inicio} até {leitura_fim}")
            
            inicio_idx = inicio_dir - 1
            fim_idx = fim_dir - 1
            
            fig = plotar_grafico_radar(
                state.df_vento, inicio_idx, fim_idx,
                state.cor_radar, tema_escuro_dir
            )
            if fig:
                st.pyplot(fig)
        else:
            st.info("Sem dados de direção do vento disponíveis.")
    
    # Botão voltar (fora das abas)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Carregar Novo Arquivo", use_container_width=True):
            state.popup_fechado = False
            go_to_upload()
            st.rerun()

# =====================================================
# NAVEGACAO PRINCIPAL
# =====================================================

if __name__ == "__main__":
    if state.page == 'upload':
        upload_page()
    elif state.page == 'visualization':
        visualization_page()
