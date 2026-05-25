# Changelog

## [1.0.8] - 2026-05-25

### Corrigido
- Correção de bug crítico de cálculo off-by-one no tamanho total do pacote de dados (`_read_data`), mudando de `8 + expected_len` para `7 + expected_len` bytes. Isso resolve de forma definitiva o problema de timeout infinito gerado pela leitura de um byte extra inexistente após o checksum.

## [1.0.7] - 2026-05-25

### Adicionado
- Logs verbosos de diagnóstico para o fluxo de conexão TCP do socket, comandos de autenticação em formato hexadecimal e loop de recebimento e fragmentação de pacotes iSEC2 para identificar timeouts.

## [1.0.6] - 2026-05-25

### Corrigido
- Desativação do perfil AppArmor (`apparmor: false`) no `config.yaml` para remover as restrições de segurança do contêiner sobre soquetes TCP de rede, permitindo conectividade irrestrita com a rede física local.

## [1.0.5] - 2026-05-25

### Corrigido
- Alteração da porta do Ingress e do servidor Flask de `8099` para `8199` para resolver conflito de endereço já em uso ("Address in use") ao rodar no modo de rede do host.

## [1.0.4] - 2026-05-25

### Corrigido
- Ativação de `host_network: true` no `config.yaml` para permitir que o add-on acesse diretamente a rede local (LAN) do host, evitando timeouts causados por isolamento de rede do Docker bridge.

## [1.0.3] - 2026-05-25

### Corrigido
- Configuração de `init: false` no `config.yaml` para desativar o wrapper tini e permitir que o s6-overlay do contêiner execute como PID 1 sem conflitos.

## [1.0.2] - 2026-05-25

### Corrigido
- Inclusão da cópia explícita do script `run.sh` no Dockerfile para corrigir falha de compilação da imagem Docker.

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
