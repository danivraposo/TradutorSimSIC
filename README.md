# TradutorSimSIC 🎙️🌍

O **TradutorSimSIC** é uma ferramenta de tradução em tempo real que captura áudio em Português (PT), transcreve para texto e traduz automaticamente para Inglês (EN), exibindo os resultados numa interface web minimalista ideal para legendas.

## 🚀 Como Funciona?

O sistema opera através de três componentes principais que correm em paralelo:

1.  **Captura de Áudio**: Utiliza a biblioteca `PyAudio` para ouvir o microfone padrão do sistema. O áudio é segmentado automaticamente quando deteta silêncio ou atinge um tempo máximo.
2.  **Transcrição (Whisper)**: O áudio capturado é processado pelo modelo **Whisper da OpenAI**. Este modelo de IA converte a fala em texto em português com alta precisão.
3.  **Tradução (Google Translate)**: O texto em português é enviado para o `GoogleTranslator` (via `deep_translator`), que o converte para inglês.
4.  **Interface Web**: Um servidor **Flask** disponibiliza uma página (acessível em `localhost:5000`) que recebe as traduções via *Server-Sent Events (SSE)* e as exibe instantaneamente no ecrã.

## 🛠️ Estrutura do Projeto

-   `Tradutor_de_PT_para_ING/server.py`: O "cérebro" do projeto (Flask + Whisper + Captura).
-   `Tradutor_de_PT_para_ING/templates/index.html`: A interface visual das legendas.
-   `run.bat`: Atalho para iniciar com o modelo **Whisper Small** (equilíbrio entre velocidade e precisão).
-   `run_quality.bat`: Atalho para iniciar com o modelo **Whisper Medium** (maior precisão, exige mais GPU).
-   `build_exe.bat`: Script para transformar o projeto num ficheiro `.exe` independente.

## 📦 Requisitos e Instalação

### Pré-requisitos
-   **Python 3.10+**
-   **FFmpeg**: Essencial para o processamento de áudio. O projeto procura por:
    -   Variável de ambiente `FFMPEG_DIR`
    -   Pasta `ffmpeg/bin` no diretório raiz
    -   `C:\ffmpeg\bin` (padrão Windows)

### Instalação Local
1.  **Criar Ambiente Virtual**:
    ```bash
    py -3 -m venv .venv
    ```
2.  **Instalar Dependências**:
    ```bash
    .venv\Scripts\python -m pip install -r requirements.txt
    ```
3.  **Executar**:
    -   Usa o `run.bat` (Recomendado para RTX 4060 ou superior).

---

## 💡 O que pode ser melhorado?

Para quem deseja contribuir ou expandir o projeto, aqui estão algumas sugestões de melhoria:

1.  **VAD (Voice Activity Detection)**: Atualmente, a deteção de fala baseia-se em volume (RMS). Implementar o `WebRTCVAD` ou `Silero VAD` tornaria a segmentação de frases muito mais robusta.
2.  **Suporte Multi-idioma**: Adicionar a opção de escolher o idioma de entrada e saída na interface web, em vez de estar fixo em PT -> EN.
3.  **Performance (Faster-Whisper)**: Migrar para o `faster-whisper` permitiria usar modelos maiores com muito menos consumo de memória e maior velocidade.
4.  **Customização da UI**: Adicionar um painel de definições na interface web para alterar o tamanho da fonte, cor do texto, fundo (ex: fundo verde para *chroma key*) e transparência.
5.  **Tradução Offline**: Integrar modelos como o `Argos Translate` ou `LibreTranslate` para permitir o funcionamento totalmente offline, sem depender da API do Google.
6.  **Histórico e Exportação**: Opção para guardar a transcrição e tradução num ficheiro de texto ou formato `.srt` no final da sessão.

---
Desenvolvido por [danivraposo](https://github.com/danivraposo) 🚀

