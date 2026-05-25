# Changelog

## [1.0.1] - 2026-05-25

### Corrigido
- Remoção da chave de download de imagem `image` para forçar a compilação local a partir do Dockerfile.
- Correção da arquitetura depreciada `armv7` para `armhf` no arquivo de configuração do add-on.

## [1.0.0] - 2026-05-25

### Adicionado
- Versão inicial do Add-on **AMT-8000 Alarm Manager**.
- Cliente do protocolo **iSEC2** robusto e adaptado, com suporte multi-thread e bloqueio de concorrência.
- API REST em Flask integrada para comunicação bidirecional de status e comandos com a central.
- Suporte nativo ao **Home Assistant Ingress** para integração no menu lateral.
- Painel de gerenciamento web moderno com design *glassmorphism* e tema escuro premium.
- Suporte a monitoramento de até **16 partições** e **64 zonas** ativas.
- Implementação de **Bypass de Zonas** (anulação temporária de zonas diretamente no painel).
- Botões de **Pânico** (Audível e Silencioso).
- Filtros inteligentes e sistema de busca em tempo real na listagem de zonas.
- Badges de diagnósticos (nível de bateria da central, firmware, IP e porta).
- Arquivos de tradução em Português (`pt.yaml`) e Inglês (`en.yaml`) para a tela de configurações do Home Assistant.
- Arte de ícone e logo geradas exclusivamente para identidade visual refinada do add-on.
