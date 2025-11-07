# Terceiros e Licenças

Este documento lista dependências de código aberto utilizadas no projeto e suas respectivas licenças. Consulte as páginas oficiais para obter os textos integrais.

| Componente | Uso | Licença |
|------------|-----|---------|
| FFmpeg (build dinâmico) | Transcodificação e mixagem | LGPL-2.1-or-later |
| yt-dlp | Download de vídeos online | Unlicense |
| Faster-Whisper | ASR opcional | MIT |
| Silero VAD | Detecção de voz | MIT |
| MoviePy | Manipulação de vídeo | MIT |
| PyAV | Manipulação de áudio/vídeo | LGPL-2.1 |
| NumPy | Processamento numérico | BSD-3-Clause |
| SciPy | Processamento de sinais | BSD-3-Clause |
| Torch (opcional, CPU) | Modelo Silero/Whisper | BSD-3-Clause |
| OpenAI Whisper weights | Modelo ASR | MIT |
| OpenCLIP | Embeddings visuais | MIT |
| CLIP Interrogator (adaptação) | Extração de descritores | Apache-2.0 |
| Piper TTS | Fallback de síntese | MIT |
| Piper voice (por padrão `pt_BR-Edilson-medium`) | Voz CC0 | CC0 |
| React | UI | MIT |
| Next.js | UI web | MIT |
| Tailwind CSS | Estilização | MIT |
| Zustand | Gerenciamento de estado | MIT |
| Wavesurfer.js | Visualização de onda | BSD-3-Clause |
| Tauri | Aplicativo desktop | Apache-2.0 / MIT |
| FastAPI | API | MIT |
| Celery | Fila de tarefas | BSD-3-Clause |
| Redis (cliente) | Broker/cache | BSD-3-Clause |
| Typer | CLI Python | MIT |
| Rich | Logs e UI textual | MIT |
| pytest | Testes | MIT |
| Docker | Empacotamento | Apache-2.0 |

Dependências opcionais devem ser instaladas pelo usuário de acordo com as necessidades. Caso utilize outras vozes Piper com licença CC-BY, configure o campo de atribuição automática disponível no aplicativo.
