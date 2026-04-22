# TradutorSimSIC

Base principal do tradutor em tempo real PT -> EN.

## Estrutura atual

- `Tradutor_de_PT_para_ING/server.py`: backend Flask, captura de audio, transcricao e traducao.
- `Tradutor_de_PT_para_ING/templates/index.html`: interface de legendas em tempo real.
- `run.bat`: perfil equilibrado (GPU + Whisper small).
- `run_quality.bat`: perfil qualidade (GPU + Whisper medium).
- `build_exe.bat`: criacao do executavel com PyInstaller.

## Arranque local

1. Criar o ambiente:
   - `py -3 -m venv .venv`
2. Instalar dependencias:
   - `.venv\Scripts\python -m pip install -r requirements.txt`
3. Executar:
   - `run.bat`

Perfis recomendados para RTX 4060:

- `run.bat`: mais rapido e ainda com boa qualidade.
- `run_quality.bat`: melhor qualidade, com mais latencia.

Nota sobre ffmpeg:

- O projeto tenta usar `FFMPEG_DIR`.
- Se essa variavel nao existir, tenta `ffmpeg/bin` dentro do projeto.
- Se tambem nao existir, em Windows tenta automaticamente `C:\ffmpeg\bin`.

## Gerar executavel

1. Garantir o ambiente ativo e as dependencias instaladas.
2. Executar `build_exe.bat`.
3. O executavel fica em `dist\TradutorSimSIC.exe`.
