# Audiodescrição Toolkit

Este repositório entrega um conjunto integrado de ferramentas para gerar audiodescrição (AD) em português brasileiro conforme boas práticas nacionais (ABNT), tanto em ambiente desktop (macOS) quanto web. O projeto é pensado para execução local sem custos de licenciamento e utiliza apenas componentes gratuitos e compatíveis com uso comercial.

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Componentes](#componentes)
- [Como executar](#como-executar)
  - [CLI Python (`adtool`)](#cli-python-adtool)
  - [Aplicativo Desktop (Tauri + React)](#aplicativo-desktop-tauri--react)
  - [Aplicativo Web (Next.js + FastAPI)](#aplicativo-web-nextjs--fastapi)
- [Pipeline de Processamento](#pipeline-de-processamento)
- [Testes automatizados](#testes-automatizados)
- [Amostras públicas](#amostras-públicas)
- [Conformidade de licenças](#conformidade-de-licenças)
- [Roadmap & contribuições](#roadmap--contribuições)

## Visão Geral

O objetivo principal é oferecer um fluxo completo de AD:

1. Ingestão de arquivos locais (MP4, MOV, AVI) ou URLs (YouTube/Vimeo) usando `yt-dlp`.
2. Detecção de janelas sem diálogos através de heurísticas baseadas em VAD (Silero), ASR (Faster-Whisper) e análise espectral.
3. Geração de roteiro textual em PT-BR seguindo diretrizes ABNT de audiodescrição.
4. Síntese de voz usando mecanismos livres (AVSpeechSynthesizer no macOS, Web Speech API no navegador, Piper com voz CC0 em fallback).
5. Mixagem com ducking suave da trilha original e exportação de ativos em SRT, TXT, WAV, MP3 e MP4 opcional.

Todos os componentes podem operar offline, preservando a privacidade das mídias processadas.

## Arquitetura

```
repo
├── LICENSE.md
├── README.md
├── TERCEIROS.md
├── docker-compose.yml
├── packages
│   └── adtool        # Biblioteca/CLI Python com pipeline de AD
├── desktop
│   └── app          # Aplicativo Tauri (macOS)
├── web
│   ├── frontend     # Next.js + Tailwind + Zustand + Wavesurfer.js
│   └── backend      # FastAPI + Celery (BullMQ opcional)
├── samples          # Amostras públicas e resultados esperados
└── tests            # Testes automatizados de pipeline
```

## Componentes

### Pacote Python `adtool`

- Implementa o pipeline de processamento de AD.
- Exposto via CLI conforme comandos especificados (`ingest`, `detect-windows`, `generate-ad`, `tts`, `mux`).
- Depende de FFmpeg (LGPL, build dinâmico), Silero VAD, Faster-Whisper, MoviePy, NumPy, Piper (opcional) e bibliotecas auxiliares.

### Desktop (Tauri)

- Front-end em React + Tailwind.
- Sidecar Rust orquestra FFmpeg, Piper e biblioteca Python via comandos nativos.
- Build universal macOS (arm64/x86_64) via `npm run tauri build`.

### Web (Next.js + FastAPI)

- Front-end Next.js (App Router) hospedável em Vercel.
- Backend FastAPI com workers Celery + Redis (opcional) ou modo síncrono local.
- Deploy sugerido: Fly.io (backend) e Vercel (frontend), ambos em tiers gratuitos.

## Como executar

### CLI Python (`adtool`)

1. Crie um ambiente virtual Python 3.10+.
2. Instale dependências locais:

   ```bash
   cd packages/adtool
   pip install -e .[dev]
   ```

3. Garanta que `ffmpeg`, `ffprobe` e `yt-dlp` estão disponíveis no `PATH`.
4. Execute o pipeline completo em um vídeo de teste:

   ```bash
   adtool ingest --input samples/demo/domain_public.mp4 --out outputs/demo
   adtool detect-windows --input outputs/demo/audio.wav --out outputs/demo/janelas.json
   adtool generate-ad --input outputs/demo/janelas.json --media outputs/demo/meta.json --out outputs/demo/ad
   adtool tts --input outputs/demo/ad/ad.srt --voice "pt-BR" --out outputs/demo/audio
   adtool mux --video outputs/demo/video.mp4 --ad outputs/demo/audio/ad.wav --srt outputs/demo/ad/ad.srt --out outputs/demo/video_com_ad.mp4
   ```

   O comando `adtool pipeline --input ...` executa todas as etapas sequencialmente.

### Aplicativo Desktop (Tauri + React)

1. Instale Node.js LTS e Rust (via `rustup`).
2. Configure FFmpeg disponível no sistema (instalação via Homebrew recomendada).
3. Instale dependências e rode em modo desenvolvimento:

   ```bash
   cd desktop/app
   npm install
   npm run tauri dev
   ```

4. Para gerar o binário assinado localmente:

   ```bash
   npm run tauri build
   ```

   O binário universal estará em `desktop/app/src-tauri/target/release/bundle/macos`.

### Aplicativo Web (Next.js + FastAPI)

#### Ambiente local

1. Configure variáveis de ambiente conforme `.env.example`.
2. Suba os serviços com Docker Compose:

   ```bash
   docker-compose up --build
   ```

3. Front-end acessível em `http://localhost:3000` e API em `http://localhost:8000`.

#### Deploy gratuito sugerido

- Front-end: `vercel --prod` dentro de `web/frontend`.
- Backend: `fly launch` dentro de `web/backend` com volume persistente para cache.

## Pipeline de Processamento

1. **Ingestão**: download/extração via `yt-dlp` e FFmpeg. Metadados salvos em JSON.
2. **Detecção de janelas**: combina resultados de ASR (opcional), VAD (Silero) e análise RMS.
3. **Geração de roteiro**: sumariza cenas via embeddings CLIP (opcional) e heurísticas textuais.
4. **Síntese (TTS)**: prioriza mecanismos nativos; fallback Piper CC0.
5. **Mixagem e exportação**: ducking calculado e exportações gerenciadas por MoviePy/FFmpeg.

## Testes automatizados

Execute a suíte principal:

```bash
pytest
```

Os testes cobrem heurísticas de detecção de janelas, formatação de SRT/TXT e integração mínima do pipeline com mídia simulada.

## Amostras públicas

`samples/demo/` contém um script `download_sample.sh` que obtém um clipe curto em domínio público (MP4) e os artefatos esperados (SRT/TXT/WAV) gerados manualmente para validação.

## Conformidade de licenças

Consulte `TERCEIROS.md` para ver a lista de dependências, versões e licenças. O projeto como um todo é licenciado sob MIT e evita dependências com royalties.

## Roadmap & contribuições

- Implementar detecção automática de ruídos complexos.
- Adicionar suporte a processamento distribuído.
- Melhorar UI de edição fina com edição visual de envelopes de ducking.

Contribuições são bem-vindas via issues e pull requests. Siga o guia de contribuição em `CONTRIBUTING.md` (a ser criado).
